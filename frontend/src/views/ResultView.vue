<template>
  <div class="result-container">
    <div class="result-header">
      <h2>📊 检测结果</h2>
      <div class="header-actions">
        <span class="email-id">Email ID: <code>{{ emailId }}</code></span>
        <button @click="loadResult" :disabled="loading" class="refresh-btn">
          <span v-if="loading" class="loading"></span>
          {{ loading ? "加载中..." : "🔄 刷新" }}
        </button>
      </div>
    </div>

    <div v-if="resultData" class="result-layout">
      <!-- 左侧：邮件预览 + 特征分析 -->
      <div class="left-panel">
        <!-- 邮件预览 -->
        <div class="email-preview card">
          <div class="preview-header">
            <h3>📧 邮件预览</h3>
            <div class="header-right">
              <span v-if="hasAttachments" class="attachment-badge">
                📎 {{ attachments.length }}
              </span>
              <div class="view-toggle">
                <button 
                  :class="['toggle-btn', { active: viewMode === 'raw' }]"
                  @click="viewMode = 'raw'"
                >
                  📄 原文
                </button>
                <button 
                  :class="['toggle-btn', { active: viewMode === 'rendered' }]"
                  @click="viewMode = 'rendered'"
                >
                  🎨 渲染
                </button>
                <button 
                  v-if="hasAttachments"
                  :class="['toggle-btn', { active: viewMode === 'attachments' }]"
                  @click="viewMode = 'attachments'"
                >
                  📎 附件
                </button>
              </div>
            </div>
          </div>
          
          <div class="email-content">
            <transition name="fade" mode="out-in">
              <pre v-if="viewMode === 'raw'" key="raw">{{ emailContent }}</pre>
              <div v-else-if="viewMode === 'rendered'" key="rendered" class="rendered-content" v-html="renderedContent"></div>
              
              <!-- 附件列表视图 -->
              <div v-else-if="viewMode === 'attachments'" key="attachments" class="attachments-view">
                <div class="attachments-grid">
                  <div 
                    v-for="attachment in attachments" 
                    :key="attachment.index" 
                    class="attachment-card"
                    @click="previewAttachment(attachment)"
                  >
                    <div class="attachment-icon-large">
                      {{ getFileIcon(attachment.filename) }}
                    </div>
                    <div class="attachment-info">
                      <div class="attachment-name-large">{{ attachment.filename }}</div>
                      <div class="attachment-meta-large">
                        <span class="attachment-size">{{ attachment.size_formatted }}</span>
                        <span class="attachment-separator">•</span>
                        <span class="attachment-type">{{ getFileExtension(attachment.filename) }}</span>
                      </div>
                    </div>
                    <div class="attachment-preview-hint">点击预览</div>
                  </div>
                </div>
              </div>
            </transition>
          </div>
        </div>

        <!-- 特征分析 -->
        <div class="features-analysis card">
          <h3>🔍 特征分析</h3>
          
          <!-- LLM 智能分析 -->
          <div v-if="resultData.llm_detection && resultData.llm_detection.llm_supported" class="feature-section">
            <h4>🤖 LLM 智能分析</h4>
            <div class="llm-analysis-content">
              <div class="llm-provider-info">
                <span class="provider-label">使用模型:</span>
                <span class="provider-value">{{ resultData.llm_detection.provider }} - {{ resultData.llm_detection.model }}</span>
              </div>
              <div class="llm-reasoning-box">
                <h5>分析推理:</h5>
                <p>{{ resultData.llm_detection.reasoning || '无详细推理信息' }}</p>
              </div>
            </div>
          </div>

          <!-- 传统特征 -->
          <div class="feature-section">
            <h4>📊 传统特征</h4>
            <div v-if="resultData.traditional_features && Object.keys(getDisplayFeatures(resultData.traditional_features)).length > 0" class="features-grid">
              <div class="feature-item" v-for="(value, key) in getDisplayFeatures(resultData.traditional_features)" :key="key">
                <span class="label">{{ formatFeatureName(key) }}</span>
                <span class="value">{{ formatFeatureValue(value) }}</span>
              </div>
            </div>
            <div v-else class="no-features">
              <p>暂无传统特征数据</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：风险分析 -->
      <div class="right-panel">
        <!-- 风险评分卡片 -->
        <div class="risk-card card" :class="getRiskClass(resultData.risk_score)">
          <div class="risk-header">
            <h3>⚠️ 风险评分</h3>
            <span class="status-badge" :class="resultData.is_phishing ? 'phishing' : 'benign'">
              {{ resultData.is_phishing ? '钓鱼邮件' : '正常邮件' }}
            </span>
          </div>
          <div class="risk-score">
            <span class="risk-score-value">{{ (resultData.risk_score * 100).toFixed(1) }}</span>
            <span class="score-unit">%</span>
          </div>
          <div class="risk-bar">
            <div class="risk-bar-fill" :style="{ width: (resultData.risk_score * 100) + '%' }"></div>
          </div>
          <div class="attack-type">
            攻击类型: <strong>{{ getAttackTypeLabel(resultData.attack_type) }}</strong>
          </div>
        </div>

        <!-- 模型得分 -->
        <div class="models-scores card">
          <h3>🎯 模型得分</h3>
          <div class="scores-list">
            <div class="score-item" v-if="resultData.rule_score !== undefined">
              <span class="score-label">📋 规则检测</span>
              <span class="score-value">{{ (resultData.rule_score * 100).toFixed(1) }}%</span>
            </div>
            <div class="score-item" v-if="resultData.iforest_score !== undefined && resultData.iforest_score !== null">
              <span class="score-label">🌲 IsolationForest</span>
              <span class="score-value">{{ (resultData.iforest_score * 100).toFixed(1) }}%</span>
            </div>
            <div class="score-item" v-if="resultData.phishmmf_rf_score !== undefined && resultData.phishmmf_rf_score !== null">
              <span class="score-label">🎯 PhishMMF-RF</span>
              <span class="score-value">{{ (resultData.phishmmf_rf_score * 100).toFixed(1) }}%</span>
            </div>
            <div class="score-item" v-if="resultData.phishmmf_xgb_score !== undefined && resultData.phishmmf_xgb_score !== null">
              <span class="score-label">⚡ PhishMMF-XGB</span>
              <span class="score-value">{{ (resultData.phishmmf_xgb_score * 100).toFixed(1) }}%</span>
            </div>
            <div class="score-item" v-if="resultData.llm_semantic_score !== undefined && resultData.llm_semantic_score !== null">
              <span class="score-label">🧠 LLM 语义</span>
              <span class="score-value">{{ (resultData.llm_semantic_score * 100).toFixed(1) }}%</span>
            </div>
            <div class="score-item" v-if="resultData.llm_detection_score !== undefined && resultData.llm_detection_score !== null">
              <span class="score-label">🤖 LLM 检测</span>
              <span class="score-value">{{ (resultData.llm_detection_score * 100).toFixed(1) }}%</span>
            </div>
          </div>
        </div>

        <!-- 模型使用情况 -->
        <div v-if="resultData.models_used" class="models-status card">
          <h3>✅ 模型使用情况</h3>
          <div class="status-list">
            <div class="status-item" :class="{ active: resultData.models_used.rule }">
              <span class="status-icon">{{ resultData.models_used.rule ? '✅' : '❌' }}</span>
              <span class="status-label">规则引擎</span>
            </div>
            <div class="status-item" :class="{ active: resultData.models_used.iforest }">
              <span class="status-icon">{{ resultData.models_used.iforest ? '✅' : '❌' }}</span>
              <span class="status-label">IsolationForest</span>
            </div>
            <div class="status-item" :class="{ active: resultData.models_used.phishmmf_rf }">
              <span class="status-icon">{{ resultData.models_used.phishmmf_rf ? '✅' : '❌' }}</span>
              <span class="status-label">PhishMMF-RF</span>
            </div>
            <div class="status-item" :class="{ active: resultData.models_used.phishmmf_xgb }">
              <span class="status-icon">{{ resultData.models_used.phishmmf_xgb ? '✅' : '❌' }}</span>
              <span class="status-label">PhishMMF-XGB</span>
            </div>
            <div class="status-item" :class="{ active: resultData.models_used.llm }">
              <span class="status-icon">{{ resultData.models_used.llm ? '✅' : '❌' }}</span>
              <span class="status-label">LLM 分析</span>
            </div>
          </div>
        </div>

        <!-- 检测原因 -->
        <div v-if="resultData.reasons && resultData.reasons.length > 0" class="detection-reasons card">
          <h3>📝 检测原因</h3>
          <ul class="reasons-list">
            <li v-for="(reason, idx) in resultData.reasons" :key="idx">{{ reason }}</li>
          </ul>
        </div>


      </div>
    </div>

    <div v-else-if="!loading" class="hint error">
      暂无检测结果，请先执行检测。
    </div>

    <!-- 附件预览模态框 -->
    <div v-if="showPreviewModal" class="modal-overlay" @click="closePreviewModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>📎 附件详情</h3>
          <button class="modal-close" @click="closePreviewModal">✕</button>
        </div>
        <div class="modal-body" v-if="currentAttachment">
          <!-- 加载状态 -->
          <div v-if="loadingAttachment" class="loading-state">
            <div class="loading-spinner"></div>
            <p>正在加载附件内容...</p>
          </div>
          
          <!-- 附件信息 -->
          <div v-else>
            <div class="attachment-preview-icon">
              {{ getFileIcon(currentAttachment.filename) }}
            </div>
            <div class="attachment-preview-info">
              <div class="info-row">
                <span class="info-label">文件名</span>
                <span class="info-value">{{ attachmentContent ? getCorrectFilename(currentAttachment.filename) : currentAttachment.filename }}</span>
              </div>
              <div class="info-row" v-if="currentAttachment.filename !== getCorrectFilename(currentAttachment.filename) && attachmentContent">
                <span class="info-label">原始文件名</span>
                <span class="info-value" style="opacity: 0.6;">{{ currentAttachment.filename }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">文件大小</span>
                <span class="info-value">{{ currentAttachment.size_formatted }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">文件类型</span>
                <span class="info-value">{{ currentAttachment.content_type }}</span>
              </div>
              <div class="info-row" v-if="currentAttachment.creation_date">
                <span class="info-label">创建时间</span>
                <span class="info-value">{{ currentAttachment.creation_date }}</span>
              </div>
            </div>
            
            <!-- 附件预览区域 -->
            <div v-if="attachmentContent && canPreview(currentAttachment.filename)" class="attachment-preview-area">
              <h4>📄 内容预览</h4>
              
              <!-- 图片预览 -->
              <div v-if="isImage(currentAttachment.filename)" class="image-preview">
                <img :src="getPreviewContent()" :alt="currentAttachment.filename" />
              </div>
              
              <!-- 文本预览 -->
              <div v-else-if="isText(currentAttachment.filename)" class="text-preview">
                <pre>{{ getPreviewContent() }}</pre>
              </div>
              
              <!-- PDF 预览 -->
              <div v-else-if="isPDF(currentAttachment.filename)" class="pdf-preview">
                <div class="pdf-viewer-container">
                  <iframe 
                    :src="getPreviewContent()" 
                    frameborder="0"
                    @error="handlePDFError"
                  ></iframe>
                  <div v-if="pdfError" class="pdf-error-overlay">
                    <div class="error-content">
                      <div class="error-icon">📄</div>
                      <h4>PDF 预览不可用</h4>
                      <p>您的浏览器可能不支持内嵌 PDF 预览。</p>
                      <button @click="downloadPDF" class="download-btn">
                        💾 下载 PDF 文件
                      </button>
                      <button @click="openPDFNewTab" class="open-btn">
                        🔗 在新标签页打开
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 不支持预览的提示 -->
            <div v-else-if="attachmentContent && !canPreview(currentAttachment.filename)" class="preview-notice warning">
              <div class="notice-icon">⚠️</div>
              <div class="notice-text">
                <strong>无法预览</strong>
                <p>此文件类型不支持在线预览。附件内容已加载，但需要下载后使用相应软件打开。</p>
              </div>
            </div>
            
            <div class="preview-notice">
              <div class="notice-icon">🔒</div>
              <div class="notice-text">
                <strong>安全环境</strong>
                <p>附件预览功能运行在隔离的安全环境中。所有附件内容均在沙箱中处理，不会对系统造成威胁。</p>
                <p>建议：对于可疑附件，请在完全隔离的虚拟环境中进一步分析。</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from "vue";
import { useRoute } from "vue-router";
import axios from "axios";

const route = useRoute();
const emailId = route.params.emailId;
const loading = ref(false);
const resultData = ref(null);
const emailContent = ref("");
const viewMode = ref("raw"); // 'raw' 或 'rendered' 或 'attachments'
const isTransitioning = ref(false);
const renderedContent = ref("");
const attachments = ref([]);
const hasAttachments = ref(false);
const showPreviewModal = ref(false);
const currentAttachment = ref(null);
const pdfError = ref(false);

// 同步左右面板高度
const syncPanelHeights = () => {
  nextTick(() => {
    const rightPanel = document.querySelector('.right-panel');
    const leftPanel = document.querySelector('.left-panel');
    
    if (rightPanel && leftPanel) {
      const rightHeight = rightPanel.offsetHeight;
      leftPanel.style.height = `${rightHeight}px`;
    }
  });
};

const loadResult = async () => {
  loading.value = true;
  try {
    console.log('正在加载结果，email_id:', emailId);
    const res = await axios.get(`/api/results/${emailId}`);
    console.log('结果数据:', res.data);
    resultData.value = res.data;
    
    // 获取邮件内容
    try {
      const emailRes = await axios.get(`/api/emails/${emailId}`);
      console.log('邮件内容:', emailRes.data);
      
      // 优先使用后端解码后的内容
      const decodedContent = emailRes.data.decoded_content || emailRes.data.content;
      emailContent.value = emailRes.data.content || "无法加载邮件内容";
      
      // 提取附件信息
      attachments.value = emailRes.data.attachments || [];
      hasAttachments.value = emailRes.data.has_attachments || false;
      console.log('附件数量:', attachments.value.length);
      
      // 处理渲染内容（使用解码后的内容）
      console.log('原始邮件内容长度:', emailContent.value.length);
      console.log('解码后内容长度:', decodedContent.length);
      renderedContent.value = processEmailForRendering(decodedContent);
      console.log('渲染后内容长度:', renderedContent.value.length);
    } catch (e) {
      console.error('获取邮件内容失败:', e);
      emailContent.value = "无法加载邮件内容";
      renderedContent.value = "无法加载邮件内容";
    }
  } catch (e) {
    console.error('加载结果失败:', e);
    console.error('错误详情:', e.response?.data);
    resultData.value = null;
  } finally {
    loading.value = false;
    // 同步左右面板高度
    syncPanelHeights();
  }
};

const processEmailForRendering = (content) => {
  if (!content) return '<div style="color: #94a3b8;">无邮件内容</div>';
  
  // 后端已经解码，直接处理内容
  
  // 1. 尝试提取 HTML 内容
  // 检查是否包含完整的 HTML 文档
  const htmlDocMatch = content.match(/<html[\s\S]*?<\/html>/i);
  if (htmlDocMatch) {
    return sanitizeHTML(htmlDocMatch[0]);
  }
  
  // 检查是否包含 body 标签
  const bodyMatch = content.match(/<body[\s\S]*?<\/body>/i);
  if (bodyMatch) {
    return sanitizeHTML(bodyMatch[0]);
  }
  
  // 检查是否包含任何 HTML 标签
  if (/<(p|div|table|h[1-6]|ul|ol|li|br|a|img|span|strong|em|b|i)[\s\S]*?>/i.test(content)) {
    // 可能是 HTML 片段
    return sanitizeHTML(content);
  }
  
  // 2. 纯文本转换为 HTML
  let html = content
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\n\n+/g, '</p><p>')
    .replace(/\n/g, '<br>')
    .replace(/(https?:\/\/[^\s<]+)/g, '<a href="$1" target="_blank" rel="noopener noreferrer" style="color: #3b82f6; text-decoration: underline;">$1</a>')
    .replace(/([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/g, '<a href="mailto:$1" style="color: #3b82f6; text-decoration: underline;">$1</a>');
  
  return `<div style="font-family: Arial, sans-serif; line-height: 1.8; color: #cbd5e1; padding: 1rem;"><p>${html}</p></div>`;
};

const sanitizeHTML = (html) => {
  // 基本的 HTML 清理，只移除潜在危险的标签和属性
  let cleaned = html
    .replace(/<script[\s\S]*?<\/script>/gi, '')
    .replace(/<iframe[\s\S]*?<\/iframe>/gi, '')
    .replace(/on\w+\s*=\s*["'][^"']*["']/gi, '') // 移除事件处理器
    .replace(/javascript:/gi, '')
    .replace(/<object[\s\S]*?<\/object>/gi, '')
    .replace(/<embed[\s\S]*?>/gi, '');
  
  // 添加包装器和基础样式
  cleaned = `
    <div class="email-html-wrapper">
      <style>
        .email-html-wrapper {
          font-family: Arial, sans-serif;
          line-height: 1.6;
        }
        .email-html-wrapper * {
          max-width: 100%;
        }
        .email-html-wrapper img {
          max-width: 100%;
          height: auto;
          display: block;
          margin: 0.5rem 0;
        }
        .email-html-wrapper table {
          border-collapse: collapse;
        }
        .email-html-wrapper td,
        .email-html-wrapper th {
          padding: 0.5rem;
        }
      </style>
      ${cleaned}
    </div>
  `;
  
  return cleaned;
};

const getFileIcon = (filename) => {
  const ext = filename.split('.').pop().toLowerCase();
  const iconMap = {
    'pdf': '📄',
    'doc': '📝',
    'docx': '📝',
    'xls': '📊',
    'xlsx': '📊',
    'ppt': '📊',
    'pptx': '📊',
    'zip': '📦',
    'rar': '📦',
    '7z': '📦',
    'jpg': '🖼️',
    'jpeg': '🖼️',
    'png': '🖼️',
    'gif': '🖼️',
    'txt': '📃',
    'exe': '⚠️',
    'bat': '⚠️',
    'sh': '⚠️',
  };
  return iconMap[ext] || '📎';
};

const getFileExtension = (filename) => {
  const ext = filename.split('.').pop().toUpperCase();
  return ext;
};

const attachmentContent = ref(null);
const loadingAttachment = ref(false);

const previewAttachment = async (attachment) => {
  currentAttachment.value = attachment;
  attachmentContent.value = null;
  showPreviewModal.value = true;
  
  // 加载附件内容
  await loadAttachmentContent(attachment.index);
};

const loadAttachmentContent = async (attachmentIndex) => {
  loadingAttachment.value = true;
  try {
    const res = await axios.get(`/api/emails/${emailId}/attachments/${attachmentIndex}`);
    attachmentContent.value = res.data.attachment;
    console.log('附件内容加载成功:', attachmentContent.value);
  } catch (e) {
    console.error('加载附件内容失败:', e);
    attachmentContent.value = null;
  } finally {
    loadingAttachment.value = false;
  }
};

const closePreviewModal = () => {
  showPreviewModal.value = false;
  currentAttachment.value = null;
  attachmentContent.value = null;
  pdfError.value = false;
};

const canPreview = (filename) => {
  // 首先检查文件扩展名
  const ext = filename.split('.').pop().toLowerCase();
  const previewableTypes = ['txt', 'pdf', 'jpg', 'jpeg', 'png', 'gif', 'html', 'htm', 'json', 'xml', 'csv'];
  if (previewableTypes.includes(ext)) {
    return true;
  }
  
  // 如果扩展名不匹配，检查 MIME 类型
  if (attachmentContent.value && attachmentContent.value.content_type) {
    const contentType = attachmentContent.value.content_type.toLowerCase();
    
    // 检查是否为可预览的 MIME 类型
    if (contentType.startsWith('image/')) return true;
    if (contentType.startsWith('text/')) return true;
    if (contentType === 'application/pdf' || contentType.includes('pdf')) return true;
    if (contentType === 'application/json') return true;
    if (contentType === 'application/xml' || contentType.includes('xml')) return true;
  }
  
  return false;
};

const isImage = (filename) => {
  // 检查文件扩展名
  const ext = filename.split('.').pop().toLowerCase();
  if (['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'].includes(ext)) {
    return true;
  }
  
  // 检查 MIME 类型
  if (attachmentContent.value && attachmentContent.value.content_type) {
    return attachmentContent.value.content_type.toLowerCase().startsWith('image/');
  }
  
  return false;
};

const isText = (filename) => {
  // 检查文件扩展名
  const ext = filename.split('.').pop().toLowerCase();
  if (['txt', 'html', 'htm', 'json', 'xml', 'csv', 'log', 'md'].includes(ext)) {
    return true;
  }
  
  // 检查 MIME 类型
  if (attachmentContent.value && attachmentContent.value.content_type) {
    const contentType = attachmentContent.value.content_type.toLowerCase();
    return contentType.startsWith('text/') || 
           contentType === 'application/json' ||
           contentType === 'application/xml' ||
           contentType.includes('xml');
  }
  
  return false;
};

const isPDF = (filename) => {
  // 检查文件扩展名
  if (filename.toLowerCase().endsWith('.pdf')) {
    return true;
  }
  
  // 检查 MIME 类型
  if (attachmentContent.value && attachmentContent.value.content_type) {
    const contentType = attachmentContent.value.content_type.toLowerCase();
    return contentType === 'application/pdf' || contentType.includes('pdf');
  }
  
  return false;
};

// 获取正确的文件名（如果是 PDF 但没有扩展名，自动添加）
const getCorrectFilename = (filename) => {
  if (!attachmentContent.value) return filename;
  
  const contentType = attachmentContent.value.content_type?.toLowerCase() || '';
  const isPdfType = contentType === 'application/pdf' || contentType.includes('pdf');
  
  // 如果是 PDF 类型但文件名没有 .pdf 扩展名
  if (isPdfType && !filename.toLowerCase().endsWith('.pdf')) {
    return `${filename}.pdf`;
  }
  
  return filename;
};

const getPreviewContent = () => {
  if (!attachmentContent.value || !attachmentContent.value.content) {
    return null;
  }
  
  const filename = attachmentContent.value.filename;
  const base64Content = attachmentContent.value.content;
  
  if (isImage(filename)) {
    // 图片预览
    const mimeType = attachmentContent.value.content_type || 'image/jpeg';
    return `data:${mimeType};base64,${base64Content}`;
  } else if (isText(filename)) {
    // 文本预览 - 解码 base64
    try {
      const decoded = atob(base64Content);
      return decoded;
    } catch (e) {
      console.error('文本解码失败:', e);
      return null;
    }
  } else if (isPDF(filename)) {
    // PDF 预览 - 使用 Blob URL 更可靠
    try {
      const binaryString = atob(base64Content);
      const bytes = new Uint8Array(binaryString.length);
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }
      const blob = new Blob([bytes], { type: 'application/pdf' });
      return URL.createObjectURL(blob);
    } catch (e) {
      console.error('PDF 处理失败:', e);
      pdfError.value = true;
      return null;
    }
  }
  
  return null;
};

const handlePDFError = () => {
  console.error('PDF iframe 加载失败');
  pdfError.value = true;
};

const downloadPDF = () => {
  if (!attachmentContent.value || !attachmentContent.value.content) return;
  
  try {
    const base64Content = attachmentContent.value.content;
    const binaryString = atob(base64Content);
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }
    const blob = new Blob([bytes], { type: 'application/pdf' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    // 使用修正后的文件名（自动添加 .pdf 扩展名）
    a.download = getCorrectFilename(attachmentContent.value.filename);
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  } catch (e) {
    console.error('下载 PDF 失败:', e);
    alert('下载失败，请稍后重试');
  }
};

const openPDFNewTab = () => {
  if (!attachmentContent.value || !attachmentContent.value.content) return;
  
  try {
    const base64Content = attachmentContent.value.content;
    const binaryString = atob(base64Content);
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }
    const blob = new Blob([bytes], { type: 'application/pdf' });
    const url = URL.createObjectURL(blob);
    
    window.open(url, '_blank');
    
    // 延迟释放 URL
    setTimeout(() => URL.revokeObjectURL(url), 60000);
  } catch (e) {
    console.error('打开 PDF 失败:', e);
    alert('打开失败，请稍后重试');
  }
};

const getRiskClass = (score) => {
  if (score >= 0.7) return 'high-risk';
  if (score >= 0.4) return 'medium-risk';
  return 'low-risk';
};

const getAttackTypeLabel = (type) => {
  const labels = {
    'traditional': '传统钓鱼',
    'llm_generated': 'LLM生成',
    'hybrid': '混合攻击',
    'benign': '正常'
  };
  return labels[type] || type;
};

const formatFeatureName = (key) => {
  const nameMap = {
    // 后端实际返回的字段名映射
    'num_urls': 'URL数量',
    'keyword_hit_count': '可疑关键词数',
    'brand_hit_count': '品牌关键词数',
    'has_html': 'HTML内容',
    'has_script_or_form': '脚本/表单',
    'has_attachment_hint': '附件提示',
    'high_risk_url_count': '高风险URL数',
    'anchor_mismatch_count': '链接文本不匹配',
    'subject_len': '主题长度',
    'num_chars': '字符总数',
    'num_lines': '行数',
    'sender_domain': '发件人域名',
    'spf_result': 'SPF验证',
    'dkim_result': 'DKIM验证',
    'dmarc_result': 'DMARC验证',
    // 钓鱼模式特征
    'has_ip_url': 'IP地址URL',
    'has_suspicious_tld': '可疑顶级域名',
    'has_url_shortener': '短链接',
    'unique_domains': '唯一域名数',
  };
  return nameMap[key] || key;
};

const formatFeatureValue = (value) => {
  if (typeof value === 'boolean') {
    return value ? '是' : '否';
  }
  if (typeof value === 'number') {
    return value;
  }
  return value;
};

const getDisplayFeatures = (features) => {
  if (!features) return {};
  
  // 使用后端实际返回的字段名
  const importantKeys = [
    'num_urls',
    'keyword_hit_count',
    'brand_hit_count',
    'has_html',
    'has_script_or_form',
    'has_attachment_hint',
    'high_risk_url_count',
    'anchor_mismatch_count',
    'subject_len',
    'num_chars',
    'num_lines',
    'sender_domain',
    'spf_result',
    'dkim_result',
    'dmarc_result',
  ];
  
  const filtered = {};
  for (const key of importantKeys) {
    if (features[key] !== undefined && features[key] !== null) {
      filtered[key] = features[key];
    }
  }
  
  // 添加钓鱼模式特征
  if (features.phishing_patterns) {
    const patterns = features.phishing_patterns;
    if (patterns.has_ip_url !== undefined) filtered['has_ip_url'] = patterns.has_ip_url;
    if (patterns.has_suspicious_tld !== undefined) filtered['has_suspicious_tld'] = patterns.has_suspicious_tld;
    if (patterns.has_url_shortener !== undefined) filtered['has_url_shortener'] = patterns.has_url_shortener;
    if (patterns.unique_domains !== undefined) filtered['unique_domains'] = patterns.unique_domains;
  }
  
  return filtered;
};

onMounted(loadResult);
</script>

<style scoped>
.result-container {
  max-width: 1600px;
  margin: 0 auto;
  padding: 2rem;
}

/* 优化滚动条样式 */
* {
  scrollbar-width: thin;
  scrollbar-color: rgba(59, 130, 246, 0.5) rgba(255, 255, 255, 0.05);
}

*::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

*::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
}

*::-webkit-scrollbar-thumb {
  background: rgba(59, 130, 246, 0.5);
  border-radius: 4px;
}

*::-webkit-scrollbar-thumb:hover {
  background: rgba(59, 130, 246, 0.7);
}

.result-header {
  margin-bottom: 2rem;
}

.result-header h2 {
  margin: 0 0 1rem 0;
  font-size: 2rem;
  color: var(--text-primary);
}

.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: rgba(15, 23, 42, 0.4);
  border-radius: 10px;
}

