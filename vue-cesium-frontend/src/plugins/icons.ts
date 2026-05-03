import type { App } from 'vue'
import {
  Bus,
  Location,
  Warning,
  Clock,
  TrendCharts,
  Speed,
  Guide,
  Connection
} from '@element-plus/icons-vue'

const icons = {
  Bus,
  Location,
  Warning,
  Clock,
  TrendCharts,
  Speed,
  Guide,
  Connection
}

export function registerIcons(app: App) {
  Object.keys(icons).forEach(key => {
    app.component(key, (icons as any)[key])
  })
}
