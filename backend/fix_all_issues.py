"""
一键修复所有问题的脚本
"""

import os
import sys
import asyncio
from pathlib import Path


def check_environment():
    """检查环境配置"""
    print("=" * 60)
    print("环境检查")
    print("=" * 60)
    
    issues = []
    
    # 检查Python版本
    print(f"\nPython 版本: {sys.version}")
    if sys.version_info < (3, 8):
        issues.append("Python版本过低，需要3.8+")
    
    # 检查依赖包
    print("\n检查依赖包:")
    required_packages = [
        "fastapi",
        "uvicorn",
        "scikit-learn",
        "joblib",
        "numpy",
        "xgboost",
        "openai",
    ]
    
    for pkg in required_packages:
        try:
            __import__(pkg)
            print(f"  ✓ {pkg}")
        except ImportError:
            print(f"  ✗ {pkg} (未安装)")
            issues.append(f"缺少依赖包: {pkg}")
    
    # 检查环境变量
    print("\n检查环境变量:")
    dashscope_key = os.getenv("DASHSCOPE_API_KEY")
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    
    print(f"  DASHSCOPE_API_KEY: {'已设置 ✓' if dashscope_key else '未设置 ✗'}")
    print(f"  DEEPSEEK_API_KEY: {'已设置 ✓' if deepseek_key else '未设置 ✗'}")
    
    if not (dashscope_key or deepseek_key):
        issues.append("未设置任何LLM API Key")
    
    # 检查模型文件
    print("\n检查模型文件:")
    model_dir = Path("models")
    model_files = {
        "phish_iforest.joblib": "IsolationForest模型",
        "phishmmf_rf.joblib": "PhishMMF RandomForest模型",
        "phishmmf_xgb.joblib": "PhishMMF XGBoost模型",
    }
    
    for filename, desc in model_files.items():
        path = model_dir / filename
        exists = path.exists()
        print(f"  {desc}: {'存在 ✓' if exists else '不存在 ✗'}")
        if not exists:
            issues.append(f"缺少模型文件: {filename}")
    
    # 检查训练数据
    print("\n检查训练数据:")
    data_dir = os.environ.get(
        "LLMPHISH_TRAIN_DIR",
        r"C:\Users\Zeus\Desktop\LLMPhish\datacon2023-spoof-email-main",
    )
    data_path = Path(data_dir)
    
    if data_path.exists():
        eml_files = list(data_path.glob("*.eml"))
        print(f"  训练数据目录: {data_dir}")
        print(f"  邮件文件数量: {len(eml_files)} ✓")
    else:
        print(f"  训练数据目录: {data_dir} ✗")
        issues.append("训练数据目录不存在")
    
    # PhishMMF数据
    phishmmf_dir = Path(r"C:\Users\Zeus\Desktop\LLMPhish\PhishMMF-main")
    if phishmmf_dir.exists():
        feat_files = list(phishmmf_dir.glob("email_phishing_feature*.npy"))
        label_file = phishmmf_dir / "email_phishing_labels.npy"
        print(f"\n  PhishMMF数据目录: {phishmmf_dir}")
        print(f"  特征文件: {'存在 ✓' if feat_files else '不存在 ✗'}")
        print(f"  标签文件: {'存在 ✓' if label_file.exists() else '不存在 ✗'}")
    else:
        print(f"\n  PhishMMF数据目录: {phishmmf_dir} ✗")
        issues.append("PhishMMF数据目录不存在")
    
    return issues


