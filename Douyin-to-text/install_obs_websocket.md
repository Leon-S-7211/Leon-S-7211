"""
Douyin-to-Text Web 管理面板

功能:
- 查看/管理博主列表（添加、删除、修改 category）
- 查看转录的 Word 内容（在线预览）
- 查看 DeepSeek 分析报告（在线预览）
- 下载 Word 和分析报告
- 查看录制历史记录
- 手动触发录制/转录/分析任务

启动:
    python -m web.app
    或: python web/app.py
"""

import json
import subprocess
import sys
import threading
from pathlib import Path
from datetime import datetime

from flask import Flask, render_template, jsonify, request, send_file, abort

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_config, save_config, CONFIG_PATH

app = Flask(__name__)

# 正在运行的后台任务
_running_tasks = {}
_task_logs = {}


# ============================================================
#  页面路由
# ============================================================

@app.route("/")
def index():
    return render_template("index.html")


# ============================================================
#  API: 博主管理
# ============================================================

@app.route("/api/creators", methods=["GET"])
def get_creators():
    config = load_config()
    return jsonify({
        "creators": config.get("creators", []),
        "live_creators": config.get("live_creators", []),
    })


@app.route("/api/creators", methods=["POST"])
def add_creator():
    data = request.json
    config = load_config()

    creator = {
        "name": data["name"],
        "url": data["url"],
        "videos": data.get("videos", 1),
        "category": data.get("category", "finance"),
    }

    if data.get("is_live"):
        creator["schedule"] = {
            "weekdays": data.get("weekdays", [1, 2, 3, 4, 5]),
            "time": data.get("time", "11:30"),
        }
        config.setdefault("live_creators", []).append(creator)
    else:
        config.setdefault("creators", []).append(creator)

    save_config(config)
    return jsonify({"ok": True})


@app.route("/api/creators/<name>", methods=["DELETE"])
def delete_creator(n):
    config = load_config()

    config["creators"] = [c for c in config.get("creators", []) if c["name"] != n]
    config["live_creators"] = [c for c in config.get("live_creators", []) if c["name"] != n]

    save_config(config)
    return jsonify({"ok": True})


# ============================================================
#  API: 文件列表和内容
# ============================================================

