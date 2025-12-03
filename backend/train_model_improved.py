"""
改进的 IsolationForest 训练脚本

主要改进：
1. 使用针对钓鱼邮件优化的特征（中文关键词、base64、伪造发件人等）
2. 更好的数据预处理
3. 保存特征统计信息用于分析
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from app.analysis import extract_traditional_features, build_feature_vector


def load_emails_from_dir(data_dir: str) -> List[str]:
    """从目录加载所有.eml文件"""
    base = Path(data_dir)
    contents: List[str] = []
    
    print(f"正在从 {data_dir} 加载邮件...")
    for p in base.glob("*.eml"):
        try:
            raw = p.read_bytes()
            text = raw.decode("utf-8", errors="ignore")
            contents.append(text)
        except Exception as e:
            print(f"  跳过文件 {p.name}: {e}")
            continue
    
    return contents


def analyze_feature_statistics(X: np.ndarray, feature_names: List[str]) -> Dict[str, Any]:
    """分析特征统计信息"""
    stats = {}
    for i, name in enumerate(feature_names):
        col = X[:, i]
        stats[name] = {
            "mean": float(np.mean(col)),
            "std": float(np.std(col)),
            "min": float(np.min(col)),
            "max": float(np.max(col)),
            "median": float(np.median(col)),
        }
    return stats


def main():
    # 训练数据目录：包含钓鱼邮件
    data_dir = os.environ.get(
        "LLMPHISH_TRAIN_DIR",
        r"..\datacon2023-spoof-email-main",
    )
    
    if not Path(data_dir).exists():
        print(f"错误：数据目录不存在: {data_dir}")
        print(f"请确保目录存在或设置环境变量 LLMPHISH_TRAIN_DIR")
        return

    # 加载邮件
    emails = load_emails_from_dir(data_dir)
    if not emails:
        print(f"错误：未在目录中加载到有效邮件：{data_dir}")
        return

    print(f"\n成功加载 {len(emails)} 封邮件")
    print("=" * 60)

    # 提取特征
    print("\n正在提取特征...")
    X = []
    failed_count = 0
    
    for i, content in enumerate(emails):
        if (i + 1) % 100 == 0:
            print(f"  处理进度: {i + 1}/{len(emails)}")
        
        try:
            feats = extract_traditional_features(content)
            vec = build_feature_vector(feats)
            X.append(vec)
        except Exception as e:
            print(f"  警告：处理邮件 {i} 时出错: {e}")
            failed_count += 1
            continue

    if not X:
        print("错误：没有成功提取任何特征！")
        return

    X = np.array(X)
    print(f"\n特征提取完成！")
    print(f"  成功样本数: {X.shape[0]}")
    print(f"  失败样本数: {failed_count}")
    print(f"  特征维度: {X.shape[1]}")
    
    # 特征名称（与build_feature_vector对应）
    feature_names = [
        # 基础统计特征 (6个)
        "num_chars", "num_lines", "num_urls", "subject_len", 
        "keyword_hit_count", "brand_hit_count",
        # URL和域名特征 (4个)
        "high_risk_url_count", "anchor_mismatch_count", 
        "unique_domains", "has_ip_url",
        # HTML和脚本特征 (3个)
        "has_html", "has_script_or_form", "has_attachment_hint",
        # 钓鱼模式特征 (8个)
        "fake_sender_score", "has_base64", "base64_blocks",
        "chinese_keyword_count", "attachment_risk_score",
        "received_count", "boundary_count", "has_x_mailer",
        # 邮件认证特征 (5个)
        "spf_fail", "dkim_fail", "dmarc_fail",
        "dkim_present", "spf_present",
    ]
    
    # 分析特征统计
    print("\n分析特征统计信息...")
    feature_stats = analyze_feature_statistics(X, feature_names)
    
    # 打印一些关键统计
    print("\n关键特征统计：")
    key_features = ["num_urls", "chinese_keyword_count", "has_base64", 
                    "fake_sender_score", "attachment_risk_score"]
    for feat in key_features:
        if feat in feature_stats:
            stats = feature_stats[feat]
            print(f"  {feat:25s}: mean={stats['mean']:.2f}, "
                  f"std={stats['std']:.2f}, max={stats['max']:.2f}")

    # 标准化特征
    print("\n标准化特征...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # 训练Isolation Forest模型
    print("\n训练 Isolation Forest 模型...")
    print("  参数配置:")
    print("    - n_estimators: 300")
    print("    - contamination: 0.1 (假设10%为极端异常)")
    print("    - random_state: 42")
    
    clf = IsolationForest(
        n_estimators=300,
        contamination=0.1,
        random_state=42,
        n_jobs=-1,
        verbose=0,
    )
    clf.fit(X_scaled)
    
    # 评估模型
    print("\n评估模型...")
    predictions = clf.predict(X_scaled)
    scores = clf.score_samples(X_scaled)
    
    n_outliers = np.sum(predictions == -1)
    n_inliers = np.sum(predictions == 1)
    
    print(f"  异常样本数: {n_outliers} ({n_outliers/len(predictions)*100:.1f}%)")
    print(f"  正常样本数: {n_inliers} ({n_inliers/len(predictions)*100:.1f}%)")
    print(f"  异常分数范围: [{scores.min():.3f}, {scores.max():.3f}]")
    print(f"  异常分数均值: {scores.mean():.3f}")
    print(f"  异常分数标准差: {scores.std():.3f}")

    # 保存模型和相关信息
    model_dir = Path("models")
    model_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n保存模型和元数据...")
    
    # 保存模型
    model_path = model_dir / "phish_iforest.joblib"
    joblib.dump(clf, model_path)
    print(f"  ✓ 模型已保存: {model_path}")
    
    # 保存标准化器
    scaler_path = model_dir / "phish_iforest_scaler.joblib"
    joblib.dump(scaler, scaler_path)
    print(f"  ✓ 标准化器已保存: {scaler_path}")
    
    # 保存特征统计信息
    metadata = {
        "n_samples": int(X.shape[0]),
        "n_features": int(X.shape[1]),
        "feature_names": feature_names,
        "feature_statistics": feature_stats,
        "model_params": {
            "n_estimators": 300,
            "contamination": 0.1,
            "random_state": 42,
        },
        "evaluation": {
            "n_outliers": int(n_outliers),
            "n_inliers": int(n_inliers),
            "score_min": float(scores.min()),
            "score_max": float(scores.max()),
            "score_mean": float(scores.mean()),
            "score_std": float(scores.std()),
        },
    }
    
    metadata_path = model_dir / "model_metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f"  ✓ 元数据已保存: {metadata_path}")
    
    print("\n" + "=" * 60)
    print("训练完成！")
    print("=" * 60)
    print("\n模型文件:")
    print(f"  - {model_path}")
    print(f"  - {scaler_path}")
    print(f"  - {metadata_path}")
    print("\n使用方法:")
    print("  1. 加载模型和标准化器")
    print("  2. 提取特征: build_feature_vector(extract_traditional_features(email))")
    print("  3. 标准化: scaler.transform([features])")
    print("  4. 预测: model.predict(scaled_features)")
    print("  5. 异常分数: model.score_samples(scaled_features)")


if __name__ == "__main__":
    main()
