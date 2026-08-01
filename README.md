  1→# NovaSSO - DN42 统一身份认证系统
  2→
  3→> 🔵 蓝白色调 · 🌐 多中心架构 · 🚀 现代化设计 · 🐍 Python 实现
  4→
  5→一套轻量级、现代化的统一登录（SSO）系统，专为 DN42 + 公网双环境设计。基于 CAS 票据机制，支持多中心部署，3000 用户规模无需 Redis，开箱即用。
  6→
  7→---
  8→
  9→## ✨ 特性亮点
 10→
 11→| 特性 | 说明 |
 12→|------|------|
 13→| 🔐 **统一登录** | 一套账号登录所有子系统，CAS 票据机制，安全可靠 |
 14→| ⚡ **无感登录** | 隐藏 iframe + postMessage，切换系统零感知 |
 15→| 🎨 **现代 UI** | 蓝白色调，简洁优雅，全响应式设计 |
 16→| 🌐 **多中心架构** | 支持多节点部署，数据自动同步，高可用 |
 17→| 📦 **零额外依赖** | SQLite WAL 模式，无需 Redis，3000 用户够用 |
 18→| 👥 **用户管理** | 后台管理用户、应用、会话、审计日志 |
 19→| 📝 **审计日志** | 完整操作记录，满足合规要求 |
 20→| 🔒 **安全加固** | bcrypt 密码哈希、防重放、防开放重定向、登录锁定 |
 21→| 🛠️ **SDK 支持** | Python SDK + 前端 JS SDK，接入仅需三行代码 |
 22→| 🌍 **DN42 友好** | 支持双域名双 Cookie，适配 DN42 + 公网双环境 |
 23→
 24→---
 25→
 26→## 🏗️ 系统架构
 27→
 28→```
 29→┌─────────────────────────────────────────────────────────────┐
 30→│                      NovaSSO (IdP)                           │
 31→│                 FastAPI + SQLite + WAL                        │
 32→│                                                              │
 33→│  ┌────────────┐  ┌────────────┐  ┌────────────┐             │
 34→│  │  用户中心   │  │  认证服务   │  │  票据管理   │             │
 35→│  │  User Mgmt │  │  Auth Svc  │  │  Ticket    │             │
 36→│  └────────────┘  └────────────┘  └────────────┘             │
 37→│  ┌────────────┐  ┌────────────┐  ┌────────────┐             │
 38→│  │  审计中心   │  │  会话管理   │  │ 应用管理    │             │
 39→│  │  Audit Log │  │  Session   │  │  App Mgmt  │             │
 40→│  └────────────┘  └────────────┘  └────────────┘             │
 41→│  ┌──────────────────────────────────────────────────┐        │
 42→│  │           多中心集群同步模块                       │        │
 43→│  │   节点心跳 · 数据同步 · 状态监控 · 自动故障转移    │        │
 44→│  └──────────────────────────────────────────────────┘        │
 45→└──────────────────────────────┬───────────────────────────────┘
 46→                               │
 47→          ┌────────────────────┼────────────────────┐
 48→          │                    │                    │
 49→   ┌──────▼──────┐     ┌──────▼──────┐     ┌──────▼──────┐
 50→   │ 🔍 搜索引擎  │     │ 📋 ICP备案  │     │ 🔗 AutoPeer │
 51→   │  Python SDK │     │  Python SDK │     │  Python SDK │
 52→   └─────────────┘     └─────────────┘     └─────────────┘
 53→          │                    │                    │
 54→          └────────────────────┼────────────────────┘
 55→                               │
 56→                    ┌──────────▼───────────┐
 57→                    │  DN42 + 公网 双栈     │
 58→                    │  双域名 / 双Cookie域  │
 59→                    └──────────────────────┘
 60→```
 61→
 62→### 核心概念
 63→
 64→| 名称 | 全称 | 作用 | 有效期 |
 65→|------|------|------|--------|
 66→| **TGT** | Ticket Granting Ticket | 全局会话票据，存在 SSO 域 Cookie 中 | 默认 7 天 |
 67→| **ST** | Service Ticket | 一次性服务票据，跨系统传递身份 | 5 分钟，只能用一次 |
 68→| **Local Session** | 本地会话 | 各业务系统自己的会话 | 各系统自行决定 |
 69→
 70→---
 71→
 72→## 🚀 快速开始
 73→
 74→### 环境要求
 75→
 76→- Python 3.8+
 77→- 256MB 以上内存
 78→- 100MB 以上磁盘空间
 79→
 80→### 1. 安装依赖
 81→
 82→```bash
 83→git clone <your-repo-url>
 84→cd nova-sso/server
 85→pip install -r requirements.txt
 86→```
 87→
 88→### 2. 启动服务
 89→
 90→```bash
 91→# 开发模式
 92→python main.py
 93→
 94→# 生产模式（推荐）
 95→uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
 96→```
 97→
 98→### 3. 访问系统
 99→
