"""
使用可提取特征重新训练 PhishMMF 模型。

只使用我们可以从邮件中直接提取的 35 个特征：
- 文本特征：主题 (6) + 发件人 (2) + 正文 (16)
- URL 基础特征 (11)

总计：35 维特征
"""

import json
import numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
import joblib


def extract_simplified_features(data: dict) -> list:
    """
    从 JSON 数据中提取可获取的 35 维特征
    """
    features = []
    
    # 1. 文本特征 - 主题 (6维)
    subject = data.get("text_features", {}).get("subject", {})
    urgency_map = {"Low": 0, "Moderate": 1, "High": 2, "unknown": 0, "Ne": 0}
    features.append(urgency_map.get(subject.get("urgency_level", "unknown"), 0))
    features.append(int(subject.get("contains_threatening_language", False)))
    features.append(int(subject.get("contains_seductive_language", False)))
    features.append(int(subject.get("contains_emergency_action_request", False)))
    features.append(float(subject.get("sentiment_score", 0.0)))
    sentiment_map = {"Negative": 0, "Neutral": 1, "Positive": 2}
    features.append(sentiment_map.get(subject.get("sentiment_label", "Neutral"), 1))
    
    # 2. 文本特征 - 发件人 (2维)
    sender = data.get("text_features", {}).get("sender", {})
    impersonation_map = {
        "unknown": 0, "None": 0, "Bank": 1, "Government": 2, 
        "E-commerce": 3, "Social Media": 4
    }
    features.append(impersonation_map.get(sender.get("impersonation_type", "unknown"), 0))
    anomaly_map = {
        "unknown": 0, "None": 0, "Non-official domain": 1, 
        "Spelling error": 2, "Suspicious": 1
    }
    features.append(anomaly_map.get(sender.get("email_address_anomalies", "unknown"), 0))
    
    # 3. 文本特征 - 正文 (16维)
    content = data.get("text_features", {}).get("content", {})
    features.append(int(content.get("word_count", 0)))
    features.append(int(content.get("url_count", 0)))
    features.append(int(content.get("spelling_errors", 0)))
    features.append(int(content.get("grammar_errors", 0)))
    features.append(len(content.get("suspicious_keywords", [])))
    features.append(int(content.get("urgency_words_count", 0)))
    features.append(int(content.get("contains_personal_information_request", False)))
    features.append(int(content.get("contains_abnormal_financial_request", False)))
    features.append(float(content.get("text_complexity", 0.0)))
    features.append(float(content.get("text_similarity_to_legitimate_emails", 0.0)))
    lang_map = {"en": 0, "zh": 1, "mixed": 2, "unknown": 0}
    features.append(lang_map.get(content.get("language", "en"), 0))
    features.append(int(content.get("contains_obfuscated_text", False)))
    features.append(int(content.get("requests_otp_or_mfa", False)))
    features.append(int(content.get("contains_phishing_call_to_action", False)))
    sentiment_map2 = {"Negative": 0, "Neutral": 1, "Positive": 2}
    features.append(sentiment_map2.get(content.get("text_sentiment", "Neutral"), 1))
    features.append(float(content.get("text_sentiment_score", 0.0)))
    
    # 4. URL 基础特征 (11维)
    url_basic = data.get("url_intelligence_features", {}).get("basic", {})
    features.append(int(url_basic.get("domain_length", 0)))
    features.append(int(url_basic.get("dot_count", 0)))
    features.append(int(url_basic.get("contains_ip_address", False)))
    features.append(int(url_basic.get("contains_at_symbol", False)))
    features.append(int(url_basic.get("contains_hyphen", False)))
    features.append(int(url_basic.get("path_length", 0)))
    features.append(int(url_basic.get("subdomains_count", 0)))
    tld_map = {"com": 0, "org": 1, "net": 2, "edu": 3, "gov": 4, "other": 5, "unknown": 5}
    tld = url_basic.get("tld", "unknown")
    if tld not in tld_map:
        tld = "other"
    features.append(tld_map.get(tld, 5))
    features.append(int(url_basic.get("query_params_count", 0)))
    features.append(int(url_basic.get("has_suspicious_query_params", False)))
    features.append(len(url_basic.get("suspicious_query_params", [])))
    
    return features


