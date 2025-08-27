"""
Multi-stage summary generation chains for NewsFrontier.

This module defines predefined question sets and branching logic
for creating high-quality article summaries using smaller models.
"""

from typing import Dict, Any
from .multi_stage_generator import (
    ChainConfig, StageConfig, StageType,
    create_binary_question_stage, create_category_question_stage, 
    create_final_generation_stage
)


def create_article_summary_chain() -> ChainConfig:
    """
    Create a multi-stage chain for article summarization.
    
    Flow:
    1. Determine if content is news or general article
    2. For news: categorize by type (breaking, analysis, etc.)
    3. For general: categorize by content type (technical, opinion, etc.)
    4. Generate appropriate summary based on category
    """
    
    stages = {}
    
    # Stage 1: Determine content type
    stages["content_type"] = create_binary_question_stage(
        stage_id="content_type",
        prompt="""分析以下文章内容，判断这是新闻报道还是一般性文章：

标题：{title}
内容：{clean_text}

新闻报道特征：时效性强、报道事实、包含时间地点人物等新闻要素
一般性文章特征：观点分析、技术教程、产品介绍、个人博客等

这是新闻报道吗？""",
        yes_stage="news_category",
        no_stage="general_category",
        required_vars=["title", "clean_text"]
    )
    
    # Stage 2a: Categorize news articles
    stages["news_category"] = create_category_question_stage(
        stage_id="news_category",
        prompt="""对以下新闻文章进行分类：

标题：{title}
内容：{clean_text}

请从以下类别中选择最合适的一个：
- 突发新闻：紧急事件、事故、突发状况
- 政策新闻：政府政策、法规变化、官方声明  
- 财经新闻：股市、经济数据、公司财报、市场分析
- 科技新闻：新产品发布、技术进展、行业动态
- 社会新闻：社会事件、民生话题、文化教育
- 体育新闻：比赛结果、体育赛事、运动员动态
- 国际新闻：国际关系、外交、海外事件

分类结果：""",
        categories={
            "突发新闻": "breaking_news_summary",
            "政策新闻": "policy_news_summary", 
            "财经新闻": "finance_news_summary",
            "科技新闻": "tech_news_summary",
            "社会新闻": "social_news_summary",
            "体育新闻": "sports_news_summary",
            "国际新闻": "international_news_summary"
        },
        required_vars=["title", "clean_text"]
    )
    
    # Stage 2b: Categorize general articles
    stages["general_category"] = create_category_question_stage(
        stage_id="general_category", 
        prompt="""对以下文章内容进行分类：

标题：{title}
内容：{clean_text}

请从以下类别中选择最合适的一个：
- 技术教程：编程、操作指南、技术解析
- 观点分析：评论、分析、个人见解
- 产品介绍：产品评测、功能介绍、使用体验
- 学术研究：研究报告、学术论文、科学发现
- 生活百科：健康、旅游、美食、生活技巧
- 商业资讯：行业分析、商业模式、创业经验

分类结果：""",
        categories={
            "技术教程": "tech_tutorial_summary",
            "观点分析": "opinion_analysis_summary",
            "产品介绍": "product_intro_summary", 
            "学术研究": "academic_research_summary",
            "生活百科": "lifestyle_summary",
            "商业资讯": "business_summary"
        },
        required_vars=["title", "clean_text"]
    )
    
    # News summary stages
    stages["breaking_news_summary"] = create_final_generation_stage(
        stage_id="breaking_news_summary",
        prompt="""为以下突发新闻创建简洁的摘要，重点突出关键事实和时效信息：

标题：{title}
内容：{clean_text}

请创建一个结构化的摘要，包含：
- 核心事件（1句话概括）
- 关键信息（时间、地点、涉及人员等）
- 当前状态或最新进展
- 潜在影响或后续发展

要求：
- 使用简洁明了的语言
- 突出事件的紧急性和重要性
- 信息准确，避免推测
- 控制在200字以内

摘要：""",
        required_vars=["title", "clean_text"],
        model_preference="summary",
        temperature=0.3
    )
    
    stages["policy_news_summary"] = create_final_generation_stage(
        stage_id="policy_news_summary",
        prompt="""为以下政策新闻创建摘要，重点解释政策内容和影响：

标题：{title}
内容：{clean_text}

请创建一个结构化的摘要，包含：
- 政策概述（核心内容是什么）
- 实施时间和适用范围
- 主要变化或新增内容
- 对相关群体或行业的影响
- 配套措施或注意事项

要求：
- 用通俗易懂的语言解释专业术语
- 突出政策的实用性和影响面
- 保持客观中立的立场
- 控制在250字以内

摘要：""",
        required_vars=["title", "clean_text"],
        model_preference="analysis",
        temperature=0.4
    )
    
    stages["finance_news_summary"] = create_final_generation_stage(
        stage_id="finance_news_summary",
        prompt="""为以下财经新闻创建摘要，重点分析经济影响和趋势：

标题：{title}
内容：{clean_text}

请创建一个结构化的摘要，包含：
- 核心财经事件或数据
- 关键数字和变化趋势
- 市场反应或影响
- 行业或经济层面的意义
- 投资者或消费者关注点

要求：
- 突出重要的财经数据和指标
- 解释专业术语和市场术语
- 保持客观分析，避免投资建议
- 控制在250字以内

摘要：""",
        required_vars=["title", "clean_text"],
        model_preference="analysis",
        temperature=0.4
    )
    
    stages["tech_news_summary"] = create_final_generation_stage(
        stage_id="tech_news_summary",
        prompt="""为以下科技新闻创建摘要，重点介绍技术创新和行业影响：

标题：{title}
内容：{clean_text}

请创建一个结构化的摘要，包含：
- 核心技术或产品亮点
- 创新点和技术优势
- 应用场景和用户价值
- 行业竞争和市场影响
- 未来发展前景

要求：
- 用通俗语言解释技术概念
- 突出创新价值和实用性
- 保持对技术发展的客观评价
- 控制在250字以内

摘要：""",
        required_vars=["title", "clean_text"],
        model_preference="summary",
        temperature=0.5
    )
    
    stages["social_news_summary"] = create_final_generation_stage(
        stage_id="social_news_summary",
        prompt="""为以下社会新闻创建摘要，重点关注社会意义和民生影响：

标题：{title}
内容：{clean_text}

请创建一个结构化的摘要，包含：
- 事件核心内容
- 涉及的社会群体或地区
- 社会反响和公众关注点
- 相关政策或制度背景
- 社会意义和启示

要求：
- 保持人文关怀和社会责任感
- 客观报道，避免主观判断
- 关注事件的社会价值和教育意义
- 控制在250字以内

摘要：""",
        required_vars=["title", "clean_text"],
        model_preference="analysis",
        temperature=0.4
    )
    
    stages["sports_news_summary"] = create_final_generation_stage(
        stage_id="sports_news_summary",
        prompt="""为以下体育新闻创建摘要，重点突出比赛结果和精彩看点：

标题：{title}
内容：{clean_text}

请创建一个结构化的摘要，包含：
- 比赛结果或核心体育事件
- 关键表现和精彩瞬间
- 运动员或队伍亮点
- 比赛意义和后续影响
- 观众和粉丝关注点

要求：
- 突出体育竞技的精彩和激情
- 用生动的语言描述关键时刻
- 保持体育精神和正面价值观
- 控制在200字以内

摘要：""",
        required_vars=["title", "clean_text"],
        model_preference="summary",
        temperature=0.6
    )
    
    stages["international_news_summary"] = create_final_generation_stage(
        stage_id="international_news_summary",
        prompt="""为以下国际新闻创建摘要，重点分析国际关系和全球影响：

标题：{title}
内容：{clean_text}

请创建一个结构化的摘要，包含：
- 核心国际事件或外交动态
- 涉及的国家和国际组织
- 事件的国际背景和历史脉络
- 对国际关系的影响
- 对中国或相关地区的意义

要求：
- 保持国际视野和客观立场
- 解释复杂的国际关系背景
- 突出事件的全球意义
- 控制在250字以内

摘要：""",
        required_vars=["title", "clean_text"],
        model_preference="analysis",
        temperature=0.4
    )
    
    # General article summary stages
    stages["tech_tutorial_summary"] = create_final_generation_stage(
        stage_id="tech_tutorial_summary",
        prompt="""为以下技术教程创建摘要，重点突出学习价值和实用性：

标题：{title}
内容：{clean_text}

请创建一个结构化的摘要，包含：
- 教程主要内容和学习目标
- 适合的技能水平和受众
- 核心技术点和关键步骤
- 实际应用场景和价值
- 学习建议和注意事项

要求：
- 突出教程的实用性和可操作性
- 用简洁明了的语言总结技术要点
- 帮助读者快速了解学习内容
- 控制在200字以内

摘要：""",
        required_vars=["title", "clean_text"],
        model_preference="summary",
        temperature=0.4
    )
    
    stages["opinion_analysis_summary"] = create_final_generation_stage(
        stage_id="opinion_analysis_summary",
        prompt="""为以下观点分析文章创建摘要，重点提炼核心观点和论证逻辑：

标题：{title}
内容：{clean_text}

请创建一个结构化的摘要，包含：
- 作者的核心观点或结论
- 主要论证思路和支撑证据
- 分析的对象或现象
- 观点的独特性或争议性
- 对读者的启发意义

要求：
- 客观总结作者观点，不加入个人判断
- 突出分析的逻辑性和深度
- 保持观点的原意和重点
- 控制在250字以内

摘要：""",
        required_vars=["title", "clean_text"],
        model_preference="analysis",
        temperature=0.3
    )
    
    stages["product_intro_summary"] = create_final_generation_stage(
        stage_id="product_intro_summary",
        prompt="""为以下产品介绍创建摘要，重点突出产品特色和用户价值：

标题：{title}
内容：{clean_text}

请创建一个结构化的摘要，包含：
- 产品基本信息和定位
- 核心功能和特色亮点
- 目标用户和使用场景
- 优势对比和竞争力
- 购买建议或使用体验

要求：
- 突出产品的实用价值和差异化优势
- 用客观的语言描述产品特点
- 帮助读者快速了解产品价值
- 控制在200字以内

摘要：""",
        required_vars=["title", "clean_text"],
        model_preference="summary",
        temperature=0.5
    )
    
    stages["academic_research_summary"] = create_final_generation_stage(
        stage_id="academic_research_summary",
        prompt="""为以下学术研究创建摘要，重点提炼研究贡献和科学价值：

标题：{title}
内容：{clean_text}

请创建一个结构化的摘要，包含：
- 研究问题和研究目的
- 主要研究方法和数据来源
- 核心发现和重要结论
- 学术贡献和创新点
- 实际应用价值和意义

要求：
- 用通俗语言解释专业概念
- 突出研究的科学严谨性和价值
- 保持学术客观性和准确性
- 控制在250字以内

摘要：""",
        required_vars=["title", "clean_text"],
        model_preference="analysis",
        temperature=0.3
    )
    
    stages["lifestyle_summary"] = create_final_generation_stage(
        stage_id="lifestyle_summary",
        prompt="""为以下生活类文章创建摘要，重点突出实用价值和生活指导：

标题：{title}
内容：{clean_text}

请创建一个结构化的摘要，包含：
- 文章主要内容和主题
- 实用的生活技巧或建议
- 适用的人群和场景
- 操作方法和注意事项
- 生活改善的效果和价值

要求：
- 突出内容的实用性和可操作性
- 用亲和的语言传达生活智慧
- 关注读者的实际需求和体验
- 控制在200字以内

摘要：""",
        required_vars=["title", "clean_text"],
        model_preference="summary",
        temperature=0.6
    )
    
    stages["business_summary"] = create_final_generation_stage(
        stage_id="business_summary",
        prompt="""为以下商业资讯创建摘要，重点分析商业价值和行业趋势：

标题：{title}
内容：{clean_text}

请创建一个结构化的摘要，包含：
- 核心商业信息或行业动态
- 商业模式和盈利逻辑
- 市场机会和挑战分析
- 行业趋势和发展方向
- 对企业和从业者的启示

要求：
- 突出商业洞察和行业价值
- 保持商业分析的客观性和深度
- 关注实用的商业知识和经验
- 控制在250字以内

摘要：""",
        required_vars=["title", "clean_text"],
        model_preference="analysis",
        temperature=0.4
    )
    
    return ChainConfig(
        name="article_summary",
        description="Multi-stage article summarization with content type detection and specialized processing",
        initial_stage="content_type",
        stages=stages
    )


def create_simple_summary_chain() -> ChainConfig:
    """
    Create a simplified summary chain for fallback use.
    
    Single stage that creates a general-purpose summary.
    """
    
    stages = {
        "simple_summary": create_final_generation_stage(
            stage_id="simple_summary",
            prompt="""为以下文章创建简洁明了的摘要：

标题：{title}
内容：{clean_text}

请创建一个结构化的摘要，包含：
- 文章核心内容概述
- 主要观点或重要信息
- 实用价值或关键takeaway

要求：
- 使用简洁明了的语言
- 突出最重要的信息和价值
- 保持内容的准确性和完整性
- 控制在200字以内

摘要：""",
            required_vars=["title", "clean_text"],
            model_preference="summary",
            temperature=0.5
        )
    }
    
    return ChainConfig(
        name="simple_summary",
        description="Single-stage general purpose summarization",
        initial_stage="simple_summary", 
        stages=stages
    )