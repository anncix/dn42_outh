  1→"""
  2→NovaSSO 示例业务系统
  3→演示如何接入统一登录（Flask 版本）
  4→
  5→运行方式:
  6→    pip install flask requests
  7→    python app.py
  8→"""
  9→import os
 10→import sys
 11→from flask import Flask, session, redirect, request, render_template_string, jsonify
 12→
 13→# 引入 SDK（实际项目中安装 nova_sso 包）
 14→sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'sdk'))
 15→from nova_sso import NovaSSOClient
 16→
 17→app = Flask(__name__)
 18→app.secret_key = os.getenv('APP_SECRET', 'demo-secret-key-change-me')
 19→
 20→# ====== SSO 配置 ======
 21→SSO_URL = os.getenv('SSO_URL', 'http://localhost:8000')
 22→APP_ID = os.getenv('APP_ID', 'demo-app')
 23→CALLBACK_URL = os.getenv('CALLBACK_URL', 'http://localhost:5000/sso/callback')
 24→APP_NAME = os.getenv('APP_NAME', '演示应用')
 25→
 26→sso = NovaSSOClient(
 27→    sso_url=SSO_URL,
 28→    app_id=APP_ID,
 29→    callback_url=CALLBACK_URL
 30→)
 31→
 32→
 33→# ====== 页面模板 ======
 34→PAGE_TEMPLATE = """
 35→<!DOCTYPE html>
 36→<html lang="zh-CN">
 37→<head>
 38→<meta charset="UTF-8">
 39→<meta name="viewport" content="width=device-width, initial-scale=1.0">
 40→<title>{{ app_name }} - NovaSSO 演示</title>
 41→<style>
 42→  * { margin: 0; padding: 0; box-sizing: border-box; }
 43→  body {
 44→    font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif;
 45→    background: linear-gradient(135deg, #eff6ff 0%, #f0f9ff 50%, #f8fafc 100%);
 46→    min-height: 100vh;
 47→    color: #0f172a;
 48→  }
 49→  .container {
 50→    max-width: 800px;
 51→    margin: 0 auto;
 52→    padding: 40px 20px;
 53→  }
 54→  .card {
 55→    background: white;
 56→    border-radius: 16px;
 57→    padding: 32px;
 58→    box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1);
 59→    margin-bottom: 20px;
 60→  }
 61→  h1 {
 62→    font-size: 24px;
 63→    margin-bottom: 8px;
 64→    color: #1e40af;
 65→  }
 66→  .subtitle {
 67→    color: #64748b;
 68→    margin-bottom: 24px;
 69→  }
 70→  .user-info {
 71→    display: flex;
 72→    align-items: center;
 73→    gap: 16px;
 74→    padding: 20px;
 75→    background: #f8fafc;
 76→    border-radius: 12px;
 77→    margin-bottom: 20px;
 78→  }
 79→  .avatar {
 80→    width: 56px;
 81→    height: 56px;
 82→    border-radius: 50%;
 83→    background: linear-gradient(135deg, #2563eb, #0ea5e9);
 84→    display: flex;
 85→    align-items: center;
 86→    justify-content: center;
 87→    color: white;
 88→    font-size: 24px;
 89→    font-weight: 600;
 90→  }
 91→  .btn {
 92→    display: inline-block;
 93→    padding: 10px 24px;
 94→    border: none;
 95→    border-radius: 8px;
 96→    font-size: 14px;
 97→    font-weight: 600;
 98→    cursor: pointer;
 99→    text-decoration: none;
    transition: all 0.2s;
  }
  .btn-primary {
    background: linear-gradient(135deg, #2563eb, #1d4ed8);
    color: white;
    box-shadow: 0 4px 12px rgba(37,99,235,0.3);
  }
  .btn-primary:hover { transform: translateY(-1px); }
  .btn-secondary {
    background: #f1f5f9;
    color: #475569;
  }
  .btn-secondary:hover { background: #e2e8f0; }
  .apps-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    margin-top: 20px;
  }
  .app-item {
    padding: 16px;
    background: #f8fafc;
    border-radius: 10px;
    text-align: center;
    text-decoration: none;
    color: #0f172a;
    transition: all 0.2s;
    border: 1px solid #e2e8f0;
  }
  .app-item:hover {
    border-color: #2563eb;
    transform: translateY(-2px);
  }
  .app-item .icon { font-size: 28px; margin-bottom: 8px; }
  .app-item .name { font-size: 13px; font-weight: 500; }
  .badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 600;
    background: #dbeafe;
    color: #1d4ed8;
  }
  .login-prompt {
    text-align: center;
    padding: 60px 20px;
  }
  .login-prompt .icon { font-size: 64px; margin-bottom: 20px; }
  .login-prompt h2 { margin-bottom: 12px; }
  .login-prompt p { color: #64748b; margin-bottom: 24px; }
  .sso-status {
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 10px 16px;
    background: white;
    border-radius: 10px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    font-size: 13px;
    z-index: 1000;
  }
  .sso-status .dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 6px;
    animation: pulse 2s infinite;
  }
  .dot.active { background: #10b981; }
  .dot.inactive { background: #f59e0b; }
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }
</style>
</head>
<body>
<div class="container">
  <div class="card">
    {% if user %}
      <h1>🔓 {{ app_name }}</h1>
      <p class="subtitle">已通过 NovaSSO 统一登录认证</p>

      <div class="user-info">
        <div class="avatar">{{ user.username[0]|upper }}</div>
        <div>
          <div style="font-weight:600;font-size:16px;">{{ user.nickname or user.username }}</div>
          <div style="color:#64748b;font-size:13px;">{{ user.username }} · {{ user.email or '未设置邮箱' }}</div>
          <div style="margin-top:4px;">
            {% if user.is_admin %}
            <span class="badge">管理员</span>
            {% endif %}
            <span class="badge" style="background:#ecfdf5;color:#059669;">SSO 已登录</span>
          </div>
        </div>
      </div>

      <div style="display:flex;gap:10px;margin-bottom:20px;">
        <a href="{{ logout_url }}" class="btn btn-secondary">退出登录</a>
      </div>

      <h3 style="margin-bottom:12px;font-size:16px;">🔗 其他系统（无感切换）</h3>
      <div class="apps-grid">
        <a href="http://localhost:5001" class="app-item">
          <div class="icon">🔍</div>
          <div class="name">搜索引擎</div>
        </a>
        <a href="http://localhost:5002" class="app-item">
          <div class="icon">📋</div>
          <div class="name">备案系统</div>
        </a>
        <a href="http://localhost:5003" class="app-item">
          <div class="icon">🔗</div>
          <div class="name">AutoPeer</div>
        </a>
      </div>

    {% else %}
      <div class="login-prompt">
        <div class="icon">🔐</div>
        <h2>欢迎使用 {{ app_name }}</h2>
        <p>请通过 NovaSSO 统一身份认证中心登录</p>
        <a href="{{ login_url }}" class="btn btn-primary">统一登录</a>
      </div>
    {% endif %}
  </div>
</div>

<!-- SSO 状态指示器 -->
<div class="sso-status">
  <span class="dot {{ 'active' if user else 'inactive' }}"></span>
  {{ '已登录' if user else '未登录' }} · {{ app_name }}
</div>

<!-- 引入无感登录 SDK -->
<script src="https://cdn.jsdelivr.net/npm/iframe-resizer@4.3.9/js/iframeResizer.min.js"></script>
<script>
// 简化版：页面加载时自动检查登录状态
// 实际项目中使用 nova-sso.js SDK
document.addEventListener('DOMContentLoaded', function() {
  // 如果用户未登录，尝试无感登录
  {% if not user %}
  console.log('[SSO] 尝试无感登录...');
  // 创建隐藏 iframe
  var iframe = document.createElement('iframe');
  iframe.style.display = 'none';
  iframe.src = '{{ sso_url }}/login?service={{ callback_url }}&app={{ app_id }}&silent=true';
  document.body.appendChild(iframe);

  // 监听消息（演示简化版）
  setTimeout(function() {
    console.log('[SSO] 无感登录检查完成');
  }, 2000);
  {% endif %}
});
</script>

</body>
</html>
"""


