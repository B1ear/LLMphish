<template>
  <div class="card">
    <h2>🤖 恶意检测</h2>
    <p class="subtitle">对目标邮件执行智能钓鱼检测，融合规则检测、机器学习模型与 LLM 辅助分析。</p>
    
    <div class="detection-header">
      <span class="email-id">Email ID: <code>{{ emailId }}</code></span>
      <button @click="detect" :disabled="loading" class="detect-btn">
        <span v-if="loading" class="loading"></span>
        {{ loading ? "检测中..." : "🚀 开始检测" }}
      </button>
    </div>

    <div v-if="resultData" class="detection-result">
      <!-- 检测结果卡片 -->
      <div class="result-card" :class="resultData.is_phishing ? 'phishing' : 'benign'">
        <div class="result-header">
          <h3>检测结果</h3>
          <span class="status-badge" :class="resultData.is_phishing ? 'phishing' : 'benign'">
            {{ resultData.is_phishing ? '⚠️ 钓鱼邮件' : '✅ 正常邮件' }}
          </span>
        </div>
        
        <div class="result-content">
          <div class="result-item">
            <span class="result-label">风险评分</span>
            <span class="result-value">{{ (resultData.risk_score * 100).toFixed(1) }}%</span>
          </div>
          <div class="result-item">
            <span class="result-label">攻击类型</span>
            <span class="result-value">{{ getAttackTypeLabel(resultData.attack_type) }}</span>
          </div>
        </div>

        <!-- 模型得分 -->
        <div class="model-scores">
          <h4>模型得分</h4>
          <div class="scores-list">
            <div class="score-row" v-if="resultData.rule_score !== undefined">
              <span>规则检测</span>
              <span class="score">{{ (resultData.rule_score * 100).toFixed(1) }}%</span>
            </div>
            <div class="score-row" v-if="resultData.iforest_score !== undefined">
              <span>IsolationForest</span>
              <span class="score">{{ (resultData.iforest_score * 100).toFixed(1) }}%</span>
            </div>
            <div class="score-row" v-if="resultData.llm_semantic_score !== undefined && resultData.llm_semantic_score !== null">
              <span>LLM 语义特征</span>
              <span class="score">{{ (resultData.llm_semantic_score * 100).toFixed(1) }}%</span>
            </div>
            <div class="score-row" v-if="resultData.llm_detection_score !== undefined && resultData.llm_detection_score !== null">
              <span>LLM 检测</span>
              <span class="score">{{ (resultData.llm_detection_score * 100).toFixed(1) }}%</span>
            </div>
          </div>
        </div>

        <!-- 检测原因 -->
        <div v-if="resultData.reasons && resultData.reasons.length > 0" class="reasons-box">
          <h4>检测原因</h4>
          <ul>
            <li v-for="(reason, idx) in resultData.reasons" :key="idx">{{ reason }}</li>
          </ul>
        </div>
      </div>

      <!-- 详细信息 -->
      <div class="details-toggle">
        <button @click="showDetails = !showDetails" class="toggle-btn">
          {{ showDetails ? '▼' : '▶' }} 查看详细信息
        </button>
        <pre v-if="showDetails" class="code-block">{{ JSON.stringify(resultData, null, 2) }}</pre>
      </div>
    </div>

    <div v-else-if="!loading" class="hint">
      点击"开始检测"按钮执行检测分析
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useRoute } from "vue-router";
import axios from "axios";

const route = useRoute();
const emailId = route.params.emailId;
const loading = ref(false);
const resultData = ref(null);
const showDetails = ref(false);

const getAttackTypeLabel = (type) => {
  const labels = {
    'traditional': '传统钓鱼',
    'llm_generated': 'LLM生成',
    'hybrid': '混合攻击',
    'benign': '正常'
  };
  return labels[type] || type;
};

const detect = async () => {
  loading.value = true;
  resultData.value = null;
  try {
    const res = await axios.post(`/api/detection/${emailId}`);
    resultData.value = res.data;
  } catch (e) {
    resultData.value = { error: "检测失败，请确认后端运行正常。" };
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.detection-header {
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

.detect-btn {
  margin-top: 0;
}

.detection-result {
  margin-top: 2rem;
}

.result-card {
  padding: 2rem;
  border-radius: 16px;
  border: 2px solid;
  margin-bottom: 1.5rem;
}

.result-card.phishing {
  background: rgba(239, 68, 68, 0.1);
  border-color: rgba(239, 68, 68, 0.3);
}

.result-card.benign {
  background: rgba(16, 185, 129, 0.1);
  border-color: rgba(16, 185, 129, 0.3);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.result-header h3 {
  margin: 0;
  font-size: 1.3rem;
}

.result-content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

.result-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.result-label {
  font-size: 0.9rem;
  color: var(--text-secondary);
}

.result-value {
  font-size: 1.8rem;
  font-weight: 700;
  color: var(--text-primary);
}

.model-scores {
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--border);
}

.model-scores h4 {
  margin: 0 0 1rem 0;
  font-size: 1rem;
  color: var(--text-secondary);
}

.scores-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.score-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background: rgba(15, 23, 42, 0.4);
  border-radius: 8px;
  font-size: 0.9rem;
}

.score-row .score {
  font-weight: 600;
  color: var(--primary);
}

.reasons-box {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--border);
}

.reasons-box h4 {
  margin: 0 0 1rem 0;
  font-size: 1rem;
  color: var(--text-secondary);
}

.reasons-box ul {
  margin: 0;
  padding-left: 1.5rem;
}

.reasons-box li {
  margin-bottom: 0.5rem;
  color: var(--text-secondary);
  line-height: 1.6;
}

.details-toggle {
  margin-top: 1.5rem;
}

.toggle-btn {
  width: 100%;
  margin-top: 0;
  background: rgba(59, 130, 246, 0.1);
  color: var(--primary);
  border: 1px solid rgba(59, 130, 246, 0.3);
}

.toggle-btn:hover {
  background: rgba(59, 130, 246, 0.2);
}
</style>


