import React from 'react';
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import { sanitizeHtml, enhanceArticleHtml, enhanceSummaryHtml, containsHtml } from '@/lib/html-utils';

interface SafeHtmlContentProps {
  content: string;
  className?: string;
  isStrict?: boolean;
  enhanceStyles?: boolean;
  fallbackToText?: boolean;
  contentType?: 'article' | 'summary';
  isMarkdown?: boolean;
}

// 配置marked选项，支持锚点链接
const configureMarked = () => {
  marked.setOptions({
    breaks: true,
    gfm: true,
  });
  
  // 自定义渲染器来处理锚点链接
  const renderer = new marked.Renderer();
  
  renderer.link = function(token) {
    // 从token对象中提取参数
    const href = token.href || '';
    const title = token.title || null;
    const text = token.text || '';
    const titleAttr = title ? `title="${title}"` : '';
    
    // 如果是锚点链接，保持原样
    if (href && href.startsWith('#')) {
      return `<a href="${href}" ${titleAttr} class="text-blue-600 hover:text-blue-800">${text}</a>`;
    }
    // 其他外部链接在新窗口打开
    return `<a href="${href}" ${titleAttr} target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:text-blue-800">${text}</a>`;
  };
  
  marked.use({ renderer });
};

/**
 * 安全HTML内容显示组件
 * 自动清理HTML内容并安全渲染，支持Markdown
 */
export default function SafeHtmlContent({ 
  content, 
  className = '', 
  isStrict = false,
  enhanceStyles = true,
  fallbackToText = false,
  contentType = 'article',
  isMarkdown = false
}: SafeHtmlContentProps) {
  if (!content) {
    return null;
  }

  // 如果是Markdown内容，先转换为HTML
  if (isMarkdown) {
    configureMarked();
    const htmlContent = marked(content) as string;
    const cleanHtml = DOMPurify.sanitize(htmlContent, {
      ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'blockquote', 'a'],
      ALLOWED_ATTR: ['href', 'title', 'target', 'rel', 'class']
    });
    
    return (
      <div 
        className={`prose prose-sm max-w-none markdown-content ${className}`}
        dangerouslySetInnerHTML={{ __html: cleanHtml }}
      />
    );
  }

  // 检查是否包含HTML标签
  const hasHtml = containsHtml(content);
  
  // 如果不包含HTML标签，直接显示文本
  if (!hasHtml) {
    return (
      <div className={`whitespace-pre-wrap ${className}`}>
        {content}
      </div>
    );
  }

  // 如果设置了fallbackToText，将HTML转换为纯文本显示
  if (fallbackToText) {
    const textContent = content
      .replace(/<br\s*\/?>/gi, '\n')
      .replace(/<\/p>/gi, '\n\n')
      .replace(/<[^>]*>/g, '')
      .replace(/&nbsp;/g, ' ')
      .replace(/&amp;/g, '&')
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/&quot;/g, '"')
      .replace(/&#39;/g, "'")
      .trim();
    
    return (
      <div className={`whitespace-pre-wrap ${className}`}>
        {textContent}
      </div>
    );
  }

  // 清理HTML内容
  let cleanHtml = sanitizeHtml(content, isStrict);
  
  // 增强样式（如果启用）
  if (enhanceStyles && !isStrict) {
    if (contentType === 'summary') {
      cleanHtml = enhanceSummaryHtml(cleanHtml);
    } else {
      cleanHtml = enhanceArticleHtml(cleanHtml);
    }
  }

  return (
    <div 
      className={className}
      dangerouslySetInnerHTML={{ __html: cleanHtml }}
    />
  );
}

/**
 * 文章内容专用显示组件
 * 预配置了适合文章显示的设置
 */
export function ArticleContent({ content, className = '' }: { content: string; className?: string }) {
  return (
    <SafeHtmlContent 
      content={content}
      className={`prose prose-lg max-w-none ${className}`}
      isStrict={false}
      enhanceStyles={true}
      fallbackToText={false}
    />
  );
}

/**
 * 摘要内容显示组件
 * 使用摘要专用样式，支持Markdown渲染
 */
export function SummaryContent({ content, className = '', isMarkdown = true }: { content: string; className?: string; isMarkdown?: boolean }) {
  return (
    <SafeHtmlContent 
      content={content}
      className={className}
      isStrict={false}
      enhanceStyles={true}
      fallbackToText={false}
      contentType="summary"
      isMarkdown={isMarkdown}
    />
  );
}

/**
 * 纯文本内容显示组件
 * 将HTML转换为纯文本显示
 */
export function TextOnlyContent({ content, className = '' }: { content: string; className?: string }) {
  return (
    <SafeHtmlContent 
      content={content}
      className={className}
      isStrict={false}
      enhanceStyles={false}
      fallbackToText={true}
    />
  );
}
