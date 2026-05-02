"""
统一浏览器管理模块

所有需要 Playwright 的模块（browser.py、live.py、run.py）
都通过这个模块启动浏览器，保证:

1. 固定使用本机安装的 Chrome 浏览器（不用 Playwright 自带的 Chromium）
   → 避免抖音检测到"多个浏览器登录"的问题
2. 共享同一份 auth.json 登录状态
3. 统一的浏览器启动参数
4. 自动确保页面声音开启（OBS 需要录到浏览器声音）

如果你想换成 Edge，改 BROWSER_CHANNEL = "msedge" 即可。
"""

from pathlib import Path
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

# ====== 在这里选择浏览器 ======
# "chrome"  = 本机安装的 Google Chrome
# "msedge"  = 本机安装的 Microsoft Edge
BROWSER_CHANNEL = "chrome"

AUTH_FILE = Path(__file__).parent.parent / "auth.json"


async def launch_browser(playwright) -> Browser:
    """
    启动本机浏览器，确保音频自动播放不被拦截。

    --autoplay-policy=no-user-gesture-required:
        允许页面在没有用户交互的情况下自动播放带声音的视频。
        Chrome 默认会阻止自动播放声音，这个参数跳过限制。

    --disable-features=PreloadMediaEngagementData,MediaEngagementBypassAutoplayPolicies:
        禁用 Chrome 的"媒体参与度"系统。Chrome 会根据你之前跟网站的
        交互记录决定是否允许自动播放声音，这两个 flag 关掉这个判断，
        确保每次都能播出声音。
    """
    browser = await playwright.chromium.launch(
        channel=BROWSER_CHANNEL,
        headless=False,
        args=[
            "--start-maximized",
            "--disable-blink-features=AutomationControlled",
            "--autoplay-policy=no-user-gesture-required",
            "--disable-features=PreloadMediaEngagementData,MediaEngagementBypassAutoplayPolicies",
        ],
    )
    return browser


async def create_context(browser: Browser) -> BrowserContext:
    """
    创建浏览器上下文。

    关键: 不设置 is_mobile、不设置 has_touch，
    这样 Chrome 不会模拟移动设备（移动设备默认静音自动播放）。
    """
    context_opts = {
        "viewport": {"width": 1280, "height": 720},
    }

    if AUTH_FILE.exists():
        context_opts["storage_state"] = str(AUTH_FILE)
        print(f"[登录] 使用已保存的登录状态 ({BROWSER_CHANNEL})")
    else:
        print(f"[登录] 首次运行({BROWSER_CHANNEL})，需要手动登录抖音")

    context = await browser.new_context(**context_opts)
    return context


async def save_auth(context: BrowserContext):
    """保存登录状态到 auth.json"""
    await context.storage_state(path=str(AUTH_FILE))
    print(f"[保存] 登录状态已保存到 {AUTH_FILE}")


async def ensure_audio(page: Page):
    """
    确保页面上所有 video 元素的声音是开启的。

    抖音网页版经常默认静音播放视频（muted=true），
    这个函数会:
    1. 取消所有 video 的 muted 属性
    2. 设置 volume 为 1.0（最大）
    3. 设置一个 MutationObserver 持续监控新加入的 video 元素，
       确保后续动态加载的视频也不会被静音

    OBS 录的是系统桌面音频，如果浏览器里视频是静音的，
    录出来的 mp4 就没声音，Whisper 转录就是空的。
    """
    await page.evaluate("""
        () => {
            // 取消当前所有 video 的静音
            function unmute(v) {
                v.muted = false;
                v.volume = 1.0;
            }

            document.querySelectorAll('video').forEach(unmute);

            // 监控后续动态加入的 video
            const observer = new MutationObserver(mutations => {
                for (const m of mutations) {
                    for (const node of m.addedNodes) {
                        if (node.tagName === 'VIDEO') unmute(node);
                        if (node.querySelectorAll) {
                            node.querySelectorAll('video').forEach(unmute);
                        }
                    }
                }
            });
            observer.observe(document.body, { childList: true, subtree: true });

            // 每 3 秒再强制扫一遍（防止 JS 重新设置 muted）
            if (!window._unmuteInterval) {
                window._unmuteInterval = setInterval(() => {
                    document.querySelectorAll('video').forEach(unmute);
                }, 3000);
            }
        }
    """)
    print("[音频] 已确保页面视频声音开启")


async def ensure_logged_in(page: Page):
    """
    如果没有 auth.json（首次运行），引导用户手动登录。
    """
    if AUTH_FILE.exists():
        return

    print("\n[登录] 请在弹出的浏览器中扫码登录抖音")
    print("       登录成功后回到终端按 Enter 继续\n")

    await page.goto("https://www.douyin.com", wait_until="domcontentloaded", timeout=60000)

    import asyncio
    await asyncio.get_event_loop().run_in_executor(
        None, lambda: input("  >>> 登录完成后按 Enter 继续...")
    )
