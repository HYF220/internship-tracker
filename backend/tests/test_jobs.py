"""
测试文件：Jobs CRUD 接口测试（需登录）

测试所有岗位接口，每个请求都带 JWT token。
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import Job

# ==================== 测试数据库设置 ====================

TEST_DATABASE_URL = "postgresql://postgres@localhost:5433/internship_tracker"
test_engine = create_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)

Base.metadata.create_all(bind=test_engine)


@pytest.fixture()
def db():
    """每个测试独立的数据库会话（事务回滚）"""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db):
    """提供 TestClient，使用测试数据库"""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture()
def auth_client(client):
    """
    创建一个"已经登录的"客户端。

    自动注册一个用户，登录获取 token，
    后续请求自动带上 Authorization 头。
    """
    # 注册
    client.post("/auth/register", json={
        "email": "jobs_test@example.com",
        "password": "123456",
    })
    # 登录获取 token
    login_resp = client.post("/auth/login", json={
        "email": "jobs_test@example.com",
        "password": "123456",
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    return client, headers


# ==================== 创建岗位测试 ====================

class TestCreateJob:
    """测试 POST /jobs（需登录）"""

    def test_create_job_basic(self, auth_client):
        """测试：登录后创建岗位成功（不需要传 user_id）"""
        client, headers = auth_client

        response = client.post("/jobs", json={
            "company_name": "测试公司",
            "title": "测试岗位",
        }, headers=headers)

        assert response.status_code == 201
        data = response.json()
        assert data["company_name"] == "测试公司"
        assert data["title"] == "测试岗位"
        assert data["id"] is not None
        assert data["status"] == "saved"
        assert "created_at" in data
        # user_id 应该被自动填入
        assert data["user_id"] is not None

    def test_create_job_with_all_fields(self, auth_client):
        """测试：创建岗位时填写所有可选字段"""
        client, headers = auth_client

        response = client.post("/jobs", json={
            "company_name": "字节跳动",
            "title": "前端开发实习生",
            "location": "北京",
            "job_url": "https://example.com/job/1",
            "jd_text": "负责前端开发...",
            "salary_range": "15k-25k",
            "status": "applied",
        }, headers=headers)

        assert response.status_code == 201
        data = response.json()
        assert data["location"] == "北京"
        assert data["salary_range"] == "15k-25k"

    def test_create_job_no_token(self, client):
        """测试：未登录创建岗位应返回 401"""
        response = client.post("/jobs", json={
            "company_name": "某公司",
            "title": "某岗位",
        })
        assert response.status_code == 401

    def test_create_job_missing_required_field(self, auth_client):
        """测试：缺少必填字段应返回 422"""
        client, headers = auth_client

        response = client.post("/jobs", json={
            "title": "测试岗位",
            # 缺少 company_name
        }, headers=headers)

        assert response.status_code == 422


# ==================== 查询岗位测试 ====================

class TestGetJobs:
    """测试 GET /jobs（需登录，只能看自己的）"""

    def test_list_jobs_empty(self, auth_client):
        """测试：新用户没有岗位，返回空列表"""
        client, headers = auth_client
        response = client.get("/jobs", headers=headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_list_jobs_only_own(self, auth_client, db):
        """测试：只能看到自己的岗位，看不到别人的"""
        client, headers = auth_client

        # 获取当前登录用户的 ID
        me = client.get("/auth/me", headers=headers)
        my_user_id = me.json()["id"]

        # 手动创建：1 个自己的，1 个别人的
        my_job = Job(user_id=my_user_id, company_name="我的", title="我的岗位")
        other_job = Job(user_id=99999, company_name="别人的", title="别人的岗位")
        db.add(my_job)
        db.add(other_job)
        db.commit()

        response = client.get("/jobs", headers=headers)
        data = response.json()
        assert len(data) == 1
        assert data[0]["company_name"] == "我的"

    def test_cannot_access_others_job(self, auth_client, db):
        """测试：尝试查看别人的岗位详情应返回 403"""
        client, headers = auth_client

        # 创建别人（user_id=99999）的岗位
        other_job = Job(user_id=99999, company_name="别人的", title="别人的岗位")
        db.add(other_job)
        db.commit()
        db.refresh(other_job)

        response = client.get(f"/jobs/{other_job.id}", headers=headers)
        assert response.status_code == 403  # Forbidden


class TestGetSingleJob:
    """测试 GET /jobs/{id}（需登录）"""

    def test_get_job_found(self, auth_client, db):
        """测试：自己的岗位能被查到"""
        client, headers = auth_client

        me = client.get("/auth/me", headers=headers)
        my_id = me.json()["id"]

        job = Job(user_id=my_id, company_name="找到我", title="测试")
        db.add(job)
        db.commit()
        db.refresh(job)

        response = client.get(f"/jobs/{job.id}", headers=headers)
        assert response.status_code == 200
        assert response.json()["company_name"] == "找到我"

    def test_get_job_not_found(self, auth_client):
        """测试：查询不存在的岗位返回 404"""
        client, headers = auth_client
        response = client.get("/jobs/99999", headers=headers)
        assert response.status_code == 404


# ==================== 更新岗位测试 ====================

class TestUpdateJob:
    """测试 PUT /jobs/{id}"""

    def test_update_job_success(self, auth_client):
        """测试：正常更新岗位"""
        client, headers = auth_client

        # 先创建一个岗位
        resp = client.post("/jobs", json={
            "company_name": "旧名称", "title": "旧标题",
        }, headers=headers)
        job_id = resp.json()["id"]

        # 更新
        resp = client.put(f"/jobs/{job_id}", json={
            "company_name": "新名称",
            "title": "新标题",
            "location": "上海",
            "salary_range": "30k-40k",
        }, headers=headers)

        assert resp.status_code == 200
        data = resp.json()
        assert data["company_name"] == "新名称"
        assert data["title"] == "新标题"
        assert data["location"] == "上海"
        assert data["salary_range"] == "30k-40k"
        # 没改的字段保持不变
        assert data["status"] == "saved"

    def test_update_job_partial(self, auth_client):
        """测试：部分更新（只传 title，其他不变）"""
        client, headers = auth_client

        resp = client.post("/jobs", json={
            "company_name": "公司", "title": "原标题",
        }, headers=headers)
        job_id = resp.json()["id"]

        # 只更新 title
        resp = client.put(f"/jobs/{job_id}", json={
            "title": "新标题",
        }, headers=headers)

        assert resp.status_code == 200
        assert resp.json()["title"] == "新标题"
        assert resp.json()["company_name"] == "公司"  # 没变

    def test_update_job_not_found(self, auth_client):
        """测试：更新不存在的岗位返回 404"""
        client, headers = auth_client
        resp = client.put("/jobs/99999", json={"title": "x"}, headers=headers)
        assert resp.status_code == 404

    def test_update_job_other_user(self, auth_client, db):
        """测试：不能更新别人的岗位"""
        client, headers = auth_client

        # 别人的岗位
        from app.models import Job
        other_job = Job(user_id=99999, company_name="别人的", title="别人的")
        db.add(other_job)
        db.commit()
        db.refresh(other_job)

        resp = client.put(f"/jobs/{other_job.id}", json={
            "title": "被我改了",
        }, headers=headers)

        assert resp.status_code == 403


# ==================== 删除岗位测试 ====================

class TestDeleteJob:
    """测试 DELETE /jobs/{id}"""

    def test_delete_job_success(self, auth_client):
        """测试：正常删除岗位"""
        client, headers = auth_client

        resp = client.post("/jobs", json={
            "company_name": "待删除", "title": "测试",
        }, headers=headers)
        job_id = resp.json()["id"]

        resp = client.delete(f"/jobs/{job_id}", headers=headers)
        assert resp.status_code == 204

        # 确认已删除
        resp = client.get(f"/jobs/{job_id}", headers=headers)
        assert resp.status_code == 404

    def test_delete_job_not_found(self, auth_client):
        """测试：删除不存在的岗位返回 404"""
        client, headers = auth_client
        resp = client.delete("/jobs/99999", headers=headers)
        assert resp.status_code == 404

    def test_delete_job_other_user(self, auth_client, db):
        """测试：不能删除别人的岗位"""
        client, headers = auth_client

        from app.models import Job
        other_job = Job(user_id=99999, company_name="别人的", title="别人的")
        db.add(other_job)
        db.commit()
        db.refresh(other_job)

        resp = client.delete(f"/jobs/{other_job.id}", headers=headers)
        assert resp.status_code == 403

    def test_delete_job_with_applications(self, auth_client, db):
        """测试：有投递记录的岗位不能删除（409 FK 保护）"""
        client, headers = auth_client

        # 创建岗位
        resp = client.post("/jobs", json={
            "company_name": "有投递的岗位", "title": "测试",
        }, headers=headers)
        job_id = resp.json()["id"]

        # 创建关联的投递记录
        from app.models import Application
        app = Application(job_id=job_id, status="applied")
        db.add(app)
        db.commit()

        # 尝试删除 → 409
        resp = client.delete(f"/jobs/{job_id}", headers=headers)
        assert resp.status_code == 409
        assert "投递" in resp.json()["detail"]