.email-id {
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.email-id code {
  background: rgba(59, 130, 246, 0.2);
  padding: 0.25rem 0.5rem;
  border-radius: 6px;
  color: var(--primary);
  font-family: monospace;
}

.refresh-btn {
  padding: 0.5rem 1rem;
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 8px;
  color: var(--primary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.refresh-btn:hover:not(:disabled) {
  background: rgba(59, 130, 246, 0.2);
}

.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.result-layout {
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  gap: 2rem;
  align-items: start;
  transition: all 0.3s ease;
}

.left-panel {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.left-panel .card {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.right-panel {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  position: sticky;
  top: 2rem;
  align-self: start;
}

.card {
  background: rgba(15, 23, 42, 0.4);
  border-radius: 12px;
  border: 1px solid var(--border);
  padding: 1.5rem;
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
  will-change: transform;
}

.card h3 {
  margin: 0 0 1rem 0;
  font-size: 1.1rem;
  color: var(--text-primary);
  font-weight: 600;
}

.card h4 {
  margin: 0 0 0.75rem 0;
  font-size: 0.95rem;
  color: var(--text-secondary);
  font-weight: 500;
}

/* 邮件预览 */
.email-preview {
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
  min-height: 0;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.preview-header h3 {
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.attachment-badge {
  padding: 0.4rem 0.75rem;
  background: rgba(59, 130, 246, 0.2);
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--primary);
}

.view-toggle {
  display: flex;
  gap: 0.5rem;
  background: rgba(0, 0, 0, 0.2);
  padding: 0.25rem;
  border-radius: 8px;
}

.toggle-btn {
  padding: 0.5rem 1rem;
  background: transparent;
  border: none;
  border-radius: 6px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  font-size: 0.85rem;
  font-weight: 500;
  position: relative;
  overflow: hidden;
}

.toggle-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--primary);
  opacity: 0;
  transition: opacity 0.3s ease;
  z-index: -1;
}

.toggle-btn:hover {
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-primary);
  transform: translateY(-1px);
}

.toggle-btn.active {
  background: var(--primary);
  color: white;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.toggle-btn.active::before {
  opacity: 1;
}

/* 附件视图 */
.attachments-view {
  width: 100%;
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
  box-sizing: border-box;
  padding: 0; /* 确保没有额外 padding */
  margin: 0; /* 确保没有额外 margin */
}

.attachments-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1rem;
  /* 不添加 padding，使用父容器 .email-content 的 padding */
  width: 100%;
  box-sizing: border-box;
}

.attachment-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1.5rem;
  background: rgba(15, 23, 42, 0.6);
  border: 2px solid rgba(59, 130, 246, 0.2);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.attachment-card:hover {
  background: rgba(15, 23, 42, 0.8);
  border-color: rgba(59, 130, 246, 0.5);
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(59, 130, 246, 0.2);
}

.attachment-card:hover .attachment-preview-hint {
  opacity: 1;
  transform: translateY(0);
}

.attachment-icon-large {
  font-size: 3.5rem;
  margin-bottom: 1rem;
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.3));
}

.attachment-info {
  text-align: center;
  width: 100%;
}

.attachment-name-large {
  font-size: 0.95rem;
  color: var(--text-primary);
  font-weight: 600;
  margin-bottom: 0.5rem;
  word-wrap: break-word;
  line-height: 1.4;
  max-height: 2.8em;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.attachment-meta-large {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.attachment-separator {
  opacity: 0.5;
}

.attachment-size {
  font-weight: 600;
  color: var(--primary);
}

.attachment-type {
  font-weight: 500;
  opacity: 0.8;
}

.attachment-preview-hint {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 0.5rem;
  background: linear-gradient(to top, rgba(59, 130, 246, 0.9), transparent);
  color: white;
  font-size: 0.8rem;
  font-weight: 600;
  text-align: center;
  opacity: 0;
  transform: translateY(10px);
  transition: all 0.3s ease;
}

.email-content {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  padding: 1rem;
  min-height: 0;
  position: relative;
}

/* 视图切换过渡动画 */
.fade-enter-active {
  transition: opacity 0.25s ease 0.1s, transform 0.25s ease 0.1s;
}

.fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.fade-enter-from {
  opacity: 0;
  transform: translateX(20px) scale(0.98);
}

.fade-leave-to {
  opacity: 0;
  transform: translateX(-20px) scale(0.98);
}

.fade-enter-to,
.fade-leave-from {
  opacity: 1;
  transform: translateX(0) scale(1);
}

/* 确保过渡期间内容不会溢出 */
.email-content > * {
  width: 100%;
  height: 100%;
  box-sizing: border-box; /* 确保 padding 不影响宽度 */
}

.email-content pre {
  margin: 0;
  padding: 0; /* 移除默认 padding */
  font-family: 'Courier New', monospace;
  font-size: 0.85rem;
  line-height: 1.6;
  color: var(--text-secondary);
  white-space: pre-wrap;
  word-wrap: break-word;
  width: 100%;
  height: 100%;
  box-sizing: border-box;
}

.rendered-content {
  font-size: 0.9rem;
  line-height: 1.6;
  color: #cbd5e1;
  background: transparent !important;
  overflow-x: auto;
  width: 100%;
  height: 100%;
  box-sizing: border-box;
  padding: 0; /* 确保没有额外 padding */
  margin: 0; /* 确保没有额外 margin */
}

/* 只设置必要的布局约束，不修改颜色 */
.rendered-content :deep(*) {
  max-width: 100%;
}

.rendered-content :deep(img) {
  max-width: 100%;
  height: auto;
  display: block;
}

.rendered-content :deep(body),
.rendered-content :deep(html) {
  background: transparent !important;
  background-color: transparent !important;
}

/* 保持 HTML 邮件的原始样式，最小干预 */
/* 只确保容器本身是透明的 */
.rendered-content :deep(body),
.rendered-content :deep(html) {
  background: transparent !important;
  background-color: transparent !important;
}

/* 特征分析 */
.features-analysis {
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  min-height: 0;
}

.feature-section {
  margin-bottom: 1.5rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.feature-section:last-child {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.5rem;
}

.feature-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.6rem 0.75rem;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.05);
  transition: all 0.2s ease;
}

.feature-item:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(59, 130, 246, 0.3);
}

.feature-item .label {
  color: var(--text-secondary);
  font-size: 0.85rem;
}

.feature-item .value {
  color: var(--text-primary);
  font-weight: 500;
  font-size: 0.9rem;
}

.semantic-summary {
  margin-top: 0.75rem;
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
}

.semantic-summary p {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.6;
  font-size: 0.9rem;
}

/* LLM 分析内容 */
.llm-analysis-content {
  margin-top: 0.5rem;
}

.llm-provider-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  background: rgba(59, 130, 246, 0.1);
  border-radius: 8px;
  margin-bottom: 0.75rem;
}

