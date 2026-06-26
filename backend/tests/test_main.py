"""
测试文件：测试 main.py 中的接口

测试是"自动检查代码是否正确"的方式。
每次改完代码，运行 pytest，它就会自动帮你检查。
"""

from fastapi.testclient import TestClient

# 从 app.main 模块导入 app 这个 FastAPI 实例
from app.main import app

# TestClient 是一个"模拟浏览器"
# 用它发请求，不需要真的启动服务器
client = TestClient(app)


def test_health_returns_ok():
    """测试：GET /health 应该返回 {"status": "ok"}"""
    response = client.get("/health")

    # 断言 HTTP 状态码是 200（表示成功）
    assert response.status_code == 200

    # 断言返回的 JSON 数据是我们期望的
    assert response.json() == {"status": "ok"}


def test_health_has_status_key():
    """测试：/health 的返回结果中必须包含 "status" 这个字段"""
    response = client.get("/health")

    data = response.json()

    # 断言 "status" 这个键存在
    assert "status" in data


def test_health_status_value_is_string():
    """测试：/health 返回的 status 值应该是字符串类型"""
    response = client.get("/health")

    data = response.json()

    # 断言 status 的值是字符串
    assert isinstance(data["status"], str)
