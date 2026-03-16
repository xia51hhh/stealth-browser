"""
代理池管理 - 支持列表轮换和健康检查
"""
import asyncio
import random
import time
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Proxy:
    url: str                    # e.g. http://user:pass@host:port
    fail_count: int = 0
    last_used: float = 0.0
    last_checked: float = 0.0
    alive: bool = True

    def mark_fail(self):
        self.fail_count += 1
        if self.fail_count >= 3:
            self.alive = False

    def mark_ok(self):
        self.fail_count = 0
        self.alive = True
        self.last_checked = time.time()


class ProxyPool:
    """
    代理池：轮换 + 健康过滤。

    用法:
        pool = ProxyPool.from_list([
            "http://1.2.3.4:8080",
            "socks5://user:pass@5.6.7.8:1080",
        ])
        proxy = pool.get()
    """

    def __init__(self, proxies: List[Proxy] = None):
        self._proxies: List[Proxy] = proxies or []
        self._index = 0

    @classmethod
    def from_list(cls, urls: List[str]) -> "ProxyPool":
        return cls([Proxy(url=u) for u in urls])

    @classmethod
    def from_file(cls, path: str) -> "ProxyPool":
        """每行一个代理URL的文本文件。"""
        with open(path) as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        return cls.from_list(urls)

    def get(self, strategy: str = "round_robin") -> Optional[str]:
        """获取一个可用代理URL，无可用代理时返回None（直连）。"""
        alive = [p for p in self._proxies if p.alive]
        if not alive:
            return None
        if strategy == "random":
            proxy = random.choice(alive)
        else:  # round_robin
            proxy = alive[self._index % len(alive)]
            self._index += 1
        proxy.last_used = time.time()
        return proxy.url

    def report_fail(self, url: str):
        for p in self._proxies:
            if p.url == url:
                p.mark_fail()
                break

    def report_ok(self, url: str):
        for p in self._proxies:
            if p.url == url:
                p.mark_ok()
                break

    def stats(self) -> dict:
        return {
            "total": len(self._proxies),
            "alive": sum(1 for p in self._proxies if p.alive),
            "dead": sum(1 for p in self._proxies if not p.alive),
        }
