<template>
  <div class="history-page">
    <!-- Header Section -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-group">
          <svg class="header-icon" viewBox="0 0 24 24" fill="none">
            <path d="M3 3v18h18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M7 16l4-4 4 4 5-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <h1 class="page-title">历史趋势</h1>
        </div>
        <p class="page-subtitle">查看主机资源使用率的历史变化趋势</p>
      </div>
    </div>

    <!-- Filter Section -->
    <div class="filter-section">
      <div class="filter-card glass-card">
        <div class="filter-group">
          <label class="filter-label">
            <svg viewBox="0 0 24 24" fill="none">
              <rect x="2" y="3" width="20" height="14" rx="2" stroke="currentColor" stroke-width="2"/>
              <path d="M8 21h8M12 17v4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
            选择主机
          </label>
          <div class="select-wrapper">
            <select v-model="selectedHost" @change="loadHistory" class="glass-select" :disabled="hosts.length === 0">
              <option value="" disabled>{{ hostSelectorPlaceholder }}</option>
              <option v-for="host in hosts" :key="host" :value="host">{{ host }}</option>
            </select>
            <svg class="select-arrow" viewBox="0 0 24 24" fill="none">
              <path d="M7 10l5 5 5-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
        </div>

        <div class="filter-group">
          <label class="filter-label">
            <svg viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
              <path d="M12 6v6l4 2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
            时间范围
          </label>
          <div class="time-buttons">
            <button
              class="time-btn"
              :class="{ active: selectedDays === '1' }"
              :disabled="!selectedHost"
              @click="setDays('1')"
            >
              今日
            </button>
            <button
              class="time-btn"
              :class="{ active: selectedDays === '7' }"
              :disabled="!selectedHost"
              @click="setDays('7')"
            >
              近7天
            </button>
            <button
              class="time-btn"
              :class="{ active: selectedDays === '30' }"
              :disabled="!selectedHost"
              @click="setDays('30')"
            >
              近30天
            </button>
          </div>
        </div>

        <button class="refresh-btn glass-btn" :disabled="!selectedHost" @click="loadHistory">
          <svg viewBox="0 0 24 24" fill="none" class="btn-icon">
            <path d="M21 12a9 9 0 11-6.219-8.56" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            <path d="M21 3v6h-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span>刷新数据</span>
        </button>
      </div>
    </div>

    <div v-if="statusBannerText" class="status-banner glass-card" :class="statusBannerClass">
      {{ statusBannerText }}
    </div>

    <!-- Charts Section -->
    <div class="charts-section">
      <div class="chart-card glass-card">
        <div class="chart-header">
          <div class="chart-title-group">
            <div class="chart-icon cpu">
              <svg viewBox="0 0 24 24" fill="none">
                <rect x="4" y="4" width="16" height="16" rx="2" stroke="currentColor" stroke-width="2"/>
                <rect x="9" y="9" width="6" height="6" stroke="currentColor" stroke-width="2"/>
                <path d="M9 1v3M15 1v3M9 20v3M15 20v3M20 9h3M20 15h3M1 9h3M1 15h3" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </div>
            <h3 class="chart-title">CPU 使用率趋势</h3>
          </div>
          <div class="chart-legend">
            <span class="legend-item">
              <span class="legend-dot warning"></span>
              警告线 70%
            </span>
            <span class="legend-item">
              <span class="legend-dot critical"></span>
              严重线 80%
            </span>
          </div>
        </div>
        <div v-if="historyData.length > 0" ref="cpuChart" class="chart-container"></div>
        <div v-else class="chart-empty">{{ chartEmptyText }}</div>
      </div>

      <div class="chart-card glass-card">
        <div class="chart-header">
          <div class="chart-title-group">
            <div class="chart-icon memory">
              <svg viewBox="0 0 24 24" fill="none">
                <path d="M4 4h16v16H4z" stroke="currentColor" stroke-width="2"/>
                <path d="M4 8h16M4 12h16M4 16h16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </div>
            <h3 class="chart-title">内存使用率趋势</h3>
          </div>
          <div class="chart-legend">
            <span class="legend-item">
              <span class="legend-dot warning"></span>
              警告线 70%
            </span>
            <span class="legend-item">
              <span class="legend-dot critical"></span>
              严重线 80%
            </span>
          </div>
        </div>
        <div v-if="historyData.length > 0" ref="memoryChart" class="chart-container"></div>
        <div v-else class="chart-empty">{{ chartEmptyText }}</div>
      </div>

      <div class="chart-card glass-card">
        <div class="chart-header">
          <div class="chart-title-group">
            <div class="chart-icon storage">
              <svg viewBox="0 0 24 24" fill="none">
                <ellipse cx="12" cy="5" rx="9" ry="3" stroke="currentColor" stroke-width="2"/>
                <path d="M21 5v14c0 1.66-4 3-9 3s-9-1.34-9-3V5" stroke="currentColor" stroke-width="2"/>
                <path d="M3 12c0 1.66 4 3 9 3s9-1.34 9-3" stroke="currentColor" stroke-width="2"/>
              </svg>
            </div>
            <h3 class="chart-title">存储使用率趋势</h3>
          </div>
          <div class="chart-legend">
            <span class="legend-item">
              <span class="legend-dot warning"></span>
              警告线 60%
            </span>
            <span class="legend-item">
              <span class="legend-dot critical"></span>
              严重线 70%
            </span>
          </div>
        </div>
        <div v-if="historyData.length > 0" ref="storageChart" class="chart-container"></div>
        <div v-else class="chart-empty">{{ chartEmptyText }}</div>
      </div>
    </div>

    <!-- Stats Summary -->
    <div v-if="historyData.length > 0" class="stats-section">
      <div class="stats-card glass-card">
        <div class="stats-header">
          <h3 class="stats-title">统计数据摘要</h3>
          <span class="data-count">{{ historyData.length }} 条记录</span>
        </div>
        <div class="stats-grid">
          <div class="stat-item">
            <div class="stat-label">CPU 最高值</div>
            <div class="stat-value">
              <span class="stat-number" :class="getValueClass(maxCpu)">{{ maxCpu.toFixed(1) }}</span>
              <span class="stat-unit">%</span>
            </div>
          </div>
          <div class="stat-item">
            <div class="stat-label">CPU 平均值</div>
            <div class="stat-value">
              <span class="stat-number" :class="getValueClass(avgCpu)">{{ avgCpu.toFixed(1) }}</span>
              <span class="stat-unit">%</span>
            </div>
          </div>
          <div class="stat-item">
            <div class="stat-label">内存最高值</div>
            <div class="stat-value">
              <span class="stat-number" :class="getValueClass(maxMemory)">{{ maxMemory.toFixed(1) }}</span>
              <span class="stat-unit">%</span>
            </div>
          </div>
          <div class="stat-item">
            <div class="stat-label">内存平均值</div>
            <div class="stat-value">
              <span class="stat-number" :class="getValueClass(avgMemory)">{{ avgMemory.toFixed(1) }}</span>
              <span class="stat-unit">%</span>
            </div>
          </div>
          <div class="stat-item">
            <div class="stat-label">存储最高值</div>
            <div class="stat-value">
              <span class="stat-number storage" :class="getStorageClass(maxStorage)">{{ maxStorage.toFixed(1) }}</span>
              <span class="stat-unit">%</span>
            </div>
          </div>
          <div class="stat-item">
            <div class="stat-label">存储平均值</div>
            <div class="stat-value">
              <span class="stat-number storage" :class="getStorageClass(avgStorage)">{{ avgStorage.toFixed(1) }}</span>
              <span class="stat-unit">%</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- History Table -->
    <div class="table-section">
      <div class="table-card glass-card">
        <div class="table-header">
          <h3 class="table-title">历史数据明细</h3>
          <span class="table-info">最多显示50条最新记录</span>
        </div>
        <div class="table-wrapper">
          <table class="glass-table">
            <thead>
              <tr>
                <th>时间</th>
                <th>CPU使用率</th>
                <th>内存使用率</th>
                <th>存储使用率</th>
                <th>状态</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, index) in historyData.slice(0, 50)" :key="index" class="table-row" :class="getRowClass(row)">
                <td class="time-cell">{{ formatTime(row.timestamp) }}</td>
                <td>
                  <div class="progress-cell">
                    <div class="progress-bar">
                      <div class="progress-fill" :style="{ width: row.cpu_usage + '%' }" :class="getProgressClass(row.cpu_usage, 'cpu')"></div>
                    </div>
                    <span class="progress-value">{{ row.cpu_usage.toFixed(1) }}%</span>
                  </div>
                </td>
                <td>
                  <div class="progress-cell">
                    <div class="progress-bar">
                      <div class="progress-fill" :style="{ width: row.memory_usage + '%' }" :class="getProgressClass(row.memory_usage, 'memory')"></div>
                    </div>
                    <span class="progress-value">{{ row.memory_usage.toFixed(1) }}%</span>
                  </div>
                </td>
                <td>
                  <div class="progress-cell">
                    <div class="progress-bar">
                      <div class="progress-fill" :style="{ width: row.storage_usage + '%' }" :class="getProgressClass(row.storage_usage, 'storage')"></div>
                    </div>
                    <span class="progress-value">{{ row.storage_usage.toFixed(1) }}%</span>
                  </div>
                </td>
                <td>
                  <span class="status-badge" :class="getStatusClass(row)">
                    {{ getStatusText(row) }}
                  </span>
                </td>
              </tr>
              <tr v-if="historyData.length === 0">
                <td colspan="5" class="empty-cell">{{ tableEmptyText }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import * as echarts from 'echarts'

const route = useRoute()

const selectedHost = ref(route.query.host || '')
const selectedDays = ref('7')
const hosts = ref([])
const historyData = ref([])
const hostsStatus = ref('loading')
const hostsMessage = ref('')
const historyStatus = ref('idle')
const historyMessage = ref('')

const cpuChart = ref(null)
const memoryChart = ref(null)
const storageChart = ref(null)

let cpuChartInstance = null
let memoryChartInstance = null
let storageChartInstance = null

const hostSelectorPlaceholder = computed(() => {
  if (hostsStatus.value === 'no_credentials') return '未配置可用主机'
  if (hostsStatus.value === 'collection_failed' || hostsStatus.value === 'error') return '主机列表加载失败'
  return '请选择主机'
})

const chartEmptyText = computed(() => {
  if (historyStatus.value === 'collection_failed' || historyStatus.value === 'error') return historyMessage.value || '历史巡检数据加载失败'
  if (historyStatus.value === 'no_data') return historyMessage.value || '当前主机暂无历史巡检记录'
  if (!selectedHost.value) return hostsMessage.value || '当前没有可用主机'
  return historyMessage.value || '暂无历史数据'
})

const tableEmptyText = computed(() => {
  if (historyStatus.value === 'collection_failed' || historyStatus.value === 'error') return historyMessage.value || '历史巡检数据加载失败'
  if (historyStatus.value === 'no_data') return historyMessage.value || '当前主机暂无历史巡检记录'
  if (!selectedHost.value) return hostsMessage.value || '当前没有可用主机'
  return historyMessage.value || '暂无数据'
})

const statusBannerClass = computed(() => {
  if (historyStatus.value === 'collection_failed' || historyStatus.value === 'error' || hostsStatus.value === 'collection_failed' || hostsStatus.value === 'error') {
    return 'error'
  }
  if (hostsStatus.value === 'partial_data' || historyStatus.value === 'partial_data') {
    return 'warning'
  }
  return 'info'
})

const statusBannerText = computed(() => {
  if (hostsStatus.value === 'no_credentials') return hostsMessage.value || '未配置可用的 API 凭证'
  if (hostsStatus.value === 'collection_failed' || hostsStatus.value === 'error') return hostsMessage.value || '主机列表加载失败'
  if (hostsStatus.value === 'partial_data') return hostsMessage.value || '部分平台主机数据采集异常'
  if (historyStatus.value === 'collection_failed' || historyStatus.value === 'error') return historyMessage.value || '历史巡检数据加载失败'
  if (historyStatus.value === 'partial_data') return historyMessage.value || '部分历史巡检数据加载异常'
  return ''
})

// Computed stats
const maxCpu = computed(() => Math.max(...historyData.value.map(d => d.cpu_usage || 0)))
const avgCpu = computed(() => historyData.value.reduce((a, b) => a + (b.cpu_usage || 0), 0) / historyData.value.length || 0)
const maxMemory = computed(() => Math.max(...historyData.value.map(d => d.memory_usage || 0)))
const avgMemory = computed(() => historyData.value.reduce((a, b) => a + (b.memory_usage || 0), 0) / historyData.value.length || 0)
const maxStorage = computed(() => Math.max(...historyData.value.map(d => d.storage_usage || 0)))
const avgStorage = computed(() => historyData.value.reduce((a, b) => a + (b.storage_usage || 0), 0) / historyData.value.length || 0)

const setDays = (days) => {
  selectedDays.value = days
  loadHistory()
}

const clearCharts = () => {
  if (cpuChartInstance) cpuChartInstance.clear()
  if (memoryChartInstance) memoryChartInstance.clear()
  if (storageChartInstance) storageChartInstance.clear()
}

const loadHosts = async () => {
  try {
    const response = await axios.get('/api/inspection/list')
    hostsStatus.value = response.data.status || 'unknown'
    hostsMessage.value = response.data.message || ''
    hosts.value = Array.isArray(response.data.data) ? response.data.data.map(h => h.host_name) : []

    if (hosts.value.length === 0) {
      selectedHost.value = ''
      historyStatus.value = hostsStatus.value === 'unknown' ? 'no_data' : hostsStatus.value
      historyMessage.value = hostsMessage.value
      historyData.value = []
      clearCharts()
      return
    }

    if (!hosts.value.includes(selectedHost.value)) {
      selectedHost.value = hosts.value[0]
    }

    if (selectedHost.value) {
      await loadHistory()
    }
  } catch (error) {
    console.error('加载主机列表失败:', error)
    hostsStatus.value = 'error'
    hostsMessage.value = '主机列表加载失败'
    historyStatus.value = 'error'
    historyMessage.value = '主机列表加载失败'
    hosts.value = []
    historyData.value = []
    selectedHost.value = ''
    clearCharts()
  }
}

const loadHistory = async () => {
  if (!selectedHost.value) {
    historyStatus.value = hostsStatus.value === 'unknown' ? 'idle' : hostsStatus.value
    historyMessage.value = hostsMessage.value || '当前没有可用主机'
    historyData.value = []
    clearCharts()
    return
  }

  try {
    const response = await axios.get(`/api/inspection/history/${encodeURIComponent(selectedHost.value)}`, {
      params: { days: selectedDays.value }
    })
    historyStatus.value = response.data.status || 'unknown'
    historyMessage.value = response.data.message || ''
    historyData.value = Array.isArray(response.data.data) ? response.data.data : []
    if (historyData.value.length > 0) {
      renderCharts()
    } else {
      clearCharts()
    }
  } catch (error) {
    console.error('加载历史数据失败:', error)
    historyStatus.value = 'error'
    historyMessage.value = '历史巡检数据加载失败'
    historyData.value = []
    clearCharts()
  }
}

const renderCharts = () => {
  // Reverse so oldest is left, newest is right
  const reversed = [...historyData.value].reverse()
  const timestamps = reversed.map(d => formatTime(d.timestamp))
  const cpuData = reversed.map(d => d.cpu_usage)
  const memoryData = reversed.map(d => d.memory_usage)
  const storageData = reversed.map(d => d.storage_usage)

  const chartTheme = {
    backgroundColor: 'transparent',
    textStyle: { color: 'rgba(255,255,255,0.7)' },
    axisLine: { lineStyle: { color: 'rgba(255,255,255,0.15)' } },
    splitLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } }
  }

  // CPU Chart
  if (cpuChart.value) {
    if (!cpuChartInstance) {
      cpuChartInstance = echarts.init(cpuChart.value)
    }
    cpuChartInstance.setOption({
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(15,15,35,0.9)',
        borderColor: 'rgba(255,255,255,0.1)',
        textStyle: { color: '#fff' }
      },
      xAxis: {
        type: 'category',
        data: timestamps,
        axisLabel: { rotate: 45, color: 'rgba(255,255,255,0.5)', fontSize: 11 },
        axisLine: { lineStyle: { color: 'rgba(255,255,255,0.15)' } }
      },
      yAxis: {
        type: 'value',
        max: 100,
        axisLabel: { color: 'rgba(255,255,255,0.5)' },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } }
      },
      series: [{
        name: 'CPU',
        type: 'line',
        data: cpuData,
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(96,165,250,0.4)' },
              { offset: 1, color: 'rgba(96,165,250,0.05)' }
            ]
          }
        },
        lineStyle: { color: '#60a5fa', width: 2 }
      }],
      grid: { left: '3%', right: '4%', bottom: '18%', top: '10%', containLabel: true },
      markLine: {
        silent: true,
        data: [
          { yAxis: 70, lineStyle: { color: '#fbbf24', width: 1, type: 'dashed' }, label: { formatter: '警告', color: '#fbbf24' } },
          { yAxis: 80, lineStyle: { color: '#f87171', width: 1, type: 'dashed' }, label: { formatter: '严重', color: '#f87171' } }
        ]
      }
    })
  }

  // Memory Chart
  if (memoryChart.value) {
    if (!memoryChartInstance) {
      memoryChartInstance = echarts.init(memoryChart.value)
    }
    memoryChartInstance.setOption({
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(15,15,35,0.9)',
        borderColor: 'rgba(255,255,255,0.1)',
        textStyle: { color: '#fff' }
      },
      xAxis: {
        type: 'category',
        data: timestamps,
        axisLabel: { rotate: 45, color: 'rgba(255,255,255,0.5)', fontSize: 11 },
        axisLine: { lineStyle: { color: 'rgba(255,255,255,0.15)' } }
      },
      yAxis: {
        type: 'value',
        max: 100,
        axisLabel: { color: 'rgba(255,255,255,0.5)' },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } }
      },
      series: [{
        name: '内存',
        type: 'line',
        data: memoryData,
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(251,191,36,0.4)' },
              { offset: 1, color: 'rgba(251,191,36,0.05)' }
            ]
          }
        },
        lineStyle: { color: '#fbbf24', width: 2 }
      }],
      grid: { left: '3%', right: '4%', bottom: '18%', top: '10%', containLabel: true },
      markLine: {
        silent: true,
        data: [
          { yAxis: 70, lineStyle: { color: '#fbbf24', width: 1, type: 'dashed' }, label: { formatter: '警告', color: '#fbbf24' } },
          { yAxis: 80, lineStyle: { color: '#f87171', width: 1, type: 'dashed' }, label: { formatter: '严重', color: '#f87171' } }
        ]
      }
    })
  }

  // Storage Chart
  if (storageChart.value) {
    if (!storageChartInstance) {
      storageChartInstance = echarts.init(storageChart.value)
    }
    storageChartInstance.setOption({
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(15,15,35,0.9)',
        borderColor: 'rgba(255,255,255,0.1)',
        textStyle: { color: '#fff' }
      },
      xAxis: {
        type: 'category',
        data: timestamps,
        axisLabel: { rotate: 45, color: 'rgba(255,255,255,0.5)', fontSize: 11 },
        axisLine: { lineStyle: { color: 'rgba(255,255,255,0.15)' } }
      },
      yAxis: {
        type: 'value',
        max: 100,
        axisLabel: { color: 'rgba(255,255,255,0.5)' },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } }
      },
      series: [{
        name: '存储',
        type: 'line',
        data: storageData,
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(52,211,153,0.4)' },
              { offset: 1, color: 'rgba(52,211,153,0.05)' }
            ]
          }
        },
        lineStyle: { color: '#34d399', width: 2 }
      }],
      grid: { left: '3%', right: '4%', bottom: '18%', top: '10%', containLabel: true },
      markLine: {
        silent: true,
        data: [
          { yAxis: 60, lineStyle: { color: '#fbbf24', width: 1, type: 'dashed' }, label: { formatter: '警告', color: '#fbbf24' } },
          { yAxis: 70, lineStyle: { color: '#f87171', width: 1, type: 'dashed' }, label: { formatter: '严重', color: '#f87171' } }
        ]
      }
    })
  }
}

