"""
测试文件：Resumes 简历上传测试

测试上传 PDF、拒绝非 PDF、查看简历列表。
"""

import io

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

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
def auth_client(client):
    """
    创建已登录的客户端。

    返回 (client, headers)
    """
    client.post("/auth/register", json={
        "email": "resume_test@example.com",
        "password": "123456",
    })
    login_resp = client.post("/auth/login", json={
        "email": "resume_test@example.com",
        "password": "123456",
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    return client, headers


def make_pdf_bytes():
    """
    创建一个最小但合法的 PDF 文件内容（bytes）。

    这样测试时不需要真的准备 PDF 文件。
    """
    pdf = b"""%PDF-1.4
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
    return pdf


# ==================== 上传测试 ====================

class TestUploadResume:
    """测试 POST /resumes/upload"""

    def test_upload_pdf_success(self, auth_client):
        """测试：上传 PDF 应该成功"""
        client, headers = auth_client

        pdf_bytes = make_pdf_bytes()
        response = client.post(
            "/resumes/upload",
            data={"name": "我的简历v1"},
            files={"file": ("resume.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
            headers=headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "我的简历v1"
        assert data["file_path"].startswith("uploads/")
        assert data["file_path"].endswith(".pdf")
        assert "id" in data

    def test_upload_pdf_uuid_filename(self, auth_client):
        """测试：上传的 PDF 文件名应该是 UUID（不是原始文件名）"""
        client, headers = auth_client

        pdf_bytes = make_pdf_bytes()
        response = client.post(
            "/resumes/upload",
            data={"name": "测试简历"},
            files={"file": ("my_original_name.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
            headers=headers,
        )

        data = response.json()
        # 文件名应该是 UUID + .pdf，不是原始文件名
        saved_name = data["file_path"].split("/")[-1]
        assert saved_name != "my_original_name.pdf"
        # UUID 格式：xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.pdf
        assert len(saved_name) == 36 + 4  # UUID(36) + .pdf(4)

    def test_upload_non_pdf_rejected(self, auth_client):
        """测试：上传非 PDF 文件应返回 400"""
        client, headers = auth_client

        text_bytes = b"This is a text file, not a PDF."
        response = client.post(
            "/resumes/upload",
            data={"name": "假的PDF"},
            files={"file": ("fake.pdf", io.BytesIO(text_bytes), "text/plain")},
            headers=headers,
        )

        assert response.status_code == 400
        assert "PDF" in response.json()["detail"]

    def test_upload_no_token(self, client):
        """测试：未登录上传应返回 401"""
        pdf_bytes = make_pdf_bytes()
        response = client.post(
            "/resumes/upload",
            data={"name": "未登录上传"},
            files={"file": ("resume.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        )
        assert response.status_code == 401


# ==================== 查询测试 ====================

class TestGetResumes:
    """测试 GET /resumes"""

    def test_list_empty(self, auth_client):
        """测试：新用户没有简历"""
        client, headers = auth_client
        response = client.get("/resumes", headers=headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_list_returns_own(self, auth_client):
        """测试：上传后列表能看到自己的简历"""
        client, headers = auth_client

        # 上传两份简历
        pdf_bytes = make_pdf_bytes()
        client.post("/resumes/upload", data={"name": "简历A"}, files={
            "file": ("a.pdf", io.BytesIO(pdf_bytes), "application/pdf"),
        }, headers=headers)

        client.post("/resumes/upload", data={"name": "简历B"}, files={
            "file": ("b.pdf", io.BytesIO(pdf_bytes), "application/pdf"),
        }, headers=headers)

        response = client.get("/resumes", headers=headers)
        data = response.json()
        assert len(data) == 2
        names = {r["name"] for r in data}
        assert names == {"简历A", "简历B"}

    def test_cannot_see_others_resumes(self, auth_client, db):
        """测试：看不到别人的简历"""
        client, headers = auth_client

        # 别人的简历（手动插入数据库）
        from app.models import Resume
        other_resume = Resume(
            user_id=99999,
            name="别人的简历",
            file_path="uploads/other.pdf",
        )
        db.add(other_resume)
        db.commit()

        # 当前用户只能看到自己的
        response = client.get("/resumes", headers=headers)
        data = response.json()
        assert len(data) == 0  # 看不到别人的
