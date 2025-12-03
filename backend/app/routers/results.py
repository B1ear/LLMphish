from fastapi import APIRouter, HTTPException

from app.storage import store

router = APIRouter()


@router.get("/{email_id}")
async def get_detection_result(email_id: str):
    """
    结果展示接口
    - 从存储中读取最近一次检测结果
    """
    result = store.get_result(email_id)
    if not result:
        raise HTTPException(status_code=404, detail="尚未对该邮件执行检测")
    return result


