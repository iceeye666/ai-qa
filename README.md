# 基于 FastAPI + Vue 的前后端分离 AI 智能问答平台

面向中小企业 / 开发者的轻量化 AI 问答系统，聚焦 **安全认证 + 灵活模型调用 + 友好交互** 三大目标。

```
ai-qa/
├── server/          # FastAPI 后端（RESTful + JWT + 可插拔模型层）
│   ├── app/
│   │   ├── main.py            # 应用入口、CORS、Swagger、lifespan 初始化
│   │   ├── core/              # config / security(JWT) / deps(鉴权依赖)
│   │   ├── db/                # 引擎会话、建表与种子数据
│   │   ├── models/            # User / Conversation / Message / ModelConfig
│   │   ├── schemas/           # Pydantic 请求响应模型
│   │   ├── api/v1/endpoints/  # auth / chat / conversations / models / users
│   │   └── services/
│   │       ├── chat_service.py        # 问答编排（上下文、模型选择、落库）
│   │       └── providers/             # ★ 可插拔模型适配层
│   │           ├── base.py            # 统一抽象 BaseProvider
│   │           ├── openai_compatible.py # Qwen / OpenAI / ChatGLM 共用
│   │           ├── echo.py            # 内置演示模型（无需 Key）
│   │           └── registry.py        # 适配器注册表 + 工厂
│   ├── smoke_test.py          # 22 项全链路冒烟测试
│   └── requirements.txt
└── web/             # Vue 3 + Vite 前端
    └── src/
        ├── api/        # axios 实例（自动携带 JWT、401 自动登出）
        ├── router/     # 路由 + 守卫（未登录拦截、管理员页面鉴权）
        ├── stores/     # Pinia 用户态
        └── views/      # 登录页 / 问答页 / 模型配置页 / 用户管理页
```

## 一、快速启动

### 1. 后端

```bash
cd server
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # 可选：填入 QWEN_API_KEY 等
uvicorn app.main:app --reload --port 8000
```

启动后访问：

- Swagger 交互文档：<http://127.0.0.1:8000/docs>
- ReDoc：<http://127.0.0.1:8000/redoc>
- 健康检查：<http://127.0.0.1:8000/health>

首次启动自动建表并写入种子数据，默认管理员：**admin / admin123**。

### 2. 前端

```bash
cd web
npm install
npm run dev        # http://localhost:5173
npm run build      # 产物在 web/dist，可直接丢 Nginx
```

开发态 Vite 已配置 `/api` 代理到 `http://127.0.0.1:8000`，无需额外配置跨域。

### 3. 一键启动（macOS / Linux）

```bash
./scripts/start.sh      # 同时拉起后端 8000 与前端 5173
./scripts/stop.sh       # 停止
```

## 二、四大核心设计

### 1. 前后端解耦

前端只通过 `/api/v1/**` 的 JSON 接口与后端通信，双方可独立开发、独立部署。
后端全部接口自带 Swagger 文档与 Pydantic 校验（字段错误返回 422 明细），前端 Axios 拦截器统一处理 token 注入与错误提示。

### 2. JWT + OAuth2 鉴权与 RBAC

| 环节 | 实现 |
| --- | --- |
| 登录 | `POST /api/v1/auth/login`，遵循 OAuth2 Password Flow（Swagger 右上角 Authorize 可直接用） |
| 签发 | JWT payload 含 `sub`(用户名) / `role`(角色) / `exp`，HS256 签名 |
| 校验 | `OAuth2PasswordBearer` 取 Bearer token → `get_current_user` 解析并查库 |
| 权限 | `get_current_active_admin` 依赖做角色拦截，普通用户调用管理接口返回 403 |
| 口令 | bcrypt 加盐哈希，明文密码不落库 |

角色矩阵：

