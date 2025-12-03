"""
基于 PhishMMF 多模态特征数据集训练有监督二分类模型的脚本。

数据说明（来自用户）：
- email_phishing_feature_228d.npy: 11672 条样本，232 维，其中前 228 维为特征，后 4 维为各模态特征掩码
- email_phishing_labels.npy: 对应标签，钓鱼为 1，正常为 0
"""

from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier


def main() -> None:
    # 默认路径指向 PhishMMF-main，可按需修改为相对路径或环境变量
    base = Path(r"C:\Users\Zeus\Desktop\LLMPhish\PhishMMF-main")

    # 部分版本文件名为 email_phishing_features_228d.npy（features 复数），做兼容处理
    feat_path_plural = base / "email_phishing_features_228d.npy"
    feat_path_single = base / "email_phishing_feature_228d.npy"
    if feat_path_plural.exists():
        feat_path = feat_path_plural
    else:
        feat_path = feat_path_single

    label_path = base / "email_phishing_labels.npy"

    if not feat_path.exists() or not label_path.exists():
        print(f"找不到特征或标签文件：{feat_path} 或 {label_path}")
        return

    print("加载 PhishMMF 特征与标签...")
    X_all = np.load(feat_path)
    y_all = np.load(label_path)

    # 前 228 维为特征，后 4 维为模态掩码（如有需要也可以拼接使用）
    X_feat = X_all[:, :228]
    X_mask = X_all[:, 228:]  # 目前未显式使用，保留以便后续扩展

    print(f"样本数: {X_feat.shape[0]}, 特征维度: {X_feat.shape[1]}, 掩码维度: {X_mask.shape[1]}")

    X_train, X_test, y_train, y_test = train_test_split(
        X_feat,
        y_all,
        test_size=0.2,
        random_state=42,
        stratify=y_all,
    )

    # 特征标准化（重要！）
    print("对特征进行标准化...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    print(f"标准化后特征统计:")
    print(f"   - 训练集均值: {X_train_scaled.mean():.4f}")
    print(f"   - 训练集标准差: {X_train_scaled.std():.4f}")
    print(f"   - 训练集范围: [{X_train_scaled.min():.2f}, {X_train_scaled.max():.2f}]")

    print("\n开始训练 RandomForest 二分类模型...")
    rf_clf = RandomForestClassifier(
        n_estimators=400,
        max_depth=None,
        min_samples_leaf=2,
        n_jobs=-1,
        random_state=42,
    )
    rf_clf.fit(X_train_scaled, y_train)

    print("在验证集上评估 RandomForest 模型...")
    rf_pred = rf_clf.predict(X_test)
    rf_proba = rf_clf.predict_proba(X_test)[:, 1]
    rf_auc = roc_auc_score(y_test, rf_proba)
    print(f"[RandomForest] AUC: {rf_auc:.4f}")
    print("[RandomForest] 分类报告：")
    print(classification_report(y_test, rf_pred, digits=4))

    print("\n开始训练 XGBoost 二分类模型...")
    xgb_clf = XGBClassifier(
        n_estimators=400,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric="logloss",
        n_jobs=-1,
        random_state=42,
        tree_method="hist",
    )
    xgb_clf.fit(X_train, y_train)

    print("在验证集上评估 XGBoost 模型...")
    xgb_pred = xgb_clf.predict(X_test)
    xgb_proba = xgb_clf.predict_proba(X_test)[:, 1]
    xgb_auc = roc_auc_score(y_test, xgb_proba)
    print(f"[XGBoost] AUC: {xgb_auc:.4f}")
    print("[XGBoost] 分类报告：")
    print(classification_report(y_test, xgb_pred, digits=4))

    # 在 backend 目录下运行时，模型目录应为 backend/models
    models_dir = Path("models")
    models_dir.mkdir(parents=True, exist_ok=True)

    rf_path = models_dir / "phishmmf_rf.joblib"
    joblib.dump(rf_clf, rf_path)
    print(f"RandomForest 模型已保存到: {rf_path}")

    xgb_path = models_dir / "phishmmf_xgb.joblib"
    joblib.dump(xgb_clf, xgb_path)
    print(f"XGBoost 模型已保存到: {xgb_path}")


if __name__ == "__main__":
    main()