.provider-label {
  color: var(--text-secondary);
  font-size: 0.85rem;
}

.provider-value {
  color: var(--primary);
  font-weight: 500;
  font-size: 0.9rem;
}

.llm-reasoning-box {
  padding: 1rem;
  background: rgba(59, 130, 246, 0.05);
  border-radius: 8px;
  border-left: 3px solid var(--primary);
}

.llm-reasoning-box h5 {
  margin: 0 0 0.5rem 0;
  font-size: 0.9rem;
  color: var(--primary);
  font-weight: 600;
}

.llm-reasoning-box p {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.8;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-size: 0.9rem;
}

.no-features {
  padding: 1rem;
  text-align: center;
  color: var(--text-secondary);
  font-style: italic;
  opacity: 0.7;
}

.no-features p {
  margin: 0;
}

/* 风险评分卡片 */
.risk-card {
  border: 2px solid;
  transition: all 0.3s ease;
}

.risk-card.high-risk {
  background: rgba(239, 68, 68, 0.1);
  border-color: rgba(239, 68, 68, 0.3);
}

.risk-card.medium-risk {
  background: rgba(245, 158, 11, 0.1);
  border-color: rgba(245, 158, 11, 0.3);
}

.risk-card.low-risk {
  background: rgba(16, 185, 129, 0.1);
  border-color: rgba(16, 185, 129, 0.3);
}

