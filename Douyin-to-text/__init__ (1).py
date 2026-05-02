"""
OBS 录制控制模块

通过 OBS WebSocket 协议远程控制录制开关。

用法:
    python -m src.recorder start
    python -m src.recorder stop
    python -m src.recorder status
"""

import sys

from .config import load_config


def get_client():
    """创建 OBS WebSocket 客户端"""
    try:
        import obsws_python as obs
    except ImportError:
        print("[错误] 请安装 obsws-python: pip install obsws-python")
        sys.exit(1)

    config = load_config()
    obs_cfg = config["obs"]

    try:
        client = obs.ReqClient(
            host=obs_cfg.get("host", "localhost"),
            port=obs_cfg.get("port", 4455),
            password=obs_cfg.get("password", ""),
        )
        return client
    except Exception as e:
        print(f"[错误] 无法连接 OBS WebSocket: {e}")
        print("       请确认:")
        print("       1. OBS Studio 已打开")
        print("       2. 工具 → WebSocket 服务器设置 → 已启用")
        print("       3. config.json 中的端口和密码正确")
        sys.exit(1)


def start_recording():
    """
    开始录制，并确认 OBS 确实在录制中。

    之前的问题: 调完 start_record() 就往下走了，但 OBS 可能因为
    窗口捕获未就绪、输出路径不对等原因没有真正开始录。
    现在会轮询 get_record_status 最多 10 秒来确认。
    """
    import time

    client = get_client()

    # 先检查是否已经在录
    try:
        status = client.get_record_status()
        if getattr(status, "output_active", False):
            print("[OBS] ● 已经在录制中，继续")
            return True
    except Exception:
        pass

    # 发出开始录制指令
    try:
        client.start_record()
        print("[OBS] ● 发送开始录制指令...")
    except Exception as e:
        print(f"[OBS] ✗ 开始录制失败: {e}")
        raise RuntimeError(f"OBS 录制启动失败: {e}")

    # 轮询确认
    for i in range(10):
        time.sleep(1)
        try:
            status = client.get_record_status()
            is_active = getattr(status, "output_active", False)
            if is_active:
                print(f"[OBS] ● 录制确认成功（等待 {i+1} 秒）")
                return True
        except Exception:
            pass

    # 10 秒后仍然没有在录
    print("[OBS] ✗ 发送了开始指令但 10 秒后 OBS 仍未开始录制！")
    print("       请检查:")
    print("       1. OBS 的窗口捕获源是否选对了 Chrome 窗口")
    print("       2. OBS 的录像路径是否存在且可写")
    print("       3. OBS 是否弹出了错误提示")
    raise RuntimeError("OBS 录制确认超时")


def stop_recording():
    """停止录制，确认文件已保存"""
    import time

    client = get_client()

    # 先检查是不是根本没在录
    try:
        status = client.get_record_status()
        if not getattr(status, "output_active", False):
            print("[OBS] ■ 当前未在录制中，无需停止")
            return None
    except Exception:
        pass

    try:
        resp = client.stop_record()
        output_path = getattr(resp, "output_path", "未知路径")
        print(f"[OBS] ■ 停止录制 → {output_path}")

        # 等一下确认文件已写盘
        time.sleep(2)

        from pathlib import Path
        if output_path and output_path != "未知路径":
            p = Path(output_path)
            if p.exists():
                size_mb = p.stat().st_size / 1024 / 1024
                print(f"[OBS] ✓ 文件已保存: {p.name} ({size_mb:.1f} MB)")
                if size_mb < 0.1:
                    print("[OBS] ⚠ 文件很小（<0.1MB），录制内容可能为空！")
            else:
                print(f"[OBS] ⚠ 文件不存在: {output_path}")

        return output_path
    except Exception as e:
        print(f"[OBS] 停止录制出错: {e}")
        return None


def get_status():
    """获取录制状态"""
    client = get_client()
    try:
        status = client.get_record_status()
        is_recording = getattr(status, "output_active", False)
        duration = getattr(status, "output_timecode", "00:00:00")
        print(f"[OBS] 录制中: {'是' if is_recording else '否'}  |  时长: {duration}")
        return is_recording
    except Exception as e:
        print(f"[OBS] 获取状态失败: {e}")
        return False


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "status"
    if action == "start":
        start_recording()
    elif action == "stop":
        stop_recording()
    else:
        get_status()
