# Prompt 测试脚本

这个目录包含了用于测试NewsFrontier postprocess中各个prompt的独立测试脚本。每个脚本都模拟与程序相同的逻辑，可以用参数指定输入数据。

## 脚本概览

### 单独测试脚本

1. **`test_summary_creation.py`** - 测试文章摘要生成prompt
2. **`test_cluster_detection.py`** - 测试事件聚类检测prompt
3. **`test_daily_summary.py`** - 测试每日摘要生成prompt
4. **`test_cover_image_generation.py`** - 测试封面图片描述生成prompt

### 便捷执行脚本

- **`run_prompt_tests.sh`** - 统一的Shell脚本，简化测试执行

## 快速开始

### 环境准备

1. 确保已安装uv：
```bash
pip install uv
```

2. 设置API密钥（必需）：
```bash
export GOOGLE_API_KEY=your_google_api_key_here
```

或者在项目根目录的`.env`文件中配置。

### 使用Shell脚本（推荐）

```bash
# 进入postprocess目录
cd postprocess

# 查看使用说明
./test_prompts/run_prompt_tests.sh --help

# 使用示例数据测试所有prompt
GOOGLE_API_KEY=your_key ./test_prompts/run_prompt_tests.sh all --sample

# 测试特定prompt
GOOGLE_API_KEY=your_key ./test_prompts/run_prompt_tests.sh summary --sample
GOOGLE_API_KEY=your_key ./test_prompts/run_prompt_tests.sh cluster --article-id 123
GOOGLE_API_KEY=your_key ./test_prompts/run_prompt_tests.sh daily --user-id 1
GOOGLE_API_KEY=your_key ./test_prompts/run_prompt_tests.sh cover --summary-id 456
```

### 直接使用uv run

```bash
# 进入postprocess目录
cd postprocess

# 测试摘要生成
GOOGLE_API_KEY=your_key uv run test_prompts/test_summary_creation.py --sample
GOOGLE_API_KEY=your_key uv run test_prompts/test_summary_creation.py --article-id 123

# 测试聚类检测
GOOGLE_API_KEY=your_key uv run test_prompts/test_cluster_detection.py --sample --user-id 1
GOOGLE_API_KEY=your_key uv run test_prompts/test_cluster_detection.py --article-id 456 --user-id 2

# 测试每日摘要
GOOGLE_API_KEY=your_key uv run test_prompts/test_daily_summary.py --sample
GOOGLE_API_KEY=your_key uv run test_prompts/test_daily_summary.py --user-id 1 --date 2024-01-15

# 测试封面图片生成
GOOGLE_API_KEY=your_key uv run test_prompts/test_cover_image_generation.py --sample
GOOGLE_API_KEY=your_key uv run test_prompts/test_cover_image_generation.py --summary-id 789
```

## 详细说明

### 1. 摘要生成测试 (`test_summary_creation.py`)

**功能**: 测试文章摘要生成prompt的效果

**参数**:
- `--article-id ID`: 指定要测试的文章ID
- `--sample`: 使用内置示例数据
- `--config PATH`: 指定配置文件路径

**输出**: 
- 原文章内容
- 生成的摘要
- 使用的prompt内容

**示例**:
```bash
# 使用示例数据
python3 test_summary_creation.py --sample

# 使用真实文章
python3 test_summary_creation.py --article-id 123
```

### 2. 聚类检测测试 (`test_cluster_detection.py`)

**功能**: 测试事件聚类决策prompt的效果

**参数**:
- `--article-id ID`: 指定要测试的文章ID
- `--user-id ID`: 指定用户ID（默认: 1）
- `--sample`: 使用内置示例数据
- `--config PATH`: 指定配置文件路径

**输出**:
- 文章信息和摘要
- 相关主题列表
- 现有事件列表
- 聚类决策结果（assign/create/ignore）

