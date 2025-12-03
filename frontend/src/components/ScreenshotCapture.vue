<template>
  <div class="screenshot-capture">
    <h3>📸 URL 网页截图功能</h3>
    <p class="subtitle">从邮件中提取 URL，使用无头浏览器访问网页并自动截图（用于图像特征提取）</p>
    
    <div v-if="urls.length > 0" class="urls-list">
      <p>📎 邮件中找到的 URL：</p>
      <ul>
        <li v-for="(url, idx) in urls" :key="idx">
          <a :href="url" target="_blank" rel="noopener noreferrer">{{ url }}</a>
        </li>
      </ul>
    </div>
    <div v-else class="hint">
      邮件中未找到 URL，无法进行截图
    </div>
    
    <div class="actions">
      <button @click="autoCapture" :disabled="!emailId || urls.length === 0 || capturing">
        <span v-if="capturing" class="loading"></span>
        {{ capturing ? "访问 URL 并截图中..." : "🚀 自动访问 URL 并截图" }}
      </button>
      <button v-if="screenshotUrl" @click="uploadScreenshot" :disabled="uploading">
        <span v-if="uploading" class="loading"></span>
        {{ uploading ? "上传中..." : "📤 上传截图" }}
      </button>
    </div>
    
    <div v-if="screenshotUrl" class="screenshot-preview">
      <p>📷 网页截图预览：</p>
      <img :src="screenshotUrl" alt="网页截图" />
    </div>
    
    <div v-if="message" :class="['hint', message.includes('成功') ? 'success' : message.includes('失败') ? 'error' : '']">
      {{ message }}
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import axios from "axios";

const props = defineProps({
  emailId: {
    type: String,
    required: true,
  },
  emailContent: {
    type: String,
    default: "",
  },
});

const urls = ref([]);
const screenshotUrl = ref("");
const screenshotBlob = ref(null);
const capturing = ref(false);
const uploading = ref(false);
const message = ref("");

// 从邮件内容中提取 URL
const extractUrls = () => {
  if (!props.emailContent) {
    urls.value = [];
    return;
  }
  
  // 简单的 URL 正则匹配
  const urlPattern = /https?:\/\/[^\s<>"']+/gi;
  const matches = props.emailContent.match(urlPattern);
  urls.value = matches ? [...new Set(matches)] : [];
};

// 自动访问 URL 并截图（后端处理）
const autoCapture = async () => {
  if (!props.emailId || urls.value.length === 0) {
    message.value = "邮件中未找到 URL";
    return;
  }

  capturing.value = true;
  message.value = "正在访问 URL 并截图...";

  try {
    const res = await axios.post(`/api/upload/screenshot/auto/${props.emailId}`);
    
    message.value = res.data.message || "截图成功";
    
    // 如果后端返回了截图数据，可以显示预览
    // 注意：这里后端返回的是成功消息，实际截图已保存
    // 如果需要预览，可以再次请求获取截图
    if (res.data.size) {
      message.value += ` (大小: ${(res.data.size / 1024).toFixed(2)} KB)`;
    }
    
    // 可以尝试获取截图用于预览（需要后端提供 GET 接口）
    // 暂时不实现，因为截图已保存到后端
    
  } catch (error) {
    console.error("自动截图失败:", error);
    message.value = "自动截图失败: " + (error.response?.data?.detail || error.message);
  } finally {
    capturing.value = false;
  }
};

const uploadScreenshot = async () => {
  // 这个功能现在主要用于手动上传截图（如果用户想自己截图）
  message.value = "请使用'自动访问 URL 并截图'功能，系统会自动处理";
};

onMounted(() => {
  extractUrls();
});
</script>

<style scoped>
.screenshot-capture {
  margin-top: 2rem;
  padding: 1.5rem;
  background: rgba(15, 23, 42, 0.4);
  border: 1px solid var(--border);
  border-radius: 12px;
}

.screenshot-capture h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1.1rem;
  color: var(--text-primary);
}

.subtitle {
  color: var(--text-secondary);
  font-size: 0.9rem;
  margin-bottom: 1.5rem;
  line-height: 1.6;
}

.urls-list {
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: rgba(15, 23, 42, 0.6);
  border-radius: 8px;
  border: 1px solid var(--border);
}

.urls-list p {
  margin: 0 0 0.75rem 0;
  font-size: 0.9rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.urls-list ul {
  margin: 0;
  padding-left: 1.5rem;
}

.urls-list li {
  margin: 0.5rem 0;
  word-break: break-all;
  line-height: 1.6;
}

.urls-list a {
  color: var(--primary);
  text-decoration: none;
  transition: all 0.2s ease;
  padding: 0.25rem 0.5rem;
  border-radius: 6px;
  display: inline-block;
}

.urls-list a:hover {
  background: rgba(59, 130, 246, 0.1);
  color: #60a5fa;
}

.actions {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

.actions button {
  flex: 1;
  min-width: 150px;
  margin-top: 0;
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, var(--primary), var(--primary-dark));
  color: white;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  transition: all 0.2s ease;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.actions button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
}

.actions button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.screenshot-preview {
  margin-top: 1.5rem;
  padding: 1rem;
  background: rgba(15, 23, 42, 0.6);
  border-radius: 8px;
  border: 1px solid var(--border);
}

.screenshot-preview p {
  margin: 0 0 0.75rem 0;
  font-size: 0.9rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.screenshot-preview img {
  max-width: 100%;
  border-radius: 8px;
  border: 1px solid var(--border);
  box-shadow: var(--shadow);
}

.hint {
  margin-top: 1rem;
  color: var(--text-secondary);
  font-size: 0.9rem;
  padding: 0.75rem 1rem;
  background: rgba(59, 130, 246, 0.1);
  border-radius: 8px;
  border-left: 3px solid var(--primary);
}

.hint.success {
  background: rgba(16, 185, 129, 0.1);
  border-left-color: var(--success);
  color: #6ee7b7;
}

.hint.error {
  background: rgba(239, 68, 68, 0.1);
  border-left-color: var(--danger);
  color: #fca5a5;
}
</style>

