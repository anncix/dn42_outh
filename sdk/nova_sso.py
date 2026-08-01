  1→"""
  2→NovaSSO Python SDK
  3→业务系统接入统一登录的客户端库
  4→
  5→使用方式:
  6→    from nova_sso import NovaSSOClient
  7→
  8→    sso = NovaSSOClient(
  9→        sso_url="https://sso.yourdomain.dn42",
 10→        app_id="your-app-id",
 11→        callback_url="https://your-app/sso/callback"
 12→    )
 13→
 14→    # Flask 示例
 15→    @app.route("/login")
 16→    def login():
 17→        return redirect(sso.get_login_url())
 18→
 19→    @app.route("/sso/callback")
 20→    def sso_callback():
 21→        ticket = request.args.get("ticket")
 22→        user = sso.validate_ticket(ticket)
 23→        if user:
 24→            session["user"] = user
 25→            return redirect("/")
 26→        return "登录失败"
 27→"""
 28→
 29→import requests
 30→from urllib.parse import urlencode, urlparse
 31→from typing import Optional, Dict
 32→
 33→
 34→class NovaSSOClient:
 35→    """NovaSSO 客户端"""
 36→
 37→    def __init__(self, sso_url: str, app_id: str, callback_url: str,
 38→                 app_secret: str = None, timeout: int = 10):
 39→        """
 40→        初始化 SSO 客户端
 41→
 42→        Args:
 43→            sso_url: SSO 服务器地址，如 https://sso.example.com
 44→            app_id: 应用ID（在SSO管理后台创建）
 45→            callback_url: 回调地址（必须与SSO中配置的一致）
 46→            app_secret: 应用密钥（可选，用于增强验证）
 47→            timeout: 请求超时时间（秒）
 48→        """
 49→        self.sso_url = sso_url.rstrip("/")
 50→        self.app_id = app_id
 51→        self.callback_url = callback_url
 52→        self.app_secret = app_secret
 53→        self.timeout = timeout
 54→
 55→    def get_login_url(self, redirect: str = "", silent: bool = False) -> str:
 56→        """
 57→        获取登录跳转URL
 58→
 59→        Args:
 60→            redirect: 登录成功后跳转的地址（可选）
 61→            silent: 是否静默模式（无感登录用）
 62→
 63→        Returns:
 64→            登录页面URL
 65→        """
 66→        params = {
 67→            "service": self.callback_url,
 68→            "app": self.app_id,
 69→        }
 70→        if redirect:
 71→            params["redirect"] = redirect
 72→        if silent:
 73→            params["silent"] = "true"
 74→
 75→        return f"{self.sso_url}/login?{urlencode(params)}"
 76→
 77→    def get_logout_url(self, redirect: str = "") -> str:
 78→        """
 79→        获取登出URL
 80→
 81→        Args:
 82→            redirect: 登出后跳转地址
 83→
 84→        Returns:
 85→            登出URL
 86→        """
 87→        params = {}
 88→        if redirect:
 89→            params["redirect"] = redirect
 90→        url = f"{self.sso_url}/logout"
 91→        if params:
 92→            url += f"?{urlencode(params)}"
 93→        return url
 94→
 95→    def validate_ticket(self, ticket: str) -> Optional[Dict]:
 96→        """
 97→        验证服务票据（ST）
 98→
 99→        Args:
            ticket: 服务票据（从回调URL的ticket参数获取）

        Returns:
            用户信息字典，验证失败返回None
            {
                "user_id": 1,
                "username": "xxx",
                "email": "xxx@xx.com",
                "nickname": "xxx",
                "avatar": "...",
                "is_admin": false,
                "tgt_id": "TGT-xxx",
                "app_id": "xxx"
            }
        """
        if not ticket or not ticket.startswith("ST-"):
            return None

        try:
            resp = requests.get(
                f"{self.sso_url}/api/serviceValidate",
                params={
                    "ticket": ticket,
                    "service": self.callback_url,
                    "app": self.app_id,
                },
                timeout=self.timeout
            )
            data = resp.json()

            if data.get("success"):
                return data.get("user")
            return None

        except requests.RequestException as e:
            print(f"[NovaSSO] 验证票据失败: {e}")
            return None

    def get_user_info(self, user_id: int) -> Optional[Dict]:
        """获取用户信息（需管理员权限，暂不实现）"""
        # 预留接口，后续可扩展
        return None

    # ===== Flask 便捷装饰器 =====

    def flask_login_required(self, f):
        """
        Flask 登录验证装饰器

        使用方式:
            @app.route("/protected")
            @sso.flask_login_required
            def protected():
                return f"Hello, {session['user']['username']}"
        """
        from functools import wraps
        from flask import session, redirect, request, url_for

        @wraps(f)
        def decorated(*args, **kwargs):
            if "user" in session:
                return f(*args, **kwargs)

            # 检查是否有ST回调
            ticket = request.args.get("ticket")
            if ticket:
                user = self.validate_ticket(ticket)
                if user:
                    session["user"] = user
                    # 重定向到干净的URL（去掉ticket参数）
                    return redirect(request.path)

            # 跳转到SSO登录
            return redirect(self.get_login_url(redirect=request.url))

        return decorated

    # ===== FastAPI 便捷依赖 =====

    def fastapi_get_current_user(self):
        """
        FastAPI 依赖注入函数

        使用方式:
            from fastapi import Depends, HTTPException

            @app.get("/protected")
            async def protected(user = Depends(sso.fastapi_get_current_user)):
                return {"user": user}
        """
        from fastapi import Request, HTTPException, Cookie
        from typing import Optional

        async def _get_user(request: Request, ticket: Optional[str] = None):
            # 1. 从session中获取
            user = request.session.get("user") if hasattr(request, 'session') else None
            if user:
                return user

            # 2. 验证ticket
            if ticket:
                user_info = self.validate_ticket(ticket)
                if user_info:
                    if hasattr(request, 'session'):
                        request.session["user"] = user_info
                    return user_info

            raise HTTPException(
                status_code=302,
                headers={"Location": self.get_login_url(redirect=str(request.url))}
            )

        return _get_user


# ===== 便捷函数 =====

def create_sso_client(sso_url: str, app_id: str, callback_url: str,
                      **kwargs) -> NovaSSOClient:
    """便捷创建SSO客户端"""
    return NovaSSOClient(sso_url, app_id, callback_url, **kwargs)