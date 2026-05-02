"""
本地音频转录模块

使用 faster-whisper 本地运行 Whisper 模型，
从视频中提取音频并转录为文字。完全免费。

用法:
    python -m src.transcriber
"""

import subprocess
import sys
from pathlib import Path

from .config import load_config

_model = None


def get_model(config: dict):
    """加载或返回缓存的 Whisper 模型"""
    global _model
    if _model is not None:
        return _model

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("[错误] 请安装 faster-whisper: pip install faster-whisper")
        sys.exit(1)

    whisper_cfg = config["whisper"]
    model_size = whisper_cfg.get("model_size", "medium")
    device = whisper_cfg.get("device", "cpu")
    compute_type = "int8" if device == "cpu" else "float16"

    print(f"[模型] 加载 {model_size}（{device}, {compute_type}）...")
    print("       首次运行需下载模型，请耐心等待。\n")

    _model = WhisperModel(model_size, device=device, compute_type=compute_type)
    return _model


def check_ffmpeg():
    """检查 ffmpeg 是否可用"""
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("[错误] 未找到 ffmpeg，请安装: https://ffmpeg.org/download.html")
        return False


def extract_audio(video_path: Path) -> Path | None:
    """从视频提取音频为 WAV（16kHz 单声道）"""
    audio_path = video_path.with_suffix(".wav")

    if audio_path.exists():
        print(f"  [音频] 已存在: {audio_path.name}")
    else:
        print(f"  [音频] 提取中: {video_path.name}")
        result = subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", str(video_path),
                "-vn", "-acodec", "pcm_s16le",
                "-ar", "16000", "-ac", "1",
                str(audio_path),
            ],
            capture_output=True, text=True,
        )

        if result.returncode != 0:
            print(f"  [错误] 提取失败: {result.stderr[:200]}")
            return None

    # 检查音频是否全静音（用 ffmpeg 的 volumedetect 滤镜）
    try:
        vol_result = subprocess.run(
            [
                "ffmpeg", "-i", str(audio_path),
                "-af", "volumedetect",
                "-f", "null", "-",
            ],
            capture_output=True, text=True,
        )
        stderr = vol_result.stderr
        # 查找 mean_volume，正常语音一般在 -30dB 到 -10dB
        import re
        m = re.search(r"mean_volume:\s*([-\d.]+)\s*dB", stderr)
        if m:
            mean_vol = float(m.group(1))
            print(f"  [音频] 平均音量: {mean_vol:.1f} dB")
            if mean_vol < -60:
                print("  ⚠ 音量极低（可能是静音）！Whisper 可能无法识别内容。")
                print("    请检查:")
                print("    1. OBS「设置 → 音频 → 桌面音频」是否选了「默认」")
                print("    2. Chrome 标签页是否被静音（标签上有 🔇 图标）")
                print("    3. Windows 音量混合器里 Chrome 音量是否为 0")
    except Exception:
        pass

    return audio_path


def transcribe_file(model, audio_path: Path, language: str = "zh") -> str:
    """转录单个音频文件"""
    print(f"  [转录] {audio_path.name}")

    segments, info = model.transcribe(
        str(audio_path),
        language=language,
        beam_size=5,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500),
    )

    lines = []
    for seg in segments:
        timestamp = f"[{_format_time(seg.start)} → {_format_time(seg.end)}]"
        lines.append(f"{timestamp} {seg.text.strip()}")
        print(f"    {timestamp} {seg.text.strip()[:40]}...")

    return "\n".join(lines)


def _format_time(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


def run():
    """处理所有待转录的视频"""
    config = load_config()
    video_dir = Path(config["paths"]["video_dir"])
    transcript_dir = Path(config["paths"]["transcript_dir"])
    language = config["whisper"].get("language", "zh")

    if not check_ffmpeg():
        sys.exit(1)

    extensions = ("*.mp4", "*.mkv", "*.flv", "*.avi", "*.webm", "*.mov")
    video_files = []
    for ext in extensions:
        video_files.extend(video_dir.glob(ext))

    if not video_files:
        print(f"[提示] {video_dir} 下没有视频")
        return

    print(f"[发现] {len(video_files)} 个视频\n")

    model = get_model(config)
    processed = 0

    for vf in sorted(video_files):
        txt_path = transcript_dir / f"{vf.stem}.txt"
        if txt_path.exists():
            print(f"[跳过] {vf.name}（已有转录）")
            continue

        print(f"\n[处理] {vf.name}  ({vf.stat().st_size / 1024 / 1024:.1f} MB)")

        audio = extract_audio(vf)
        if audio is None:
            continue

        text = transcribe_file(model, audio, language)

        if not text.strip():
            print("  ⚠ 转录结果为空！视频里可能没有语音内容。")
            print("    最可能的原因: OBS 没有录到系统声音。")
            print("    请检查 OBS「设置 → 音频 → 桌面音频」是否为「默认」。")
            print("    跳过此文件，不生成空的 txt。")
            if audio.exists() and audio.suffix == ".wav":
                audio.unlink()
            continue

        txt_path.write_text(text, encoding="utf-8")
        print(f"  [保存] {txt_path}")

        if audio.exists() and audio.suffix == ".wav":
            audio.unlink()

        processed += 1

    print(f"\n[完成] 转录 {processed} 个视频")


if __name__ == "__main__":
    run()
