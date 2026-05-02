"""共享配置加载模块"""

import json
import sys
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent / "config.json"


def load_config() -> dict:
    """加载并验证配置文件"""
    if not CONFIG_PATH.exists():
        print(f"[错误] 找不到配置文件: {CONFIG_PATH}")
        print("请复制 config.json 并填入你的博主信息。")
        sys.exit(1)

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)

    # 确保输出目录存在
    for key in ("video_dir", "transcript_dir", "word_dir"):
        Path(config["paths"][key]).mkdir(parents=True, exist_ok=True)

    return config


def save_config(config: dict):
    """保存配置（用于更新博主列表等）"""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
