  1→"""
  2→NovaSSO - 主入口
  3→统一身份认证系统 · 蓝白色调 · 多中心架构
  4→"""
  5→import os
  6→import threading
  7→import time
  8→from contextlib import asynccontextmanager
  9→
 10→from fastapi import FastAPI, Request, Response, Depends, Form, HTTPException, Cookie
 11→from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
 12→from fastapi.staticfiles import StaticFiles
 13→from fastapi.templating import Jinja2Templates
 14→from fastapi.middleware.cors import CORSMiddleware
 15→from urllib.parse import urlparse, urlencode
 16→
 17→from config import (
 18→    APP_NAME, APP_VERSION, DEBUG, SECRET_KEY,
 19→    COOKIE_TGT, COOKIE_DOMAIN, COOKIE_SECURE, COOKIE_HTTPONLY, COOKIE_SAMESITE,
 20→    BRAND, THEME, NODE_ID, NODE_NAME, NODE_ROLE
 21→)
 22→from database import init_db, get_db
 23→import auth
 24→from cluster import init_cluster, get_cluster
 25→
 26→
 27→# ========== FastAPI 初始化 ==========
 28→
 29→@asynccontextmanager
 30→async def lifespan(app: FastAPI):
 31→    # 启动时
 32→    init_db()
 33→    init_cluster()
 34→    # 创建默认管理员
 35→    _create_default_admin()
 36→    # 启动后台清理线程
 37→    _start_cleanup_thread()
 38→    yield
 39→    # 关闭时
 40→    pass
 41→
 42→
 43→app = FastAPI(
 44→    title=APP_NAME,
 45→    version=APP_VERSION,
 46→    debug=DEBUG,
 47→    lifespan=lifespan
 48→)
 49→
 50→# CORS 支持
 51→app.add_middleware(
 52→    CORSMiddleware,
 53→    allow_origins=["*"],
 54→    allow_credentials=True,
 55→    allow_methods=["*"],
 56→    allow_headers=["*"],
 57→)
 58→
 59→# 模板
 60→templates = Jinja2Templates(directory="templates")
 61→
 62→# 静态文件
 63→app.mount("/static", StaticFiles(directory="static"), name="static")
 64→
 65→# 管理后台页面
 66→@app.get("/admin", response_class=HTMLResponse)
 67→async def admin_page(request: Request, nova_tgt: str = Cookie("")):
 68→    """管理后台页面"""
 69→    if not nova_tgt:
 70→        return RedirectResponse(url=f"/login?redirect=/admin")
 71→
 72→    tgt_data = auth.get_tgt(nova_tgt)
 73→    if not tgt_data:
 74→        return RedirectResponse(url=f"/login?redirect=/admin")
 75→
 76→    user = auth.get_user_by_id(tgt_data['user_id'])
 77→    if not user or not user['is_admin']:
 78→        return HTMLResponse(content="<h1>403 Forbidden</h1><p>需要管理员权限</p>", status_code=403)
 79→
 80→    return templates.TemplateResponse(request, "admin.html", {
 81→        "request": request,
 82→        "user": user,
 83→        "brand": BRAND,
 84→        "theme": THEME,
 85→    })
 86→
 87→
 88→# ========== 辅助函数 ==========
 89→
 90→def _create_default_admin():
 91→    """创建默认管理员账号"""
 92→    admin = auth.get_user_by_username("admin")
 93→    if not admin:
 94→        auth.create_user(
 95→            username="admin",
 96→            password="admin123",
 97→            email="admin@nova-sso.local",
 98→            nickname="超级管理员",
 99→            is_admin=True
        )
        print("[NovaSSO] 默认管理员已创建: admin / admin123")
        print("[NovaSSO] ⚠️  请尽快修改默认密码！")


def _start_cleanup_thread():
    """启动后台清理线程"""
    def cleanup_loop():
        while True:
            try:
                deleted = auth.cleanup_expired()
                if deleted:
                    print(f"[NovaSSO] 清理过期数据: {deleted} 条")
            except Exception as e:
                print(f"[NovaSSO] 清理异常: {e}")
            time.sleep(1800)  # 每30分钟

    t = threading.Thread(target=cleanup_loop, daemon=True)
    t.start()


