# 介绍

这是 NewsFrontier 的根目录。

NewsFrontier 是一个智能新闻聚合与分析平台，为个人用户获取、分析、分类和总结新闻文章。该系统通过先进的聚类和机器学习技术提供个性化的新闻洞察。

# 工作原理

## 概述
NewsFrontier 通过多阶段管道运行，将原始 RSS 订阅源转换为有组织的、摘要化的新闻聚类：

1. **数据收集**：用户可以通过 Web 界面添加感兴趣的主题和 RSS 源
2. **RSS 获取**：系统定期获取 RSS 源并将新闻文章存储在 PostgreSQL 数据库中，包含完整元数据（URL、标题、内容、时间戳等）
3. **内容摘要**：专用工作进程使用 LLM 技术生成每篇文章的简洁摘要
4. **向量嵌入**：嵌入服务使用现代嵌入 API 将文章摘要转换为高维向量
5. **聚类分析**：程序会尝试创建cluster，并且把文章归类到cluster中
6. **API 层**：基于 FastAPI 的后端为前端应用程序提供 RESTful 接口

## AI 管道

AI 处理管道通过智能内容分析和上下文感知将原始 RSS 文章转换为结构化的聚类驱动新闻洞察：

### 1. 主题嵌入生成
系统为用户定义的主题创建向量嵌入，使用 Google 的 gemini-embedding-001 模型将其语义含义编码为高维向量。这些 768 维主题嵌入在整个处理管道中作为内容分类和相关性评分的参考点。

### 2. 文章处理和摘要
每篇获取的文章都经过全面的两阶段处理：
* **内容摘要**：文章通过 Google Gemini LLM API（gemini-2.0-flash-lite）处理，生成捕获关键点、上下文并保持锚链接引用的简洁结构化摘要
* **向量生成**：文章摘要使用 gemini-embedding-001 转换为 768 维向量嵌入，用于语义相似性计算和聚类操作

### 3. 智能聚类检测和分类
在处理每篇文章时，系统采用复杂的多阶段聚类方法：

#### 主题相关性评估
* **初步过滤**：系统首先使用向量相似性计算确定文章是否与任何用户定义的主题在语义上相似
* **相关性评分**：满足相似性阈值的文章对特定主题进行相关性评分

#### 聚类分配决策
对于每个相关主题，系统按顺序处理聚类：
* **现有聚类匹配**：当主题内存在相似聚类时，文章会根据嵌入距离分类并分配给语义上最相似的聚类
* **相似性阈值**：使用可配置的相似性阈值（默认：主题 0.62，聚类 0.7）确保高质量分组

#### 智能新聚类创建
当文章不匹配现有聚类时：
* **基于 LLM 的分析**：系统使用 Gemini-2.5-Pro 分析文章内容，确定是否代表真正的新聚类或发展
* **上下文感知创建**：LLM 考虑现有聚类标题、描述和主题层次结构做出智能聚类决策
* **动态关联**：创建具有 AI 生成标题和描述的新聚类，并将文章与新聚类关联，具有适当的相关性评分

### 4. 聚类演化和关系管理
* **聚类更新**：随着新相关文章的添加，现有聚类动态更新
* **跨聚类分析**：系统识别主题内不同聚类之间的关系
* **时间跟踪**：聚类演化随时间跟踪，以保持聚类一致性和相关性

### 5. 每日摘要创建
使用上下文信息生成个性化的每日新闻摘要：
* **系统范围提示**：定义摘要格式、语调和 markdown 链接约定的结构化提示
* **用户偏好**：个人主题兴趣、订阅优先级和个性化摘要提示
* **历史上下文**：之前的每日摘要和用户交互模式
* **聚类亮点**：今日顶级聚类和发展的精选亮点，包含内部仪表板链接

### 6. 每日封面图片生成
通过使用 Imagen-3.0-Generate-002 的 AI 驱动图像生成创建视觉内容：
* **情感色调**：从每日摘要内容中提取的核心情感和情绪
* **视觉场景**：来自新闻聚类的具体设置、情况和上下文元素
* **关键主题**：在新闻中识别的主要参与者、对象和实体，不包含文本叠加
* **叙事元素**：概括当天最重要发展的引人注目的视觉故事

### AI 模型和应用

AI 管道利用 Google AI 套件中的多个专用模型，每个模型都针对特定任务进行了优化：

| 模型 | 类型 | 应用 |
|------|------|------|
| **gemini-2.0-flash-lite** | 指令遵循 | 文章摘要<br/>图像生成提示生成 |
| **gemini-2.5-pro** | 指令遵循 | 创建新聚类<br/>每日摘要 |
| **imagen-3.0-generate-002** | 图像生成 | 每日摘要封面图片 |
| **gemini-embedding-001** | 嵌入 | 文章嵌入<br/>主题嵌入<br/>聚类嵌入 |

这种多模型方法确保每个特定任务的最佳性能，同时保持整个 AI 处理管道的一致性。

# 项目结构

## 目录概览

### 核心应用程序
* **`frontend/`** - 使用 TypeScript 的 Next.js Web 应用程序
  * **技术栈**：Next.js 15+ 搭配 App Router、TypeScript、TailwindCSS + DaisyUI
  * **架构**：具有服务器端渲染和客户端交互的 React 组件
  * **身份验证**：基于 JWT 的身份验证和中间件保护
  * **关键功能**：
    - 桌面和移动设备的响应式设计
    - 具有每日新闻摘要的交互式仪表板
    - 分层新闻浏览（主题 → 聚类 → 文章）
    - 实时更新和数据可视化
    - 系统管理的管理界面
    - RSS 订阅源管理和配置
    - 用户设置和偏好管理
  * **包管理器**：pnpm 用于高效的依赖管理

* **`backend/`** - 基于 FastAPI 的 REST API 服务器
  * **技术栈**：Python 3.11+、FastAPI、SQLAlchemy ORM、PostgreSQL、JWT 身份验证
  * **架构**：具有依赖注入和中间件管道的异步优先微服务
  * **核心组件**：
    - 具有自动 OpenAPI 文档生成的 FastAPI 应用程序
    - 基于 JWT 的身份验证和 bcrypt 密码哈希
    - 跨域前端集成的 CORS 中间件
    - 具有性能跟踪的请求/响应日志记录中间件
    - 具有详细错误日志记录的全局异常处理
    - 与共享 newsfrontier-lib 的数据库操作集成
  * **关键功能**：
    - 完整的用户身份验证系统（登录、注册、注销）
    - 具有日期导航的每日个性化新闻摘要
    - 具有 AI 生成向量嵌入的主题管理
    - 文章和聚类内容发现 API
    - RSS 订阅源订阅管理
    - 具有段落锚点插入的 HTML 文本处理
    - 爬虫和后处理通信的内部服务 API
    - 系统配置的管理端点

