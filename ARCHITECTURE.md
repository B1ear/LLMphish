# 系统架构

## 概览

LLMPhish 是一个基于多模型融合的钓鱼邮件检测系统，采用前后端分离架构。

```
┌─────────────┐
│   Browser   │
│  (Vue 3)    │
└──────┬──────┘
       │ HTTP/REST
       ↓
┌─────────────────────────────────────┐
│         FastAPI Backend             │
│  ┌─────────────────────────────┐   │
│  │   Detection Router          │   │
│  │  - Upload Email             │   │
│  │  - Multi-Model Detection    │   │
│  │  - Result Management        │   │
│  └────────┬────────────────────┘   │
│           ↓                         │
│  ┌─────────────────────────────┐   │
│  │   Detection Engine          │   │
│  │  ┌──────────────────────┐   │   │
│  │  │ Simplified PhishMMF  │   │   │
│  │  │  - RF Model          │   │   │
│  │  │  - XGBoost Model     │   │   │
│  │  │  - 35D Features      │   │   │
│  │  └──────────────────────┘   │   │
│  │  ┌──────────────────────┐   │   │
│  │  │ IsolationForest      │   │   │
│  │  │  - Anomaly Detection │   │   │
│  │  └──────────────────────┘   │   │
│  │  ┌──────────────────────┐   │   │
│  │  │ Rule-based Detection │   │   │
│  │  │  - Keywords          │   │   │
│  │  │  - URL Patterns      │   │   │
│  │  └──────────────────────┘   │   │
│  │  ┌──────────────────────┐   │   │
│  │  │ LLM Detection (Opt)  │   │   │
│  │  │  - Qwen / DeepSeek   │   │   │
│  │  │  - Semantic Analysis │   │   │
│  │  └──────────────────────┘   │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

## 技术栈

### 后端

- **框架**: FastAPI 0.104+
- **机器学习**: 
  - scikit-learn 1.3+
  - XGBoost 2.0+
- **LLM 集成**: 
  - OpenAI SDK (兼容 DashScope/DeepSeek)
- **数据处理**: 
  - NumPy
  - Pandas

### 前端

- **框架**: Vue 3
- **构建工具**: Vite
- **UI 组件**: 自定义组件
- **状态管理**: Composition API
- **HTTP 客户端**: Axios

## 核心模块

### 1. 特征提取 (`simplified_phishmmf_features.py`)

从邮件中提取 35 维特征：

**文本特征 (24维)**:
- 主题分析 (6维): 紧急程度、威胁性、诱惑性、情感
- 发件人分析 (2维): 冒充类型、异常检测
- 正文分析 (16维): 词数、URL、关键词、复杂度等

**URL 特征 (11维)**:
- 域名长度、点号数、IP地址
- 路径长度、子域名数、TLD
- 查询参数、可疑参数

### 2. 模型加载 (`model.py`)

**简化 PhishMMF 模型**:
- RandomForest: 100 棵树，准确率 96%
- XGBoost: 100 轮迭代，AUC 0.9876
- StandardScaler: 特征标准化

**IsolationForest**:
- 无监督异常检测
- 适用于未知攻击模式

### 3. 检测路由 (`routers/detection.py`)

**主要端点**:
- `POST /api/detection/{email_id}`: 综合检测
- `POST /api/detection/phishmmf/{email_id}`: PhishMMF 专用检测
- `POST /api/detection/llm/{email_id}`: LLM 检测

### 4. LLM 服务 (`llm_service.py`)

**支持的 LLM**:
- 阿里云 DashScope (Qwen-Plus)
- DeepSeek (DeepSeek-Chat)

**功能**:
- 语义特征提取
- 钓鱼意图分析
- 攻击类型识别

## 数据流

### 检测流程

```
1. 用户上传邮件
   ↓
2. 存储邮件内容
   ↓
3. 提取特征
   - 文本特征
   - URL 特征
   ↓
4. 多模型检测
   - 简化 PhishMMF (权重 1.5)
   - IsolationForest (权重 1.0)
   - 规则检测 (权重 1.0)
   - LLM 检测 (权重 1.8, 可选)
   ↓
5. 加权融合
   final_score = Σ(score_i × weight_i) / Σ(weight_i)
   ↓
6. 返回结果
   - 是否钓鱼
   - 风险评分
   - 各模型得分
   - 检测原因
```

## 性能指标

### 简化 PhishMMF 模型

| 指标 | RandomForest | XGBoost |
|------|-------------|---------|
| 准确率 | 96% | 96% |
| AUC-ROC | 0.9853 | 0.9876 |
| F1-Score | 0.96 | 0.96 |
| 响应时间 | <10ms | <10ms |

### 系统性能

- **吞吐量**: ~100 请求/秒
- **平均延迟**: 
  - 不含 LLM: <50ms
  - 含 LLM: 2-3秒
- **内存占用**: ~500MB

## 扩展性

### 添加新模型

1. 在 `model.py` 中添加模型加载函数
2. 在 `detection.py` 中集成到检测流程
3. 调整权重和融合策略

### 添加新特征

1. 在 `simplified_phishmmf_features.py` 中添加特征提取逻辑
2. 重新训练模型
3. 更新特征维度

### 支持新的 LLM

1. 在 `llm_service.py` 中添加新的 provider
2. 实现相应的 API 调用
3. 更新环境变量配置

## 安全考虑

- **输入验证**: 所有用户输入都经过验证
- **文件大小限制**: 邮件内容限制在 10MB
- **API 限流**: 防止滥用
- **敏感信息**: 不存储个人信息
- **临时存储**: 检测结果定期清理

## 部署建议

### 开发环境

```bash
# 后端
cd backend
python run_server.py

# 前端
cd frontend
npm run dev
```

### 生产环境

**后端**:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**前端**:
```bash
npm run build
# 使用 nginx 或其他 web 服务器托管 dist/
```

**Docker** (推荐):
```bash
docker-compose up -d
```

## 监控和日志

- **日志级别**: INFO (生产), DEBUG (开发)
- **日志位置**: `logs/app.log`
- **监控指标**: 
  - 请求数
  - 响应时间
  - 错误率
  - 模型准确率

## 未来改进

- [ ] 支持更多 LLM 提供商
- [ ] 添加深度学习模型
- [ ] 实时学习和模型更新
- [ ] 分布式部署支持
- [ ] 更详细的可视化分析
- [ ] 邮件威胁情报集成