def get_cookie_domain(request: Request) -> str:
    """根据请求动态获取Cookie域"""
    if COOKIE_DOMAIN:
        return COOKIE_DOMAIN
    host = request.url.hostname or ""
    # dn42 域名处理
    if host.endswith(".dn42"):
        parts = host.split(".")
        if len(parts) >= 2:
            return "." + ".".join(parts[-2:])
    # 普通域名
    parts = host.split(".")
    if len(parts) >= 2:
        return "." + ".".join(parts[-2:])
    return host


def set_tgt_cookie(response: Response, tgt: str, request: Request):
    """设置TGT Cookie"""
    domain = get_cookie_domain(request)
    response.set_cookie(
        key=COOKIE_TGT,
        value=tgt,
        max_age=7 * 24 * 3600,
        httponly=COOKIE_HTTPONLY,
        secure=COOKIE_SECURE and not DEBUG,
        samesite=COOKIE_SAMESITE,
        domain=domain if domain != request.url.hostname else None,
        path="/"
    )


def clear_tgt_cookie(response: Response, request: Request):
    """清除TGT Cookie"""
    domain = get_cookie_domain(request)
    response.delete_cookie(
        key=COOKIE_TGT,
        domain=domain if domain != request.url.hostname else None,
        path="/"
    )


def get_current_user(request: Request, nova_tgt: str = Cookie("")) -> dict:
    """获取当前登录用户（管理后台用）"""
    if not nova_tgt:
        raise HTTPException(status_code=401, detail="未登录")
    
    tgt_data = auth.get_tgt(nova_tgt)
    if not tgt_data:
        raise HTTPException(status_code=401, detail="登录已过期")
    
    user = auth.get_user_by_id(tgt_data['user_id'])
    if not user or not user['is_active']:
        raise HTTPException(status_code=401, detail="用户不存在或已禁用")
    
    if not user['is_admin']:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    auth.touch_tgt(nova_tgt)
    return user


# ========== 页面路由 ==========

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, nova_tgt: str = Cookie("")):
    """首页 / 用户中心"""
    user = None
    if nova_tgt:
        tgt_data = auth.get_tgt(nova_tgt)
        if tgt_data:
            user = auth.get_user_by_id(tgt_data['user_id'])
            auth.touch_tgt(nova_tgt)
    
    apps = auth.list_apps() if user else []
    
    return templates.TemplateResponse(request, "index.html", {
        "request": request,
        "user": user,
        "apps": apps,
        "brand": BRAND,
        "theme": THEME,
        "node_id": NODE_ID,
        "node_name": NODE_NAME,
    })


@app.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    service: str = "",
    app: str = "",
    silent: bool = False,
    redirect: str = "",
    nova_tgt: str = Cookie("")
):
    """登录页"""
    # 已登录的话，直接签发ST跳转
    if nova_tgt:
        tgt_data = auth.get_tgt(nova_tgt)
        if tgt_data:
            if service and auth.verify_service_url(service, app):
                st = auth.create_st(nova_tgt, tgt_data['user_id'], app or "unknown", service)
                sep = "&" if "?" in service else "?"
                url = f"{service}{sep}ticket={st}"
                if redirect:
                    url += f"&redirect={redirect}"
                return RedirectResponse(url=url)
            if not silent:
                return RedirectResponse(url="/")
    
    # 静默模式下未登录
    if silent and service:
        sep = "&" if "?" in service else "?"
        return RedirectResponse(url=f"{service}{sep}error=login_required")
    
    return templates.TemplateResponse(request, "login.html", {
        "request": request,
        "service": service,
        "app_id": app,
        "silent": silent,
        "redirect": redirect,
        "brand": BRAND,
        "theme": THEME,
        "error": None,
        "node_id": NODE_ID,
    })


