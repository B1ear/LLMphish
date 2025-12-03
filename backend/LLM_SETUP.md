# LLM 配置说明

本项目支持使用阿里云 DashScope (Qwen3) 和 DeepSeek (DeepSeek-V3) 进行钓鱼邮件检测。

## 环境变量配置

### 1. 阿里云 DashScope (Qwen3)

设置环境变量：
```bash
# Windows PowerShell
$env:DASHSCOPE_API_KEY="your-dashscope-api-key"

# Windows CMD
set DASHSCOPE_API_KEY=your-dashscope-api-key

# Linux/Mac
export DASHSCOPE_API_KEY="your-dashscope-api-key"
```

获取 API Key：
1. 访问 [阿里云 DashScope 控制台](https://dashscope.console.aliyun.com/)
2. 创建 API Key
3. 将 API Key 设置为环境变量

### 2. DeepSeek (DeepSeek-V3)

设置环境变量：
```bash
# Windows PowerShell
$env:DEEPSEEK_API_KEY="your-deepseek-api-key"

# Windows CMD
set DEEPSEEK_API_KEY=your-deepseek-api-key

# Linux/Mac
export DEEPSEEK_API_KEY="your-deepseek-api-key"
```

获取 API Key：
1. 访问 [DeepSeek 官网](https://www.deepseek.com/)
2. 注册账号并创建 API Key
3. 将 API Key 设置为环境变量

## 使用说明

### 优先级

系统会按以下优先级使用 LLM：
1. **优先使用 DashScope (Qwen3)**
2. 如果 DashScope 不可用，自动回退到 **DeepSeek (DeepSeek-V3)**
3. 如果两者都不可用，系统会使用传统规则检测（不依赖LLM）

### API 接口

#### 1. 特征提取（包含LLM语义特征）
```
GET /api/features/{email_id}
```

返回结果中包含 `llm_semantic_features`，包括：
- `phishing_intent_score`: 钓鱼意图得分 (0-1)
- `urgency_score`: 紧急程度得分 (0-1)
- `sentiment_score`: 情感得分 (-1到1)
- `suspicious_language_score`: 可疑语言得分 (0-1)
- `confidence_level`: 置信度 (0-1)

#### 2. 综合检测（集成LLM）
```
POST /api/detection/{email_id}
```

该接口会综合以下结果：
- 传统规则检测
- IsolationForest 模型
- LLM 语义特征
- LLM 辅助检测

#### 3. 纯LLM检测
```
POST /api/detection/llm/{email_id}
```

仅使用 LLM 进行检测，返回：
- `is_phishing`: 是否为钓鱼邮件
- `attack_type`: 攻击类型（traditional/llm_generated/hybrid/benign）
- `risk_score`: 风险评分 (0-1)
- `reasoning`: LLM 的推理过程

## 注意事项

1. **API 费用**：使用 LLM API 会产生费用，请关注用量
2. **网络要求**：需要能够访问 DashScope 和 DeepSeek 的 API 端点
3. **响应时间**：LLM 调用可能需要几秒时间，请耐心等待
4. **Token 限制**：邮件内容过长时会被截断（限制在2000字符以内）

## 故障排查

如果 LLM 功能不可用，检查：
1. 环境变量是否正确设置
2. API Key 是否有效
3. 网络连接是否正常
4. 查看后端日志中的错误信息