def load_data():
    """加载 PhishMMF 数据"""
    jsonl_path = Path("PhishMMF-main/all/all.jsonl")
    labels_path = Path("PhishMMF-main/email_phishing_labels.npy")
    
    if not jsonl_path.exists():
        print(f"❌ 文件不存在: {jsonl_path}")
        return None, None
    
    if not labels_path.exists():
        print(f"❌ 文件不存在: {labels_path}")
        return None, None
    
    print("📂 加载数据...")
    
    # 加载标签
    labels = np.load(labels_path)
    print(f"  标签数量: {len(labels)}")
    print(f"  钓鱼邮件: {np.sum(labels == 1)} ({np.sum(labels == 1)/len(labels)*100:.1f}%)")
    print(f"  正常邮件: {np.sum(labels == 0)} ({np.sum(labels == 0)/len(labels)*100:.1f}%)")
    
    # 加载特征
    features_list = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i % 1000 == 0:
                print(f"  处理中: {i}/{len(labels)}", end='\r')
            
            line = line.strip()
            if not line:  # 跳过空行
                continue
            
            try:
                data = json.loads(line)
                features = extract_simplified_features(data)
                features_list.append(features)
            except json.JSONDecodeError as e:
                print(f"\n⚠️  JSON解析错误 (行 {i}): {e}")
                continue
    
    print(f"  处理完成: {len(features_list)}/{len(labels)}")
    
    X = np.array(features_list, dtype=float)
    y = labels
    
    print(f"\n✅ 数据加载完成:")
    print(f"  特征矩阵: {X.shape}")
    print(f"  标签向量: {y.shape}")
    print(f"  特征范围: [{X.min():.2f}, {X.max():.2f}]")
    print(f"  特征均值: {X.mean():.4f}")
    print(f"  特征标准差: {X.std():.4f}")
    
    return X, y