### 数据管道组件  
* **`scraper/`** - RSS 订阅源收集服务
  * **技术栈**：Python 3.11+、requests、feedparser、SQLAlchemy
  * **架构**：具有可配置调度的并发 RSS 获取
  * **关键功能**：
    - 具有并发获取能力的异步 RSS 解析
    - 使用 SHA256 哈希的内容去重
    - 强大的错误处理和重试机制
    - 订阅源获取操作的状态跟踪
    - 数据持久化的后端 API 集成
    - 每个订阅源的可配置获取间隔
    - 守护进程和一次性执行模式
  
* **`postprocess/`** - AI 驱动的内容分析和处理服务
  * **技术栈**：Python 3.11+、Google AI (Gemini)、scikit-learn、pgvector、FastAPI
  * **架构**：具有智能聚类和内容分析的 AI 处理管道
  * **核心职责**：
    - 分析文章内容并提取主题、实体、关键词
    - 为语义搜索生成 768 维向量嵌入
    - 使用 AI 创建文章摘要和衍生内容
    - 基于内容相似性聚类相关文章
    - 执行情感分析和可读性评分
  * **AI 集成功能**：
    - Google Gemini 模型：Gemini-2.0-Flash-Lite 用于快速摘要
    - 高级分析：Gemini-2.5-Pro 用于复杂聚类和每日摘要
    - 向量嵌入：gemini-embedding-001 用于高质量的 768 维向量
    - 聚类：基于 LLM 逻辑的上下文感知聚类决策
    - 每日摘要：具有结构化 markdown 输出的个性化新闻摘要
    - 封面图片生成：使用 Imagen 模型的 AI 生成图像描述
  * **操作功能**：
    - 守护进程和一次性执行模式
    - AI 服务不可用时的优雅降级
    - 全面的 AI 提示测试框架
    - 服务间通信的 FastAPI 内部服务器
    - 封面图片存储的 S3 集成

### 基础设施和实用程序
* **`lib/`** - 共享 Python 库和实用程序
  * **技术栈**：Python 3.11+、SQLAlchemy、pgvector、Pydantic
  * **架构**：通用功能的共享工作空间库
  * **关键组件**：
    - 所有数据库表的 SQLAlchemy ORM 模型
    - API 请求/响应验证的 Pydantic 模式
    - 具有类型安全数据库访问的 CRUD 操作
    - LLM 客户端集成（Google Generative AI）
    - 云存储操作的 S3 客户端
    - 具有 pgvector 支持的向量嵌入实用程序
  
* **`scripts/`** - 开发和部署实用程序
  * **关键脚本**：
    - `init.sql` - 具有 pgvector 扩展的 PostgreSQL 数据库模式
    - `dev.sh` / `stop-dev.sh` - 开发环境管理
    - `generate-init-sql.py` - 具有可配置向量维度的动态模式生成
    - `create-test-users.py` - 测试数据创建实用程序
    - 调试的数据库转储和恢复实用程序
    - AI 服务的系统提示模板
  
* **`data/`** - PostgreSQL 数据目录（Docker 卷）
  * 数据库容器的持久存储
  * 出于安全和性能考虑从版本控制中排除


# 系统架构

## 架构概览

NewsFrontier 遵循微服务架构，明确分离关注点：

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Database      │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│  (PostgreSQL    │
│                 │    │                 │    │   + pgvector)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                       ▲                       ▲
         │              ┌────────┴────────┐              │
         │              │                 │              │
         │       ┌─────────────┐   ┌─────────────┐       │
         │       │   Scraper   │   │ PostProcess │       │
         │       │  (RSS Feed) │   │ (AI/ML)     │       │
         └───────┤             │   │             ├───────┘
                 └─────────────┘   └─────────────┘
