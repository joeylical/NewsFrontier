# NewsFrontier Enhanced Configuration - 部署指南

## 🎉 恭喜！所有任务已完成

本指南将帮助您部署和配置增强的NewsFrontier系统，包括加密API密钥存储和数据库驱动的配置管理。

## ✅ 已完成功能

### 核心增强功能
- 🔐 **加密存储系统**: 使用Fernet对称加密安全存储API密钥
- 🗄️ **数据库配置**: 所有配置存储在数据库中，支持运行时修改
- 🤖 **增强LLM客户端**: 支持LiteLLM多提供商集成
- ☁️ **增强S3客户端**: 数据库配置的存储服务
- 🔄 **可配置间隔**: scraper和postprocess运行间隔可配置
- 🎛️ **功能开关**: 可启用/禁用每日摘要和封面图片
- 🛠️ **管理员界面**: 完整的Web管理界面

## 🚀 快速部署

### 1. 环境准备

```bash
# 确认在正确目录
cd /home/nixos/NewsFrontier

# 同步依赖
uv sync

# 生成加密主密钥
python -c "from newsfrontier_lib.crypto import generate_master_key; print('CRYPTO_MASTER_KEY=' + generate_master_key())"
```

### 2. 环境配置

将生成的主密钥添加到 `.env` 文件：

```bash
# 复制模板并编辑
cp .env.template .env

# 编辑 .env 文件，添加：
CRYPTO_MASTER_KEY=your-generated-32-character-key-here

# 添加其他必要配置...
DATABASE_URL=postgresql://newsfrontier:dev_password@localhost:5432/newsfrontier_db
JWT_SECRET=your-jwt-secret-key
```

### 3. 数据库初始化

```bash
# 运行数据库迁移
cd lib && uv run python -c "
from newsfrontier_lib.db_migrations import run_all_migrations
from newsfrontier_lib.init_config import init_default_settings

print('🔧 Initializing default settings...')
init_default_settings()

print('📦 Running database migrations...')
run_all_migrations()

print('✅ Database initialization complete!')
"
```

### 4. 启动服务

```bash
# 启动backend (在新终端)
cd backend && uv run python main.py

# 启动scraper (在新终端)  
cd scraper && uv run python main.py --daemon

# 启动postprocess (在新终端)
cd postprocess && uv run python main.py --daemon
```

### 5. 启动前端并访问管理界面

```bash
# 启动前端 (在新终端)
cd frontend && npm run dev
# 或者
cd frontend && pnpm dev
```

访问管理界面：
- 主应用: http://localhost:3000
- 管理员设置: http://localhost:3000/dashboard/settings (需要管理员权限)

## 🔧 配置管理

### 通过管理界面配置

1. **访问管理界面**: http://localhost:3000/dashboard/settings
2. **配置管理员设置** (需要管理员权限):
   - 登录后访问设置页面
   - 管理员用户将看到"System Settings"区域
   - 配置按类别分组显示：
     - **AI & LLM**: 模型配置
     - **API Keys**: 加密存储的API密钥
     - **Features**: 功能开关
     - **Processing**: 处理间隔和参数
     - **Storage**: S3存储配置
   - 修改设置后点击"Save All Settings"保存

### 通过API配置

```bash
# 获取所有系统设置
curl -X GET "http://localhost:8000/api/admin/system-settings" \
  -H "Authorization: Bearer admin-token"

# 更新系统设置
curl -X PUT "http://localhost:8000/api/admin/system-settings" \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "setting_key": "google_api_key_encrypted", 
      "setting_value": "your-google-api-key",
      "setting_type": "string",
      "setting_description": "Google API Key for LLM services"
    },
    {
      "setting_key": "scraper_interval_minutes",
      "setting_value": "30", 
      "setting_type": "integer",
      "setting_description": "RSS scraper interval in minutes"
    }
  ]'
```

### 通过Python代码配置

```python
from newsfrontier_lib.config_service import get_config

config = get_config()

# 设置加密API密钥
config.set_encrypted('google_api_key_encrypted', 'your-google-api-key')
config.set_encrypted('openai_api_key_encrypted', 'your-openai-api-key')

# 设置S3配置
config.set_encrypted('s3_endpoint_encrypted', 'https://s3.amazonaws.com')
config.set_encrypted('s3_access_key_id_encrypted', 'your-access-key-id')
config.set_encrypted('s3_secret_key_encrypted', 'your-secret-key')

# 设置普通配置
config.set('scraper_interval_minutes', 30, 'integer')
config.set('daily_summary_enabled', True, 'boolean')
```

## 📋 可配置项目清单

### LLM模型配置
- ✅ `llm_summary_model`: 文章摘要模型 (默认: gemini-2.0-flash-lite)
- ✅ `llm_analysis_model`: 分析模型 (默认: gemini-2.5-pro)  
- ✅ `llm_embedding_model`: 嵌入模型 (默认: text-embedding-004)
- ✅ `llm_image_model`: 图像生成模型 (默认: imagen-3.0-generate-002)

### API密钥 (加密存储)
- ✅ `google_api_key_encrypted`: Google API密钥
- ✅ `openai_api_key_encrypted`: OpenAI API密钥
- ✅ `s3_access_key_id_encrypted`: S3访问密钥ID
- ✅ `s3_secret_key_encrypted`: S3秘密访问密钥
- ✅ `s3_endpoint_encrypted`: S3端点URL

