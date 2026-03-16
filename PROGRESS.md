# stealth-browser 项目进度文档

> 更新时间：2026-03-16

---

## 项目目标

构建一套基于开源工具的浏览器自动化反检测系统，能够绕过主流bot检测平台（Cloudflare、Akamai、DataDome等），用于合法的网络自动化测试和研究。

---

## 技术选型

| 层级 | 选型 | 版本 | 说明 |
|------|------|------|------|
| 核心浏览器 | **Camoufox** | 0.4.11 | Firefox引擎，C++源码级指纹保护，最强反检测能力 |
| TLS/JA3层 | **curl_cffi** | 0.14.0 | 伪装浏览器TLS握手指纹，适用于纯HTTP请求 |
| 行为模拟 | **core/behavior.py** | 自实现 | 三次贝塞尔鼠标轨迹、随机打字节奏、分步滚动 |
| 代理管理 | **proxy/pool.py** | 自实现 | 轮换+健康检查+失败标记 |
| 配置管理 | **YAML** | - | config/default.yaml |

### 选型对比

| 框架 | Stars | 反检测层级 | 最终选择原因 |
|------|------:|----------|-----------|
| **Camoufox** | 6,144 | C++原生 | 唯一在浏览器引擎层解决指纹问题，Firefox引擎 |
| Patchright | 2,596 | CDP协议层 | Chrome-only，无原生指纹保护 |
| undetected-chromedriver | 12,449 | 驱动层 | 维护减缓，1147个issues |
| nodriver | 3,836 | 驱动层 | 不解决指纹问题 |

---

## 当前系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    业务逻辑层（待开发）                    │
├─────────────────────────────────────────────────────────┤
│  行为层  │  core/behavior.py  贝塞尔鼠标 + 人类打字        │
├─────────────────────────────────────────────────────────┤
│  浏览器层 │  Camoufox 0.4.11  Firefox C++级指纹保护        │
│          │  headless='virtual' 内置Xvfb，启用GPU渲染       │
│          │  geoip=True 跟随代理IP设置时区/语言              │
├─────────────────────────────────────────────────────────┤
│  HTTP层  │  curl_cffi 0.14.0   TLS/JA3指纹伪装            │
├─────────────────────────────────────────────────────────┤
│  网络层  │  proxy/pool.py      代理轮换 + 健康检查          │
└─────────────────────────────────────────────────────────┘
```

---

## 部署状态 ✅

| 项目 | 状态 | 说明 |
|------|------|------|
| 虚拟环境 | ✅ | `/home/toe2/stealth-browser/bin/activate` |
| camoufox | ✅ | v0.4.11，Firefox 135二进制已下载 |
| camoufox[geoip] | ✅ | GeoIP数据库63.5MB已下载 |
| curl_cffi | ✅ | v0.14.0 |
| 微软字体 | ✅ | 60个TTF已安装 `/usr/share/fonts/truetype/msttcorefonts/` |
| Xvfb | ✅ | 已安装，`headless='virtual'`模式依赖 |
| 代理 | ✅ | `http://192.168.31.30:10000`（端口10000-10002均可用）|

### 激活环境
```bash
cd /home/toe2/stealth-browser && source bin/activate
```

---

## 最优配置

```python
import asyncio, glob
from camoufox.async_api import AsyncCamoufox

fonts = glob.glob('/usr/share/fonts/truetype/msttcorefonts/*.ttf')

async def main():
    async with AsyncCamoufox(
        headless='virtual',   # 内置Xvfb，启用GPU/WebGL
        os='windows',
        block_webrtc=True,
        geoip=True,
        proxy={'server': 'http://192.168.31.30:10000'},
        fonts=fonts,
    ) as browser:
        page = await browser.new_page()
        await page.goto('https://target.com')
        await page.screenshot(path='screenshot.png')

asyncio.run(main())
```

---

## 检测测试结果

### 测试日期：2026-03-16
### 配置：camoufox 0.4.11，headless='virtual'，geoip=True

#### 1. bot.sannysoft.com — **28/31通过（90.3%）✅**

