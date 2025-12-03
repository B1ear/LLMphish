"""
URL 网页截图功能模块。
使用 Playwright 无头浏览器访问邮件中的 URL 并截图。
"""

from __future__ import annotations

import asyncio
from typing import Optional
from io import BytesIO

try:
    from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeoutError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

from app.analysis import URL_PATTERN


_browser: Optional[Browser] = None


async def _get_browser() -> Optional[Browser]:
    """获取或创建浏览器实例（单例模式）"""
    global _browser
    if not PLAYWRIGHT_AVAILABLE:
        return None
    
    if _browser is None:
        try:
            playwright = await async_playwright().start()
            _browser = await playwright.chromium.launch(headless=True)
        except Exception as e:
            print(f"无法启动 Playwright 浏览器: {e}")
            print("提示: 请运行 'playwright install chromium' 安装浏览器")
            return None
    
    return _browser


async def capture_url_screenshot(url: str, timeout: int = 30000) -> Optional[bytes]:
    """
    访问指定 URL 并截图。
    
    Args:
        url: 要访问的 URL
        timeout: 超时时间（毫秒），默认 30 秒
    
    Returns:
        截图图像的字节数据，失败时返回 None
    """
    browser = await _get_browser()
    if not browser:
        return None
    
    try:
        # 创建新页面
        page = await browser.new_page()
        
        # 设置视口大小（常见网页尺寸）
        await page.set_viewport_size({"width": 1920, "height": 1080})
        
        # 访问 URL（带超时）
        await page.goto(url, wait_until="networkidle", timeout=timeout)
        
        # 等待页面加载完成（额外等待 2 秒）
        await asyncio.sleep(2)
        
        # 截图
        screenshot_bytes = await page.screenshot(full_page=True, type="png")
        
        await page.close()
        return screenshot_bytes
    
    except PlaywrightTimeoutError:
        print(f"访问 URL 超时: {url}")
        return None
    except Exception as e:
        print(f"截图失败 {url}: {e}")
        return None


def extract_urls_from_email(content: str) -> list[str]:
    """
    从邮件内容中提取所有 URL。
    
    Returns:
        URL 列表
    """
    urls = URL_PATTERN.findall(content)
    # 去重并清理
    unique_urls = list(set(urls))
    # 移除末尾可能的标点符号
    cleaned_urls = []
    for url in unique_urls:
        # 移除末尾的常见标点
        url = url.rstrip('.,;!?)>"')
        if url.startswith(('http://', 'https://')):
            cleaned_urls.append(url)
    return cleaned_urls


async def capture_email_urls_screenshot(content: str, max_urls: int = 3) -> Optional[bytes]:
    """
    从邮件内容中提取 URL，访问第一个可访问的 URL 并截图。
    
    Args:
        content: 邮件内容
        max_urls: 最多尝试的 URL 数量
    
    Returns:
        第一个成功截图的图像字节数据，失败时返回 None
    """
    urls = extract_urls_from_email(content)
    
    if not urls:
        return None
    
    # 尝试访问前几个 URL，直到成功
    for url in urls[:max_urls]:
        screenshot = await capture_url_screenshot(url)
        if screenshot:
            return screenshot
    
    return None

