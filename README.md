# stealth-browser

反检测浏览器自动化框架，基于 **Camoufox 0.4.11**（Firefox引擎，C++级指纹保护）。

> 最后更新：2026-03-16

---

## 架构

```
浏览器层  →  Camoufox 0.4.11   C++源码级指纹保护（Canvas/WebGL/字体/UA）
HTTP层    →  curl_cffi 0.14.0  TLS/JA3 指纹伪装（纯HTTP场景）
行为层    →  core/behavior.py  贝塞尔鼠标轨迹 + 人类打字节奏
代理层    →  proxy/pool.py     代理轮换 + 健康检查
```

---

## 反检测测试报告（2026-03-16，有头virtual模式）

> 测试配置：`headless='virtual'`，`os='windows'`，`geoip=True`，代理池10个出口IP

### bot.sannysoft.com — 28/31 通过 ✅

| 检测项 | 结果 |
|--------|------|
| `navigator.webdriver` | ✅ missing（隐藏） |
| WebDriver Advanced | ✅ passed |
| SELENIUM_DRIVER | ✅ ok |
| 所有 PHANTOM_* (8项) | ✅ ok |
| 所有 HEADCHR_* (5项) | ✅ ok |
| CHR_BATTERY / CHR_MEMORY | ✅ ok |
| VIDEO_CODECS / SEQUENTUM | ✅ ok |
| Chrome (New) | ❌ missing — **预期**，Firefox无`window.chrome` |
| WebGL Vendor/Renderer | ❌ virtual模式下GPU软渲染，WebGL context存在但参数不同 |

### creepjs — headless 0% ✅

| 指标 | 结果 |
|------|------|
| `chromium: false` | ✅ |
| `0% like headless` | ✅ |
| `0% headless` | ✅ |
| `0% stealth` | ✅ |
| WebRTC | ✅ IP已匿名 |
| GPU | ✅ Google Inc.(Intel)/ANGLE |
| Timezone | ✅ 跟随代理IP自动设置 |
| UserAgent | ✅ Windows NT 10.0 Firefox/135.0 |
| 字体 | ⚠️ Sans:Linux（camoufox底层限制）|

### browserleaks.com/javascript

| 指标 | 结果 |
|------|------|
| `navigator.webdriver` | ✅ `false`（未泄漏）|
| 127个JS字段 | ✅ 无异常 |

### 代理池

| 端口 | 出口IP | 状态 |
|------|--------|------|
| 10000 | 43.199.63.158 (HK) | ✅ |
| 10001 | 104.28.x.x (CF) | ✅ |
| 10002 | 103.62.49.130 | ✅ |
| 10003 | 108.181.23.253 | ✅ |
| 10004 | 140.238.37.247 | ✅ |
| 10005 | 130.61.149.111 | ✅ |
| 10006 | 132.145.62.88 | ✅ |
| 10008 | 54.249.25.98 (JP) | ✅ |
| 10009 | 3.1.81.181 (SG) | ✅ |
| 10010 | 155.117.87.197 | ✅ |
| 10007 | - | ❌ 不可用 |

---

## 快速开始

```bash
# 1. 激活虚拟环境
cd /home/toe2/stealth-browser && source bin/activate

# 2. 下载 Camoufox Firefox 二进制（已完成，无需重复）
https_proxy=http://192.168.31.30:10000 camoufox fetch

# 3. 运行检测测试
python tests/multi_site_test.py

# 4. 运行使用示例
python example.py
```

---

## 最优配置（推荐）

```python
import asyncio
import glob
from camoufox.async_api import AsyncCamoufox

fonts = glob.glob('/usr/share/fonts/truetype/msttcorefonts/*.ttf')

async def main():
    async with AsyncCamoufox(
        headless='virtual',   # 内置Xvfb虚拟显示，启用GPU渲染，解决WebGL问题
        os='windows',         # 伪装OS: windows / macos / linux
        block_webrtc=True,    # 阻止WebRTC IP泄漏
        geoip=True,           # 根据代理IP自动设置时区/语言
        proxy={'server': 'http://192.168.31.30:10000'},
        fonts=fonts,          # 注入微软字体
    ) as browser:
        page = await browser.new_page()
        await page.goto('https://target.com')
        content = await page.content()
        await page.screenshot(path='screenshot.png')

asyncio.run(main())
```

### 参数说明