const formatTime = (time) => new Date(time).toLocaleString('zh-CN')

const getValueClass = (value) => {
  if (value >= 80) return 'critical'
  if (value >= 70) return 'warning'
  return 'normal'
}

const getStorageClass = (value) => {
  if (value >= 70) return 'critical'
  if (value >= 60) return 'warning'
  return 'normal'
}

const getProgressClass = (value, type) => {
  if (type === 'storage') {
    if (value >= 70) return 'critical'
    if (value >= 60) return 'warning'
    return 'normal'
  }
  if (value >= 80) return 'critical'
  if (value >= 70) return 'warning'
  return 'normal'
}

const getRowClass = (row) => {
  if (row.cpu_usage >= 80 || row.memory_usage >= 80 || row.storage_usage >= 70) return 'critical-row'
  if (row.cpu_usage >= 70 || row.memory_usage >= 70 || row.storage_usage >= 60) return 'warning-row'
  return ''
}

const getStatusClass = (row) => {
  if (row.cpu_usage >= 80 || row.memory_usage >= 80 || row.storage_usage >= 70) return 'critical'
  if (row.cpu_usage >= 70 || row.memory_usage >= 70 || row.storage_usage >= 60) return 'warning'
  return 'normal'
}

const getStatusText = (row) => {
  const status = getStatusClass(row)
  if (status === 'critical') return '严重'
  if (status === 'warning') return '警告'
  return '正常'
}