.risk-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.status-badge {
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: 600;
}

.status-badge.phishing {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.status-badge.benign {
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
}

.risk-score {
  display: flex;
  align-items: baseline;
  justify-content: center;
  margin-bottom: 1.5rem;
}

.risk-score-value {
  font-size: 8rem;
  font-weight: 700;
  line-height: 1;
  background: linear-gradient(135deg, var(--primary), var(--primary-dark));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.score-unit {
  font-size: 2.5rem;
  margin-left: 0.5rem;
  font-weight: 700;
  background: linear-gradient(135deg, var(--primary), var(--primary-dark));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  opacity: 0.8;
}

.risk-bar {
  width: 100%;
  height: 10px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 999px;
  overflow: hidden;
  margin-bottom: 1rem;
}

.risk-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--primary), var(--primary-dark));
  border-radius: 999px;
  transition: width 0.5s ease;
}

.attack-type {
  color: var(--text-secondary);
  font-size: 0.95rem;
}

.attack-type strong {
  color: var(--text-primary);
}

/* 模型得分 */
.scores-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.score-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
}

.score-label {
  font-size: 0.9rem;
  color: var(--text-secondary);
}

.score-value {
  font-size: 1.3rem;
  font-weight: 700;
  background: linear-gradient(135deg, var(--primary), var(--primary-dark));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* 模型使用情况 */
.status-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  opacity: 0.5;
  transition: all 0.3s ease;
}