### 功能开关
- ✅ `daily_summary_enabled`: 启用每日摘要 (默认: true)
- ✅ `daily_summary_cover_enabled`: 启用封面图片 (默认: true)

### 处理配置  
- ✅ `scraper_interval_minutes`: 爬虫间隔 (默认: 60分钟)
- ✅ `postprocess_interval_minutes`: 后处理间隔 (默认: 30分钟)
- ✅ `cluster_threshold`: 聚类阈值 (默认: 0.8)
- ✅ `max_processing_attempts`: 最大重试次数 (默认: 3)

### S3存储配置
- ✅ `s3_region`: S3区域 (默认: us-east-1)
- ✅ `s3_bucket`: S3存储桶名称
- ✅ `s3_endpoint_encrypted`: S3端点 (加密)
- ✅ `s3_access_key_id_encrypted`: 访问密钥 (加密)
- ✅ `s3_secret_key_encrypted`: 秘密密钥 (加密)

## 🔒 安全最佳实践

### 1. 主密钥管理
```bash
# 生成强密钥
python -c "from newsfrontier_lib.crypto import generate_master_key; print(generate_master_key())"

# 设置环境变量 (production)
export CRYPTO_MASTER_KEY="your-32-character-master-key"

# 或在 .env 文件中设置 (development)
echo "CRYPTO_MASTER_KEY=your-32-character-master-key" >> .env
```

### 2. 密钥轮换
```python
# 更新API密钥
from newsfrontier_lib.config_service import get_config

config = get_config()
config.set_encrypted('google_api_key_encrypted', 'new-google-api-key')

# 验证新密钥
# 访问 http://localhost:8000/admin 并测试API密钥
```

### 3. 权限控制
- 管理界面需要管理员权限
- API密钥在界面中显示为 `<encrypted>`
- 配置更改记录在数据库中

## 🧪 测试和验证

### 1. 测试加密功能
```bash
cd lib && CRYPTO_MASTER_KEY="your-master-key" uv run python -c "
from newsfrontier_lib.crypto import test_encryption
if test_encryption():
    print('✅ 加密功能正常')
else:
    print('❌ 加密功能异常')
"
```

### 2. 验证配置
```bash
# 列出所有配置
curl -X GET "http://localhost:8000/api/admin/settings/" \
  -H "Authorization: Bearer admin-token"

# 测试API密钥
curl -X POST "http://localhost:8000/api/admin/settings/api-keys/test" \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{"provider": "google"}'
```

### 3. 服务状态检查
```bash
# 检查postprocess配置加载
tail -f postprocess/postprocess.log | grep "Configuration Status"

# 检查scraper间隔配置  
tail -f scraper/scraper.log | grep "Waiting.*minutes"
```

## 🔧 故障排除

### 常见问题

1. **加密错误**
   ```
   问题: KeyManager not available
   解决: 检查CRYPTO_MASTER_KEY是否正确设置
   验证: echo $CRYPTO_MASTER_KEY
   ```

2. **数据库连接错误**
   ```
   问题: 无法连接数据库
   解决: 检查DATABASE_URL配置
   验证: psql $DATABASE_URL -c "SELECT 1;"
   ```

3. **API密钥测试失败**
   ```
   问题: API key test failed
   解决: 
   - 检查密钥是否正确
   - 验证网络连接
   - 查看API配额限制
   ```

4. **管理界面无法访问**
   ```
   问题: 404 Admin interface not found
   解决: 确保static/admin-settings.html文件存在
   验证: ls backend/static/admin-settings.html
   ```

### 日志检查
```bash
# 查看各服务日志
tail -f backend/server.log
tail -f scraper/scraper.log  
tail -f postprocess/postprocess.log
```

## 🎯 下一步

### 推荐操作顺序

1. ✅ **部署基础服务**: 按照上述步骤部署系统
2. ✅ **配置API密钥**: 通过管理界面添加Google和OpenAI密钥
3. ✅ **测试功能**: 验证API密钥和基本功能工作正常
4. ✅ **调整配置**: 根据需要调整处理间隔和功能开关
5. ✅ **监控运行**: 观察日志确保系统稳定运行
6. 🔄 **持续优化**: 根据使用情况调整配置参数

### 扩展功能
- 添加更多LLM提供商支持
- 实现配置变更审计日志
- 添加配置备份和恢复功能
- 集成Kubernetes ConfigMap支持

## 📞 支持

如遇问题，请检查：
1. 📋 本部署指南
2. 📄 `/home/nixos/NewsFrontier/ENHANCED_ENCRYPTION_IMPLEMENTATION.md`
3. 🔍 服务日志文件
4. 🧪 加密功能测试结果

---

🎉 **恭喜！您已成功完成NewsFrontier增强配置系统的部署！**

系统现在支持：
- 🔐 加密API密钥存储
- 🗄️ 数据库驱动配置
- 🤖 多LLM提供商支持  
- ⚙️ 可配置处理间隔
- 🎛️ 功能开关控制
- 🛠️ Web管理界面

开始使用吧！🚀