```

## 数据流

1. **RSS 摄取**：爬虫服务定期获取 RSS 订阅源并存储原始文章
2. **内容处理**：PostProcess 服务分析文章、生成摘要并创建嵌入  
3. **聚类**：计算向量相似性以对相关文章进行分组
4. **API 层**：后端通过 RESTful 端点公开处理过的数据
5. **用户界面**：前端使用 API 呈现有组织的新闻聚类

## 工作空间配置

项目在根目录中使用 **uv 工作空间** 结构，带有 Git 版本控制。

### 基础设施文件
* **`docker-compose.yml`** - 容器编排
  * **数据库**：支持向量扩展的 `pgvector/pgvector:pg17` 容器
    * 使用 `scripts/init.sql` 初始化模式设置
    * 持久卷映射到 `./data/` 目录
  * **后端**：Python FastAPI 应用程序容器
  * **前端**：Node.js Next.js 应用程序容器
  * **网络**：服务通信的内部 Docker 网络

* **`shell.nix`** - Nix 开发环境定义
  * 在不同机器上提供一致的开发工具
  * 包括 Python、Node.js、PostgreSQL 客户端和其他依赖项
  
* **`.vimrc.lua`** - 项目特定的 Neovim 配置
  * Python 和 TypeScript 开发的自定义设置
  * 集成调试和测试工作流程

# 技术规格

## 技术栈

### 后端服务
* **语言**：Python 3.11+
* **框架**：FastAPI 用于高性能异步 API 开发，具有自动 OpenAPI 文档
* **架构**：具有模块化中间件管道的单文件应用程序
* **数据库集成**： 
  * **PostgreSQL 17** 带有用于向量操作的 pgvector 扩展
  * **SQLAlchemy ORM** 通过共享 newsfrontier-lib 包
  * **数据库会话管理** 具有依赖注入
* **安全性**： 
  * **JWT 身份验证** 具有可配置过期
  * **bcrypt 密码哈希** 具有盐轮次
  * **CORS 中间件** 用于跨域请求
* **项目结构**：具有最小文件占用的 UV 工作空间成员

#### 关键模块
* **`main.py`** - 具有完整 API 实现的 FastAPI 应用程序入口点
  * 身份验证端点（登录、注册、注销、用户管理）
  * 具有日期导航和日历集成的每日摘要 API
  * 具有 AI 向量嵌入生成的主题管理
  * 内容发现 API（主题、聚类、文章）
  * RSS 订阅源订阅管理
  * 爬虫和后处理通信的内部服务 API
  * 系统配置的管理端点
  * 综合中间件管道（CORS、日志记录、异常处理）

* **`text_processor.py`** - HTML 内容处理实用程序
  * 段落锚点 ID 生成（P-xxxxx 格式）
  * 多段落内容的 HTML 锚点插入
  * 具有锚点元数据的段落提取
  * 锚点 ID 验证和文本处理分析
  * 支持 SEN-xxxxx 和 P-xxxxx 锚点格式

* **共享依赖项**（通过 newsfrontier-lib）：
  * 所有数据库实体的 SQLAlchemy ORM 模型
  * 请求/响应验证的 Pydantic 模式
  * 具有类型安全数据库访问的 CRUD 操作
  * 主题嵌入生成的 AI 客户端集成

#### API

后端提供使用 FastAPI 构建的综合 RESTful API，具有自动 OpenAPI 文档和异步请求处理。

**基础 URL**：`/api`

##### 身份验证端点
* **`POST /api/login`** - 用户身份验证和会话创建
  * 请求：`{username: string, password: string}`
  * 响应：`{token: string, user_id: number, expires: string, user: UserResponse}`
  * 为会话管理设置仅 HTTP 身份验证 cookie
  
* **`POST /api/register`** - 带验证的新用户注册
  * 请求：`{username: string, password: string, email: string}`
  * 响应：`{user_id: number, message: string}`
  * 验证唯一用户名和电子邮件，创建安全密码哈希
  
* **`POST /api/logout`** - 用户会话终止
  * 头部：`Authorization: Bearer <token>`
  * 响应：`{message: string}`
  * 清除身份验证 cookie 并使会话无效

##### 用户管理
* **`GET /api/user/me`** - 获取当前用户配置文件信息
  * 头部：`Authorization: Bearer <token>`
  * 响应：包含用户详细信息、积分和设置的 `UserResponse`
  
* **`PUT /api/user/settings`** - 更新用户偏好和配置
  * 头部：`Authorization: Bearer <token>`
  * 请求：`{daily_summary_prompt?: string, ...}`
  * 响应：`{message: string}`

##### 仪表板和分析
* **`GET /api/today`** - 每日个性化新闻摘要和统计
  * 头部：`Authorization: Bearer <token>`
  * 查询：`?date=YYYY-MM-DD`（可选，默认为今天）
  * 响应：包含每日摘要、文章计数、热门主题和趋势关键词的 `TodayResponse`
  
* **`GET /api/available-dates`** - 获取日历导航的可用摘要日期
  * 头部：`Authorization: Bearer <token>`
  * 查询：`?year=2024&month=1`
  * 响应：`{month: string, available_dates: string[]}`

##### 主题管理
* **`GET /api/topics`** - 列出具有活动指标的所有用户主题
  * 头部：`Authorization: Bearer <token>`
  * 响应：具有主题详细信息和统计的 `TopicResponse[]`
  
* **`POST /api/topics`** - 创建具有自动向量生成的新主题
  * 头部：`Authorization: Bearer <token>`
  * 请求：具有名称和可选关键词的 `TopicCreate`
  * 响应：具有生成主题向量的 `TopicResponse`
  
* **`GET /api/topics/{id}`** - 获取特定主题详细信息和相关聚类
  * 头部：`Authorization: Bearer <token>`
  * 响应：具有关联聚类和文章的 `TopicResponse`
  
* **`PUT /api/topics/{id}`** - 更新主题配置和设置
  * 头部：`Authorization: Bearer <token>`
  * 请求：具有名称、关键词或活动状态的 `TopicUpdate`
  * 响应：具有更新信息的 `TopicResponse`
  
* **`DELETE /api/topics/{id}`** - 删除主题和关联数据
  * 头部：`Authorization: Bearer <token>`
  * 响应：`{message: string}`

##### 内容发现
* **`GET /api/topic/{id}`** - 获取特定主题的 AI 生成聚类
  * 头部：`Authorization: Bearer <token>`
  * 查询：`?limit=20&offset=0&since=YYYY-MM-DD`
  * 响应：`{topic: TopicResponse, events: EventResponse[]}`
  
* **`GET /api/cluster/{id}`** - 具有关联文章的详细聚类信息
  * 头部：`Authorization: Bearer <token>`
  * 响应：具有聚类详细信息和文章列表的 `EventDetailResponse`
  
* **`GET /api/article/{id}`** - 具有 AI 生成洞察的个人文章
  * 头部：`Authorization: Bearer <token>`
  * 响应：具有内容、摘要和元数据的 `RSSItemDetailResponse`
  
* **`GET /api/articles`** - 列出具有过滤和分页的文章
  * 头部：`Authorization: Bearer <token>`
  * 查询：`?limit=50&offset=0&status=completed&topic_id=1`
  * 响应：`PaginatedResponse<RSSItemResponse[]>`

##### RSS 订阅源管理
* **`GET /api/feeds`** - 列出用户的 RSS 订阅和订阅源状态
  * 头部：`Authorization: Bearer <token>`
  * 响应：具有订阅源详细信息和获取状态的 `RSSSubscriptionResponse[]`
  
* **`POST /api/feeds`** - 添加新的 RSS 订阅源订阅
  * 头部：`Authorization: Bearer <token>`
  * 请求：具有订阅源 URL 和可选别名的 `RSSSubscriptionCreate`
  * 响应：具有订阅详细信息的 `RSSSubscriptionResponse`
  
* **`PUT /api/feeds/{uuid}`** - 更新 RSS 订阅设置
  * 头部：`Authorization: Bearer <token>`
  * 请求：具有别名或活动状态的 `RSSSubscriptionUpdate`
  * 响应：具有更新设置的 `RSSSubscriptionResponse`
  
* **`DELETE /api/feeds/{uuid}`** - 删除 RSS 订阅源订阅
  * 头部：`Authorization: Bearer <token>`
  * 响应：`{message: string}`

##### 内部服务 API（服务间通信）
* **`GET /api/internal/articles/pending`** - 获取等待 AI 处理的文章
  * 由后处理服务用于获取未处理的文章
  * 响应：具有处理状态和元数据的 `RSSItemResponse[]`
  
* **`POST /api/internal/articles/{id}/process`** - 更新文章处理结果
  * 由后处理服务用于存储 AI 生成的内容
  * 请求：具有摘要、嵌入和分析的处理结果
  
* **`GET /api/internal/feeds/pending`** - 获取应获取的 RSS 订阅源
  * 由爬虫服务用于确定要处理的订阅源
  * 响应：具有获取计划和间隔的 `RSSFeedResponse[]`
  
* **`POST /api/internal/feeds/{id}/status`** - 更新订阅源获取状态
  * 由爬虫服务用于报告获取结果和错误
  * 请求：获取状态、时间和错误信息

##### 系统管理（仅限管理员）
* **`GET /api/admin/users`** - 列出具有综合统计的所有用户
  * 头部：`Authorization: Bearer <admin_token>`
  * 响应：具有用户详细信息、活动指标和管理标志的 `UserResponse[]`
  
* **`GET /api/admin/system-stats`** - 系统范围的性能和健康指标
  * 头部：`Authorization: Bearer <admin_token>`
  * 响应：包括处理队列、活动订阅源和性能数据的系统统计
  
* **`POST /api/admin/system-settings`** - 更新全局系统配置
  * 头部：`Authorization: Bearer <admin_token>`
  * 请求：具有配置键值对的 `SystemSettingCreate`
  * 响应：具有更新设置的 `SystemSettingResponse`
  
* **`GET /api/admin/system-settings`** - 检索系统配置设置
  * 头部：`Authorization: Bearer <admin_token>`
  * 响应：具有所有系统设置和元数据的 `SystemSettingResponse[]`

##### 错误响应
所有端点返回标准化错误响应：
```json
{
  "error": "error_code",
  "message": "Human-readable error description",
  "details": "Additional context (optional)"
}
```

**常见 HTTP 状态码：**
* `200` - 成功
* `201` - 已创建
* `400` - 错误请求（验证错误）
* `401` - 未授权（无效/缺失令牌）
* `403` - 禁止（权限不足）
* `404` - 未找到
* `422` - 不可处理实体（无效数据格式）
* `500` - 内部服务器错误

#### 后端项目架构

后端遵循简化的 FastAPI 架构，具有最小的文件占用，针对可维护性和直接集成进行了优化：

```
backend/
├── main.py                    # 具有所有端点的完整 FastAPI 应用程序
├── text_processor.py          # HTML 文本处理实用程序
├── pyproject.toml            # Python 依赖项和项目元数据
├── server.log                # 应用程序日志文件
└── uv.lock                   # 依赖项锁定文件

