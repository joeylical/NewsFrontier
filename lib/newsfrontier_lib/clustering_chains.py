"""
Multi-stage clustering chains for NewsFrontier.

This module defines predefined question sets and branching logic
for intelligent event clustering and detection using smaller models.
"""

from typing import Dict, Any, List
from .multi_stage_generator import (
    ChainConfig, StageConfig, StageType,
    create_binary_question_stage, create_category_question_stage, 
    create_final_generation_stage
)


def create_clustering_detection_chain() -> ChainConfig:
    """
    Create a multi-stage chain for event clustering detection.
    
    Flow:
    1. Determine if article represents a new event or relates to existing ones
    2. If related: find the best matching existing event
    3. If new: categorize the event type for proper naming
    4. Generate appropriate event description and metadata
    """
    
    stages = {}
    
    # Stage 1: New event vs existing event detection
    stages["event_novelty"] = StageConfig(
        id="event_novelty",
        stage_type=StageType.QUESTION,
        prompt_template="""分析以下文章是否描述了一个全新的事件，还是与已有事件相关：

文章标题：{title}
文章摘要：{summary}

现有相关事件：
{existing_events_context}

判断标准：
- 全新事件：描述的是独立的、之前未发生的事件
- 相关事件：是已有事件的后续发展、补充报道或不同角度

这篇文章描述的是全新事件吗？请回答：是 或 否""",
        expected_responses={
            "是": "new_event_category",
            "yes": "new_event_category", 
            "y": "new_event_category",
            "否": "existing_event_match",
            "no": "existing_event_match",
            "n": "existing_event_match"
        },
        required_variables=["title", "summary", "existing_events_context"],
        temperature=0.2
    )
    
    # Stage 2a: Categorize new events by type
    stages["new_event_category"] = create_category_question_stage(
        stage_id="new_event_category",
        prompt="""为以下新事件确定最合适的类别：

文章标题：{title}
文章摘要：{summary}

请从以下事件类别中选择最合适的一个：
- 突发事件：自然灾害、事故、紧急情况
- 政策发布：政府政策、法规变化、官方声明
- 商业动态：公司发布、合作协议、市场变化
- 技术进展：新产品、技术突破、研发成果
- 社会事件：社会现象、民生事件、文化活动
- 体育赛事：比赛、竞技、体育活动
- 国际事务：外交、国际合作、跨国事件
- 学术研究：科研成果、学术发现、研究报告

事件类别：""",
        categories={
            "突发事件": "breaking_event_creation",
            "政策发布": "policy_event_creation",
            "商业动态": "business_event_creation", 
            "技术进展": "tech_event_creation",
            "社会事件": "social_event_creation",
            "体育赛事": "sports_event_creation",
            "国际事务": "international_event_creation",
            "学术研究": "research_event_creation"
        },
        required_vars=["title", "summary"]
    )
    
    # Stage 2b: Match with existing events
    stages["existing_event_match"] = StageConfig(
        id="existing_event_match",
        stage_type=StageType.QUESTION,
        prompt_template="""确定以下文章最相关的已有事件：

文章标题：{title}
文章摘要：{summary}

现有事件列表：
{existing_events_detailed}

请选择最相关的事件编号，或回答"无匹配"如果没有合适的：

最相关的事件编号：""",
        expected_responses={
            # This will be dynamically populated based on existing events
            "无匹配": "new_event_category",
            "none": "new_event_category",
            "无": "new_event_category"
        },
        response_extractor=r"(\d+|无匹配|none|无)",
        required_variables=["title", "summary", "existing_events_detailed"],
        temperature=0.3
    )
    
    # New event creation stages
    stages["breaking_event_creation"] = create_final_generation_stage(
        stage_id="breaking_event_creation",
        prompt="""为以下突发事件创建事件描述：

文章标题：{title}
文章摘要：{summary}

请创建一个突发事件描述，包含：
- 事件名称（简洁明了，10字以内）
- 事件描述（客观描述事件核心内容）
- 关键要素（时间、地点、涉及对象等）
- 紧急程度和影响范围
- 后续关注点

格式要求：
事件名称：[事件名称]
事件描述：[详细描述]

事件名称：""",
        required_vars=["title", "summary"],
        model_preference="analysis",
        temperature=0.4
    )
    
    stages["policy_event_creation"] = create_final_generation_stage(
        stage_id="policy_event_creation",
        prompt="""为以下政策事件创建事件描述：

文章标题：{title}
文章摘要：{summary}

请创建一个政策事件描述，包含：
- 事件名称（突出政策主题，10字以内）
- 政策内容概述
- 实施时间和范围
- 影响对象和程度
- 政策意义和价值

格式要求：
事件名称：[事件名称]
事件描述：[详细描述]

事件名称：""",
        required_vars=["title", "summary"],
        model_preference="analysis",
        temperature=0.3
    )
    
    stages["business_event_creation"] = create_final_generation_stage(
        stage_id="business_event_creation", 
        prompt="""为以下商业事件创建事件描述：

文章标题：{title}
文章摘要：{summary}

请创建一个商业事件描述，包含：
- 事件名称（突出商业行为，10字以内）
- 商业活动内容
- 涉及的企业和行业
- 市场影响和意义
- 行业趋势体现

格式要求：
事件名称：[事件名称]
事件描述：[详细描述]

事件名称：""",
        required_vars=["title", "summary"],
        model_preference="analysis",
        temperature=0.4
    )
    
    stages["tech_event_creation"] = create_final_generation_stage(
        stage_id="tech_event_creation",
        prompt="""为以下技术事件创建事件描述：

文章标题：{title}
文章摘要：{summary}

请创建一个技术事件描述，包含：
- 事件名称（突出技术亮点，10字以内）
- 技术内容和创新点
- 应用领域和场景
- 技术意义和价值
- 行业影响和趋势

格式要求：
事件名称：[事件名称]
事件描述：[详细描述]

事件名称：""",
        required_vars=["title", "summary"],
        model_preference="analysis",
        temperature=0.5
    )
    
    stages["social_event_creation"] = create_final_generation_stage(
        stage_id="social_event_creation",
        prompt="""为以下社会事件创建事件描述：

文章标题：{title}
文章摘要：{summary}

请创建一个社会事件描述，包含：
- 事件名称（反映社会现象，10字以内）
- 事件内容和背景
- 社会群体和地区
- 社会意义和影响
- 公众关注和反响

格式要求：
事件名称：[事件名称]
事件描述：[详细描述]

事件名称：""",
        required_vars=["title", "summary"],
        model_preference="analysis",
        temperature=0.4
    )
    
    stages["sports_event_creation"] = create_final_generation_stage(
        stage_id="sports_event_creation",
        prompt="""为以下体育事件创建事件描述：

文章标题：{title}
文章摘要：{summary}

请创建一个体育事件描述，包含：
- 事件名称（突出体育亮点，10字以内）
- 比赛或活动内容
- 参与的运动员或队伍
- 比赛结果和表现
- 体育意义和价值

格式要求：
事件名称：[事件名称]
事件描述：[详细描述]

事件名称：""",
        required_vars=["title", "summary"],
        model_preference="summary",
        temperature=0.5
    )
    
    stages["international_event_creation"] = create_final_generation_stage(
        stage_id="international_event_creation",
        prompt="""为以下国际事件创建事件描述：

文章标题：{title}
文章摘要：{summary}

请创建一个国际事件描述，包含：
- 事件名称（体现国际性质，10字以内）
- 事件内容和背景
- 涉及的国家和组织
- 国际关系影响
- 地缘政治意义

格式要求：
事件名称：[事件名称]
事件描述：[详细描述]

事件名称：""",
        required_vars=["title", "summary"],
        model_preference="analysis",
        temperature=0.4
    )
    
    stages["research_event_creation"] = create_final_generation_stage(
        stage_id="research_event_creation",
        prompt="""为以下学术研究事件创建事件描述：

文章标题：{title}
文章摘要：{summary}

请创建一个学术事件描述，包含：
- 事件名称（突出研究主题，10字以内）
- 研究内容和发现
- 学术机构和研究者
- 科学价值和创新性
- 应用前景和意义

格式要求：
事件名称：[事件名称]
事件描述：[详细描述]

事件名称：""",
        required_vars=["title", "summary"],
        model_preference="analysis",
        temperature=0.4
    )
    
    return ChainConfig(
        name="clustering_detection",
        description="Multi-stage event clustering with novelty detection and specialized event creation",
        initial_stage="event_novelty",
        stages=stages
    )


