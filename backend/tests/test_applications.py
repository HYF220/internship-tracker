"""
测试文件：Applications 投递流程测试

测试创建投递、查询投递、状态更新、流程流转。
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
    """提供 TestClient"""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture()
def auth_client(client, db):
    """
    创建已登录的客户端 + 一个自己的岗位。

    返回 (client, headers, my_job_id)
    """
    # 注册 + 登录
    client.post("/auth/register", json={
        "email": "app_test@example.com",
        "password": "123456",
    })
    login_resp = client.post("/auth/login", json={
        "email": "app_test@example.com",
        "password": "123456",
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 先获取当前用户 ID，再创建一个岗位
    me = client.get("/auth/me", headers=headers)
    user_id = me.json()["id"]

    job = Job(user_id=user_id, company_name="测试公司", title="测试岗位")
    db.add(job)
    db.commit()
    db.refresh(job)

    return client, headers, job.id


# ==================== 创建投递测试 ====================

class TestCreateApplication:
    """测试 POST /applications"""

    def test_create_application_basic(self, auth_client):
        """测试：为自己的岗位创建投递记录应该成功"""
        client, headers, job_id = auth_client

        response = client.post("/applications", json={
            "job_id": job_id,
            "status": "applied",
        }, headers=headers)

        assert response.status_code == 201
        data = response.json()
        assert data["job_id"] == job_id
        assert data["status"] == "applied"

    def test_create_application_default_status(self, auth_client):
        """测试：不传 status 时默认为 saved"""
        client, headers, job_id = auth_client

        response = client.post("/applications", json={
            "job_id": job_id,
        }, headers=headers)

        assert response.status_code == 201
        assert response.json()["status"] == "saved"

    def test_create_application_other_users_job(self, client, db):
        """测试：不能给别人的岗位创建投递"""
        # 注册用户 A
        client.post("/auth/register", json={
            "email": "user_a@test.com",
            "password": "123456",
        })
        token_a = client.post("/auth/login", json={
            "email": "user_a@test.com",
            "password": "123456",
        }).json()["access_token"]

        # 用户 A 创建一个岗位
        a_headers = {"Authorization": f"Bearer {token_a}"}
        job_resp = client.post("/jobs", json={
            "company_name": "A的公司", "title": "A的岗位"
        }, headers=a_headers)
        job_id = job_resp.json()["id"]

        # 注册用户 B
        client.post("/auth/register", json={
            "email": "user_b@test.com",
            "password": "123456",
        })
        token_b = client.post("/auth/login", json={
            "email": "user_b@test.com",
            "password": "123456",
        }).json()["access_token"]

        # 用户 B 尝试给 A 的岗位创建投递 → 应被拒绝
        b_headers = {"Authorization": f"Bearer {token_b}"}
        response = client.post("/applications", json={
            "job_id": job_id,
        }, headers=b_headers)

        assert response.status_code == 403

    def test_create_application_invalid_status(self, auth_client):
        """测试：传无效状态值应返回 422"""
        client, headers, job_id = auth_client

        response = client.post("/applications", json={
            "job_id": job_id,
            "status": "invalid_status",
        }, headers=headers)

        assert response.status_code == 422

    def test_create_application_no_token(self, client):
        """测试：未登录创建投递应返回 401"""
        response = client.post("/applications", json={
            "job_id": 1,
        })
        assert response.status_code == 401


# ==================== 查询投递测试 ====================

class TestGetApplications:
    """测试 GET /applications"""

    def test_list_empty(self, auth_client):
        """测试：新用户没有投递记录"""
        client, headers, _ = auth_client
        response = client.get("/applications", headers=headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_list_only_own(self, auth_client, db):
        """测试：只返回自己的投递，不返回别人的"""
        client, headers, my_job_id = auth_client

        # 当前用户创建一条投递
        client.post("/applications", json={
            "job_id": my_job_id, "status": "applied"
        }, headers=headers)

        # 别人的岗位
        other_job = Job(user_id=99999, company_name="别人的", title="别人的岗位")
        db.add(other_job)
        db.commit()
        db.refresh(other_job)

        # 手动创建别人岗位上的投递
        from app.models import Application
        other_app = Application(job_id=other_job.id, status="applied")
        db.add(other_app)
        db.commit()

        # 当前用户只能看到自己的投递
        response = client.get("/applications", headers=headers)
        data = response.json()
        assert len(data) == 1
        assert data[0]["job_id"] == my_job_id


# ==================== 状态更新测试 ====================

class TestUpdateApplication:
    """测试 PUT /applications/{id}"""

    def test_update_status(self, auth_client):
        """测试：更新投递状态"""
        client, headers, job_id = auth_client

        # 创建投递
        app_resp = client.post("/applications", json={
            "job_id": job_id, "status": "saved"
        }, headers=headers)
        app_id = app_resp.json()["id"]

        # 更新状态
        response = client.put(f"/applications/{app_id}", json={
            "status": "applied",
            "applied_at": "2026-07-01T10:00:00",
        }, headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "applied"
        assert data["applied_at"] is not None

    def test_cannot_update_others(self, auth_client, db):
        """测试：不能更新别人的投递"""
        client, headers, _ = auth_client

        # 别人岗位上的投递
        from app.models import Application
        other_job = Job(user_id=99999, company_name="别人的", title="别人的岗位")
        db.add(other_job)
        db.commit()
        db.refresh(other_job)

        other_app = Application(job_id=other_job.id, status="saved")
        db.add(other_app)
        db.commit()
        db.refresh(other_app)

        response = client.put(f"/applications/{other_app.id}", json={
            "status": "applied",
        }, headers=headers)

        assert response.status_code == 403

    def test_update_not_found(self, auth_client):
        """测试：更新不存在的投递返回 404"""
        client, headers, _ = auth_client
        resp = client.put("/applications/99999", json={
            "status": "applied",
        }, headers=headers)
        assert resp.status_code == 404

    def test_update_invalid_status(self, auth_client):
        """测试：更新为无效状态返回 422"""
        client, headers, job_id = auth_client

        app_resp = client.post("/applications", json={
            "job_id": job_id,
        }, headers=headers)
        app_id = app_resp.json()["id"]

        resp = client.put(f"/applications/{app_id}", json={
            "status": "hired",  # 不在枚举中
        }, headers=headers)
        assert resp.status_code == 422


# ==================== 流程流转测试 ====================

class TestApplicationFlow:
    """
    测试完整的投递流程：
    saved → applied → oa → interview → offer
    """

    def test_full_flow(self, auth_client):
        """测试：完整投递流程的每一个状态转换"""
        client, headers, job_id = auth_client

        # 1. 创建投递（默认 saved）
        app_resp = client.post("/applications", json={
            "job_id": job_id,
        }, headers=headers)
        app_id = app_resp.json()["id"]
        assert app_resp.json()["status"] == "saved"

        # 2. saved → applied（投递简历）
        resp = client.put(f"/applications/{app_id}", json={
            "status": "applied",
        }, headers=headers)
        assert resp.json()["status"] == "applied"

        # 3. applied → oa（收到在线测评）
        resp = client.put(f"/applications/{app_id}", json={
            "status": "oa",
        }, headers=headers)
        assert resp.json()["status"] == "oa"

        # 4. oa → interview（进入面试）
        resp = client.put(f"/applications/{app_id}", json={
            "status": "interview",
            "interview_date": "2026-07-15T14:00:00",
        }, headers=headers)
        assert resp.json()["status"] == "interview"
        assert resp.json()["interview_date"] is not None

        # 5. interview → offer（拿到 offer！）
        resp = client.put(f"/applications/{app_id}", json={
            "status": "offer",
            "notes": "薪资满意，准备接受",
        }, headers=headers)
        assert resp.json()["status"] == "offer"
        assert resp.json()["notes"] == "薪资满意，准备接受"

        # 验证最终状态
        app_resp = client.get("/applications", headers=headers)
        assert app_resp.json()[0]["status"] == "offer"

    def test_rejected_flow(self, auth_client):
        """测试：被拒绝的流程"""
        client, headers, job_id = auth_client

        # 创建 → 投递 → 被拒
        app_resp = client.post("/applications", json={
            "job_id": job_id,
        }, headers=headers)
        app_id = app_resp.json()["id"]

        client.put(f"/applications/{app_id}", json={
            "status": "applied",
        }, headers=headers)

        client.put(f"/applications/{app_id}", json={
            "status": "rejected",
            "notes": "岗位已招满",
        }, headers=headers)

        final = client.get("/applications", headers=headers)
        assert final.json()[0]["status"] == "rejected"

    def test_withdrawn_flow(self, auth_client):
        """测试：主动放弃的流程"""
        client, headers, job_id = auth_client

        app_resp = client.post("/applications", json={
            "job_id": job_id,
        }, headers=headers)
        app_id = app_resp.json()["id"]

        client.put(f"/applications/{app_id}", json={
            "status": "applied",
        }, headers=headers)

        # 主动撤回
        client.put(f"/applications/{app_id}", json={
            "status": "withdrawn",
        }, headers=headers)

        final = client.get("/applications", headers=headers)
        assert final.json()[0]["status"] == "withdrawn"