| 参数 | 值 | 说明 |
|------|-----|------|
| `headless` | `'virtual'` | 内置Xvfb，启用GPU/WebGL，推荐 |
| `headless` | `True` | 纯无头，WebGL不可用 |
| `headless` | `False` | 真实显示器模式 |
| `os` | `'windows'/'macos'/'linux'` | 伪装操作系统 |
| `geoip` | `True` | 需要 `pip install camoufox[geoip]` |

---

## TLS层HTTP请求

不需要JS渲染时，用curl_cffi直接发请求（更快）：

```python
import asyncio
from core.http_client import StealthHTTPClient

async def main():
    async with StealthHTTPClient(impersonate='chrome120') as client:
        resp = await client.get('https://api.example.com/data')
        print(resp.status_code, resp.json())

asyncio.run(main())
```

---

## 代理池

```python
from proxy.pool import ProxyPool

pool = ProxyPool.from_list([
    'http://user:pass@1.2.3.4:8080',
    'socks5://5.6.7.8:1080',
])
proxy = pool.get()          # 轮换获取
pool.report_fail(proxy)     # 标记失败
pool.report_ok(proxy)       # 标记成功
print(pool.stats())         # {'total':2,'alive':1,'dead':1}
```

---

## 文件结构

```
stealth-browser/
├── core/
│   ├── browser.py        # StealthBrowser / StealthPage 主类
│   ├── behavior.py       # HumanBehavior 行为模拟
│   ├── stealth.py        # JS注入补丁（WebRTC防泄漏等）
│   ├── config.py         # YAML配置管理
│   └── http_client.py    # StealthHTTPClient（curl_cffi）
├── behavior/
│   └── mouse.py          # 独立贝塞尔曲线鼠标函数
├── proxy/
│   └── pool.py           # ProxyPool 代理池
├── tests/
│   ├── multi_site_test.py     # 多站点检测测试
│   ├── run_detection_test.py  # 单站点检测测试
│   └── screenshots/           # 测试截图
├── config/
│   └── default.yaml      # 主配置文件
├── example.py            # 使用示例
├── requirements.txt      # 依赖清单
├── README.md             # 本文件
└── PROGRESS.md           # 进度文档
```

---

## 反检测覆盖面

| 检测向量 | 状态 | 实现方式 |
|---------|:----:|--------|
| `navigator.webdriver` | ✅ | Camoufox内置 |
| CDP信号泄漏 | ✅ | Camoufox内置（Firefox无CDP）|
| Canvas指纹 | ✅ | Camoufox C++原生 |
| WebGL指纹 | ✅ | Camoufox C++原生（virtual模式）|
| 字体指纹 | ✅ | Camoufox C++原生 |
| WebRTC IP泄漏 | ✅ | `block_webrtc=True` |
| TLS/JA3指纹 | ✅ | curl_cffi（纯HTTP场景）|
| 时区/语言 | ✅ | `geoip=True` 跟随代理IP |
| 鼠标行为 | ✅ | core/behavior.py 贝塞尔曲线 |
| 打字行为 | ✅ | core/behavior.py 随机间隔 |
| Selenium特征 | ✅ | 不使用Selenium |
| IP信誉 | 手动 | proxy/pool.py |
| 字体回退链(Linux) | ⚠️ | camoufox已知限制，等官方修复 |

---

## 检测测试结果（2026-03-16）

### bot.sannysoft.com — 28/31通过 ✅
所有核心bot检测项通过（webdriver / Selenium / PhantomJS / HeadlessChrome）

### creepjs — headless 0% ✅
```
WebGL:    Google Inc.(Intel) / ANGLE  ✅
GPU:      Intel HD Graphics           ✅
headless: 0%                          ✅
stealth:  0%                          ✅
WebRTC:   IP已匿名(000.000.000.000)   ✅
Timezone: 跟随代理IP                  ✅
UA:       Windows NT 10.0 Firefox     ✅
字体:     Sans:Linux                  ⚠️
```

### browserleaks.com/javascript — 127字段无泄漏 ✅

---

## 环境信息

- **Python**: 3.12.3
- **camoufox**: 0.4.11（Firefox 135）
- **curl_cffi**: 0.14.0
- **代理**: `http://192.168.31.30:10000`（端口10000-10002可用）
- **GeoIP数据库**: 已下载（63.5MB）
- **微软字体**: 已安装（60个TTF，`/usr/share/fonts/truetype/msttcorefonts/`）
- **Xvfb**: 已安装（virtual模式依赖）