@app.post("/login")
async def login_submit(
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    service: str = Form(""),
    app: str = Form(""),
    silent: str = Form("false"),
    redirect: str = Form(""),
):
    """登录提交"""
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")
    
    # 查找用户
    user = auth.get_user_by_username(username)
    
    if not user:
        # 记录失败审计
        auth.audit_log("login_failed", None, username, None,
                       client_ip, user_agent, False, "用户不存在")
        return templates.TemplateResponse(request, "login.html", {
            "request": request,
            "service": service,
            "app_id": app,
            "silent": silent == "true",
            "redirect": redirect,
            "brand": BRAND,
            "theme": THEME,
            "error": "用户名或密码错误",
            "node_id": NODE_ID,
        })
    
    # 检查是否被锁定
    if auth.is_user_locked(user['id']):
        auth.audit_log("login_locked", user['id'], username, None,
                       client_ip, user_agent, False, "账号已锁定")
        return templates.TemplateResponse(request, "login.html", {
            "request": request,
            "service": service,
            "app_id": app,
            "silent": silent == "true",
            "redirect": redirect,
            "brand": BRAND,
            "theme": THEME,
            "error": f"账号已被锁定，请稍后再试或联系管理员",
            "node_id": NODE_ID,
        })
    
    # 验证密码
    if not auth.verify_password(password, user['password_hash']):
        attempts = auth.increment_failed_attempts(user['id'])
        auth.audit_log("login_failed", user['id'], username, None,
                       client_ip, user_agent, False, f"密码错误 (第{attempts}次)")
        
        error_msg = "用户名或密码错误"
        remaining = max(0, auth.MAX_LOGIN_ATTEMPTS - attempts)
        if remaining <= 2:
            error_msg += f"（还剩{remaining}次机会）"
        
        return templates.TemplateResponse(request, "login.html", {
            "request": request,
            "service": service,
            "app_id": app,
            "silent": silent == "true",
            "redirect": redirect,
            "brand": BRAND,
            "theme": THEME,
            "error": error_msg,
            "node_id": NODE_ID,
        })
    
    # 登录成功
    auth.update_last_login(user['id'], client_ip)
    auth.audit_log("login_success", user['id'], username, None,
                   client_ip, user_agent, True)
    
    # 创建TGT
    tgt = auth.create_tgt(user['id'], user['username'], client_ip, user_agent)
    
    # 决定跳转目标
    if service and auth.verify_service_url(service, app):
        st = auth.create_st(tgt, user['id'], app or "unknown", service)
        sep = "&" if "?" in service else "?"
        redirect_url = f"{service}{sep}ticket={st}"
        if redirect:
            redirect_url += f"&redirect={redirect}"
    else:
        redirect_url = "/"
    
    resp = RedirectResponse(url=redirect_url, status_code=303)
    set_tgt_cookie(resp, tgt, request)
    return resp


@app.get("/logout")
async def logout(
    request: Request,
    redirect: str = "/",
    nova_tgt: str = Cookie("")
):
    """登出"""
    if nova_tgt:
        tgt_data = auth.get_tgt(nova_tgt)
        if tgt_data:
            auth.audit_log("logout", tgt_data['user_id'], tgt_data['username'])
        auth.delete_tgt(nova_tgt)
    
    resp = templates.TemplateResponse(request, "logout.html", {
        "request": request,
        "redirect": redirect,
        "brand": BRAND,
        "theme": THEME,
    })
    clear_tgt_cookie(resp, request)
    return resp


# ========== 票据验证接口（后端调用） ==========

@app.get("/api/serviceValidate")
async def service_validate(ticket: str, service: str, app: str = ""):
    """
    服务票据验证接口
    各业务系统后端调用此接口验证ST
    """
    user_data = auth.validate_st(ticket, service)
    if user_data:
        return {
            "success": True,
            "user": user_data
        }
    return {"success": False, "error": "invalid_ticket"}


@app.post("/api/serviceValidate")
async def service_validate_post(ticket: str, service: str, app: str = ""):
    """POST方式验证"""
    return await service_validate(ticket, service, app)


# ========== 管理后台 API ==========

