<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Douyin-to-Text 管理面板</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700&display=swap" rel="stylesheet">
<style>
:root {
  --bg: #0a0a0f;
  --surface: #13131a;
  --surface2: #1a1a24;
  --border: #2a2a3a;
  --text: #e8e8f0;
  --text2: #8888a0;
  --accent: #6c5ce7;
  --accent2: #a29bfe;
  --green: #00b894;
  --red: #ff6b6b;
  --orange: #fdcb6e;
  --blue: #74b9ff;
  --radius: 12px;
  --shadow: 0 4px 24px rgba(0,0,0,0.4);
}

* { margin:0; padding:0; box-sizing:border-box; }

body {
  font-family: 'Noto Sans SC', -apple-system, sans-serif;
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
}

/* ---- Layout ---- */
.app { display: flex; min-height: 100vh; }

.sidebar {
  width: 220px;
  background: var(--surface);
  border-right: 1px solid var(--border);
  padding: 24px 0;
  flex-shrink: 0;
  position: fixed;
  height: 100vh;
  overflow-y: auto;
}

.sidebar .logo {
  padding: 0 20px 24px;
  font-size: 18px;
  font-weight: 700;
  color: var(--accent2);
  border-bottom: 1px solid var(--border);
  margin-bottom: 16px;
}

.sidebar .logo span { font-size: 22px; margin-right: 8px; }

.nav-item {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 20px;
  cursor: pointer;
  color: var(--text2);
  transition: all 0.2s;
  font-size: 14px;
  border-left: 3px solid transparent;
}

.nav-item:hover { background: var(--surface2); color: var(--text); }
.nav-item.active {
  color: var(--accent2);
  background: rgba(108,92,231,0.1);
  border-left-color: var(--accent);
}

.nav-item .icon { font-size: 18px; width: 24px; text-align: center; }

.main {
  margin-left: 220px;
  flex: 1;
  padding: 32px;
  max-width: 1100px;
}

.page { display: none; }
.page.active { display: block; }

.page-title {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 24px;
  color: var(--text);
}

/* ---- Cards ---- */
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  margin-bottom: 16px;
}

.card-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 12px;
}

.card-title { font-size: 16px; font-weight: 500; }

/* ---- Buttons ---- */
.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  font-family: inherit;
  transition: all 0.2s;
  display: inline-flex; align-items: center; gap: 6px;
}

.btn-primary { background: var(--accent); color: #fff; }
.btn-primary:hover { background: var(--accent2); }
.btn-sm { padding: 5px 10px; font-size: 12px; }
.btn-danger { background: var(--red); color: #fff; }
.btn-danger:hover { opacity: 0.8; }
.btn-outline {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text2);
}
.btn-outline:hover { border-color: var(--accent); color: var(--accent2); }
.btn-green { background: var(--green); color: #fff; }
.btn-green:hover { opacity: 0.85; }

/* ---- Tags ---- */
.tag {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 500;
}
.tag-finance { background: rgba(116,185,255,0.15); color: var(--blue); }
.tag-career { background: rgba(253,203,110,0.15); color: var(--orange); }
.tag-live { background: rgba(255,107,107,0.15); color: var(--red); }

/* ---- Table ---- */
.file-list { width: 100%; }

.file-row {
  display: flex; align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
  gap: 12px;
  transition: background 0.15s;
}
.file-row:hover { background: var(--surface2); }
.file-row:last-child { border-bottom: none; }

.file-icon { font-size: 20px; width: 28px; text-align: center; }
.file-name { flex: 1; font-size: 14px; cursor: pointer; color: var(--accent2); }
.file-name:hover { text-decoration: underline; }
.file-meta { color: var(--text2); font-size: 12px; white-space: nowrap; }
.file-actions { display: flex; gap: 6px; }

/* ---- Modal ---- */
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.7);
  display: flex; justify-content: center; align-items: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.modal {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  width: 90%; max-width: 800px; max-height: 85vh;
  display: flex; flex-direction: column;
  box-shadow: var(--shadow);
}

.modal-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
}

.modal-title { font-size: 16px; font-weight: 500; }

.modal-close {
  background: none; border: none; color: var(--text2);
  font-size: 20px; cursor: pointer; padding: 4px 8px;
}
.modal-close:hover { color: var(--text); }

.modal-body {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
  line-height: 1.8;
  font-size: 14px;
}

.modal-body h1, .modal-body h2, .modal-body h3 {
  margin: 16px 0 8px;
  color: var(--accent2);
}
.modal-body h1 { font-size: 20px; }
.modal-body h2 { font-size: 17px; }
.modal-body h3 { font-size: 15px; }
.modal-body p { margin-bottom: 8px; }

