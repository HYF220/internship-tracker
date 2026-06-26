"""
集成测试：端到端 API 联通性测试

完整模拟多用户场景，验证所有 API 协同工作和权限隔离。
"""

import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = "postgresql://postgres@localhost:5433/internship_tracker"
test_engine = create_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)

Base.metadata.create_all(bind=test_engine)


@pytest.fixture()
def db():
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.pop(get_db, None)


def make_pdf_bytes():
    return b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]>>endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
trailer<</Size 4/Root 1 0 R>>
startxref
190
%%EOF"""


# ==================== 完整用户流程 ====================

class TestFullUserFlow:
    """测试从注册到投递的完整流程"""

    def test_complete_flow(self, client):
        """单个用户完整流程：注册→登录→创建岗位→创建投递→统计→上传简历"""
        # 1. 注册
        resp = client.post("/auth/register", json={
            "email": "fullflow@test.com",
            "password": "password123",
        })
        assert resp.status_code == 201
        assert resp.json()["email"] == "fullflow@test.com"

        # 2. 登录
        resp = client.post("/auth/login", json={
            "email": "fullflow@test.com",
            "password": "password123",
        })
        assert resp.status_code == 200
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 3. 查看个人信息
        resp = client.get("/auth/me", headers=headers)
        assert resp.status_code == 200
        user_id = resp.json()["id"]

        # 4. 创建岗位
        resp = client.post("/jobs", json={
            "company_name": "字节跳动",
            "title": "前端实习生",
            "location": "北京",
            "salary_range": "20k-30k",
        }, headers=headers)
        assert resp.status_code == 201
        job_id = resp.json()["id"]
        assert resp.json()["user_id"] == user_id

        # 5. 创建第二个岗位
        resp = client.post("/jobs", json={
            "company_name": "阿里巴巴",
            "title": "后端开发实习生",
        }, headers=headers)
        assert resp.status_code == 201
        job2_id = resp.json()["id"]

        # 6. 查看岗位列表
        resp = client.get("/jobs", headers=headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 2

        # 7. 更新岗位
        resp = client.put(f"/jobs/{job_id}", json={
            "status": "applied",
        }, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "applied"

        # 8. 创建投递记录
        resp = client.post("/applications", json={
            "job_id": job_id,
            "status": "applied",
            "applied_at": "2026-07-01T10:00:00",
        }, headers=headers)
        assert resp.status_code == 201
        app_id = resp.json()["id"]

        # 9. 更新投递状态
        resp = client.put(f"/applications/{app_id}", json={
            "status": "interview",
            "notes": "一面通过，准备二面",
        }, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "interview"

        # 10. 创建第二条投递
        resp = client.post("/applications", json={
            "job_id": job2_id,
            "status": "offer",
        }, headers=headers)
        assert resp.status_code == 201

        # 11. 查看投递列表
        resp = client.get("/applications", headers=headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 2

        # 12. Dashboard 统计
        resp = client.get("/stats/summary", headers=headers)
        assert resp.status_code == 200
        stats = resp.json()
        assert stats["total_jobs"] == 2
        assert stats["total_interview"] == 1
        assert stats["total_offer"] == 1

        # 13. 上传简历
        resp = client.post("/resumes/upload", data={"name": "我的简历"}, files={
            "file": ("resume.pdf", io.BytesIO(make_pdf_bytes()), "application/pdf"),
        }, headers=headers)
        assert resp.status_code == 201
        assert resp.json()["name"] == "我的简历"

        # 14. 查看简历列表
        resp = client.get("/resumes", headers=headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 1

        # 15. 删除岗位（先确认能被删除——该岗位不能有级联数据时，后端返回错误）
        # 创建没有投递记录的新岗位来测试删除
        resp = client.post("/jobs", json={
            "company_name": "待删除公司",
            "title": "待删除岗位",
        }, headers=headers)
        assert resp.status_code == 201
        delete_target_id = resp.json()["id"]

        resp = client.delete(f"/jobs/{delete_target_id}", headers=headers)
        assert resp.status_code == 204

        # 16. 确认删除后岗位数正确
        resp = client.get("/jobs", headers=headers)
        assert len(resp.json()) == 2  # 字节跳动 + 阿里巴巴还在


class TestMultiUserIsolation:
    """测试多用户数据隔离"""

    def test_users_cannot_access_each_others_data(self, client):
        """用户A和用户B的数据完全隔离"""
        # 注册两个用户
        client.post("/auth/register", json={
            "email": "isolation_a@test.com", "password": "123456",
        })
        client.post("/auth/register", json={
            "email": "isolation_b@test.com", "password": "123456",
        })

        token_a = client.post("/auth/login", json={
            "email": "isolation_a@test.com", "password": "123456",
        }).json()["access_token"]
        token_b = client.post("/auth/login", json={
            "email": "isolation_b@test.com", "password": "123456",
        }).json()["access_token"]

        headers_a = {"Authorization": f"Bearer {token_a}"}
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # A 创建一个岗位
        resp = client.post("/jobs", json={
            "company_name": "A的公司", "title": "A的岗位",
        }, headers=headers_a)
        job_a_id = resp.json()["id"]

        # B 创建一个岗位
        resp = client.post("/jobs", json={
            "company_name": "B的公司", "title": "B的岗位",
        }, headers=headers_b)

        # A 看不到 B 的岗位
        resp = client.get("/jobs", headers=headers_a)
        assert len(resp.json()) == 1
        assert resp.json()[0]["company_name"] == "A的公司"

        # B 看不到 A 的岗位
        resp = client.get("/jobs", headers=headers_b)
        assert len(resp.json()) == 1
        assert resp.json()[0]["company_name"] == "B的公司"

        # B 不能直接访问 A 的岗位
        resp = client.get(f"/jobs/{job_a_id}", headers=headers_b)
        assert resp.status_code == 403

        # B 不能修改 A 的岗位
        resp = client.put(f"/jobs/{job_a_id}", json={
            "title": "被B改了",
        }, headers=headers_b)
        assert resp.status_code == 403

        # B 不能删除 A 的岗位
        resp = client.delete(f"/jobs/{job_a_id}", headers=headers_b)
        assert resp.status_code == 403

        # B 不能给 A 的岗位创建投递
        resp = client.post("/applications", json={
            "job_id": job_a_id,
        }, headers=headers_b)
        assert resp.status_code == 403

        # Dashboard 统计各自独立
        resp_a = client.get("/stats/summary", headers=headers_a)
        resp_b = client.get("/stats/summary", headers=headers_b)
        assert resp_a.json()["total_jobs"] == 1
        assert resp_b.json()["total_jobs"] == 1


class TestErrorHandling:
    """测试统一的错误格式"""

    def test_validation_error_format(self, client):
        """422 错误格式应该包含 detail 字段"""
        resp = client.post("/auth/register", json={
            "email": "bad-email",
            "password": "123456",
        })
        assert resp.status_code == 422
        assert "detail" in resp.json()

    def test_unauthorized_format(self, client):
        """401 错误格式应该包含 detail 字段"""
        resp = client.get("/jobs")
        assert resp.status_code == 401
        assert "detail" in resp.json()

    def test_not_found_format(self, client):
        """404 错误格式应该包含 detail 字段（需要先登录）"""
        client.post("/auth/register", json={
            "email": "error_test@test.com", "password": "123456",
        })
        token = client.post("/auth/login", json={
            "email": "error_test@test.com", "password": "123456",
        }).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        resp = client.get("/jobs/99999", headers=headers)
        assert resp.status_code == 404
        assert "detail" in resp.json()

    def test_conflict_format(self, client):
        """409 错误格式应该包含 detail 字段"""
        client.post("/auth/register", json={
            "email": "conflict_test@test.com", "password": "123456",
        })
        resp = client.post("/auth/register", json={
            "email": "conflict_test@test.com", "password": "123456",
        })
        assert resp.status_code == 409
        assert "detail" in resp.json()
