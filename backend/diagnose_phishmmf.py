"""
PhishMMF-XGB 模型诊断脚本

检查：
1. 模型是否正确加载
2. 特征提取是否合理
3. 模型预测分布是否正常
4. 训练数据是否平衡
"""

import sys
from pathlib import Path

import joblib
import numpy as np

# 添加 backend 到路径
sys.path.insert(0, str(Path(__file__).parent))

from app.phishmmf_features import extract_phishmmf_features_228d


def check_model_loading():
    """检查模型是否正确加载"""
    print("=" * 60)
    print("1. 检查模型加载")
    print("=" * 60)
    
    # 使用绝对路径
    script_dir = Path(__file__).parent
    models_dir = script_dir / "models"
    rf_path = models_dir / "phishmmf_rf.joblib"
    xgb_path = models_dir / "phishmmf_xgb.joblib"
    
    if not rf_path.exists():
        print(f"❌ RF 模型不存在: {rf_path}")
        return None, None
    
    if not xgb_path.exists():
        print(f"❌ XGB 模型不存在: {xgb_path}")
        return None, None
    
    try:
        rf_model = joblib.load(rf_path)
        print(f"✅ RF 模型加载成功")
        print(f"   - 类型: {type(rf_model)}")
        print(f"   - 特征数: {rf_model.n_features_in_}")
        print(f"   - 类别数: {rf_model.n_classes_}")
        print(f"   - 类别: {rf_model.classes_}")
    except Exception as e:
        print(f"❌ RF 模型加载失败: {e}")
        rf_model = None
    
    try:
        xgb_model = joblib.load(xgb_path)
        print(f"✅ XGB 模型加载成功")
        print(f"   - 类型: {type(xgb_model)}")
        print(f"   - 特征数: {xgb_model.n_features_in_}")
        print(f"   - 类别数: {xgb_model.n_classes_}")
        print(f"   - 类别: {xgb_model.classes_}")
    except Exception as e:
        print(f"❌ XGB 模型加载失败: {e}")
        xgb_model = None
    
    return rf_model, xgb_model


def check_feature_extraction():
    """检查特征提取是否合理"""
    print("\n" + "=" * 60)
    print("2. 检查特征提取")
    print("=" * 60)
    
    # 测试正常邮件
    normal_email = """
From: support@company.com
Subject: Weekly Newsletter
Date: Mon, 1 Jan 2024 10:00:00 +0000

Hello,

This is our weekly newsletter with updates about our products.

Best regards,
Company Team
"""
    
    # 测试钓鱼邮件
    phishing_email = """
From: security@paypa1-verify.com
Subject: URGENT: Your account will be suspended!
Date: Mon, 1 Jan 2024 10:00:00 +0000

Dear Customer,

Your PayPal account has been locked due to suspicious activity.
Click here immediately to verify your account: http://192.168.1.1/verify
If you don't verify within 24 hours, your account will be permanently closed.

Enter your password, credit card number, and SSN to verify.

PayPal Security Team
"""
    
    print("\n正常邮件特征:")
    normal_features = extract_phishmmf_features_228d(normal_email)
    print(f"  - 特征维度: {len(normal_features)}")
    print(f"  - 特征范围: [{min(normal_features):.2f}, {max(normal_features):.2f}]")
    print(f"  - 非零特征数: {sum(1 for f in normal_features if f != 0.0)}")
    print(f"  - 前10个特征: {[f'{f:.2f}' for f in normal_features[:10]]}")
    
    print("\n钓鱼邮件特征:")
    phishing_features = extract_phishmmf_features_228d(phishing_email)
    print(f"  - 特征维度: {len(phishing_features)}")
    print(f"  - 特征范围: [{min(phishing_features):.2f}, {max(phishing_features):.2f}]")
    print(f"  - 非零特征数: {sum(1 for f in phishing_features if f != 0.0)}")
    print(f"  - 前10个特征: {[f'{f:.2f}' for f in phishing_features[:10]]}")
    
    # 检查特征差异
    diff = np.array(phishing_features) - np.array(normal_features)
    significant_diff = sum(1 for d in diff if abs(d) > 0.1)
    print(f"\n特征差异分析:")
    print(f"  - 显著差异特征数 (|diff| > 0.1): {significant_diff}")
    print(f"  - 最大差异: {max(abs(d) for d in diff):.2f}")
    
    return normal_features, phishing_features