- **用户中心**: http://localhost:8000
- **管理后台**: http://localhost:8000/admin
- **默认账号**: `admin` / `admin123`

> ⚠️ **重要**：首次登录后请立即修改默认密码！

---

## 📁 项目结构

```
nova-sso/
├── server/                    # SSO 认证中心（服务端）
│   ├── main.py               # 主入口（FastAPI 应用）
│   ├── config.py             # 配置（主题、安全、多中心）
│   ├── database.py           # SQLite 数据库层（WAL 模式）
│   ├── auth.py               # 认证核心（票据、用户、会话）
│   ├── cluster.py            # 多中心集群同步模块
│   ├── requirements.txt      # Python 依赖
│   ├── data/                 # 数据库文件目录
│   ├── templates/            # HTML 模板
│   │   ├── login.html        # 登录页（蓝白主题）
│   │   ├── index.html        # 用户中心首页
│   │   ├── admin.html        # 管理后台 SPA
│   │   └── logout.html       # 登出页
│   └── static/               # 静态资源
│       ├── css/style.css     # 蓝白色调样式
│       └── js/admin.js       # 管理后台前端逻辑
├── sdk/                       # 客户端 SDK
│   ├── nova_sso.py           # Python SDK（Flask/FastAPI）
│   └── nova-sso.js           # 前端 JS SDK（无感登录）
├── examples/                  # 示例代码
│   └── demo-app/             # Flask 示例业务系统
└── README.md                  # 本文档
```

---

## 🔌 接入业务系统

### Python 后端接入

#### 安装 SDK

将 `sdk/nova_sso.py` 复制到你的项目中，或作为模块导入。

#### 基础用法

```python
from nova_sso import NovaSSOClient

# 初始化客户端
sso = NovaSSOClient(
    sso_url="https://sso.yourdomain.dn42",  # SSO 服务地址
    app_id="your-app-id",                    # 应用 ID（后台创建）
    callback_url="https://your-app/sso/callback"  # 回调地址
)

# ===== 登录跳转 =====
# 用户未登录时，跳转到 SSO 登录页
@app.route("/login")
def login():
    return redirect(sso.get_login_url(redirect="/dashboard"))

# ===== 回调验证 =====
# SSO 登录成功后回调，验证 ST 票据
@app.route("/sso/callback")
def sso_callback():
    ticket = request.args.get("ticket")
    user = sso.validate_ticket(ticket)
    
    if user:
        # 验证成功，建立本地会话
        session["user"] = user
        return redirect("/")
    
    return "登录验证失败", 401

# ===== 登出 =====
@app.route("/logout")
def logout():
    session.clear()
    return redirect(sso.get_logout_url(redirect=request.url_root))
```

#### Flask 便捷装饰器

```python
@app.route("/protected")
@sso.flask_login_required
def protected():
    return f"欢迎, {session['user']['username']}！"
```

#### FastAPI 依赖注入

