"""
自动浏览抖音博主视频

策略:
    1. 打开博主主页
    2. 用 JS 从作品列表区域精确提取 /video/xxx 链接
    3. 过滤掉已录过的(查 recorded_videos.json)
    4. 依次导航到每条视频的独立页面并等待播放结束
    5. 强制 1 倍速，保证转录准确率

使用本机 Chrome 浏览器，避免多浏览器登录冲突。

用法:
    python -m src.browser
"""

import asyncio
import re
import sys

from playwright.async_api import async_playwright

from .config import load_config
from .history import extract_video_id, is_recorded, mark_recorded
from .shared_browser import launch_browser, create_context, save_auth, ensure_logged_in, ensure_audio

# 连续遇到 N 条已录过的视频就放弃这个博主
SKIP_LIMIT = 5


async def force_playback_rate(page, rate: float = 1.0):
    """强制所有 <video> 元素播放速度为指定值"""
    try:
        await page.evaluate(f"""
            () => {{
                document.querySelectorAll('video').forEach(v => {{
                    v.playbackRate = {rate};
                }});
            }}
        """)
    except Exception:
        pass


async def collect_video_urls(page, max_scroll: int = 10) -> list[str]:
    """
    在博主主页上精确提取作品列表中的视频链接。

    只取作品区域 [data-e2e="user-post-list"] 内的链接,
    不会拿到推荐、广告、侧边栏的视频。
    """
    all_urls = []
    seen_ids = set()

    for scroll_round in range(max_scroll):
        urls = await page.evaluate("""
            () => {
                const links = [];
                // 优先在作品列表容器内找
                const postList = document.querySelector('[data-e2e="user-post-list"]');
                const searchArea = postList || document.body;
                const anchors = searchArea.querySelectorAll('a[href*="/video/"]');
                for (const a of anchors) {
                    if (a.href && a.href.includes('/video/')) {
                        links.push(a.href);
                    }
                }
                return links;
            }
        """)

        new_count = 0
        for url in urls:
            vid = extract_video_id(url)
            if vid and vid not in seen_ids:
                seen_ids.add(vid)
                all_urls.append(url)
                new_count += 1

        if new_count == 0 and scroll_round > 0:
            break

        await page.evaluate("window.scrollBy(0, window.innerHeight)")
        await asyncio.sleep(1.5)

    return all_urls


async def wait_for_video_end(page, max_seconds: int = 600):
    """等待当前视频播放结束"""
    print("    等待播放完毕", end="", flush=True)

    elapsed = 0
    poll_interval = 3
    stale_count = 0
    last_time = -1

    while elapsed < max_seconds:
        try:
            info = await page.evaluate("""
                () => {
                    const v = document.querySelector('video');
                    if (!v) return null;
                    return {
                        currentTime: v.currentTime,
                        duration: v.duration,
                        paused: v.paused,
                        ended: v.ended,
                        playbackRate: v.playbackRate
                    };
                }
            """)

            if info:
                if info["playbackRate"] != 1.0:
                    await force_playback_rate(page, 1.0)

                if info["ended"]:
                    print(f" ✓ ({int(info['duration'])}秒)")
                    return

                if info["duration"] and info["duration"] > 0 and not info["paused"]:
                    remaining = info["duration"] - info["currentTime"]
                    if remaining < 2:
                        print(f" ✓ ({int(info['duration'])}秒)")
                        return

                    if elapsed > 0 and elapsed % 15 == 0:
                        pct = info["currentTime"] / info["duration"] * 100
                        print(f" {pct:.0f}%", end="", flush=True)

                if info["currentTime"] == last_time:
                    stale_count += 1
                    if stale_count >= 5:
                        print(f" ⚠ (播放卡住，跳过)")
                        return
                else:
                    stale_count = 0
                last_time = info["currentTime"]
            else:
                if elapsed > 0 and elapsed % 15 == 0:
                    print(".", end="", flush=True)

        except Exception:
            pass

        await asyncio.sleep(poll_interval)
        elapsed += poll_interval

    print(f" ⚠ (达到最大等待时间 {max_seconds}秒)")