# ====== 路由 ======

@app.route("/")
def index():
    user = session.get("user")
    return render_template_string(
        PAGE_TEMPLATE,
        user=user,
        app_name=APP_NAME,
        login_url=sso.get_login_url(redirect=request.url_root),
        logout_url=sso.get_logout_url(redirect=request.url_root),
        sso_url=SSO_URL,
        callback_url=CALLBACK_URL,
        app_id=APP_ID,
    )


@app.route("/sso/callback")
def sso_callback():
    """SSO 回调：接收并验证ST"""
    ticket = request.args.get("ticket")

    if ticket:
        user = sso.validate_ticket(ticket)
        if user:
            session["user"] = user
            return redirect("/")

    return "登录验证失败", 401


@app.route("/sso/silent-callback")
def sso_silent_callback():
    """无感登录回调页（前端用）"""
    ticket = request.args.get("ticket")
    error = request.args.get("error")

    user = None
    if ticket:
        user = sso.validate_ticket(ticket)
        if user:
            session["user"] = user

    return f"""
    <!DOCTYPE html>
    <html><body><script>
    (function() {{
      var data = {{
        type: 'nova_sso_auth',
        success: {str(bool(user)).lower()},
        user: {str(user) if user else 'null'},
        error: '{error or ''}'
      }};
      if (window.parent && window.parent !== window) {{
        window.parent.postMessage(data, '*');
      }}
    }})();
    </script></body></html>
    """


@app.route("/api/sso-validate")
def sso_validate_api():
    """前端调用的验证接口"""
    ticket = request.args.get("ticket")
    if not ticket:
        return jsonify({"success": False, "error": "no ticket"})

    user = sso.validate_ticket(ticket)
    if user:
        session["user"] = user
        return jsonify({"success": True, "user": user})

    return jsonify({"success": False, "error": "invalid ticket"})


@app.route("/logout")
def logout():
    session.clear()
    return redirect(sso.get_logout_url(redirect=request.url_root))


@app.route("/api/user")
def api_user():
    user = session.get("user")
    if not user:
        return jsonify({"success": False, "error": "not logged in"}), 401
    return jsonify({"success": True, "user": user})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"🚀 {APP_NAME} 启动: http://localhost:{port}")
    print(f"   SSO Server: {SSO_URL}")
    print(f"   App ID: {APP_ID}")
    app.run(host="0.0.0.0", port=port, debug=True)