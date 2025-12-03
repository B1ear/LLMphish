# 部署指南

本文档介绍如何在不同环境中部署 LLMPhish。

## 目录

- [开发环境](#开发环境)
- [生产环境](#生产环境)
- [Docker 部署](#docker-部署)
- [云平台部署](#云平台部署)
- [性能优化](#性能优化)

## 开发环境

### 快速启动

#### 后端

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run_server.py
```

后端将在 `http://localhost:8000` 运行

#### 前端

```bash
cd frontend
npm install
npm run dev
```

前端将在 `http://localhost:5173` 运行

### 环境变量

创建 `.env` 文件（可选）：

```bash
# LLM API Keys (可选)
DASHSCOPE_API_KEY=your_key_here
DEEPSEEK_API_KEY=your_key_here

# 服务器配置
HOST=0.0.0.0
PORT=8000
```

## 生产环境

### 系统要求

- **操作系统**: Linux (推荐 Ubuntu 20.04+)
- **Python**: 3.8+
- **Node.js**: 16+
- **内存**: 最低 2GB，推荐 4GB+
- **磁盘**: 最低 10GB

### 后端部署

#### 1. 安装依赖

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 2. 使用 Gunicorn + Uvicorn

安装 Gunicorn:

```bash
pip install gunicorn
```

启动服务:

```bash
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log
```

#### 3. 使用 Systemd 管理服务

创建 `/etc/systemd/system/llmphish.service`:

```ini
[Unit]
Description=LLMPhish Backend Service
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/path/to/LLMPhish/backend
Environment="PATH=/path/to/LLMPhish/backend/venv/bin"
ExecStart=/path/to/LLMPhish/backend/venv/bin/gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务:

```bash
sudo systemctl daemon-reload
sudo systemctl start llmphish
sudo systemctl enable llmphish
sudo systemctl status llmphish
```

### 前端部署

#### 1. 构建

```bash
cd frontend
npm install
npm run build
```

构建产物在 `dist/` 目录

#### 2. 使用 Nginx

安装 Nginx:

```bash
sudo apt install nginx
```

配置 `/etc/nginx/sites-available/llmphish`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端
    location / {
        root /path/to/LLMPhish/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # 后端 API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 静态文件缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        root /path/to/LLMPhish/frontend/dist;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

启用配置:

```bash
sudo ln -s /etc/nginx/sites-available/llmphish /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 3. HTTPS (推荐)

使用 Let's Encrypt:

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## Docker 部署

### 创建 Dockerfile

#### 后端 Dockerfile

创建 `backend/Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 前端 Dockerfile

创建 `frontend/Dockerfile`:

```dockerfile
FROM node:16-alpine as build

WORKDIR /app

# 安装依赖
COPY package*.json ./
RUN npm ci

# 构建
COPY . .
RUN npm run build

# 生产环境
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Docker Compose

创建 `docker-compose.yml`:

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DASHSCOPE_API_KEY=${DASHSCOPE_API_KEY}
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
    volumes:
      - ./backend/models:/app/models
      - ./backend/logs:/app/logs
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped
```

启动:

```bash
docker-compose up -d
```

## 云平台部署

### AWS

#### 使用 EC2

1. 启动 EC2 实例 (t2.medium 或更高)
2. 安装 Docker 和 Docker Compose
3. 克隆项目并使用 Docker Compose 部署
4. 配置安全组开放 80 和 443 端口

#### 使用 ECS

1. 构建 Docker 镜像并推送到 ECR
2. 创建 ECS 任务定义
3. 创建 ECS 服务
4. 配置 Application Load Balancer

### Azure

#### 使用 App Service

1. 创建 App Service (Python 3.10)
2. 配置部署中心连接 GitHub
3. 设置环境变量
4. 部署应用

### Google Cloud

#### 使用 Cloud Run

1. 构建 Docker 镜像
2. 推送到 Google Container Registry
3. 部署到 Cloud Run
4. 配置自定义域名

## 性能优化

### 后端优化

#### 1. 使用多进程

```bash
gunicorn app.main:app \
  --workers $(nproc) \
  --worker-class uvicorn.workers.UvicornWorker
```

#### 2. 启用缓存

在 `app/main.py` 中添加:

```python
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis

@app.on_event("startup")
async def startup():
    redis = aioredis.from_url("redis://localhost")
    FastAPICache.init(RedisBackend(redis), prefix="llmphish-cache")
```

#### 3. 模型预加载

确保模型在启动时加载，而不是首次请求时。

### 前端优化

#### 1. 代码分割

在 `vite.config.ts` 中:

```typescript
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor': ['vue', 'axios'],
        }
      }
    }
  }
})
```

#### 2. 启用 Gzip

在 Nginx 配置中:

```nginx
gzip on;
gzip_types text/plain text/css application/json application/javascript;
gzip_min_length 1000;
```

### 数据库优化

如果使用数据库存储结果:

- 添加适当的索引
- 使用连接池
- 定期清理过期数据

## 监控和日志

### 日志管理

使用 logrotate 管理日志:

创建 `/etc/logrotate.d/llmphish`:

```
/path/to/LLMPhish/backend/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload llmphish
    endscript
}
```

### 监控

推荐使用:

- **Prometheus + Grafana**: 系统指标监控
- **Sentry**: 错误追踪
- **ELK Stack**: 日志分析

## 备份

### 模型文件

```bash
# 备份模型
tar -czf models-backup-$(date +%Y%m%d).tar.gz backend/models/

# 恢复模型
tar -xzf models-backup-20250101.tar.gz
```

### 配置文件

定期备份:
- `.env` 文件
- Nginx 配置
- Systemd 服务文件

## 故障排查

### 后端无法启动

1. 检查日志: `tail -f backend/logs/error.log`
2. 验证依赖: `pip list`
3. 检查端口占用: `lsof -i :8000`

### 前端无法访问

1. 检查 Nginx 状态: `sudo systemctl status nginx`
2. 查看 Nginx 日志: `tail -f /var/log/nginx/error.log`
3. 验证构建产物: `ls frontend/dist/`

### 模型加载失败

1. 检查模型文件是否存在
2. 验证文件权限
3. 查看内存使用情况

## 安全建议

- 使用 HTTPS
- 设置防火墙规则
- 定期更新依赖
- 使用环境变量存储敏感信息
- 启用 API 限流
- 定期备份数据

## 更新部署

```bash
# 拉取最新代码
git pull origin main

# 更新后端
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart llmphish

# 更新前端
cd ../frontend
npm install
npm run build
sudo systemctl reload nginx
```

## 支持

如遇到部署问题，请:
- 查看 [Issues](https://github.com/yourusername/LLMPhish/issues)
- 提交新的 Issue
- 联系项目维护者
