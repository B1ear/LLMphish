<template>
  <div class="card">
    <h2>📊 检测结果</h2>
    <p class="subtitle">展示检测结果与风险评分，包含多模型融合结果与可解释性信息。</p>
    
    <div class="result-header">
      <span class="email-id">Email ID: <code>{{ emailId }}</code></span>
      <button @click="loadResult" :disabled="loading" class="refresh-btn">
        <span v-if="loading" class="loading"></span>
        {{ loading ? "加载中..." : "🔄 刷新结果" }}
      </button>
    </div>

    <div v-if="resultData" class="result-content">
      <!-- 风险评分卡片 -->
      <div class="risk-card" :class="getRiskClass(resultData.risk_score)">
        <div class="risk-header">
          <h3>风险评分</h3>
          <span class="status-badge" :class="resultData.is_phishing ? 'phishing' : 'benign'">
            {{ resultData.is_phishing ? '⚠️ 钓鱼邮件' : '✅ 正常邮件' }}
          </span>
        </div>
        <div class="risk-score">
          <span class="score-value">{{ (resultData.risk_score * 100).toFixed(1) }}</span>
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
      <div class="scores-grid">
        <div class="score-item" v-if="resultData.rule_score !== undefined">
          <div class="score-label">📋 规则检测</div>
          <div class="score-value-small">{{ (resultData.rule_score * 100).toFixed(1) }}%</div>
        </div>
        <div class="score-item" v-if="resultData.iforest_score !== undefined && resultData.iforest_score !== null">
          <div class="score-label">🌲 IsolationForest</div>
          <div class="score-value-small">{{ (resultData.iforest_score * 100).toFixed(1) }}%</div>
        </div>
        <div class="score-item" v-if="resultData.phishmmf_rf_score !== undefined && resultData.phishmmf_rf_score !== null">
          <div class="score-label">🎯 PhishMMF-RF</div>
          <div class="score-value-small">{{ (resultData.phishmmf_rf_score * 100).toFixed(1) }}%</div>
        </div>
        <div class="score-item" v-if="resultData.phishmmf_xgb_score !== undefined && resultData.phishmmf_xgb_score !== null">
          <div class="score-label">⚡ PhishMMF-XGB</div>
          <div class="score-value-small">{{ (resultData.phishmmf_xgb_score * 100).toFixed(1) }}%</div>
        </div>
        <div class="score-item" v-if="resultData.llm_semantic_score !== undefined && resultData.llm_semantic_score !== null">
          <div class="score-label">🧠 LLM 语义</div>
          <div class="score-value-small">{{ (resultData.llm_semantic_score * 100).toFixed(1) }}%</div>
        </div>
        <div class="score-item" v-if="resultData.llm_detection_score !== undefined && resultData.llm_detection_score !== null">
          <div class="score-label">🤖 LLM 检测</div>
          <div class="score-value-small">{{ (resultData.llm_detection_score * 100).toFixed(1) }}%</div>
        </div>
      </div>

      <!-- 模型使用情况 -->
      <div v-if="resultData.models_used" class="models-status">
        <h3>模型使用情况</h3>
        <div class="status-grid">
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
      <div v-if="resultData.reasons && resultData.reasons.length > 0" class="reasons-section">
        <h3>检测原因</h3>
        <ul class="reasons-list">
          <li v-for="(reason, idx) in resultData.reasons" :key="idx">{{ reason }}</li>
        </ul>
      </div>

      <!-- LLM 分析详情 -->
      <div v-if="resultData.llm_detection && resultData.llm_detection.llm_supported" class="llm-analysis-section">
        <h3>🤖 LLM 智能分析</h3>
        <div class="llm-content">
          <div class="llm-provider">
            <span class="label">使用模型:</span>
            <span class="value">{{ resultData.llm_detection.provider }} - {{ resultData.llm_detection.model }}</span>
          </div>
          <div class="llm-reasoning">
            <h4>分析推理过程:</h4>
            <div class="reasoning-text">{{ resultData.llm_detection.reasoning || '无详细推理信息' }}</div>
          </div>
          <div v-if="resultData.llm_detection.confidence" class="llm-confidence">
            <span class="label">置信度:</span>
            <span class="value">{{ (resultData.llm_detection.confidence * 100).toFixed(1) }}%</span>
          </div>
        </div>
      </div>

      <!-- LLM 语义特征 -->
      <div v-if="resultData.llm_semantic_features && resultData.llm_semantic_features.llm_supported" class="llm-semantic-section">
        <h3>🧠 LLM 语义特征分析</h3>
        <div class="semantic-grid">
          <div class="semantic-item" v-if="resultData.llm_semantic_features.phishing_intent_score !== undefined">
            <span class="label">钓鱼意图得分:</span>
            <span class="value">{{ (resultData.llm_semantic_features.phishing_intent_score * 100).toFixed(1) }}%</span>
          </div>
          <div class="semantic-item" v-if="resultData.llm_semantic_features.urgency_level !== undefined">
            <span class="label">紧急程度:</span>
            <span class="value">{{ resultData.llm_semantic_features.urgency_level }}</span>
          </div>
          <div class="semantic-item" v-if="resultData.llm_semantic_features.emotional_manipulation !== undefined">
            <span class="label">情感操纵:</span>
            <span class="value">{{ resultData.llm_semantic_features.emotional_manipulation ? '是' : '否' }}</span>
          </div>
          <div class="semantic-item" v-if="resultData.llm_semantic_features.authority_impersonation !== undefined">
            <span class="label">权威冒充:</span>
            <span class="value">{{ resultData.llm_semantic_features.authority_impersonation ? '是' : '否' }}</span>
          </div>
        </div>
        <div v-if="resultData.llm_semantic_features.semantic_summary" class="semantic-summary">
          <h4>语义摘要:</h4>
          <p>{{ resultData.llm_semantic_features.semantic_summary }}</p>
        </div>
      </div>

      <!-- 传统特征 -->
      <div v-if="resultData.traditional_features" class="traditional-features-section">
        <h3>📊 传统特征分析</h3>
        <div class="features-grid">
          <div class="feature-item" v-for="(value, key) in getDisplayFeatures(resultData.traditional_features)" :key="key">
            <span class="label">{{ formatFeatureName(key) }}:</span>
            <span class="value">{{ formatFeatureValue(value) }}</span>
          </div>
        </div>
      </div>

      <!-- 详细信息（折叠） -->
      <div class="details-section">
        <div class="details-header" @click="showDetails = !showDetails">
          <h3>🔍 完整技术详情</h3>
          <span class="toggle-icon">{{ showDetails ? '▼' : '▶' }}</span>
        </div>
        <pre v-show="showDetails" class="code-block">{{ JSON.stringify(resultData, null, 2) }}</pre>
      </div>
    </div>

    <div v-else-if="!loading" class="hint error">
      暂无检测结果，请先执行检测。
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRoute } from "vue-router";
import axios from "axios";

