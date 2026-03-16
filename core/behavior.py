"""
行为模拟器 - 模拟真实人类的鼠标、键盘、滚动行为
目的：骗过行为分析型反检测系统（DataDome、Akamai 等）
"""
import asyncio
import math
import random


class HumanBehavior:
    """模拟人类操作行为"""

    def __init__(self, page, config: dict = None):
        self.page = page
        self.cfg = config or {}
        self._mouse_cfg = self.cfg.get("mouse", {})
        self._type_cfg = self.cfg.get("typing", {})
        self._scroll_cfg = self.cfg.get("scroll", {})
        self._delay_cfg = self.cfg.get("random_delay", {"min": 800, "max": 3000})

    async def random_delay(self, min_ms: int = None, max_ms: int = None):
        """随机等待"""
        lo = min_ms or self._delay_cfg.get("min", 800)
        hi = max_ms or self._delay_cfg.get("max", 3000)
        await asyncio.sleep(random.uniform(lo, hi) / 1000)

    async def human_move_to(self, x: int, y: int, steps: int = None):
        """
        贝塞尔曲线鼠标移动 - 不是直线移动，模拟人类手部抖动
        """
        viewport = self.page.viewport_size or {"width": 1920, "height": 1080}
        # 起点：当前鼠标位置（用随机初始点模拟）
        start_x = random.randint(0, viewport["width"])
        start_y = random.randint(0, viewport["height"])

        if steps is None:
            dist = math.sqrt((x - start_x) ** 2 + (y - start_y) ** 2)
            steps = max(10, int(dist / 15))

        # 贝塞尔控制点（添加随机偏移模拟人类手部抖动）
        cp1_x = start_x + (x - start_x) * 0.3 + random.uniform(-50, 50)
        cp1_y = start_y + (y - start_y) * 0.3 + random.uniform(-50, 50)
        cp2_x = start_x + (x - start_x) * 0.7 + random.uniform(-30, 30)
        cp2_y = start_y + (y - start_y) * 0.7 + random.uniform(-30, 30)

        for i in range(steps + 1):
            t = i / steps
            # 三次贝塞尔曲线
            mt = 1 - t
            px = (mt ** 3 * start_x +
                  3 * mt ** 2 * t * cp1_x +
                  3 * mt * t ** 2 * cp2_x +
                  t ** 3 * x)
            py = (mt ** 3 * start_y +
                  3 * mt ** 2 * t * cp1_y +
                  3 * mt * t ** 2 * cp2_y +
                  t ** 3 * y)

            # 微抖动
            if self._mouse_cfg.get("jitter", True) and 0.1 < t < 0.9:
                px += random.uniform(-2, 2)
                py += random.uniform(-2, 2)

            await self.page.mouse.move(px, py)
            # 速度变化：开始和结束慢，中间快
            speed_factor = math.sin(t * math.pi)
            delay = random.uniform(2, 8) / max(speed_factor, 0.3)
            await asyncio.sleep(delay / 1000)

    async def human_click(self, selector: str = None, x: int = None, y: int = None):
        """
        人类式点击 - 先移动鼠标到目标，停顿，然后点击
        """
        if selector:
            el = self.page.locator(selector)
            box = await el.bounding_box()
            if box:
                # 不精确点中心，加一点随机偏移
                x = box["x"] + box["width"] * random.uniform(0.3, 0.7)
                y = box["y"] + box["height"] * random.uniform(0.3, 0.7)

        if x is not None and y is not None:
            await self.human_move_to(int(x), int(y))
            # 停顿一下再点（人类反应时间）
            await asyncio.sleep(random.uniform(50, 200) / 1000)
            await self.page.mouse.click(x, y)

    async def human_type(self, selector: str, text: str):
        """
        人类式打字 - 随机间隔、偶尔打错字再修正
        """
        await self.human_click(selector)
        await asyncio.sleep(random.uniform(200, 500) / 1000)

        delay_min = self._type_cfg.get("delay_min", 50)
        delay_max = self._type_cfg.get("delay_max", 150)
        mistake_rate = self._type_cfg.get("mistake_rate", 0.02)

        for char in text:
            # 概率打错字
            if random.random() < mistake_rate:
                wrong = chr(ord(char) + random.choice([-1, 1]))
                await self.page.keyboard.press(wrong)
                await asyncio.sleep(random.uniform(100, 300) / 1000)
                await self.page.keyboard.press("Backspace")
                await asyncio.sleep(random.uniform(50, 150) / 1000)

            await self.page.keyboard.press(char)
            # 随机打字间隔
            delay = random.uniform(delay_min, delay_max)
            # 空格和标点后停顿稍长
            if char in " .,;!?":
                delay *= random.uniform(1.5, 3.0)
            await asyncio.sleep(delay / 1000)

    async def human_scroll(self, direction: str = "down", distance: int = None):
        """
        人类式滚动 - 不均匀的速度和距离
        """
        if distance is None:
            distance = random.randint(
                self._scroll_cfg.get("step_min", 100),
                self._scroll_cfg.get("step_max", 300)
            )

        sign = -1 if direction == "up" else 1
        scrolled = 0
        while scrolled < distance:
            step = random.randint(30, 80)
            step = min(step, distance - scrolled)
            await self.page.mouse.wheel(0, sign * step)
            scrolled += step
            await asyncio.sleep(random.uniform(20, 60) / 1000)

        # 滚动后停顿（阅读时间）
        await asyncio.sleep(random.uniform(
            self._scroll_cfg.get("pause_min", 500),
            self._scroll_cfg.get("pause_max", 2000)
        ) / 1000)

    async def random_mouse_movement(self, count: int = 3):
        """随机移动鼠标几次，模拟闲逛"""
        viewport = self.page.viewport_size or {"width": 1920, "height": 1080}
        for _ in range(count):
            x = random.randint(100, viewport["width"] - 100)
            y = random.randint(100, viewport["height"] - 100)
            await self.human_move_to(x, y)
            await asyncio.sleep(random.uniform(300, 1000) / 1000)
