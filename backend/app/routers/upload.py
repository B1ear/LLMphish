from fastapi import APIRouter, UploadFile, File, HTTPException

from app.storage import store

router = APIRouter()


@router.post("/")
async def upload_email(file: UploadFile = File(...)):
    """
    邮件上传接口
    - 接收原始邮件文件（EML/文本等）
    - 将内容与基础元数据写入内存存储
    - 返回 email_id，供后续特征提取/检测使用
    """
    raw_bytes = await file.read()
    size = len(raw_bytes)
    try:
        content = raw_bytes.decode("utf-8", errors="ignore")
    except Exception:  # pragma: no cover - 防御性代码
        content = ""

    meta = {
        "filename": file.filename,
        "content_type": file.content_type,
        "size": size,
    }
    email_id = store.save_email(content=content, meta=meta)

    return {
        "email_id": email_id,
        "message": "上传成功",
        "meta": meta,
    }


@router.get("/{email_id}")
async def get_email(email_id: str):
    """
    获取邮件内容接口
    - 返回邮件原始内容和元数据
    - 供前端显示和截图使用
    """
    email = store.get_email(email_id)
    if not email:
        raise HTTPException(status_code=404, detail="email_id 不存在")
    
    return {
        "email_id": email_id,
        "content": email.get("content", ""),
        "meta": email.get("meta", {}),
    }


@router.post("/screenshot/{email_id}")
async def upload_screenshot(email_id: str, file: UploadFile = File(...)):
    """
    上传邮件截图接口
    - 接收前端截取的邮件/网页截图（PNG/JPEG）
    - 保存截图数据，供后续图像特征提取使用
    """
    if not store.get_email(email_id):
        raise HTTPException(status_code=404, detail="email_id 不存在")
    
    image_bytes = await file.read()
    
    # 简单验证：检查是否为图像格式
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="文件必须是图像格式（PNG/JPEG）")
    
    store.save_screenshot(email_id, image_bytes)
    
    return {
        "email_id": email_id,
        "message": "截图上传成功",
        "size": len(image_bytes),
        "content_type": file.content_type,
    }


@router.post("/screenshot/auto/{email_id}")
async def auto_capture_url_screenshot(email_id: str):
    """
    自动截图接口：从邮件中提取 URL，访问并截图。
    - 自动从邮件内容中提取所有 URL
    - 使用无头浏览器访问第一个可访问的 URL 并截图
    - 保存截图数据，供后续图像特征提取使用
    """
    email = store.get_email(email_id)
    if not email:
        raise HTTPException(status_code=404, detail="email_id 不存在")
    
    content = email.get("content", "")
    
    from app.url_screenshot import capture_email_urls_screenshot, extract_urls_from_email
    
    urls = extract_urls_from_email(content)
    if not urls:
        raise HTTPException(status_code=400, detail="邮件中未找到 URL")
    
    # 访问 URL 并截图
    screenshot_bytes = await capture_email_urls_screenshot(content, max_urls=3)
    
    if not screenshot_bytes:
        raise HTTPException(
            status_code=503,
            detail=f"无法访问邮件中的 URL 并截图。已尝试的 URL: {urls[:3]}。请确保 Playwright 已正确安装（运行 'playwright install chromium'）"
        )
    
    store.save_screenshot(email_id, screenshot_bytes)
    
    return {
        "email_id": email_id,
        "message": "自动截图成功",
        "size": len(screenshot_bytes),
        "urls_found": urls,
        "urls_tried": urls[:3],
    }