@app.get("/api/admin/stats")
async def admin_stats(user: dict = Depends(get_current_user)):
    """获取统计数据"""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as total FROM users")
        total_users = cur.fetchone()['total']
        
        cur.execute("SELECT COUNT(*) as total FROM apps WHERE is_active = 1")
        total_apps = cur.fetchone()['total']
        
        cur.execute("SELECT COUNT(*) as total FROM tgt_sessions WHERE expires_at > datetime('now')")
        active_sessions = cur.fetchone()['total']
        
        cur.execute("SELECT COUNT(*) as total FROM audit_logs WHERE date(created_at) = date('now')")
        today_logins = cur.fetchone()['total']
        
        cur.close()
    
    cluster_info = get_cluster().get_cluster_status()
    
    return {
        "success": True,
        "stats": {
            "total_users": total_users,
            "total_apps": total_apps,
            "active_sessions": active_sessions,
            "today_logins": today_logins,
        },
        "cluster": cluster_info
    }


@app.get("/api/admin/users")
async def admin_users(
    page: int = 1,
    page_size: int = 20,
    keyword: str = "",
    user: dict = Depends(get_current_user)
):
    """用户列表"""
    result = auth.list_users(page, page_size, keyword)
    return {"success": True, "data": result}


@app.post("/api/admin/users")
async def admin_create_user(
    request: Request,
    user_data: dict,
    user: dict = Depends(get_current_user)
):
    """创建用户"""
    username = user_data.get("username", "").strip()
    password = user_data.get("password", "")
    email = user_data.get("email", "")
    nickname = user_data.get("nickname", "")
    is_admin = user_data.get("is_admin", False)
    
    if not username or not password:
        return {"success": False, "error": "用户名和密码不能为空"}
    
    if auth.get_user_by_username(username):
        return {"success": False, "error": "用户名已存在"}
    
    strength = auth.check_password_strength(password)
    if not strength["strong"]:
        return {"success": False, "error": "密码强度不足: " + ", ".join(strength["issues"])}
    
    user_id = auth.create_user(username, password, email, nickname, is_admin)
    auth.audit_log("user_create", user['id'], user['username'],
                   f"user:{username}", success=True,
                   detail=f"创建用户 {username}")
    
    return {"success": True, "user_id": user_id}


@app.put("/api/admin/users/{user_id}/status")
async def admin_toggle_user_status(
    user_id: int,
    status_data: dict,
    user: dict = Depends(get_current_user)
):
    """启用/禁用用户"""
    is_active = status_data.get("is_active", True)
    target_user = auth.get_user_by_id(user_id)
    
    if not target_user:
        return {"success": False, "error": "用户不存在"}
    
    if target_user['username'] == 'admin' and not is_active:
        return {"success": False, "error": "不能禁用超级管理员"}
    
    auth.update_user_status(user_id, is_active)
    auth.audit_log("user_status_change", user['id'], user['username'],
                   f"user:{target_user['username']}", success=True,
                   detail=f"{'启用' if is_active else '禁用'}用户 {target_user['username']}")
    
    # 如果禁用用户，同时踢掉所有会话
    if not is_active:
        auth.delete_user_all_tgts(user_id)
    
    return {"success": True}


@app.put("/api/admin/users/{user_id}/password")
async def admin_reset_password(
    user_id: int,
    pwd_data: dict,
    user: dict = Depends(get_current_user)
):
    """管理员重置用户密码"""
    new_password = pwd_data.get("password", "")
    
    if not new_password:
        return {"success": False, "error": "新密码不能为空"}
    
    strength = auth.check_password_strength(new_password)
    if not strength["strong"]:
        return {"success": False, "error": "密码强度不足: " + ", ".join(strength["issues"])}
    
    target_user = auth.get_user_by_id(user_id)
    if not target_user:
        return {"success": False, "error": "用户不存在"}
    
    auth.update_user_password(user_id, new_password)
    
    # 重置密码后踢掉所有会话，强制重新登录
    auth.delete_user_all_tgts(user_id)
    
    auth.audit_log("user_password_reset", user['id'], user['username'],
                   f"user:{target_user['username']}", success=True,
                   detail=f"重置用户 {target_user['username']} 的密码")
    
    return {"success": True}