# 共享依赖项 (../lib/newsfrontier-lib)
../lib/newsfrontier-lib
├── models.py                 # SQLAlchemy 数据库模型
├── database.py               # 数据库连接和会话管理  
├── crud.py                   # 数据库操作（创建、读取、更新、删除）
├── schemas.py                # Pydantic 请求/响应模式
├── llm_client.py             # AI/LLM 集成实用程序
├── s3_client.py              # S3 存储客户端
└── __init__.py              # 具有实用程序导出的包初始化
```

**核心架构组件：**

##### `main.py` - 单体应用程序设计
* **完整 API 实现**：单文件中的所有端点以简化部署
* **FastAPI 应用程序配置**：CORS 中间件、请求日志记录和全局异常处理
* **身份验证系统**：JWT 令牌生成、验证和用户会话管理
* **数据库集成**：与 newsfrontier-lib 的直接集成，用于所有数据操作
* **中间件管道**：具有性能计时和错误跟踪的请求/响应日志记录
* **API 类别**：身份验证、用户管理、仪表板分析、内容发现、RSS 管理和管理端点

##### `text_processor.py` - 内容处理实用程序
* **HTML 锚点处理**：文章内容的段落锚点自动插入
* **内容分析**：基于 HTML 结构的文本处理策略确定
* **锚点管理**：生成、验证和提取 P-xxxxx 和 SEN-xxxxx 格式锚点
* **错误处理**：处理失败时优雅回退到原始内容

##### 数据库层 (`../lib/`)
* **`models.py`** - SQLAlchemy ORM 模型
  * 用户身份验证和授权模型
  * RSS 订阅源和订阅关系
  * 具有向量嵌入的文章元数据
  * 主题和聚类分类模式
  * AI 工作流程的处理状态跟踪

* **`database.py`** - 连接管理
  * 具有 pgvector 扩展的异步 PostgreSQL 连接
  * 高并发处理的连接池
  * 数据库迁移支持和健康检查
  * 数据一致性的事务管理

* **`crud.py`** - 数据访问层
  * 使用 SQLAlchemy 异步会话的类型安全数据库操作
  * 使用 pgvector 的向量相似性搜索的复杂查询
  * AI 处理工作流程的批量操作
  * 仪表板分析和报告的优化查询

* **`schemas.py`** - API 合约
  * 请求验证和序列化的 Pydantic 模型
  * 具有前端消费的计算字段的响应模式
  * 数据库模型和 API 响应之间的类型安全数据转换
  * 用户输入和系统约束的验证规则

**关键设计模式：**

##### 异步优先架构
* 所有数据库操作使用 async/await 模式进行非阻塞 I/O
* FastAPI 的异步请求处理最小化资源消耗
* AI 处理工作流程的后台任务排队
* 并发 RSS 订阅源处理和内容分析

##### 依赖注入
* FastAPI 的依赖系统用于数据库会话、身份验证和配置
* AI 集成（LLM、嵌入、聚类）的模块化服务层
* 不同部署上下文的基于环境的配置注入
* 具有可模拟依赖项的测试友好架构

##### 错误处理和日志记录
* 具有调试上下文信息的结构化日志记录
* AI 服务的优雅错误恢复和重试机制
* 具有调试技术细节的用户友好错误消息
* 性能监控和健康检查端点

##### 安全实现
* 具有可配置过期的基于 JWT 的身份验证
* 使用具有盐轮次的 bcrypt 的密码哈希
* 基于角色的访问控制（用户/管理员权限）
* 输入验证和 SQL 注入防护
* 速率限制和请求节流功能

### 前端应用程序  
* **语言**：TypeScript 用于类型安全开发
* **包管理**：pnpm 用于更快更现代的开发
* **框架**：Next.js 14+ 带 App Router
* **UI 库**：DaisyUI 组件与 Tailwind CSS
* **状态管理**：React Context API / Zustand
* **测试**：Jest 和 React Testing Library

#### 关键页面和组件
* **仪表板**：个性化新闻概览
  * 每日新闻摘要
  * 每日新闻包括文章或聚类的参考链接。

* **新闻浏览器**：具有智能聚类的分层新闻浏览
  * **主题列表**：具有活动指标的用户定义兴趣类别
  * **主题聚类**：选定主题内的 AI 生成文章组
    * 具有文章计数和相关性评分的视觉聚类表示
    * 基于内容分析的智能聚类命名
  * **新闻列表**：选定聚类内的详细文章列表
    * 具有来源归属和发布时间戳的文章标题
    * 摘要预览和相关性指标
  * **文章阅读器**：具有增强功能的全内容文章查看器
    * 具有阅读时间估计的原始文章内容
    * AI 生成的摘要和关键洞察提取
    * 相关文章和跨聚类推荐

* **设置和管理**：全面的系统配置
  * **主题管理**：动态主题创建和关键词管理
    * 具有基于向量匹配的自定义主题定义
    * 主题性能分析和优化建议
  * **RSS 源管理**：订阅源配置和监控仪表板
  * **用户偏好**：个性化选项和通知设置

#### 前端项目架构

```
src/
├── components/                 # 可重用 UI 组件
│   ├── Modal.tsx              # 表单和确认的模态对话框组件
│   ├── ListItem.tsx           # 主题和新闻的通用列表项组件
│   ├── ListView.tsx           # 分页列表的容器组件
│   ├── Timeline.tsx           # 聚类可视化的交互式时间线组件
│   ├── LoadingSpinner.tsx     # 加载状态指示器
│   └── ErrorBoundary.tsx      # 错误处理包装器组件
│
├── lib/                       # 实用程序和配置
│   ├── auth-context.tsx       # 身份验证状态管理的 React Context
│   ├── types.ts              # API 响应的 TypeScript 类型定义
│   ├── api-client.ts         # 具有身份验证处理的 HTTP 客户端
│   ├── utils.ts              # 常用实用函数
│   └── constants.ts          # 应用程序常量和配置
│
├── app/                      # Next.js App Router 页面
│   ├── (auth)/              # 身份验证路由组
│   │   ├── login/
│   │   │   └── page.tsx     # 具有验证的用户登录表单
│   │   ├── register/
│   │   │   └── page.tsx     # 具有电子邮件验证的用户注册
│   │   └── layout.tsx       # 身份验证特定布局（登录/注册）
│   │
│   ├── dashboard/           # 主要应用程序路由
│   │   ├── page.tsx        # 显示今日摘要。
│   │   ├── topics/
│   │   │   ├── page.tsx    # 具有聚类时间线的主题列表
│   │   │   └── [id]/
│   │   │       └── page.tsx # 具有聚类视图的主题详细信息
│   │   ├── clusters/
│   │   │   └── [id]/
│   │   │       └── page.tsx # 聚类内的新闻列表
│   │   ├── article/
│   │   │   └── [id]/
│   │   │       └── page.tsx # 具有 AI 洞察的文章阅读器
│   │   └── settings/
│   │       └── page.tsx    # 用户偏好和主题管理
│   │
│   ├── admin/              # 管理界面
│   │   ├── page.tsx       # 具有系统指标的管理仪表板
│   │   ├── users/
│   │   │   └── page.tsx   # 用户管理界面
│   │   ├── rss-feeds/
│   │   │   └── page.tsx   # RSS 源配置
│   │   ├── ai-config/
│   │   │   └── page.tsx   # LLM 和嵌入服务设置
│   │   └── system/
│   │       └── page.tsx   # 系统范围配置
│   │
│   ├── globals.css       # 具有 DaisyUI 的全局样式
│   ├── layout.tsx        # 具有导航的根布局
│   └── page.tsx          # 登陆/主页
│
└── middleware.ts         # 路由保护的 Next.js 中间件
```

**关键架构决策：**
- **App Router**：利用 Next.js 13+ 基于文件的路由和布局
- **路由组**：分别组织身份验证和管理路由  
- **组件可重用性**：通用组件（ListView、ListItem）支持多种数据类型
- **类型安全**：集中式 TypeScript 定义确保 API 合约一致性
- **身份验证流程**：基于上下文的身份验证状态和中间件保护
- **渐进增强**：服务器端渲染与客户端交互


### 数据处理服务

#### RSS 爬虫服务
* **语言**：Python 3.11+
* **架构**：UV 工作空间成员
* **关键功能**：
  * 具有并发获取的异步 RSS 解析
  * 可配置调度和重试机制
  * 数据验证和清理
  * PostgreSQL 持久层

#### PostProcess AI 服务  
* **语言**：Python 3.11+
* **架构**：具有 AI 处理管道的 UV 工作空间成员
* **AI/ML 栈**：
  * **LLM 集成**：Google AI (Gemini) 用于内容分析和摘要
  * **模型**：Gemini-2.0-Flash-Lite（快速）、Gemini-2.5-Pro（高级分析）
  * **嵌入**：gemini-embedding-001 具有 768 维向量
  * **向量存储**：pgvector 用于相似性搜索和聚类
  * **图像生成**：Imagen-3.0-Generate-002 用于封面图片
  * **聚类**：Scikit-learn 与基于 LLM 的决策制定
* **关键能力**：
  * 具有主题提取和实体识别的内容分析
  * 具有上下文感知决策的智能聚类
  * 具有结构化 markdown 输出的个性化每日摘要
  * 开发和调试的 AI 提示测试框架
  * 封面图片存储的 S3 集成
  * 服务间通信的 FastAPI 内部服务器

#### 共享库 (`lib`)
* **语言**：Python 3.11+
* **架构**：UV 工作空间成员  
* **内容**：
  * 数据库模式定义
  * 共享数据模型和类型
  * 常用实用程序和辅助函数
  * 配置管理

# 开发和部署

## 快速开始脚本

### `scripts/dev.sh` - 开发环境设置
编排所有服务的自动化开发环境启动器：

### `scripts/init.sql` - 数据库模式初始化
具有 pgvector 扩展的完整 PostgreSQL 模式设置：
* 具有安全密码哈希的用户身份验证表
* 具有全文搜索索引的新闻文章表
* 主题和 RSS 源配置
* 具有优化索引的向量嵌入存储
* 聚类结果和关系

## 生产部署

### Docker Compose 配置

项目包含完整的 `docker-compose.yml` 配置，在容器化环境中编排所有 NewsFrontier 服务。设置遵循开发脚本（`scripts/dev.sh`）中定义的架构和环境变量。

#### 服务架构：

**数据库服务 (`newsfrontier-db`)：**
- 使用具有向量扩展支持的 `pgvector/pgvector:pg17` 镜像
- 使用基于环境的凭据配置 PostgreSQL
- 挂载持久数据卷和初始化脚本
- 包括服务依赖管理的健康检查
- 暴露端口 5432 用于外部数据库访问

**后端服务 (`newsfrontier-backend`)：**
- 从 `./backend` 目录使用 Dockerfile 构建
- 配置完整的 AI/ML 环境（LLM API、嵌入服务）
- 包括所有安全设置（JWT、bcrypt）和处理参数
- 在启动前依赖健康的数据库服务
- 在端口 8000 上暴露 FastAPI 服务器，带有日志卷挂载

**前端服务 (`newsfrontier-frontend`)：**
- 从 `./frontend` 目录构建 Next.js 应用程序
- 配置后端通信的 API 端点
- 在端口 3000 上暴露 Web 应用程序
- 依赖后端服务可用性

**爬虫服务 (`newsfrontier-scraper`)：**
- 从 `./scraper` 目录构建 RSS 爬取服务
- 配置 RSS 获取参数和数据库连接
- 以守护进程模式运行，带有日志文件持久性
- 依赖健康的数据库服务

**后处理服务 (`newsfrontier-postprocess`)：**
- 从 `./postprocess` 目录构建 AI 处理服务
- 配置完整的 AI 管道（LLM、嵌入、图像生成）
- 包括封面图片的 S3 存储配置
- 以守护进程模式运行，带有全面日志记录

#### 部署功能：

- **环境变量集成**：所有服务使用 `.env` 文件变量，具有合理默认值
- **服务依赖**：具有健康检查依赖的正确启动顺序
- **持久存储**：数据库数据持久性和日志文件挂载
- **网络隔离**：服务通过内部 Docker 网络通信
- **重启策略**：失败时自动服务重启
- **资源管理**：容器命名和卷管理

#### 使用：
```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f [service-name]

