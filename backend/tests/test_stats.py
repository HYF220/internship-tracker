"""
测试文件：Dashboard 统计接口测试

测试 /stats/summary 的 SQL 聚合统计是否准确
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import Job, Application

# ==================== 测试数据库设置 ====================

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


@pytest.fixture()
def auth_client(client, db):
    """已登录客户端，返回 (client, headers, user_id)"""
    client.post("/auth/register", json={
        "email": "stats_test@example.com",
        "password": "123456",
    })
    login_resp = client.post("/auth/login", json={
        "email": "stats_test@example.com",
        "password": "123456",
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    me = client.get("/auth/me", headers=headers)
    user_id = me.json()["id"]
    return client, headers, user_id


# ==================== 统计测试 ====================

class TestStatsSummary:
    """测试 GET /stats/summary"""

    def test_stats_empty(self, auth_client):
        """新用户所有统计为 0"""
        client, headers, _ = auth_client
        response = client.get("/stats/summary", headers=headers)
        assert response.status_code == 200
        assert response.json() == {
            "total_jobs": 0,
            "total_applied": 0,
            "total_interview": 0,
            "total_offer": 0,
            "total_rejected": 0,
        }

    def test_stats_jobs_only(self, auth_client, db):
        """只有岗位时，岗位数正确，投递数为 0"""
        client, headers, user_id = auth_client

        for i in range(5):
            job = Job(user_id=user_id, company_name=f"公司{i}", title=f"岗位{i}")
            db.add(job)
        db.commit()

        response = client.get("/stats/summary", headers=headers)
        data = response.json()
        assert data["total_jobs"] == 5
        assert data["total_applied"] == 0

    def test_stats_mixed_statuses(self, auth_client, db):
        """有不同状态的投递时，统计完全正确"""
        client, headers, user_id = auth_client

        # 创建 4 个岗位
        jobs = []
        for i in range(4):
            job = Job(user_id=user_id, company_name=f"公司{i}", title=f"岗位{i}")
            db.add(job)
            db.commit()
            db.refresh(job)
            jobs.append(job)

        # 创建不同状态的投递（同一岗位可有多条投递记录）
        statuses = [
            ("applied", jobs[0].id),
            ("applied", jobs[1].id),
            ("interview", jobs[2].id),
            ("offer", jobs[0].id),
            ("rejected", jobs[3].id),
            ("rejected", jobs[3].id),
        ]
        for status, job_id in statuses:
            db.add(Application(job_id=job_id, status=status))
        db.commit()

        response = client.get("/stats/summary", headers=headers)
        data = response.json()
        assert data["total_jobs"] == 4
        assert data["total_applied"] == 2
        assert data["total_interview"] == 1
        assert data["total_offer"] == 1
        assert data["total_rejected"] == 2

    def test_stats_user_isolation(self, auth_client, db):
        """只统计自己的数据，不包含别人的"""
        client, headers, user_id = auth_client

        # 自己的：2 个岗位
        for i in range(2):
            db.add(Job(user_id=user_id, company_name=f"我的{i}", title=f"岗位{i}"))
        db.commit()

        # 别人的：10 个岗位
        for i in range(10):
            db.add(Job(user_id=99999, company_name=f"别人的{i}", title=f"岗位{i}"))
        db.commit()

        response = client.get("/stats/summary", headers=headers)
        data = response.json()
        # 只统计自己的
        assert data["total_jobs"] == 2

    def test_stats_no_token(self, client):
        """未登录访问返回 401"""
        response = client.get("/stats/summary")
        assert response.status_code == 401
