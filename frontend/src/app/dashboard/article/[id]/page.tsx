'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/lib/auth-context';
import { apiClient } from '@/lib/api-client';
import { Article, ArticleDerivative, Topic, Cluster } from '@/lib/types';
import LoadingSpinner from '@/components/LoadingSpinner';
import { ArticleContent, SummaryContent } from '@/components/SafeHtmlContent';
import { formatDate } from '@/lib/utils';
import { containsHtml, htmlToText } from '@/lib/html-utils';
import { ChevronLeft, User, Clock, CheckCircle, TrendingUp, ExternalLink, Share2 } from 'lucide-react';

interface ArticleDetail {
  article: Article;
  derivative?: ArticleDerivative;
  related_articles?: Article[];
  topics?: Topic[];
  clusters?: Cluster[];
}

export default function ArticleDetailPage() {
  const { user } = useAuth();
  const params = useParams();
  const router = useRouter();
  const articleId = parseInt(params.id as string);
  
  const [articleDetail, setArticleDetail] = useState<ArticleDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'content' | 'summary' | 'related'>('content');

  useEffect(() => {
    // Redirect admin users to system settings
    if (user?.is_admin) {
      router.replace('/dashboard/settings');
      return;
    }

    if (isNaN(articleId)) {
      setError('Invalid article ID');
      setIsLoading(false);
      return;
    }
    
    fetchArticleDetail();
  }, [articleId, user, router]);

  const highlightParagraph = (elementId: string, retryCount = 0) => {
    // 移除之前的高亮
    document.querySelectorAll('.highlighted-paragraph').forEach(el => {
      el.classList.remove('highlighted-paragraph');
    });

    // 找到目标元素
    const targetElement = document.getElementById(elementId);
    if (targetElement) {
      // 找到对应的段落
      const paragraph = targetElement.nextElementSibling as HTMLElement;
      if (paragraph && paragraph.tagName === 'P') {
        paragraph.classList.add('highlighted-paragraph');
        paragraph.scrollIntoView({ behavior: 'smooth', block: 'center' });
        return true;
      }
    }
    
    // 如果没有找到元素且重试次数少于3次，则延迟重试
    if (retryCount < 3) {
      setTimeout(() => {
        highlightParagraph(elementId, retryCount + 1);
      }, 300);
    }
    
    return false;
  };

  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.slice(1); // 移除#号
      if (hash.startsWith('P-')) {
        // 使用setTimeout确保DOM已经渲染完成
        setTimeout(() => {
          highlightParagraph(hash);
        }, 100);
      }
    };

    // 监听hash变化
    window.addEventListener('hashchange', handleHashChange);
    
    // 页面加载时检查是否有hash
    if (window.location.hash) {
      handleHashChange();
    }

    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  // 当文章内容加载完成后，再次检查锚点
  useEffect(() => {
    if (articleDetail?.article?.content && window.location.hash) {
      const hash = window.location.hash.slice(1);
      if (hash.startsWith('P-')) {
        // 使用MutationObserver监听DOM变化，确保文章内容完全渲染后再高亮
        const observer = new MutationObserver((mutations) => {
          for (const mutation of mutations) {
            if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
              // 检查是否找到了目标元素
              const targetElement = document.getElementById(hash);
              if (targetElement) {
                highlightParagraph(hash);
                observer.disconnect();
                return;
              }
            }
          }
        });

        // 开始观察文章内容区域的DOM变化
        const articleContainer = document.querySelector('.article-content');
        if (articleContainer) {
          observer.observe(articleContainer, {
            childList: true,
            subtree: true
          });
          
          // 设置超时，避免无限等待
          setTimeout(() => {
            observer.disconnect();
            // 最后尝试一次高亮
            highlightParagraph(hash);
          }, 2000);
        } else {
          // 如果没有找到容器，使用延迟方式
          setTimeout(() => {
            highlightParagraph(hash);
          }, 200);
        }
      }
    }
  }, [articleDetail?.article?.content]);

  const fetchArticleDetail = async () => {
    try {
      // The backend returns just an Article object, not an ArticleDetail
      const articleData = await apiClient.get<Article>(`/api/article/${articleId}`);
      
      // Wrap the article data in the expected structure
      setArticleDetail({
        article: articleData,
        derivative: articleData.derivative, // Now included in article data
        related_articles: undefined, // Not provided by backend yet
        topics: undefined, // Not provided by backend yet
        clusters: undefined // Not provided by backend yet
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load article details');
    } finally {
      setIsLoading(false);
    }
  };

  const calculateReadingTime = (content: string): number => {
    const wordsPerMinute = 200;
    // 如果内容包含HTML，先转换为纯文本再计算词数
    const textContent = containsHtml(content) ? htmlToText(content) : content;
    const wordCount = textContent.trim().split(/\s+/).length;
    return Math.ceil(wordCount / wordsPerMinute);
  };

  if (isLoading) {
    return <LoadingSpinner size="lg" className="mt-20" />;
  }

  if (error || !articleDetail || !articleDetail.article) {
    return (
      <div className="max-w-4xl mx-auto mt-8 p-4 border border-red-300 rounded-lg text-red-700">
        <h3 className="font-semibold">Error loading article</h3>
        <p className="text-sm mt-1">{error || 'Article not found'}</p>
        <div className="mt-4 flex gap-3">
          <button 
            onClick={() => router.back()}
            className="text-sm underline"
          >
            Go back
          </button>
          {error && (
            <button 
              onClick={() => {
                setError(null);
                fetchArticleDetail();
              }}
              className="text-sm underline"
            >
              Try again
            </button>
          )}
        </div>
      </div>
    );
  }

  const { article, related_articles, topics } = articleDetail;
  const content = article?.content || '';
  const summary = article?.derivative?.summary;
  const readingTime = content ? calculateReadingTime(content) : 0;

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="border-b border-gray-200 pb-6 mb-8">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.back()}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              title="Go back"
            >
              <ChevronLeft className="w-5 h-5 text-gray-600" />
            </button>
            <div>
              <h1 className="text-3xl font-semibold text-gray-900 mb-3 leading-tight">
                {article.title}
              </h1>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-6 text-sm text-gray-600">
                  {article.author && (
                    <span className="flex items-center gap-1">
                      <User className="w-4 h-4" />
                      {article.author}
                    </span>
                  )}
                  {article.published_at && (
                    <span className="flex items-center gap-1">
                      <Clock className="w-4 h-4" />
                      {formatDate(article.published_at)}
                    </span>
                  )}
                  {content && (
                    <span className="flex items-center gap-1">
                      <CheckCircle className="w-4 h-4" />
                      {containsHtml(content) 
                        ? htmlToText(content).trim().split(/\s+/).length 
                        : content.trim().split(/\s+/).length
                      } words
                    </span>
                  )}
                  {readingTime > 0 && (
                    <span className="flex items-center gap-1">
                      <TrendingUp className="w-4 h-4" />
                      {readingTime} min read
                    </span>
                  )}
                </div>
                
                {/* Action icons */}
                <div className="flex items-center gap-3 text-gray-600">
                  {article.url && (
                    <a
                      href={article.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="hover:text-gray-900 transition-colors"
                      title="Open Original"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  )}
                  <button
                    onClick={() => navigator.share?.({ title: article.title, url: window.location.href }) || 
                      navigator.clipboard?.writeText(window.location.href)}
                    className="hover:text-gray-900 transition-colors"
                    title="Share"
                  >
                    <Share2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
              </div>
            </div>
          </div>
          
        </div>

        {/* Topics and Categories */}
        {((topics?.length && topics?.length > 0) || article.category) && (
          <div className="mt-4 space-y-2">
            {topics && topics.length > 0 && (
              <div>
                <span className="text-sm font-medium text-gray-700 mr-2">Topics:</span>
                <div className="inline-flex flex-wrap gap-1">
                  {topics.map((topic) => (
                    <Link
                      key={topic.id}
                      href={`/dashboard/topics/${topic.id}`}
                      className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded hover:bg-blue-200 transition-colors"
                    >
                      {topic.name}
                    </Link>
                  ))}
                </div>
              </div>
            )}
            {article.category && (
              <div>
                <span className="text-sm font-medium text-gray-700 mr-2">Category:</span>
                <span className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded">
                  {article.category}
                </span>
              </div>
            )}
          </div>
        )}

      {/* AI Summary Section */}
      {summary && (
        <div className="mb-8">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <div className="flex items-start gap-3">
              <div className="flex-1">
                <div className="text-blue-800 leading-relaxed">
                  <SummaryContent content={summary} className="" />
                </div>
                {article?.derivative?.summary_generated_at && (
                  <p className="text-sm text-blue-600 mt-4">
                    Generated on {formatDate(article.derivative.summary_generated_at)}
                    {article.derivative.llm_model_version && ` using ${article.derivative.llm_model_version}`}
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Content Tabs */}
      <div className="mb-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('content')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'content'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Full Article
            </button>
            {related_articles && related_articles.length > 0 && (
              <button
                onClick={() => setActiveTab('related')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'related'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Related Articles ({related_articles.length})
              </button>
            )}
          </nav>
        </div>
      </div>

      {/* Tab Content */}
      <div className="grid grid-cols-1 gap-8">
        <div>
          {activeTab === 'content' && (
            <div className="bg-white">
              {content ? (
                <div className="article-content">
                  <ArticleContent 
                    content={content}
                    className=""
                  />
                </div>
              ) : (
                <div className="text-center py-12 text-gray-500">
                  <p>No content available for this article.</p>
                  {article.url && (
                    <a
                      href={article.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="mt-2 inline-flex items-center text-blue-600 hover:text-blue-800"
                    >
                      View original source
                      <ExternalLink className="w-4 h-4 ml-1" />
                    </a>
                  )}
                </div>
              )}
            </div>
          )}


          {activeTab === 'related' && related_articles && related_articles.length > 0 && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900">Related Articles</h3>
              <div className="space-y-4">
                {related_articles.map((relatedArticle) => (
                  <div key={relatedArticle.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-sm transition-shadow">
                    <Link
                      href={`/dashboard/article/${relatedArticle.id}`}
                      className="block group"
                    >
                      <h4 className="font-medium text-gray-900 group-hover:text-blue-600 transition-colors mb-2">
                        {relatedArticle.title}
                      </h4>
                      <div className="flex items-center gap-4 text-sm text-gray-500">
                        {relatedArticle.author && <span>{relatedArticle.author}</span>}
                        {relatedArticle.published_at && (
                          <span>{formatDate(relatedArticle.published_at)}</span>
                        )}
                      </div>
                    </Link>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