const handleResize = () => {
  if (cpuChartInstance) cpuChartInstance.resize()
  if (memoryChartInstance) memoryChartInstance.resize()
  if (storageChartInstance) storageChartInstance.resize()
}

onMounted(() => {
  loadHosts()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (cpuChartInstance) cpuChartInstance.dispose()
  if (memoryChartInstance) memoryChartInstance.dispose()
  if (storageChartInstance) storageChartInstance.dispose()
})
</script>

<style scoped>
.history-page {
  padding: 24px;
  min-height: calc(100vh - 80px);
  background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 50%, #0d0d1f 100%);
}

/* Header */
.page-header {
  margin-bottom: 32px;
}

.header-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.title-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-icon {
  width: 32px;
  height: 32px;
  color: #60a5fa;
}

.page-title {
  font-size: 28px;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: 0.5px;
}

.page-subtitle {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
}

/* Glass Card */
.glass-card {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  transition: all 0.3s ease;
}

.glass-card:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.15);
}

/* Filter Section */
.filter-section {
  margin-bottom: 24px;
}

.filter-card {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 16px 24px;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
}

.filter-label svg {
  width: 16px;
  height: 16px;
}

.select-wrapper {
  position: relative;
}

.glass-select {
  padding: 10px 40px 10px 14px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: #ffffff;
  font-size: 14px;
  min-width: 200px;
  cursor: pointer;
  appearance: none;
}