/* ---- Form ---- */
.form-group { margin-bottom: 14px; }
.form-label { display: block; font-size: 13px; color: var(--text2); margin-bottom: 4px; }
.form-input, .form-select {
  width: 100%; padding: 8px 12px;
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text);
  font-size: 14px;
  font-family: inherit;
}
.form-input:focus, .form-select:focus {
  outline: none; border-color: var(--accent);
}

/* ---- Task Log ---- */
.log-box {
  background: #000;
  border-radius: 8px;
  padding: 12px;
  font-family: 'Consolas', 'Courier New', monospace;
  font-size: 12px;
  color: var(--green);
  max-height: 300px;
  overflow-y: auto;
  white-space: pre-wrap;
  line-height: 1.6;
}

/* ---- Creator list ---- */
.creator-row {
  display: flex; align-items: center; gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid var(--border);
}
.creator-row:last-child { border-bottom: none; }
.creator-name { font-weight: 500; min-width: 120px; }
.creator-url { flex: 1; color: var(--text2); font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* ---- History ---- */
.history-creator { margin-bottom: 16px; }
.history-creator-name { font-weight: 500; margin-bottom: 8px; color: var(--accent2); }
.history-ids {
  display: flex; flex-wrap: wrap; gap: 6px;
}
.history-id {
  background: var(--surface2);
  padding: 3px 10px;
  border-radius: 6px;
  font-size: 11px;
  color: var(--text2);
  font-family: monospace;
}

/* ---- Status badge ---- */
.status-dot {
  width: 8px; height: 8px; border-radius: 50%;
  display: inline-block; margin-right: 6px;
}
.status-running { background: var(--orange); animation: pulse 1s infinite; }
.status-done { background: var(--green); }
.status-error { background: var(--red); }

@keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.3; } }

