import DOMPurify from 'dompurify';

/**
 * Configuration for DOMPurify to safely clean HTML content
 */
const PURIFY_CONFIG = {
  // 允许的HTML标签
  ALLOWED_TAGS: [
    'p', 'br', 'strong', 'b', 'em', 'i', 'u', 'strike', 'del', 's',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li',
    'blockquote', 'pre', 'code',
    'a', 'img',
    'table', 'thead', 'tbody', 'tr', 'th', 'td',
    'div', 'span',
    'sub', 'sup'
  ],
  
  // 允许的属性
  ALLOWED_ATTR: [
    'href', 'title', 'alt', 'src', 'width', 'height',
    'class', 'id', 'target', 'rel'
  ],
  
  // 允许的URI协议
  ALLOWED_URI_REGEXP: /^(?:(?:(?:f|ht)tps?|mailto|tel|callto|cid|xmpp):|[^a-z]|[a-z+.\-]+(?:[^a-z+.\-:]|$))/i,
  
  // 其他配置
  KEEP_CONTENT: true,
  RETURN_DOM: false,
  RETURN_DOM_FRAGMENT: false,
  RETURN_TRUSTED_TYPE: false
};

/**
 * 清理HTML内容，移除恶意脚本和不安全的标签/属性
 * @param htmlContent - 需要清理的HTML字符串
 * @param isStrict - 是否使用严格模式（仅允许基本格式标签）
 * @returns 清理后的安全HTML字符串
 */
export function sanitizeHtml(htmlContent: string, isStrict: boolean = false): string {
  if (!htmlContent) return '';
  
  const config = { ...PURIFY_CONFIG };
  
  if (isStrict) {
    // 严格模式：仅允许基本的文本格式标签
    config.ALLOWED_TAGS = ['a', 'p', 'br', 'strong', 'b', 'em', 'i', 'u'];
    config.ALLOWED_ATTR = [];
  }
  
  return DOMPurify.sanitize(htmlContent, config);
}

/**
 * 清理HTML内容并转换为纯文本
 * @param htmlContent - HTML字符串
 * @param maxLength - 最大长度限制
 * @returns 纯文本字符串
 */
export function htmlToText(htmlContent: string, maxLength?: number): string {
  if (!htmlContent) return '';
  
  // 首先清理HTML
  const cleanHtml = sanitizeHtml(htmlContent, true);
  
  // 转换为纯文本
  const textContent = cleanHtml
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<\/p>/gi, '\n\n')
    .replace(/<[^>]*>/g, '')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/\s+/g, ' ')
    .trim();
  
  if (maxLength && textContent.length > maxLength) {
    return textContent.substring(0, maxLength) + '...';
  }
  
  return textContent;
}

/**
 * 检查内容是否包含HTML标签
 * @param content - 要检查的内容
 * @returns 是否包含HTML标签
 */
export function containsHtml(content: string): boolean {
  if (!content) return false;
  return /<[^>]*>/g.test(content);
}

/**
 * 为文章内容添加适当的CSS类
 * @param htmlContent - 清理后的HTML内容
 * @returns 添加CSS类后的HTML内容
 */