const route = useRoute();
const emailId = route.params.emailId;
const loading = ref(false);
const resultData = ref(null);
const showDetails = ref(false);

const loadResult = async () => {
  loading.value = true;
  try {
    const res = await axios.get(`/api/results/${emailId}`);
    resultData.value = res.data;
  } catch (e) {
    resultData.value = null;
  } finally {
    loading.value = false;
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
    'has_suspicious_keywords': '可疑关键词',
    'has_urgent_words': '紧急词汇',
    'has_chinese_keywords': '中文钓鱼词',
    'has_base64_content': 'Base64编码',
    'has_fake_sender': '伪造发件人',
    'url_count': 'URL数量',
    'suspicious_url_count': '可疑URL数量',
    'has_ip_url': 'IP地址URL',
    'has_shortened_url': '短链接',
    'attachment_count': '附件数量',
    'has_executable': '可执行文件',
    'has_script': '脚本文件',
    'has_html_content': 'HTML内容',
    'has_form': '表单',
    'has_input_field': '输入框',
    'has_external_resource': '外部资源',
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
  // 只显示重要的特征
  const importantKeys = [
    'has_suspicious_keywords',
    'has_urgent_words',
    'has_chinese_keywords',
    'has_base64_content',
    'has_fake_sender',
    'url_count',
    'suspicious_url_count',
    'has_ip_url',
    'attachment_count',
    'has_executable',
    'has_html_content',
    'has_form',
  ];
  
  const filtered = {};
  for (const key of importantKeys) {
    if (features[key] !== undefined) {
      filtered[key] = features[key];
    }
  }
  return filtered;
};

onMounted(loadResult);
</script>

<style scoped>
.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
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
  margin-top: 0;
}

