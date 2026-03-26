#!/usr/bin/env python3
"""
悟空官网邀请码定时获取脚本
邀请码是图片形式，通过OCR识别提取
"""

import re
import subprocess
import sys
import os
import time
from datetime import datetime


def ensure_deps():
    """自动安装依赖"""
    deps = {
        "playwright": "playwright",
        "requests": "requests",
        "opencc": "opencc-python-reimplemented",
    }
    missing = []
    for module, package in deps.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(package)

    if missing:
        print(f"正在安装依赖: {', '.join(missing)} ...")
        subprocess.check_call(["pip3", "install"] + missing)

    # 检查playwright浏览器
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            p.chromium.launch(headless=True).close()
    except Exception:
        print("正在安装 chromium 浏览器 ...")
        subprocess.check_call(["python3", "-m", "playwright", "install", "chromium"])


ensure_deps()

from playwright.sync_api import sync_playwright  # noqa: E402
import requests as req  # noqa: E402

# 轮询间隔（秒），图片URL不变时不调OCR
POLL_INTERVAL = 60
URL = "https://www.dingtalk.com/wukong"




def extract_code_from_image(page) -> tuple[str | None, str | None]:
    """
    从页面中找到邀请码图片，多种方式提取
    返回 (邀请码文字, 图片URL)
    """
    selectors = [
        "img.wk-hero-invite-img",
        "img[alt*='邀请码']",
        "img[class*='invite']",
    ]

    img_url = None
    img_alt = None
    for sel in selectors:
        try:
            el = page.query_selector(sel)
            if el:
                img_url = el.get_attribute("src")
                img_alt = el.get_attribute("alt")
                if img_url:
                    break
        except Exception:
            continue

    if not img_url:
        return None, None

    # 方式1: 检查alt属性
    if img_alt and len(img_alt) > 1 and img_alt != "邀请码":
        print(f"  图片alt: {img_alt}")

    # 方式2: 检查图片URL中是否编码了邀请码信息
    print(f"  图片URL: {img_url}")

    # 方式3: 用Playwright截图邀请码区域，保存供查看
    try:
        el = page.query_selector("img.wk-hero-invite-img") or page.query_selector("img[alt*='邀请码']")
        if el:
            el.screenshot(path="wukong_invite_screenshot.png")
            print("  已截图保存: wukong_invite_screenshot.png")
    except Exception:
        pass

    # 方式4: 在线OCR识别图片
    code = ocr_from_url(img_url)
    if code:
        return code, img_url

    return None, img_url


# OCR结果缓存：{图片URL: 邀请码}
_ocr_cache = {}


def ocr_from_url(img_url: str) -> str | None:
    """用免费在线OCR API识别图片中的中文"""
    # 同一张图片只调一次API
    if img_url in _ocr_cache:
        return _ocr_cache[img_url]

    # 优先用截图（尺寸小，成功率高）
    if os.path.exists("wukong_invite_screenshot.png"):
        code = ocr_from_file("wukong_invite_screenshot.png")
        if code:
            _ocr_cache[img_url] = code
            return code

    # 回退：下载原图再OCR
    try:
        print("  正在下载原图...")
        resp = req.get(img_url, headers={"Referer": URL}, timeout=15)
        if resp.status_code == 200:
            tmp_path = "wukong_invite_download.png"
            with open(tmp_path, "wb") as f:
                f.write(resp.content)
            code = ocr_from_file(tmp_path)
            if code:
                _ocr_cache[img_url] = code
                return code
    except Exception as e:
        print(f"  原图OCR失败: {e}")

    return None


def ocr_from_file(filepath: str) -> str | None:
    """上传本地图片到在线OCR，带重试"""
    try:
        with open(filepath, "rb") as f:
            img_bytes = f.read()

        file_size_kb = len(img_bytes) / 1024
        print(f"  上传图片: {filepath} ({file_size_kb:.0f}KB)")

        if file_size_kb > 500:
            print("  图片较大，尝试压缩...")
            img_bytes = compress_image(img_bytes)
            print(f"  压缩后: {len(img_bytes)/1024:.0f}KB")

        # 每个Engine重试2次
        for engine in ["1", "2"]:
            for attempt in range(2):
                try:
                    if attempt > 0:
                        print(f"  Engine{engine} 重试第{attempt}次...")
                        time.sleep(3)

                    print(f"  调用OCR Engine{engine}...")
                    api_url = "https://api.ocr.space/parse/image"
                    payload = {
                        "apikey": "helloworld",
                        "language": "chs",
                        "OCREngine": engine,
                        "scale": "true",
                        "isTable": "false",
                    }
                    files = {"file": ("img.png", img_bytes, "image/png")}
                    resp = req.post(api_url, data=payload, files=files, timeout=30)

                    if resp.status_code == 200:
                        data = resp.json()
                        parsed = data.get("ParsedResults")
                        if parsed:
                            text = parsed[0].get("ParsedText", "").strip()
                            exit_code = parsed[0].get("FileParseExitCode", -1)
                            print(f"  Engine{engine} 返回(exit={exit_code}): '{text}'")
                            if text:
                                code = parse_invite_code(text)
                                if code:
                                    return code
                        else:
                            err = data.get("ErrorMessage", data.get("ErrorDetails", ""))
                            is_exit = data.get("IsErroredOnProcessing", False)
                            print(f"  Engine{engine} 无结果(err={is_exit}): {err}")
                    else:
                        print(f"  Engine{engine} HTTP {resp.status_code}")
                        if resp.status_code == 403:
                            print("  API被限流，等待10秒...")
                            time.sleep(10)
                except Exception as e:
                    print(f"  Engine{engine} 异常: {e}")

    except Exception as e:
        print(f"  文件OCR失败: {e}")

    return None