export function enhanceArticleHtml(htmlContent: string): string {
  if (!htmlContent) return '';
  
  return htmlContent
    // 为段落添加样式类
    .replace(/<p>/g, '<p class="mb-4 text-gray-800 leading-relaxed">')
    // 为标题添加样式类
    .replace(/<h1>/g, '<h1 class="text-2xl font-bold mb-4 text-gray-900">')
    .replace(/<h2>/g, '<h2 class="text-xl font-bold mb-3 text-gray-900">')
    .replace(/<h3>/g, '<h3 class="text-lg font-semibold mb-3 text-gray-900">')
    .replace(/<h4>/g, '<h4 class="text-base font-semibold mb-2 text-gray-900">')
    // 为链接添加样式类
    .replace(/<a /g, '<a class="text-blue-600 hover:text-blue-800" target="_blank" rel="noopener noreferrer" ')
    // 为列表添加样式类
    .replace(/<ul>/g, '<ul class="list-disc list-inside mb-4 ml-4">')
    .replace(/<ol>/g, '<ol class="list-decimal list-inside mb-4 ml-4">')
    .replace(/<li>/g, '<li class="mb-1">')
    // 为引用添加样式类
    .replace(/<blockquote>/g, '<blockquote class="border-l-4 border-gray-300 pl-4 mb-4 italic text-gray-700">')
    // 为代码添加样式类
    .replace(/<code>/g, '<code class="bg-gray-100 px-1 py-0.5 rounded text-sm font-mono">')
    .replace(/<pre>/g, '<pre class="bg-gray-100 p-4 rounded mb-4 overflow-x-auto"><code class="text-sm font-mono">')
    .replace(/<\/pre>/g, '</code></pre>')
    // 为图片添加样式类
    .replace(/<img /g, '<img class="max-w-full h-auto rounded mb-4" ');
}

/**
 * 为摘要内容添加适当的CSS类
 * @param htmlContent - 清理后的HTML内容
 * @returns 添加CSS类后的HTML内容
 */
export function enhanceSummaryHtml(htmlContent: string): string {
  if (!htmlContent) return '';
  
  return htmlContent
    // 为段落添加摘要样式类
    .replace(/<p>/g, '<p class="mb-2 text-gray-700 leading-normal text-sm">')
    // 为标题添加摘要样式类
    .replace(/<h1>/g, '<h1 class="text-lg font-semibold mb-2 text-gray-800">')
    .replace(/<h2>/g, '<h2 class="text-base font-semibold mb-2 text-gray-800">')
    .replace(/<h3>/g, '<h3 class="text-sm font-medium mb-1 text-gray-800">')
    .replace(/<h4>/g, '<h4 class="text-sm font-medium mb-1 text-gray-800">')
    // 为链接添加摘要样式类
    .replace(/<a /g, '<a class="text-blue-500 hover:text-blue-700 text-sm" rel="noopener noreferrer" ')
    // 为列表添加摘要样式类
    .replace(/<ul>/g, '<ul class="list-disc list-inside mb-2 ml-2">')
    .replace(/<ol>/g, '<ol class="list-decimal list-inside mb-2 ml-2">')
    .replace(/<li>/g, '<li class="mb-0.5 text-sm">')
    // 为引用添加摘要样式类
    .replace(/<blockquote>/g, '<blockquote class="border-l-2 border-gray-200 pl-2 mb-2 italic text-gray-600 text-sm">')
    // 为代码添加摘要样式类
    .replace(/<code>/g, '<code class="bg-gray-50 px-1 py-0.5 rounded text-xs font-mono">')
    .replace(/<pre>/g, '<pre class="bg-gray-50 p-2 rounded mb-2 overflow-x-auto text-xs"><code class="font-mono">')
    .replace(/<\/pre>/g, '</code></pre>')
    // 为图片添加摘要样式类
    .replace(/<img /g, '<img class="max-w-full h-auto rounded mb-2 max-h-32" ');
}

/**
 * 提取文章摘要（不包含HTML标签）
 * @param content - 文章内容
 * @param maxLength - 摘要最大长度
 * @returns 文章摘要
 */
export function extractSummary(content: string, maxLength: number = 200): string {
  const textContent = htmlToText(content);
  
  if (textContent.length <= maxLength) {
    return textContent;
  }
  
  // 尝试在句号处截断
  const sentences = textContent.split('.');
  let summary = '';
  
  for (const sentence of sentences) {
    const nextLength = summary.length + sentence.length + 1;
    if (nextLength > maxLength) {
      break;
    }
    summary += sentence + '.';
  }
  
  // 如果没有找到合适的句号，直接截断
  if (summary.length === 0) {
    summary = textContent.substring(0, maxLength) + '...';
  }
  
  return summary.trim();
}