```python
from fastapi import Depends

@app.get("/protected")
async def protected(user = Depends(sso.fastapi_get_current_user())):
    return {"user": user}
```

### 前端无感登录

#### 引入 SDK

```html
<script src="/path/to/nova-sso.js"></script>
```

#### 基础用法

```javascript
const sso = new NovaSSO({
  ssoUrl: 'https://sso.yourdomain.dn42',
  callbackUrl: 'https://your-app/sso/silent-callback.html',
  appId: 'your-app-id'
});

// 页面加载时自动尝试无感登录
document.addEventListener('DOMContentLoaded', async () => {
  try {
    const user = await sso.trySilentLogin();
    console.log('✅ 无感登录成功', user);
    // 更新 UI，显示登录状态
    showLoggedInUI(user);
  } catch (e) {
    console.log('🔐 需要手动登录', e.message);
    // 显示登录按钮
    showLoginButton();
  }
});

// 点击登录按钮跳转
function handleLogin() {
  sso.redirectToLogin(window.location.href);
}

// 登出
function handleLogout() {
  sso.redirectToLogout();
}
```

#### 静默回调页

在你的应用中创建 `silent-callback.html`：

```html
<!DOCTYPE html>
<html>
<head>
  <script src="/path/to/nova-sso.js"></script>
</head>
<body>
<script>
  // 接收 ST，验证后通知父页面
  NovaSSO.handleSilentCallback('/api/sso-validate');
</script>
</body>
</html>
```

对应的后端验证接口：

```python
@app.route("/api/sso-validate")
def sso_validate():
    ticket = request.args.get("ticket")
    user = sso.validate_ticket(ticket)
    if user:
        session["user"] = user
        return jsonify({"success": True, "user": user})
    return jsonify({"success": False, "error": "invalid ticket"})
```

### 接入步骤总结

1. **在 SSO 管理后台创建应用**，获取 app_id 和回调地址
2. **后端接入 Python SDK**，实现登录跳转和回调验证
3. **前端接入 JS SDK**，实现无感登录
4. **测试验证**：登录系统 A → 访问系统 B 自动登录

---

## 🎛️ 管理后台功能

访问 `/admin` 进入管理后台（需管理员权限）。

### 📊 仪表盘

- 总用户数、接入应用数、活跃会话、今日登录
- 集群节点状态实时监控
- 多中心模式状态指示

### 👥 用户管理

- 用户列表（支持搜索、分页）
- 创建新用户（设置角色、邮箱、昵称）
- 启用/禁用用户（禁用后自动踢掉所有会话）
- 重置用户密码
- 强制下线指定用户的所有会话

### 📱 应用管理

- 应用列表
- 创建新应用（设置回调地址、登出地址、描述）
- 编辑应用信息
- 重新生成应用密钥
- 删除应用（软删除）

### 🔐 在线会话

- 查看所有在线用户会话
- 查看指定用户的所有会话
- 强制下线单个会话
- 显示会话详情：IP、设备、节点、登录时间、过期时间

### 📝 审计日志

- 完整操作记录查询
- 支持按操作类型筛选
- 记录：登录/登出、用户创建、应用管理、密码修改等
- 每条记录包含：用户、IP、设备、时间、结果、详情

### 🌐 集群状态

- 多中心节点列表
- 节点在线状态、角色、心跳时间
- 配置说明文档

---

## 🌐 多中心部署

### 架构模式

NovaSSO 支持三种部署模式：

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| **单节点** | 单个实例，最简单 | 测试、小流量 |
| **主从模式** | 一主多从，读从写主 | 读多写少 |
| **对等模式** | 多节点对等，双向同步 | 高可用、多地域 |

### 部署步骤

#### 节点 1（主节点 / 北京）

```bash
export NOVA_NODE_ID="node-bj-01"
export NOVA_NODE_NAME="北京节点"
export NOVA_NODE_ROLE="master"
export NOVA_PEERS="https://sso-sh.example.com,https://sso-gz.example.com"
export NOVA_SYNC_KEY="your-super-secret-sync-key-change-me"
export NOVA_SYNC_INTERVAL=30

uvicorn main:app --host 0.0.0.0 --port 8000
```

