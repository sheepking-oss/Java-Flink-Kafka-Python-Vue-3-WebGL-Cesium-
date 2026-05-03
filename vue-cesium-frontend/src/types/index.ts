export interface BusGpsData {
  bus_id: string
  route_id: string
  latitude: number
  longitude: number
  speed: number
  heading: number
  timestamp: string
}

export interface AggregatedGpsData {
  window_start: string
  window_end: string
  total_buses: number
  active_buses: number
  average_speed: number
  buses: BusGpsData[]
}

export interface IntersectionInfo {
  intersection_id: string
  intersection_name: string
  latitude: number
  longitude: number
  radius: number
  polygon_coordinates: number[][]
}

export interface IntersectionTrafficData {
  intersection_id: string
  intersection_name: string
  latitude: number
  longitude: number
  timestamp: string
  bus_count: number
  average_speed: number
  bus_ids: string[]
  polygon_coordinates: number[][]
}

export type CongestionLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'SEVERE'

export interface TrafficPrediction {
  prediction_id: string
  intersection_id: string
  intersection_name: string
  latitude: number
  longitude: number
  prediction_timestamp: string
  prediction_window_minutes: number
  congestion_level: CongestionLevel
  confidence: number
  predicted_bus_count: number
  predicted_average_speed: number
  polygon_coordinates: number[][]
  is_glowing: boolean
}

export interface BusPosition {
  id: string
  longitude: number
  latitude: number
  height: number
  heading: number
  speed: number
  routeId: string
  timestamp: string
}
