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
from newsfrontier_lib import get_llm_client
import requests
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# 添加父目录到系统路径以导入模块化服务
sys.path.insert(0, str(Path(__file__).parent.parent))
from summary_generator import SummaryGenerator, PromptManager
from embedding_generator import EmbeddingGenerator, SimilarityCalculator
from clustering_service import ClusteringService, BackendClient

# 获取项目根目录
project_root = Path(__file__).parent.parent.parent


class ClusterDetectionTester:
    def __init__(self, config_path=None):
        """初始化测试器"""
        self.config_path = config_path or os.path.join(project_root, 'scripts', 'config.json')
        self.llm_client = None
        self.backend_url = "http://localhost:8000"
        self.prompt_manager = PromptManager()
        self.summary_generator = None
        self.embedding_generator = None
        self.similarity_calculator = None
        self.clustering_service = None
        
    async def setup(self):
        """设置AI服务"""
        self.llm_client = get_llm_client()
        # 加载prompts从文件而不是数据库
        await self._load_prompts_from_files()
        # 初始化模块化服务
        self.summary_generator = SummaryGenerator(self.prompt_manager)
        self.embedding_generator = EmbeddingGenerator()
        self.similarity_calculator = SimilarityCalculator()
        backend_client = BackendClient(self.backend_url)
        self.clustering_service = ClusteringService(
            self.prompt_manager,
            self.similarity_calculator,
            backend_client,
            cluster_threshold=0.7
        )
        
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
            summary = self._create_summary(article)
            print(f"Generated Summary: {summary[:200]}...")
            
            # 获取文章的相关主题
            print("\nFinding related topics...")
            
            # 生成标题嵌入
            print("Generating title embedding...")
            title_embedding = self._generate_title_embedding(article)
            
            # 生成摘要嵌入
            print("Generating summary embedding...")
            summary_embedding = self._generate_summary_embedding(summary)
            
            # 查找相似主题（使用双重embedding判断）
            similar_topics = self._find_similar_topics(
                title_embedding=title_embedding,
                summary_embedding=summary_embedding, 
                user_id=user_id, 
                similarity_threshold=0.6
            )
            
            print(f"Found {len(similar_topics)} similar topics")
            for i, topic in enumerate(similar_topics[:3]):  # 显示前3个相关主题
                similarity = topic.get('similarity_score', 0)
                print(f"  Topic {i+1}: {topic.get('name', 'Unknown')} "
                      f"(similarity: {similarity:.3f})")
            
            if similar_topics:
                # 使用第一个最相关的主题进行聚类检测
                primary_topic = similar_topics[0]
                topic_id = primary_topic['id']
                
                print(f"\nTesting cluster detection for topic ID: {topic_id}")
                
                # 获取该主题下的现有事件
                existing_events = self._get_events_by_topic(topic_id)
                
                print(f"Found {len(existing_events)} existing events for this topic")
                for i, event in enumerate(existing_events[:3]):  # 显示前3个事件
                    print(f"  Event {i+1}: {event.get('title', 'Unknown')} "
                          f"(ID: {event.get('id')})")
                
                # 执行聚类检测
                print(f"\n{'-'*40}")
                print("Running cluster detection...")
                
                # 使用模块化的clustering service
                cluster_result = self.clustering_service.detect_or_create_cluster(
                    user_id=user_id,
                    topic_id=topic_id,
                    topic_name=primary_topic.get('name', 'Unknown Topic'),
                    article_title=article['title'],
                    article_summary=summary,
                    title_embedding=title_embedding,
                    summary_embedding=summary_embedding
                )
                
                # 转换为测试输出格式
                if cluster_result:
                    cluster_decision = {
                        'action': 'assign' if cluster_result.get('id') else 'create',
                        'event_id': cluster_result.get('id'),
                        'title': cluster_result.get('title'),
                        'description': cluster_result.get('description'),
                        'reason': f"Clustering service result: {cluster_result}"
                    }
                else:
                    cluster_decision = {
                        'action': 'ignore',
                        'reason': 'No cluster decision made by clustering service'
                    }
                
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
                used_prompt = self.prompt_manager.get_prompt('cluster_detection')
                if used_prompt:
                    print(f"\nUsed Prompt:\n{'-'*40}")
                    print(used_prompt[:300] + "..." if len(used_prompt) > 300 else used_prompt)
                
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
            
    def _create_summary(self, article):
        """创建文章摘要"""
        # 使用新的模块化SummaryGenerator
        if not self.summary_generator:
            raise ValueError("Summary generator not initialized")
            
        return self.summary_generator.create_article_summary(article)
        
    def _generate_title_embedding(self, article):
        """生成标题嵌入"""
        if not self.embedding_generator:
            raise ValueError("Embedding generator not initialized")
            
        return self.embedding_generator.generate_title_embedding(article)
        
    def _generate_summary_embedding(self, summary):
        """生成摘要嵌入"""
        if not self.embedding_generator:
            raise ValueError("Embedding generator not initialized")
            
        return self.embedding_generator.generate_summary_embedding(summary)
        
    def _find_similar_topics(self, title_embedding=None, summary_embedding=None, user_id=None, similarity_threshold=0.7):
        """查找相似主题，使用title和summary embedding的双重判断"""
        try:
            # 获取所有topics
            topics_response = requests.get(f"{self.backend_url}/api/internal/topics?user_id={user_id}" if user_id else f"{self.backend_url}/api/internal/topics")
            if topics_response.status_code != 200:
                print(f"Error getting topics: {topics_response.status_code}")
                return []
            
            topics = topics_response.json()
            if not topics:
                print("No topics found for comparison")
                return []
            
            print(f"Using modular similarity calculator for topic matching")
            print(f"  Title embedding: {'Available' if title_embedding else 'Not available'}")
            print(f"  Summary embedding: {'Available' if summary_embedding else 'Not available'}")
            print(f"  Similarity threshold: {similarity_threshold}")
            
            # 使用模块化的SimilarityCalculator
            similar_topics = self.similarity_calculator.find_similar_topics(
                article_title_embedding=title_embedding,
                article_summary_embedding=summary_embedding,
                topics=topics,
                threshold=similarity_threshold
            )
            
            # 显示详细信息（保留原来的显示逻辑）
            for topic in similar_topics:
                topic_name = topic.get('name', 'Unknown')
                topic_id = topic.get('id', 'N/A')
                final_similarity = topic.get('similarity_score', 0)
                
                print(f"  Topic '{topic_name}' (ID: {topic_id})")
                print(f"    Final Similarity: {final_similarity:.4f}")
                print(f"    Match (≥ {similarity_threshold}): ✅ YES")
            
            return similar_topics
            
        except Exception as e:
            print(f"Error finding similar topics: {e}")
            import traceback
            traceback.print_exc()
            return []
            
    def _get_events_by_topic(self, topic_id):
        """获取主题下的事件"""
        try:
            response = requests.get(f"{self.backend_url}/api/internal/topics/{topic_id}/events")
            if response.status_code == 200:
                return response.json()
            return []
        except requests.RequestException as e:
            print(f"Error getting events: {e}")
            return []
        
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