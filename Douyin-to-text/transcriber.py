"""
抖音直播自动录制模块

功能:
- 读取 config.json 中的 live_creators 列表
- 每个博主有独立的定时计划（按星期几 + 具体时刻）
- 到点后自动打开直播链接，启动 OBS 录制
- 录满指定时长自动停止
- 使用本机 Chrome，避免多浏览器冲突

用法:
    python -m src.live                # 守护进程，持续监控
    python -m src.live --once         # 检查一次当前时间
    python -m src.live --now <name>   # 立即录制指定博主
"""

import argparse
import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

from playwright.async_api import async_playwright

from .config import load_config
from .recorder import start_recording, stop_recording
from .shared_browser import launch_browser, create_context, ensure_audio, AUTH_FILE

WEEKDAY_NAMES = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"]


def python_weekday_to_user(py_weekday: int) -> int:
    """Python weekday (周一=0) → 用户约定 (周日=0, 周一=1)"""
    return (py_weekday + 1) % 7


def is_live_due(creator: dict, now: datetime, tolerance_minutes: int = 2) -> bool:
    """判断当前时刻是否该录制此博主"""
    schedule = creator.get("schedule", {})
    weekdays = schedule.get("weekdays", [])
    time_str = schedule.get("time", "")

    if not weekdays or not time_str:
        return False

    if python_weekday_to_user(now.weekday()) not in weekdays:
        return False

    try:
        sched_hour, sched_minute = map(int, time_str.split(":"))
    except ValueError:
        print(f"[警告] {creator['name']} 的 time 格式错误: {time_str}")
        return False

    sched_time = now.replace(hour=sched_hour, minute=sched_minute, second=0, microsecond=0)
    diff = abs((now - sched_time).total_seconds())
    return diff <= tolerance_minutes * 60


def next_schedule(creator: dict, from_time: datetime) -> datetime | None:
    """计算下一次预定直播时间"""
    schedule = creator.get("schedule", {})
    weekdays = schedule.get("weekdays", [])
    time_str = schedule.get("time", "")
    if not weekdays or not time_str:
        return None

    try:
        sched_hour, sched_minute = map(int, time_str.split(":"))
    except ValueError:
        return None

    for offset in range(8):
        candidate = from_time + timedelta(days=offset)
        if python_weekday_to_user(candidate.weekday()) in weekdays:
            sched = candidate.replace(hour=sched_hour, minute=sched_minute, second=0, microsecond=0)
            if sched > from_time:
                return sched
    return None


async def check_live_active(page, url: str, timeout: int = 30000) -> bool:
    """
    打开直播链接，判断是否真的在直播。

    判断策略（三重验证）:
    1. 页面文字检测: 如果出现"直播已结束""暂未开播"等关键词 → 不在播
    2. video 元素检测: 没有 video 或 video 暂停 → 不在播
    3. 直播流确认: video.duration 必须是 Infinity（直播流特征），
       且 currentTime 在持续增长 → 才算真正在播

    之前的 bug: 直播结束页面仍有 video 元素（可能是回放），
    仅靠 "video 存在且未暂停" 判断会误判。
    """
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=timeout)
    except Exception as e:
        print(f"  [警告] 加载直播页超时: {e}")
        return False

    # 等页面充分渲染（抖音直播页是 SPA，关键文字可能延迟出现）
    await asyncio.sleep(8)

    # ---- 第一重: 页面文字检测 ----
    try:
        # 同时检查 innerText 和 innerHTML，有些提示在弹层/特殊容器中
        page_content = await page.evaluate("""
            () => {
                const text = document.body.innerText || '';
                const html = document.body.innerHTML || '';
                return text + '|||' + html;
            }
        """)
        negative_keywords = [
            "直播已结束", "暂未开播", "主播正在努力",
            "主播不在", "直播间不存在", "未开播",
            "直播结束", "已结束",
        ]
        for kw in negative_keywords:
            if kw in page_content:
                print(f"    (检测到「{kw}」)")
                return False
    except Exception:
        pass

    # ---- 第二重: video 元素基本检测 ----
    try:
        video_info = await page.evaluate("""
            () => {
                const v = document.querySelector('video');
                if (!v) return null;
                return {
                    paused: v.paused,
                    readyState: v.readyState,
                    duration: v.duration,
                    currentTime: v.currentTime
                };
            }
        """)
    except Exception:
        video_info = None

    if not video_info:
        print("    (未找到 video 元素)")
        return False

    if video_info["paused"] and video_info["readyState"] < 2:
        print("    (video 暂停且未就绪)")
        return False

    # ---- 第三重: 确认是直播流而非回放 ----
    # 直播流的 duration 是 Infinity 或 NaN（非有限数值）
    duration = video_info["duration"]
    # JS 传过来的 Infinity 在 Python 里是 float('inf')，NaN 是 None 或 float
    is_live_stream = (duration is None or
                      (isinstance(duration, float) and (duration != duration or duration == float('inf'))))

    if not is_live_stream:
        # duration 是有限值 → 这是一个有固定时长的视频（回放），不是直播
        print(f"    (video duration={duration}，是回放而非直播)")
        return False

    # 最后确认: currentTime 在增长（等 3 秒再读一次）
    time1 = video_info["currentTime"]
    await asyncio.sleep(3)
    try:
        time2 = await page.evaluate("""
            () => {
                const v = document.querySelector('video');
                return v ? v.currentTime : 0;
            }
        """)
    except Exception:
        time2 = time1

    if time2 > time1:
        print(f"    (直播流确认: currentTime {time1:.0f} → {time2:.0f})")
        return True
    else:
        print(f"    (currentTime 未增长: {time1} → {time2}，可能不在播)")
        return False