@app.route("/api/files/<file_type>")
def list_files(file_type):
    """列出指定目录下的文件: word / analysis / recordings / transcripts"""
    config = load_config()
    paths_map = {
        "word": config["paths"]["word_dir"],
        "analysis": config["paths"].get("analysis_dir", ""),
        "recordings": config["paths"]["video_dir"],
        "transcripts": config["paths"]["transcript_dir"],
    }

    dir_path = paths_map.get(file_type, "")
    if not dir_path:
        return jsonify({"files": []})

    p = Path(dir_path)
    if not p.exists():
        return jsonify({"files": []})

    files = []
    for f in sorted(p.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
        if f.is_file() and not f.name.startswith("."):
            files.append({
                "name": f.name,
                "size_mb": round(f.stat().st_size / 1024 / 1024, 2),
                "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
                "type": file_type,
            })

    return jsonify({"files": files})


@app.route("/api/files/<file_type>/<filename>/content")
def get_file_content(file_type, filename):
    """读取 Word/txt 文件的文本内容用于在线预览"""
    config = load_config()
    paths_map = {
        "word": config["paths"]["word_dir"],
        "analysis": config["paths"].get("analysis_dir", ""),
        "transcripts": config["paths"]["transcript_dir"],
    }

    dir_path = paths_map.get(file_type, "")
    if not dir_path:
        abort(404)

    file_path = Path(dir_path) / filename
    if not file_path.exists():
        abort(404)

    # txt 文件直接读
    if file_path.suffix == ".txt":
        text = file_path.read_text(encoding="utf-8")
        return jsonify({"content": text, "format": "text"})

    # docx 文件提取文本
    if file_path.suffix == ".docx":
        try:
            from docx import Document
            doc = Document(str(file_path))
            paragraphs = []
            for p in doc.paragraphs:
                if p.style.name.startswith("Heading"):
                    level = p.style.name.replace("Heading ", "")
                    paragraphs.append({"type": "heading", "level": level, "text": p.text})
                else:
                    if p.text.strip():
                        paragraphs.append({"type": "paragraph", "text": p.text})
            return jsonify({"content": paragraphs, "format": "docx"})
        except Exception as e:
            return jsonify({"content": str(e), "format": "error"})

    abort(400)


@app.route("/api/files/<file_type>/<filename>/download")
def download_file(file_type, filename):
    """下载文件"""
    config = load_config()
    paths_map = {
        "word": config["paths"]["word_dir"],
        "analysis": config["paths"].get("analysis_dir", ""),
        "recordings": config["paths"]["video_dir"],
        "transcripts": config["paths"]["transcript_dir"],
    }

    dir_path = paths_map.get(file_type, "")
    if not dir_path:
        abort(404)

    file_path = Path(dir_path) / filename
    if not file_path.exists():
        abort(404)

    return send_file(str(file_path), as_attachment=True)


# ============================================================
#  API: 录制历史
# ============================================================

@app.route("/api/history")
def get_history():
    history_path = PROJECT_ROOT / "recorded_videos.json"
    if not history_path.exists():
        return jsonify({"history": {}})

    with open(history_path, "r", encoding="utf-8") as f:
        history = json.load(f)

    return jsonify({"history": history})


# ============================================================
#  API: 任务触发
# ============================================================

def _run_task(task_id: str, cmd: list[str]):
    """在后台线程中运行命令"""
    import os

    _running_tasks[task_id] = "running"
    _task_logs[task_id] = []

    try:
        # Windows 默认用 GBK 编码读子进程输出，会导致中文乱码/崩溃
        # 强制子进程和读取都用 UTF-8
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"

        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace",
            cwd=str(PROJECT_ROOT), env=env,
        )
        for line in process.stdout:
            _task_logs[task_id].append(line.rstrip())
        process.wait()
        _running_tasks[task_id] = "done" if process.returncode == 0 else "error"
    except Exception as e:
        _task_logs[task_id].append(f"[异常] {e}")
        _running_tasks[task_id] = "error"


@app.route("/api/tasks/start", methods=["POST"])
def start_task():
    data = request.json
    task_type = data.get("type", "")

    cmd_map = {
        "transcribe": [sys.executable, "run.py", "--transcribe-only", "--yes"],
        "browse": [sys.executable, "run.py", "--skip-live", "--yes"],
        "live": [sys.executable, "-m", "src.live", "--once"],
        "full": [sys.executable, "run.py", "--yes"],
        "analyze": [sys.executable, "-m", "src.analyzer"],
    }

    cmd = cmd_map.get(task_type)
    if not cmd:
        return jsonify({"error": f"未知任务类型: {task_type}"}), 400

    # 检查是否已有同类任务在运行
    if _running_tasks.get(task_type) == "running":
        return jsonify({"error": f"{task_type} 任务正在运行中"}), 409

    task_id = task_type
    _task_logs[task_id] = []

    thread = threading.Thread(target=_run_task, args=(task_id, cmd), daemon=True)
    thread.start()

    return jsonify({"ok": True, "task_id": task_id})


@app.route("/api/tasks/<task_id>/status")
def task_status(task_id):
    status = _running_tasks.get(task_id, "unknown")
    logs = _task_logs.get(task_id, [])
    # 只返回最后 50 行日志
    return jsonify({
        "status": status,
        "logs": logs[-50:],
        "total_lines": len(logs),
    })


# ============================================================
#  启动
# ============================================================

if __name__ == "__main__":
    print("=" * 50)
    print("  Douyin-to-Text Web 管理面板")
    print("  打开浏览器访问: http://localhost:5000")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=True)