@app.get("/api/admin/apps")
async def admin_apps(user: dict = Depends(get_current_user)):
    """应用列表"""
    apps = auth.list_apps()
    # 去掉secret字段
    safe_apps = [{k: v for k, v in a.items() if k != 'app_secret'} for a in apps]
    return {"success": True, "data": safe_apps}


@app.post("/api/admin/apps")
async def admin_create_app(
    app_data: dict,
    user: dict = Depends(get_current_user)
):
    """创建应用"""
    app_id = app_data.get("app_id", "").strip()
    app_name = app_data.get("app_name", "").strip()
    callback_url = app_data.get("callback_url", "").strip()
    app_description = app_data.get("app_description", "")
    logout_url = app_data.get("logout_url", "")
    
    if not app_id or not app_name or not callback_url:
        return {"success": False, "error": "应用ID、名称、回调地址不能为空"}
    
    if auth.get_app(app_id):
        return {"success": False, "error": "应用ID已存在"}
    
    new_id = auth.create_app(app_id, app_name, callback_url,
                             app_description, logout_url, user['id'])
    
    # 获取创建后的应用信息（含secret）
    app_info = auth.get_app(app_id)
    
    auth.audit_log("app_create", user['id'], user['username'],
                   f"app:{app_id}", success=True)
    
    return {"success": True, "app_id": new_id, "app_secret": app_info['app_secret']}


@app.put("/api/admin/apps/{app_id}")
async def admin_update_app(
    app_id: str,
    app_data: dict,
    user: dict = Depends(get_current_user)
):
    """更新应用信息"""
    app = auth.get_app(app_id)
    if not app:
        return {"success": False, "error": "应用不存在"}
    
    update_data = {}
    if 'app_name' in app_data:
        update_data['app_name'] = app_data['app_name'].strip()
    if 'app_description' in app_data:
        update_data['app_description'] = app_data['app_description']
    if 'callback_url' in app_data:
        update_data['callback_url'] = app_data['callback_url'].strip()
    if 'logout_url' in app_data:
        update_data['logout_url'] = app_data['logout_url']
    
    if not update_data:
        return {"success": False, "error": "没有需要更新的字段"}
    
    auth.update_app(app_id, **update_data)
    auth.audit_log("app_update", user['id'], user['username'],
                   f"app:{app_id}", success=True,
                   detail=f"更新应用 {app_id}")
    
    return {"success": True}


@app.post("/api/admin/apps/{app_id}/regenerate-secret")
async def admin_regenerate_app_secret(
    app_id: str,
    user: dict = Depends(get_current_user)
):
    """重新生成应用密钥"""
    app = auth.get_app(app_id)
    if not app:
        return {"success": False, "error": "应用不存在"}
    
    new_secret = auth.regenerate_app_secret(app_id)
    auth.audit_log("app_secret_regenerate", user['id'], user['username'],
                   f"app:{app_id}", success=True,
                   detail=f"重新生成应用 {app_id} 的密钥")
    
    return {"success": True, "app_secret": new_secret}


@app.delete("/api/admin/apps/{app_id}")
async def admin_delete_app(
    app_id: str,
    user: dict = Depends(get_current_user)
):
    """删除应用（软删除）"""
    app = auth.get_app(app_id)
    if not app:
        return {"success": False, "error": "应用不存在"}
    
    auth.delete_app(app_id)
    auth.audit_log("app_delete", user['id'], user['username'],
                   f"app:{app_id}", success=True,
                   detail=f"删除应用 {app_id}")
    
    return {"success": True}


@app.get("/api/admin/audit")
async def admin_audit(
    page: int = 1,
    page_size: int = 20,
    action: str = None,
    user: dict = Depends(get_current_user)
):
    """审计日志"""
    result = auth.get_audit_logs(page, page_size, action)
    return {"success": True, "data": result}


