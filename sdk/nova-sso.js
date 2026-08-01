  1→/**
  2→ * NovaSSO 前端无感登录 SDK
  3→ * 基于隐藏 iframe + postMessage 实现跨域无感登录
  4→ *
  5→ * 使用方式:
  6→ *   const sso = new NovaSSO({
  7→ *     ssoUrl: 'https://sso.yourdomain.dn42',
  8→ *     callbackUrl: 'https://your-app/sso/silent-callback.html'
  9→ *   });
 10→ *
 11→ *   // 页面加载时尝试无感登录
 12→ *   sso.trySilentLogin().then(user => {
 13→ *     console.log('登录成功', user);
 14→ *   }).catch(() => {
 15→ *     console.log('需要手动登录');
 16→ *   });
 17→ */
 18→
 19→class NovaSSO {
 20→  constructor(options) {
 21→    this.ssoUrl = options.ssoUrl.replace(/\/$/, '');
 22→    this.callbackUrl = options.callbackUrl;
 23→    this.appId = options.appId || '';
 24→    this.timeout = options.timeout || 5000;
 25→    this.user = null;
 26→    this._storageKey = 'nova_sso_user';
 27→
 28→    // 从本地存储恢复用户信息
 29→    const saved = localStorage.getItem(this._storageKey);
 30→    if (saved) {
 31→      try {
 32→        this.user = JSON.parse(saved);
 33→      } catch (e) {}
 34→    }
 35→  }
 36→
 37→  /**
 38→   * 尝试无感登录
 39→   * @returns {Promise<Object>} 用户信息
 40→   */
 41→  async trySilentLogin() {
 42→    return new Promise((resolve, reject) => {
 43→      // 已有用户信息，直接返回
 44→      if (this.user) {
 45→        resolve(this.user);
 46→        return;
 47→      }
 48→
 49→      const iframe = document.createElement('iframe');
 50→      iframe.style.display = 'none';
 51→      iframe.style.position = 'absolute';
 52→      iframe.style.width = '0';
 53→      iframe.style.height = '0';
 54→      iframe.style.border = 'none';
 55→      iframe.setAttribute('sandbox', 'allow-scripts allow-same-origin allow-forms');
 56→
 57→      const params = new URLSearchParams({
 58→        service: this.callbackUrl,
 59→        app: this.appId,
 60→        silent: 'true'
 61→      });
 62→
 63→      iframe.src = `${this.ssoUrl}/login?${params.toString()}`;
 64→
 65→      let resolved = false;
 66→
 67→      const messageHandler = (e) => {
 68→        // 验证消息来源（生产环境请精确匹配）
 69→        if (e.data && e.data.type === 'nova_sso_auth') {
 70→          resolved = true;
 71→          this._cleanup(iframe, messageHandler, timeoutId);
 72→
 73→          if (e.data.success && e.data.user) {
 74→            this.user = e.data.user;
 75→            localStorage.setItem(this._storageKey, JSON.stringify(this.user));
 76→            resolve(this.user);
 77→          } else {
 78→            reject(new Error(e.data.error || '登录失败'));
 79→          }
 80→        }
 81→      };
 82→
 83→      const timeoutId = setTimeout(() => {
 84→        if (!resolved) {
 85→          this._cleanup(iframe, messageHandler, timeoutId);
 86→          reject(new Error('SSO 登录超时'));
 87→        }
 88→      }, this.timeout);
 89→
 90→      window.addEventListener('message', messageHandler);
 91→      document.body.appendChild(iframe);
 92→    });
 93→  }
 94→
 95→  /**
 96→   * 跳转到登录页
 97→   * @param {string} redirect 登录后跳转地址
 98→   */
 99→  redirectToLogin(redirect = '') {
    const params = new URLSearchParams({
      service: this.callbackUrl,
      app: this.appId
    });
    if (redirect) {
      params.set('redirect', redirect);
    }
    window.location.href = `${this.ssoUrl}/login?${params.toString()}`;
  }

  /**
   * 跳转到登出页
   * @param {string} redirect 登出后跳转地址
   */
  redirectToLogout(redirect = '') {
    this.user = null;
    localStorage.removeItem(this._storageKey);
    const params = redirect ? `?redirect=${encodeURIComponent(redirect)}` : '';
    window.location.href = `${this.ssoUrl}/logout${params}`;
  }

  /**
   * 获取当前用户
   * @returns {Object|null}
   */
  getCurrentUser() {
    return this.user;
  }

  /**
   * 检查是否已登录
   * @returns {boolean}
   */
  isLoggedIn() {
    return !!this.user;
  }

  /**
   * 清除本地登录状态
   */
  clearLocalAuth() {
    this.user = null;
    localStorage.removeItem(this._storageKey);
  }

  // 清理
  _cleanup(iframe, handler, timeoutId) {
    window.removeEventListener('message', handler);
    if (timeoutId) clearTimeout(timeoutId);
    if (iframe.parentNode) {
      iframe.parentNode.removeChild(iframe);
    }
  }
}

/**
 * 静默回调页脚本
 * 在 silent-callback.html 中引入
 * 作用：接收ST，验证后通过 postMessage 通知父页面
 */
NovaSSO.handleSilentCallback = async function(validateUrl = '/api/sso-validate') {
  const params = new URLSearchParams(window.location.search);
  const ticket = params.get('ticket');
  const error = params.get('error');

  const sendMessage = (data) => {
    if (window.parent && window.parent !== window) {
      window.parent.postMessage({
        type: 'nova_sso_auth',
        ...data
      }, '*'); // 生产环境请替换为具体的 origin
    }
  };

  if (ticket) {
    try {
      const resp = await fetch(`${validateUrl}?ticket=${encodeURIComponent(ticket)}`);
      const data = await resp.json();
      if (data.success) {
        sendMessage({ success: true, user: data.user });
      } else {
        sendMessage({ success: false, error: data.error || '验证失败' });
      }
    } catch (e) {
      sendMessage({ success: false, error: e.message });
    }
  } else {
    sendMessage({ success: false, error: error || '需要登录' });
  }
};

// CommonJS / ES Module 兼容
if (typeof module !== 'undefined' && module.exports) {
  module.exports = NovaSSO;
}
if (typeof window !== 'undefined') {
  window.NovaSSO = NovaSSO;
}