def check_model_predictions(rf_model, xgb_model, normal_features, phishing_features):
    """检查模型预测是否合理"""
    print("\n" + "=" * 60)
    print("3. 检查模型预测")
    print("=" * 60)
    
    if rf_model is None or xgb_model is None:
        print("❌ 模型未加载，跳过预测检查")
        return
    
    # 转换为 numpy 数组
    X_normal = np.array(normal_features).reshape(1, -1)
    X_phishing = np.array(phishing_features).reshape(1, -1)
    
    print("\n正常邮件预测:")
    try:
        rf_proba_normal = rf_model.predict_proba(X_normal)[0]
        print(f"  RF:  钓鱼概率 = {rf_proba_normal[1]:.4f}")
    except Exception as e:
        print(f"  RF:  预测失败 - {e}")
    
    try:
        xgb_proba_normal = xgb_model.predict_proba(X_normal)[0]
        print(f"  XGB: 钓鱼概率 = {xgb_proba_normal[1]:.4f}")
    except Exception as e:
        print(f"  XGB: 预测失败 - {e}")
    
    print("\n钓鱼邮件预测:")
    try:
        rf_proba_phishing = rf_model.predict_proba(X_phishing)[0]
        print(f"  RF:  钓鱼概率 = {rf_proba_phishing[1]:.4f}")
    except Exception as e:
        print(f"  RF:  预测失败 - {e}")
    
    try:
        xgb_proba_phishing = xgb_model.predict_proba(X_phishing)[0]
        print(f"  XGB: 钓鱼概率 = {xgb_proba_phishing[1]:.4f}")
    except Exception as e:
        print(f"  XGB: 预测失败 - {e}")


def check_training_data():
    """检查训练数据是否平衡"""
    print("\n" + "=" * 60)
    print("4. 检查训练数据")
    print("=" * 60)
    
    # 尝试加载原始训练数据
    base = Path(r"C:\Users\Zeus\Desktop\LLMPhish\PhishMMF-main")
    
    feat_path_plural = base / "email_phishing_features_228d.npy"
    feat_path_single = base / "email_phishing_feature_228d.npy"
    if feat_path_plural.exists():
        feat_path = feat_path_plural
    else:
        feat_path = feat_path_single
    
    label_path = base / "email_phishing_labels.npy"
    
    if not feat_path.exists() or not label_path.exists():
        print(f"⚠️  训练数据不存在，跳过检查")
        print(f"   特征文件: {feat_path}")
        print(f"   标签文件: {label_path}")
        return
    
    try:
        X_all = np.load(feat_path)
        y_all = np.load(label_path)
        
        print(f"✅ 训练数据加载成功")
        print(f"   - 样本数: {len(y_all)}")
        print(f"   - 特征维度: {X_all.shape[1]}")
        
        # 检查标签分布
        unique, counts = np.unique(y_all, return_counts=True)
        print(f"\n标签分布:")
        for label, count in zip(unique, counts):
            percentage = count / len(y_all) * 100
            label_name = "钓鱼" if label == 1 else "正常"
            print(f"   - {label_name} (label={label}): {count} ({percentage:.1f}%)")
        
        # 检查特征统计
        X_feat = X_all[:, :228]
        print(f"\n特征统计:")
        print(f"   - 特征范围: [{X_feat.min():.2f}, {X_feat.max():.2f}]")
        print(f"   - 特征均值: {X_feat.mean():.2f}")
        print(f"   - 特征标准差: {X_feat.std():.2f}")
        
        # 检查是否有全零特征
        zero_features = np.sum(X_feat == 0, axis=0)
        all_zero_count = sum(1 for z in zero_features if z == len(X_feat))
        print(f"   - 全零特征数: {all_zero_count} / 228")
        
        # 检查钓鱼和正常样本的特征差异
        phishing_mask = y_all == 1
        normal_mask = y_all == 0
        
        phishing_mean = X_feat[phishing_mask].mean(axis=0)
        normal_mean = X_feat[normal_mask].mean(axis=0)
        
        diff = np.abs(phishing_mean - normal_mean)
        significant_diff_count = sum(1 for d in diff if d > 0.1)
        
        print(f"\n钓鱼 vs 正常特征差异:")
        print(f"   - 显著差异特征数 (|diff| > 0.1): {significant_diff_count} / 228")
        print(f"   - 最大差异: {diff.max():.2f}")
        print(f"   - 平均差异: {diff.mean():.2f}")
        
        if significant_diff_count < 20:
            print(f"\n⚠️  警告: 显著差异特征数较少，模型可能难以区分钓鱼和正常邮件")
        
    except Exception as e:
        print(f"❌ 训练数据加载失败: {e}")