async def record_live(creator: dict, duration_minutes: int):
    """录制单个博主的直播"""
    name = creator["name"]
    url = creator["url"]

    print(f"\n{'='*55}")
    print(f"  ▶ 开始录制直播: {name}")
    print(f"    链接: {url}")
    print(f"    计划时长: {duration_minutes} 分钟")
    print(f"{'='*55}")

    async with async_playwright() as p:
        browser = await launch_browser(p)
        context = await create_context(browser)
        page = await context.new_page()

        # 检测是否在播
        is_active = await check_live_active(page, url)
        if not is_active:
            print(f"  [跳过] {name} 当前未开播")
            await browser.close()
            return False

        print("  [检测] 直播进行中，开始录制")

        # 确保声音开启
        await ensure_audio(page)

        # 启动 OBS 录制
        try:
            start_recording()
        except Exception as e:
            print(f"  [错误] 启动 OBS 录制失败: {e}")
            await browser.close()
            return False

        total_seconds = duration_minutes * 60
        elapsed = 0
        check_interval = 60
        pause_count = 0       # 连续检测到暂停的次数
        PAUSE_LIMIT = 3       # 连续 3 次暂停就刷新页面

        try:
            while elapsed < total_seconds:
                wait = min(check_interval, total_seconds - elapsed)
                await asyncio.sleep(wait)
                elapsed += wait

                try:
                    still_live = await page.evaluate("""
                        () => {
                            const v = document.querySelector('video');
                            if (!v) return false;
                            return !v.paused && v.readyState >= 2;
                        }
                    """)
                except Exception:
                    still_live = False

                minutes_done = elapsed // 60

                if still_live:
                    pause_count = 0
                    print(f"  [进度] 已录 {minutes_done} / {duration_minutes} 分钟")
                else:
                    pause_count += 1
                    print(f"  [警告] 检测到暂停/卡顿 ({pause_count}/{PAUSE_LIMIT})")

                    if pause_count >= PAUSE_LIMIT:
                        # 连续 3 次暂停 → 关闭页面重新打开
                        print(f"  [刷新] 连续 {PAUSE_LIMIT} 次暂停，重新加载直播页面...")

                        try:
                            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                            await asyncio.sleep(8)
                            await ensure_audio(page)

                            # 再次检测是否在播
                            is_still_active = await check_live_active(page, url)

                            if is_still_active:
                                print(f"  [恢复] 刷新后直播仍在进行，继续录制")
                                await ensure_audio(page)
                                pause_count = 0
                            else:
                                print(f"  [结束] 刷新后确认直播已结束（已录 {minutes_done} 分钟）")
                                break
                        except Exception as e:
                            print(f"  [错误] 刷新页面失败: {e}")
                            print(f"  [结束] 无法恢复，停止录制（已录 {minutes_done} 分钟）")
                            break
        finally:
            try:
                output_path = stop_recording()
                # 重命名文件加博主名前缀，让 analyzer 能匹配 category
                if output_path:
                    from pathlib import Path
                    old = Path(output_path)
                    if old.exists() and not old.name.startswith(name):
                        new_name = f"{name}_{old.name}"
                        new_path = old.parent / new_name
                        try:
                            old.rename(new_path)
                            print(f"  [文件] 重命名: {old.name} → {new_name}")
                        except Exception as e:
                            print(f"  [文件] 重命名失败: {e}")
            except Exception as e:
                print(f"  [警告] 停止录制出错: {e}")
            await browser.close()

        print(f"  ✅ {name} 直播录制完成")
        return True


