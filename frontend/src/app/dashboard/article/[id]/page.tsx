'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { apiClient } from '@/lib/api-client';
import { Article, ArticleDerivative, Topic, Cluster } from '@/lib/types';
import LoadingSpinner from '@/components/LoadingSpinner';
import { formatDate } from '@/lib/utils';

interface ArticleDetail {
  article: Article;
  derivative?: ArticleDerivative;
  related_articles?: Article[];
  topics?: Topic[];
  clusters?: Cluster[];
}

export default function ArticleDetailPage() {
  const params = useParams();
  const router = useRouter();
  const articleId = parseInt(params.id as string);
  
  const [articleDetail, setArticleDetail] = useState<ArticleDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showFullContent, setShowFullContent] = useState(false);
  const [activeTab, setActiveTab] = useState<'content' | 'summary' | 'related'>('content');

  useEffect(() => {
    if (isNaN(articleId)) {
      setError('Invalid article ID');
      setIsLoading(false);
      return;
    }
    
    fetchArticleDetail();
  }, [articleId]);

  const fetchArticleDetail = async () => {
    try {
      // Note: This endpoint might not exist yet in the backend, 
      // so we'll construct it from available data
      const data = await apiClient.get<ArticleDetail>(`/api/article/${articleId}`);
      setArticleDetail(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load article details');
    } finally {
      setIsLoading(false);
    }
  };

  const calculateReadingTime = (content: string): number => {
    const wordsPerMinute = 200;
    const wordCount = content.trim().split(/\s+/).length;
    return Math.ceil(wordCount / wordsPerMinute);
  };

  if (isLoading) {
    return <LoadingSpinner size="lg" className="mt-20" />;
  }

  if (error || !articleDetail) {
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

  const { article, derivative, related_articles, topics, clusters } = articleDetail;
  const content = article.content || '';
  const summary = derivative?.summary;
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
              <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <div>
              <h1 className="text-3xl font-semibold text-gray-900 mb-3 leading-tight">
                {article.title}
              </h1>
              <div className="flex items-center gap-6 text-sm text-gray-600">
                {article.author && (
                  <span className="flex items-center gap-1">
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                    </svg>
                    {article.author}
                  </span>
                )}
                {article.published_at && (
                  <span className="flex items-center gap-1">
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
                    </svg>
                    {formatDate(article.published_at)}
                  </span>
                )}
                {readingTime > 0 && (
                  <span className="flex items-center gap-1">
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M12 7a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0V8.414l-4.293 4.293a1 1 0 01-1.414 0L8 10.414l-4.293 4.293a1 1 0 01-1.414-1.414l5-5a1 1 0 011.414 0L11 10.586 14.586 7H12z" clipRule="evenodd" />
                    </svg>
                    {readingTime} min read
                  </span>
                )}
                <span className={`px-2 py-1 text-xs rounded-full ${
                  article.processing_status === 'completed' ? 'bg-green-100 text-green-800' :
                  article.processing_status === 'processing' ? 'bg-yellow-100 text-yellow-800' :
                  article.processing_status === 'failed' ? 'bg-red-100 text-red-800' :
                  'bg-gray-100 text-gray-600'
                }`}>
                  {article.processing_status}
                </span>
              </div>
            </div>
          </div>
          
          <div className="flex gap-3">
            {article.url && (
              <a
                href={article.url}
                target="_blank"
                rel="noopener noreferrer"
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded hover:bg-gray-50 transition-colors flex items-center gap-2"
              >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4.25 5.5a.75.75 0 00-.75.75v8.5c0 .414.336.75.75.75h8.5a.75.75 0 00.75-.75v-4a.75.75 0 011.5 0v4A2.25 2.25 0 0112.75 17h-8.5A2.25 2.25 0 012 14.75v-8.5A2.25 2.25 0 014.25 4h5a.75.75 0 010 1.5h-5z" clipRule="evenodd" />
                  <path fillRule="evenodd" d="M6.194 12.753a.75.75 0 001.06.053L16.5 4.44v2.81a.75.75 0 001.5 0v-4.5a.75.75 0 00-.75-.75h-4.5a.75.75 0 000 1.5h2.553l-9.056 8.194a.75.75 0 00-.053 1.06z" clipRule="evenodd" />
                </svg>
                Original Source
              </a>
            )}
            <Link
              href="/dashboard"
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
            >
              Dashboard
            </Link>
          </div>
        </div>

        {/* Topics and Categories */}
        {(topics?.length > 0 || article.category) && (
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
      </div>

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
            {summary && (
              <button
                onClick={() => setActiveTab('summary')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'summary'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                AI Summary
              </button>
            )}
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
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        <div className="lg:col-span-3">
          {activeTab === 'content' && (
            <div className="bg-white">
              {content ? (
                <div className="prose prose-lg max-w-none">
                  <div 
                    className={`text-gray-800 leading-relaxed ${
                      !showFullContent && content.length > 2000 ? 'line-clamp-[50]' : ''
                    }`}
                  >
                    {content.split('\n').map((paragraph, index) => (
                      <p key={index} className="mb-4 text-base leading-7">
                        {paragraph}
                      </p>
                    ))}
                  </div>
                  {!showFullContent && content.length > 2000 && (
                    <button
                      onClick={() => setShowFullContent(true)}
                      className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                    >
                      Show Full Article
                    </button>
                  )}
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
                      <svg className="w-4 h-4 ml-1" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M4.25 5.5a.75.75 0 00-.75.75v8.5c0 .414.336.75.75.75h8.5a.75.75 0 00.75-.75v-4a.75.75 0 011.5 0v4A2.25 2.25 0 0112.75 17h-8.5A2.25 2.25 0 012 14.75v-8.5A2.25 2.25 0 014.25 4h5a.75.75 0 010 1.5h-5z" clipRule="evenodd" />
                      </svg>
                    </a>
                  )}
                </div>
              )}
            </div>
          )}

          {activeTab === 'summary' && summary && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
              <div className="flex items-start gap-3">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <svg className="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M3 4a1 1 0 011-1h4a1 1 0 010 2H6.414l2.293 2.293a1 1 0 01-1.414 1.414L5 6.414V8a1 1 0 01-2 0V4zm9 1a1 1 0 010-2h4a1 1 0 011 1v4a1 1 0 01-2 0V6.414l-2.293 2.293a1 1 0 11-1.414-1.414L13.586 5H12zm-9 7a1 1 0 012 0v1.586l2.293-2.293a1 1 0 111.414 1.414L6.414 15H8a1 1 0 010 2H4a1 1 0 01-1-1v-4zm13-1a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 010-2h1.586l-2.293-2.293a1 1 0 111.414-1.414L15.586 13H14a1 1 0 01-1-1z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-blue-900 mb-3">AI-Generated Summary</h3>
                  <p className="text-blue-800 leading-relaxed">{summary}</p>
                  {derivative?.summary_generated_at && (
                    <p className="text-sm text-blue-600 mt-4">
                      Generated on {formatDate(derivative.summary_generated_at)}
                      {derivative.llm_model_version && ` using ${derivative.llm_model_version}`}
                    </p>
                  )}
                </div>
              </div>
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

        {/* Sidebar */}
        <div className="lg:col-span-1 space-y-6">
          {/* Article Metadata */}
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <h3 className="font-semibold text-gray-900 mb-3">Article Information</h3>
            <div className="space-y-2 text-sm">
              <div>
                <span className="font-medium text-gray-700">Status:</span>
                <span className={`ml-2 px-2 py-1 text-xs rounded-full ${
                  article.processing_status === 'completed' ? 'bg-green-100 text-green-800' :
                  article.processing_status === 'processing' ? 'bg-yellow-100 text-yellow-800' :
                  article.processing_status === 'failed' ? 'bg-red-100 text-red-800' :
                  'bg-gray-100 text-gray-600'
                }`}>
                  {article.processing_status}
                </span>
              </div>
              {article.created_at && (
                <div>
                  <span className="font-medium text-gray-700">Added:</span>
                  <span className="ml-2 text-gray-600">{formatDate(article.created_at)}</span>
                </div>
              )}
              {readingTime > 0 && (
                <div>
                  <span className="font-medium text-gray-700">Reading time:</span>
                  <span className="ml-2 text-gray-600">{readingTime} minutes</span>
                </div>
              )}
              {content && (
                <div>
                  <span className="font-medium text-gray-700">Word count:</span>
                  <span className="ml-2 text-gray-600">{content.trim().split(/\s+/).length} words</span>
                </div>
              )}
            </div>
          </div>

          {/* Clusters */}
          {clusters && clusters.length > 0 && (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <h3 className="font-semibold text-gray-900 mb-3">Part of Clusters</h3>
              <div className="space-y-2">
                {clusters.map((cluster) => (
                  <Link
                    key={cluster.id}
                    href={`/dashboard/clusters/${cluster.id}`}
                    className="block p-3 border border-gray-200 rounded bg-white hover:bg-gray-50 transition-colors"
                  >
                    <h4 className="font-medium text-gray-900 text-sm mb-1">{cluster.title}</h4>
                    <p className="text-xs text-gray-600">{cluster.article_count} articles</p>
                  </Link>
                ))}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <h3 className="font-semibold text-gray-900 mb-3">Actions</h3>
            <div className="space-y-2">
              {article.url && (
                <a
                  href={article.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block w-full px-3 py-2 text-sm text-center border border-gray-300 rounded hover:bg-white transition-colors"
                >
                  Open Original
                </a>
              )}
              <button
                onClick={() => navigator.share?.({ title: article.title, url: window.location.href }) || 
                  navigator.clipboard?.writeText(window.location.href)}
                className="block w-full px-3 py-2 text-sm text-center border border-gray-300 rounded hover:bg-white transition-colors"
              >
                Share Article
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}