def check_model_bias(xgb_model):
    """检查模型是否有偏向"""
    print("\n" + "=" * 60)
    print("5. 检查模型偏向")
    print("=" * 60)
    
    if xgb_model is None:
        print("❌ XGB 模型未加载，跳过偏向检查")
        return
    
    # 生成随机特征向量，检查预测分布
    print("\n生成 1000 个随机特征向量，检查预测分布...")
    np.random.seed(42)
    
    # 生成不同分布的随机特征
    test_cases = {
        "全零特征": np.zeros((1000, 228)),
        "均匀分布 [0, 1]": np.random.uniform(0, 1, (1000, 228)),
        "正态分布 (0, 0.5)": np.abs(np.random.normal(0, 0.5, (1000, 228))),
        "小值分布 [0, 0.1]": np.random.uniform(0, 0.1, (1000, 228)),
    }
    
    for name, X_test in test_cases.items():
        try:
            probas = xgb_model.predict_proba(X_test)[:, 1]
            mean_proba = probas.mean()
            std_proba = probas.std()
            high_risk_count = sum(1 for p in probas if p > 0.7)
            
            print(f"\n{name}:")
            print(f"   - 平均钓鱼概率: {mean_proba:.4f}")
            print(f"   - 标准差: {std_proba:.4f}")
            print(f"   - 高风险样本 (>0.7): {high_risk_count} / 1000 ({high_risk_count/10:.1f}%)")
            
            if mean_proba > 0.7:
                print(f"   ⚠️  警告: 平均概率过高，模型可能偏向预测为钓鱼邮件")
            elif mean_proba < 0.3:
                print(f"   ✅ 正常: 平均概率较低")
            else:
                print(f"   ⚠️  注意: 平均概率居中，模型可能不够确定")
        except Exception as e:
            print(f"\n{name}: 预测失败 - {e}")


def main():
    print("PhishMMF-XGB 模型诊断工具")
    print("=" * 60)
    
    # 1. 检查模型加载
    rf_model, xgb_model = check_model_loading()
    
    # 2. 检查特征提取
    normal_features, phishing_features = check_feature_extraction()
    
    # 3. 检查模型预测
    check_model_predictions(rf_model, xgb_model, normal_features, phishing_features)
    
    # 4. 检查训练数据
    check_training_data()
    
    # 5. 检查模型偏向
    check_model_bias(xgb_model)
    
    print("\n" + "=" * 60)
    print("诊断完成")
    print("=" * 60)
    
    print("\n建议:")
    print("1. 如果模型对所有邮件都预测为钓鱼，可能是:")
    print("   - 训练数据不平衡（钓鱼样本过多）")
    print("   - 特征提取有问题（提取的特征与训练数据不匹配）")
    print("   - 模型训练参数不当（过拟合）")
    print("\n2. 解决方案:")
    print("   - 检查训练数据标签是否正确")
    print("   - 调整模型训练参数（降低复杂度）")
    print("   - 使用类别权重平衡训练")
    print("   - 调整决策阈值（不使用默认的 0.5）")


if __name__ == "__main__":
    main()