def train_models(X, y):
    """训练简化模型"""
    print("\n" + "="*70)
    print("🎯 训练简化 PhishMMF 模型")
    print("="*70)
    
    # 划分训练集和测试集
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"\n📊 数据划分:")
    print(f"  训练集: {X_train.shape[0]} 样本")
    print(f"  测试集: {X_test.shape[0]} 样本")
    
    # 特征标准化
    print(f"\n🔧 特征标准化...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    print(f"  标准化后范围: [{X_train_scaled.min():.2f}, {X_train_scaled.max():.2f}]")
    print(f"  标准化后均值: {X_train_scaled.mean():.4f}")
    print(f"  标准化后标准差: {X_train_scaled.std():.4f}")
    
    # 训练 RandomForest
    print(f"\n🌲 训练 RandomForest...")
    rf = RandomForestClassifier(
        n_estimators=100,
        max_depth=20,
        min_samples_split=10,
        min_samples_leaf=5,
        random_state=42,
        n_jobs=-1,
        verbose=1
    )
    rf.fit(X_train_scaled, y_train)
    
    # 评估 RandomForest
    print(f"\n📊 RandomForest 评估:")
    y_pred_rf = rf.predict(X_test_scaled)
    y_proba_rf = rf.predict_proba(X_test_scaled)[:, 1]
    
    print(f"\n分类报告:")
    print(classification_report(y_test, y_pred_rf, target_names=["正常", "钓鱼"]))
    
    print(f"混淆矩阵:")
    cm = confusion_matrix(y_test, y_pred_rf)
    print(f"  TN={cm[0,0]}, FP={cm[0,1]}")
    print(f"  FN={cm[1,0]}, TP={cm[1,1]}")
    
    auc_rf = roc_auc_score(y_test, y_proba_rf)
    print(f"AUC-ROC: {auc_rf:.4f}")
    
    # 交叉验证
    cv_scores_rf = cross_val_score(rf, X_train_scaled, y_train, cv=5, scoring='roc_auc', n_jobs=-1)
    print(f"交叉验证 AUC: {cv_scores_rf.mean():.4f} ± {cv_scores_rf.std():.4f}")
    
    # 训练 XGBoost
    print(f"\n🚀 训练 XGBoost...")
    xgb = XGBClassifier(
        n_estimators=100,
        max_depth=10,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1,
        verbosity=1
    )
    xgb.fit(X_train_scaled, y_train)
    
    # 评估 XGBoost
    print(f"\n📊 XGBoost 评估:")
    y_pred_xgb = xgb.predict(X_test_scaled)
    y_proba_xgb = xgb.predict_proba(X_test_scaled)[:, 1]
    
    print(f"\n分类报告:")
    print(classification_report(y_test, y_pred_xgb, target_names=["正常", "钓鱼"]))
    
    print(f"混淆矩阵:")
    cm = confusion_matrix(y_test, y_pred_xgb)
    print(f"  TN={cm[0,0]}, FP={cm[0,1]}")
    print(f"  FN={cm[1,0]}, TP={cm[1,1]}")
    
    auc_xgb = roc_auc_score(y_test, y_proba_xgb)
    print(f"AUC-ROC: {auc_xgb:.4f}")
    
    # 交叉验证
    cv_scores_xgb = cross_val_score(xgb, X_train_scaled, y_train, cv=5, scoring='roc_auc', n_jobs=-1)
    print(f"交叉验证 AUC: {cv_scores_xgb.mean():.4f} ± {cv_scores_xgb.std():.4f}")
    
    # 特征重要性
    print(f"\n📈 特征重要性 (Top 10):")
    feature_names = [
        "urgency_level", "threatening", "seductive", "emergency", "sentiment_score", "sentiment_label",
        "impersonation", "email_anomaly",
        "word_count", "url_count", "spelling_errors", "grammar_errors", "suspicious_keywords",
        "urgency_words", "personal_info_request", "financial_request", "text_complexity",
        "similarity_to_legit", "language", "obfuscated", "otp_request", "phishing_cta",
        "text_sentiment", "text_sentiment_score",
        "domain_length", "dot_count", "ip_address", "at_symbol", "hyphen",
        "path_length", "subdomains", "tld", "query_params", "suspicious_params", "suspicious_params_list"
    ]
    
    importances = rf.feature_importances_
    indices = np.argsort(importances)[::-1][:10]
    
    for i, idx in enumerate(indices, 1):
        print(f"  {i:2d}. {feature_names[idx]:25s}: {importances[idx]:.4f}")
    
    return rf, xgb, scaler


def save_models(rf, xgb, scaler):
    """保存模型"""
    print(f"\n💾 保存模型...")
    
    models_dir = Path("backend/models")
    models_dir.mkdir(exist_ok=True)
    
    # 保存模型
    joblib.dump(rf, models_dir / "phishmmf_simplified_rf.joblib")
    joblib.dump(xgb, models_dir / "phishmmf_simplified_xgb.joblib")
    joblib.dump(scaler, models_dir / "phishmmf_simplified_scaler.joblib")
    
    print(f"  ✅ RandomForest: {models_dir / 'phishmmf_simplified_rf.joblib'}")
    print(f"  ✅ XGBoost: {models_dir / 'phishmmf_simplified_xgb.joblib'}")
    print(f"  ✅ Scaler: {models_dir / 'phishmmf_simplified_scaler.joblib'}")


def main():
    print("🔍 简化 PhishMMF 模型训练")
    print("="*70)
    print("使用 35 个可提取特征:")
    print("  - 文本特征: 24 维 (主题 + 发件人 + 正文)")
    print("  - URL 基础特征: 11 维")
    print("="*70)
    
    # 加载数据
    X, y = load_data()
    if X is None or y is None:
        return
    
    # 训练模型
    rf, xgb, scaler = train_models(X, y)
    
    # 保存模型
    save_models(rf, xgb, scaler)
    
    print("\n" + "="*70)
    print("✅ 训练完成！")
    print("="*70)
    print("\n下一步:")
    print("1. 实现对应的特征提取代码 (backend/app/simplified_phishmmf_features.py)")
    print("2. 更新模型加载代码 (backend/app/model.py)")
    print("3. 测试简化模型效果")


if __name__ == "__main__":
    main()
