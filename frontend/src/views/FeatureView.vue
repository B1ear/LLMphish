<template>
  <div class="card">
    <h2>🔍 特征提取</h2>
    <p class="subtitle">展示邮件的传统特征与基于 LLM 的语义特征，支持多模态特征提取。</p>
    
    <div class="feature-header">
      <span class="email-id">Email ID: <code>{{ emailId }}</code></span>
      <button @click="loadFeatures" :disabled="loading" class="refresh-btn">
        <span v-if="loading" class="loading"></span>
        {{ loading ? "加载中..." : "🔄 重新加载" }}
      </button>
    </div>

    <div v-if="featuresData" class="features-content">
      <!-- 传统特征 -->
      <div class="feature-section">
        <h3>📋 传统特征</h3>
        <div class="feature-grid">
          <div class="feature-item" v-if="featuresData.traditional_features">
            <span class="feature-label">字符数</span>
            <span class="feature-value">{{ featuresData.traditional_features.num_chars || 0 }}</span>
          </div>
          <div class="feature-item" v-if="featuresData.traditional_features">
            <span class="feature-label">URL数量</span>
            <span class="feature-value">{{ featuresData.traditional_features.num_urls || 0 }}</span>
          </div>
          <div class="feature-item" v-if="featuresData.traditional_features">
            <span class="feature-label">可疑关键词</span>
            <span class="feature-value">{{ featuresData.traditional_features.keyword_hit_count || 0 }}</span>
          </div>
          <div class="feature-item" v-if="featuresData.traditional_features">
            <span class="feature-label">包含HTML</span>
            <span class="feature-value">{{ featuresData.traditional_features.has_html ? '是' : '否' }}</span>
          </div>
        </div>
      </div>

      <!-- LLM语义特征 -->
      <div class="feature-section" v-if="featuresData.llm_semantic_features">
        <h3>🤖 LLM 语义特征</h3>
        <div v-if="featuresData.llm_semantic_features.llm_supported" class="llm-features">
          <div class="llm-feature-grid">
            <div class="llm-feature-item">
              <span class="llm-label">钓鱼意图得分</span>
              <div class="llm-bar">
                <div class="llm-bar-fill" :style="{ width: (featuresData.llm_semantic_features.phishing_intent_score * 100) + '%' }"></div>
                <span class="llm-value">{{ (featuresData.llm_semantic_features.phishing_intent_score * 100).toFixed(1) }}%</span>
              </div>
            </div>
            <div class="llm-feature-item">
              <span class="llm-label">紧急程度</span>
              <div class="llm-bar">
                <div class="llm-bar-fill" :style="{ width: (featuresData.llm_semantic_features.urgency_score * 100) + '%' }"></div>
                <span class="llm-value">{{ (featuresData.llm_semantic_features.urgency_score * 100).toFixed(1) }}%</span>
              </div>
            </div>
            <div class="llm-feature-item">
              <span class="llm-label">情感得分</span>
              <span class="llm-value">{{ featuresData.llm_semantic_features.sentiment_score?.toFixed(2) || '0.00' }}</span>
            </div>
            <div class="llm-feature-item" v-if="featuresData.llm_semantic_features.provider">
              <span class="llm-label">LLM 提供商</span>
              <span class="llm-value">{{ featuresData.llm_semantic_features.provider }}</span>
            </div>
          </div>
        </div>
        <div v-else class="hint">
          {{ featuresData.llm_semantic_features.note || 'LLM 特征不可用' }}
        </div>
      </div>

      <!-- 详细信息 -->
      <div class="details-toggle">
        <button @click="showDetails = !showDetails" class="toggle-btn">
          {{ showDetails ? '▼' : '▶' }} 查看完整特征数据
        </button>
        <pre v-if="showDetails" class="code-block">{{ JSON.stringify(featuresData, null, 2) }}</pre>
      </div>
    </div>

    <!-- 截图功能组件 -->
    <div class="screenshot-section">
      <ScreenshotCapture :email-id="emailId" :email-content="emailContent" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRoute } from "vue-router";
import axios from "axios";
import ScreenshotCapture from "../components/ScreenshotCapture.vue";

const route = useRoute();
const emailId = route.params.emailId;
const loading = ref(false);
const featuresData = ref(null);
const emailContent = ref("");
const showDetails = ref(false);

const loadFeatures = async () => {
  loading.value = true;
  try {
    const res = await axios.get(`/api/features/${emailId}`);
    featuresData.value = res.data;
    
    // 尝试获取邮件内容用于截图
    try {
      const emailRes = await axios.get(`/api/upload/${emailId}`);
      emailContent.value = emailRes.data.content || "";
    } catch (e) {
      console.log("无法获取邮件内容:", e);
    }
  } catch (e) {
    featuresData.value = null;
  } finally {
    loading.value = false;
  }
};

onMounted(loadFeatures);
</script>

<style scoped>
.feature-header {
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

.features-content {
  margin-top: 2rem;
}

.feature-section {
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: rgba(15, 23, 42, 0.4);
  border-radius: 12px;
  border: 1px solid var(--border);
}

.feature-section h3 {
  margin: 0 0 1.5rem 0;
  font-size: 1.2rem;
  color: var(--text-primary);
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
}

.feature-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1rem;
  background: rgba(30, 41, 59, 0.6);
  border-radius: 8px;
  border: 1px solid var(--border);
}

.feature-label {
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.feature-value {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--primary);
}

.llm-features {
  margin-top: 1rem;
}

.llm-feature-grid {
  display: grid;
  gap: 1rem;
}

.llm-feature-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.llm-label {
  font-size: 0.9rem;
  color: var(--text-secondary);
}

.llm-bar {
  display: flex;
  align-items: center;
  gap: 1rem;
  width: 100%;
}

.llm-bar-fill {
  flex: 1;
  height: 8px;
  background: linear-gradient(90deg, var(--primary), var(--primary-dark));
  border-radius: 999px;
  transition: width 0.5s ease;
}

.llm-value {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--primary);
  min-width: 50px;
  text-align: right;
}

.screenshot-section {
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 1px solid var(--border);
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


