import asyncio
import math
import random
from typing import Tuple


def _bezier_points(start: Tuple, end: Tuple, steps: int = 30):
    """生成贝塞尔曲线轨迹点（含随机控制点）。"""
    sx, sy = start
    ex, ey = end
    cx = (sx + ex) / 2 + random.randint(-80, 80)
    cy = (sy + ey) / 2 + random.randint(-80, 80)
    points = []
    for i in range(steps + 1):
        t = i / steps
        x = (1 - t) ** 2 * sx + 2 * (1 - t) * t * cx + t ** 2 * ex
        y = (1 - t) ** 2 * sy + 2 * (1 - t) * t * cy + t ** 2 * ey
        points.append((x, y))
    return points


async def human_move(page, x: float, y: float):
    """模拟人类鼠标移动到目标坐标。"""
    current = await page.evaluate("() => ({x: window.mouseX || 0, y: window.mouseY || 0})")
    start = (current.get("x", 0), current.get("y", 0))
    steps = random.randint(20, 40)
    points = _bezier_points(start, (x, y), steps)
    for px, py in points:
        await page.mouse.move(px, py)
        await asyncio.sleep(random.uniform(0.005, 0.018))


async def human_click(page, x: float, y: float):
    """移动到目标后模拟人类点击（含按下/抬起随机延迟）。"""
    await human_move(page, x, y)
    await asyncio.sleep(random.uniform(0.05, 0.15))
    await page.mouse.down()
    await asyncio.sleep(random.uniform(0.04, 0.12))
    await page.mouse.up()


async def human_click_element(page, selector: str):
    """定位元素并人类化点击。"""
    el = await page.wait_for_selector(selector, timeout=10000)
    box = await el.bounding_box()
    if not box:
        raise RuntimeError(f"Element {selector} has no bounding box")
    x = box["x"] + box["width"] * random.uniform(0.3, 0.7)
    y = box["y"] + box["height"] * random.uniform(0.3, 0.7)
    await human_click(page, x, y)


async def human_type(page, selector: str, text: str):
    """人类化输入文字（随机按键间隔，偶尔停顿）。"""
    await human_click_element(page, selector)
    await asyncio.sleep(random.uniform(0.2, 0.5))
    for char in text:
        await page.keyboard.type(char)
        delay = random.uniform(0.04, 0.16)
        if random.random() < 0.05:
            delay += random.uniform(0.3, 0.8)
        await asyncio.sleep(delay)


async def human_scroll(page, direction: str = "down", distance: int = None):
    """人类化滚动页面。"""
    if distance is None:
        distance = random.randint(200, 600)
    delta = distance if direction == "down" else -distance
    steps = random.randint(3, 7)
    for _ in range(steps):
        await page.mouse.wheel(0, delta // steps)
        await asyncio.sleep(random.uniform(0.05, 0.15))