.glass-select:focus {
  outline: none;
  border-color: rgba(96, 165, 250, 0.5);
}

.glass-select:disabled,
.time-btn:disabled,
.glass-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.glass-select option {
  background: #1a1a3e;
  color: #ffffff;
}

.select-arrow {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  width: 16px;
  height: 16px;
  color: rgba(255, 255, 255, 0.4);
}

.time-buttons {
  display: flex;
  gap: 8px;
}

.time-btn {
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  color: rgba(255, 255, 255, 0.6);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.time-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.12);
  color: rgba(255, 255, 255, 0.8);
}

.time-btn.active {
  background: rgba(96, 165, 250, 0.2);
  border-color: rgba(96, 165, 250, 0.3);
  color: #60a5fa;
}

.glass-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 8px;
  color: #ffffff;
  cursor: pointer;
  transition: all 0.3s ease;
}

.glass-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.25);
  transform: translateY(-2px);
}

.btn-icon {
  width: 18px;
  height: 18px;
}

.status-banner {
  margin-bottom: 24px;
  padding: 14px 18px;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.88);
}

.status-banner.info {
  border-color: rgba(96, 165, 250, 0.35);
  background: rgba(96, 165, 250, 0.12);
}

.status-banner.warning {
  border-color: rgba(251, 191, 36, 0.35);
  background: rgba(251, 191, 36, 0.12);
}

