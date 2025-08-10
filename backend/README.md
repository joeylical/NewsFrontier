# NewsFrontier Backend

这是NewsFrontier项目的后端API服务器，使用FastAPI实现。

## 快速开始

### 安装依赖
```bash
uv sync
```

### 启动开发服务器
```bash
# 方法1：直接运行
uv run python main.py

# 方法2：使用uvicorn
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 方法3：运行开发脚本
uv run python run_dev.py
```

服务器将在 http://localhost:8000 启动

## API文档

启动服务器后，可以访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 测试数据

### 默认用户
- 用户名: `testuser`  
- 密码: `password123`
- 邮箱: `test@example.com`

### 测试登录
```bash
curl -X POST "http://localhost:8000/api/login" \
     -H "Content-Type: application/json" \
     -d '{"username":"testuser","password":"password123"}'
```

## API端点

- `POST /api/login` - 用户登录
- `POST /api/logout` - 用户登出
- `POST /api/register` - 用户注册
- `GET /api/today` - 今日新闻摘要
- `GET /api/topics` - 获取话题列表
- `POST /api/topics` - 创建新话题
- `GET /api/topic/{id}` - 获取话题详情和集群
- `GET /api/cluster/{id}` - 获取集群详情和文章