# 🔧 问题修复指南

## 快速修复（3步）

### 1️⃣ 配置LLM API Key

选择一个服务并配置环境变量：

```powershell
# 阿里云 DashScope (推荐)
$env:DASHSCOPE_API_KEY="your-api-key"

# 或 DeepSeek
$env:DEEPSEEK_API_KEY="your-api-key"
```

### 2️⃣ 重新训练模型

```bash
cd backend

# 训练改进的 IsolationForest 模型
python train_model_improved.py

# 训练 PhishMMF 模型
python train_phishmmf_model.py
```

### 3️⃣ 测试和启动

```bash
# 一键检查和测试
python fix_all_issues.py

# 启动服务器
python run_server.py
```

---

## 📚 详细文档

- **快速开始**: [QUICK_START.md](QUICK_START.md)
- **问题详情**: [FIXES.md](FIXES.md)
- **完整总结**: [SOLUTION_SUMMARY.md](SOLUTION_SUMMARY.md)
- **LLM配置**: [LLM_SETUP.md](LLM_SETUP.md)

---

## 🎯 解决的问题

✅ **IsolationForest 识别率低**
- 原因：BASE64编码、特征不足
- 方案：改进的训练脚本 + 特征增强

✅ **无法调用LLM**
- 原因：未配置API Key
- 方案：配置环境变量

✅ **PhishMMF 模型无法使用**
- 原因：模型未训练
- 方案：运行训练脚本

---

## 🧪 测试脚本

```bash
# 测试LLM连接
python test_llm_connection.py

# 测试PhishMMF模型
python test_phishmmf_models.py

# 一键检查所有问题
python fix_all_issues.py
```

---

## 📊 预期效果

| 功能 | 修复前 | 修复后 |
|------|--------|--------|
| IsolationForest | ❌ 识别率低 | ✅ 识别率>70% |
| LLM语义分析 | ❌ 不可用 | ✅ 可用 |
| PhishMMF检测 | ❌ 不可用 | ✅ 可用 |
| 综合检测 | ⚠️ 仅规则 | ✅ 多模型融合 |

---

## 🆘 需要帮助？

1. 查看 [QUICK_START.md](QUICK_START.md) 的常见问题部分
2. 运行 `python fix_all_issues.py` 进行诊断
3. 检查后端日志输出

---

**祝使用愉快！** 🚀