.status-banner.error {
  border-color: rgba(248, 113, 113, 0.35);
  background: rgba(248, 113, 113, 0.12);
}

/* Charts Section */
.charts-section {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.chart-card {
  padding: 20px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.chart-title-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chart-icon {
  width: 36px;
  height: 36px;
  padding: 8px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart-icon svg {
  width: 20px;
  height: 20px;
}

.chart-icon.cpu { background: rgba(96, 165, 250, 0.2); color: #60a5fa; }
.chart-icon.memory { background: rgba(251, 191, 36, 0.2); color: #fbbf24; }
.chart-icon.storage { background: rgba(52, 211, 153, 0.2); color: #34d399; }

.chart-title {
  font-size: 16px;
  font-weight: 600;
  color: #ffffff;
  margin: 0;
}

.chart-legend {
  display: flex;
  gap: 12px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.legend-dot.warning { background: #fbbf24; }
.legend-dot.critical { background: #f87171; }

.chart-container,
.chart-empty {
  height: 280px;
}

.chart-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: rgba(255, 255, 255, 0.5);
  font-size: 14px;
}

/* Stats Section */
.stats-section {
  margin-bottom: 24px;
}

.stats-card {
  padding: 24px;
}

.stats-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.stats-title {
  font-size: 18px;
  font-weight: 600;
  color: #ffffff;
  margin: 0;
}

.data-count {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.5);
  padding: 4px 12px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 6px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 16px;
}

.stat-item {
  text-align: center;
  padding: 16px;
  background: rgba(255, 255, 255, 0.04);
  border-radius: 12px;
}

.stat-label {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.5);
  margin-bottom: 8px;
}

.stat-value {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 4px;
}

.stat-number {
  font-size: 24px;
  font-weight: 700;
  color: #34d399;
}

.stat-number.warning { color: #fbbf24; }
.stat-number.critical { color: #f87171; }

.stat-unit {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.5);
}

/* Table Section */
.table-section {
  margin-bottom: 24px;
}

.table-card {
  padding: 24px;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.table-title {
  font-size: 18px;
  font-weight: 600;
  color: #ffffff;
  margin: 0;
}

.table-info {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.5);
}

.table-wrapper {
  overflow-x: auto;
}

.glass-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: auto;
}

.glass-table th {
  padding: 12px 14px;
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.7);
  font-size: 13px;
  font-weight: 500;
  text-align: left;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  white-space: nowrap;
}

.glass-table td {
  padding: 12px 14px;
  color: #ffffff;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.table-row {
  transition: all 0.3s ease;
}

.table-row:hover {
  background: rgba(255, 255, 255, 0.05);
}

.table-row.warning-row {
  background: rgba(251, 191, 36, 0.05);
}

.table-row.warning-row:hover {
  background: rgba(251, 191, 36, 0.08);
}

.table-row.critical-row {
  background: rgba(248, 113, 113, 0.08);
}

.table-row.critical-row:hover {
  background: rgba(248, 113, 113, 0.12);
}

.time-cell {
  color: rgba(255, 255, 255, 0.6);
}

.progress-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.progress-bar {
  width: 120px;
  height: 8px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.5s ease;
}

.progress-fill.normal { background: linear-gradient(90deg, #34d399, #60a5fa); }
.progress-fill.warning { background: linear-gradient(90deg, #fbbf24, #f59e0b); }
.progress-fill.critical { background: linear-gradient(90deg, #f87171, #ef4444); }

.progress-value {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.8);
  min-width: 50px;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge.normal {
  background: rgba(52, 211, 153, 0.2);
  color: #34d399;
}

.status-badge.warning {
  background: rgba(251, 191, 36, 0.2);
  color: #fbbf24;
}

.status-badge.critical {
  background: rgba(248, 113, 113, 0.2);
  color: #f87171;
}

.empty-cell {
  text-align: center;
  color: rgba(255, 255, 255, 0.4);
  padding: 40px;
}

/* Responsive */
@media (max-width: 1200px) {
  .charts-section {
    grid-template-columns: repeat(2, 1fr);
  }

  .stats-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 768px) {
  .charts-section {
    grid-template-columns: 1fr;
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .filter-card {
    flex-wrap: wrap;
  }
}
</style>