# 停止所有服务
docker-compose down
```

## 数据库设计

### 核心设计原则
* **数据可靠性分离**：原始 RSS 数据和 AI 处理数据分开存储，以保持数据完整性并支持重新处理
* **错误恢复支持**：所有处理表包括状态跟踪，用于可靠重启和恢复
* **可扩展架构**：向量嵌入和聚类设计用于大容量新闻处理

### 数据库模式

#### 核心用户管理

##### `users` - 用户身份验证和配置文件信息
* `id` - INTEGER PRIMARY KEY（自增）
* `username` - VARCHAR(50) UNIQUE NOT NULL
* `password_hash` - VARCHAR(255) NOT NULL（bcrypt 盐哈希）
* `email` - VARCHAR(255) UNIQUE NOT NULL（电子邮件验证）
* `is_admin` - BOOLEAN DEFAULT FALSE（基于角色的访问控制）
* `credits` - INTEGER DEFAULT 0 CHECK (credits >= 0)（用户积分系统）
* `credits_accrual` - INTEGER DEFAULT 0 CHECK (credits_accrual >= 0)（赚取积分）
* `daily_summary_prompt` - TEXT（个性化 AI 提示）
* `created_at` - TIMESTAMP DEFAULT NOW()
* `updated_at` - TIMESTAMP DEFAULT NOW()（自动更新触发器）

**关系：**
- 与主题、聚类、摘要、RSS 订阅的一对多关系

#### RSS 订阅源管理

##### `rss_feeds` - RSS 订阅源配置
* `id` - INTEGER PRIMARY KEY（自增）
* `uuid` - UUID UNIQUE NOT NULL DEFAULT gen_random_uuid()（稳定外部标识符）
* `url` - TEXT NOT NULL UNIQUE（RSS 订阅源 URL）
* `title` - VARCHAR(255)（从订阅源元数据中提取）
* `description` - TEXT（订阅源描述）
* `last_fetch_at` - TIMESTAMP（最近获取时间）
* `last_fetch_status` - VARCHAR(50) DEFAULT 'pending' CHECK (last_fetch_status IN ('pending', 'success', 'failed', 'timeout'))
* `fetch_interval_minutes` - INTEGER DEFAULT 60（可配置获取频率）
* `created_at` - TIMESTAMP DEFAULT NOW()
* `updated_at` - TIMESTAMP DEFAULT NOW()

**设计说明：** UUID 作为 URL 更改时的稳定标识符

##### `rss_subscriptions` - 用户 RSS 订阅源订阅（多对多）
* `user_id` - INTEGER REFERENCES users(id) ON DELETE CASCADE
* `rss_uuid` - UUID REFERENCES rss_feeds(uuid) ON DELETE CASCADE
* `alias` - VARCHAR(255)（用户定义的订阅源名称）
* `is_active` - BOOLEAN DEFAULT TRUE（订阅切换）
* `created_at` - TIMESTAMP DEFAULT NOW()
* **PRIMARY KEY** (user_id, rss_uuid)

##### `rss_fetch_records` - 具有去重的原始 RSS 内容
* `id` - INTEGER PRIMARY KEY（自增）
* `rss_feed_id` - INTEGER REFERENCES rss_feeds(id) ON DELETE CASCADE
* `raw_content` - TEXT NOT NULL（原始 RSS XML/JSON 内容）
* `content_hash` - VARCHAR(64) NOT NULL（用于去重的 SHA256）
* `first_fetch_timestamp` - TIMESTAMP DEFAULT NOW()（初始发现）
* `last_fetch_timestamp` - TIMESTAMP DEFAULT NOW()（最近获取）
* `http_status` - INTEGER（HTTP 响应码）
* `content_encoding` - VARCHAR(50)（内容编码类型）

**设计模式：** 将原始 RSS 数据与处理文章分离以保证数据完整性

#### 文章处理管道

##### `rss_items_metadata` - AI 提取的文章数据
* `id` - INTEGER PRIMARY KEY（自增）
* `rss_fetch_record_id` - INTEGER REFERENCES rss_fetch_records(id) ON DELETE CASCADE
* `guid` - TEXT（用于去重的 RSS 项目 GUID）
* `title` - TEXT NOT NULL（文章标题）
* `content` - TEXT（完整文章内容）
* `url` - TEXT（文章 URL）
* `published_at` - TIMESTAMP（文章发布时间）
* `author` - VARCHAR(255)（文章作者）
* `category` - VARCHAR(255)（文章类别/主题）
* `processing_status` - VARCHAR(20) DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed'))
* `processing_started_at` - TIMESTAMP（AI 处理开始时间）
* `processing_completed_at` - TIMESTAMP（AI 处理完成时间）
* `processing_attempts` - INTEGER DEFAULT 0 CHECK (processing_attempts >= 0 AND processing_attempts <= 10)
* `last_error_message` - TEXT（调试错误跟踪）
* `created_at` - TIMESTAMP DEFAULT NOW()
* **UNIQUE CONSTRAINT：** (rss_fetch_record_id, guid) - 防止每个订阅源的重复文章

##### `rss_item_derivatives` - AI 生成的内容和嵌入
* `id` - INTEGER PRIMARY KEY（自增）
* `rss_item_id` - INTEGER UNIQUE REFERENCES rss_items_metadata(id) ON DELETE CASCADE（一对一关系）
* `summary` - TEXT（AI 生成的文章摘要）
* `title_embedding` - VECTOR(dynamic_dimension)（pgvector 标题嵌入）
* `summary_embedding` - VECTOR(dynamic_dimension)（pgvector 摘要嵌入）
* `processing_status` - VARCHAR(20) DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed'))
* `summary_generated_at` - TIMESTAMP（LLM 处理时间戳）
* `embeddings_generated_at` - TIMESTAMP（嵌入生成时间戳）
* `processing_attempts` - INTEGER DEFAULT 0（重试计数器）
* `last_error_message` - TEXT（AI 处理错误详细信息）
* `llm_model_version` - VARCHAR(100)（AI 模型版本跟踪）
* `embedding_model_version` - VARCHAR(100)（嵌入模型版本）
* `created_at` - TIMESTAMP DEFAULT NOW()

**向量维度：** 通过环境变量可配置（默认：1536 用于 OpenAI 兼容性）

#### 主题和聚类管理

##### `topics` - 用户定义的新闻分类
* `id` - INTEGER PRIMARY KEY（自增）
* `user_id` - INTEGER REFERENCES users(id) ON DELETE CASCADE
* `name` - VARCHAR(255) NOT NULL（主题名称）
* `topic_vector` - VECTOR(dynamic_dimension)（AI 生成的主题嵌入）
* `is_active` - BOOLEAN DEFAULT TRUE（主题状态切换）
* `created_at` - TIMESTAMP DEFAULT NOW()
* `updated_at` - TIMESTAMP DEFAULT NOW()
* **UNIQUE CONSTRAINT：** (user_id, name) - 防止每个用户的重复主题名称

##### `events` - 从文章分析中提取的新闻事件聚类
* `id` - INTEGER PRIMARY KEY（自增）
* `user_id` - INTEGER REFERENCES users(id) ON DELETE CASCADE
* `topic_id` - INTEGER REFERENCES topics(id) ON DELETE CASCADE
* `title` - VARCHAR(500) NOT NULL（聚类标题）
* `description` - TEXT（聚类描述）
* `event_description` - TEXT（详细事件分析）
* `event_embedding` - VECTOR(dynamic_dimension)（事件向量表示）
* `last_updated_at` - TIMESTAMP DEFAULT NOW()（事件演化跟踪）
* `created_at` - TIMESTAMP DEFAULT NOW()
* `updated_at` - TIMESTAMP DEFAULT NOW()

#### 关系表（多对多）

##### `article_topics` - 具有相关性评分的文章-主题关联
* `rss_item_id` - INTEGER REFERENCES rss_items_metadata(id) ON DELETE CASCADE
* `topic_id` - INTEGER REFERENCES topics(id) ON DELETE CASCADE
* `relevance_score` - FLOAT CHECK (relevance_score >= 0.0 AND relevance_score <= 1.0)（AI 计算的相关性）
* `created_at` - TIMESTAMP DEFAULT NOW()
* **PRIMARY KEY** (rss_item_id, topic_id)

##### `article_events` - 文章-事件聚类关联
* `rss_item_id` - INTEGER REFERENCES rss_items_metadata(id) ON DELETE CASCADE
* `event_id` - INTEGER REFERENCES events(id) ON DELETE CASCADE
* `relevance_score` - FLOAT CHECK (relevance_score >= 0.0 AND relevance_score <= 1.0)（聚类置信度）
* `created_at` - TIMESTAMP DEFAULT NOW()
* **PRIMARY KEY** (rss_item_id, event_id)

##### `user_topics` - 用户主题偏好和优先级
* `user_id` - INTEGER REFERENCES users(id) ON DELETE CASCADE
* `topic_id` - INTEGER REFERENCES topics(id) ON DELETE CASCADE
* `priority` - INTEGER DEFAULT 1 CHECK (priority >= 1 AND priority <= 10)（用户偏好排名）
* `notification_enabled` - BOOLEAN DEFAULT TRUE（通知设置）
* `created_at` - TIMESTAMP DEFAULT NOW()
* **PRIMARY KEY** (user_id, topic_id)

#### 每日摘要和系统配置

##### `user_summaries` - 每日个性化新闻摘要
* `id` - INTEGER PRIMARY KEY（自增）
* `user_id` - INTEGER REFERENCES users(id) ON DELETE CASCADE
* `summary` - TEXT（AI 生成的每日摘要）
* `cover_arguments` - TEXT（封面图片生成参数）
* `cover_prompt` - TEXT（AI 图像生成提示）
* `cover_seed` - INTEGER（图像生成种子以保证重现性）
* `cover_s3key` - TEXT（生成的封面图片的 S3 存储键）
* `date` - DATE NOT NULL（摘要日期）
* `created_at` - TIMESTAMP DEFAULT NOW()
* **UNIQUE CONSTRAINT：** (user_id, date) - 每个用户每天一个摘要

##### `system_settings` - 全局系统配置
* `id` - INTEGER PRIMARY KEY（自增）
* `setting_key` - VARCHAR(100) UNIQUE NOT NULL（配置键）
* `setting_value` - TEXT（配置值）
* `setting_type` - VARCHAR(20) DEFAULT 'string' CHECK (setting_type IN ('string', 'integer', 'boolean', 'json', 'float'))
* `description` - TEXT（设置文档）
* `is_public` - BOOLEAN DEFAULT FALSE（公共/私有设置标志）
* `updated_at` - TIMESTAMP DEFAULT NOW()
* `updated_by` - INTEGER REFERENCES users(id) ON DELETE SET NULL（审计跟踪）
* `created_at` - TIMESTAMP DEFAULT NOW()

**常见系统设置：**

**处理配置：**
* `default_rss_fetch_interval` - 默认 RSS 轮询间隔（分钟）（默认：60）
* `max_processing_attempts` - 失败处理的最大重试次数（默认：3）
* `embedding_dimension` - 向量维度大小（默认：768）
* `max_articles_per_event` - 与单个事件关联的最大文章数（默认：50）

**AI 聚类阈值：**
* `similarity_threshold` - 聚类文章的最小相似性评分（默认：0.62）
* `cluster_threshold` - 直接事件分配的最小嵌入相似性评分（默认：0.7）

**AI 系统提示（私有设置）：**
* `prompt_summary_creation` - 生成具有项目符号和锚链接的文章摘要的模板提示
* `prompt_cluster_detection` - 创建新事件聚类的模板提示
* `prompt_daily_summary_system` - 创建具有 markdown 链接的个性化每日新闻摘要的系统提示
* `prompt_cover_image_generation` - 为每日摘要生成封面图片描述的模板提示

**提示功能：**
- 具有锚链接保留的文章摘要（`<a id="P-67890">` → `[text](#P-67890)`）
- 具有主题层次强制的事件聚类（用户主题下一级）
- 具有仪表板页面结构化 markdown 链接的每日摘要生成
- 具有专业编辑插图指南的封面图片提示生成

### 数据库性能优化

#### 向量搜索性能
* **pgvector 扩展**：所有向量列使用 IVFFlat 索引进行快速相似性搜索
* **索引调优**：向量索引配置为 `lists = 100` 以获得最佳性能
* **嵌入维度**：所有表中一致的 1536 维向量

#### 查询性能增强
* **复合索引**：常见查询模式的多列索引
* **部分索引**：基于状态的过滤使用专用索引优化  
* **时间序列优化**：时间戳列上的 DESC 索引用于最近数据查询

#### 数据完整性保护
* **约束验证**：CHECK 约束防止无效数据状态
* **引用完整性**：外键的适当 CASCADE/SET NULL 行为
* **唯一约束**：业务逻辑约束防止重复数据
* **处理限制**：有界重试尝试防止无限处理循环

#### 维护建议
* **定期 VACUUM**：向量索引从定期维护中受益
* **索引监控**：监控查询性能并随着数据增长调整 `lists` 参数
* **分区策略**：考虑按日期分区大表以提高性能
* **归档策略**：为历史记录实施数据保留策略


### 环境变量

#### 必需配置
复制 `.env.template` 到 `.env` 并配置以下变量：

**数据库和核心服务：**
* `DATABASE_URL` - PostgreSQL 连接字符串 
  * 格式：`postgresql://newsfrontier:dev_password@localhost:5432/newsfrontier_db`
* `DB_PASSWORD` - PostgreSQL 数据库密码
* `S3API_REGION` - S3 兼容存储区域
* `S3API_ENDPOINT` - S3 兼容存储端点 URL
* `S3API_BUCKET` - 封面图片存储的 S3 存储桶名称
* `S3API_KEY_ID` - S3 访问密钥 ID
* `S3API_KEY` - S3 密钥

**安全和身份验证：**
* `JWT_SECRET` - JWT 令牌签名的密钥（生产中使用强随机字符串）
  * 默认：`your-super-secret-jwt-key-change-this-in-production`
* `JWT_EXPIRE_HOURS` - JWT 令牌过期时间（小时）（默认：24）
* `PASSWORD_SALT_ROUNDS` - 密码哈希的 Bcrypt 盐轮次（默认：12）

**AI/ML 服务：**
* `LLM_API_URL` - 主要 LLM 服务端点
  * 默认：`https://generativelanguage.googleapis.com/v1beta/openai/`
* `LLM_API_KEY` - LLM 服务的 API 密钥
* `GOOGLE_API_KEY` - Google AI API 密钥（用于 Gemini 模型）

**LLM 模型配置：**
* `LLM_MODEL_SUMMARY` - 文章摘要的快速模型
  * 默认：`gemini-2.0-flash-lite`
* `LLM_MODEL_ANALYSIS` - 聚类检测和每日摘要的强大模型
  * 默认：`gemini-2.5-pro`

**向量嵌入服务：**
* `EMBEDDING_API_URL` - 向量嵌入服务端点
  * 默认：`https://api.openai.com/v1`
* `EMBEDDING_MODEL` - 嵌入模型名称
  * 默认：`gemini-embedding-001`
* `EMBEDDING_DIMENSION` - 向量维度大小（默认：768）

**图像生成服务：**
* `IMAGEGEN_MODEL` - AI 图像生成模型
  * 默认：`imagen-3.0-generate-002`
* `IMAGEGEN_ASPECT_RATIO` - 生成图像长宽比（默认：16:9）
* `IMAGEGEN_PERSON_GENERATE` - 人物生成策略（默认：dont_allow）

**可选 AI 服务：**
* `TRANSCRIPT_API_URL` - 语音转文本服务端点（可选）
* `TTS_API_URL` - 文本转语音服务端点（可选）
* `TTS_API_KEY` - 音频服务的 API 密钥（可选）

**应用程序设置：**
* `LOG_LEVEL` - 应用程序日志级别（DEBUG、INFO、WARNING、ERROR）
  * 默认：`INFO`
* `ENVIRONMENT` - 运行时环境（development、staging、production）
  * 默认：`development`
* `DEBUG` - 启用调试模式（true/false）
  * 默认：`true`

**处理配置：**
* `MAX_PROCESSING_ATTEMPTS` - 失败 AI 处理的最大重试次数（默认：3）
* `DEFAULT_RSS_INTERVAL` - 默认 RSS 获取间隔（分钟）（默认：60）
* `SCRAPER_CONCURRENT_FEEDS` - 并发处理的 RSS 订阅源数量（默认：5）
* `POSTPROCESS_BATCH_SIZE` - AI 处理批大小（默认：10）

**API 配置：**
* `API_RATE_LIMIT` - API 速率限制（每分钟请求数，默认：100）
* `CORS_ORIGINS` - 前端访问允许的 CORS 来源
  * 默认：`http://localhost:3000,http://localhost:8000`

**开发设置：**
* `NEXT_PUBLIC_API_URL` - 前端 API 端点配置
  * 默认：`http://localhost:8000`