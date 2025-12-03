<template>
  <div class="layout">
    <header class="header">
      <div class="brand">🛡️ LLMPhish 混合威胁钓鱼邮件检测系统</div>
      <nav class="nav">
        <router-link to="/">📊 概览</router-link>
        <router-link to="/upload">📧 邮件上传</router-link>
      </nav>
    </header>
    <main class="main">
      <router-view />
    </main>
    <footer class="footer">
      © {{ new Date().getFullYear() }} LLMPhish - 面向混合威胁的智能钓鱼邮件检测系统
    </footer>
  </div>
</template>

<script setup>
</script>


