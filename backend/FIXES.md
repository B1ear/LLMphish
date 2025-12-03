# LLMPhish 系统问题修复方案

## 问题1: IsolationForest 模型识别率低

### 原因分析
1. 训练数据可能包含BASE64编码的邮件内容，导致特征提取不准确
2. 特征向量维度较少（仅14维），信息量不足
3. 训练时使用的是钓鱼邮件（异常类），但IsolationForest期望的是正常样本

### 解决方案

#### 方案A: 重新训练模型（推荐）
使用更好的特征和训练策略：

```bash
# 1. 清理训练数据（去除BASE64编码部分）
# 2. 使用扩展的特征集
# 3. 重新训练模型
cd backend
python train_model_improved.py
```

#### 方案B: 调整现有模型的阈值
如果无法重新训练，可以调整决策阈值。

## 问题2: 无法调用LLM

### 解决方案

#### 步骤1: 配置环境变量

**Windows PowerShell:**
```powershell
# 配置 DashScope (Qwen3) - 推荐
$env:DASHSCOPE_API_KEY="your-dashscope-api-key"

# 或配置 DeepSeek (DeepSeek-V3)
$env:DEEPSEEK_API_KEY="your-deepseek-api-key"
```

**Windows CMD:**
```cmd
set DASHSCOPE_API_KEY=your-dashscope-api-key
set DEEPSEEK_API_KEY=your-deepseek-api-key
```

#### 步骤2: 安装依赖
```bash
pip install openai
```

#### 步骤3: 测试LLM连接
```bash
python test_llm_connection.py
```

## 问题3: PhishMMF模型无法使用

### 解决方案

#### 步骤1: 检查模型文件
```bash
# 检查模型是否存在
dir backend\models\phishmmf_rf.joblib
dir backend\models\phishmmf_xgb.joblib
```

#### 步骤2: 重新训练PhishMMF模型
```bash
cd backend
python train_phishmmf_model.py
```

#### 步骤3: 验证模型加载
```bash
python test_phishmmf_models.py
```

## 快速修复脚本

运行以下命令进行一键修复：

```bash
cd backend
python fix_all_issues.py
```

## 验证修复

### 1. 测试IsolationForest
```bash
curl -X POST http://localhost:8000/api/detection/{email_id}
```

### 2. 测试LLM
```bash
curl -X POST http://localhost:8000/api/detection/llm/{email_id}
```

### 3. 测试PhishMMF
```bash
curl -X POST http://localhost:8000/api/detection/phishmmf/{email_id}
```

## 注意事项

1. **API费用**: LLM调用会产生费用，请注意用量控制
2. **网络要求**: 需要能访问DashScope和DeepSeek的API端点
3. **模型性能**: 重新训练模型可能需要较长时间（取决于数据量）
