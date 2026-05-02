# 🎬 Douyin-to-Text

抖音视频自动转文字稿工具。自动浏览博主视频 → 录屏 → 本地 AI 转录 → 输出 Word 文档。

**完全免费，全部本地运行，不依赖任何付费 API。**

## ✨ 功能

- **直播优先** — 启动时自动检查直播博主是否在播，在播就先录直播
- **自动浏览抖音** — Playwright 驱动本机 Chrome，打开博主主页、逐条播放视频
- **视频去重** — 自动跳过已录过的视频，不会重复录制
- **1 倍速保护** — 强制 1 倍速播放，保证转录准确率
- **自动录屏** — OBS Studio 通过 WebSocket 自动控制录制
- **本地转录** — faster-whisper 本地运行，中文准确率高，零费用
- **Word 输出** — 转录结果自动整理为 `.docx` 文档
- **AI 分析** — 可选接入 DeepSeek 大模型，按类别（金融/求职）自动分析转录内容
- **Web 管理面板** — Flask 驱动的本地 Web UI，管理博主、预览文档、触发任务
- **自动清理** — 转录完成后自动删除视频文件
- **直播定时监控** — 守护进程按时间表自动检测开播并录制

## 📁 目录结构

```
douyin-to-text/
├── config.example.json        # 配置模板（复制为 config.json 后填入你的信息）
├── requirements.txt
├── setup.py                   # 环境检查
├── run.py                     # 一键运行（直播优先）
├── prompt_finance.txt         # 金融分析提示词
├── prompt_career.txt          # 求职分析提示词
├── src/
│   ├── shared_browser.py      # 统一浏览器管理（固定用 Chrome）
│   ├── browser.py             # 视频自动浏览（带去重）
│   ├── live.py                # 直播定时录制
│   ├── recorder.py            # OBS 控制
│   ├── transcriber.py         # 音频转录
│   ├── analyzer.py            # DeepSeek 大模型分析
│   ├── exporter.py            # Word 导出
│   ├── cleaner.py             # 视频清理
│   ├── history.py             # 录制历史（去重）
│   └── config.py              # 配置加载
├── web/
│   ├── app.py                 # Web 管理面板
│   └── templates/
│       └── index.html
└── scripts/
    ├── install_obs_websocket.md
    ├── setup_autostart.md
    └── start_live_monitor.bat
```

## 🚀 快速开始

### 1. 环境要求

- Python 3.10+
- [Google Chrome](https://google.com/chrome)（必须安装，程序固定用 Chrome）
- [FFmpeg](https://ffmpeg.org/download.html)（添加到 PATH）
- [OBS Studio](https://obsproject.com/)
- Windows 10/11

### 2. 安装

```bash
git clone https://github.com/你的用户名/douyin-to-text.git
cd douyin-to-text

pip install -r requirements.txt

# 检查环境
python setup.py
```

> **注意**: 不需要运行 `playwright install`。程序使用你本机的 Chrome，不需要 Playwright 下载额外浏览器。

### 3. 配置

```bash
cp config.example.json config.json
```

编辑 `config.json`，填入你的博主信息。主要配置项：

| 字段 | 说明 |
|------|------|
| `creators` | 要录制的视频博主列表 |
| `live_creators` | 要监控的直播博主列表 |
| `paths` | 视频、转录、Word 文件存储路径 |
| `whisper.model_size` | Whisper 模型大小（见下方模型选择） |
| `whisper.device` | `cpu` 或 `cuda`（NVIDIA 显卡） |
| `obs.password` | OBS WebSocket 密码 |
| `deepseek.api_key` | DeepSeek API Key（可选，用于 AI 分析） |

### 4. 配置 OBS

详见 [OBS WebSocket 配置指南](scripts/install_obs_websocket.md)。

### 5. 运行

```bash
# 全流程: 直播检查 → 视频录制 → 询问是否转录
python run.py

# 只录不转录
python run.py --no-transcribe

# 只转录已有视频
python run.py --transcribe-only

# 跳过直播检查
python run.py --skip-live

# 自动确认所有提示
python run.py --yes
```

### 6. 首次登录

第一次运行会打开 Chrome 浏览器到抖音，需要你手动扫码登录一次。登录状态保存到 `auth.json`，之后无需重复登录。

## 🌐 Web 管理面板

启动本地 Web 管理界面：

```bash
python -m web.app
```

打开浏览器访问 `http://localhost:5000`，可以：

- 查看/管理博主列表
- 在线预览 Word 和分析报告
- 下载文件
- 手动触发录制/转录/分析任务

## 🔴 直播自动录制

### 配置

在 `config.json` 的 `live_creators` 中添加：

```json
"live_creators": [
    {
        "name": "主播名称",
        "url": "https://live.douyin.com/直播间ID",
        "schedule": {
            "weekdays": [1, 2, 3, 4, 5],
            "time": "11:30"
        },
        "category": "career"
    }
]
```

### 运行

```bash
# 守护进程（推荐配合开机自启）
python -m src.live

# 检查一次
python -m src.live --once

# 立即录制指定主播
python -m src.live --now "主播名称"
```

### 开机自启

详见 [开机自启配置](scripts/setup_autostart.md)。

## 🤖 AI 分析（可选）

配置 DeepSeek API Key 后，转录完成会自动提示是否分析。也可以单独运行：

```bash
python -m src.analyzer
```

通过 `config.json` 中每个博主的 `category` 字段选择分析模板：

| Category | 提示词文件 | 用途 |
|----------|-----------|------|
| `finance` | `prompt_finance.txt` | 金融行业分析、股价波动、投资判断 |
| `career` | `prompt_career.txt` | 求职案例提取、岗位推荐 |

你可以修改提示词文件来自定义分析逻辑。

## 🔧 浏览器设置

程序固定使用本机 Chrome 浏览器。如果想换成 Edge：

编辑 `src/shared_browser.py`，改一行：

```python
BROWSER_CHANNEL = "msedge"   # 改这里
```

## ⚙️ Whisper 模型选择

| 模型 | 磁盘 | 内存 | 中文效果 | CPU 速度（3分钟音频） |
|------|------|------|---------|---------------------|
| `tiny` | 75 MB | ~1 GB | 勉强 | ~30 秒 |
| `small` | 500 MB | ~2 GB | 不错 | ~2 分钟 |
| `medium` | 1.5 GB | ~4 GB | 推荐 | ~5 分钟 |
| `large-v3` | 3 GB | ~6 GB | 最佳 | ~10 分钟 |

有 NVIDIA 显卡：`config.json` 中 `device` 改为 `"cuda"`，提速 5-10 倍。

## 📝 License

MIT
