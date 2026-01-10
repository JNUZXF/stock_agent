# 股票分析智能体 - 生产级后端系统

## 项目简介

这是一个基于豆包API的股票分析智能体后端系统,采用生产级架构设计,支持API版本管理、完整日志系统、数据库持久化、监控告警和全面测试覆盖。

## 技术栈

- **框架**: FastAPI 0.104+
- **数据库**: PostgreSQL 15 + SQLAlchemy 2.0 (异步)
- **缓存**: Redis 7
- **AI模型**: 豆包 API
- **数据源**: 雪球API (pysnowball)
- **监控**: Prometheus
- **日志**: 结构化JSON日志
- **测试**: pytest + pytest-asyncio

## 架构设计

### 分层架构

```
┌─────────────────────────────────────┐
│      API Layer (表现层)              │
│  - Routes (v1/v2)                   │
│  - Middleware (日志/错误/指标)       │
│  - Schemas (Pydantic模型)           │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│   Service Layer (业务逻辑层)         │
│  - AgentService                     │
│  - ConversationService              │
│  - StockService                     │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Repository Layer (数据访问层)       │
│  - ConversationRepository           │
│  - MessageRepository                │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│      Database (PostgreSQL)          │
└─────────────────────────────────────┘
```

### 目录结构

```
backend/
├── app/                    # 应用核心代码
│   ├── api/               # API层
│   │   ├── v1/           # v1版本API
│   │   │   ├── routes/   # 路由
│   │   │   └── schemas/  # 数据模型
│   │   └── middleware/   # 中间件
│   ├── core/             # 核心基础设施
│   │   ├── config.py     # 配置管理
│   │   ├── logging.py    # 日志系统
│   │   ├── database.py   # 数据库
│   │   ├── cache.py      # 缓存
│   │   └── metrics.py    # 监控指标
│   ├── services/         # 业务逻辑层
│   ├── repositories/     # 数据访问层
│   ├── models/           # 数据库模型
│   ├── agents/           # Agent模块
│   │   ├── tools/        # Agent工具
│   │   ├── prompts.py    # 提示词
│   │   └── stock_agent.py
│   └── utils/            # 工具函数
├── tests/                # 测试
│   ├── unit/            # 单元测试
│   ├── integration/     # 集成测试
│   └── e2e/             # 端到端测试
├── scripts/             # 运维脚本
├── logs/                # 日志目录
└── alembic/             # 数据库迁移
```

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
cd backend

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

复制环境配置模板:

```bash
cp env.template .env
```

编辑`.env`文件,填入必要的配置:

```env
# 豆包API
DOUBAO_API_KEY=your_api_key_here

# 雪球API
XQ_A_TOKEN=your_token_here

# 数据库
DATABASE_URL=postgresql+asyncpg://admin:password@localhost:5432/stock_analysis

# Redis
REDIS_URL=redis://localhost:6379/0
```

### 3. 启动依赖服务

使用Docker Compose启动PostgreSQL和Redis:

```bash
# 返回项目根目录
cd ..

# 启动服务
docker-compose -f docker-compose.dev.yml up -d postgres redis
```

### 4. 初始化数据库

```bash
cd backend
python scripts/init_db.py
```

### 5. 启动应用

```bash
# 开发模式(热重载)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或使用
python -m app.main
```

### 6. 访问API文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- 健康检查: http://localhost:8000/api/v1/health

## API端点

### v1 API

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/v1/chat` | POST | 聊天接口(SSE流式) |
| `/api/v1/conversations` | GET | 获取会话列表 |
| `/api/v1/conversations/{id}` | GET | 获取会话详情 |
| `/api/v1/conversations` | POST | 创建会话 |
| `/api/v1/conversations/{id}` | PATCH | 更新会话 |
| `/api/v1/conversations/{id}` | DELETE | 删除会话 |
| `/api/v1/health` | GET | 健康检查 |
| `/api/v1/health/liveness` | GET | 存活探针 |
| `/api/v1/health/readiness` | GET | 就绪探针 |

## 数据迁移

将现有`files/`目录下的会话数据迁移到数据库:

```bash
python scripts/migrate_files_to_db.py
```

迁移完成后,原文件会保留作为备份。

## 测试

```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit -m unit

