  1→"""
  2→NovaSSO - 认证核心模块
  3→票据管理 · 密码验证 · 会话管理
  4→"""
  5→import secrets
  6→import hashlib
  7→import json
  8→from datetime import datetime, timedelta
  9→from typing import Optional, Dict, List
 10→import bcrypt
 11→
 12→from database import db_cursor
 13→from config import (
 14→    TGT_EXPIRE_DAYS, ST_EXPIRE_MINUTES, BCRYPT_ROUNDS,
 15→    MAX_LOGIN_ATTEMPTS, LOCKOUT_MINUTES, NODE_ID, PASSWORD_MIN_LENGTH
 16→)
 17→
 18→
 19→# ========== 密码相关 ==========
 20→
 21→def hash_password(password: str) -> str:
 22→    """密码哈希（bcrypt）"""
 23→    return bcrypt.hashpw(
 24→        password.encode('utf-8'),
 25→        bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
 26→    ).decode('utf-8')
 27→
 28→
 29→def verify_password(password: str, password_hash: str) -> bool:
 30→    """验证密码"""
 31→    try:
 32→        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
 33→    except Exception:
 34→        return False
 35→
 36→
 37→def check_password_strength(password: str) -> Dict:
 38→    """检查密码强度"""
 39→    result = {
 40→        "strong": True,
 41→        "score": 0,
 42→        "issues": []
 43→    }
 44→    
 45→    if len(password) < PASSWORD_MIN_LENGTH:
 46→        result["issues"].append(f"密码长度至少{PASSWORD_MIN_LENGTH}位")
 47→        result["strong"] = False
 48→    else:
 49→        result["score"] += 1
 50→    
 51→    if not any(c.islower() for c in password):
 52→        result["issues"].append("需要包含小写字母")
 53→        result["strong"] = False
 54→    else:
 55→        result["score"] += 1
 56→    
 57→    if not any(c.isupper() for c in password):
 58→        result["issues"].append("需要包含大写字母")
 59→        result["score"] += 0
 60→    
 61→    if not any(c.isdigit() for c in password):
 62→        result["issues"].append("需要包含数字")
 63→        result["strong"] = False
 64→    else:
 65→        result["score"] += 1
 66→    
 67→    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
 68→        result["score"] += 0
 69→    else:
 70→        result["score"] += 1
 71→    
 72→    return result
 73→
 74→
 75→# ========== 用户相关 ==========
 76→
 77→def get_user_by_username(username: str) -> Optional[Dict]:
 78→    """根据用户名获取用户"""
 79→    with db_cursor() as cur:
 80→        cur.execute("SELECT * FROM users WHERE username = ?", (username,))
 81→        row = cur.fetchone()
 82→        return dict(row) if row else None
 83→
 84→
 85→def get_user_by_id(user_id: int) -> Optional[Dict]:
 86→    """根据ID获取用户"""
 87→    with db_cursor() as cur:
 88→        cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
 89→        row = cur.fetchone()
 90→        return dict(row) if row else None
 91→
 92→
 93→def get_user_by_email(email: str) -> Optional[Dict]:
 94→    """根据邮箱获取用户"""
 95→    with db_cursor() as cur:
 96→        cur.execute("SELECT * FROM users WHERE email = ?", (email,))
 97→        row = cur.fetchone()
 98→        return dict(row) if row else None
 99→

def create_user(username: str, password: str, email: str = None,
                nickname: str = None, is_admin: bool = False) -> int:
    """创建用户"""
    password_hash = hash_password(password)
    with db_cursor() as cur:
        cur.execute("""
            INSERT INTO users (username, email, password_hash, nickname, is_admin)
            VALUES (?, ?, ?, ?, ?)
        """, (username, email, password_hash, nickname or username, is_admin))
        return cur.lastrowid


def update_last_login(user_id: int, ip: str):
    """更新最后登录信息"""
    with db_cursor() as cur:
        cur.execute("""
            UPDATE users SET last_login_at = ?, last_login_ip = ?, failed_attempts = 0
            WHERE id = ?
        """, (datetime.now(), ip, user_id))


def increment_failed_attempts(user_id: int) -> int:
    """增加登录失败次数，返回当前失败次数"""
    with db_cursor() as cur:
        cur.execute("SELECT failed_attempts FROM users WHERE id = ?", (user_id,))
        row = cur.fetchone()
        attempts = (row['failed_attempts'] if row else 0) + 1
        
        locked_until = None
        if attempts >= MAX_LOGIN_ATTEMPTS:
            locked_until = datetime.now() + timedelta(minutes=LOCKOUT_MINUTES)
        
        cur.execute("""
            UPDATE users SET failed_attempts = ?, locked_until = ?
            WHERE id = ?
        """, (attempts, locked_until, user_id))
        
        return attempts


