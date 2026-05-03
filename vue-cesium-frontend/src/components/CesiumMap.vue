<template>
  <div class="cesium-container">
    <div id="cesiumContainer" ref="cesiumContainer"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import * as Cesium from 'cesium'
import 'cesium/Build/Cesium/Widgets/widgets.css'
import { useTrafficStore } from '@/stores/traffic'
import type { BusPosition, TrafficPrediction, CongestionLevel } from '@/types'

const store = useTrafficStore()
const cesiumContainer = ref<HTMLDivElement | null>(null)
const viewer = ref<Cesium.Viewer | null>(null)
const busEntities = ref<Map<string, Cesium.Entity>>(new Map())
const intersectionEntities = ref<Map<string, Cesium.Entity>>(new Map())
const glowingInterval = ref<number | null>(null)

const congestionColors: Record<CongestionLevel, string> = {
  LOW: '#00FF00',
  MEDIUM: '#FFFF00',
  HIGH: '#FF8C00',
  SEVERE: '#FF0000'
}

function initCesium() {
  if (!cesiumContainer.value) return

  Cesium.Ion.defaultAccessToken = ''
  
  viewer.value = new Cesium.Viewer('cesiumContainer', {
    animation: true,
    timeline: true,
    baseLayerPicker: false,
    geocoder: false,
    homeButton: false,
    sceneModePicker: false,
    navigationHelpButton: false,
    fullscreenButton: false,
    vrButton: false,
    infoBox: true,
    selectionIndicator: true,
    shadows: false,
    shouldAnimate: true
  })

  viewer.value.scene.globe.enableLighting = true
  viewer.value.scene.fog.enabled = true
  
  const beijingPosition = Cesium.Cartesian3.fromDegrees(116.4074, 39.9042, 15000)
  viewer.value.camera.setView({
    destination: beijingPosition,
    orientation: {
      heading: Cesium.Math.toRadians(0),
      pitch: Cesium.Math.toRadians(-45),
      roll: 0
    }
  })

  createGlowingEffect()
}

function createGlowingEffect() {
  let pulsePhase = 0
  glowingInterval.value = window.setInterval(() => {
    pulsePhase += 0.1
    if (pulsePhase > Math.PI * 2) {
      pulsePhase = 0
    }

    store.glowingPredictions.forEach(prediction => {
      const entity = intersectionEntities.value.get(prediction.intersection_id)
      if (entity && entity.polygon) {
        const intensity = 0.5 + 0.5 * Math.sin(pulsePhase)
        const alpha = 0.3 + 0.4 * intensity
        
        if (entity.polygon.material instanceof Cesium.ColorMaterialProperty) {
          const color = Cesium.Color.fromCssColorString(congestionColors[prediction.congestion_level])
          color.alpha = alpha
          entity.polygon.material = new Cesium.ColorMaterialProperty(color)
        }
      }
    })
  }, 100)
}

function createBusEntity(bus: BusPosition): Cesium.Entity {
  const position = Cesium.Cartesian3.fromDegrees(
    bus.longitude,
    bus.latitude,
    100
  )

  const heading = Cesium.Math.toRadians(bus.heading)
  const modelMatrix = Cesium.Transforms.headingPitchRollToFixedFrame(
    position,
    new Cesium.HeadingPitchRoll(heading, 0, 0)
  )

  const color = bus.speed < 10 ? Cesium.Color.RED : 
                bus.speed < 30 ? Cesium.Color.ORANGE : 
                Cesium.Color.GREEN

  return new Cesium.Entity({
    id: bus.id,
    name: `公交车 ${bus.id}`,
    position: position,
    point: {
      pixelSize: 8,
      color: color,
      outlineColor: Cesium.Color.WHITE,
      outlineWidth: 2,
      disableDepthTestDistance: Number.POSITIVE_INFINITY
    },
    label: {
      text: bus.id,
      font: '12px sans-serif',
      fillColor: Cesium.Color.WHITE,
      outlineColor: Cesium.Color.BLACK,
      outlineWidth: 2,
      style: Cesium.LabelStyle.FILL_AND_OUTLINE,
      verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
      pixelOffset: new Cesium.Cartesian2(0, -10),
      disableDepthTestDistance: Number.POSITIVE_INFINITY
    },
    path: {
      leadTime: 0,
      trailTime: 60,
      width: 5,
      material: new Cesium.PolylineGlowMaterialProperty({
        glowPower: 0.3,
        color: Cesium.Color.CYAN
      })
    },
    description: `
      <table style="width: 100%;">
        <tr><td><strong>车辆编号:</strong></td><td>${bus.id}</td></tr>
        <tr><td><strong>线路:</strong></td><td>${bus.routeId}</td></tr>
        <tr><td><strong>当前速度:</strong></td><td>${bus.speed.toFixed(1)} km/h</td></tr>
        <tr><td><strong>方向:</strong></td><td>${bus.heading.toFixed(1)}°</td></tr>
        <tr><td><strong>时间:</strong></td><td>${bus.timestamp}</td></tr>
      </table>
    `
  })
}

