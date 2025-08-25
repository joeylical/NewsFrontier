#!/usr/bin/env python3
"""
测试cluster_detection prompt的脚本
使用与postprocess相同的逻辑测试事件聚类决策功能
"""

import sys
import os
import argparse
import asyncio
import json
from pathlib import Path

# 导入共享库
from newsfrontier_lib import get_llm_client, create_summary, generate_content_embedding
import requests
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# 获取项目根目录
project_root = Path(__file__).parent.parent.parent


class ClusterDetectionTester:
    def __init__(self, config_path=None):
        """初始化测试器"""
        self.config_path = config_path or os.path.join(project_root, 'scripts', 'config.json')
        self.llm_client = None
        self.backend_url = "http://localhost:8000"
        
    async def setup(self):
        """设置AI服务"""
        self.llm_client = get_llm_client()
        # 加载prompts从文件而不是数据库
        await self._load_prompts_from_files()
        
    async def test_with_article_id(self, article_id, user_id=None):
        """使用article ID测试聚类检测"""
        print(f"Testing cluster detection with article ID: {article_id}")
        
        # 从后端获取文章数据
        article = await self._get_article_by_id(article_id)
        if not article:
            print(f"Error: Article with ID {article_id} not found")
            return None
            
        # 如果没有指定user_id，使用文章的user_id或默认值
        test_user_id = user_id or article.get('user_id', 1)
        
        return await self._test_cluster_detection(article, test_user_id)
        
    async def test_with_sample_data(self, user_id=1):
        """使用示例数据测试聚类检测"""
        print("Testing cluster detection with sample data")
        
        sample_article = {
            'id': 999999,
            'title': '特斯拉发布新款电动汽车Model Y',
            'content': '''
            特斯拉公司今日正式发布了其最新款电动汽车Model Y。这款新车型采用了最新的
            电池技术，续航里程达到500公里，比上一代产品提升了20%。
            
            Model Y配备了特斯拉最新的自动驾驶系统FSD Beta 12.0，具备更强的环境感知
            能力和决策能力。车内采用了15.4英寸触控屏，支持游戏、影音娱乐等多种功能。
            
            在价格方面，Model Y标准版售价为32万元人民币，高性能版售价为42万元。
            特斯拉表示，新车将于2024年第二季度开始交付。
            
            这是特斯拉继Model 3成功后推出的又一款重要产品，预计将进一步巩固特斯拉
            在电动汽车市场的领导地位。
            ''',
            'url': 'https://example.com/tesla-model-y',
            'published_at': '2024-01-15T14:30:00Z',
            'author': '汽车记者',
            'category': '汽车',
            'user_id': user_id
        }
        
        return await self._test_cluster_detection(sample_article, user_id)
        
    async def _test_cluster_detection(self, article, user_id):
        """执行聚类检测测试的核心逻辑"""
        print(f"\n{'='*60}")
        print(f"Article Title: {article['title']}")
        print(f"User ID: {user_id}")
        print(f"Article Category: {article.get('category', 'N/A')}")
        print(f"{'='*60}")
        
        try:
            # 首先生成文章摘要（聚类检测需要摘要）
            print("Generating article summary for cluster analysis...")
            summary = await self._create_summary(article)
            print(f"Generated Summary: {summary[:200]}...")
            
            # 获取文章的相关主题
            print("\nFinding related topics...")
            
            # 生成标题嵌入
            print("Generating title embedding...")
            title_embedding = await self._generate_title_embedding(article)
            
            # 生成摘要嵌入
            print("Generating summary embedding...")
            summary_embedding = await self._generate_summary_embedding(summary)
            
            # 查找相似主题（使用双重embedding判断）
            similar_topics = await self._find_similar_topics(
                title_embedding=title_embedding,
                summary_embedding=summary_embedding, 
                user_id=user_id, 
                similarity_threshold=0.6
            )
            
            print(f"Found {len(similar_topics)} similar topics")
            for i, topic in enumerate(similar_topics[:3]):  # 显示前3个相关主题
                similarity = topic.get('similarity', 0)
                source = topic.get('similarity_source', 'unknown')
                print(f"  Topic {i+1}: {topic.get('name', 'Unknown')} "
                      f"(similarity: {similarity:.3f}, source: {source})")
                
                # 显示详细的相似度分数
                if 'title_similarity' in topic:
                    print(f"    - Title similarity: {topic['title_similarity']:.3f}")
                if 'summary_similarity' in topic:
                    print(f"    - Summary similarity: {topic['summary_similarity']:.3f}")
            
            if similar_topics:
                # 使用第一个最相关的主题进行聚类检测
                primary_topic = similar_topics[0]
                topic_id = primary_topic['id']
                
                print(f"\nTesting cluster detection for topic ID: {topic_id}")
                
                # 获取该主题下的现有事件
                existing_events = await self._get_events_by_topic(topic_id)
                
                print(f"Found {len(existing_events)} existing events for this topic")
                for i, event in enumerate(existing_events[:3]):  # 显示前3个事件
                    print(f"  Event {i+1}: {event.get('title', 'Unknown')} "
                          f"(ID: {event.get('id')})")
                
                # 执行聚类检测
                print(f"\n{'-'*40}")
                print("Running cluster detection...")
                
                cluster_decision = await self._detect_or_create_cluster(
                    article, user_id, topic_id, summary, existing_events
                )
                
                print(f"\nCluster Decision Result:\n{'-'*40}")
                print(json.dumps(cluster_decision, indent=2, ensure_ascii=False))
                
                # 解析决策类型
                decision_type = cluster_decision.get('action', 'unknown')
                print(f"\nDecision Type: {decision_type}")
                
                if decision_type == 'assign':
                    event_id = cluster_decision.get('event_id')
                    reason = cluster_decision.get('reason', 'No reason provided')
                    print(f"Assigned to existing event ID: {event_id}")
                    print(f"Reason: {reason}")
                    
                elif decision_type == 'create':
                    title = cluster_decision.get('title', 'New Event')
                    description = cluster_decision.get('description', 'No description')
                    print(f"Creating new event: {title}")
                    print(f"Description: {description}")
                    
                elif decision_type == 'ignore':
                    reason = cluster_decision.get('reason', 'No reason provided')
                    print(f"Ignoring article")
                    print(f"Reason: {reason}")
                
                # 显示使用的prompt
                if hasattr(self, 'cluster_prompt'):
                    print(f"\nUsed Prompt:\n{'-'*40}")
                    # print(self.cluster_prompt[:300] + "..." if len(self.cluster_prompt) > 300 else self.cluster_prompt)
                    print(self.cluster_prompt)
                
                return {
                    'article': article,
                    'summary': summary,
                    'similar_topics': similar_topics,
                    'existing_events': existing_events,
                    'cluster_decision': cluster_decision,
                    'success': True
                }
            else:
                print("\nNo similar topics found - cannot test cluster detection")
                return {
                    'article': article,
                    'summary': summary,
                    'similar_topics': [],
                    'cluster_decision': None,
                    'success': False,
                    'error': 'No similar topics found'
                }
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"\nError in cluster detection: {str(e)}")
            return {
                'article': article,
                'success': False,
                'error': str(e)
            }
            
    async def _load_prompts_from_files(self):
        """从文件加载prompts"""
        prompts_dir = os.path.join(project_root, 'scripts', 'prompts')
        
        prompt_dict = {}
            
        # 加载摘要创建prompt
        summary_prompt_file = os.path.join(prompts_dir, 'summary_creation.txt')
        try:
            with open(summary_prompt_file, 'r', encoding='utf-8') as f:
                prompt_dict['summary_creation'] = f.read().strip()
        except FileNotFoundError:
            prompt_dict['summary_creation'] = "Generate a concise summary of the following article:"
            
        # 加载聚类检测prompt
        cluster_prompt_file = os.path.join(prompts_dir, 'cluster_detection.txt')
        try:
            with open(cluster_prompt_file, 'r', encoding='utf-8') as f:
                prompt_dict['cluster_detection'] = f.read().strip()
            print(f"Loaded cluster prompt from: {cluster_prompt_file}")
        except FileNotFoundError:
            print(f"Warning: Prompt file not found: {cluster_prompt_file}")
            prompt_dict['cluster_detection'] = "Analyze if this article belongs to an existing event cluster."
            
        # 设置到prompt manager
        self.prompt_manager.set_prompts(prompt_dict)
            
    async def _get_article_by_id(self, article_id):
        """从后端API获取文章"""
        try:
            response = requests.get(f"{self.backend_url}/api/internal/articles/{article_id}")
            if response.status_code == 200:
                return response.json()
            return None
        except requests.RequestException as e:
            print(f"Error fetching article: {e}")
            return None
            
    async def _create_summary(self, article):
        """创建文章摘要"""
        prompt_template = getattr(self, 'summary_prompt', 'Create a summary of: {title}\n\nContent: {content}')
        return create_summary(
            title=article['title'],
            content=article['content'],
            prompt_template=prompt_template
        )
        
    async def _generate_title_embedding(self, article):
        """生成标题嵌入"""
        title = article.get('title', '')
        if not title:
            return None
        return generate_content_embedding(title, "")
        
    async def _generate_summary_embedding(self, summary):
        """生成摘要嵌入"""
        return generate_content_embedding("Summary", summary)
        
    async def _find_similar_topics(self, title_embedding=None, summary_embedding=None, user_id=None, similarity_threshold=0.7):
        """查找相似主题，使用title和summary embedding的双重判断"""
        try:
            # 至少需要一个embedding
            if not title_embedding and not summary_embedding:
                print("Warning: No embeddings provided for topic similarity comparison")
                return []
            
            # 获取所有topics（这里简化处理，实际应该通过API获取）
            topics_response = requests.get(f"{self.backend_url}/api/internal/topics?user_id={user_id}" if user_id else f"{self.backend_url}/api/internal/topics")
            if topics_response.status_code != 200:
                print(f"Error getting topics: {topics_response.status_code}")
                return []
            
            topics = topics_response.json()
            if not topics:
                print("No topics found for comparison")
                return []
            
            # 转换embeddings为numpy数组
            title_embedding_np = None
            summary_embedding_np = None
            
            if title_embedding:
                title_embedding_np = np.array(title_embedding).reshape(1, -1)
            if summary_embedding:
                summary_embedding_np = np.array(summary_embedding).reshape(1, -1)
            
            print(f"Using dual embedding similarity comparison:")
            print(f"  Title embedding: {'Available' if title_embedding else 'Not available'}")
            print(f"  Summary embedding: {'Available' if summary_embedding else 'Not available'}")
            print(f"  Similarity threshold: {similarity_threshold}")
            
            similar_topics = []
            
            for topic in topics:
                topic_vector = topic.get('topic_vector')
                if not topic_vector:
                    continue
                
                topic_embedding = np.array(topic_vector).reshape(1, -1)
                
                # 计算两个embedding的相似度
                title_similarity = None
                summary_similarity = None
                
                if title_embedding_np is not None:
                    title_similarity = cosine_similarity(title_embedding_np, topic_embedding)[0][0]
                
                if summary_embedding_np is not None:
                    summary_similarity = cosine_similarity(summary_embedding_np, topic_embedding)[0][0]
                
                # 使用较高的相似度作为最终相似度
                if title_similarity is not None and summary_similarity is not None:
                    final_similarity = max(title_similarity, summary_similarity)
                    higher_source = "title" if title_similarity > summary_similarity else "summary"
                elif title_similarity is not None:
                    final_similarity = title_similarity
                    higher_source = "title"
                elif summary_similarity is not None:
                    final_similarity = summary_similarity
                    higher_source = "summary"
                else:
                    continue

                
                topic_name = topic.get('name', 'Unknown')
                topic_id = topic.get('id', 'N/A')
                
                print(f"{topic_name}: {final_similarity}")

                print(f"  Topic '{topic_name}' (ID: {topic_id})")
                if title_similarity is not None:
                    print(f"    Title Similarity: {title_similarity:.4f}")
                if summary_similarity is not None:
                    print(f"    Summary Similarity: {summary_similarity:.4f}")
                print(f"    Final Similarity (max, from {higher_source}): {final_similarity:.4f}")
                print(f"    Match (≥ {similarity_threshold}): {'✅ YES' if final_similarity >= similarity_threshold else '❌ NO'}")
                
                if final_similarity >= similarity_threshold:
                    topic_copy = topic.copy()
                    topic_copy['similarity'] = float(final_similarity)
                    topic_copy['similarity_source'] = higher_source
                    if title_similarity is not None:
                        topic_copy['title_similarity'] = float(title_similarity)
                    if summary_similarity is not None:
                        topic_copy['summary_similarity'] = float(summary_similarity)
                    similar_topics.append(topic_copy)
            
            # 按相似度排序
            similar_topics.sort(key=lambda x: x['similarity'], reverse=True)
            
            return similar_topics
            
        except Exception as e:
            print(f"Error finding similar topics: {e}")
            import traceback
            traceback.print_exc()
            return []
            
    async def _get_events_by_topic(self, topic_id):
        """获取主题下的事件"""
        try:
            response = requests.get(f"{self.backend_url}/api/internal/topics/{topic_id}/events")
            if response.status_code == 200:
                return response.json()
            return []
        except requests.RequestException as e:
            print(f"Error getting events: {e}")
            return []
            
    async def _detect_or_create_cluster(self, article, user_id, topic_id, summary, existing_events):
        """执行聚类检测"""
        # 构建prompt
        prompt = self._build_cluster_prompt(article, user_id, topic_id, summary, existing_events)
        
        # Define JSON schema for structured output
        cluster_schema = {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["assign", "create", "ignore"]
                },
                "event_id": {
                    "type": "integer",
                },
                "topic_id": {
                    "type": "array",
                    "items": {
                        "type": "integer"
                    }
                },
                "title": {
                    "type": "string",
                },
                "description": {
                    "type": "string",
                },
                "event_description": {
                    "type": "string",
                },
            },
            "required": ["action"],
            "oneOf": [
                {
                    "if": {
                        "properties": {"action": {"const": "create"}}
                    },
                    "then": {
                        "required": ["event_description", "description"]
                    }
                },
                {
                    "if": {
                        "properties": {"action": {"const": "assign"}}
                    },
                    "then": {
                        "required": ["event_id"]
                    }
                },
            ],
            "additionalProperties": False
        }
        
        print(prompt)
        # 调用LLM with structured output using analysis model
        response = self.llm_client.create_analysis_completion(prompt,
                                                              response_schema=cluster_schema,
                                                              max_tokens=5000)
        
        # 解析JSON响应
        try:
            return json.loads(response.strip())
        except json.JSONDecodeError:
            return {
                "action": "ignore",
                "reason": "Failed to parse LLM response"
            }
            
    def _build_cluster_prompt(self, article, user_id, topic_id, summary, existing_events):
        """构建聚类检测prompt"""
        events_info = "\n".join([
            f"- Event {i+1}: {event.get('title', 'Unknown')} (ID: {event.get('id')})"
            for i, event in enumerate(existing_events[:5])  # 最多显示5个事件
        ])
        
        return f"""{self.cluster_prompt}

Article Information:
Title: {article['title']}
Summary: {summary}
User ID: {user_id}
Topic ID: {topic_id}

Existing Events in this Topic:
{events_info or "No existing events"}

Please respond with a JSON object containing:
{{"action": "assign|create|ignore", "event_id": number_or_null, "title": "string_or_null", "description": "string_or_null", "reason": "explanation"}}"""
        
    async def cleanup(self):
        """清理资源"""
        pass


async def main():
    parser = argparse.ArgumentParser(description='Test cluster detection prompt')
    parser.add_argument('--article-id', type=int, help='Article ID to test with')
    parser.add_argument('--user-id', type=int, default=1, help='User ID for testing (default: 1)')
    parser.add_argument('--config', help='Path to config file')
    parser.add_argument('--sample', action='store_true', help='Use sample data instead of real article')
    
    args = parser.parse_args()
    
    tester = ClusterDetectionTester(config_path=args.config)
    
    try:
        await tester.setup()
        
        if args.sample:
            result = await tester.test_with_sample_data(user_id=args.user_id)
        elif args.article_id:
            result = await tester.test_with_article_id(args.article_id, user_id=args.user_id)
        else:
            print("Please specify either --article-id or --sample")
            return
            
        if result and result['success']:
            print(f"\n{'='*60}")
            print("Cluster detection test completed successfully!")
        else:
            print(f"\n{'='*60}")
            print("Cluster detection test failed!")
            
    except Exception as e:
        print(f"Test setup failed: {str(e)}")
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