def is_user_locked(user_id: int) -> bool:
    """检查用户是否被锁定"""
    with db_cursor() as cur:
        cur.execute("SELECT locked_until FROM users WHERE id = ?", (user_id,))
        row = cur.fetchone()
        if not row or not row['locked_until']:
            return False
        return datetime.fromisoformat(row['locked_until']) > datetime.now()


def list_users(page: int = 1, page_size: int = 20, keyword: str = "") -> Dict:
    """用户列表"""
    offset = (page - 1) * page_size
    with db_cursor() as cur:
        where = ""
        params = []
        if keyword:
            where = "WHERE username LIKE ? OR email LIKE ? OR nickname LIKE ?"
            params = [f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"]
        
        cur.execute(f"SELECT COUNT(*) as total FROM users {where}", params)
        total = cur.fetchone()['total']
        
        cur.execute(f"""
            SELECT id, username, email, nickname, is_active, is_admin,
                   last_login_at, last_login_ip, created_at
            FROM users {where}
            ORDER BY id DESC
            LIMIT ? OFFSET ?
        """, params + [page_size, offset])
        
        users = [dict(row) for row in cur.fetchall()]
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": users
    }


# ========== TGT 全局会话 ==========

def create_tgt(user_id: int, username: str, ip: str,
               user_agent: str, device_info: str = None) -> str:
    """创建全局会话票据"""
    tgt_id = "TGT-" + secrets.token_urlsafe(48)
    expires_at = datetime.now() + timedelta(days=TGT_EXPIRE_DAYS)
    
    with db_cursor() as cur:
        cur.execute("""
            INSERT INTO tgt_sessions 
            (tgt_id, user_id, username, ip, user_agent, device_info, node_id, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (tgt_id, user_id, username, ip, user_agent,
              device_info, NODE_ID, expires_at))
    
    _record_sync('tgt', tgt_id, 'create')
    return tgt_id


def get_tgt(tgt_id: str) -> Optional[Dict]:
    """获取TGT信息（自动检查过期）"""
    if not tgt_id or not tgt_id.startswith("TGT-"):
        return None
    
    with db_cursor() as cur:
        cur.execute("""
            SELECT * FROM tgt_sessions
            WHERE tgt_id = ? AND expires_at > ?
        """, (tgt_id, datetime.now()))
        row = cur.fetchone()
        return dict(row) if row else None


def touch_tgt(tgt_id: str):
    """更新TGT最后活跃时间"""
    with db_cursor() as cur:
        cur.execute("""
            UPDATE tgt_sessions SET last_active_at = ?
            WHERE tgt_id = ?
        """, (datetime.now(), tgt_id))


def delete_tgt(tgt_id: str):
    """删除TGT（登出用）"""
    with db_cursor() as cur:
        cur.execute("DELETE FROM tgt_sessions WHERE tgt_id = ?", (tgt_id,))
        cur.execute("DELETE FROM service_tickets WHERE tgt_id = ?", (tgt_id,))
    
    _record_sync('tgt', tgt_id, 'delete')


def get_user_tgts(user_id: int) -> List[Dict]:
    """获取用户的所有活跃会话"""
    with db_cursor() as cur:
        cur.execute("""
            SELECT * FROM tgt_sessions
            WHERE user_id = ? AND expires_at > ?
            ORDER BY last_active_at DESC
        """, (user_id, datetime.now()))
        return [dict(row) for row in cur.fetchall()]


def delete_user_all_tgts(user_id: int):
    """删除用户所有会话（强制下线）"""
    with db_cursor() as cur:
        cur.execute("SELECT tgt_id FROM tgt_sessions WHERE user_id = ?", (user_id,))
        tgts = [row['tgt_id'] for row in cur.fetchall()]
        
        cur.execute("DELETE FROM tgt_sessions WHERE user_id = ?", (user_id,))
        cur.execute("""
            DELETE FROM service_tickets WHERE tgt_id IN
            (SELECT tgt_id FROM tgt_sessions WHERE user_id = ?)
        """, (user_id,))
    
    for tgt_id in tgts:
        _record_sync('tgt', tgt_id, 'delete')


# ========== ST 服务票据 ==========

def create_st(tgt_id: str, user_id: int, app_id: str, service: str) -> str:
    """创建一次性服务票据"""
    st_id = "ST-" + secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(minutes=ST_EXPIRE_MINUTES)
    
    with db_cursor() as cur:
        cur.execute("""
            INSERT INTO service_tickets
            (st_id, tgt_id, user_id, app_id, service, node_id, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (st_id, tgt_id, user_id, app_id, service, NODE_ID, expires_at))
    
    return st_id


def validate_st(st_id: str, service: str) -> Optional[Dict]:
    """
    验证服务票据
    成功则标记为已使用（一次性），返回用户完整信息
    """
    if not st_id or not st_id.startswith("ST-"):
        return None
    
    with db_cursor() as cur:
        # 查找未使用且未过期的ST
        cur.execute("""
            SELECT * FROM service_tickets
            WHERE st_id = ? AND service = ? AND used = 0 AND expires_at > ?
        """, (st_id, service, datetime.now()))
        st_row = cur.fetchone()
        
        if not st_row:
            return None
        
        # 标记为已使用（原子操作）
        cur.execute("""
            UPDATE service_tickets SET used = 1, used_at = ?
            WHERE st_id = ?
        """, (datetime.now(), st_id))
        
        # 获取用户完整信息
        user = get_user_by_id(st_row['user_id'])
        if not user:
            return None
        
        # 返回安全的用户信息（去掉敏感字段）
        return {
            "user_id": user['id'],
            "username": user['username'],
            "email": user['email'],
            "nickname": user['nickname'],
            "avatar": user['avatar'],
            "is_admin": user['is_admin'],
            "tgt_id": st_row['tgt_id'],
            "app_id": st_row['app_id']
        }


# ========== 应用管理 ==========

def get_app(app_id: str) -> Optional[Dict]:
    """获取应用信息"""
    with db_cursor() as cur:
        cur.execute("SELECT * FROM apps WHERE app_id = ? AND is_active = 1", (app_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def list_apps() -> List[Dict]:
    """获取所有活跃应用"""
    with db_cursor() as cur:
        cur.execute("SELECT * FROM apps WHERE is_active = 1 ORDER BY id")
        return [dict(row) for row in cur.fetchall()]


def create_app(app_id: str, app_name: str, callback_url: str,
               app_description: str = "", logout_url: str = "",
               created_by: int = None) -> int:
    """创建应用"""
    app_secret = secrets.token_urlsafe(32)
    with db_cursor() as cur:
        cur.execute("""
            INSERT INTO apps (app_id, app_name, app_description, callback_url,
                              logout_url, app_secret, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (app_id, app_name, app_description, callback_url,
              logout_url, app_secret, created_by))
        return cur.lastrowid


def verify_service_url(service: str, app_id: str = None) -> bool:
    """
    验证service回调地址是否合法
    防止开放重定向攻击
    """
    from urllib.parse import urlparse
    
    try:
        parsed = urlparse(service)
        if not parsed.scheme or not parsed.netloc:
            return False
        
        # 精确匹配已注册的应用回调地址
        if app_id:
            app = get_app(app_id)
            if app:
                return service.startswith(app['callback_url'].split('?')[0])
            return False
        
        # 没指定app_id的话，匹配所有已注册应用
        apps = list_apps()
        for app in apps:
            base = app['callback_url'].split('?')[0]
            if service.startswith(base):
                return True
        
        return False
    except Exception:
        return False


# ========== 审计日志 ==========

def audit_log(action: str, user_id: int = None, username: str = None,
              target: str = None, ip: str = None, user_agent: str = None,
              success: bool = True, detail: str = None):
    """记录审计日志"""
    with db_cursor() as cur:
        cur.execute("""
            INSERT INTO audit_logs
            (user_id, username, action, target, ip, user_agent, success, detail, node_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, username, action, target, ip, user_agent,
              success, detail, NODE_ID))


def get_audit_logs(page: int = 1, page_size: int = 20,
                   action: str = None, user_id: int = None) -> Dict:
    """获取审计日志"""
    offset = (page - 1) * page_size
    conditions = []
    params = []
    
    if action:
        conditions.append("action = ?")
        params.append(action)
    if user_id:
        conditions.append("user_id = ?")
        params.append(user_id)
    
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    
    with db_cursor() as cur:
        cur.execute(f"SELECT COUNT(*) as total FROM audit_logs {where}", params)
        total = cur.fetchone()['total']
        
        cur.execute(f"""
            SELECT * FROM audit_logs {where}
            ORDER BY id DESC
            LIMIT ? OFFSET ?
        """, params + [page_size, offset])
        
        items = [dict(row) for row in cur.fetchall()]
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items
    }


# ========== 数据清理 ==========

def cleanup_expired() -> int:
    """清理过期数据（TGT、ST、审计日志）"""
    now = datetime.now()
    deleted = 0
    
    with db_cursor() as cur:
        # 清理过期TGT
        cur.execute("DELETE FROM tgt_sessions WHERE expires_at < ?", (now,))
        deleted += cur.rowcount
        
        # 清理过期ST
        cur.execute("DELETE FROM service_tickets WHERE expires_at < ?", (now,))
        deleted += cur.rowcount
        
        # 清理90天前的审计日志
        ninety_days_ago = now - timedelta(days=90)
        cur.execute("DELETE FROM audit_logs WHERE created_at < ?", (ninety_days_ago,))
        deleted += cur.rowcount
    
    return deleted


# ========== 新增：用户管理扩展 ==========

def update_user_status(user_id: int, is_active: bool) -> bool:
    """启用/禁用用户"""
    with db_cursor() as cur:
        cur.execute("UPDATE users SET is_active = ? WHERE id = ?", (is_active, user_id))
        return cur.rowcount > 0


def update_user_password(user_id: int, new_password: str) -> bool:
    """修改用户密码"""
    password_hash = hash_password(new_password)
    with db_cursor() as cur:
        cur.execute("UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?",
                   (password_hash, datetime.now(), user_id))
        return cur.rowcount > 0


def update_user_profile(user_id: int, nickname: str = None, email: str = None,
                        avatar: str = None) -> bool:
    """更新用户资料"""
    fields = []
    params = []
    if nickname is not None:
        fields.append("nickname = ?")
        params.append(nickname)
    if email is not None:
        fields.append("email = ?")
        params.append(email)
    if avatar is not None:
        fields.append("avatar = ?")
        params.append(avatar)
    
    if not fields:
        return False
    
    params.append(user_id)
    fields.append("updated_at = ?")
    params.append(datetime.now())
    
    with db_cursor() as cur:
        cur.execute(f"UPDATE users SET {', '.join(fields)} WHERE id = ?", params)
        return cur.rowcount > 0


def get_all_active_sessions(page: int = 1, page_size: int = 20) -> Dict:
    """获取所有活跃会话（管理员用）"""
    offset = (page - 1) * page_size
    with db_cursor() as cur:
        cur.execute("SELECT COUNT(*) as total FROM tgt_sessions WHERE expires_at > ?",
                   (datetime.now(),))
        total = cur.fetchone()['total']
        
        cur.execute("""
            SELECT * FROM tgt_sessions
            WHERE expires_at > ?
            ORDER BY last_active_at DESC
            LIMIT ? OFFSET ?
        """, (datetime.now(), page_size, offset))
        
        items = [dict(row) for row in cur.fetchall()]
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items
    }


# ========== 新增：应用管理扩展 ==========

def update_app(app_id: str, **kwargs) -> bool:
    """更新应用信息"""
    allowed_fields = ['app_name', 'app_description', 'callback_url', 'logout_url', 'is_active']
    fields = []
    params = []
    
    for key, value in kwargs.items():
        if key in allowed_fields:
            fields.append(f"{key} = ?")
            params.append(value)
    
    if not fields:
        return False
    
    params.append(app_id)
    
    with db_cursor() as cur:
        cur.execute(f"UPDATE apps SET {', '.join(fields)} WHERE app_id = ?", params)
        return cur.rowcount > 0


def delete_app(app_id: str) -> bool:
    """删除应用（软删除，实际置为不可用）"""
    with db_cursor() as cur:
        cur.execute("UPDATE apps SET is_active = 0 WHERE app_id = ?", (app_id,))
        return cur.rowcount > 0


def regenerate_app_secret(app_id: str) -> Optional[str]:
    """重新生成应用密钥"""
    new_secret = secrets.token_urlsafe(32)
    with db_cursor() as cur:
        cur.execute("UPDATE apps SET app_secret = ? WHERE app_id = ?",
                   (new_secret, app_id))
        if cur.rowcount > 0:
            return new_secret
    return None


# ========== 多中心同步辅助 ==========

def _record_sync(sync_type: str, record_id: str, operation: str):
    """记录同步事件（多中心架构用）"""
    with db_cursor() as cur:
        cur.execute("""
            INSERT INTO sync_records (sync_type, record_id, operation, node_id)
            VALUES (?, ?, ?, ?)
        """, (sync_type, record_id, operation, NODE_ID))


def get_pending_syncs(since_id: int) -> List[Dict]:
    """获取待同步的变更记录"""
    with db_cursor() as cur:
        cur.execute("""
            SELECT * FROM sync_records
            WHERE id > ? AND node_id != ?
            ORDER BY id ASC
            LIMIT 100
        """, (since_id, NODE_ID))
        return [dict(row) for row in cur.fetchall()]