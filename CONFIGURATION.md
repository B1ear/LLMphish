# 配置指南

## 配置方式

LLMPhish 支持两种配置方式：

1. **配置文件**（推荐）：`backend/config.json`
2. **环境变量**：优先级高于配置文件

## 配置文件

### 创建配置文件

```bash
cd backend
cp config.example.json config.json
```

### 配置项说明

```json
{
  "llm": {
    // 阿里云 DashScope API Key（可选）
    // 获取地址: https://dashscope.console.aliyun.com/
    "dashscope_api_key": "",
    
    // DeepSeek API Key（可选）
    // 获取地址: https://platform.deepseek.com/
    "deepseek_api_key": ""
  },
  "server": {
    // 服务器监听地址
    "host": "0.0.0.0",
    
    // 服务器端口
    "port": 8000,
    
    // 日志级别: DEBUG, INFO, WARNING, ERROR
    "log_level": "INFO"
  },
  "detection": {
    // 最大上传文件大小（MB）
    "max_upload_size_mb": 10,
    
    // 会话过期时间（秒）
    "session_expire_seconds": 3600
  }
}
```

## 环境变量

环境变量的优先级高于配置文件。

### LLM API Keys

```bash
# 阿里云 DashScope (Qwen)
export DASHSCOPE_API_KEY=your_key_here
# 或
export QWEN_API_KEY=your_key_here

# DeepSeek
export DEEPSEEK_API_KEY=your_key_here
```

### 服务器配置

```bash
# 服务器主机
export SERVER_HOST=0.0.0.0

# 服务器端口
export SERVER_PORT=8000

# 日志级别
export SERVER_LOG_LEVEL=INFO
```

### 检测配置

```bash
# 最大上传大小（MB）
export DETECTION_MAX_UPLOAD_SIZE_MB=10

# 会话过期时间（秒）
export DETECTION_SESSION_EXPIRE_SECONDS=3600
```

## 配置优先级

1. **环境变量**（最高优先级）
2. **配置文件** `backend/config.json`
3. **默认值**（最低优先级）

例如，如果同时设置了：
- 配置文件：`"dashscope_api_key": "key_from_file"`
- 环境变量：`DASHSCOPE_API_KEY=key_from_env`

系统将使用环境变量的值 `key_from_env`。

## LLM 配置

### 不使用 LLM

如果不需要 LLM 检测功能，可以不配置 API Keys。系统将：
- 跳过 LLM 语义特征提取
- 跳过 LLM 辅助检测
- 仅使用机器学习模型和规则检测

### 使用单个 LLM

可以只配置一个 LLM：

```json
{
  "llm": {
    "dashscope_api_key": "your_key_here",
    "deepseek_api_key": ""
  }
}
```

系统将只使用配置了 API Key 的 LLM。

### 使用多个 LLM

配置多个 LLM 可以实现：
- 主 LLM 失败时自动切换到备用 LLM
- 更高的可用性

```json
{
  "llm": {
    "dashscope_api_key": "your_dashscope_key",
    "deepseek_api_key": "your_deepseek_key"
  }
}
```

## 安全建议

### 保护配置文件

1. **不要提交到 Git**

   `config.json` 已在 `.gitignore` 中，不会被提交。

2. **设置文件权限**

   ```bash
   chmod 600 backend/config.json
   ```

3. **使用环境变量（生产环境）**

   在生产环境中，推荐使用环境变量而不是配置文件。

### API Key 管理

1. **定期轮换**：定期更换 API Keys
2. **最小权限**：只授予必要的权限
3. **监控使用**：监控 API 调用量和费用
4. **分离环境**：开发和生产使用不同的 Keys

## 配置验证

启动服务时，系统会自动验证配置：

```bash
cd backend
python run_server.py
```

输出示例：

```
✅ 配置文件加载成功: /path/to/backend/config.json
✅ DashScope (Qwen) 客户端初始化成功
✅ DeepSeek 客户端初始化成功
```

如果配置有问题，会显示警告：

```
⚠️  配置文件不存在: /path/to/backend/config.json
⚠️  DashScope API Key 未配置
⚠️  DeepSeek API Key 未配置
```

## 配置示例

### 开发环境

```json
{
  "llm": {
    "dashscope_api_key": "sk-dev-xxx",
    "deepseek_api_key": ""
  },
  "server": {
    "host": "127.0.0.1",
    "port": 8000,
    "log_level": "DEBUG"
  },
  "detection": {
    "max_upload_size_mb": 5,
    "session_expire_seconds": 1800
  }
}
```

### 生产环境

使用环境变量：

```bash
export DASHSCOPE_API_KEY=sk-prod-xxx
export DEEPSEEK_API_KEY=sk-prod-yyy
export SERVER_HOST=0.0.0.0
export SERVER_PORT=8000
export SERVER_LOG_LEVEL=INFO
```

## 故障排查

### LLM 不可用

**问题**：LLM 检测功能不工作

**检查**：
1. 确认 API Key 已配置
2. 检查 API Key 是否有效
3. 查看服务启动日志
4. 测试 API 连接

### 配置未生效

**问题**：修改配置后没有生效

**解决**：
1. 重启服务
2. 检查环境变量是否覆盖了配置文件
3. 验证 JSON 格式是否正确

### 权限问题

**问题**：无法读取配置文件

**解决**：
```bash
chmod 644 backend/config.json
```

## 更多帮助

- [README.md](README.md) - 快速开始
- [DEPLOYMENT.md](DEPLOYMENT.md) - 部署指南
- [Issues](https://github.com/B1ear/LLMphish/issues) - 提交问题