def create_event_similarity_chain() -> ChainConfig:
    """
    Create a chain specifically for determining event similarity.
    
    Used when embedding-based similarity is inconclusive.
    """
    
    stages = {
        "similarity_analysis": create_final_generation_stage(
            stage_id="similarity_analysis",
            prompt="""深度分析两个事件的相似性：

事件A：
标题：{title_a}
描述：{description_a}

事件B：
标题：{title_b}  
描述：{description_b}

分析维度：
1. 主题相似性：是否涉及相同或相关的主题领域
2. 时间相关性：是否发生在相近的时间段
3. 空间相关性：是否涉及相同或相近的地理位置
4. 参与者相关性：是否涉及相同的人物、组织或机构
5. 因果关系：是否存在因果关系或逻辑连接
6. 影响范围：是否影响相同的群体或领域

基于以上分析，请给出相似性评分（0-100分）和理由。

格式：
相似性评分：[0-100]
主要理由：[详细分析]

相似性评分：""",
            required_vars=["title_a", "description_a", "title_b", "description_b"],
            model_preference="analysis",
            temperature=0.3
        )
    }
    
    return ChainConfig(
        name="event_similarity",
        description="Deep analysis of event similarity for clustering decisions",
        initial_stage="similarity_analysis",
        stages=stages
    )