function createIntersectionEntity(prediction: TrafficPrediction): Cesium.Entity {
  const coordinates: number[] = []
  prediction.polygon_coordinates.forEach(point => {
    if (point.length >= 2) {
      coordinates.push(point[0], point[1])
    }
  })

  const color = Cesium.Color.fromCssColorString(congestionColors[prediction.congestion_level])
  color.alpha = prediction.is_glowing ? 0.5 : 0.3

  const outlineColor = prediction.is_glowing ? 
    Cesium.Color.RED : 
    Cesium.Color.fromCssColorString(congestionColors[prediction.congestion_level])

  return new Cesium.Entity({
    id: prediction.intersection_id,
    name: prediction.intersection_name,
    polygon: {
      hierarchy: Cesium.Cartesian3.fromDegreesArray(coordinates),
      height: 50,
      material: new Cesium.ColorMaterialProperty(color),
      outline: true,
      outlineColor: outlineColor,
      outlineWidth: 3
    },
    description: `
      <table style="width: 100%;">
        <tr><td><strong>路口名称:</strong></td><td>${prediction.intersection_name}</td></tr>
        <tr><td><strong>拥堵等级:</strong></td><td style="color: ${congestionColors[prediction.congestion_level]}"><strong>${prediction.congestion_level}</strong></td></tr>
        <tr><td><strong>置信度:</strong></td><td>${(prediction.confidence * 100).toFixed(0)}%</td></tr>
        <tr><td><strong>预测公交车数:</strong></td><td>${prediction.predicted_bus_count}</td></tr>
        <tr><td><strong>预测平均速度:</strong></td><td>${prediction.predicted_average_speed.toFixed(1)} km/h</td></tr>
        <tr><td><strong>发光预警:</strong></td><td>${prediction.is_glowing ? '<span style="color: red;">是</span>' : '否'}</td></tr>
      </table>
    `
  })
}

function updateBusEntity(bus: BusPosition) {
  if (!viewer.value) return

  const existingEntity = busEntities.value.get(bus.id)
  
  if (existingEntity) {
    const position = Cesium.Cartesian3.fromDegrees(
      bus.longitude,
      bus.latitude,
      100
    )
    
    const color = bus.speed < 10 ? Cesium.Color.RED : 
                  bus.speed < 30 ? Cesium.Color.ORANGE : 
                  Cesium.Color.GREEN

    existingEntity.position = new Cesium.ConstantPositionProperty(position)
    if (existingEntity.point) {
      existingEntity.point.color = new Cesium.ConstantProperty(color)
    }
  } else {
    const entity = createBusEntity(bus)
    viewer.value.entities.add(entity)
    busEntities.value.set(bus.id, entity)
  }
}

function updateIntersectionEntity(prediction: TrafficPrediction) {
  if (!viewer.value) return

  const existingEntity = intersectionEntities.value.get(prediction.intersection_id)
  
  if (existingEntity) {
    viewer.value.entities.remove(existingEntity)
  }

  const entity = createIntersectionEntity(prediction)
  viewer.value.entities.add(entity)
  intersectionEntities.value.set(prediction.intersection_id, entity)
}

function removeOldEntities(currentBuses: string[], currentIntersections: string[]) {
  if (!viewer.value) return

  const busesToRemove = Array.from(busEntities.value.keys()).filter(
    id => !currentBuses.includes(id)
  )
  
  busesToRemove.forEach(id => {
    const entity = busEntities.value.get(id)
    if (entity) {
      viewer.value!.entities.remove(entity)
      busEntities.value.delete(id)
    }
  })
}

watch(
  () => store.busList,
  (newBuses) => {
    newBuses.forEach(bus => updateBusEntity(bus))
    
    const currentBusIds = newBuses.map(b => b.id)
    removeOldEntities(currentBusIds, [])
  },
  { deep: true }
)

watch(
  () => store.predictionList,
  (newPredictions) => {
    newPredictions.forEach(prediction => updateIntersectionEntity(prediction))
  },
  { deep: true }
)

onMounted(() => {
  initCesium()
})

onUnmounted(() => {
  if (glowingInterval.value) {
    window.clearInterval(glowingInterval.value)
  }
  
  if (viewer.value) {
    viewer.value.destroy()
    viewer.value = null
  }
  
  busEntities.value.clear()
  intersectionEntities.value.clear()
})
</script>

<style scoped>
.cesium-container {
  width: 100%;
  height: 100%;
}

#cesiumContainer {
  width: 100%;
  height: 100%;
}
</style>
