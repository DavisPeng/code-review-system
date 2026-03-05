# AI Code Review System

智能代码审查系统，为 C/C++ 项目提供 AI 驱动的代码审查服务。

## 功能特性

- 🤖 **AI 智能审查**: 使用 Claude 或 OpenAI API 进行智能代码分析
- 🔍 **静态分析**: 集成 clang-tidy 和 cppcheck
- 📊 **Web Dashboard**: 实时查看审查结果和统计
- 🔔 **飞书通知**: 审查完成后自动发送通知
- 🔄 **GitHub Webhook**: 自动触发代码审查
- 📦 **Docker 部署**: 一键部署到生产环境

## 技术栈

- **后端**: Python FastAPI + Celery + Redis
- **前端**: React + TypeScript + Ant Design
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **AI**: Anthropic Claude API / OpenAI API

## 快速开始

### 本地开发

1. 克隆项目
```bash
git clone https://github.com/DavisPeng/code-review-system.git
cd code-review-system
```

2. 安装后端依赖
```bash
cd backend
pip install -r requirements.txt
```

3. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 填入你的 API keys
```

4. 启动后端
```bash
cd backend
uvicorn app.main:app --port 8000 --reload
```

5. 安装前端依赖
```bash
cd frontend
npm install
```

6. 启动前端
```bash
cd frontend
npm run dev
```

7. 访问
- 前端: http://localhost:5173
- API 文档: http://localhost:8000/docs

### Docker 部署

```bash
docker-compose up --build
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
│   │   ├── utils/        # 工具函数
│   │   └── prompts/      # AI 提示词
│   ├── tests/            # 测试
│   ├── scripts/          # 脚本
│   └── alembic/          # 数据库迁移
├── frontend/
│   ├── src/
│   │   ├── components/  # 组件
│   │   ├── pages/        # 页面
│   │   ├── services/     # API 服务
│   │   └── assets/       # 静态资源
│   └── ...
├── docker-compose.yml
├── .env.example
└── README.md
```

## 配置说明

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATABASE_URL` | 数据库连接字符串 | `sqlite:///./data.db` |
| `REDIS_URL` | Redis 连接地址 | `redis://localhost:6379/0` |
| `AI_PROVIDER` | AI 提供商 | `anthropic` |
| `ANTHROPIC_API_KEY` | Anthropic API Key | - |
| `OPENAI_API_KEY` | OpenAI API Key | - |
| `GITHUB_WEBHOOK_SECRET` | GitHub Webhook 密钥 | - |
| `FEISHU_WEBHOOK_URL` | 飞书 Webhook URL | - |

### GitHub Webhook 配置

1. 在 GitHub 仓库设置中添加 Webhook
2. Payload URL: `https://your-domain.com/api/v1/webhooks/github`
3. Content type: `application/json`
4. 添加事件: `push`, `pull requests`

## 开发任务

项目按照 TASK-01 到 TASK-17 的顺序开发：

- TASK-01: 项目脚手架初始化 ✅
- TASK-02: 数据库模型与迁移
- TASK-03: Git Webhook 接收与解析
- TASK-04: Git Diff 提取服务
- TASK-05: 静态分析引擎集成
- TASK-06: AI Review 引擎
- TASK-07: Review Pipeline 编排
- TASK-08: Review 结果 API
- TASK-09: 规则配置管理 API
- TASK-10: 飞书通知服务
- TASK-11: 前端 Dashboard
- TASK-12: 前端 Review 详情页
- TASK-13: 前端规则配置页面
- TASK-14: 前端通知配置页面
- TASK-15: 用户认证与权限
- TASK-16: Docker 部署与文档
- TASK-17: 端到端测试与优化

## 许可证

MIT License