<template>
  <div class="app-container">
    <el-container class="main-container">
      <el-header class="app-header">
        <div class="header-content">
          <div class="logo-section">
            <el-icon :size="32" color="#409EFF">
              <Guide />
            </el-icon>
            <span class="app-title">智慧城市交通监控数字孪生系统</span>
          </div>
          <div class="header-actions">
            <el-tag type="primary" effect="dark">
              <el-icon><Connection /></el-icon>
              系统运行中
            </el-tag>
            <el-tag type="success" effect="dark">
              <el-icon><Clock /></el-icon>
              {{ currentTime }}
            </el-tag>
          </div>
        </div>
      </el-header>
      
      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import dayjs from 'dayjs'

const currentTime = ref('')
let timer: number | null = null

function updateTime() {
  currentTime.value = dayjs().format('YYYY-MM-DD HH:mm:ss')
}

onMounted(() => {
  updateTime()
  timer = window.setInterval(updateTime, 1000)
})

onUnmounted(() => {
  if (timer) {
    window.clearInterval(timer)
  }
})
</script>

<style scoped>
.app-container {
  width: 100vw;
  height: 100vh;
  overflow: hidden;
}

.main-container {
  height: 100%;
}

.app-header {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  padding: 0;
  height: 60px !important;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
  padding: 0 30px;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 15px;
}

.app-title {
  font-size: 22px;
  font-weight: bold;
  color: #ffffff;
  letter-spacing: 2px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 15px;
}

.app-main {
  padding: 0;
  overflow: hidden;
  background-color: #f5f7fa;
}
</style>
