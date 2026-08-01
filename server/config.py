 1→"""
 2→NovaSSO - 统一身份认证系统配置
 3→蓝白色调 · 多中心架构 · 现代化设计
 4→"""
 5→import os
 6→from pathlib import Path
 7→
 8→BASE_DIR = Path(__file__).resolve().parent
 9→
# ====== 基础配置 ======
APP_NAME = "NovaSSO"
APP_VERSION = "1.0.0"
DEBUG = os.getenv("NOVA_DEBUG", "false").lower() == "true"
SECRET_KEY = os.getenv("NOVA_SECRET", "nova-sso-secret-key-change-in-production")

# ====== 数据库配置 ======
DB_PATH = os.getenv("NOVA_DB_PATH", str(BASE_DIR / "data" / "nova_sso.db"))

# ====== 会话配置 ======
TGT_EXPIRE_DAYS = int(os.getenv("NOVA_TGT_DAYS", "7"))       # 全局会话有效期（天）
ST_EXPIRE_MINUTES = int(os.getenv("NOVA_ST_MIN", "5"))        # 服务票据有效期（分钟）
LOCAL_SESSION_HOURS = int(os.getenv("NOVA_LOCAL_HRS", "24"))  # 本地会话有效期（小时）

# ====== Cookie配置 ======
COOKIE_TGT = "nova_tgt"
COOKIE_SESSION = "nova_session"
COOKIE_DOMAIN = os.getenv("NOVA_COOKIE_DOMAIN", None)  # 自动检测，也可手动设置
COOKIE_SECURE = os.getenv("NOVA_COOKIE_SECURE", "true").lower() == "true"
COOKIE_HTTPONLY = True
COOKIE_SAMESITE = "Lax"

# ====== 安全配置 ======
PASSWORD_MIN_LENGTH = 8
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 30
BCRYPT_ROUNDS = 12

# ====== 多中心配置 ======
# 当前节点ID
NODE_ID = os.getenv("NOVA_NODE_ID", "node-01")
# 节点名称
NODE_NAME = os.getenv("NOVA_NODE_NAME", "主节点")
# 节点角色: master / slave / peer
NODE_ROLE = os.getenv("NOVA_NODE_ROLE", "master")
# 对等节点列表（用于多中心数据同步）
PEER_NODES = os.getenv("NOVA_PEERS", "").split(",") if os.getenv("NOVA_PEERS") else []
# 数据同步间隔（秒）
SYNC_INTERVAL = int(os.getenv("NOVA_SYNC_INTERVAL", "30"))
# 同步API密钥（节点间通信认证）
SYNC_API_KEY = os.getenv("NOVA_SYNC_KEY", "nova-sync-key-change-me")

# ====== 主题配置 ======
THEME = {
    "primary": "#2563eb",       # 主蓝
    "primary_dark": "#1d4ed8",  # 深蓝
    "primary_light": "#3b82f6", # 亮蓝
    "accent": "#0ea5e9",        # 青蓝
    "bg": "#f8fafc",            # 背景
    "surface": "#ffffff",       # 表面
    "text": "#0f172a",          # 主文字
    "text_muted": "#64748b",    # 次要文字
    "border": "#e2e8f0",        # 边框
    "success": "#10b981",
    "warning": "#f59e0b",
    "error": "#ef4444",
}

# ====== 品牌配置 ======
BRAND = {
    "name": "NovaSSO",
    "full_name": "Nova 统一身份认证中心",
    "logo": "🚀",
    "tagline": "一站式身份管理 · 安全便捷的统一登录体验",
    "footer": "© 2026 NovaSSO · 安全 · 高效 · 现代化",
}