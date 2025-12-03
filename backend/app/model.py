"""
模型加载与打分接口。
包含：
- IsolationForest（基于传统特征的一类模型）
- PhishMMF-RF / PhishMMF-XGB（基于多模态 228 维特征的监督模型）
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple

import joblib
import numpy as np

# 约定：模型位于 backend/models 下
# 使用绝对路径，确保从任何位置运行都能找到模型
_BASE_DIR = Path(__file__).parent.parent  # backend/app -> backend
_MODELS_DIR = _BASE_DIR / "models"
_IFOREST_PATH = _MODELS_DIR / "phish_iforest.joblib"
_IFOREST_SCALER_PATH = _MODELS_DIR / "phish_iforest_scaler.joblib"
_PHISHMMF_RF_PATH = _MODELS_DIR / "phishmmf_rf.joblib"
_PHISHMMF_XGB_PATH = _MODELS_DIR / "phishmmf_xgb.joblib"
_PHISHMMF_SCALER_PATH = _MODELS_DIR / "phishmmf_scaler.joblib"
_PHISHMMF_SIMPLIFIED_RF_PATH = _MODELS_DIR / "phishmmf_simplified_rf.joblib"
_PHISHMMF_SIMPLIFIED_XGB_PATH = _MODELS_DIR / "phishmmf_simplified_xgb.joblib"
_PHISHMMF_SIMPLIFIED_SCALER_PATH = _MODELS_DIR / "phishmmf_simplified_scaler.joblib"

_iforest_model = None
_iforest_scaler = None
_phishmmf_rf = None
_phishmmf_xgb = None
_phishmmf_scaler = None
_phishmmf_simplified_rf = None
_phishmmf_simplified_xgb = None
_phishmmf_simplified_scaler = None


def _load_iforest():
    global _iforest_model, _iforest_scaler
    if _iforest_model is not None:
        return _iforest_model, _iforest_scaler
    
    if _IFOREST_PATH.exists():
        _iforest_model = joblib.load(_IFOREST_PATH)
        # 尝试加载标准化器（如果存在）
        if _IFOREST_SCALER_PATH.exists():
            _iforest_scaler = joblib.load(_IFOREST_SCALER_PATH)
        else:
            _iforest_scaler = None
    else:
        _iforest_model = None
        _iforest_scaler = None
    
    return _iforest_model, _iforest_scaler


def _load_phishmmf_scaler():
    global _phishmmf_scaler
    if _phishmmf_scaler is not None:
        return _phishmmf_scaler
    if _PHISHMMF_SCALER_PATH.exists():
        _phishmmf_scaler = joblib.load(_PHISHMMF_SCALER_PATH)
    else:
        _phishmmf_scaler = None
    return _phishmmf_scaler


def _load_phishmmf_rf():
    global _phishmmf_rf
    if _phishmmf_rf is not None:
        return _phishmmf_rf
    if _PHISHMMF_RF_PATH.exists():
        _phishmmf_rf = joblib.load(_PHISHMMF_RF_PATH)
    else:
        _phishmmf_rf = None
    return _phishmmf_rf


def _load_phishmmf_xgb():
    global _phishmmf_xgb
    if _phishmmf_xgb is not None:
        return _phishmmf_xgb
    if _PHISHMMF_XGB_PATH.exists():
        _phishmmf_xgb = joblib.load(_PHISHMMF_XGB_PATH)
    else:
        _phishmmf_xgb = None
    return _phishmmf_xgb


def _load_phishmmf_simplified_scaler():
    global _phishmmf_simplified_scaler
    if _phishmmf_simplified_scaler is not None:
        return _phishmmf_simplified_scaler
    if _PHISHMMF_SIMPLIFIED_SCALER_PATH.exists():
        _phishmmf_simplified_scaler = joblib.load(_PHISHMMF_SIMPLIFIED_SCALER_PATH)
    else:
        _phishmmf_simplified_scaler = None
    return _phishmmf_simplified_scaler


def _load_phishmmf_simplified_rf():
    global _phishmmf_simplified_rf
    if _phishmmf_simplified_rf is not None:
        return _phishmmf_simplified_rf
    if _PHISHMMF_SIMPLIFIED_RF_PATH.exists():
        _phishmmf_simplified_rf = joblib.load(_PHISHMMF_SIMPLIFIED_RF_PATH)
    else:
        _phishmmf_simplified_rf = None
    return _phishmmf_simplified_rf


def _load_phishmmf_simplified_xgb():
    global _phishmmf_simplified_xgb
    if _phishmmf_simplified_xgb is not None:
        return _phishmmf_simplified_xgb
    if _PHISHMMF_SIMPLIFIED_XGB_PATH.exists():
        _phishmmf_simplified_xgb = joblib.load(_PHISHMMF_SIMPLIFIED_XGB_PATH)
    else:
        _phishmmf_simplified_xgb = None
    return _phishmmf_simplified_xgb


def iforest_available() -> bool:
    model, _ = _load_iforest()
    return model is not None


def phishmmf_models_available() -> Tuple[bool, bool]:
    """
    返回 (rf_available, xgb_available)
    """
    return _load_phishmmf_rf() is not None, _load_phishmmf_xgb() is not None


def phishmmf_simplified_models_available() -> Tuple[bool, bool]:
    """
    返回简化模型的可用性 (rf_available, xgb_available)
    """
    return _load_phishmmf_simplified_rf() is not None, _load_phishmmf_simplified_xgb() is not None


def score_with_iforest(feature_vector: List[float]) -> Optional[float]:
    """
    使用 IsolationForest 对邮件进行打分：
    - decision_function 值越小越“异常”（更像钓鱼）
    - 将其归一化到 [0, 1] 并反转，使得数值越大表示越像钓鱼
    """
    clf, scaler = _load_iforest()
    if clf is None:
        return None

    X = np.array(feature_vector, dtype=float).reshape(1, -1)
    
    # 如果有标准化器，先标准化特征
    if scaler is not None:
        try:
            X = scaler.transform(X)
        except Exception as e:
            print(f"特征标准化失败: {e}")
            # 如果标准化失败，继续使用原始特征
    
    df = float(clf.decision_function(X)[0])

    df_clipped = max(min(df, 0.5), -0.5)
    normalized = (df_clipped + 0.5) / 1.0  # -> [0,1] 正常高，异常低
    phishing_score = 1.0 - normalized
    return float(phishing_score)


def score_with_phishmmf_rf(features_228: List[float]) -> Optional[float]:
    """
    使用 PhishMMF-RF 模型对 228 维特征向量打分，返回钓鱼概率。
    """
    clf = _load_phishmmf_rf()
    scaler = _load_phishmmf_scaler()
    if clf is None:
        return None
    
    X = np.array(features_228, dtype=float).reshape(1, -1)
    
    # 应用特征标准化（重要！）
    if scaler is not None:
        X = scaler.transform(X)
    
    proba = float(clf.predict_proba(X)[0, 1])
    return proba


def score_with_phishmmf_xgb(features_228: List[float]) -> Optional[float]:
    """
    使用 PhishMMF-XGB 模型对 228 维特征向量打分，返回钓鱼概率。
    """
    clf = _load_phishmmf_xgb()
    scaler = _load_phishmmf_scaler()
    if clf is None:
        return None
    
    X = np.array(features_228, dtype=float).reshape(1, -1)
    
    # 应用特征标准化（重要！）
    if scaler is not None:
        X = scaler.transform(X)
    
    proba = float(clf.predict_proba(X)[0, 1])
    return proba




def score_with_phishmmf_simplified_rf(features_35: List[float]) -> Optional[float]:
    """
    使用简化 PhishMMF-RF 模型对 35 维特征向量打分，返回钓鱼概率。
    注意：模型输出取反（1 - 原始输出），因为训练时标签可能相反。
    """
    clf = _load_phishmmf_simplified_rf()
    scaler = _load_phishmmf_simplified_scaler()
    if clf is None:
        return None
    
    X = np.array(features_35, dtype=float).reshape(1, -1)
    
    # 应用特征标准化
    if scaler is not None:
        X = scaler.transform(X)
    
    # 获取类别1的概率，然后取反
    proba = float(clf.predict_proba(X)[0, 1])
    return 1.0 - proba  # 取反


def score_with_phishmmf_simplified_xgb(features_35: List[float]) -> Optional[float]:
    """
    使用简化 PhishMMF-XGB 模型对 35 维特征向量打分，返回钓鱼概率。
    注意：模型输出取反（1 - 原始输出），因为训练时标签可能相反。
    """
    clf = _load_phishmmf_simplified_xgb()
    scaler = _load_phishmmf_simplified_scaler()
    if clf is None:
        return None
    
    X = np.array(features_35, dtype=float).reshape(1, -1)
    
    # 应用特征标准化
    if scaler is not None:
        X = scaler.transform(X)
    
    # 获取类别1的概率，然后取反
    proba = float(clf.predict_proba(X)[0, 1])
    return 1.0 - proba  # 取反
