from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, conlist

from app.storage import store
from app.analysis import (
    extract_traditional_features,
    dummy_llm_semantic_features,
    analyze_email_semantics_async,
    simple_rule_based_detection,
    build_feature_vector,
)
from app.llm_service import llm_service, LLMProvider
from app.model import (
    iforest_available,
    score_with_iforest,
    phishmmf_simplified_models_available,
    score_with_phishmmf_simplified_rf,
    score_with_phishmmf_simplified_xgb,
)
from app.simplified_phishmmf_features import extract_simplified_phishmmf_features

router = APIRouter()


@router.post("/{email_id}")
async def detect_email(email_id: str):
    """
    恶意检测接口（集成LLM语义特征）
    当前实现：
    - 提取传统特征 & LLM 语义特征（使用 Qwen3/DeepSeek-V3）
    - 规则检测得到 rule_score
    - 如存在 ML 模型，则对特征向量进行打分 ml_score
    - LLM辅助检测（可选）
    - 综合多源结果得到最终 risk_score
    """
    email = store.get_email(email_id)
    if not email:
        raise HTTPException(status_code=404, detail="email_id 不存在或已过期")

    content: str = email.get("content", "")

    traditional = extract_traditional_features(content)
    
    # 使用真实LLM提取语义特征
    llm_feats = await analyze_email_semantics_async(content)
    
    # LLM辅助检测（可选）
    llm_detection = await llm_service.detect_phishing_with_llm(
        content,
        traditional,
        provider=LLMProvider.DASHSCOPE,
        fallback_provider=LLMProvider.DEEPSEEK
    )

    rule_result = simple_rule_based_detection(
        email_id=email_id,
        traditional_features=traditional,
        llm_features=llm_feats,
    )

    rule_score = float(rule_result["risk_score"])
    iforest_score = None
    phishmmf_rf_score = None
    phishmmf_xgb_score = None

    # IsolationForest 模型
    if iforest_available():
        vec = build_feature_vector(traditional)
        iforest_score = score_with_iforest(vec)

    # 简化 PhishMMF 模型（RF 和 XGBoost）- 使用 35 维可提取特征
    rf_available, xgb_available = phishmmf_simplified_models_available()
    if rf_available or xgb_available:
        try:
            # 提取简化 PhishMMF 35 维特征（不需要截图和外部数据）
            features_35d = extract_simplified_phishmmf_features(content)
            
            if rf_available:
                phishmmf_rf_score = score_with_phishmmf_simplified_rf(features_35d)
            if xgb_available:
                phishmmf_xgb_score = score_with_phishmmf_simplified_xgb(features_35d)
        except Exception as e:
            print(f"简化 PhishMMF 特征提取失败: {e}")

    # 综合评分：规则 + IsolationForest + PhishMMF + LLM
    scores = [rule_score]
    weights = [1.0]
    
    if iforest_score is not None:
        scores.append(iforest_score)
        weights.append(1.0)
    
    # 简化 PhishMMF 模型得分（96% 准确率，AUC 0.98+）
    if phishmmf_rf_score is not None:
        scores.append(phishmmf_rf_score)
        weights.append(1.5)  # 简化 PhishMMF 权重提高（性能优秀）
    
    if phishmmf_xgb_score is not None:
        scores.append(phishmmf_xgb_score)
        weights.append(1.5)  # 简化 PhishMMF 权重提高（性能优秀）
    
    # 如果LLM可用，加入LLM语义特征中的钓鱼意图得分
    if llm_feats.get("llm_supported") and llm_feats.get("phishing_intent_score", 0) > 0:
        llm_semantic_score = llm_feats["phishing_intent_score"]
        scores.append(llm_semantic_score)
        weights.append(1.5)  # LLM语义特征权重提高
    
    # 如果LLM检测可用，加入LLM检测结果
    if llm_detection.get("llm_supported") and llm_detection.get("risk_score", 0) > 0:
        llm_detection_score = llm_detection["risk_score"]
        scores.append(llm_detection_score)
        weights.append(1.8)  # LLM检测结果权重显著提高
    
    # 加权平均
    final_score = sum(s * w for s, w in zip(scores, weights)) / sum(weights) if weights else rule_score
    final_score = min(1.0, max(0.0, final_score))  # 限制在[0,1]范围

    # 根据最终分数重新确定标签
    if final_score >= 0.7:
        attack_type = "hybrid"
    elif final_score >= 0.4:
        attack_type = "traditional"
    elif final_score >= 0.25:
        attack_type = "llm_generated"
    else:
        attack_type = "benign"

    result = {
        "email_id": email_id,
        "is_phishing": attack_type != "benign",
        "attack_type": attack_type,
        "risk_score": round(final_score, 3),
        "rule_score": rule_score,
        "iforest_score": iforest_score,
        "phishmmf_rf_score": phishmmf_rf_score,
        "phishmmf_xgb_score": phishmmf_xgb_score,
        "llm_semantic_score": llm_feats.get("phishing_intent_score") if llm_feats.get("llm_supported") else None,
        "llm_detection_score": llm_detection.get("risk_score") if llm_detection.get("llm_supported") else None,
        "reasons": rule_result.get("reasons", []),
        "traditional_features": traditional,
        "llm_semantic_features": llm_feats,
        "llm_detection": llm_detection,
        "models_used": {
            "rule": True,
            "iforest": iforest_score is not None,
            "phishmmf_rf": phishmmf_rf_score is not None,
            "phishmmf_xgb": phishmmf_xgb_score is not None,
            "llm": llm_feats.get("llm_supported", False) or llm_detection.get("llm_supported", False),
        },
    }

    # 将检测结果写入存储，供 /api/results/{email_id} 使用
    store.save_result(email_id, result)
    return result


