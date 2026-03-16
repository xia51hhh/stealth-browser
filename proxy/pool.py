"""
代理池管理 - 针对 192.168.31.30:10000-10010 本地代理池
支持：自动扫描可用端口、定时重检、轮换、失败自动切换
"""
import asyncio
import random
import time
import logging
from dataclasses import dataclass, field
from typing import List, Optional

from curl_cffi.requests import AsyncSession

logger = logging.getLogger("proxy.pool")

CHECK_URL = "https://httpbin.org/ip"  # 用于检测代理可用性的URL
CHECK_TIMEOUT = 8                      # 检测超时秒数
FAIL_THRESHOLD = 3                     # 连续失败N次标记不可用
RECHECK_INTERVAL = 300                 # 定时重检间隔（秒）


@dataclass
class Proxy:
    url: str                    # e.g. http://192.168.31.30:10000
    port: int = 0
    exit_ip: str = ""           # 出口IP（检测时获取）
    fail_count: int = 0
    last_used: float = 0.0
    last_checked: float = 0.0
    alive: bool = True

    def mark_fail(self):
        self.fail_count += 1
        if self.fail_count >= FAIL_THRESHOLD:
            self.alive = False
            logger.warning("代理不可用: %s (连续失败%d次)", self.url, self.fail_count)

    def mark_ok(self, exit_ip: str = ""):
        self.fail_count = 0
        self.alive = True
        self.last_checked = time.time()
        if exit_ip:
            self.exit_ip = exit_ip

    def __str__(self):
        status = "✓" if self.alive else "✗"
        return f"{status} {self.url} → {self.exit_ip or '?'}"


class LocalProxyPool:
    """
    本地代理池，专为 host:port_start~port_end 格式设计。

    用法:
        pool = LocalProxyPool(host='192.168.31.30', port_range=(10000, 10010))
        await pool.init()  # 扫描可用端口
        proxy_url = pool.get()  # 获取一个可用代理
        pool.start_recheck()  # 启动后台定时重检
    """

    def __init__(
        self,
        host: str = "192.168.31.30",
        port_range: tuple = (10000, 10010),
        strategy: str = "round_robin",  # round_robin | random
    ):
        self.host = host
        self.port_range = port_range
        self.strategy = strategy
        self._proxies: List[Proxy] = []
        self._index = 0
        self._recheck_task = None

        # 预填充所有端口（初始状态未知，alive=True等待检测）
        for port in range(port_range[0], port_range[1] + 1):
            self._proxies.append(Proxy(
                url=f"http://{host}:{port}",
                port=port,
                alive=True,
            ))

    async def init(self):
        """启动时并发检测所有端口，过滤出可用代理。"""
        logger.info("扫描代理端口 %s:%d-%d ...",
                    self.host, self.port_range[0], self.port_range[1])
        tasks = [self._check(p) for p in self._proxies]
        await asyncio.gather(*tasks)
        alive = self.alive_count
        total = len(self._proxies)
        logger.info("代理扫描完成: %d/%d 可用", alive, total)
        for p in self._proxies:
            logger.info("  %s", p)

    async def _check(self, proxy: Proxy) -> bool:
        """检测单个代理可用性，返回是否存活。"""
        try:
            async with AsyncSession(
                impersonate="chrome120",
                proxies={"http": proxy.url, "https": proxy.url},
                timeout=CHECK_TIMEOUT,
            ) as session:
                resp = await session.get(CHECK_URL)
                if resp.status_code == 200:
                    data = resp.json()
                    exit_ip = data.get("origin", "").split(",")[0].strip()
                    proxy.mark_ok(exit_ip)
                    return True
        except Exception as e:
            logger.debug("代理检测失败 %s: %s", proxy.url, e)
        proxy.alive = False
        return False

    def get(self) -> Optional[str]:
        """获取一个可用代理URL，无可用代理时返回None（直连）。"""
        alive = [p for p in self._proxies if p.alive]
        if not alive:
            logger.warning("所有代理不可用，使用直连")
            return None

        if self.strategy == "random":
            proxy = random.choice(alive)
        else:  # round_robin
            self._index = self._index % len(alive)
            proxy = alive[self._index]
            self._index += 1

        proxy.last_used = time.time()
        return proxy.url

    def get_proxy_dict(self) -> Optional[dict]:
        """返回camoufox格式的代理配置字典。"""
        url = self.get()
        return {"server": url} if url else None

    def mark_fail(self, proxy_url: str):
        """标记某个代理失败（请求失败时调用）。"""
        for p in self._proxies:
            if p.url == proxy_url:
                p.mark_fail()
                break

    def mark_ok(self, proxy_url: str):
        """标记某个代理成功（请求成功时调用）。"""
        for p in self._proxies:
            if p.url == proxy_url:
                p.mark_ok()
                break

    @property
    def alive_count(self) -> int:
        return sum(1 for p in self._proxies if p.alive)

    def stats(self) -> str:
        alive = self.alive_count
        total = len(self._proxies)
        ips = [p.exit_ip for p in self._proxies if p.alive and p.exit_ip]
        return f"代理池: {alive}/{total} 可用 | 出口IP: {ips}"

    def start_recheck(self, interval: int = RECHECK_INTERVAL):
        """启动后台定时重检任务。"""
        if self._recheck_task and not self._recheck_task.done():
            return
        self._recheck_task = asyncio.create_task(self._recheck_loop(interval))
        logger.info("启动代理定时重检，间隔 %ds", interval)

    async def _recheck_loop(self, interval: int):
        while True:
            await asyncio.sleep(interval)
            logger.info("定时重检代理池...")
            tasks = [self._check(p) for p in self._proxies]
            await asyncio.gather(*tasks)
            logger.info("重检完成: %s", self.stats())

    def stop_recheck(self):
        if self._recheck_task:
            self._recheck_task.cancel()
            self._recheck_task = None


async def with_proxy_retry(pool: LocalProxyPool, coro_fn, max_retries: int = 3):
    """
    带代理自动切换的重试装饰器。

    用法:
        result = await with_proxy_retry(pool, lambda proxy: fetch(proxy, url))
    """
    last_proxy = None
    for attempt in range(max_retries):
        proxy_url = pool.get()
        try:
            result = await coro_fn(proxy_url)
            if last_proxy:
                pool.mark_ok(last_proxy)
            return result
        except Exception as e:
            logger.warning("请求失败(attempt %d/%d) proxy=%s: %s",
                           attempt + 1, max_retries, proxy_url, e)
            if proxy_url:
                pool.mark_fail(proxy_url)
            last_proxy = proxy_url
    raise RuntimeError(f"所有重试失败（{max_retries}次）")


# 向后兼容：保留旧的 ProxyPool 类名
class ProxyPool(LocalProxyPool):
    """向后兼容别名。"""

    @classmethod
    def from_list(cls, urls: List[str]) -> "ProxyPool":
        pool = cls.__new__(cls)
        pool._proxies = [Proxy(url=u) for u in urls]
        pool._index = 0
        pool._recheck_task = None
        pool.strategy = "round_robin"
        return pool

    @classmethod
    def from_file(cls, path: str) -> "ProxyPool":
        with open(path) as f:
            urls = [l.strip() for l in f if l.strip() and not l.startswith("#")]
        return cls.from_list(urls)