def fix_issues(issues):
    """修复问题"""
    print("\n" + "=" * 60)
    print("问题修复")
    print("=" * 60)
    
    if not issues:
        print("\n✓ 没有发现问题！")
        return True
    
    print(f"\n发现 {len(issues)} 个问题:")
    for i, issue in enumerate(issues, 1):
        print(f"  {i}. {issue}")
    
    print("\n开始修复...")
    
    # 修复依赖包
    if any("依赖包" in issue for issue in issues):
        print("\n1. 安装缺失的依赖包:")
        print("   pip install -r requirements.txt")
        print("   (请手动执行)")
    
    # 修复环境变量
    if any("API Key" in issue for issue in issues):
        print("\n2. 配置LLM API Key:")
        print("   Windows PowerShell:")
        print("   $env:DASHSCOPE_API_KEY=\"your-dashscope-api-key\"")
        print("   $env:DEEPSEEK_API_KEY=\"your-deepseek-api-key\"")
        print("   (请手动配置)")
    
    # 修复模型文件
    if any("模型文件" in issue for issue in issues):
        print("\n3. 训练缺失的模型:")
        
        model_dir = Path("models")
        if not (model_dir / "phish_iforest.joblib").exists():
            print("\n   训练 IsolationForest 模型:")
            print("   python train_model_improved.py")
            
            response = input("\n   是否现在训练? (y/n): ")
            if response.lower() == 'y':
                try:
                    import train_model_improved
                    train_model_improved.main()
                    print("   ✓ IsolationForest 模型训练完成")
                except Exception as e:
                    print(f"   ✗ 训练失败: {e}")
        
        if not (model_dir / "phishmmf_rf.joblib").exists() or \
           not (model_dir / "phishmmf_xgb.joblib").exists():
            print("\n   训练 PhishMMF 模型:")
            print("   python train_phishmmf_model.py")
            
            response = input("\n   是否现在训练? (y/n): ")
            if response.lower() == 'y':
                try:
                    import train_phishmmf_model
                    train_phishmmf_model.main()
                    print("   ✓ PhishMMF 模型训练完成")
                except Exception as e:
                    print(f"   ✗ 训练失败: {e}")
    
    return False


async def test_system():
    """测试系统功能"""
    print("\n" + "=" * 60)
    print("系统功能测试")
    print("=" * 60)
    
    # 测试LLM
    print("\n1. 测试LLM连接:")
    try:
        from app.llm_service import llm_service, LLMProvider
        
        dashscope_available = llm_service.is_available(LLMProvider.DASHSCOPE)
        deepseek_available = llm_service.is_available(LLMProvider.DEEPSEEK)
        
        if dashscope_available or deepseek_available:
            print("   ✓ LLM服务可用")
            
            # 简单测试
            test_email = "Test email content"
            result = await llm_service.analyze_email_semantics(
                test_email,
                provider=LLMProvider.DASHSCOPE if dashscope_available else LLMProvider.DEEPSEEK
            )
            
            if result.get("llm_supported"):
                print(f"   ✓ LLM调用成功 (提供商: {result.get('provider')})")
            else:
                print(f"   ✗ LLM调用失败: {result.get('note')}")
        else:
            print("   ✗ LLM服务不可用")
    except Exception as e:
        print(f"   ✗ LLM测试失败: {e}")
    
    # 测试模型
    print("\n2. 测试模型加载:")
    try:
        from app.model import (
            iforest_available,
            phishmmf_models_available,
        )
        
        if iforest_available():
            print("   ✓ IsolationForest 模型可用")
        else:
            print("   ✗ IsolationForest 模型不可用")
        
        rf_available, xgb_available = phishmmf_models_available()
        if rf_available:
            print("   ✓ PhishMMF RandomForest 模型可用")
        else:
            print("   ✗ PhishMMF RandomForest 模型不可用")
        
        if xgb_available:
            print("   ✓ PhishMMF XGBoost 模型可用")
        else:
            print("   ✗ PhishMMF XGBoost 模型不可用")
    
    except Exception as e:
        print(f"   ✗ 模型测试失败: {e}")
    
    # 测试特征提取
    print("\n3. 测试特征提取:")
    try:
        from app.analysis import extract_traditional_features
        from app.phishmmf_features import extract_phishmmf_features_228d
        
        test_email = "From: test@example.com\nSubject: Test\n\nTest content"
        
        traditional = extract_traditional_features(test_email)
        print(f"   ✓ 传统特征提取成功 ({len(traditional)} 个特征)")
        
        phishmmf_features = extract_phishmmf_features_228d(test_email)
        print(f"   ✓ PhishMMF特征提取成功 ({len(phishmmf_features)} 维)")
    
    except Exception as e:
        print(f"   ✗ 特征提取测试失败: {e}")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("LLMPhish 系统修复工具")
    print("=" * 60)
    
    # 检查环境
    issues = check_environment()
    
    # 修复问题
    all_fixed = fix_issues(issues)
    
    # 测试系统
    if all_fixed or input("\n是否继续测试系统? (y/n): ").lower() == 'y':
        asyncio.run(test_system())
    
    print("\n" + "=" * 60)
    print("修复完成!")
    print("=" * 60)
    
    print("\n后续步骤:")
    print("1. 如果有未解决的问题，请按照提示手动修复")
    print("2. 启动服务器: python run_server.py")
    print("3. 访问 API 文档: http://localhost:8000/docs")
    print("4. 查看详细修复说明: FIXES.md")


if __name__ == "__main__":
    main()
