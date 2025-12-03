# LLMPhish 快速启动指南

## 问题修复步骤

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

如果没有requirements.txt，手动安装：

```bash
pip install fastapi uvicorn scikit-learn joblib numpy xgboost openai pillow
```

### 2. 配置LLM API Key

**选择一个或两个LLM服务：**

#### 方案A: 使用阿里云 DashScope (Qwen3) - 推荐

```powershell
# Windows PowerShell
$env:DASHSCOPE_API_KEY="sk-your-dashscope-api-key"
```

获取API Key: https://dashscope.console.aliyun.com/

#### 方案B: 使用 DeepSeek (DeepSeek-V3)

```powershell
# Windows PowerShell
$env:DEEPSEEK_API_KEY="sk-your-deepseek-api-key"
```

获取API Key: https://platform.deepseek.com/

### 3. 重新训练IsolationForest模型

**问题原因：** 原模型可能使用BASE64编码的邮件训练，导致识别率低。

**解决方案：** 使用改进的训练脚本

```bash
cd backend
python train_model_improved.py
```

这个脚本会：
- 自动清理BASE64编码内容
- 使用更丰富的特征集（从14维扩展到25+维）
- 应用特征标准化
- 生成两个文件：
  - `models/phish_iforest.joblib` (模型)
  - `models/phish_iforest_scaler.joblib` (标准化器)

### 4. 训练PhishMMF模型

```bash
cd backend
python train_phishmmf_model.py
```

这会生成：
- `models/phishmmf_rf.joblib` (RandomForest模型)
- `models/phishmmf_xgb.joblib` (XGBoost模型)

### 5. 测试系统

#### 测试LLM连接

```bash
python test_llm_connection.py
```

#### 测试PhishMMF模型

```bash
python test_phishmmf_models.py
```

#### 一键检查和修复

```bash
python fix_all_issues.py
```

### 6. 启动服务器

```bash
python run_server.py
```

服务器将在 http://localhost:8000 启动

### 7. 测试API

访问API文档: http://localhost:8000/docs

#### 测试端点：

1. **上传邮件**
```bash
curl -X POST "http://localhost:8000/api/upload" \
  -F "file=@test_email.eml"
```

2. **提取特征（包含LLM语义特征）**
```bash
curl "http://localhost:8000/api/features/{email_id}"
```

3. **综合检测（集成所有模型+LLM）**
```bash
curl -X POST "http://localhost:8000/api/detection/{email_id}"
```

4. **纯LLM检测**
```bash
curl -X POST "http://localhost:8000/api/detection/llm/{email_id}"
```

5. **PhishMMF模型检测**
```bash
curl -X POST "http://localhost:8000/api/detection/phishmmf/{email_id}"
```

## 常见问题

### Q1: IsolationForest识别率仍然很低？

**可能原因：**
1. 训练数据质量问题
2. 特征提取不准确
3. 模型参数需要调整

**解决方案：**
1. 检查训练数据是否包含大量BASE64编码
2. 调整 `train_model_improved.py` 中的 `contamination` 参数（默认0.1）
3. 增加更多特征维度

### Q2: LLM调用失败？

**检查清单：**
1. ✓ API Key是否正确设置
2. ✓ 网络是否能访问API端点
3. ✓ API Key是否有效（未过期、有余额）
4. ✓ openai包是否已安装

**调试命令：**
```bash
python test_llm_connection.py
```

### Q3: PhishMMF模型无法加载？

**检查清单：**
1. ✓ 模型文件是否存在于 `backend/models/` 目录
2. ✓ PhishMMF数据集是否存在
3. ✓ 训练是否成功完成

**重新训练：**
```bash
python train_phishmmf_model.py
```

### Q4: 特征维度不匹配？

**原因：** IsolationForest模型期望的特征维度与实际提取的不一致

**解决方案：**
1. 重新训练模型（推荐）
2. 或修改 `app/analysis.py` 中的 `build_feature_vector()` 函数

## 性能优化建议

### 1. IsolationForest模型优化

编辑 `train_model_improved.py`：

```python
clf = IsolationForest(
    n_estimators=500,      # 增加树的数量（默认300）
    contamination=0.15,    # 调整异常比例（默认0.1）
    max_samples='auto',
    max_features=1.0,
    n_jobs=-1,
    random_state=42,
)
```

### 2. PhishMMF模型优化

编辑 `train_phishmmf_model.py`：

```python
# RandomForest
rf_clf = RandomForestClassifier(
    n_estimators=600,      # 增加树的数量（默认400）
    max_depth=None,
    min_samples_leaf=1,    # 减少叶子节点最小样本数（默认2）
    n_jobs=-1,
    random_state=42,
)

# XGBoost
xgb_clf = XGBClassifier(
    n_estimators=600,      # 增加树的数量（默认400）
    max_depth=8,           # 增加树深度（默认6）
    learning_rate=0.03,    # 降低学习率（默认0.05）
    subsample=0.8,
    colsample_bytree=0.8,
    n_jobs=-1,
    random_state=42,
)
```

### 3. LLM调用优化

- 使用缓存避免重复调用
- 限制邮件内容长度（当前限制2000字符）
- 批量处理多个邮件

## 下一步

1. 查看详细修复说明: `FIXES.md`
2. 阅读LLM配置文档: `LLM_SETUP.md`
3. 查看API文档: http://localhost:8000/docs
4. 监控日志输出以发现问题

## 技术支持

如果问题仍未解决，请检查：
1. 后端日志输出
2. 浏览器控制台错误
3. API响应详情

祝使用愉快！
