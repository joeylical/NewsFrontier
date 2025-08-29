# NewsFrontier 多模型架构实现

## 概述

NewsFrontier 现在支持完全可配置的多模型系统，用户可以添加、管理和使用多个LLM模型，支持不同的模型类型和提供商。

## 🏗️ 架构变更

### 1. 数据库架构

#### 新增 `llm_models` 表

```sql
CREATE TABLE llm_models (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL CHECK (name ~ '^[a-zA-Z][a-zA-Z0-9_]*$'),
    model_type VARCHAR(50) NOT NULL CHECK (model_type IN ('chat', 'embedding', 'image', 'audio', 'transcript')),
    provider VARCHAR(100) NOT NULL,  -- LiteLLM provider (openai, anthropic, etc.)
    model_name VARCHAR(200) NOT NULL, -- 实际模型名称 (gpt-4, claude-3-sonnet, etc.)
    api_key_encrypted TEXT,           -- 加密的API密钥
    api_base_url VARCHAR(500),        -- 自定义API endpoint (可选)
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,
    display_order INTEGER DEFAULT 0,
    config_json TEXT,                 -- 额外配置参数 (JSON格式)
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**关键特性:**
- `name`: 用户定义的模型名称，必须符合YAML标识符规范 (`^[a-zA-Z][a-zA-Z0-9_]*$`)
- `model_type`: 模型类型 - chat, embedding, image, audio, transcript
- `provider`: LiteLLM提供商名称 (不在数据库层面限制，由LiteLLM动态验证)
- 每个模型类型只能有一个默认模型 (`unique_default_per_active_type` 约束)

### 2. 核心服务层

#### LLMModelService (`llm_model_service.py`)
- **功能**: LiteLLM提供商验证、模型配置验证、模型管理
- **Provider验证**: 动态从LiteLLM获取支持的提供商列表
- **模型验证**: 验证provider-model组合的兼容性

#### MultiModelLLMClient (`llm_client_multi.py`)
- **功能**: 替代原有LLM客户端，支持多模型动态路由
- **模型缓存**: 5分钟TTL的模型配置缓存
- **API密钥管理**: 自动解密和设置环境变量
- **回退机制**: 如果没有指定模型，使用默认模型或类型的第一个模型

#### 更新的ChainLoader (`chain_loader.py`)
- **新字段支持**: YAML配置中支持 `model_name` 和 `model_type` 字段
- **验证增强**: 验证模型类型的有效性

### 3. YAML配置增强

#### 支持的新字段

```yaml
name: Enhanced Summary Generation
description: Multi-model summary generation with specific model selection
stages:
  - name: extract_key_points
    type: question
    model_name: advanced_chat        # 指定特定模型名称
    model_type: chat                 # 或指定模型类型
    prompt: |
      Extract the key points from this article:
      {{content}}
    llm_params:
      temperature: 0.3
      max_tokens: 500
      
  - name: generate_summary
    type: final
    model_type: chat                 # 使用默认chat模型
    prompt: |
      Based on the key points: {{previous_response}}
      Generate a concise summary.
    llm_params:
      temperature: 0.5
      max_tokens: 200
```

#### 模型选择逻辑
1. **明确指定**: `model_name: "advanced_chat"` - 使用指定模型
2. **类型指定**: `model_type: "chat"` - 使用该类型的默认模型
3. **回退机制**: 无指定时使用第一个chat模型
4. **错误处理**: 如果指定模型不存在，记录错误并回退

### 4. API层更新

#### 新增Pydantic模型
- `LLMModelBase`: 基础模型配置
- `LLMModelCreate`: 创建新模型（包含未加密的API key）
- `LLMModelUpdate`: 更新模型配置
- `LLMModelResponse`: API响应格式

#### 新增CRUD操作
- `llm_model.get_by_name()`: 按名称获取模型
- `llm_model.get_by_type()`: 按类型获取模型列表
- `llm_model.get_default_by_type()`: 获取类型默认模型
- `llm_model.get_first_by_type()`: 获取类型第一个模型

## 🚀 使用示例

### 1. 添加新模型

```python
from newsfrontier_lib.llm_model_service import get_llm_model_service
from newsfrontier_lib.schemas import LLMModelCreate

service = get_llm_model_service()

# 添加Claude模型
claude_model = LLMModelCreate(
    name="claude_sonnet",
    model_type="chat", 
    provider="anthropic",
    model_name="claude-3-sonnet-20240229",
    api_key="sk-ant-xxx...",  # 将被自动加密
    is_default=False,
    description="Claude 3 Sonnet for advanced reasoning"
)

with get_db_session() as db:
    model = service.create_model(db, claude_model)
    print(f"Created model: {model.name}")
```

### 2. 在YAML中使用模型

```yaml
name: Multi-Model News Analysis
stages:
  - name: extract_entities
    model_name: claude_sonnet        # 使用Claude进行实体提取
    prompt: "Extract entities from: {{content}}"
    
  - name: generate_embedding
    model_type: embedding            # 使用默认embedding模型
    prompt: "{{title}} {{content}}"
    
  - name: final_summary
    model_name: advanced_chat        # 使用GPT-4生成最终摘要
    prompt: "Summarize based on entities: {{stage_1_response}}"
```

### 3. 程序化调用

```python
from newsfrontier_lib.llm_client_multi import get_multi_model_llm_client

client = get_multi_model_llm_client()

# 使用指定模型
response = client.create_completion(
    prompt="Analyze this news article...",
    model_name="claude_sonnet",
    max_tokens=1000
)

# 使用默认chat模型
response = client.create_completion(
    prompt="Generate a summary...",
    max_tokens=500
)

# 生成embedding
embedding = client.generate_embedding(
    text="News article content",
    model_name="large_embedding"  # 或不指定使用默认
)
```

## 🔧 配置要求

### 最低要求
- **至少一个chat模型**: 用于文本生成
- **至少一个embedding模型**: 用于向量操作

### 默认配置
系统自动创建以下默认模型：
- `default_chat`: gpt-3.5-turbo (默认chat模型)
- `default_embedding`: text-embedding-ada-002 (默认embedding模型)  
- `advanced_chat`: gpt-4 (高级chat模型)
- `large_embedding`: text-embedding-3-large (大型embedding模型)

## 🔐 安全特性

1. **API密钥加密**: 所有API密钥使用系统加密密钥加密存储
2. **环境变量隔离**: API密钥只在运行时设置到环境变量
3. **访问控制**: 通过数据库约束确保模型名称的唯一性和格式
4. **Provider验证**: 使用LiteLLM动态验证提供商支持

## 🎯 优势

1. **灵活性**: 支持任意LiteLLM兼容的提供商和模型
2. **可扩展性**: 新模型类型和提供商可轻松添加
3. **向后兼容**: 现有YAML配置无需修改即可工作
4. **性能优化**: 模型配置缓存减少数据库查询
5. **错误恢复**: 智能回退机制确保系统稳定性

## 🔄 迁移路径

现有系统会自动迁移到新架构：
1. 保留现有system_settings配置（向后兼容）
2. 自动创建默认模型配置
3. 现有YAML配置继续工作（使用默认模型）
4. 逐步迁移到使用model_name/model_type字段

这个架构为NewsFrontier提供了强大的多模型支持能力，使用户能够根据具体需求选择最适合的模型，同时保持系统的简单性和稳定性。