async def browse_creator(page, creator: dict, default_videos: int, max_seconds: int):
    """浏览单个博主:收集作品链接 → 过滤已录 → 逐条播放"""
    name = creator["name"]
    url = creator["url"]
    target_count = creator.get("videos", default_videos)

    print(f"\n{'='*55}")
    print(f"  博主: {name}  |  目标: {target_count} 条新视频")
    print(f"  链接: {url}")
    print(f"{'='*55}")

    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        print(f"[警告] 页面加载超时: {e}")

    await asyncio.sleep(4)

    # 收集作品列表视频 URL
    print(f"[扫描] 收集 {name} 的作品列表...")
    video_urls = await collect_video_urls(page, max_scroll=5)

    if not video_urls:
        print(f"[警告] 未找到 {name} 的视频链接，请检查 URL")
        return

    print(f"[扫描] 找到 {len(video_urls)} 条视频")

    # 过滤已录过的
    new_videos = []
    consecutive_old = 0

    for vurl in video_urls:
        vid = extract_video_id(vurl)
        if vid and is_recorded(name, vid):
            consecutive_old += 1
            print(f"  ⏭  {vid} 已录过 ({consecutive_old}/{SKIP_LIMIT})")
            if consecutive_old >= SKIP_LIMIT:
                print(f"  ℹ  连续 {SKIP_LIMIT} 条旧视频，{name} 可能没更新")
                break
        else:
            consecutive_old = 0
            new_videos.append((vurl, vid))
            if len(new_videos) >= target_count:
                break

    if not new_videos:
        print(f"  ℹ  {name} 没有新视频")
        return

    print(f"[计划] 录制 {len(new_videos)} 条新视频\n")

    # 逐条导航到视频独立页面播放
    for i, (vurl, vid) in enumerate(new_videos):
        print(f"  ▶ [{name}] 视频 {i+1}/{len(new_videos)}  (id={vid or '?'})")

        try:
            await page.goto(vurl, wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            print(f"    [警告] 加载视频页超时: {e}")

        await asyncio.sleep(3)
        await ensure_audio(page)
        await force_playback_rate(page, 1.0)
        await wait_for_video_end(page, max_seconds)

        if vid:
            mark_recorded(name, vid)
            print(f"    [记录] 已标记 {vid}")

    print(f"\n  ✅ {name} 完成，新增 {len(new_videos)} 条")


async def run():
    """
    主流程：一次性浏览所有博主。

    注意：如果由 run.py 调用（分博主录制模式），
    不会走这个函数，而是走 run_per_creator()。
    这个函数保留给 `python -m src.browser` 单独使用。
    """
    config = load_config()
    creators = config["creators"]
    default_videos = config.get("default_videos_per_creator", 5)
    max_seconds = config.get("max_video_seconds", 600)

    if not creators:
        print("[错误] config.json 中没有配置博主。")
        sys.exit(1)

    total = sum(c.get("videos", default_videos) for c in creators)
    print(f"[配置] {len(creators)} 个博主，目标 {total} 条新视频")
    print(f"[配置] 每条最大 {max_seconds} 秒，连续 {SKIP_LIMIT} 条旧的就跳过\n")

    async with async_playwright() as p:
        browser = await launch_browser(p)
        context = await create_context(browser)
        page = await context.new_page()

        await ensure_logged_in(page)

        for creator in creators:
            await browse_creator(page, creator, default_videos, max_seconds)

        await save_auth(context)
        await browser.close()

    print("\n[完成] 所有博主浏览完毕!")


async def run_per_creator(on_before_creator=None, on_after_creator=None):
    """
    逐个博主浏览，每个博主前后调用回调函数。

    这样 run.py 可以在回调里控制 OBS：
    - on_before_creator(creator_name): 浏览前调用 → 开始录制
    - on_after_creator(creator_name):  浏览后调用 → 停止录制

    每个博主生成独立的 mp4 文件，转录出来的 Word 也是分开的。
    """
    config = load_config()
    creators = config["creators"]
    default_videos = config.get("default_videos_per_creator", 5)
    max_seconds = config.get("max_video_seconds", 600)

    if not creators:
        print("[错误] config.json 中没有配置博主。")
        sys.exit(1)

    total = sum(c.get("videos", default_videos) for c in creators)
    print(f"[配置] {len(creators)} 个博主，目标 {total} 条新视频")
    print(f"[配置] 每条最大 {max_seconds} 秒，连续 {SKIP_LIMIT} 条旧的就跳过\n")

    async with async_playwright() as p:
        browser = await launch_browser(p)
        context = await create_context(browser)
        page = await context.new_page()

        await ensure_logged_in(page)

        for creator in creators:
            name = creator["name"]

            # 浏览前回调（run.py 在这里开 OBS 录制）
            if on_before_creator:
                await on_before_creator(name)

            await browse_creator(page, creator, default_videos, max_seconds)

            # 浏览后回调（run.py 在这里停 OBS 录制）
            if on_after_creator:
                await on_after_creator(name)

        await save_auth(context)
        await browser.close()

    print("\n[完成] 所有博主浏览完毕!")


if __name__ == "__main__":
    asyncio.run(run())
