

# LLMPhish - 智能钓鱼邮件检测系统

基于机器学习和大语言模型的钓鱼邮件检测系统，集成多种检测方法，提供高准确率的邮件安全分析。

## ✨ 特性

### 多模型融合检测
- **简化 PhishMMF 模型**：96% 准确率，AUC 0.98+，使用 35 个可提取特征
- **IsolationForest**：无监督异常检测
- **规则检测**：基于关键词和模式的快速筛选
- **LLM 语义检测**（可选）：支持 Qwen 和 DeepSeek，深度语义理解

### 现代化 Web 界面
- 📧 邮件上传和预览
- 📊 实时检测结果展示
- 🎨 响应式设计，支持移动端
- 🌓 深色模式支持
- 📎 附件预览和下载

### 高性能架构
- FastAPI 后端，异步处理
- Vue 3 前端，组件化设计
- RESTful API，易于集成
- 模块化设计，易于扩展

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Node.js 16+
- npm 或 yarn

### 安装

#### 1. 克隆项目

```bash
git clone https://github.com/B1ear/LLMphish.git
cd LLMphish
```

#### 2. 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

#### 3. 安装前端依赖

```bash
cd ../frontend
npm install
# 或
yarn install
```

### 配置

#### 配置文件（推荐）

如果需要使用 LLM 检测功能，配置 API Keys：

1. 复制配置文件模板：
```bash
cd backend
cp config.example.json config.json
```

2. 编辑 `backend/config.json`，填入你的 API Keys：
```json
{
  "llm": {
    "dashscope_api_key": "your_dashscope_api_key_here",
    "deepseek_api_key": "your_deepseek_api_key_here"
  }
}
```

#### 环境变量（可选）

也可以使用环境变量（优先级高于配置文件）：

```bash
# 阿里云 DashScope (Qwen)
export DASHSCOPE_API_KEY=your_dashscope_api_key

# DeepSeek
export DEEPSEEK_API_KEY=your_deepseek_api_key
```

### 运行

#### 启动后端

```bash
cd backend
python run_server.py
```

后端将在 `http://localhost:8000` 运行

#### 启动前端

```bash
cd frontend
npm run dev
# 或
yarn dev
```

前端将在 `http://localhost:5173` 运行

### 访问应用

打开浏览器访问 `http://localhost:5173`

## 📖 使用指南

### 1. 上传邮件

- 点击"上传邮件"按钮
- 粘贴邮件内容（支持 EML 格式）
- 点击"提交检测"

### 2. 查看结果

系统会显示：
- 是否为钓鱼邮件
- 风险评分（0-1）
- 各模型的检测结果
- 详细的特征分析

### 3. API 使用

#### 上传邮件

```bash
POST /api/emails/upload
Content-Type: application/json

{
  "content": "邮件内容..."
}
```

#### 检测邮件

```bash
POST /api/detection/{email_id}
```

#### 使用简化 PhishMMF 检测

```bash
POST /api/detection/phishmmf/{email_id}
```

## 🏗️ 项目结构

```
LLMPhish/
├── backend/                 # 后端代码
│   ├── app/
│   │   ├── routers/        # API 路由
│   │   ├── model.py        # 模型加载
│   │   ├── simplified_phishmmf_features.py  # 特征提取
│   │   ├── llm_service.py  # LLM 服务
│   │   └── ...
│   ├── models/             # 训练好的模型
│   │   ├── phishmmf_simplified_rf.joblib
│   │   ├── phishmmf_simplified_xgb.joblib
│   │   └── phishmmf_simplified_scaler.joblib
│   ├── train_phishmmf_model.py  # 模型训练脚本
│   ├── requirements.txt
│   └── run_server.py
├── frontend/               # 前端代码
│   ├── src/
│   │   ├── views/         # 页面组件
│   │   ├── components/    # 通用组件
│   │   └── ...
│   ├── package.json
│   └── vite.config.ts
├── test_emails/           # 测试邮件样本
├── PhishMMF-main/         # PhishMMF 训练数据
└── README.md
```

## 🤖 模型说明

### 简化 PhishMMF 模型

基于 PhishMMF 数据集训练的简化版本，只使用 35 个可从邮件中直接提取的特征：

**特征类别**：
- 文本特征（24维）：主题、发件人、正文分析
- URL 基础特征（11维）：域名、路径、参数分析

**性能指标**：
- 准确率：96%
- AUC-ROC：0.9853 (RF), 0.9876 (XGB)
- F1-Score：0.96

**优势**：
- ✅ 不依赖外部数据（URL OSINT、网站截图）
- ✅ 可以自动化提取特征
- ✅ 毫秒级响应
- ✅ 成本低

### 重新训练模型

如果需要重新训练模型：

```bash
cd backend
python train_phishmmf_model.py
```

训练数据来自 [PhishMMF](https://github.com/phishmmf/phishmmf) 项目。

## 🔧 开发

### 添加新的检测方法

1. 在 `backend/app/` 中创建新的检测模块
2. 在 `backend/app/routers/detection.py` 中添加路由
3. 更新前端显示逻辑

### 自定义特征

编辑 `backend/app/simplified_phishmmf_features.py` 添加新特征。

## 📊 API 文档

启动后端后，访问 `http://localhost:8000/docs` 查看完整的 API 文档（Swagger UI）。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🙏 致谢

- [PhishMMF](https://github.com/phishmmf/phishmmf) - 提供训练数据集
- [FastAPI](https://fastapi.tiangolo.com/) - 后端框架
- [Vue 3](https://vuejs.org/) - 前端框架
- [scikit-learn](https://scikit-learn.org/) - 机器学习库
- [XGBoost](https://xgboost.readthedocs.io/) - 梯度提升库

## 📮 联系

如有问题或建议，请提交 Issue 或联系项目维护者。

---

**注意**：本项目仅用于学习和研究目的，请勿用于非法用途。
