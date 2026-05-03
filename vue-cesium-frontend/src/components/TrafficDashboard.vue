<template>
  <div class="traffic-dashboard">
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon" :size="40" color="#409EFF">
              <Bus />
            </el-icon>
            <div class="stat-info">
              <div class="stat-value">{{ store.totalBuses }}</div>
              <div class="stat-label">运行公交车</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon" :size="40" color="#67C23A">
              <Location />
            </el-icon>
            <div class="stat-info">
              <div class="stat-value">{{ store.totalIntersections }}</div>
              <div class="stat-label">监控路口</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card danger">
          <div class="stat-content">
            <el-icon class="stat-icon" :size="40" color="#F56C6C">
              <Warning />
            </el-icon>
            <div class="stat-info">
              <div class="stat-value">{{ store.congestionStats.HIGH + store.congestionStats.SEVERE }}</div>
              <div class="stat-label">拥堵路口</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon" :size="40" color="#E6A23C">
              <Clock />
            </el-icon>
            <div class="stat-info">
              <div class="stat-value">{{ lastUpdateTime }}</div>
              <div class="stat-label">最后更新</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="content-row">
      <el-col :span="8">
        <el-card class="list-card">
          <template #header>
            <div class="card-header">
              <span>拥堵预警路口</span>
              <el-tag type="danger" effect="dark">
                {{ store.glowingPredictions.length }} 个
              </el-tag>
            </div>
          </template>
          
          <div v-if="store.glowingPredictions.length === 0" class="empty-state">
            <el-empty description="暂无拥堵预警" />
          </div>
          
          <div v-else class="warning-list">
            <div 
              v-for="prediction in store.glowingPredictions" 
              :key="prediction.intersection_id"
              class="warning-item"
              :class="{ selected: store.selectedIntersectionId === prediction.intersection_id }"
              @click="handleSelectIntersection(prediction.intersection_id)"
            >
              <div class="warning-header">
                <span class="warning-name">{{ prediction.intersection_name }}</span>
                <el-tag :type="getCongestionTagType(prediction.congestion_level)" effect="dark" size="small">
                  {{ getCongestionLevelText(prediction.congestion_level) }}
                </el-tag>
              </div>
              <div class="warning-detail">
                <span class="detail-item">
                  <el-icon><TrendCharts /></el-icon>
                  预测车辆: {{ prediction.predicted_bus_count }}
                </span>
                <span class="detail-item">
                  <el-icon><Speed /></el-icon>
                  速度: {{ prediction.predicted_average_speed }} km/h
                </span>
              </div>
              <el-progress 
                :percentage="Math.round(prediction.confidence * 100)" 
                :color="getProgressColor(prediction.congestion_level)"
                :stroke-width="6"
              />
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card class="list-card">
          <template #header>
            <div class="card-header">
              <span>所有路口状态</span>
            </div>
          </template>
          
          <el-table :data="store.predictionList" style="width: 100%" height="400">
            <el-table-column prop="intersection_name" label="路口名称" width="120" />
            <el-table-column label="拥堵等级" width="100">
              <template #default="{ row }">
                <el-tag :type="getCongestionTagType(row.congestion_level)" effect="dark" size="small">
                  {{ getCongestionLevelText(row.congestion_level) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="predicted_bus_count" label="预测车辆" width="80" />
            <el-table-column prop="predicted_average_speed" label="预测速度" width="100">
              <template #default="{ row }">
                {{ row.predicted_average_speed }} km/h
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card class="list-card">
          <template #header>
            <div class="card-header">
              <span>系统状态</span>
              <el-switch 
                v-model="autoRefresh" 
                active-text="自动刷新"
                @change="handleRefreshChange"
              />
            </div>
          </template>
          
          <div class="status-info">
            <div class="status-item">
              <span class="status-label">数据连接状态:</span>
              <el-tag :type="isConnected ? 'success' : 'danger'" effect="dark">
                {{ isConnected ? '已连接' : '未连接' }}
              </el-tag>
            </div>
            
            <div class="status-item">
              <span class="status-label">刷新频率:</span>
              <el-select v-model="refreshInterval" size="small" style="width: 120px;">
                <el-option label="1秒" :value="1000" />
                <el-option label="2秒" :value="2000" />
                <el-option label="5秒" :value="5000" />
              </el-select>
            </div>

            <el-divider />
            
            <div class="congestion-legend">
              <div class="legend-title">拥堵等级图例:</div>
              <div class="legend-items">
                <div class="legend-item">
                  <span class="legend-color" style="background: #00FF00;"></span>
                  <span>畅通</span>
                </div>
                <div class="legend-item">
                  <span class="legend-color" style="background: #FFFF00;"></span>
                  <span>缓行</span>
                </div>
                <div class="legend-item">
                  <span class="legend-color" style="background: #FF8C00;"></span>
                  <span>拥堵</span>
                </div>
                <div class="legend-item">
                  <span class="legend-color" style="background: #FF0000;"></span>
                  <span>严重拥堵</span>
                </div>
              </div>
            </div>

            <el-divider />
            
            <div class="action-buttons">
              <el-button type="primary" @click="handleRefresh" :loading="store.isLoading">
                手动刷新
              </el-button>
              <el-button type="warning" @click="handleSimulateData">
                模拟数据
              </el-button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useTrafficStore } from '@/stores/traffic'
import type { CongestionLevel, BusPosition, TrafficPrediction } from '@/types'
import dayjs from 'dayjs'

const store = useTrafficStore()
const autoRefresh = ref(true)
const refreshInterval = ref(1000)
const isConnected = ref(true)
const refreshTimer = ref<number | null>(null)

const lastUpdateTime = computed(() => {
  return store.lastUpdateTime || '--:--:--'
})

function getCongestionLevelText(level: CongestionLevel): string {
  const texts: Record<CongestionLevel, string> = {
    LOW: '畅通',
    MEDIUM: '缓行',
    HIGH: '拥堵',
    SEVERE: '严重拥堵'
  }
  return texts[level]
}

function getCongestionTagType(level: CongestionLevel): string {
  const types: Record<CongestionLevel, string> = {
    LOW: 'success',
    MEDIUM: 'warning',
    HIGH: 'danger',
    SEVERE: 'danger'
  }
  return types[level]
}

function getProgressColor(level: CongestionLevel): string {
  const colors: Record<CongestionLevel, string> = {
    LOW: '#67C23A',
    MEDIUM: '#E6A23C',
    HIGH: '#F56C6C',
    SEVERE: '#FF0000'
  }
  return colors[level]
}

function handleSelectIntersection(intersectionId: string) {
  store.selectIntersection(
    store.selectedIntersectionId === intersectionId ? null : intersectionId
  )
}

function handleRefreshChange(val: boolean) {
  if (val) {
    startRefreshTimer()
  } else {
    stopRefreshTimer()
  }
}

function startRefreshTimer() {
  stopRefreshTimer()
  refreshTimer.value = window.setInterval(() => {
    handleRefresh()
  }, refreshInterval.value)
}

function stopRefreshTimer() {
  if (refreshTimer.value) {
    window.clearInterval(refreshTimer.value)
    refreshTimer.value = null
  }
}

async function handleRefresh() {
  store.setLoading(true)
  
  setTimeout(() => {
    store.setLastUpdateTime(dayjs().format('HH:mm:ss'))
    store.setLoading(false)
  }, 300)
}

function handleSimulateData() {
  const buses: BusPosition[] = []
  const predictions: TrafficPrediction[] = []
  
  for (let i = 0; i < 100; i++) {
    buses.push({
      id: `BUS-${String(i + 1).padStart(5, '0')}`,
      longitude: 116.4074 + (Math.random() - 0.5) * 0.1,
      latitude: 39.9042 + (Math.random() - 0.5) * 0.1,
      height: 100,
      heading: Math.random() * 360,
      speed: Math.random() * 80,
      routeId: `ROUTE-${String(Math.floor(Math.random() * 100) + 1).padStart(3, '0')}`,
      timestamp: dayjs().format('YYYY-MM-DD HH:mm:ss')
    })
  }
  
  const intersections = [
    { id: 'INT-001', name: '天安门东', lng: 116.4090, lat: 39.9060 },
    { id: 'INT-002', name: '天安门西', lng: 116.4020, lat: 39.9060 },
    { id: 'INT-003', name: '王府井', lng: 116.4110, lat: 39.9100 },
    { id: 'INT-004', name: '前门', lng: 116.4050, lat: 39.8980 },
    { id: 'INT-005', name: '建国门', lng: 116.4350, lat: 39.9080 }
  ]
  
  const levels: CongestionLevel[] = ['LOW', 'MEDIUM', 'HIGH', 'SEVERE']
  
  intersections.forEach((int, index) => {
    const level = levels[Math.floor(Math.random() * levels.length)]
    const isGlowing = level === 'HIGH' || level === 'SEVERE'
    
    predictions.push({
      prediction_id: `pred-${Date.now()}-${index}`,
      intersection_id: int.id,
      intersection_name: int.name,
      latitude: int.lat,
      longitude: int.lng,
      prediction_timestamp: dayjs().toISOString(),
      prediction_window_minutes: 15,
      congestion_level: level,
      confidence: 0.7 + Math.random() * 0.3,
      predicted_bus_count: Math.floor(Math.random() * 20) + 5,
      predicted_average_speed: Math.random() * 60,
      polygon_coordinates: generatePolygon(int.lat, int.lng, 150),
      is_glowing: isGlowing
    })
  })
  
  store.updateBuses(buses)
  store.updatePredictions(predictions)
  store.setLastUpdateTime(dayjs().format('HH:mm:ss'))
}

function generatePolygon(lat: number, lng: number, radius: number): number[][] {
  const polygon: number[][] = []
  const sides = 8
  const latPerMeter = 1.0 / 111000.0
  const lngPerMeter = 1.0 / (111000.0 * Math.cos(lat * Math.PI / 180))

  for (let i = 0; i < sides; i++) {
    const angle = 2 * Math.PI * i / sides
    const dLat = radius * latPerMeter * Math.cos(angle)
    const dLng = radius * lngPerMeter * Math.sin(angle)
    polygon.push([lng + dLng, lat + dLat])
  }

  if (polygon.length > 0) {
    polygon.push(polygon[0])
  }
  return polygon
}

onMounted(() => {
  if (autoRefresh.value) {
    startRefreshTimer()
  }
  handleSimulateData()
})

onUnmounted(() => {
  stopRefreshTimer()
})
</script>

<style scoped>
.traffic-dashboard {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100%;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.stat-card.danger {
  border-left: 4px solid #F56C6C;
}

.stat-content {
  display: flex;
  align-items: center;
}

.stat-icon {
  margin-right: 20px;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 5px;
}

.content-row {
  margin-bottom: 20px;
}

.list-card {
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  height: 500px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 300px;
}

.warning-list {
  max-height: 400px;
  overflow-y: auto;
}

.warning-item {
  padding: 15px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  margin-bottom: 10px;
  cursor: pointer;
  transition: all 0.3s;
}

.warning-item:hover {
  border-color: #409EFF;
  box-shadow: 0 2px 12px rgba(64, 158, 255, 0.2);
}

.warning-item.selected {
  border-color: #409EFF;
  background-color: #ecf5ff;
}

.warning-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.warning-name {
  font-weight: bold;
  font-size: 16px;
}

.warning-detail {
  display: flex;
  gap: 20px;
  margin-bottom: 10px;
  font-size: 13px;
  color: #606266;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 5px;
}

.status-info {
  padding: 10px 0;
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.status-label {
  font-weight: 500;
}

.congestion-legend {
  margin-top: 10px;
}

.legend-title {
  font-weight: 500;
  margin-bottom: 10px;
}

.legend-items {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.legend-color {
  width: 20px;
  height: 20px;
  border-radius: 4px;
}

.action-buttons {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}
</style>
