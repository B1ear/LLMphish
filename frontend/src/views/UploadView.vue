<template>
  <div class="card">
    <h2>📧 邮件上传</h2>
    <p class="subtitle">上传待检测的钓鱼嫌疑邮件，支持 EML / 文本格式。系统将自动提取特征并进行检测。</p>
    
    <div class="upload-area" :class="{ 'drag-over': dragOver, 'has-file': file }" 
         @drop.prevent="handleDrop" 
         @dragover.prevent="dragOver = true"
         @dragleave.prevent="dragOver = false">
      <input 
        type="file" 
        id="file-input"
        @change="onFileChange" 
        accept=".eml,.txt,.email"
        style="display: none"
      />
      <label for="file-input" class="upload-label">
        <div class="upload-icon">📎</div>
        <div v-if="!file" class="upload-text">
          <p class="upload-title">点击选择文件或拖拽文件到此处</p>
          <p class="upload-hint">支持 .eml, .txt, .email 格式</p>
        </div>
        <div v-else class="file-info">
          <div class="file-name">📄 {{ file.name }}</div>
          <div class="file-size">{{ formatFileSize(file.size) }}</div>
        </div>
      </label>
    </div>

    <button :disabled="!file || loading" @click="upload" class="upload-btn">
      <span v-if="loading" class="loading"></span>
      {{ loading ? "上传中..." : "🚀 上传并提取特征" }}
    </button>

    <div v-if="message" :class="['hint', message.includes('成功') ? 'success' : message.includes('失败') ? 'error' : '']">
      {{ message }}
    </div>

    <div v-if="emailId" class="next-steps">
      <p>✅ 邮件已上传成功！</p>
      <button @click="startDetection" :disabled="detecting" class="detect-btn">
        <span v-if="detecting" class="loading"></span>
        {{ detecting ? "检测中..." : "🤖 开始检测" }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import axios from "axios";

const router = useRouter();
const file = ref(null);
const loading = ref(false);
const detecting = ref(false);
const message = ref("");
const emailId = ref("");
const dragOver = ref(false);

const onFileChange = (e) => {
  const files = e.target.files;
  file.value = files && files[0] ? files[0] : null;
  dragOver.value = false;
};

const handleDrop = (e) => {
  dragOver.value = false;
  const files = e.dataTransfer.files;
  if (files && files.length > 0) {
    file.value = files[0];
  }
};

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
};

const upload = async () => {
  if (!file.value) return;
  loading.value = true;
  message.value = "";
  try {
    const formData = new FormData();
    formData.append("file", file.value);
    const res = await axios.post("/api/upload/", formData, {
      headers: { "Content-Type": "multipart/form-data" }
    });
    message.value = res.data.message || "上传成功";
    emailId.value = res.data.email_id;
  } catch (err) {
    console.error(err);
    message.value = "上传失败，请检查后端服务是否启动。";
  } finally {
    loading.value = false;
  }
};

const startDetection = async () => {
  if (!emailId.value) return;
  detecting.value = true;
  message.value = "";
  try {
    console.log('开始检测，email_id:', emailId.value);
    const res = await axios.post(`/api/detection/${emailId.value}`);
    console.log('检测完成，结果:', res.data);
    message.value = "✅ 检测完成！正在跳转...";
    
    // 等待一小段时间确保数据已保存
    setTimeout(() => {
      router.push(`/results/${emailId.value}`);
    }, 500);
  } catch (err) {
    console.error('检测失败:', err);
    console.error('错误详情:', err.response?.data);
    message.value = `检测失败: ${err.response?.data?.detail || err.message}`;
    detecting.value = false;
  }
};
</script>

<style scoped>
.upload-area {
  margin: 2rem 0;
  padding: 3rem 2rem;
  border: 2px dashed var(--border);
  border-radius: 16px;
  background: rgba(15, 23, 42, 0.4);
  transition: all 0.3s ease;
  cursor: pointer;
}

.upload-area:hover {
  border-color: var(--primary);
  background: rgba(59, 130, 246, 0.05);
}

.upload-area.drag-over {
  border-color: var(--primary);
  background: rgba(59, 130, 246, 0.1);
  transform: scale(1.02);
}

.upload-area.has-file {
  border-color: var(--success);
  background: rgba(16, 185, 129, 0.05);
}

.upload-label {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.upload-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.upload-text {
  text-align: center;
}

.upload-title {
  font-size: 1.1rem;
  font-weight: 500;
  color: var(--text-primary);
  margin: 0 0 0.5rem 0;
}

.upload-hint {
  font-size: 0.9rem;
  color: var(--text-secondary);
  margin: 0;
}

.file-info {
  text-align: center;
}

.file-name {
  font-size: 1rem;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 0.5rem;
}

.file-size {
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.upload-btn {
  width: 100%;
  margin-top: 1.5rem;
}

.action-buttons {
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
}

.action-btn {
  flex: 1;
  padding: 0.75rem 1.5rem;
  border-radius: 10px;
  text-align: center;
  font-weight: 500;
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.3);
  color: var(--primary);
  transition: all 0.2s ease;
}

.action-btn:hover {
  background: rgba(59, 130, 246, 0.2);
  transform: translateY(-2px);
}

.action-btn.primary {
  background: linear-gradient(135deg, var(--primary), var(--primary-dark));
  color: white;
  border: none;
}

.action-btn.primary:hover {
  box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
}

.detect-btn {
  width: 100%;
  margin-top: 1rem;
  padding: 1rem 2rem;
  font-size: 1.1rem;
  font-weight: 600;
  background: linear-gradient(135deg, var(--primary), var(--primary-dark));
  color: white;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.detect-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(59, 130, 246, 0.4);
}

.detect-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>