@app.get("/api/admin/sessions")
async def admin_sessions(
    all: bool = False,
    user_id: int = None,
    page: int = 1,
    page_size: int = 20,
    user: dict = Depends(get_current_user)
):
    """活跃会话列表"""
    if all:
        # 管理员查看所有会话
        result = auth.get_all_active_sessions(page, page_size)
        return {"success": True, "data": result}
    elif user_id:
        # 查看指定用户的会话
        sessions = auth.get_user_tgts(user_id)
        return {"success": True, "data": {"items": sessions, "total": len(sessions)}}
    else:
        # 查看自己的会话
        sessions = auth.get_user_tgts(user['id'])
        return {"success": True, "data": {"items": sessions, "total": len(sessions)}}


@app.post("/api/admin/sessions/{tgt_id}/revoke")
async def admin_revoke_session(
    tgt_id: str,
    user: dict = Depends(get_current_user)
):
    """强制下线某个会话"""
    tgt_data = auth.get_tgt(tgt_id)
    if tgt_data:
        auth.delete_tgt(tgt_id)
        auth.audit_log("session_revoke", user['id'], user['username'],
                       f"session:{tgt_id}", success=True,
                       detail=f"强制下线用户 {tgt_data['username']} 的会话")
    
    # 多中心同步：通知其他节点
    get_cluster().push_to_peers('tgt', tgt_id, 'delete')
    
    return {"success": True}


# ========== 多中心集群 API ==========

@app.get("/api/cluster/status")
async def cluster_status():
    """集群状态"""
    return {"success": True, "data": get_cluster().get_cluster_status()}


@app.get("/api/cluster/sync/pull")
async def cluster_sync_pull(request: Request, since_id: int = 0):
    """对等节点拉取同步数据"""
    sync_key = request.headers.get("X-Sync-Key", "")
    from config import SYNC_API_KEY
    if sync_key != SYNC_API_KEY:
        raise HTTPException(status_code=403, detail="invalid sync key")
    
    records = auth.get_pending_syncs(since_id)
    max_id = max((r['id'] for r in records), default=since_id)
    
    return {
        "success": True,
        "records": records,
        "max_id": max_id,
        "node_id": NODE_ID
    }


@app.post("/api/cluster/sync/push")
async def cluster_sync_push(request: Request):
    """对等节点推送变更"""
    sync_key = request.headers.get("X-Sync-Key", "")
    from config import SYNC_API_KEY
    if sync_key != SYNC_API_KEY:
        raise HTTPException(status_code=403, detail="invalid sync key")
    
    data = await request.json()
    sync_type = data.get("sync_type")
    record_id = data.get("record_id")
    operation = data.get("operation")
    
    # 应用变更
    if sync_type == "tgt" and operation == "delete":
        auth.delete_tgt(record_id)
    
    return {"success": True}


# ========== 用户自助 API ==========

@app.get("/api/user/info")
async def user_info(nova_tgt: str = Cookie("")):
    """获取当前登录用户信息"""
    if not nova_tgt:
        return {"success": False, "error": "not_logged_in"}
    
    tgt_data = auth.get_tgt(nova_tgt)
    if not tgt_data:
        return {"success": False, "error": "session_expired"}
    
    user = auth.get_user_by_id(tgt_data['user_id'])
    if not user or not user['is_active']:
        return {"success": False, "error": "user_not_found"}
    
    auth.touch_tgt(nova_tgt)
    
    # 返回安全的用户信息
    return {
        "success": True,
        "user": {
            "id": user['id'],
            "username": user['username'],
            "email": user['email'],
            "nickname": user['nickname'],
            "avatar": user['avatar'],
            "is_admin": user['is_admin'],
            "email_verified": user['email_verified'],
            "mfa_enabled": user['mfa_enabled'],
            "last_login_at": user['last_login_at'],
            "last_login_ip": user['last_login_ip'],
            "created_at": user['created_at'],
        }
    }