/* ---- Empty state ---- */
.empty { text-align: center; padding: 40px; color: var(--text2); }
.empty .icon { font-size: 40px; margin-bottom: 12px; }
</style>
</head>
<body>
<div class="app">
  <!-- Sidebar -->
  <div class="sidebar">
    <div class="logo"><span>🎬</span>D2T</div>
    <div class="nav-item active" data-page="dashboard"><span class="icon">📊</span>概览</div>
    <div class="nav-item" data-page="creators"><span class="icon">👤</span>博主管理</div>
    <div class="nav-item" data-page="word"><span class="icon">📄</span>转录文档</div>
    <div class="nav-item" data-page="analysis"><span class="icon">🤖</span>分析报告</div>
    <div class="nav-item" data-page="history"><span class="icon">📋</span>录制历史</div>
    <div class="nav-item" data-page="tasks"><span class="icon">⚡</span>任务控制</div>
  </div>

  <!-- Main content -->
  <div class="main">

    <!-- Dashboard -->
    <div class="page active" id="page-dashboard">
      <h1 class="page-title">📊 概览</h1>
      <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap:16px; margin-bottom:24px;">
        <div class="card" style="text-align:center;">
          <div style="font-size:32px; font-weight:700; color:var(--accent2);" id="stat-creators">-</div>
          <div style="color:var(--text2); font-size:13px;">博主数量</div>
        </div>
        <div class="card" style="text-align:center;">
          <div style="font-size:32px; font-weight:700; color:var(--green);" id="stat-words">-</div>
          <div style="color:var(--text2); font-size:13px;">转录文档</div>
        </div>
        <div class="card" style="text-align:center;">
          <div style="font-size:32px; font-weight:700; color:var(--blue);" id="stat-analysis">-</div>
          <div style="color:var(--text2); font-size:13px;">分析报告</div>
        </div>
      </div>
      <div class="card">
        <div class="card-title" style="margin-bottom:12px;">最近文档</div>
        <div id="recent-files"></div>
      </div>
    </div>

    <!-- Creators -->
    <div class="page" id="page-creators">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:24px;">
        <h1 class="page-title" style="margin:0;">👤 博主管理</h1>
        <button class="btn btn-primary" onclick="showAddCreator()">+ 添加博主</button>
      </div>
      <div class="card">
        <div class="card-title" style="margin-bottom:4px;">视频博主</div>
        <div id="creator-list"></div>
      </div>
      <div class="card">
        <div class="card-title" style="margin-bottom:4px;">直播博主</div>
        <div id="live-creator-list"></div>
      </div>
    </div>

    <!-- Word docs -->
    <div class="page" id="page-word">
      <h1 class="page-title">📄 转录文档</h1>
      <div class="card"><div id="word-files"></div></div>
    </div>

    <!-- Analysis -->
    <div class="page" id="page-analysis">
      <h1 class="page-title">🤖 分析报告</h1>
      <div class="card"><div id="analysis-files"></div></div>
    </div>

    <!-- History -->
    <div class="page" id="page-history">
      <h1 class="page-title">📋 录制历史</h1>
      <div class="card"><div id="history-content"></div></div>
    </div>

    <!-- Tasks -->
    <div class="page" id="page-tasks">
      <h1 class="page-title">⚡ 任务控制</h1>
      <div style="display:grid; grid-template-columns: repeat(2, 1fr); gap:16px; margin-bottom:24px;">
        <div class="card">
          <div class="card-title">🔴 录制直播</div>
          <p style="color:var(--text2); font-size:13px; margin:8px 0;">检查直播博主是否在播，在播就录</p>
          <button class="btn btn-green" onclick="startTask('live')">▶ 检查并录制</button>
        </div>
        <div class="card">
          <div class="card-title">📹 录制视频（需要 OBS）</div>
          <p style="color:var(--text2); font-size:13px; margin:8px 0;">浏览视频博主 + OBS 录屏</p>
          <button class="btn btn-primary" onclick="startTask('browse')">▶ 开始录制</button>
        </div>
        <div class="card">
          <div class="card-title">✍ 转录已有视频</div>
          <p style="color:var(--text2); font-size:13px; margin:8px 0;">转录 recordings 里的视频 → 导出 Word</p>
          <button class="btn btn-green" onclick="startTask('transcribe')">▶ 开始转录</button>
        </div>
        <div class="card">
          <div class="card-title">🤖 DeepSeek 分析</div>
          <p style="color:var(--text2); font-size:13px; margin:8px 0;">分析所有未处理的 Word 文档</p>
          <button class="btn btn-green" onclick="startTask('analyze')">▶ 开始分析</button>
        </div>
      </div>
      <div class="card" style="margin-bottom:16px;">
        <div class="card-title">🚀 全流程</div>
        <p style="color:var(--text2); font-size:13px; margin:8px 0;">直播检查 → 视频录制 → 转录 → 分析（全自动）</p>
        <button class="btn btn-primary" onclick="startTask('full')">▶ 全部运行</button>
      </div>
      <div class="card">
        <div class="card-header">
          <div class="card-title">任务日志</div>
          <span id="task-status"></span>
        </div>
        <div class="log-box" id="task-log">等待任务启动...</div>
      </div>
    </div>

  </div>
</div>

<!-- Modal (for viewing content and adding creators) -->
<div class="modal-overlay" id="modal" style="display:none;" onclick="if(event.target===this)closeModal()">
  <div class="modal">
    <div class="modal-header">
      <div class="modal-title" id="modal-title">文档内容</div>
      <button class="modal-close" onclick="closeModal()">✕</button>
    </div>
    <div class="modal-body" id="modal-body"></div>
  </div>
</div>

<script>
// ============================================================
//  Navigation
// ============================================================
document.querySelectorAll('.nav-item').forEach(item => {
  item.addEventListener('click', () => {
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    item.classList.add('active');
    document.getElementById('page-' + item.dataset.page).classList.add('active');

    // Load data for the page
    const page = item.dataset.page;
    if (page === 'dashboard') loadDashboard();
    if (page === 'creators') loadCreators();
    if (page === 'word') loadFiles('word', 'word-files');
    if (page === 'analysis') loadFiles('analysis', 'analysis-files');
    if (page === 'history') loadHistory();
  });
});

// ============================================================
//  API helpers
// ============================================================
async function api(url, opts = {}) {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  });
  return res.json();
}

// ============================================================
//  Dashboard
// ============================================================
async function loadDashboard() {
  const creators = await api('/api/creators');
  const words = await api('/api/files/word');
  const analysis = await api('/api/files/analysis');

  const total = (creators.creators?.length || 0) + (creators.live_creators?.length || 0);
  document.getElementById('stat-creators').textContent = total;
  document.getElementById('stat-words').textContent = words.files?.length || 0;
  document.getElementById('stat-analysis').textContent = analysis.files?.length || 0;

  // Recent files (combine word + analysis, sort by date)
  const all = [...(words.files || []), ...(analysis.files || [])];
  all.sort((a, b) => b.modified.localeCompare(a.modified));
  const recent = all.slice(0, 8);

  const container = document.getElementById('recent-files');
  if (recent.length === 0) {
    container.innerHTML = '<div class="empty"><div class="icon">📭</div>暂无文档</div>';
    return;
  }
  container.innerHTML = recent.map(f => fileRow(f)).join('');
}