# 运行集成测试
pytest tests/integration -m integration

# 运行E2E测试
pytest tests/e2e -m e2e

# 生成覆盖率报告
pytest --cov=app --cov-report=html
```

## 日志系统

### 日志级别

- **DEBUG**: 详细调试信息
- **INFO**: 一般信息(默认)
- **WARNING**: 警告信息
- **ERROR**: 错误信息
- **CRITICAL**: 严重错误

### 日志文件

- `logs/app/app.log`: 应用日志
- `logs/error/error.log`: 错误日志
- `logs/access/access.log`: 访问日志

### 日志格式

生产环境使用JSON格式,包含:
- 时间戳
- 日志级别
- 模块名称
- 请求ID
- 消息内容
- 上下文信息

## 监控指标

### Prometheus指标

应用暴露以下指标:

**请求指标**:
- `http_requests_total`: HTTP请求总数
- `http_request_duration_seconds`: 请求延迟

**业务指标**:
- `conversations_total`: 会话总数
- `messages_total`: 消息总数
- `tool_calls_total`: 工具调用总数

**系统指标**:
- `db_pool_size`: 数据库连接池大小
- `cache_hits_total`: 缓存命中数
- `errors_total`: 错误总数

## 配置说明

### 核心配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `ENVIRONMENT` | 运行环境 | development |
| `DEBUG` | 调试模式 | True |
| `LOG_LEVEL` | 日志级别 | INFO |
| `DATABASE_POOL_SIZE` | 数据库连接池大小 | 20 |
| `REDIS_POOL_SIZE` | Redis连接池大小 | 10 |
| `CACHE_TTL` | 缓存过期时间(秒) | 300 |

## 生产部署

### 使用Docker

```bash
# 构建镜像
docker build -t stock-analysis-backend .

# 运行容器
docker run -d \
  --name stock-backend \
  -p 8000:8000 \
  --env-file .env \
  stock-analysis-backend
```

### 使用Docker Compose

```bash
# 生产环境
docker-compose -f docker-compose.yml up -d

# 开发环境
docker-compose -f docker-compose.dev.yml up -d
```

### 环境变量

生产环境必须设置:
- `ENVIRONMENT=production`
- `DEBUG=False`
- `LOG_LEVEL=INFO`
- `DATABASE_URL`: 生产数据库URL
- `REDIS_URL`: 生产Redis URL
- `DOUBAO_API_KEY`: 豆包API密钥
- `XQ_A_TOKEN`: 雪球API Token

## 性能优化

### 数据库优化

- 使用连接池(默认20个连接)
- 异步查询(asyncpg)
- 适当的索引
- 查询结果缓存

### 缓存策略

- 股票数据缓存(5分钟)
- Agent实例缓存
- 热点会话缓存

### 并发处理

- 异步I/O(FastAPI + asyncio)
- 流式响应(SSE)
- 连接池管理

## 故障排查

### 常见问题

1. **数据库连接失败**
   - 检查PostgreSQL是否运行
   - 验证DATABASE_URL配置
   - 检查网络连接

2. **Redis连接失败**
   - 检查Redis是否运行
   - 验证REDIS_URL配置
   - 应用会降级到无缓存模式

3. **API调用失败**
   - 检查DOUBAO_API_KEY
   - 检查XQ_A_TOKEN
   - 查看日志文件

### 日志查看

```bash
# 查看应用日志
tail -f logs/app/app.log

# 查看错误日志
tail -f logs/error/error.log

# 查看访问日志
tail -f logs/access/access.log
```

## 开发指南

### 添加新功能

1. **创建数据模型** (`app/models/`)
2. **创建Repository** (`app/repositories/`)
3. **创建Service** (`app/services/`)
4. **创建API路由** (`app/api/v1/routes/`)
5. **编写测试** (`tests/`)

### 代码规范

- 使用类型提示
- 遵循PEP 8
- 单文件不超过300行
- 函数不超过50行
- 添加文档字符串

### 提交规范

```
feat: 添加新功能
fix: 修复bug
docs: 更新文档
refactor: 重构代码
test: 添加测试
chore: 构建/工具变动
```

## 许可证

MIT License

## 联系方式

如有问题,请提交Issue或联系维护者。
