<template>
  <div class="card">
    <h1>系统概览</h1>
    <p class="subtitle">
      基于机器学习和大语言模型的智能钓鱼邮件检测系统，融合多种检测方法，提供高准确率的邮件安全分析。
    </p>
    
    <div class="features-grid">
      <div class="feature-card">
        <div class="feature-icon">📧</div>
        <h3>邮件上传</h3>
        <p>支持 EML / 文本格式邮件上传，自动解析邮件内容与元数据</p>
        <router-link to="/upload" class="feature-link">开始上传 →</router-link>
      </div>
      
      <div class="feature-card">
        <div class="feature-icon">🔍</div>
        <h3>特征提取</h3>
        <p>35 维可提取特征：文本分析（主题、发件人、正文）+ URL 基础特征</p>
      </div>
      
      <div class="feature-card">
        <div class="feature-icon">🤖</div>
        <h3>多模型融合</h3>
        <p>机器学习模型 + 异常检测 + 规则检测 + LLM 语义分析</p>
      </div>
      
      <div class="feature-card">
        <div class="feature-icon">📊</div>
        <h3>结果展示</h3>
        <p>风险评分、攻击类型分类与可解释性信息展示</p>
      </div>
    </div>

    <div class="stats-section">
      <h2>检测能力</h2>
      <div class="stats-grid">
        <div class="stat-item">
          <div class="stat-value">96%</div>
          <div class="stat-label">模型准确率</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">35</div>
          <div class="stat-label">特征维度</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">4</div>
          <div class="stat-label">检测方法</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">3+</div>
          <div class="stat-label">模型数量</div>
        </div>
      </div>
      
      
    </div>
  </div>
</template>

<script setup>
</script>

<style scoped>
.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1.5rem;
  margin: 2rem 0;
}

.feature-card {
  background: rgba(15, 23, 42, 0.4);
  border-radius: 16px;
  padding: 1.5rem;
  border: 1px solid var(--border);
  transition: all 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-4px);
  border-color: rgba(59, 130, 246, 0.4);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}

.feature-icon {
  font-size: 2.5rem;
  margin-bottom: 0.75rem;
}

.feature-card h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1.1rem;
  color: var(--text-primary);
}

.feature-card p {
  margin: 0 0 1rem 0;
  color: var(--text-secondary);
  font-size: 0.9rem;
  line-height: 1.5;
}

.feature-link {
  color: var(--primary);
  font-weight: 500;
  font-size: 0.9rem;
  display: inline-block;
  transition: all 0.2s ease;
}

.feature-link:hover {
  color: #60a5fa;
  transform: translateX(4px);
}

.stats-section {
  margin-top: 3rem;
  padding-top: 2rem;
  border-top: 1px solid var(--border);
}

.stats-section h2 {
  margin-bottom: 1.5rem;
  font-size: 1.5rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1.5rem;
}

.stat-item {
  text-align: center;
  padding: 1.5rem;
  background: rgba(59, 130, 246, 0.1);
  border-radius: 12px;
  border: 1px solid rgba(59, 130, 246, 0.2);
}

.stat-value {
  font-size: 2.5rem;
  font-weight: 700;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 0.5rem;
}

.stat-label {
  color: var(--text-secondary);
  font-size: 0.9rem;
  font-weight: 500;
}

.model-info {
  margin-top: 2rem;
  padding: 1.5rem;
  background: rgba(16, 185, 129, 0.1);
  border-radius: 12px;
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.model-info h3 {
  margin: 0 0 1rem 0;
  font-size: 1.2rem;
  color: var(--text-primary);
}

.model-details {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.model-detail-item {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
  font-size: 0.9rem;
}

.detail-label {
  color: var(--text-secondary);
  font-weight: 600;
  min-width: 100px;
}

.detail-value {
  color: var(--text-primary);
  flex: 1;
}
</style>