def create_simple_clustering_chain() -> ChainConfig:
    """
    Create a simplified clustering chain for fallback use.
    
    Single stage that makes a clustering decision based on simple heuristics.
    """
    
    stages = {
        "simple_clustering": create_final_generation_stage(
            stage_id="simple_clustering",
            prompt="""分析文章是否应该创建新事件或归类到现有事件：

文章标题：{title}
文章摘要：{summary}

现有相关事件：
{existing_events_context}

请判断：
- 如果文章描述全新的独立事件，回答"创建新事件"并提供事件名称
- 如果文章与现有事件相关，回答"归类现有事件"并指明最相关的事件编号

格式：
决策：[创建新事件/归类现有事件]
理由：[简要说明]
事件名称或编号：[具体内容]

决策：""",
            required_vars=["title", "summary", "existing_events_context"],
            model_preference="analysis",
            temperature=0.4
        )
    }
    
    return ChainConfig(
        name="simple_clustering",
        description="Single-stage clustering decision making",
        initial_stage="simple_clustering",
        stages=stages
    )


def create_event_naming_chain() -> ChainConfig:
    """
    Create a specialized chain for generating event names.
    
    Used when we need to create a concise, descriptive name for a new event.
    """
    
    stages = {}
    
    # Stage 1: Determine event scope (local, national, international)
    stages["event_scope"] = create_category_question_stage(
        stage_id="event_scope",
        prompt="""确定以下事件的地理影响范围：

标题：{title}
描述：{event_description}

请选择最合适的影响范围：
- 本地：影响特定城市、地区或社区
- 国内：影响整个国家或多个省份/州
- 国际：跨国影响或全球关注
- 行业：特定行业或专业领域

影响范围：""",
        categories={
            "本地": "local_event_naming",
            "国内": "national_event_naming", 
            "国际": "international_event_naming",
            "行业": "industry_event_naming"
        },
        required_vars=["title", "event_description"]
    )
    
    # Naming stages for different scopes
    stages["local_event_naming"] = create_final_generation_stage(
        stage_id="local_event_naming",
        prompt="""为以下本地事件创建简洁的名称：

标题：{title}
事件描述：{event_description}

要求：
- 突出地理位置（城市、地区）
- 体现事件核心内容
- 便于理解和记忆
- 控制在8-12个字

请提供3个候选名称：

候选名称：""",
        required_vars=["title", "event_description"],
        model_preference="summary",
        temperature=0.6
    )
    
    stages["national_event_naming"] = create_final_generation_stage(
        stage_id="national_event_naming", 
        prompt="""为以下国家级事件创建简洁的名称：

标题：{title}
事件描述：{event_description}

要求：
- 体现国家层面的重要性
- 突出事件的核心特征
- 具有权威性和正式感
- 控制在8-12个字

请提供3个候选名称：

候选名称：""",
        required_vars=["title", "event_description"],
        model_preference="summary",
        temperature=0.5
    )
    
    stages["international_event_naming"] = create_final_generation_stage(
        stage_id="international_event_naming",
        prompt="""为以下国际事件创建简洁的名称：

标题：{title}
事件描述：{event_description}

要求：
- 体现国际性和全球影响
- 便于国际理解和传播
- 具有历史意义感
- 控制在8-12个字

请提供3个候选名称：

候选名称：""",
        required_vars=["title", "event_description"],
        model_preference="summary",
        temperature=0.5
    )
    
    stages["industry_event_naming"] = create_final_generation_stage(
        stage_id="industry_event_naming",
        prompt="""为以下行业事件创建简洁的名称：

标题：{title}
事件描述：{event_description}

要求：
- 突出行业特色和专业性
- 体现事件对行业的意义
- 便于业内人士理解
- 控制在8-12个字

请提供3个候选名称：

候选名称：""",
        required_vars=["title", "event_description"],
        model_preference="summary", 
        temperature=0.6
    )
    
    return ChainConfig(
        name="event_naming",
        description="Specialized event naming based on scope and impact",
        initial_stage="event_scope",
        stages=stages
    )