| 能力 | 管理员 | 普通用户 |
| --- | :---: | :---: |
| 问答 / 会话管理 | ✅ | ✅（仅本人数据） |
| 查看模型列表 | ✅ | ✅ |
| 模型增删改 | ✅ | ❌ 403 |
| 用户管理 | ✅ | ❌ 403 |

### 3. 可插拔多模型适配

所有模型继承同一个抽象：

```python
class BaseProvider(ABC):
    async def generate(self, messages, temperature=0.7, **kw) -> ModelResult: ...
    async def stream_generate(self, messages, **kw) -> AsyncIterator[str]: ...
```

- **Qwen / OpenAI / ChatGLM** 均走 OpenAI 兼容协议 → 共用一个适配器，只改 `base_url` + `model_name`；
- **Echo** 内置演示模型无需任何 Key，未配置凭据时自动兜底，**保证项目 clone 下来就能跑通全链路**；
- 新增模型：写一个 `BaseProvider` 子类 + 在 `registry.PROVIDER_CLASSES` 注册一行，或在「模型配置」页新增记录，**问答主流程零改动**；
- 前端下拉框一键切换，后端 `resolve_model()` 负责选模型与降级。

### 4. 轻量化部署

- 后端：`uvicorn` 单进程即可跑，默认 SQLite 零配置（改 `DATABASE_URL` 即可切 MySQL）；
- 前端：`npm run build` 产出静态资源，Nginx `/api` 反向代理到后端（示例见 `deploy/nginx.conf`）；
- 依赖极简，无 Redis / 消息队列等重型组件。

## 三、接口清单

| 方法 | 路径 | 说明 | 权限 |
| --- | --- | --- | --- |
| POST | `/api/v1/auth/register` | 注册普通用户 | 公开 |
| POST | `/api/v1/auth/login` | 登录获取 JWT | 公开 |
| GET | `/api/v1/auth/me` | 当前用户信息 | 登录 |
| POST | `/api/v1/chat` | 问答（一次性返回） | 登录 |
| POST | `/api/v1/chat/stream` | 问答（SSE 流式） | 登录 |
| GET | `/api/v1/conversations` | 会话列表（含搜索） | 登录 |
| POST | `/api/v1/conversations` | 新建会话 | 登录 |
| GET | `/api/v1/conversations/{id}` | 会话详情（含消息） | 登录 |
| PATCH | `/api/v1/conversations/{id}` | 重命名会话 | 登录 |
| DELETE | `/api/v1/conversations/{id}` | 删除会话 | 登录 |
| GET | `/api/v1/models` | 可用模型列表 | 登录 |
| GET | `/api/v1/models/providers` | 支持的适配器 | 登录 |
| POST/PUT/DELETE | `/api/v1/models[/id]` | 模型增删改 | 管理员 |
| GET/POST/PUT/DELETE | `/api/v1/users[/id]` | 用户管理 | 管理员 |

## 四、测试

```bash
cd server
python smoke_test.py
```

覆盖 22 项：健康检查、未登录 401、错误口令 401、登录签发、JWT 解析、模型列表、
问答降级、多轮上下文、会话记录落库、模型 CRUD、RBAC 403、数据隔离、伪造 token 401。

当前结果：**22 项全部通过**。

## 五、接入真实大模型

方式一（推荐，不改代码）：用管理员登录 → 「模型配置」页编辑 `qwen-plus` → 填入 API Key → 保存。

方式二（环境变量）：

```bash
# server/.env
QWEN_API_KEY=sk-xxxxxx
DEFAULT_MODEL=qwen-plus
```

未配置 Key 时系统自动回退到内置 Echo 演示模型并在回答中提示，不影响功能演示。

## 六、注意事项

- 生产环境务必修改 `SECRET_KEY` 与默认管理员密码；
- `DATABASE_URL` 切换 MySQL 时需额外 `pip install pymysql cryptography`；
- 流式接口使用 SSE，Nginx 反代需关闭缓冲：`proxy_buffering off;`。