| 检测项 | 结果 |
|--------|------|
| navigator.webdriver | ✅ PASS（完全隐藏）|
| WebDriver Advanced | ✅ PASS |
| Permissions | ✅ PASS |
| Plugins (5个) | ✅ PASS |
| PHANTOM_UA/PROPERTIES/ETSL/LANGUAGE/WEBSOCKET | ✅ 全部PASS |
| MQ_SCREEN/PHANTOM_OVERFLOW/PHANTOM_WINDOW_HEIGHT | ✅ 全部PASS |
| HEADCHR_UA/CHROME_OBJ/PERMISSIONS/PLUGINS/IFRAME | ✅ 全部PASS |
| CHR_DEBUG_TOOLS/SELENIUM_DRIVER/BATTERY/MEMORY | ✅ 全部PASS |
| TRANSPARENT_PIXEL/SEQUENTUM/VIDEO_CODECS | ✅ 全部PASS |
| Chrome(New) | ❌ Firefox无window.chrome，**预期行为** |
| WebGL Vendor/Renderer | ❌ v0.1.3测试时无头无GPU，**virtual模式已解决** |

#### 2. creepjs — **核心指标全绿 ✅**

| 指标 | 结果 |
|------|------|
| WebGL | Google Inc.(Intel)/ANGLE ✅ |
| GPU | Intel HD Graphics ✅ |
| headless | 0% ✅ |
| stealth | 0% ✅ |
| chromium headless | false ✅ |
| WebRTC | IP已匿名(000.000.000.000) ✅ |
| Timezone | 跟随代理IP(HK) ✅ |
| UA | Windows NT 10.0 Firefox/135.0 ✅ |
| 字体回退链 | Sans:Linux ⚠️ |

#### 3. browserleaks.com/javascript — **127字段无泄漏 ✅**

#### 4. pixelscan.net — **⚠️ 跳转主页**
- 点击按钮成功，但结果页跳转回主页
- 疑因字体回退链(Linux)或WebGL特征触发
- 截图已保存：`tests/screenshots/pixelscan_final.png`

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
| 时区/语言一致性 | ✅ | `geoip=True` 跟随代理IP |
| 鼠标行为 | ✅ | core/behavior.py 贝塞尔曲线 |
| 打字行为 | ✅ | core/behavior.py 随机间隔 |
| Selenium特征 | ✅ | 不使用Selenium |
| IP信誉 | 手动 | proxy/pool.py |
| 字体回退链(Linux) | ⚠️ | camoufox底层限制，待官方修复 |

---

## 已知限制

### 字体回退链显示Linux
- **现象**：creepjs的`platform hints`显示`Sans:Linux`
- **根因**：camoufox在Linux上CSS`sans-serif`通用族回退链始终映射到Linux字体，与传入的字体文件无关
- **尝试过的方案**：安装微软字体、`fonts`参数传入TTF、virtual/headed模式，均无效
- **实际影响**：低——大多数bot检测系统不以CSS字体回退链作为主要判断依据
- **解决方案**：等camoufox官方修复，或在Windows/macOS机器上运行

---

## 下一步计划

### 优先级高
- [ ] 针对具体目标网站开发业务逻辑
- [ ] 将最优配置（virtual+geoip+fonts）同步到 `core/browser.py`
- [ ] 更新 `config/default.yaml` 支持headless='virtual'

### 优先级中
- [ ] 接入免费代理源自动抓取（proxy/pool.py扩展）
- [ ] 添加请求速率限制
- [ ] 完善日志和监控

### 优先级低
- [ ] 支持多浏览器实例并发
- [ ] 接入付费CAPTCHA解决服务（2captcha/unicaps）
- [ ] pixelscan.net通过率优化

---

## 环境信息

- **OS**: Linux Ubuntu 24.04, kernel 6.17
- **Python**: 3.12.3
- **camoufox**: 0.4.11（Firefox 135）
- **curl_cffi**: 0.14.0
- **代理**: `http://192.168.31.30:10000`（端口10000-10002可用）
- **出口IP**: 43.199.63.158
- **Mesa**: 25.2.8（swrast_dri.so已安装）
- **Xvfb**: 2:21.1.12
- **微软字体**: 60个TTF
- **GeoIP DB**: 已下载（63.5MB）
