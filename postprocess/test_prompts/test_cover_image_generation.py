#!/usr/bin/env python3
"""
测试cover_image_generation prompt的脚本
使用与postprocess相同的逻辑测试封面图片描述生成功能
"""

import sys
import os
import argparse
import asyncio
from pathlib import Path

# 导入共享库
from newsfrontier_lib import get_llm_client
import requests

# 获取项目根目录
project_root = Path(__file__).parent.parent.parent


class CoverImageGenerationTester:
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
        
    async def test_with_summary_id(self, summary_id):
        """使用每日摘要ID测试封面图片生成"""
        print(f"Testing cover image generation with summary ID: {summary_id}")
        
        # 从后端获取每日摘要数据
        summary_data = await self._get_daily_summary_by_id(summary_id)
        if not summary_data:
            print(f"Error: Daily summary with ID {summary_id} not found")
            return None
            
        return await self._test_cover_image_generation(summary_data)
        
    async def test_with_sample_data(self):
        """使用示例数据测试封面图片生成"""
        print("Testing cover image generation with sample data")
        
        sample_summary = {
            'id': 999999,
            'user_id': 1,
            'date': '2024-01-15',
            'title': '今日科技要闻摘要',
            'content': '''
            # 今日科技要闻摘要 (2024年1月15日)

            ## 🤖 人工智能
            
            **GPT-5模型正式发布**
            • OpenAI发布GPT-5，性能较GPT-4提升50%
            • 支持更长上下文窗口，可处理100万token
            • 新增多模态理解和代码生成能力
            • 能耗降低30%，推理速度提升2倍
            
            ## 🚗 电动汽车
            
            **特斯拉Model Y新版本发布**
            • 续航里程提升至500公里
            • 配备FSD Beta 12.0自动驾驶系统
            • 标准版售价32万元，高性能版42万元
            • 预计第二季度开始交付
            
            ## 🛰️ 航天科技
            
            **中国空间站科学实验新进展**
            • 完成蛋白质结晶实验，获得高质量样品
            • 微重力环境下材料科学实验突破
            • 成功培养新型合金材料
            • 下月计划载人出舱活动
            
            ## 🌍 环境科技
            
            **全球气候变化会议达成协议**
            • 196国承诺2030年前减排45%
            • 发达国家提供1000亿美元绿色转型资金
            • 建立全球碳交易市场机制
            • 加强可再生能源技术合作
            
            ---
            
            **今日关键词**: 人工智能、电动汽车、航天科技、气候变化
            **总计文章数**: 12篇
            **涵盖分类**: 科技、汽车、航天、环境
            ''',
            'article_count': 12,
            'categories': ['科技', '汽车', '航天', '环境'],
            'topics': ['人工智能', '电动汽车', '航天科技', '气候变化']
        }
        
        return await self._test_cover_image_generation(sample_summary)
        
    async def _test_cover_image_generation(self, summary_data):
        """执行封面图片生成测试的核心逻辑"""
        print(f"\n{'='*60}")
        print(f"Summary Title: {summary_data.get('title', 'N/A')}")
        print(f"Date: {summary_data.get('date', 'N/A')}")
        print(f"User ID: {summary_data.get('user_id', 'N/A')}")
        print(f"Article Count: {summary_data.get('article_count', 'N/A')}")
        print(f"{'='*60}")
        
        # 显示摘要内容（部分）
        content = summary_data.get('content', '')
        print(f"\nSummary Content Preview:\n{'-'*40}")
        content_preview = content[:500] + "..." if len(content) > 500 else content
        print(content_preview)
        
        # 显示分类和主题
        if 'categories' in summary_data:
            print(f"\nCategories: {summary_data['categories']}")
        if 'topics' in summary_data:
            print(f"Topics: {summary_data['topics']}")
        
        try:
            # 生成封面图片描述
            print(f"\n{'-'*40}")
            print("Generating cover image description...")
            
            image_description = await self._generate_cover_image_description(summary_data)
            
            print(f"\nGenerated Cover Image Description:\n{'-'*40}")
            print(image_description)
            
            # 分析生成的描述
            print(f"\nDescription Analysis:\n{'-'*40}")
            word_count = len(image_description.split())
            char_count = len(image_description)
            print(f"Word count: {word_count}")
            print(f"Character count: {char_count}")
            
            # 检查是否包含关键元素
            key_elements = self._analyze_image_description(image_description)
            print(f"\nKey Elements Detected:")
            for element, detected in key_elements.items():
                status = "✓" if detected else "✗"
                print(f"  {status} {element}")
            
            # 显示使用的prompt
            if hasattr(self, 'cover_image_prompt'):
                print(f"\nUsed Prompt:\n{'-'*40}")
                print(self.cover_image_prompt[:300] + "..." if len(self.cover_image_prompt) > 300 else self.cover_image_prompt)
            
            return {
                'summary_data': summary_data,
                'image_description': image_description,
                'analysis': {
                    'word_count': word_count,
                    'char_count': char_count,
                    'key_elements': key_elements
                },
                'success': True
            }
            
        except Exception as e:
            print(f"\nError generating cover image description: {str(e)}")
            return {
                'summary_data': summary_data,
                'image_description': None,
                'success': False,
                'error': str(e)
            }
            
    async def _load_prompts_from_files(self):
        """从文件加载prompts"""
        prompts_dir = os.path.join(project_root, 'scripts', 'prompts')
        
        # 加载封面图片生成prompt
        cover_image_prompt_file = os.path.join(prompts_dir, 'cover_image_generation.txt')
        try:
            with open(cover_image_prompt_file, 'r', encoding='utf-8') as f:
                self.cover_image_prompt = f.read().strip()
            print(f"Loaded cover image prompt from: {cover_image_prompt_file}")
        except FileNotFoundError:
            print(f"Warning: Prompt file not found: {cover_image_prompt_file}")
            self.cover_image_prompt = "Generate a cover image description for the following daily summary:"
            
    async def _get_daily_summary_by_id(self, summary_id):
        """从后端API获取每日摘要"""
        try:
            response = requests.get(f"{self.backend_url}/api/internal/daily-summaries/{summary_id}")
            if response.status_code == 200:
                return response.json()
            return None
        except requests.RequestException as e:
            print(f"Error fetching daily summary: {e}")
            return None
            
    def _generate_cover_image_description(self, summary_data):
        """生成封面图片描述（使用模块化ImageGenerator）"""
        if not self.image_generator:
            raise ValueError("Image generator not initialized")
        
        # 使用模块化服务生成图片描述
        summary_content = summary_data.get('content', '')
        return self.image_generator.generate_cover_image_prompt(summary_content)
        
    def _build_cover_image_prompt(self, summary_data):
        """构建封面图片生成的prompt"""
        content = summary_data.get('content', '')
        title = summary_data.get('title', '每日新闻摘要')
        categories = summary_data.get('categories', [])
        topics = summary_data.get('topics', [])
        
        return f"""{self.cover_image_prompt}

摘要信息:
标题: {title}
日期: {summary_data.get('date', 'Unknown')}
主要分类: {', '.join(categories)}
关键主题: {', '.join(topics)}
文章数量: {summary_data.get('article_count', 'Unknown')}

摘要内容:
{content}

请生成一个详细的封面图片描述，包含:
1. 整体视觉风格和色调
2. 主要视觉元素和构图
3. 文字和图标元素
4. 专业性和现代感的体现
5. 与内容主题的关联性

描述应适合用于AI图片生成工具。"""
        
    def _analyze_image_description(self, description):
        """分析图片描述中的关键元素"""
        description_lower = description.lower()
        
        return {
            '颜色描述': any(color in description_lower for color in 
                          ['红色', '蓝色', '绿色', '黄色', '白色', '黑色', '橙色', '紫色', 
                           'red', 'blue', 'green', 'yellow', 'white', 'black', 'orange', 'purple', '色彩', '颜色']),
            '构图元素': any(element in description_lower for element in 
                          ['背景', '前景', '中心', '左侧', '右侧', '上方', '下方', '布局', '构图',
                           'background', 'foreground', 'center', 'layout', 'composition']),
            '技术元素': any(tech in description_lower for tech in 
                          ['科技', '数字', '电路', '屏幕', '电脑', '手机', '机器人', '芯片',
                           'technology', 'digital', 'screen', 'robot', 'tech', '高科技']),
            '现代感': any(modern in description_lower for modern in 
                         ['现代', '未来', '时尚', '简洁', '极简', '科幻',
                          'modern', 'future', 'minimalist', 'sleek', '现代化']),
            '专业性': any(professional in description_lower for professional in 
                         ['专业', '商务', '正式', '清晰', '精确', '企业',
                          'professional', 'business', 'formal', 'clear', '新闻'])
        }
            
    async def cleanup(self):
        """清理资源"""
        pass


async def main():
    parser = argparse.ArgumentParser(description='Test cover image generation prompt')
    parser.add_argument('--summary-id', type=int, help='Daily summary ID to test with')
    parser.add_argument('--config', help='Path to config file')
    parser.add_argument('--sample', action='store_true', help='Use sample data instead of real summary')
    
    args = parser.parse_args()
    
    tester = CoverImageGenerationTester(config_path=args.config)
    
    try:
        await tester.setup()
        
        if args.sample:
            result = await tester.test_with_sample_data()
        elif args.summary_id:
            result = await tester.test_with_summary_id(args.summary_id)
        else:
            print("Please specify either --summary-id or --sample")
            return
            
        if result and result['success']:
            print(f"\n{'='*60}")
            print("Cover image generation test completed successfully!")
        else:
            print(f"\n{'='*60}")
            print("Cover image generation test failed!")
            
    except Exception as e:
        print(f"Test setup failed: {str(e)}")
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())