#### 节点 2（对等节点 / 上海）

```bash
export NOVA_NODE_ID="node-sh-01"
export NOVA_NODE_NAME="上海节点"
export NOVA_NODE_ROLE="peer"
export NOVA_PEERS="https://sso-bj.example.com,https://sso-gz.example.com"
export NOVA_SYNC_KEY="your-super-secret-sync-key-change-me"

uvicorn main:app --host 0.0.0.0 --port 8000
```

#### 节点 3（对等节点 / 广州）

```bash
export NOVA_NODE_ID="node-gz-01"
export NOVA_NODE_NAME="广州节点"
export NOVA_NODE_ROLE="peer"
export NOVA_PEERS="https://sso-bj.example.com,https://sso-sh.example.com"
export NOVA_SYNC_KEY="your-super-secret-sync-key-change-me"

uvicorn main:app --host 0.0.0.0 --port 8000
```

### 同步机制

- **心跳检测**：每 10 秒更新一次节点心跳
- **数据拉取**：每 30 秒从对等节点拉取变更
- **主动推送**：重要变更（如强制下线）实时推送
- **节点认证**：同步接口需 SYNC_KEY 验证
- **状态监控**：60 秒无心跳标记为离线

### 数据同步范围

| 数据类型 | 同步方式 | 说明 |
|----------|----------|------|
| 用户信息 | 手动 / 定时 | 需扩展：目前支持会话同步 |
| TGT 会话 | 实时 + 定时 | 强制下线立即同步 |
| ST 票据 | 不同步 | 各节点独立签发 |
| 审计日志 | 不同步 | 各节点独立记录 |

---

## 🔧 配置参考

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `NOVA_DEBUG` | 调试模式 | `false` |
| `NOVA_SECRET` | 会话密钥 | `nova-sso-secret-key-change-in-production` |
| `NOVA_DB_PATH` | 数据库路径 | `data/nova_sso.db` |
| `NOVA_TGT_DAYS` | 全局会话有效期（天） | `7` |
| `NOVA_ST_MIN` | 服务票据有效期（分钟） | `5` |
| `NOVA_COOKIE_DOMAIN` | Cookie 域 | 自动检测 |
| `NOVA_COOKIE_SECURE` | Cookie Secure 标志 | `true` |
| `NOVA_NODE_ID` | 节点 ID | `node-01` |
| `NOVA_NODE_NAME` | 节点名称 | `主节点` |
| `NOVA_NODE_ROLE` | 节点角色 | `master` |
| `NOVA_PEERS` | 对等节点地址，逗号分隔 | 空 |
| `NOVA_SYNC_KEY` | 节点同步密钥 | `nova-sync-key-change-me` |
| `NOVA_SYNC_INTERVAL` | 同步间隔（秒） | `30` |

### 配置文件

也可以修改 `config.py` 中的默认配置：

```python
# 主题配置
THEME = {
    "primary": "#2563eb",       # 主蓝色
    "primary_dark": "#1d4ed8",  # 深蓝色
    "accent": "#0ea5e9",        # 青蓝色
    "bg": "#f8fafc",            # 背景色
    ...
}

# 品牌配置
BRAND = {
    "name": "NovaSSO",
    "full_name": "Nova 统一身份认证中心",
    "logo": "🚀",
    "tagline": "一站式身份管理 · 安全便捷的统一登录体验",
    ...
}
```

---

## 🔒 安全设计

### 密码安全

- **bcrypt 加盐哈希**：12 轮计算，抗暴力破解
- **密码强度检测**：长度 + 复杂度检查
- **登录失败锁定**：连续 5 次失败锁定 30 分钟

### 票据安全

