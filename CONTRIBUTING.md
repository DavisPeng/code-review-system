# Contributing to AI Code Review System

感谢你对本项目的兴趣！我们欢迎任何形式的贡献，包括但不限于 bug 报告、功能建议、代码提交、文档改进等。

## 行为准则

请阅读并遵守我们的 [行为准则](CODE_OF_CONDUCT.md)（如有）。尊重他人，保持友善和专业的沟通态度。

## 如何贡献

### 报告 Bug

1. 搜索现有 [Issues](https://github.com/DavisPeng/code-review-system/issues) 确保没有重复
2. 创建新 Issue，使用 `bug` 标签
3. 包含以下信息：
   - 清晰的标题和描述
   - 复现步骤
   - 预期行为 vs 实际行为
   - 环境信息（OS、Python 版本、Docker 版本等）
   - 可能的截图或日志

### 提出新功能

1. 搜索现有 Issues 和 PRs
2. 创建新 Issue，使用 `feature` 标签
3. 描述：
   - 你想实现什么功能
   - 为什么需要这个功能
   - 可能的实现方案

### 提交代码

#### 开发环境设置

```bash
# 克隆项目
git clone https://github.com/DavisPeng/code-review-system.git
cd code-review-system

# 创建开发分支
git checkout -b feature/your-feature-name
```

#### 后端开发

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 运行测试
pytest tests/ -v

# 启动开发服务器
uvicorn app.main:app --reload
```

#### 前端开发

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```

#### Docker 开发

```bash
# 启动所有服务
docker-compose up --build

# 运行后端测试
docker-compose exec backend pytest tests/ -v

# 查看日志
docker-compose logs -f backend
```

### 提交 Pull Request

1. 保持代码风格一致
   - Python: 遵循 PEP 8，使用 Black 格式化
   - TypeScript: 遵循项目 ESLint 配置

2. 提交信息规范

   使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

   ```
   <type>(<scope>): <description>

   [optional body]

   [optional footer]
   ```

   类型：
   - `feat`: 新功能
   - `fix`: Bug 修复
   - `docs`: 文档更新
   - `style`: 代码格式（不影响功能）
   - `refactor`: 重构
   - `test`: 测试相关
   - `chore`: 构建过程或辅助工具变动

3. PR 描述模板

   ```markdown
   ## 描述
   简要描述这个 PR 做了什么

   ## 改动类型
   - [ ] Bug 修复
   - [ ] 新功能
   - [ ] 破坏性改动
   - [ ] 文档更新

   ## 测试
   - [ ] 单元测试通过
   - [ ] 手动测试通过

   ## 截图（如适用）
   ```

4. 确保所有测试通过

   ```bash
   # 后端测试
   pytest tests/ -v --cov=app

   # 前端测试
   npm test
   ```

## 项目结构

```
code-review-system/
├── backend/
│   ├── app/
│   │   ├── api/          # API 路由
│   │   ├── models/       # 数据库模型
│   │   ├── services/     # 业务逻辑
│   │   ├── tasks/        # Celery 任务
│   │   └── prompts/      # AI 提示词
│   ├── tests/            # 测试
│   └── scripts/          # 脚本
├── frontend/
│   ├── src/
│   │   ├── pages/        # 页面组件
│   │   ├── services/     # API 服务
│   │   └── utils/        # 工具函数
│   └── ...
└── ...
```

## 开发规范

### 后端规范

- 使用 Pydantic 进行数据验证
- 所有 API 端点添加类型注解和文档字符串
- 使用 async/await 处理 I/O 操作
- 数据库操作使用 SQLAlchemy ORM

### 前端规范

- 使用 TypeScript 严格模式
- 组件使用函数式组件 + Hooks
- 使用 Ant Design 组件库
- 遵循 React 最佳实践

### Git 规范

- 保持提交粒度适中
- 每个提交应该是原子性的
- 提交信息清晰描述改动内容
- 不要提交敏感信息（API Keys、密码等）

## 里程碑

项目按照 TASK-01 到 TASK-17 的顺序开发，详见 [README.md](README.md)。

## 许可证

本项目使用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。

## 联系方式

- 提交 Issue
- 加入讨论（在 Issue 中 @ maintainer）

感谢你的贡献！🎉