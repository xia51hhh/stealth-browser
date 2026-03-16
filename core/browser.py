"""
StealthBrowser - 核心浏览器管理器
整合 Camoufox + 隐身注入 + 行为模拟
"""
import asyncio
import glob
import logging
import os
from pathlib import Path

from camoufox.async_api import AsyncCamoufox

from .config import Config
from .stealth import get_stealth_scripts
from .behavior import HumanBehavior

logger = logging.getLogger("stealth-browser")


class StealthBrowser:
    """
    反检测浏览器封装

    用法:
        async with StealthBrowser() as browser:
            page = await browser.new_page()
            await page.goto("https://example.com")
    """

    def __init__(self, config_path: str = None):
        self.config = Config(config_path)
        self._browser = None   # camoufox Browser对象
        self._context = None   # Playwright BrowserContext
        self._setup_logging()

    def _setup_logging(self):
        level = self.config.get("logging.level", "INFO")
        log_file = self.config.get("logging.file")
        if log_file:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            handler = logging.FileHandler(log_file, encoding="utf-8")
        else:
            handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s"
        ))
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    def _build_launch_kwargs(self) -> dict:
        """构建camoufox启动参数，与camoufox版本解耦——只使用公开文档参数。"""
        browser_cfg = self.config.browser
        proxy_cfg = self.config.proxy

        kwargs = {
            "headless": browser_cfg.get("headless", "virtual"),
            "os": browser_cfg.get("os", "windows"),
            "block_webrtc": True,
            "geoip": browser_cfg.get("geoip", True),
        }

        # 微软字体（可选，目录不存在时跳过）
        ms_fonts = glob.glob('/usr/share/fonts/truetype/msttcorefonts/*.ttf')
        if ms_fonts:
            kwargs["fonts"] = ms_fonts

        # 代理
        if proxy_cfg.get("enabled"):
            proxy = {"server": proxy_cfg["server"]}
            if proxy_cfg.get("username"):
                proxy["username"] = proxy_cfg["username"]
                proxy["password"] = proxy_cfg.get("password", "")
            kwargs["proxy"] = proxy

        return kwargs

    async def __aenter__(self):
        launch_kwargs = self._build_launch_kwargs()
        browser_cfg = self.config.browser

        logger.info("启动 Camoufox | os=%s headless=%s",
                    launch_kwargs.get("os"), launch_kwargs.get("headless"))

        # 使用标准 async with，camoufox更新时只需检查这一处参数
        self._camoufox = AsyncCamoufox(**launch_kwargs)
        self._browser = await self._camoufox.__aenter__()

        self._context = await self._browser.new_context(
            viewport=browser_cfg.get("viewport") or {"width": 1920, "height": 1080},
            locale=browser_cfg.get("locale", "zh-CN"),
        )

        # 注入补充隐身脚本（WebRTC防泄漏等camoufox未覆盖的部分）
        disable_webrtc = self.config.webrtc.get("disable", True)
        stealth_scripts = get_stealth_scripts(disable_webrtc)
        for script in stealth_scripts:
            await self._context.add_init_script(script)

        logger.info("Camoufox 启动成功，注入 %d 个补充脚本", len(stealth_scripts))
        return self

    async def __aexit__(self, *args):
        if self._context:
            await self._context.close()
            self._context = None
        if hasattr(self, '_camoufox') and self._camoufox:
            await self._camoufox.__aexit__(*args)
            self._camoufox = None
        logger.info("浏览器已关闭")

    async def new_page(self) -> "StealthPage":
        """创建新的隐身页面。"""
        import random
        page = await self._context.new_page()

        async def _handle_dialog(dialog):
            await asyncio.sleep(random.uniform(1.0, 4.0))
            await dialog.dismiss()

        page.on("dialog", lambda d: asyncio.ensure_future(_handle_dialog(d)))
        return StealthPage(page, self.config.behavior)

    @property
    def context(self):
        return self._context


class StealthPage:
    """
    增强的页面对象 - 包装 Camoufox Page + 行为模拟

    既可以用原生 page 方法，也可以用 stealth_* 方法进行拟人操作
    """

    def __init__(self, page, behavior_config: dict = None):
        self.page = page
        self.human = HumanBehavior(page, behavior_config)

    def __getattr__(self, name):
        """代理到原生 page 对象"""
        return getattr(self.page, name)

    async def stealth_goto(self, url: str, **kwargs):
        """
        隐身导航 - 访问页面后做一些随机人类行为
        """
        kwargs.setdefault("timeout", 60000)
        kwargs.setdefault("wait_until", "domcontentloaded")
        response = await self.page.goto(url, **kwargs)
        # 等待页面加载
        await self.page.wait_for_load_state("domcontentloaded")
        # 随机鼠标移动（触发行为检测的 mousemove 监听器）
        await self.human.random_mouse_movement(count=2)
        return response

    async def stealth_click(self, selector: str):
        """人类式点击"""
        await self.human.human_click(selector)

    async def stealth_type(self, selector: str, text: str):
        """人类式打字"""
        await self.human.human_type(selector, text)

    async def stealth_scroll(self, direction: str = "down", distance: int = None):
        """人类式滚动"""
        await self.human.human_scroll(direction, distance)

    async def save_screenshot(self, path: str = None):
        """保存截图"""
        if path is None:
            import time
            os.makedirs("screenshots", exist_ok=True)
            path = f"screenshots/{int(time.time())}.png"
        await self.page.screenshot(path=path, full_page=True)
        logger.info("截图已保存: %s", path)
        return path