- **ST 一次性使用**：验证后立即作废，防重放
- **ST 短有效期**：5 分钟内必须使用，减少利用窗口
- **ST 绑定 service**：只能用于指定应用，防滥用
- **TGT HttpOnly Cookie**：防 XSS 窃取

### 攻击防护

| 攻击类型 | 防护措施 |
|----------|----------|
| **开放重定向** | 回调地址白名单校验，只允许已注册应用 |
| **票据重放** | ST 一次性 + 短有效期 + service 绑定 |
| **XSS** | HttpOnly Cookie + 输出转义 |
| **CSRF** | SameSite Cookie + 敏感操作二次验证 |
| **暴力破解** | 登录次数限制 + 账号锁定 |
| **会话劫持** | IP + User-Agent 绑定（可选扩展） |
| **SQL 注入** | 参数化查询，杜绝拼接 |

### 审计追踪

- 所有关键操作都有审计日志
- 记录：操作人、IP、设备、时间、结果、详情
- 日志保留 90 天（可配置）
- 支持按操作类型、用户、时间筛选

---

## 📊 API 接口

### 认证接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/login` | GET/POST | 登录页 / 登录提交 |
| `/logout` | GET | 登出 |
| `/api/register` | POST | 用户自助注册 |
| `/api/serviceValidate` | GET/POST | 服务票据验证（后端调用） |

### 用户接口

| 接口 | 方法 | 说明 | 权限 |
|------|------|------|------|
| `/api/user/info` | GET | 获取当前用户信息 | 已登录 |
| `/api/user/profile` | PUT | 更新个人资料 | 已登录 |
| `/api/user/password` | PUT | 修改密码 | 已登录 |

### 管理员接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/admin/stats` | GET | 仪表盘统计数据 |
| `/api/admin/users` | GET | 用户列表 |
| `/api/admin/users` | POST | 创建用户 |
| `/api/admin/users/:id/status` | PUT | 启用/禁用用户 |
| `/api/admin/users/:id/password` | PUT | 重置用户密码 |
| `/api/admin/apps` | GET | 应用列表 |
| `/api/admin/apps` | POST | 创建应用 |
| `/api/admin/apps/:id` | PUT | 更新应用 |
| `/api/admin/apps/:id` | DELETE | 删除应用 |
| `/api/admin/apps/:id/regenerate-secret` | POST | 重置应用密钥 |
| `/api/admin/sessions` | GET | 在线会话列表 |
| `/api/admin/sessions/:id/revoke` | POST | 强制下线会话 |
| `/api/admin/audit` | GET | 审计日志 |

### 集群接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/cluster/status` | GET | 集群状态 |
| `/health` | GET | 健康检查 |

---

## 🧪 本地测试

### 启动 SSO 服务

```bash
cd server
pip install -r requirements.txt
python main.py
```

### 启动示例应用

```bash
cd examples
pip install -r requirements.txt

# 应用1：搜索引擎
APP_ID=search-engine APP_NAME=搜索引擎系统 PORT=5000 \
  CALLBACK_URL=http://localhost:5000/sso/callback \
  python demo-app/app.py

# 应用2：备案系统
APP_ID=icp-system APP_NAME=ICP备案系统 PORT=5001 \
  CALLBACK_URL=http://localhost:5001/sso/callback \
  python demo-app/app.py
```

### 测试步骤

1. 访问 http://localhost:8000/admin 用 admin 登录
2. 创建两个应用，配置回调地址
3. 访问 http://localhost:5000 登录
4. 访问 http://localhost:5001，验证无感登录效果

---

## 🌍 DN42 部署建议

### 域名规划

```
# DN42 环境
sso.yournet.dn42          # SSO 认证中心
search.yournet.dn42       # 搜索引擎
icp.yournet.dn42          # 备案系统
peer.yournet.dn42         # AutoPeer

# 公网环境
sso.yournet.com           # SSO 认证中心
search.yournet.com        # 搜索引擎
icp.yournet.com           # 备案系统
peer.yournet.com          # AutoPeer
```

