#!/usr/bin/env python3
"""
测试summary_creation prompt的脚本
使用与postprocess相同的逻辑测试摘要生成功能
"""

import sys
import os
import argparse
import asyncio
from pathlib import Path

# 导入共享库
from newsfrontier_lib import get_llm_client
import requests

# 添加父目录到系统路径以导入模块化服务
sys.path.insert(0, str(Path(__file__).parent.parent))
from summary_generator import SummaryGenerator, PromptManager

# 获取项目根目录
project_root = Path(__file__).parent.parent.parent


class SummaryCreationTester:
    def __init__(self, config_path=None):
        """初始化测试器"""
        self.config_path = config_path or os.path.join(project_root, 'scripts', 'config.json')
        self.llm_client = None
        self.backend_url = "http://localhost:8000"
        self.prompt_manager = PromptManager()
        self.summary_generator = None
        
    async def setup(self):
        """设置AI服务"""
        self.llm_client = get_llm_client()
        # 加载prompts从文件而不是数据库
        await self._load_prompts_from_files()
        # 初始化summary generator
        self.summary_generator = SummaryGenerator(self.prompt_manager)
        
    async def test_with_article_id(self, article_id):
        """使用article ID测试摘要生成"""
        print(f"Testing summary creation with article ID: {article_id}")
        
        # 从后端获取文章数据
        article = await self._get_article_by_id(article_id)
        if not article:
            print(f"Error: Article with ID {article_id} not found")
            return None
            
        return await self._test_summary_creation(article)
        
    async def test_with_sample_data(self):
        """使用示例数据测试摘要生成"""
        print("Testing summary creation with sample data")
        
        sample_article = {
            'id': 999999,
            'title': '人工智能技术在新闻媒体中的应用前景',
            'content': '''
            人工智能技术正在深刻改变新闻媒体行业的运作方式。从自动化新闻写作到个性化内容推荐，
            AI技术的应用范围越来越广泛。
            
            自动化新闻生成是AI在新闻领域最直接的应用之一。通过自然语言处理技术，AI可以快速
            处理大量数据并生成新闻报道，特别是在体育赛事、财经数据等标准化程度较高的领域。
            
            内容个性化推荐是另一个重要应用方向。AI算法可以分析用户的阅读习惯和兴趣偏好，
            为每个用户推荐最相关的新闻内容，提高用户体验和媒体平台的用户粘性。
            
            此外，AI还可以帮助新闻编辑室进行事实核查、内容审核、情感分析等工作，
            提高新闻生产的效率和质量。
            
            然而，AI技术的应用也带来了一些挑战，包括算法偏见、信息茧房、深度伪造等问题，
            需要媒体行业和技术开发者共同努力解决。
            ''',
            'url': 'https://example.com/ai-news-media',
            'published_at': '2024-01-15T10:30:00Z',
            'author': 'AI研究员',
            'category': '科技'
        }
        
        return await self._test_summary_creation(sample_article)
        
    async def _test_summary_creation(self, article):
        """执行摘要创建测试的核心逻辑"""
        print(f"\n{'='*60}")
        print(f"Article Title: {article['title']}")
        print(f"Article URL: {article.get('url', 'N/A')}")
        print(f"Article Author: {article.get('author', 'N/A')}")
        print(f"Article Category: {article.get('category', 'N/A')}")
        print(f"{'='*60}")
        
        # 显示文章内容
        print(f"\nOriginal Content:\n{'-'*40}")
        content = article['content'][:500] + "..." if len(article['content']) > 500 else article['content']
        print(content)
        
        try:
            # 使用与postprocess相同的逻辑创建摘要
            print(f"\n{'-'*40}")
            print("Generating summary...")
            
            summary = self._create_summary(article)
            
            print(f"\nGenerated Summary:\n{'-'*40}")
            print(summary)
            
            # 显示摘要统计信息
            word_count = len(summary.split())
            char_count = len(summary)
            print(f"\nSummary Statistics:\n{'-'*40}")
            print(f"Word count: {word_count}")
            print(f"Character count: {char_count}")
            
            # 显示调用的prompt
            used_prompt = self.prompt_manager.get_prompt('summary_creation')
            if used_prompt:
                print(f"\nUsed Prompt:\n{'-'*40}")
                print(used_prompt[:300] + "..." if len(used_prompt) > 300 else used_prompt)
            
            return {
                'article': article,
                'summary': summary,
                'statistics': {
                    'word_count': word_count,
                    'char_count': char_count
                },
                'success': True
            }
            
        except Exception as e:
            print(f"\nError generating summary: {str(e)}")
            return {
                'article': article,
                'summary': None,
                'success': False,
                'error': str(e)
            }
            
    async def _load_prompts_from_files(self):
        """从文件加载prompts"""
        prompts_dir = os.path.join(project_root, 'scripts', 'prompts')
        summary_prompt_file = os.path.join(prompts_dir, 'summary_creation.txt')
        
        try:
            with open(summary_prompt_file, 'r', encoding='utf-8') as f:
                summary_prompt = f.read().strip()
            print(f"Loaded summary prompt from: {summary_prompt_file}")
            # 设置到prompt manager
            self.prompt_manager.set_prompts({'summary_creation': summary_prompt})
        except FileNotFoundError:
            print(f"Warning: Prompt file not found: {summary_prompt_file}")
            # 使用默认prompt进行测试
            default_prompt = "Generate a concise summary of the following article:"
            self.prompt_manager.set_prompts({'summary_creation': default_prompt})
            
    async def _get_article_by_id(self, article_id):
        """从后端API获取文章"""
        try:
            response = requests.get(f"{self.backend_url}/api/internal/articles/{article_id}")
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except requests.RequestException as e:
            print(f"Error fetching article: {e}")
            return None
            
    async def _create_summary(self, article):
        """创建文章摘要"""
        # 使用新的模块化SummaryGenerator
        if not self.summary_generator:
            raise ValueError("Summary generator not initialized")
            
        return self.summary_generator.create_article_summary(article)
        
    async def cleanup(self):
        """清理资源"""
        pass


async def main():
    parser = argparse.ArgumentParser(description='Test summary creation prompt')
    parser.add_argument('--article-id', type=int, help='Article ID to test with')
    parser.add_argument('--config', help='Path to config file')
    parser.add_argument('--sample', action='store_true', help='Use sample data instead of real article')
    
    args = parser.parse_args()
    
    tester = SummaryCreationTester(config_path=args.config)
    
    try:
        await tester.setup()
        
        if args.sample:
            result = await tester.test_with_sample_data()
        elif args.article_id:
            result = await tester.test_with_article_id(args.article_id)
        else:
            print("Please specify either --article-id or --sample")
            return
            
        if result and result['success']:
            print(f"\n{'='*60}")
            print("Summary creation test completed successfully!")
        else:
            print(f"\n{'='*60}")
            print("Summary creation test failed!")
            
    except Exception as e:
        print(f"Test setup failed: {str(e)}")
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())