@router.post("/llm/{email_id}")
async def detect_email_with_llm(email_id: str):
    """
    使用 LLM 进行钓鱼邮件检测（纯LLM检测接口）。
    - 使用 Qwen3 (DashScope) 或 DeepSeek-V3 进行检测
    - 返回LLM的检测结果和推理过程
    """
    email = store.get_email(email_id)
    if not email:
        raise HTTPException(status_code=404, detail="email_id 不存在或已过期")

    content: str = email.get("content", "")
    traditional = extract_traditional_features(content)
    
    # LLM检测
    llm_detection = await llm_service.detect_phishing_with_llm(
        content,
        traditional,
        provider=LLMProvider.DASHSCOPE,
        fallback_provider=LLMProvider.DEEPSEEK
    )
    
    if not llm_detection.get("llm_supported"):
        raise HTTPException(
            status_code=503,
            detail="LLM服务不可用。请确保已设置环境变量 DASHSCOPE_API_KEY 或 DEEPSEEK_API_KEY"
        )
    
    return {
        "email_id": email_id,
        "is_phishing": llm_detection.get("is_phishing", False),
        "attack_type": llm_detection.get("attack_type", "benign"),
        "risk_score": round(llm_detection.get("risk_score", 0.0), 3),
        "reasoning": llm_detection.get("reasoning", ""),
        "provider": llm_detection.get("provider", "unknown"),
        "model": llm_detection.get("model", "unknown"),
    }


class PhishMMFFeatures(BaseModel):
    """
    简化 PhishMMF 特征输入：
    - features: 长度为 35 的特征向量（只使用可提取特征）
    """

    features: conlist(float, min_length=35, max_length=35)


@router.post("/phishmmf")
async def detect_with_phishmmf(payload: PhishMMFFeatures):
    """
    基于简化 PhishMMF 35 维特征的检测接口（手动提供特征向量）。
    - 使用 RF 与 XGBoost 两个监督模型对同一特征打分
    - 输出各自概率与简单均值融合
    - 准确率 96%，AUC 0.98+
    """
    rf_available, xgb_available = phishmmf_simplified_models_available()
    if not (rf_available or xgb_available):
        raise HTTPException(status_code=503, detail="简化 PhishMMF 模型尚未训练或未找到")

    feats = list(payload.features)

    rf_score = score_with_phishmmf_simplified_rf(feats) if rf_available else None
    xgb_score = score_with_phishmmf_simplified_xgb(feats) if xgb_available else None

    scores: List[float] = [s for s in [rf_score, xgb_score] if s is not None]
    final_score = float(sum(scores) / len(scores)) if scores else None

    if final_score is None:
        raise HTTPException(status_code=500, detail="无法计算综合得分")

    attack_type = "phishing" if final_score >= 0.5 else "benign"

    return {
        "attack_type": attack_type,
        "risk_score": round(final_score, 3),
        "rf_score": rf_score,
        "xgb_score": xgb_score,
        "models_used": {
            "rf": rf_available,
            "xgb": xgb_available,
        },
    }


@router.post("/phishmmf/{email_id}")
async def detect_email_with_phishmmf(email_id: str):
    """
    基于邮件ID自动提取简化 PhishMMF 35 维特征并使用模型检测。
    - 从存储中读取邮件内容
    - 自动提取 35 维可提取特征（不需要截图和外部数据）
    - 使用 RF 与 XGBoost 模型进行检测
    - 准确率 96%，AUC 0.98+
    """
    email = store.get_email(email_id)
    if not email:
        raise HTTPException(status_code=404, detail="email_id 不存在或已过期")

    content: str = email.get("content", "")
    
    # 提取 35 维简化特征（只使用可提取特征）
    features_35d = extract_simplified_phishmmf_features(content)
    
    rf_available, xgb_available = phishmmf_simplified_models_available()
    if not (rf_available or xgb_available):
        raise HTTPException(status_code=503, detail="简化 PhishMMF 模型尚未训练或未找到")

    rf_score = score_with_phishmmf_simplified_rf(features_35d) if rf_available else None
    xgb_score = score_with_phishmmf_simplified_xgb(features_35d) if xgb_available else None

    scores: List[float] = [s for s in [rf_score, xgb_score] if s is not None]
    final_score = float(sum(scores) / len(scores)) if scores else None

    if final_score is None:
        raise HTTPException(status_code=500, detail="无法计算综合得分")

    attack_type = "phishing" if final_score >= 0.5 else "benign"
    
    result = {
        "email_id": email_id,
        "attack_type": attack_type,
        "is_phishing": attack_type == "phishing",
        "risk_score": round(final_score, 3),
        "rf_score": rf_score,
        "xgb_score": xgb_score,
        "models_used": {
            "rf": rf_available,
            "xgb": xgb_available,
        },
        "feature_dimension": len(features_35d),
        "model_info": {
            "name": "简化 PhishMMF",
            "features": 35,
            "accuracy": "96%",
            "auc": "0.98+",
            "note": "只使用可提取特征，不依赖外部数据"
        },
    }
    
    # 保存结果
    store.save_result(email_id, result)
    return result

