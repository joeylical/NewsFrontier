#!/usr/bin/env python3
"""
测试daily_summary_system prompt的脚本
使用与postprocess相同的逻辑测试每日摘要生成功能
"""

import sys
import os
import argparse
import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path

# 导入共享库
from newsfrontier_lib import get_llm_client
import requests

# 获取项目根目录
project_root = Path(__file__).parent.parent.parent


class DailySummaryTester:
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
        
    async def test_with_user_id(self, user_id, date=None):
        """使用用户ID测试每日摘要生成"""
        target_date = date or (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        print(f"Testing daily summary for user {user_id} on {target_date}")
        
        return await self._test_daily_summary(user_id, target_date)
        
    async def test_with_sample_data(self, user_id=1):
        """使用示例数据测试每日摘要生成"""
        print("Testing daily summary with sample data")
        
        # 创建示例用户上下文数据
        sample_context = {
            'user_id': user_id,
            'username': 'User 1',
            'custom_prompt': '',
            'date': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
            'topics': [],
            'relevant_articles': [
                {
                    'id': 1001,
                    'title': '人工智能领域重大突破：GPT-5模型发布',
                    'summary': '''
                    • OpenAI正式发布GPT-5模型，性能较GPT-4提升50%
                    • 新模型在多模态理解、逻辑推理、代码生成方面表现卓越
                    • 支持更长的上下文窗口，可处理100万token的输入
                    • 能耗降低30%，推理速度提升2倍
                    • 计划于2024年第二季度向开发者开放API接口
                    ''',
                    'url': 'https://example.com/gpt5-release',
                    'category': '科技',
                    'published_at': '2024-01-15T09:00:00Z',
                    'topics': ['人工智能', '自然语言处理', 'OpenAI']
                },
                {
                    'id': 1002,
                    'title': '全球气候变化会议达成重要协议',
                    'summary': '''
                    • 196个国家在联合国气候变化大会上达成新协议
                    • 承诺2030年前将全球碳排放量减少45%
                    • 发达国家将提供1000亿美元资助发展中国家绿色转型
                    • 建立全球碳交易市场机制
                    • 加强可再生能源技术合作与共享
                    ''',
                    'url': 'https://example.com/climate-agreement',
                    'category': '环境',
                    'published_at': '2024-01-15T11:30:00Z',
                    'topics': ['气候变化', '环境保护', '国际合作']
                },
                {
                    'id': 1003,
                    'title': '中国空间站科学实验取得新进展',
                    'summary': '''
                    • 天宫空间站完成蛋白质结晶实验，获得高质量晶体样品
                    • 微重力环境下的材料科学实验产生突破性成果
                    • 成功培养出在地面难以获得的新型合金材料
                    • 空间生命科学实验为医学研究提供新数据
                    • 计划下个月进行载人出舱活动维护设备
                    ''',
                    'url': 'https://example.com/space-station-research',
                    'category': '科学',
                    'published_at': '2024-01-15T16:45:00Z',
                    'topics': ['航天科技', '科学研究', '中国空间站']
                }
            ],
            'new_events': [],
            'recent_summaries': [],
            'user_preferences': {
                'categories': ['科技', '科学', '环境'],
                'keywords': ['人工智能', '气候变化', '航天'],
                'language': 'zh-CN'
            }
        }
        
        return await self._test_daily_summary_with_context(sample_context)
        
    async def _test_daily_summary(self, user_id, date):
        """执行每日摘要测试的核心逻辑"""
        print(f"\n{'='*60}")
        print(f"User ID: {user_id}")
        print(f"Target Date: {date}")
        print(f"{'='*60}")
        
        try:
            # 获取用户每日上下文数据
            print("Fetching user daily context...")
            context = await self._get_user_daily_context(user_id, date)
            
            if not context or not context.get('relevant_articles'):
                print(f"No relevant articles found for user {user_id} on {date}")
                return {
                    'user_id': user_id,
                    'date': date,
                    'success': False,
                    'error': 'No relevant articles found'
                }
            
            return await self._test_daily_summary_with_context(context)
            
        except Exception as e:
            print(f"\nError fetching user context: {str(e)}")
            return {
                'user_id': user_id,
                'date': date,
                'success': False,
                'error': str(e)
            }
            
    async def _test_daily_summary_with_context(self, context):
        """使用上下文数据执行每日摘要测试"""
        print(f"\nUser Context:\n{'-'*40}")
        print(f"Articles count: {len(context['relevant_articles'])}")
        print(f"Date: {context.get('date', 'Unknown')}")
        
        # 显示文章列表
        print(f"\nArticles to summarize:")
        for i, article in enumerate(context['relevant_articles'][:5]):  # 显示前5篇文章
            # Handle both API structure (with rss_item) and sample data structure
            article_info = article.get('rss_item', article)
            title = article_info.get('title', 'Untitled')
            category = article_info.get('category', 'N/A')
            print(f"  {i+1}. {title} ({category})")
        
        if len(context['relevant_articles']) > 5:
            print(f"  ... and {len(context['relevant_articles']) - 5} more articles")
        
        # 显示用户偏好（如果有）
        if 'user_preferences' in context:
            prefs = context['user_preferences']
            print(f"\nUser Preferences:")
            print(f"  Categories: {prefs.get('categories', [])}")
            print(f"  Keywords: {prefs.get('keywords', [])}")
            print(f"  Language: {prefs.get('language', 'default')}")
        
        try:
            # 生成每日摘要
            print(f"\n{'-'*40}")
            print("Generating daily summary...")
            
            summary_content = await self._create_daily_summary_content(context)
            
            print(f"\nGenerated Daily Summary:\n{'-'*40}")
            print(summary_content)
            
            # 显示摘要统计信息
            word_count = len(summary_content.split())
            char_count = len(summary_content)
            print(f"\nSummary Statistics:\n{'-'*40}")
            print(f"Word count: {word_count}")
            print(f"Character count: {char_count}")
            
            # 显示使用的prompt
            if hasattr(self, 'daily_summary_prompt'):
                print(f"\nUsed Prompt:\n{'-'*40}")
                print(self.daily_summary_prompt[:300] + "..." if len(self.daily_summary_prompt) > 300 else self.daily_summary_prompt)
            
            return {
                'user_id': context.get('user_id'),
                'date': context.get('date'),
                'context': context,
                'summary_content': summary_content,
                'statistics': {
                    'word_count': word_count,
                    'char_count': char_count,
                    'article_count': len(context['relevant_articles'])
                },
                'success': True
            }
            
        except Exception as e:
            print(f"\nError generating daily summary: {str(e)}")
            return {
                'user_id': context.get('user_id'),
                'date': context.get('date'),
                'context': context,
                'summary_content': None,
                'success': False,
                'error': str(e)
            }
            
    async def _load_prompts_from_files(self):
        """从文件加载prompts"""
        prompts_dir = os.path.join(project_root, 'scripts', 'prompts')
        
        # 加载每日摘要prompt
        daily_summary_prompt_file = os.path.join(prompts_dir, 'daily_summary_system.txt')
        try:
            with open(daily_summary_prompt_file, 'r', encoding='utf-8') as f:
                self.daily_summary_prompt = f.read().strip()
            print(f"Loaded daily summary prompt from: {daily_summary_prompt_file}")
        except FileNotFoundError:
            print(f"Warning: Prompt file not found: {daily_summary_prompt_file}")
            self.daily_summary_prompt = "Create a daily summary of the following articles:"
            
    async def _get_user_daily_context(self, user_id, date):
        """获取用户每日上下文数据（使用与main.py相同的方式）"""
        try:
            # Get user's subscriptions and custom prompt
            user_response = requests.get(f"{self.backend_url}/api/internal/user/{user_id}")
            if user_response.status_code != 200:
                print(f"Error getting user {user_id}: {user_response.status_code}")
                return None
            user_data = user_response.json()
            
            # Get user's topics
            topics_response = requests.get(f"{self.backend_url}/api/internal/topics?user_id={user_id}")
            if topics_response.status_code != 200:
                print(f"Error getting topics for user {user_id}: {topics_response.status_code}")
                return None
            user_topics = topics_response.json()  # Returns list directly
            
            if not user_topics:
                print(f"User {user_id} has no topics defined")
                return None
            
            # Get today's relevant articles (published today, related to user's topics)
            relevant_articles = []
            for topic in user_topics:
                try:
                    topic_articles_response = requests.get(
                        f"{self.backend_url}/api/internal/article-topics?topic_id={topic['id']}&date={date}"
                    )
                    if topic_articles_response.status_code == 200:
                        topic_articles = topic_articles_response.json()  # Returns list directly
                        print(f"Debug: Got {len(topic_articles)} articles for topic {topic.get('id')}")
                        relevant_articles.extend(topic_articles)
                    else:
                        print(f"Debug: Failed to get articles for topic {topic.get('id')}: {topic_articles_response.status_code}")
                except Exception as e:
                    print(f"Debug: Error processing topic {topic.get('id')}: {e}")
            
            # Get new events created today related to user's topics
            new_events = []
            for topic in user_topics:
                events_response = requests.get(
                    f"{self.backend_url}/api/internal/events?topic_id={topic['id']}&created_date={date}"
                )
                if events_response.status_code == 200:
                    topic_events = events_response.json()  # Returns list directly
                    # Add topic information to each event
                    for event in topic_events:
                        event['topic_name'] = topic.get('name', 'Unknown Topic')
                        event['topic_id'] = topic['id']
                    new_events.extend(topic_events)
            
            # Get recent daily summaries (last 5)
            recent_summaries_response = requests.get(
                f"{self.backend_url}/api/internal/user-summaries/{user_id}?limit=5"
            )
            recent_summaries = []
            if recent_summaries_response.status_code == 200:
                recent_summaries = recent_summaries_response.json().get('data', [])  # Wrapped in data
            
            return {
                'user_id': user_id,
                'username': user_data.get('username', 'User'),
                'custom_prompt': user_data.get('daily_summary_prompt', ''),
                'topics': user_topics,
                'relevant_articles': relevant_articles,
                'new_events': new_events,
                'recent_summaries': recent_summaries
            }
            
        except Exception as e:
            print(f"Error getting user daily context: {e}")
            import traceback
            print("Full traceback:")
            traceback.print_exc()
            return None
            
    async def _create_daily_summary_content(self, context):
        """创建每日摘要内容（使用与main.py相同的方式）"""
        # 格式化文章、事件和摘要文本
        articles_text = self._format_articles_for_summary(context.get('relevant_articles', []))
        events_text = self._format_events_for_summary(context.get('new_events', []))
        recent_summaries_text = self._format_recent_summaries(context.get('recent_summaries', []))
        
        # 使用system prompt模板并填充字段
        formatted_system_prompt = self.daily_summary_prompt.format(
            articles=articles_text,
            summaries=recent_summaries_text,
            events=events_text
        )

        print(formatted_system_prompt)
        
        # 调用LLM using analysis model for daily summary
        response = self.llm_client.create_analysis_completion(formatted_system_prompt, max_tokens=2000, temperature=0.7)
        
        return response.strip()
        
    def _format_articles_for_summary(self, articles):
        """Format articles for summary context."""
        if not articles:
            return "No relevant articles found for today."
        
        formatted_articles = []
        for article in articles[:10]:  # Limit to 10 most relevant articles
            # Handle both API structure (with rss_item) and sample data structure
            article_info = article.get('rss_item', article)
            title = article_info.get('title', 'Untitled')
            article_id = article_info.get('id', article.get('id', ''))
            summary = article_info.get('summary', '')
            
            # Use local dashboard link format instead of external URL
            article_link = f"/dashboard/article/{article_id}" if article_id else "#"
            formatted_articles.append(f"- **[{title}]({article_link})**")
            if summary:
                formatted_articles.append(f"  Summary: {summary}")
        
        return "\n".join(formatted_articles)
    
    def _format_events_for_summary(self, events):
        """Format new events for summary context."""
        if not events:
            return "No new events detected today."
        
        formatted_events = []
        for event in events:
            title = event.get('title', 'Untitled Event')
            event_id = event.get('id', '')
            description = event.get('description', '')
            topic_name = event.get('topic_name', 'Unknown Topic')
            topic_id = event.get('topic_id', '')
            
            # Use local dashboard link format for events (clusters) and topics
            event_link = f"/dashboard/clusters/{event_id}" if event_id else "#"
            topic_link = f"/dashboard/topics/{topic_id}" if topic_id else "#"
            
            formatted_events.append(f"- **Topic: [{topic_name}]({topic_link})**")
            formatted_events.append(f"  - **Event: [{title}]({event_link})**")
            if description:
                formatted_events.append(f"    {description}")
        
        return "\n".join(formatted_events)
    
    def _format_recent_summaries(self, summaries):
        """Format recent summaries for context."""
        if not summaries:
            return "No recent summaries available."
        
        formatted_summaries = []
        for summary in summaries:
            date = summary.get('date', 'Unknown date')
            content = summary.get('summary', '')[:200] + "..." if len(summary.get('summary', '')) > 200 else summary.get('summary', '')
            formatted_summaries.append(f"- {date}: {content}")
        
        return "\n".join(formatted_summaries)
        
    def _build_daily_summary_prompt(self, context):
        """构建每日摘要prompt"""
        articles_info = "\n\n".join([
            f"文章 {i+1}:\n标题: {article.get('title', 'Untitled')}\n摘要: {article.get('summary', 'No summary')}\n分类: {article.get('category', 'Unknown')}"
            for i, article in enumerate(context['relevant_articles'])
        ])
        
        user_prefs = context.get('user_preferences', {})
        categories = ', '.join(user_prefs.get('categories', []))
        keywords = ', '.join(user_prefs.get('keywords', []))
        
        return f"""{self.daily_summary_prompt}

用户信息:
- 用户ID: {context['user_id']}
- 日期: {context['date']}
- 偏好分类: {categories or '无特定偏好'}
- 关键词: {keywords or '无特定关键词'}

今日文章 ({len(context['relevant_articles'])}篇):
{articles_info}

请生成一个结构化的每日摘要，包含:
1. 日期和总览
2. 按分类组织的要点
3. 重要新闻亮点
4. 总结和关键词"""
        
    async def cleanup(self):
        """清理资源"""
        pass


async def main():
    parser = argparse.ArgumentParser(description='Test daily summary prompt')
    parser.add_argument('--user-id', type=int, default=1, help='User ID to test with (default: 1)')
    parser.add_argument('--date', help='Date to test (YYYY-MM-DD format, default: yesterday)')
    parser.add_argument('--config', help='Path to config file')
    parser.add_argument('--sample', action='store_true', help='Use sample data instead of real user data')
    
    args = parser.parse_args()
    
    tester = DailySummaryTester(config_path=args.config)
    
    try:
        await tester.setup()
        
        if args.sample:
            result = await tester.test_with_sample_data(user_id=args.user_id)
        else:
            result = await tester.test_with_user_id(args.user_id, date=args.date)
            
        if result and result['success']:
            print(f"\n{'='*60}")
            print("Daily summary test completed successfully!")
        else:
            print(f"\n{'='*60}")
            print("Daily summary test failed!")
            
    except Exception as e:
        print(f"Test setup failed: {str(e)}")
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