**示例**:
```bash
# 使用示例数据
python3 test_cluster_detection.py --sample --user-id 1

# 使用真实文章
python3 test_cluster_detection.py --article-id 456 --user-id 2
```

### 3. 每日摘要测试 (`test_daily_summary.py`)

**功能**: 测试每日摘要生成prompt的效果

**参数**:
- `--user-id ID`: 指定用户ID（默认: 1）
- `--date YYYY-MM-DD`: 指定日期（默认: 昨天）
- `--sample`: 使用内置示例数据
- `--config PATH`: 指定配置文件路径

**输出**:
- 用户上下文信息
- 文章列表
- 生成的每日摘要
- 摘要统计信息

**示例**:
```bash
# 使用示例数据
python3 test_daily_summary.py --sample

# 使用真实用户数据
python3 test_daily_summary.py --user-id 1 --date 2024-01-15
```

### 4. 封面图片生成测试 (`test_cover_image_generation.py`)

**功能**: 测试封面图片描述生成prompt的效果

**参数**:
- `--summary-id ID`: 指定每日摘要ID
- `--sample`: 使用内置示例数据
- `--config PATH`: 指定配置文件路径

**输出**:
- 摘要内容预览
- 生成的图片描述
- 描述分析（颜色、构图等元素检测）

**示例**:
```bash
# 使用示例数据
python3 test_cover_image_generation.py --sample

# 使用真实摘要
python3 test_cover_image_generation.py --summary-id 789
```

## 测试数据

### 示例数据模式

每个测试脚本都包含内置的示例数据，包括：

- **文章数据**: 标题、内容、分类、作者等
- **用户数据**: 用户偏好、订阅分类等
- **摘要数据**: 每日摘要内容、统计信息等

### 真实数据模式

测试脚本可以连接到后端API获取真实数据：

- 通过article_id获取文章
- 通过user_id获取用户上下文
- 通过summary_id获取每日摘要

## 配置文件

测试脚本使用与postprocess相同的配置文件（通常是`config.json`）。如果需要使用不同的配置，可以通过`--config`参数指定。

配置文件应包含：
- LLM API密钥
- 后端服务地址
- 数据库连接信息

## 输出格式

所有测试脚本都提供详细的输出，包括：

1. **输入数据显示**: 显示用于测试的原始数据
2. **处理过程**: 显示AI处理的中间步骤
3. **输出结果**: 显示最终生成的内容
4. **使用的Prompt**: 显示实际使用的prompt内容
5. **统计信息**: 显示字数、字符数等统计数据
6. **错误处理**: 清晰的错误信息和调试信息

## 故障排除

### 常见问题

1. **配置文件未找到**
   - 确保`config.json`存在于项目根目录
   - 或使用`--config`参数指定配置文件路径

2. **API密钥错误**
   - 检查配置文件中的LLM API密钥
   - 确保API密钥有效且有足够的额度

3. **网络连接问题**
   - 检查后端服务是否运行
   - 确保网络连接正常

4. **数据库连接失败**
   - 确保数据库服务运行正常
   - 检查数据库连接配置

### 调试模式

可以通过修改脚本中的日志级别来获取更详细的调试信息：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 扩展测试

### 添加新的测试场景

要添加新的测试场景，可以：

1. 在相应的测试脚本中添加新的示例数据
2. 创建新的测试方法
3. 在`run_prompt_tests.sh`中添加新的选项

### 批量测试

可以创建批量测试脚本来测试多个文章或用户：

```bash
#!/bin/bash
for article_id in 100 101 102 103; do
    echo "Testing article $article_id"
    python3 test_summary_creation.py --article-id $article_id
done
```

## 性能监控

测试脚本会显示执行时间和资源使用情况，可以用于：

- 性能优化
- prompt效果评估
- API调用成本估算

## 集成到CI/CD

这些测试脚本可以集成到持续集成流程中，用于：

- 自动化prompt测试
- 回归测试
- 性能监控
- 质量控制