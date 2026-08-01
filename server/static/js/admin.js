  1→/**
  2→ * NovaSSO 管理后台前端逻辑
  3→ * 蓝白色调 · 现代化设计
  4→ */
  5→
  6→const API_BASE = '/api/admin';
  7→
  8→// 当前页面
  9→let currentPage = 'dashboard';
 10→let currentPageNum = 1;
 11→
 12→// 初始化
 13→document.addEventListener('DOMContentLoaded', function() {
 14→  // 侧边栏点击事件
 15→  document.querySelectorAll('.sidebar-item').forEach(item => {
 16→    item.addEventListener('click', function() {
 17→      const page = this.dataset.page;
 18→      switchPage(page);
 19→    });
 20→  });
 21→
 22→  // 加载仪表盘
 23→  loadDashboard();
 24→});
 25→
 26→// 切换页面
 27→function switchPage(page) {
 28→  currentPage = page;
 29→  currentPageNum = 1;
 30→
 31→  // 更新侧边栏激活状态
 32→  document.querySelectorAll('.sidebar-item').forEach(item => {
 33→    item.classList.remove('active');
 34→    if (item.dataset.page === page) {
 35→      item.classList.add('active');
 36→    }
 37→  });
 38→
 39→  // 加载对应页面
 40→  switch(page) {
 41→    case 'dashboard': loadDashboard(); break;
 42→    case 'users': loadUsers(); break;
 43→    case 'apps': loadApps(); break;
 44→    case 'sessions': loadSessions(); break;
 45→    case 'audit': loadAudit(); break;
 46→    case 'cluster': loadCluster(); break;
 47→  }
 48→}
 49→
 50→// 通用请求函数
 51→async function apiGet(url) {
 52→  try {
 53→    const res = await fetch(API_BASE + url, { credentials: 'include' });
 54→    if (res.status === 401) {
 55→      window.location.href = '/login?redirect=/admin';
 56→      return null;
 57→    }
 58→    return await res.json();
 59→  } catch (e) {
 60→    console.error('API请求失败:', e);
 61→    return { success: false, error: e.message };
 62→  }
 63→}
 64→
 65→async function apiPost(url, data) {
 66→  try {
 67→    const res = await fetch(API_BASE + url, {
 68→      method: 'POST',
 69→      headers: { 'Content-Type': 'application/json' },
 70→      credentials: 'include',
 71→      body: JSON.stringify(data)
 72→    });
 73→    if (res.status === 401) {
 74→      window.location.href = '/login?redirect=/admin';
 75→      return null;
 76→    }
 77→    return await res.json();
 78→  } catch (e) {
 79→    console.error('API请求失败:', e);
 80→    return { success: false, error: e.message };
 81→  }
 82→}
 83→
 84→// ========== 仪表盘 ==========
 85→
 86→async function loadDashboard() {
 87→  const data = await apiGet('/stats');
 88→  if (!data || !data.success) return;
 89→
 90→  const stats = data.stats;
 91→  const cluster = data.cluster;
 92→
 93→  document.getElementById('admin-content').innerHTML = `
 94→    <div class="page-header">
 95→      <h1 class="page-title">仪表盘</h1>
 96→      <p class="page-subtitle">系统运行概览与关键指标</p>
 97→    </div>
 98→
 99→    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon primary">👥</div>
        <div class="stat-value">${stats.total_users}</div>
        <div class="stat-label">总用户数</div>
      </div>
      <div class="stat-card">
        <div class="stat-icon success">📱</div>
        <div class="stat-value">${stats.total_apps}</div>
        <div class="stat-label">接入应用</div>
      </div>
      <div class="stat-card">
        <div class="stat-icon accent">🔐</div>
        <div class="stat-value">${stats.active_sessions}</div>
        <div class="stat-label">活跃会话</div>
      </div>
      <div class="stat-card">
        <div class="stat-icon warning">📊</div>
        <div class="stat-value">${stats.today_logins}</div>
        <div class="stat-label">今日登录</div>
      </div>
    </div>

    <div class="card">
      <div class="card-header">
        <span class="card-title">🌐 集群状态</span>
        <span class="badge ${cluster.multi_center ? 'badge-success' : 'badge-muted'}">
          ${cluster.multi_center ? '多中心模式' : '单节点模式'}
        </span>
      </div>
      <table class="data-table">
        <thead>
          <tr>
            <th>节点ID</th>
            <th>节点名称</th>
            <th>角色</th>
            <th>状态</th>
            <th>最后心跳</th>
          </tr>
        </thead>
        <tbody>
          ${cluster.nodes.map(n => `
            <tr>
              <td class="text-primary">${n.node_id}</td>
              <td>${n.node_name || '-'}</td>
              <td><span class="badge badge-primary">${n.node_role}</span></td>
              <td>
                <span class="badge ${n.status === 'online' ? 'badge-success' : 'badge-error'}">
                  ${n.status === 'online' ? '在线' : '离线'}
                </span>
              </td>
              <td class="text-muted">${n.last_heartbeat || '-'}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
  `;
}

// ========== 用户管理 ==========

async function loadUsers(keyword = '') {
  const data = await apiGet(`/users?page=${currentPageNum}&page_size=20&keyword=${encodeURIComponent(keyword)}`);
  if (!data || !data.success) return;

  const result = data.data;

  document.getElementById('admin-content').innerHTML = `
    <div class="page-header">
      <h1 class="page-title">用户管理</h1>
      <p class="page-subtitle">管理系统用户账号与权限</p>
    </div>

    <div class="card">
      <div class="card-header">
        <span class="card-title">用户列表 (共 ${result.total} 人)</span>
        <div style="display:flex;gap:10px;">
          <input type="text" id="user-search" placeholder="搜索用户名/邮箱..."
                 style="padding:8px 12px;border:1px solid var(--border);border-radius:var(--radius-sm);font-size:13px;width:240px;"
                 value="${keyword}">
          <button class="btn btn-primary btn-sm" onclick="searchUsers()">搜索</button>
          <button class="btn btn-secondary btn-sm" onclick="showCreateUserModal()">+ 新建用户</button>
        </div>
      </div>

      <table class="data-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>用户名</th>
            <th>邮箱</th>
            <th>昵称</th>
            <th>角色</th>
            <th>状态</th>
            <th>最后登录</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          ${result.items.map(u => `
            <tr>
              <td>${u.id}</td>
              <td class="text-primary">${u.username}</td>
              <td>${u.email || '-'}</td>
              <td>${u.nickname || '-'}</td>
              <td>
                <span class="badge ${u.is_admin ? 'badge-primary' : 'badge-muted'}">
                  ${u.is_admin ? '管理员' : '普通用户'}
                </span>
              </td>
              <td>
                <span class="badge ${u.is_active ? 'badge-success' : 'badge-error'}">
                  ${u.is_active ? '正常' : '禁用'}
                </span>
              </td>
              <td class="text-muted">${u.last_login_at ? new Date(u.last_login_at).toLocaleString('zh-CN') : '从未登录'}</td>
              <td>
                <button class="btn btn-sm" style="background:transparent;color:var(--primary);border:none;padding:4px 8px;"
                        onclick="forceLogoutUser(${u.id}, '${u.username}')">强制下线</button>
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>

      ${renderPagination(result.total, result.page, result.page_size)}
    </div>

    <!-- 新建用户模态框 -->
    <div id="create-user-modal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:1000;align-items:center;justify-content:center;">
      <div style="background:white;border-radius:16px;padding:32px;width:480px;max-width:90vw;">
        <h3 style="margin-bottom:20px;">新建用户</h3>
        <div class="form-group">
          <label>用户名 *</label>
          <input type="text" id="new-username" placeholder="请输入用户名">
        </div>
        <div class="form-group">
          <label>密码 *</label>
          <input type="password" id="new-password" placeholder="请输入密码">
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>邮箱</label>
            <input type="email" id="new-email" placeholder="选填">
          </div>
          <div class="form-group">
            <label>昵称</label>
            <input type="text" id="new-nickname" placeholder="选填">
          </div>
        </div>
        <div class="form-group">
          <label style="display:flex;align-items:center;gap:8px;">
            <input type="checkbox" id="new-is-admin">
            <span>设为管理员</span>
          </label>
        </div>
        <div class="form-actions">
          <button class="btn btn-secondary btn-sm" onclick="hideCreateUserModal()">取消</button>
          <button class="btn btn-primary btn-sm" onclick="createUser()">创建</button>
        </div>
      </div>
    </div>
  `;
}

function searchUsers() {
  currentPageNum = 1;
  const keyword = document.getElementById('user-search').value;
  loadUsers(keyword);
}

function showCreateUserModal() {
  document.getElementById('create-user-modal').style.display = 'flex';
}

function hideCreateUserModal() {
  document.getElementById('create-user-modal').style.display = 'none';
}

async function createUser() {
  const userData = {
    username: document.getElementById('new-username').value,
    password: document.getElementById('new-password').value,
    email: document.getElementById('new-email').value,
    nickname: document.getElementById('new-nickname').value,
    is_admin: document.getElementById('new-is-admin').checked
  };

  const result = await apiPost('/users', userData);
  if (result.success) {
    alert('用户创建成功！');
    hideCreateUserModal();
    loadUsers();
  } else {
    alert('创建失败: ' + (result.error || '未知错误'));
  }
}

async function forceLogoutUser(userId, username) {
  if (!confirm(`确定要强制下线用户 "${username}" 的所有会话吗？`)) return;

  // 获取用户会话列表
  const sessions = await apiGet(`/sessions?user_id=${userId}`);
  if (sessions && sessions.success) {
    for (const s of sessions.data) {
      await apiPost(`/sessions/${s.tgt_id}/revoke`, {});
    }
    alert('已强制下线所有会话');
    loadUsers();
  }
}

// ========== 应用管理 ==========

async function loadApps() {
  const data = await apiGet('/apps');
  if (!data || !data.success) return;

  const apps = data.data;

  document.getElementById('admin-content').innerHTML = `
    <div class="page-header">
      <h1 class="page-title">应用管理</h1>
      <p class="page-subtitle">管理接入统一登录的业务系统</p>
    </div>

    <div class="card">
      <div class="card-header">
        <span class="card-title">应用列表 (共 ${apps.length} 个)</span>
        <button class="btn btn-primary btn-sm" onclick="showCreateAppModal()">+ 新建应用</button>
      </div>

      <table class="data-table">
        <thead>
          <tr>
            <th>应用ID</th>
            <th>应用名称</th>
            <th>回调地址</th>
            <th>描述</th>
            <th>状态</th>
            <th>创建时间</th>
          </tr>
        </thead>
        <tbody>
          ${apps.map(a => `
            <tr>
              <td class="text-primary">${a.app_id}</td>
              <td>${a.app_name}</td>
              <td style="font-size:12px;color:var(--text-muted);word-break:break-all;">${a.callback_url}</td>
              <td>${a.app_description || '-'}</td>
              <td><span class="badge ${a.is_active ? 'badge-success' : 'badge-error'}">${a.is_active ? '启用' : '禁用'}</span></td>
              <td class="text-muted">${new Date(a.created_at).toLocaleDateString('zh-CN')}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>

    <!-- 新建应用模态框 -->
    <div id="create-app-modal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:1000;align-items:center;justify-content:center;">
      <div style="background:white;border-radius:16px;padding:32px;width:520px;max-width:90vw;">
        <h3 style="margin-bottom:20px;">新建应用</h3>
        <div class="form-group">
          <label>应用ID *</label>
          <input type="text" id="new-app-id" placeholder="如: search, icp, autopeer">
        </div>
        <div class="form-group">
          <label>应用名称 *</label>
          <input type="text" id="new-app-name" placeholder="如: 搜索引擎系统">
        </div>
        <div class="form-group">
          <label>回调地址 *</label>
          <input type="text" id="new-callback-url" placeholder="https://app.example.com/sso/callback">
        </div>
        <div class="form-group">
          <label>登出回调地址</label>
          <input type="text" id="new-logout-url" placeholder="选填，用于单点登出">
        </div>
        <div class="form-group">
          <label>应用描述</label>
          <textarea id="new-app-desc" placeholder="选填"></textarea>
        </div>
        <div class="form-actions">
          <button class="btn btn-secondary btn-sm" onclick="hideCreateAppModal()">取消</button>
          <button class="btn btn-primary btn-sm" onclick="createApp()">创建</button>
        </div>
      </div>
    </div>
  `;
}

function showCreateAppModal() {
  document.getElementById('create-app-modal').style.display = 'flex';
}

function hideCreateAppModal() {
  document.getElementById('create-app-modal').style.display = 'none';
}

async function createApp() {
  const appData = {
    app_id: document.getElementById('new-app-id').value,
    app_name: document.getElementById('new-app-name').value,
    callback_url: document.getElementById('new-callback-url').value,
    logout_url: document.getElementById('new-logout-url').value,
    app_description: document.getElementById('new-app-desc').value
  };

  const result = await apiPost('/apps', appData);
  if (result.success) {
    alert(`应用创建成功！\n\n应用密钥: ${result.app_secret}\n\n请妥善保存，只显示一次。`);
    hideCreateAppModal();
    loadApps();
  } else {
    alert('创建失败: ' + (result.error || '未知错误'));
  }
}

// ========== 在线会话 ==========

async function loadSessions() {
  const data = await apiGet('/sessions');
  if (!data || !data.success) return;

  const sessions = data.data;

  document.getElementById('admin-content').innerHTML = `
    <div class="page-header">
      <h1 class="page-title">在线会话</h1>
      <p class="page-subtitle">查看当前活跃的用户会话</p>
    </div>

    <div class="card">
      <div class="card-header">
        <span class="card-title">活跃会话 (共 ${sessions.length} 个)</span>
      </div>

      <table class="data-table">
        <thead>
          <tr>
            <th>用户</th>
            <th>IP地址</th>
            <th>设备</th>
            <th>节点</th>
            <th>登录时间</th>
            <th>最后活跃</th>
            <th>过期时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          ${sessions.map(s => `
            <tr>
              <td class="text-primary">${s.username}</td>
              <td>${s.ip || '-'}</td>
              <td class="text-muted" style="font-size:12px;max-width:200px;overflow:hidden;text-overflow:ellipsis;">${s.user_agent ? s.user_agent.substring(0, 50) + '...' : '-'}</td>
              <td><span class="badge badge-primary">${s.node_id || '-'}</span></td>
              <td class="text-muted">${new Date(s.created_at).toLocaleString('zh-CN')}</td>
              <td class="text-muted">${new Date(s.last_active_at).toLocaleString('zh-CN')}</td>
              <td class="text-warning">${new Date(s.expires_at).toLocaleString('zh-CN')}</td>
              <td>
                <button class="btn btn-danger btn-sm" onclick="revokeSession('${s.tgt_id}', '${s.username}')">下线</button>
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
  `;
}

async function revokeSession(tgtId, username) {
  if (!confirm(`确定要强制下线用户 "${username}" 的这个会话吗？`)) return;

  const result = await apiPost(`/sessions/${tgtId}/revoke`, {});
  if (result.success) {
    loadSessions();
  }
}

// ========== 审计日志 ==========

async function loadAudit() {
  const data = await apiGet(`/audit?page=${currentPageNum}&page_size=20`);
  if (!data || !data.success) return;

  const result = data.data;

  document.getElementById('admin-content').innerHTML = `
    <div class="page-header">
      <h1 class="page-title">审计日志</h1>
      <p class="page-subtitle">查看系统操作记录与安全审计</p>
    </div>

    <div class="card">
      <div class="card-header">
        <span class="card-title">日志记录 (共 ${result.total} 条)</span>
      </div>

      <table class="data-table">
        <thead>
          <tr>
            <th>时间</th>
            <th>用户</th>
            <th>操作</th>
            <th>目标</th>
            <th>IP</th>
            <th>状态</th>
            <th>节点</th>
          </tr>
        </thead>
        <tbody>
          ${result.items.map(log => `
            <tr>
              <td class="text-muted" style="white-space:nowrap;font-size:12px;">${new Date(log.created_at).toLocaleString('zh-CN')}</td>
              <td class="text-primary">${log.username || '-'}</td>
              <td>${log.action}</td>
              <td class="text-muted">${log.target || '-'}</td>
              <td style="font-size:12px;">${log.ip || '-'}</td>
              <td>
                <span class="badge ${log.success ? 'badge-success' : 'badge-error'}">
                  ${log.success ? '成功' : '失败'}
                </span>
              </td>
              <td><span class="badge badge-muted">${log.node_id || '-'}</span></td>
            </tr>
          `).join('')}
        </tbody>
      </table>

      ${renderPagination(result.total, result.page, result.page_size)}
    </div>
  `;
}

// ========== 集群状态 ==========

async function loadCluster() {
  const data = await apiGet('/stats');
  if (!data || !data.success) return;

  const cluster = data.cluster;

  document.getElementById('admin-content').innerHTML = `
    <div class="page-header">
      <h1 class="page-title">集群状态</h1>
      <p class="page-subtitle">多中心架构节点状态监控</p>
    </div>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon primary">🌐</div>
        <div class="stat-value">${cluster.total_nodes}</div>
        <div class="stat-label">总节点数</div>
      </div>
      <div class="stat-card">
        <div class="stat-icon success">✅</div>
        <div class="stat-value">${cluster.online_nodes}</div>
        <div class="stat-label">在线节点</div>
      </div>
      <div class="stat-card">
        <div class="stat-icon accent">📍</div>
        <div class="stat-value" style="font-size:18px;">${cluster.current_node}</div>
        <div class="stat-label">当前节点</div>
      </div>
      <div class="stat-card">
        <div class="stat-icon warning">⚙️</div>
        <div class="stat-value" style="font-size:18px;">${cluster.current_role}</div>
        <div class="stat-label">节点角色</div>
      </div>
    </div>

    <div class="card">
      <div class="card-header">
        <span class="card-title">节点列表</span>
        <span class="badge ${cluster.multi_center ? 'badge-success' : 'badge-muted'}">
          ${cluster.multi_center ? '多中心架构' : '单节点运行'}
        </span>
      </div>

      <table class="data-table">
        <thead>
          <tr>
            <th>节点ID</th>
            <th>节点名称</th>
            <th>角色</th>
            <th>状态</th>
            <th>最后心跳</th>
            <th>最后同步</th>
          </tr>
        </thead>
        <tbody>
          ${cluster.nodes.map(n => `
            <tr>
              <td class="text-primary">${n.node_id}</td>
              <td>${n.node_name || '-'}</td>
              <td><span class="badge badge-primary">${n.node_role}</span></td>
              <td>
                <span class="badge ${n.status === 'online' ? 'badge-success' : 'badge-error'}">
                  ${n.status === 'online' ? '● 在线' : '○ 离线'}
                </span>
              </td>
              <td class="text-muted">${n.last_heartbeat ? new Date(n.last_heartbeat).toLocaleString('zh-CN') : '-'}</td>
              <td class="text-muted">${n.last_sync_at ? new Date(n.last_sync_at).toLocaleString('zh-CN') : '-'}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>

    <div class="card">
      <div class="card-header">
        <span class="card-title">📖 多中心配置说明</span>
      </div>
      <div style="color:var(--text-secondary);font-size:13px;line-height:1.8;">
        <p><strong>当前模式：</strong>${cluster.multi_center ? '多中心模式' : '单节点模式'}</p>
        <p><strong>配置方式：</strong>通过环境变量配置对等节点，实现数据自动同步</p>
        <ul style="margin-left:20px;margin-top:8px;">
          <li><code>NOVA_NODE_ID</code> - 当前节点ID</li>
          <li><code>NOVA_NODE_NAME</code> - 节点名称</li>
          <li><code>NOVA_NODE_ROLE</code> - 节点角色 (master/slave/peer)</li>
          <li><code>NOVA_PEERS</code> - 对等节点地址，逗号分隔</li>
          <li><code>NOVA_SYNC_KEY</code> - 节点间同步密钥</li>
          <li><code>NOVA_SYNC_INTERVAL</code> - 同步间隔（秒）</li>
        </ul>
      </div>
    </div>
  `;
}

// ========== 分页 ==========

function renderPagination(total, page, pageSize) {
  const totalPages = Math.ceil(total / pageSize);
  if (totalPages <= 1) return '';

  let pages = [];
  const maxVisible = 5;
  let start = Math.max(1, page - Math.floor(maxVisible / 2));
  let end = Math.min(totalPages, start + maxVisible - 1);
  start = Math.max(1, end - maxVisible + 1);

  for (let i = start; i <= end; i++) {
    pages.push(i);
  }

  return `
    <div class="pagination">
      <button ${page <= 1 ? 'disabled' : ''} onclick="goToPage(${page - 1})">上一页</button>
      ${start > 1 ? '<button onclick="goToPage(1)">1</button>' : ''}
      ${start > 2 ? '<span style="padding:0 8px;color:var(--text-muted);">...</span>' : ''}
      ${pages.map(p => `
        <button class="${p === page ? 'active' : ''}" onclick="goToPage(${p})">${p}</button>
      `).join('')}
      ${end < totalPages - 1 ? '<span style="padding:0 8px;color:var(--text-muted);">...</span>' : ''}
      ${end < totalPages ? `<button onclick="goToPage(${totalPages})">${totalPages}</button>` : ''}
      <button ${page >= totalPages ? 'disabled' : ''} onclick="goToPage(${page + 1})">下一页</button>
    </div>
  `;
}

function goToPage(page) {
  currentPageNum = page;
  switch(currentPage) {
    case 'users': loadUsers(); break;
    case 'audit': loadAudit(); break;
  }
}