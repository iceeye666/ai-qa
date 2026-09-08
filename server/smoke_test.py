"""全链路冒烟测试：不依赖真实网络，直接走 ASGI TestClient。

覆盖：健康检查 -> 登录鉴权 -> JWT 校验 -> 模型列表 -> 问答（Echo 兜底）
-> 会话记录 -> RBAC 权限（普通用户不能改模型）-> 未带 token 401。
运行： python smoke_test.py
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
client.__enter__()  # 进入 lifespan：建表 + 写入管理员与默认模型
BASE = "/api/v1"
ok, fail = 0, 0


def check(name, cond, extra=""):
    global ok, fail
    if cond:
        ok += 1
        print(f"  [PASS] {name} {extra}")
    else:
        fail += 1
        print(f"  [FAIL] {name} {extra}")


print("== 1. 健康检查 ==")
r = client.get("/health")
check("GET /health", r.status_code == 200, r.text)

print("== 2. 未登录访问受保护接口 ==")
r = client.get(f"{BASE}/conversations")
check("无 token 返回 401", r.status_code == 401, str(r.status_code))

print("== 3. 登录（OAuth2 密码模式）==")
r = client.post(f"{BASE}/auth/login", json={"username": "admin", "password": "wrong"})
check("错误密码 401", r.status_code == 401, str(r.status_code))

r = client.post(f"{BASE}/auth/login", json={"username": "admin", "password": "admin123"})
check("正确密码 200", r.status_code == 200, r.text[:120])
token = r.json().get("access_token", "")
assert token, "登录未返回 token"
headers = {"Authorization": f"Bearer {token}"}
check("返回角色 admin", r.json().get("role") == "admin")

print("== 4. 当前用户 ==")
r = client.get(f"{BASE}/auth/me", headers=headers)
check("GET /auth/me", r.status_code == 200 and r.json()["username"] == "admin", r.text[:120])

print("== 5. 模型列表（含种子数据）==")
r = client.get(f"{BASE}/models", headers=headers)
models = r.json()
check("模型列表非空", r.status_code == 200 and len(models) >= 5, f"共 {len(models)} 个")
check("含 qwen-plus", any(m["key"] == "qwen-plus" for m in models))

print("== 6. 问答（无 Key 自动降级 Echo）==")
r = client.post(f"{BASE}/chat", json={"message": "你好，介绍一下 JWT 认证"}, headers=headers)
data = r.json()
check("POST /chat 200", r.status_code == 200, r.text[:150])
check("有回答内容", bool(data.get("answer")), data.get("model_key", ""))
conv_id = data.get("conversation_id")

print("== 7. 多轮上下文 + 会话记录 ==")
r = client.post(
    f"{BASE}/chat",
    json={"message": "再说说模型怎么切换", "conversation_id": conv_id, "model_key": "echo-demo"},
    headers=headers,
)
check("第二轮问答", r.status_code == 200 and r.json()["conversation_id"] == conv_id)

r = client.get(f"{BASE}/conversations", headers=headers)
check("会话列表", r.status_code == 200 and len(r.json()) >= 1, f"共 {len(r.json())} 条")

r = client.get(f"{BASE}/conversations/{conv_id}", headers=headers)
detail = r.json()
check("会话详情含 4 条消息", r.status_code == 200 and len(detail["messages"]) == 4,
      f"实际 {len(detail.get('messages', []))}")

print("== 8. 模型 CRUD（管理员）==")
r = client.post(
    f"{BASE}/models",
    json={"key": "test-model", "name": "测试模型", "provider": "echo", "model_name": "test"},
    headers=headers,
)
check("新增模型 201", r.status_code == 201, r.text[:120])
model_id = r.json().get("id")
r = client.put(f"{BASE}/models/{model_id}", json={"description": "改过了"}, headers=headers)
check("修改模型 200", r.status_code == 200)
r = client.delete(f"{BASE}/models/{model_id}", headers=headers)
check("删除模型 204", r.status_code == 204, str(r.status_code))

print("== 9. RBAC：普通用户不能管理模型/用户 ==")
r = client.post(f"{BASE}/auth/register", json={"username": "tester001", "password": "test123456"})
check("注册普通用户 201", r.status_code in (200, 201), r.text[:120])
r = client.post(f"{BASE}/auth/login", json={"username": "tester001", "password": "test123456"})
user_headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
r = client.post(
    f"{BASE}/models",
    json={"key": "hack", "name": "hack", "provider": "echo"},
    headers=user_headers,
)
check("普通用户建模型 403", r.status_code == 403, str(r.status_code))
r = client.get(f"{BASE}/users", headers=user_headers)
check("普通用户看用户列表 403", r.status_code == 403, str(r.status_code))
r = client.get(f"{BASE}/models", headers=user_headers)
check("普通用户可看模型列表 200", r.status_code == 200)
r = client.get(f"{BASE}/conversations", headers=user_headers)
check("数据隔离：新用户无会话", r.status_code == 200 and len(r.json()) == 0)

print("== 10. 伪造 token ==")
r = client.get(f"{BASE}/auth/me", headers={"Authorization": "Bearer abc.def.ghi"})
check("伪造 token 401", r.status_code == 401, str(r.status_code))

print(f"\n结果：通过 {ok} 项，失败 {fail} 项")
raise SystemExit(1 if fail else 0)
