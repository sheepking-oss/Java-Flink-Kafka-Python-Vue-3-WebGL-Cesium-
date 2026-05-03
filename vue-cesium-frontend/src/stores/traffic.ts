import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { BusPosition, TrafficPrediction, CongestionLevel } from '@/types'

export const useTrafficStore = defineStore('traffic', () => {
  const buses = ref<Map<string, BusPosition>>(new Map())
  const predictions = ref<Map<string, TrafficPrediction>>(new Map())
  const selectedBusId = ref<string | null>(null)
  const selectedIntersectionId = ref<string | null>(null)
  const isLoading = ref(false)
  const lastUpdateTime = ref<string>('')

  const busList = computed(() => Array.from(buses.value.values()))
  
  const predictionList = computed(() => Array.from(predictions.value.values()))
  
  const glowingPredictions = computed(() => 
    predictionList.value.filter(p => p.is_glowing)
  )

  const congestionStats = computed(() => {
    const stats: Record<CongestionLevel, number> = {
      LOW: 0,
      MEDIUM: 0,
      HIGH: 0,
      SEVERE: 0
    }
    
    predictionList.value.forEach(p => {
      stats[p.congestion_level]++
    })
    
    return stats
  })

  const totalBuses = computed(() => buses.value.size)
  const totalIntersections = computed(() => predictions.value.size)

  function updateBus(bus: BusPosition) {
    buses.value.set(bus.id, { ...bus })
  }

  function updateBuses(newBuses: BusPosition[]) {
    newBuses.forEach(bus => updateBus(bus))
  }

  function updatePrediction(prediction: TrafficPrediction) {
    predictions.value.set(prediction.intersection_id, { ...prediction })
  }

  function updatePredictions(newPredictions: TrafficPrediction[]) {
    newPredictions.forEach(p => updatePrediction(p))
  }

  function selectBus(busId: string | null) {
    selectedBusId.value = busId
  }

  function selectIntersection(intersectionId: string | null) {
    selectedIntersectionId.value = intersectionId
  }

  function setLoading(loading: boolean) {
    isLoading.value = loading
  }

  function setLastUpdateTime(time: string) {
    lastUpdateTime.value = time
  }

  function clearAll() {
    buses.value.clear()
    predictions.value.clear()
    selectedBusId.value = null
    selectedIntersectionId.value = null
  }

  return {
    buses,
    predictions,
    selectedBusId,
    selectedIntersectionId,
    isLoading,
    lastUpdateTime,
    busList,
    predictionList,
    glowingPredictions,
    congestionStats,
    totalBuses,
    totalIntersections,
    updateBus,
    updateBuses,
    updatePrediction,
    updatePredictions,
    selectBus,
    selectIntersection,
    setLoading,
    setLastUpdateTime,
    clearAll
  }
})
