"""
HTTP客户端 - 使用 curl_cffi 伪装TLS/JA3指纹
适用于不需要JS渲染的API请求，绕过TLS层检测
"""
from curl_cffi.requests import AsyncSession

# 支持的浏览器指纹
BROWSER_PROFILES = [
    "chrome120", "chrome119", "chrome118",
    "firefox120", "firefox117",
    "safari17_0", "safari16_5",
]


class StealthHTTPClient:
    """
    伪装浏览器TLS指纹的HTTP客户端。
    用于直接HTTP请求（不需要JS），比启动浏览器快得多。

    用法:
        async with StealthHTTPClient() as client:
            resp = await client.get("https://api.example.com/data")
            print(resp.json())
    """

    def __init__(self, impersonate: str = "chrome120", proxy: str = None):
        self.impersonate = impersonate
        self.proxy = proxy
        self._session = None

    async def __aenter__(self):
        self._session = AsyncSession(
            impersonate=self.impersonate,
            proxies={"http": self.proxy, "https": self.proxy} if self.proxy else None,
        )
        return self

    async def __aexit__(self, *args):
        if self._session:
            await self._session.close()
            self._session = None

    async def get(self, url: str, **kwargs):
        return await self._session.get(url, **kwargs)

    async def post(self, url: str, **kwargs):
        return await self._session.post(url, **kwargs)

    async def request(self, method: str, url: str, **kwargs):
        return await self._session.request(method, url, **kwargs)