// ============================================================
//  File listing
// ============================================================
function fileRow(f) {
  const icon = f.name.endsWith('.docx') ? '📄' : f.name.endsWith('.mp4') ? '🎥' : '📝';
  return `<div class="file-row">
    <span class="file-icon">${icon}</span>
    <span class="file-name" onclick="viewFile('${f.type}','${f.name}')">${f.name}</span>
    <span class="file-meta">${f.size_mb} MB</span>
    <span class="file-meta">${f.modified}</span>
    <div class="file-actions">
      <button class="btn btn-outline btn-sm" onclick="downloadFile('${f.type}','${f.name}')">下载</button>
    </div>
  </div>`;
}

async function loadFiles(type, containerId) {
  const data = await api('/api/files/' + type);
  const container = document.getElementById(containerId);
  if (!data.files || data.files.length === 0) {
    container.innerHTML = '<div class="empty"><div class="icon">📭</div>暂无文件</div>';
    return;
  }
  container.innerHTML = data.files.map(f => fileRow(f)).join('');
}

// ============================================================
//  View file content
// ============================================================
async function viewFile(type, filename) {
  if (filename.endsWith('.mp4')) {
    // Can't preview video
    downloadFile(type, filename);
    return;
  }

  document.getElementById('modal-title').textContent = filename;
  document.getElementById('modal-body').innerHTML = '<p style="color:var(--text2)">加载中...</p>';
  document.getElementById('modal').style.display = 'flex';

  const data = await api(`/api/files/${type}/${filename}/content`);
  const body = document.getElementById('modal-body');

  if (data.format === 'docx') {
    body.innerHTML = data.content.map(p => {
      if (p.type === 'heading') return `<h${p.level}>${esc(p.text)}</h${p.level}>`;
      return `<p>${esc(p.text)}</p>`;
    }).join('');
  } else if (data.format === 'text') {
    body.innerHTML = `<pre style="white-space:pre-wrap; color:var(--text); line-height:1.8;">${esc(data.content)}</pre>`;
  } else {
    body.innerHTML = `<p style="color:var(--red)">无法预览: ${esc(data.content)}</p>`;
  }
}

function downloadFile(type, filename) {
  window.open(`/api/files/${type}/${filename}/download`, '_blank');
}

function closeModal() {
  document.getElementById('modal').style.display = 'none';
}