@app.put("/api/user/password")
async def user_change_password(
    pwd_data: dict,
    nova_tgt: str = Cookie("")
):
    """用户修改自己的密码"""
    if not nova_tgt:
        return {"success": False, "error": "not_logged_in"}
    
    tgt_data = auth.get_tgt(nova_tgt)
    if not tgt_data:
        return {"success": False, "error": "session_expired"}
    
    user = auth.get_user_by_id(tgt_data['user_id'])
    if not user:
        return {"success": False, "error": "user_not_found"}
    
    old_password = pwd_data.get("old_password", "")
    new_password = pwd_data.get("new_password", "")
    
    # 验证旧密码
    if not auth.verify_password(old_password, user['password_hash']):
        return {"success": False, "error": "旧密码错误"}
    
    # 检查新密码强度
    strength = auth.check_password_strength(new_password)
    if not strength["strong"]:
        return {"success": False, "error": "新密码强度不足: " + ", ".join(strength["issues"])}
    
    # 更新密码
    auth.update_user_password(user['id'], new_password)
    
    # 修改密码后踢掉所有其他会话，保留当前会话
    # （简化实现：踢掉所有，然后当前会话也失效，用户需要重新登录）
    auth.delete_user_all_tgts(user['id'])
    
    auth.audit_log("password_change", user['id'], user['username'],
                   success=True, detail="用户自主修改密码")
    
    return {"success": True, "message": "密码修改成功，请重新登录"}


@app.put("/api/user/profile")
async def user_update_profile(
    profile_data: dict,
    nova_tgt: str = Cookie("")
):
    """用户更新自己的资料"""
    if not nova_tgt:
        return {"success": False, "error": "not_logged_in"}
    
    tgt_data = auth.get_tgt(nova_tgt)
    if not tgt_data:
        return {"success": False, "error": "session_expired"}
    
    user = auth.get_user_by_id(tgt_data['user_id'])
    if not user:
        return {"success": False, "error": "user_not_found"}
    
    nickname = profile_data.get("nickname")
    email = profile_data.get("email")
    avatar = profile_data.get("avatar")
    
    # 邮箱唯一性检查
    if email and email != user['email']:
        existing = auth.get_user_by_email(email)
        if existing:
            return {"success": False, "error": "邮箱已被使用"}
    
    auth.update_user_profile(user['id'], nickname=nickname, email=email, avatar=avatar)
    auth.audit_log("profile_update", user['id'], user['username'],
                   success=True)
    
    return {"success": True}


@app.post("/api/register")
async def register_user(request: Request, user_data: dict):
    """用户自助注册"""
    from config import PASSWORD_MIN_LENGTH
    
    username = user_data.get("username", "").strip()
    password = user_data.get("password", "")
    email = user_data.get("email", "").strip() or None
    nickname = user_data.get("nickname", "").strip() or None
    
    # 验证
    if not username or not password:
        return {"success": False, "error": "用户名和密码不能为空"}
    
    if len(username) < 3 or len(username) > 32:
        return {"success": False, "error": "用户名长度需在3-32位之间"}
    
    # 检查用户名格式（只允许字母、数字、下划线）
    import re
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return {"success": False, "error": "用户名只能包含字母、数字和下划线"}
    
    if auth.get_user_by_username(username):
        return {"success": False, "error": "用户名已存在"}
    
    if email and auth.get_user_by_email(email):
        return {"success": False, "error": "邮箱已被注册"}
    
    # 密码强度检查
    strength = auth.check_password_strength(password)
    if not strength["strong"]:
        return {"success": False, "error": "密码强度不足: " + ", ".join(strength["issues"])}
    
    # 创建用户
    user_id = auth.create_user(username, password, email, nickname, is_admin=False)
    
    client_ip = request.client.host if request.client else "unknown"
    auth.audit_log("user_register", user_id, username,
                   ip=client_ip, success=True)
    
    return {"success": True, "user_id": user_id, "username": username}


# ========== 健康检查 ==========

@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "ok",
        "app": APP_NAME,
        "version": APP_VERSION,
        "node_id": NODE_ID,
        "node_role": NODE_ROLE,
    }


# ========== 启动 ==========

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=DEBUG,
        log_level="info"
    )