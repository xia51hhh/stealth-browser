"""
多站点反检测效果测试
测试站点：
  1. bot.sannysoft.com  - 经典bot检测
  2. pixelscan.net      - 指纹一致性检测（需点击按钮）
  3. browserleaks.com/javascript - JS属性泄漏
  4. abrahamjuliot.github.io/creepjs - 综合信任评分
"""
import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from camoufox.async_api import AsyncCamoufox

PROXY = {'server': 'http://192.168.31.30:10000'}
SCREENSHOT_DIR = 'tests/screenshots'


def make_browser():
    return AsyncCamoufox(
        headless=True,
        os='windows',
        block_webrtc=True,
        proxy=PROXY,
    )


async def test_sannysoft():
    """bot.sannysoft.com - 提取所有pass/fail项"""
    print('\n' + '='*60)
    print('[1/4] bot.sannysoft.com')
    async with make_browser() as browser:
        page = await browser.new_page()
        await page.goto('https://bot.sannysoft.com', timeout=30000, wait_until='domcontentloaded')
        await asyncio.sleep(4)
        result = await page.evaluate(
            "() => { const r={}; document.querySelectorAll('table tr').forEach(row=>{ "
            "const c=row.querySelectorAll('td'); if(c.length>=2){ "
            "const k=c[0].innerText.trim(),cl=c[1].className||'',v=c[1].innerText.trim(); "
            "if(k&&(cl.includes('passed')||cl.includes('failed')))r[k]={v,ok:cl.includes('passed')};}}); return r;}"
        )
        passed = [k for k,v in result.items() if v['ok']]
        failed = [k for k,v in result.items() if not v['ok']]
        print(f'  通过: {len(passed)}, 未通过: {len(failed)}')
        for k in passed:
            print(f'  ✓ {k}')
        for k in failed:
            print(f'  ✗ {k}: {result[k]["v"][:50]}')
        await page.screenshot(path=f'{SCREENSHOT_DIR}/sannysoft_final.png', full_page=True)
        return {'site': 'sannysoft', 'passed': len(passed), 'failed': len(failed), 'details': result}


async def test_pixelscan():
    """pixelscan.net - 点击Scan按钮后提取结果"""
    print('\n' + '='*60)
    print('[2/4] pixelscan.net')
    async with make_browser() as browser:
        page = await browser.new_page()
        await page.goto('https://pixelscan.net', timeout=30000, wait_until='domcontentloaded')
        await asyncio.sleep(2)
        # 点击 "Scan My Browser Now" 按钮
        try:
            btn = await page.wait_for_selector('a.btn.btn-primary.btn-xl', timeout=8000)
            await btn.click()
            print('  已点击 Scan My Browser Now')
            await asyncio.sleep(20)  # 等待扫描完成（pixelscan异步JS较慢）
        except Exception as e:
            print(f'  按钮点击失败: {e}')
        await page.screenshot(path=f'{SCREENSHOT_DIR}/pixelscan_after_click.png', full_page=True)
        # 提取结果文字
        text = await page.evaluate("() => document.body.innerText.slice(0, 2000)")
        # 找一致性评分
        score_el = await page.evaluate(
            "() => { const els=document.querySelectorAll('[class*=score],[class*=result],[class*=status],[class*=verdict],[class*=rating]'); "
            "return [...els].map(e=>e.innerText.trim()).filter(t=>t).slice(0,10).join(' | '); }"
        )
        print(f'  评分元素: {score_el[:200] if score_el else "未找到"}')
        print(f'  页面摘要: {text[:400]}')
        return {'site': 'pixelscan', 'text': text[:500]}


async def test_browserleaks():
    """browserleaks.com/javascript - JS属性检测"""
    print('\n' + '='*60)
    print('[3/4] browserleaks.com/javascript')
    async with make_browser() as browser:
        page = await browser.new_page()
        await page.goto('https://browserleaks.com/javascript', timeout=30000, wait_until='domcontentloaded')
        await asyncio.sleep(3)
        result = await page.evaluate(
            "() => { const r={}; document.querySelectorAll('tr').forEach(row=>{ "
            "const c=row.querySelectorAll('td'); "
            "if(c.length>=2){const k=c[0].innerText.trim(),v=c[1].innerText.trim(); if(k&&v)r[k]=v;} }); return r; }"
        )
        key_fields = ['User Agent', 'Navigator Platform', 'WebDriver', 'Languages', 'Plugins']
        for f in key_fields:
            if f in result:
                print(f'  {f}: {result[f][:80]}')
        print(f'  总字段数: {len(result)}')
        await page.screenshot(path=f'{SCREENSHOT_DIR}/browserleaks_js.png', full_page=True)
        return {'site': 'browserleaks', 'fields': len(result), 'details': {k: result[k] for k in key_fields if k in result}}


async def test_creepjs():
    """creepjs - 综合信任评分（需较长等待时间）"""
    print('\n' + '='*60)
    print('[4/4] abrahamjuliot.github.io/creepjs')
    async with make_browser() as browser:
        page = await browser.new_page()
        await page.goto('https://abrahamjuliot.github.io/creepjs/', timeout=40000, wait_until='domcontentloaded')
        await asyncio.sleep(18)  # creepjs需要较长时间运行
        # 提取信任分数
        score = await page.evaluate(
            "() => { "
            "const scoreEl = document.querySelector('#creep-score,[class*=trust],[id*=score]'); "
            "const likelyBot = document.querySelector('[class*=bot],[class*=likely]'); "
            "const summary = document.querySelector('#fingerprint-data,.visitor-info'); "
            "return { "
            "  score: scoreEl ? scoreEl.innerText.trim().slice(0,100) : 'not found', "
            "  bot: likelyBot ? likelyBot.innerText.trim().slice(0,100) : 'not found', "
            "  bodyStart: document.body.innerText.slice(0,600) "
            "}; }"
        )
        print(f'  Score元素: {score["score"]}')
        print(f'  Bot元素: {score["bot"]}')
        print(f'  页面摘要:\n{score["bodyStart"][:400]}')
        await page.screenshot(path=f'{SCREENSHOT_DIR}/creepjs.png', full_page=True)
        return {'site': 'creepjs', 'score': score}


async def main():
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    print('开始多站点反检测测试')
    print(f'代理: {PROXY["server"]}')
    print(f'截图目录: {SCREENSHOT_DIR}/')

    results = []
    for test_fn in [test_sannysoft, test_pixelscan, test_browserleaks, test_creepjs]:
        try:
            r = await test_fn()
            results.append(r)
        except Exception as e:
            print(f'  [ERROR] {e}')

    print('\n' + '='*60)
    print('测试完成！截图保存在:', SCREENSHOT_DIR)
    print('\n汇总:')
    for r in results:
        site = r.get('site', '?')
        if 'passed' in r:
            print(f'  {site}: {r["passed"]}通过 / {r["failed"]}未通过')
        else:
            print(f'  {site}: 已完成（见截图）')


if __name__ == '__main__':
    asyncio.run(main())