function esc(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

// ============================================================
//  Creators
// ============================================================
async function loadCreators() {
  const data = await api('/api/creators');

  const renderList = (list, containerId) => {
    const container = document.getElementById(containerId);
    if (!list || list.length === 0) {
      container.innerHTML = '<div class="empty"><div class="icon">👤</div>暂无博主</div>';
      return;
    }
    container.innerHTML = list.map(c => `
      <div class="creator-row">
        <span class="creator-name">${esc(c.name)}</span>
        <span class="tag ${c.category === 'finance' ? 'tag-finance' : 'tag-career'}">
          ${c.category === 'finance' ? '💰 金融' : '💼 求职'}
        </span>
        ${c.schedule ? '<span class="tag tag-live">🔴 直播</span>' : ''}
        <span class="creator-url">${esc(c.url)}</span>
        <button class="btn btn-danger btn-sm" onclick="deleteCreator('${esc(c.name)}')">删除</button>
      </div>
    `).join('');
  };

  renderList(data.creators, 'creator-list');
  renderList(data.live_creators, 'live-creator-list');
}

async function deleteCreator(name) {
  if (!confirm(`确定删除博主「${name}」?`)) return;
  await api('/api/creators/' + encodeURIComponent(name), { method: 'DELETE' });
  loadCreators();
}

function showAddCreator() {
  document.getElementById('modal-title').textContent = '添加博主';
  document.getElementById('modal-body').innerHTML = `
    <div class="form-group">
      <label class="form-label">博主名称</label>
      <input class="form-input" id="add-name" placeholder="例: 机构一手调研">
    </div>
    <div class="form-group">
      <label class="form-label">抖音链接</label>
      <input class="form-input" id="add-url" placeholder="https://www.douyin.com/user/...">
    </div>
    <div class="form-group">
      <label class="form-label">类型</label>
      <select class="form-select" id="add-category">
        <option value="finance">💰 金融分析</option>
        <option value="career">💼 求职分析</option>
      </select>
    </div>
    <div class="form-group">
      <label class="form-label">每次录制条数</label>
      <input class="form-input" id="add-videos" type="number" value="1" min="1" max="20">
    </div>
    <div class="form-group">
      <label style="display:flex; align-items:center; gap:8px; cursor:pointer;">
        <input type="checkbox" id="add-is-live" onchange="toggleLiveFields()">
        <span class="form-label" style="margin:0;">这是直播博主</span>
      </label>
    </div>
    <div id="live-fields" style="display:none;">
      <div class="form-group">
        <label class="form-label">直播时间（24小时制）</label>
        <input class="form-input" id="add-time" placeholder="11:30">
      </div>
      <div class="form-group">
        <label class="form-label">直播星期（逗号分隔，周日=0 周一=1 ... 周六=6）</label>
        <input class="form-input" id="add-weekdays" placeholder="1,2,3,4,5">
      </div>
    </div>
    <button class="btn btn-primary" onclick="submitAddCreator()" style="width:100%; margin-top:8px;">添加</button>
  `;
  document.getElementById('modal').style.display = 'flex';
}

function toggleLiveFields() {
  document.getElementById('live-fields').style.display =
    document.getElementById('add-is-live').checked ? 'block' : 'none';
}

async function submitAddCreator() {
  const name = document.getElementById('add-name').value.trim();
  const url = document.getElementById('add-url').value.trim();
  if (!name || !url) { alert('请填写名称和链接'); return; }

  const body = {
    name, url,
    category: document.getElementById('add-category').value,
    videos: parseInt(document.getElementById('add-videos').value) || 1,
    is_live: document.getElementById('add-is-live').checked,
  };

  if (body.is_live) {
    body.time = document.getElementById('add-time').value.trim();
    const wd = document.getElementById('add-weekdays').value.trim();
    body.weekdays = wd ? wd.split(',').map(Number) : [1,2,3,4,5];
  }

  await api('/api/creators', { method: 'POST', body: JSON.stringify(body) });
  closeModal();
  loadCreators();
}

// ============================================================
//  History
// ============================================================
async function loadHistory() {
  const data = await api('/api/history');
  const container = document.getElementById('history-content');

  const history = data.history || {};
  const names = Object.keys(history);

  if (names.length === 0) {
    container.innerHTML = '<div class="empty"><div class="icon">📋</div>暂无录制历史</div>';
    return;
  }

  container.innerHTML = names.map(name => `
    <div class="history-creator">
      <div class="history-creator-name">${esc(name)} (${history[name].length} 条)</div>
      <div class="history-ids">
        ${history[name].map(id => `<span class="history-id">${id}</span>`).join('')}
      </div>
    </div>
  `).join('');
}

// ============================================================
//  Tasks
// ============================================================
let _pollTimer = null;

async function startTask(type) {
  const labels = { transcribe: '转录', analyze: '分析', browse: '视频录制', full: '全流程', live: '直播录制' };
  document.getElementById('task-log').textContent = `正在启动${labels[type] || type}任务...\n`;
  document.getElementById('task-status').innerHTML = '<span class="status-dot status-running"></span>运行中';

  const res = await api('/api/tasks/start', {
    method: 'POST',
    body: JSON.stringify({ type }),
  });

  if (res.error) {
    document.getElementById('task-log').textContent += res.error + '\n';
    document.getElementById('task-status').innerHTML = '<span class="status-dot status-error"></span>错误';
    return;
  }

  // Start polling
  if (_pollTimer) clearInterval(_pollTimer);
  _pollTimer = setInterval(() => pollTask(type), 1500);
}

async function pollTask(taskId) {
  const data = await api(`/api/tasks/${taskId}/status`);
  const logBox = document.getElementById('task-log');
  logBox.textContent = (data.logs || []).join('\n');
  logBox.scrollTop = logBox.scrollHeight;

  if (data.status === 'done') {
    document.getElementById('task-status').innerHTML = '<span class="status-dot status-done"></span>完成';
    clearInterval(_pollTimer);
    _pollTimer = null;
  } else if (data.status === 'error') {
    document.getElementById('task-status').innerHTML = '<span class="status-dot status-error"></span>失败';
    clearInterval(_pollTimer);
    _pollTimer = null;
  } else {
    document.getElementById('task-status').innerHTML = '<span class="status-dot status-running"></span>运行中';
  }
}

// ============================================================
//  Init
// ============================================================
loadDashboard();
</script>
</body>
</html>