async def check_all_live() -> bool:
    """
    检查所有直播博主是否在播，按顺序逐个录制。

    策略（方案 A）:
    - 先扫描一遍谁在播
    - 按 config 中的顺序录制（排前面的优先）
    - 录完一个后再检查后面的是否还在播
    - OBS 同时只能录一个，所以必须排队
    """
    config = load_config()
    live_creators = config.get("live_creators", [])
    duration = config.get("live_record_minutes", 60)

    if not live_creators:
        return False

    print(f"\n[直播] 检查 {len(live_creators)} 个博主是否在播...")

    # 先快速扫描谁在播
    from .shared_browser import launch_browser, create_context
    active_creators = []

    async with async_playwright() as p:
        browser = await launch_browser(p)
        context = await create_context(browser)
        page = await context.new_page()

        for creator in live_creators:
            name = creator["name"]
            print(f"  • 检查 {name}...", end=" ", flush=True)

            is_active = await check_live_active(page, creator["url"])
            if is_active:
                print("🔴 在播!")
                active_creators.append(creator)
            else:
                print("○ 未开播")

        await browser.close()

    if not active_creators:
        return False

    if len(active_creators) > 1:
        print(f"\n[直播] {len(active_creators)} 个博主同时在播，按顺序录制:")
        for i, c in enumerate(active_creators):
            print(f"  {i+1}. {c['name']}")

    # 按顺序逐个录制
    recorded = False
    for i, creator in enumerate(active_creators):
        if i > 0:
            # 录完上一个后，重新检查这个博主是否还在播
            print(f"\n[直播] 检查 {creator['name']} 是否还在播...")
            async with async_playwright() as p:
                browser = await launch_browser(p)
                context = await create_context(browser)
                page = await context.new_page()
                still_active = await check_live_active(page, creator["url"])
                await browser.close()

            if not still_active:
                print(f"  [跳过] {creator['name']} 已经下播了")
                continue

        result = await record_live(creator, duration)
        if result:
            recorded = True

    return recorded


async def run_loop(check_interval_seconds: int = 60):
    """守护进程:持续监控，到点就录"""
    config = load_config()
    live_creators = config.get("live_creators", [])
    duration = config.get("live_record_minutes", 60)

    if not live_creators:
        print("[错误] 没有配置 live_creators")
        sys.exit(1)

    print("📺 直播监控启动")
    print(f"   {len(live_creators)} 个博主，单次 {duration} 分钟\n")

    now = datetime.now()
    for c in live_creators:
        nxt = next_schedule(c, now)
        if nxt:
            wd = WEEKDAY_NAMES[python_weekday_to_user(nxt.weekday())]
            print(f"  • {c['name']}: 下次 {nxt.strftime('%m-%d %H:%M')} ({wd})")
        else:
            print(f"  • {c['name']}: ⚠ 未设置时间表")
    print()

    last_recorded = {}
    print(f"[运行] 每 {check_interval_seconds} 秒检查... (Ctrl+C 退出)\n")

    while True:
        now = datetime.now()
        for creator in live_creators:
            name = creator["name"]

            last = last_recorded.get(name)
            if last and (now - last).total_seconds() < duration * 60:
                continue

            if is_live_due(creator, now):
                last_recorded[name] = now
                print(f"\n⏰ [{now.strftime('%H:%M:%S')}] {name} 到点了")
                try:
                    await record_live(creator, duration)
                except Exception as e:
                    print(f"[错误] 录制 {name} 异常: {e}")

        await asyncio.sleep(check_interval_seconds)


async def run_once():
    """单次检查"""
    config = load_config()
    live_creators = config.get("live_creators", [])
    duration = config.get("live_record_minutes", 60)

    now = datetime.now()
    print(f"[检查] {now.strftime('%Y-%m-%d %H:%M %A')}")

    triggered = False
    for creator in live_creators:
        if is_live_due(creator, now):
            print(f"[触发] {creator['name']}")
            await record_live(creator, duration)
            triggered = True

    if not triggered:
        print("[结果] 当前无博主到点")


async def run_now(name: str):
    """立即录制指定博主"""
    config = load_config()
    live_creators = config.get("live_creators", [])
    duration = config.get("live_record_minutes", 60)

    for creator in live_creators:
        if creator["name"] == name:
            print(f"[手动] 立即录制 {name}")
            await record_live(creator, duration)
            return

    print(f"[错误] 找不到博主: {name}")
    print(f"       可选: {', '.join(c['name'] for c in live_creators)}")


def main():
    parser = argparse.ArgumentParser(description="抖音直播自动录制")
    parser.add_argument("--once", action="store_true", help="仅检查一次")
    parser.add_argument("--now", type=str, metavar="NAME", help="立即录制")
    parser.add_argument("--interval", type=int, default=60, help="检查间隔(秒)")
    args = parser.parse_args()

    if args.now:
        asyncio.run(run_now(args.now))
    elif args.once:
        asyncio.run(run_once())
    else:
        try:
            asyncio.run(run_loop(args.interval))
        except KeyboardInterrupt:
            print("\n[退出] 监控已停止")


if __name__ == "__main__":
    main()
