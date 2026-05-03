<template>
  <div class="home-view">
    <el-row :gutter="0" class="main-row">
      <el-col :span="16" class="map-column">
        <div class="map-container">
          <CesiumMap />
        </div>
      </el-col>
      <el-col :span="8" class="dashboard-column">
        <div class="dashboard-container">
          <TrafficDashboard />
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import CesiumMap from '@/components/CesiumMap.vue'
import TrafficDashboard from '@/components/TrafficDashboard.vue'
</script>

<style scoped>
.home-view {
  width: 100%;
  height: 100%;
}

.main-row {
  height: 100%;
}

.map-column {
  height: 100%;
}

.map-container {
  width: 100%;
  height: 100%;
}

.dashboard-column {
  height: 100%;
  overflow-y: auto;
}

.dashboard-container {
  width: 100%;
  height: 100%;
  padding: 0;
}
</style>