.status-item.active {
  opacity: 1;
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.3);
}

.status-icon {
  font-size: 1.1rem;
}

.status-label {
  font-size: 0.9rem;
  color: var(--text-secondary);
}

.status-item.active .status-label {
  color: var(--text-primary);
  font-weight: 500;
}

/* 检测原因 */
.reasons-list {
  margin: 0;
  padding-left: 1.5rem;
}

.reasons-list li {
  margin-bottom: 0.5rem;
  color: var(--text-secondary);
  line-height: 1.6;
}



/* 附件预览模态框 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.modal-content {
  background: rgba(15, 23, 42, 0.95);
  border: 2px solid rgba(59, 130, 246, 0.3);
  border-radius: 16px;
  max-width: 900px;
  width: 90%;
  max-height: 85vh;
  overflow: hidden;
  animation: slideUp 0.3s ease;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

@keyframes slideUp {
  from {
    transform: translateY(30px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.modal-header h3 {
  margin: 0;
  font-size: 1.3rem;
  color: var(--text-primary);
}

.modal-close {
  width: 32px;
  height: 32px;
  border: none;
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-secondary);
  border-radius: 8px;
  cursor: pointer;
  font-size: 1.2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.modal-close:hover {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.modal-body {
  padding: 2rem;
  overflow-y: auto;
  max-height: calc(85vh - 80px);
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  gap: 1rem;
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid rgba(59, 130, 246, 0.2);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading-state p {
  color: var(--text-secondary);
  font-size: 0.95rem;
  margin: 0;
}

.attachment-preview-icon {
  font-size: 5rem;
  text-align: center;
  margin-bottom: 2rem;
  filter: drop-shadow(0 4px 12px rgba(0, 0, 0, 0.3));
}

.attachment-preview-info {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 2rem;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.info-label {
  font-size: 0.9rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.info-value {
  font-size: 0.95rem;
  color: var(--text-primary);
  font-weight: 600;
  text-align: right;
  max-width: 60%;
  word-wrap: break-word;
}

/* 附件预览区域 */
.attachment-preview-area {
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.attachment-preview-area h4 {
  margin: 0 0 1rem 0;
  font-size: 1rem;
  color: var(--text-primary);
  font-weight: 600;
}

.image-preview {
  background: rgba(0, 0, 0, 0.3);
  border-radius: 12px;
  padding: 1rem;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
  max-height: 500px;
  overflow: auto;
}

.image-preview img {
  max-width: 100%;
  max-height: 450px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.text-preview {
  background: rgba(0, 0, 0, 0.3);
  border-radius: 12px;
  padding: 1.5rem;
  max-height: 400px;
  overflow: auto;
}

.text-preview pre {
  margin: 0;
  font-family: 'Courier New', monospace;
  font-size: 0.85rem;
  line-height: 1.6;
  color: var(--text-secondary);
  white-space: pre-wrap;
  word-wrap: break-word;
}

.pdf-preview {
  background: rgba(0, 0, 0, 0.3);
  border-radius: 12px;
  overflow: hidden;
  height: 500px;
}

.pdf-viewer-container {
  position: relative;
  width: 100%;
  height: 100%;
}

.pdf-preview iframe {
  width: 100%;
  height: 100%;
  border: none;
  border-radius: 12px;
}

.pdf-error-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(15, 23, 42, 0.95);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  z-index: 10;
}

.error-content {
  text-align: center;
  padding: 2rem;
  max-width: 400px;
}

.error-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.error-content h4 {
  margin: 0 0 0.5rem 0;
  color: var(--text-primary);
  font-size: 1.2rem;
}

.error-content p {
  margin: 0 0 1.5rem 0;
  color: var(--text-secondary);
  font-size: 0.9rem;
  line-height: 1.6;
}

.download-btn,
.open-btn {
  display: block;
  width: 100%;
  padding: 0.75rem 1.5rem;
  margin: 0.5rem 0;
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 8px;
  color: var(--primary);
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.download-btn:hover,
.open-btn:hover {
  background: rgba(59, 130, 246, 0.2);
  border-color: rgba(59, 130, 246, 0.5);
  transform: translateY(-2px);
}

.download-btn:active,
.open-btn:active {
  transform: translateY(0);
}

.preview-notice {
  display: flex;
  gap: 1rem;
  padding: 1.5rem;
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 12px;
  margin-top: 1.5rem;
}

.preview-notice.warning {
  background: rgba(245, 158, 11, 0.1);
  border-color: rgba(245, 158, 11, 0.3);
}

.preview-notice.warning .notice-text strong {
  color: #f59e0b;
}

.notice-icon {
  font-size: 2rem;
  flex-shrink: 0;
}

.notice-text {
  flex: 1;
}

.notice-text strong {
  display: block;
  color: var(--primary);
  font-size: 1rem;
  margin-bottom: 0.5rem;
}

.notice-text p {
  margin: 0.5rem 0 0 0;
  color: var(--text-secondary);
  font-size: 0.9rem;
  line-height: 1.6;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .result-layout {
    grid-template-columns: 1fr;
  }
  
  .attachments-grid {
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  }
}

@media (max-width: 768px) {
  .modal-content {
    width: 95%;
    max-height: 90vh;
  }
  
  .attachments-grid {
    grid-template-columns: 1fr;
  }
}
</style>
