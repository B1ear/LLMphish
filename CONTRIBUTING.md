# 贡献指南

感谢你对 LLMPhish 项目的关注！我们欢迎各种形式的贡献。

## 如何贡献

### 报告 Bug

如果你发现了 bug，请：

1. 检查 [Issues](https://github.com/yourusername/LLMPhish/issues) 确认问题是否已被报告
2. 如果没有，创建一个新的 Issue，包含：
   - 清晰的标题和描述
   - 重现步骤
   - 预期行为和实际行为
   - 环境信息（操作系统、Python 版本等）
   - 相关的日志或截图

### 提出新功能

如果你有新功能的想法：

1. 先创建一个 Issue 讨论
2. 说明功能的用途和价值
3. 如果可能，提供实现思路

### 提交代码

1. **Fork 项目**

2. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **编写代码**
   - 遵循项目的代码风格
   - 添加必要的注释
   - 编写测试（如果适用）

4. **提交更改**
   ```bash
   git commit -m "feat: add your feature description"
   ```
   
   提交信息格式：
   - `feat:` 新功能
   - `fix:` 修复 bug
   - `docs:` 文档更新
   - `style:` 代码格式调整
   - `refactor:` 代码重构
   - `test:` 测试相关
   - `chore:` 构建或辅助工具

5. **推送到 GitHub**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **创建 Pull Request**
   - 清晰描述你的更改
   - 关联相关的 Issue
   - 等待代码审查

## 开发环境设置

### 后端

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

## 代码规范

### Python

- 遵循 PEP 8
- 使用类型提示
- 函数和类添加文档字符串
- 保持函数简洁（单一职责）

### JavaScript/Vue

- 使用 ESLint 配置
- 组件命名使用 PascalCase
- 变量命名使用 camelCase
- 添加必要的注释

## 测试

在提交 PR 前，请确保：

- 代码能正常运行
- 没有引入新的 bug
- 相关功能已测试

## 文档

如果你的更改影响了用户使用方式：

- 更新 README.md
- 添加或更新 API 文档
- 更新相关的配置说明

## 行为准则

- 尊重所有贡献者
- 保持友好和专业
- 接受建设性的批评
- 关注项目的最佳利益

## 问题？

如有任何问题，欢迎：
- 创建 Issue
- 在 Pull Request 中提问
- 联系项目维护者

感谢你的贡献！🎉
