"""
视频录制历史记录模块

维护 recorded_videos.json，记录每个博主已经录过的视频 ID，避免重复录制。

文件格式:
    {
        "博主A": ["7123456789", "7234567890"],
        "博主B": ["7345678901"]
    }

每录完一个视频就立刻追加写入，避免中途崩溃丢记录。
"""

import json
import re
from pathlib import Path
from threading import Lock

HISTORY_PATH = Path(__file__).parent.parent / "recorded_videos.json"
_lock = Lock()


def extract_video_id(url: str) -> str | None:
    """
    从抖音视频 URL 里提取视频 ID。

    支持格式:
        https://www.douyin.com/video/7123456789012345678
        https://www.douyin.com/user/MS4.../video/7123456789012345678
    """
    if not url:
        return None
    m = re.search(r"/video/(\d+)", url)
    return m.group(1) if m else None


def load_history() -> dict:
    """加载历史记录。文件不存在时返回空字典。"""
    if not HISTORY_PATH.exists():
        return {}
    try:
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"[警告] recorded_videos.json 读取失败 ({e})，视为空历史")
        return {}


def save_history(history: dict):
    """整体保存历史记录"""
    with _lock:
        HISTORY_PATH.write_text(
            json.dumps(history, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def is_recorded(creator_name: str, video_id: str) -> bool:
    """查询某博主的某条视频是否已录过"""
    if not video_id:
        return False
    history = load_history()
    return video_id in history.get(creator_name, [])


def mark_recorded(creator_name: str, video_id: str):
    """标记一条视频为已录制，立刻写盘"""
    if not video_id:
        return
    with _lock:
        history = load_history()
        if creator_name not in history:
            history[creator_name] = []
        if video_id not in history[creator_name]:
            history[creator_name].append(video_id)
            HISTORY_PATH.write_text(
                json.dumps(history, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )


def count_recorded(creator_name: str) -> int:
    """返回某博主已录过的视频数"""
    return len(load_history().get(creator_name, []))