.risk-card {
  margin: 1.5rem 0;
  padding: 2rem;
  border-radius: 16px;
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
  margin-bottom: 1.5rem;
}

.risk-header h3 {
  margin: 0;
  font-size: 1.2rem;
}

.risk-score {
  display: flex;
  align-items: baseline;
  margin-bottom: 1rem;
}

.score-value {
  font-size: 4rem;
  font-weight: 700;
  line-height: 1;
}

.score-unit {
  font-size: 2rem;
  margin-left: 0.5rem;
  opacity: 0.7;
}

.risk-bar {
  width: 100%;
  height: 12px;
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
  font-size: 1.1rem;
}

.scores-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
  margin: 1.5rem 0;
}

.score-item {
  padding: 1rem;
  background: rgba(15, 23, 42, 0.4);
  border-radius: 10px;
  text-align: center;
  border: 1px solid var(--border);
}

.score-label {
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin-bottom: 0.5rem;
}

.score-value-small {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--primary);
}

.reasons-section,
.details-section {
  margin: 2rem 0;
  padding: 1.5rem;
  background: rgba(15, 23, 42, 0.4);
  border-radius: 12px;
  border: 1px solid var(--border);
}

.reasons-section h3,
.details-section h3 {
  margin: 0 0 1rem 0;
  font-size: 1.1rem;
}

.reasons-list {
  margin: 0;
  padding-left: 1.5rem;
}

.reasons-list li {
  margin-bottom: 0.5rem;
  color: var(--text-secondary);
  line-height: 1.6;
}

.models-status {
  margin: 2rem 0;
  padding: 1.5rem;
  background: rgba(15, 23, 42, 0.4);
  border-radius: 12px;
  border: 1px solid var(--border);
}

.models-status h3 {
  margin: 0 0 1rem 0;
  font-size: 1.1rem;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  opacity: 0.5;
  transition: all 0.3s ease;
}

.status-item.active {
  opacity: 1;
  background: rgba(59, 130, 246, 0.1);
  border-color: rgba(59, 130, 246, 0.3);
}

.status-icon {
  font-size: 1.2rem;
}

.status-label {
  font-size: 0.9rem;
  color: var(--text-secondary);
}

.status-item.active .status-label {
  color: var(--text-primary);
  font-weight: 500;
}

.llm-analysis-section,
.llm-semantic-section,
.traditional-features-section {
  margin: 2rem 0;
  padding: 1.5rem;
  background: rgba(15, 23, 42, 0.4);
  border-radius: 12px;
  border: 1px solid var(--border);
}

.llm-analysis-section h3,
.llm-semantic-section h3,
.traditional-features-section h3 {
  margin: 0 0 1rem 0;
  font-size: 1.1rem;
}

.llm-content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.llm-provider,
.llm-confidence {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
}

.llm-reasoning {
  padding: 1rem;
  background: rgba(59, 130, 246, 0.1);
  border-radius: 8px;
  border-left: 3px solid var(--primary);
}

.llm-reasoning h4 {
  margin: 0 0 0.75rem 0;
  font-size: 0.95rem;
  color: var(--primary);
}

.reasoning-text {
  color: var(--text-secondary);
  line-height: 1.8;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.semantic-grid,
.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.semantic-item,
.feature-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
}

.semantic-item .label,
.feature-item .label,
.llm-provider .label,
.llm-confidence .label {
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.semantic-item .value,
.feature-item .value,
.llm-provider .value,
.llm-confidence .value {
  color: var(--text-primary);
  font-weight: 500;
}

.semantic-summary {
  margin-top: 1rem;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
}

.semantic-summary h4 {
  margin: 0 0 0.5rem 0;
  font-size: 0.95rem;
  color: var(--text-secondary);
}

.semantic-summary p {
  margin: 0;
  color: var(--text-primary);
  line-height: 1.6;
}

.details-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  user-select: none;
  transition: opacity 0.2s ease;
}

.details-header:hover {
  opacity: 0.8;
}

.details-header h3 {
  margin: 0;
}

.toggle-icon {
  font-size: 1.2rem;
  color: var(--text-secondary);
  transition: transform 0.3s ease;
}
</style>