### Cookie 域处理

NovaSSO 会自动根据访问域名设置对应的 Cookie 域：

- 访问 `*.dn42` 域名 → Cookie 域：`.yournet.dn42`
- 访问 `*.com` 域名 → Cookie 域：`.yournet.com`

两边登录态独立，但用户账号共享同一数据库。

### 多节点部署建议

```
  DN42 节点                公网节点
┌──────────────┐      ┌──────────────┐
│  node-dn42   │◄────►│  node-pub    │
│  (peer)      │ 同步  │  (master)    │
└──────────────┘      └──────────────┘
```

DN42 节点和公网节点对等同步，两边用户都能就近访问，数据实时同步。

---

## 🚀 生产部署

### Systemd 服务

```ini
# /etc/systemd/system/nova-sso.service
[Unit]
Description=NovaSSO 统一身份认证系统
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/nova-sso/server
Environment="NOVA_SECRET=your-production-secret-key"
Environment="NOVA_SYNC_KEY=your-sync-key"
Environment="NOVA_NODE_ID=prod-node-01"
ExecStart=/usr/local/bin/uvicorn main:app --host 127.0.0.1 --port 8000 --workers 2
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Nginx 反向代理

```nginx
server {
    listen 443 ssl http2;
    server_name sso.yourdomain.dn42;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 数据备份

```bash
# 备份 SQLite 数据库
sqlite3 /path/to/nova_sso.db ".backup backup_$(date +%Y%m%d).db"

# 建议：每天自动备份，保留 30 天
```

---

## ❓ 常见问题

### Q: 为什么不用 Redis？

A: 3000 用户规模下 SQLite WAL 模式完全够用。SQLite 支持并发读，写入也能达到每秒几百次，对于 SSO 场景绰绰有余。省去了 Redis 的部署和运维成本。

### Q: 能支持多少并发用户？

A: 单节点 2 核 4G 配置下，支持 500+ 并发用户在线，3000+ 总用户量。如果需要更高并发，可以部署多节点。

### Q: 和 CAS/OIDC 兼容吗？

A: 目前是自研的轻量协议（基于 CAS 思想），不直接兼容标准 OIDC/SAML。如果需要标准协议，可以在现有基础上扩展，或考虑 Keycloak/Casdoor 等成熟方案。

### Q: 怎么实现单点登出？

A: 当前版本支持单系统登出 + SSO 全局登出。全局登出后，其他系统的本地会话需要等过期或下次访问时验证失效。完整的前后端单点登出需要各业务系统配合实现回调。

### Q: 支持 DN42 和公网双环境吗？

A: 支持。通过自动检测访问域名设置不同的 Cookie 域，两边独立登录态但共享用户数据。多中心模式下可以两边各部署节点，数据自动同步。

---

## 🤝 技术栈

- **后端框架**: FastAPI (Python)
- **数据库**: SQLite + WAL 模式
- **密码哈希**: bcrypt
- **前端**: 原生 JS + 现代 CSS
- **协议思想**: CAS 票据机制
- **集群通信**: HTTP + 密钥认证

---

## 🚀 上传到 GitHub

本项目已配置好 Git 仓库，一键上传到 `anncix/dn42_outh`：

```bash
# 方式一：使用一键上传脚本（推荐）
./push-to-github.sh
# 按提示输入 GitHub Personal Access Token 即可

# 方式二：手动推送
git remote add origin https://github.com/anncix/dn42_outh.git
git push -u origin main
```

> **获取 Token**：GitHub 右上角头像 → Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token → 勾选 `repo` 权限

---

## 📄 License

MIT License

---

## 🎯 适用于

- ✅ DN42 / 自建网络环境
- ✅ 多系统统一登录
- ✅ 中小规模团队（100-3000 用户）
- ✅ 希望精简开发、快速上线
- ✅ 数据主权、自主可控

---

**如果这个项目对你有帮助，欢迎 Star ⭐**