def compress_image(img_bytes: bytes) -> bytes:
    """压缩图片到500KB以内（纯Python，不依赖numpy）"""
    from PIL import Image
    import io
    img = Image.open(io.BytesIO(img_bytes))
    # 缩小到50%
    w, h = img.size
    img = img.resize((w // 2, h // 2))
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def parse_invite_code(text: str) -> str | None:
    """从OCR文本中提取邀请码"""
    # 1. 繁简转换
    text = t2s(text)

    # 2. OCR常见错误纠正
    ocr_fixes = {
        "業请到": "邀请码", "業请码": "邀请码", "業請到": "邀请码",
        "業請碼": "邀请码", "邀请到": "邀请码", "邀請碼": "邀请码",
        "邀請到": "邀请码", "遨请码": "邀请码", "遨请到": "邀请码",
        "邀请碼": "邀请码", "已领": "", "已領": "",
    }
    for wrong, right in ocr_fixes.items():
        text = text.replace(wrong, right)

    print(f"  纠错后: {text}")

    # 3. 提取邀请码
    patterns = [
        r'(?:当前)?邀请码[：:]\s*(.+?)(?:\s*限|\s*\d+|\n|$)',
        r'邀请码[：:]\s*(\S+)',
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            code = m.group(1).strip()
            # 去掉尾部可能的杂字
            code = re.sub(r'[已限完领領\s]+$', '', code)
            if code and len(code) >= 2:
                return code
    return None


def t2s(text: str) -> str:
    """繁体转简体"""
    try:
        import opencc
        converter = opencc.OpenCC("t2s")
        return converter.convert(text)
    except ImportError:
        # 没装opencc就用内置映射表处理常见字
        mapping = str.maketrans(
            "業請碼頂領開註冊體驗試書號據點擊獲個費連結網頁關閉確認輸選項設計劃動態鏈接庫運環境變數據處標準備記錄導區塊鏈節點監測試驗證書號碼頭像顯示區域範圍內容許可權限製作業務場景觀測試運營銷售後臺賬戶頭條評論區塊鏈節點監測試驗證書號碼頭像顯示區域範圍內容許可權限製作業務場景觀測試運營銷售後臺賬戶頭條評論",
            "业请码顶领开注册体验试书号据点击获个费连结网页关闭确认输选项设计划动态链接库运环境变数据处标准备记录导区块链节点监测试验证书号码头像显示区域范围内容许可权限制作业务场景观测试运营销售后台账户头条评论区块链节点监测试验证书号码头像显示区域范围内容许可权限制作业务场景观测试运营销售后台账户头条评论",
        )
        return text.translate(mapping)


def extract_code_from_text(page) -> str | None:
    """回退方案：从页面文本提取"""
    try:
        text = page.inner_text("body")
        for line in text.split("\n"):
            if "当前邀请码" in line:
                m = re.search(r'当前邀请码[：:]\s*(.+)', line.strip())
                if m:
                    return m.group(1).strip()
    except Exception:
        pass
    return None


def extract_code(page) -> tuple[str | None, str | None]:
    """提取邀请码，优先图片OCR，回退文本"""
    code, img_url = extract_code_from_image(page)
    if code:
        return code, img_url

    # 回退到文本提取
    text_code = extract_code_from_text(page)
    return text_code, img_url


def run():
    last_code = None
    last_img_url = None
    check_count = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print(f"正在打开悟空官网: {URL}")
        page.goto(URL, wait_until="networkidle", timeout=30000)

        # 等待邀请码图片出现
        print("等待邀请码图片加载...")
        try:
            page.wait_for_selector(
                "img.wk-hero-invite-img, img[alt*='邀请码']",
                timeout=60000,
            )
            page.wait_for_timeout(2000)
            print("检测到邀请码图片")
        except Exception:
            print("未检测到邀请码图片，继续轮询...")

        print(f"开始定时获取邀请码（每 {POLL_INTERVAL} 秒）\n")

        try:
            while True:
                check_count += 1
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                code, img_url = extract_code(page)

                if code:
                    if code != last_code:
                        print("=" * 50)
                        print(f"🐵 [{now}] 当前邀请码: {code}")
                        if last_code:
                            print(f"   ⚡ 邀请码已更新！上一个: {last_code}")
                        if img_url and img_url != last_img_url:
                            print(f"   🖼️  图片: {img_url}")
                        print("=" * 50)
                        last_code = code
                        last_img_url = img_url
                    else:
                        print(f"[{now}] 第{check_count}次 | 邀请码: {code}（未变化）")
                else:
                    if img_url:
                        # 有图片但OCR失败，直接输出图片URL让用户看
                        if img_url != last_img_url:
                            print("=" * 50)
                            print(f"🖼️  [{now}] OCR未识别，邀请码图片已更新:")
                            print(f"   {img_url}")
                            print("=" * 50)
                            last_img_url = img_url
                        else:
                            print(f"[{now}] 第{check_count}次 | OCR未识别，图片未变化")
                    else:
                        print(f"[{now}] 第{check_count}次 | 未检测到邀请码")

                time.sleep(POLL_INTERVAL)

                # 刷新页面
                try:
                    page.reload(wait_until="networkidle", timeout=30000)
                    page.wait_for_selector(
                        "img.wk-hero-invite-img, img[alt*='邀请码']",
                        timeout=15000,
                    )
                    page.wait_for_timeout(1000)
                except Exception:
                    pass

        except KeyboardInterrupt:
            print("\n已停止监控")
        finally:
            browser.close()


if __name__ == "__main__":
    run()
