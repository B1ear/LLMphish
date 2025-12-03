from fastapi import APIRouter, HTTPException

from app.storage import store
from app.analysis import (
    extract_traditional_features,
    dummy_llm_semantic_features,
    analyze_email_semantics_async,
)

router = APIRouter()


@router.get("/{email_id}")
async def extract_features(email_id: str):
    """
    特征提取接口（集成LLM语义特征）
    - 从存储中取回邮件内容
    - 提取传统特征（行数、长度、URL、可疑关键词等）
    - 使用 LLM (Qwen3/DeepSeek-V3) 提取语义特征
    """
    email = store.get_email(email_id)
    if not email:
        raise HTTPException(status_code=404, detail="email_id 不存在或已过期")

    content: str = email.get("content", "")

    traditional = extract_traditional_features(content)
    
    # 使用真实LLM提取语义特征
    llm_feats = await analyze_email_semantics_async(content)

    return {
        "email_id": email_id,
        "traditional_features": traditional,
        "llm_semantic_features": llm_feats,
    }


