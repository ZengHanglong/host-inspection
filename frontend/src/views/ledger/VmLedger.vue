<template>
  <div class="vm-ledger-page">
    <div class="page-header">
      <div class="header-content">
        <div class="title-group">
          <svg class="header-icon" viewBox="0 0 24 24" fill="none"><rect x="2" y="3" width="20" height="14" rx="2" stroke="currentColor" stroke-width="2"/><path d="M8 21h8M12 17v4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
          <h1 class="page-title">虚拟机台账</h1>
        </div>
        <p class="page-subtitle">管理所有虚拟机资产信息</p>
      </div>
      <div class="header-actions">
        <button class="export-btn" @click="exportData">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>
          <span>导出台账</span>
        </button>
      </div>
    </div>

    <!-- 搜索筛选 -->
    <div class="filter-section">
      <div class="filter-card">
        <div class="search-box">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="search-icon"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          <input class="search-input" v-model="searchQuery" :placeholder="searchMode === 'fuzzy' ? '模糊搜索：名称、IP、负责人...' : '精准搜索：完整名称或IP'" />
          <button class="search-mode-btn" @click="searchMode = searchMode === 'fuzzy' ? 'exact' : 'fuzzy'">{{ searchMode === 'fuzzy' ? '模糊' : '精准' }}</button>
        </div>
        <div class="filter-row">
          <div class="filter-group">
            <label class="filter-label">平台</label>
            <select v-model="filterPlatform" class="filter-select"><option value="">全部</option><option value="vmware">VMware</option><option value="smartx">SmartX</option></select>
          </div>
          <div class="filter-group">
            <label class="filter-label">环境</label>
            <select v-model="filterEnvironment" class="filter-select"><option value="">全部</option><option value="生产">生产</option><option value="灾备">灾备</option><option value="测试">测试</option><option value="临时">临时</option></select>
          </div>
          <div class="filter-group">
            <label class="filter-label">快照</label>
            <select v-model="filterSnapshot" class="filter-select"><option value="">全部</option><option value="true">有快照</option><option value="false">无快照</option></select>
          </div>
          <div class="filter-group"><span class="result-count">共 {{ filteredData.length }} 台</span></div>
        </div>
      </div>
    </div>

    <!-- 统计 -->
    <div class="stats-section">
      <div class="stat-card" v-for="s in statCards" :key="s.key">
        <div class="stat-icon" :class="s.key"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path :d="s.icon"/></svg></div>
        <div class="stat-body">
          <span class="stat-value">{{ s.value }} <small v-if="s.unit">{{ s.unit }}</small></span>
          <span class="stat-label">{{ s.label }}</span>
        </div>
      </div>
    </div>

    <!-- 表格 -->
    <div class="table-section">
      <div class="table-card">
        <div class="table-wrapper" v-if="filteredData.length > 0">
          <table class="glass-table">
            <thead>
              <tr>
                <th>平台</th><th>集群</th><th>虚拟机名称</th><th>IP</th><th>CPU</th><th>内存</th><th>磁盘</th><th>环境</th><th>快照</th><th>电源</th><th>备注</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, idx) in filteredData" :key="idx" class="table-row" @click="openDetail(row)">
                <td><span class="platform-badge" :class="row.platform">{{ row.platform }}</span></td>
                <td>{{ row.cluster }}</td>
                <td class="vm-name-cell">{{ row.vm_name }}</td>
                <td><span class="ip-badge">{{ row.ip }}</span></td>
                <td>{{ row.cpu }}核</td>
                <td>{{ row.memory_gb }}GB</td>
                <td>{{ row.disk_gb }}GB</td>
                <td><span class="env-badge" :class="getEnvClass(row.environment)">{{ row.environment }}</span></td>
                <td><span class="snapshot-badge" :class="{ has: row.has_snapshot }">{{ row.has_snapshot ? row.snapshot_days + '天' : '无' }}</span></td>
                <td><span class="power-badge" :class="row.power_state === 'poweredOn' ? 'on' : 'off'">{{ row.power_state === 'poweredOn' ? '运行' : '关机' }}</span></td>
                <td class="note-cell">{{ row.note || '-' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="empty-state" v-else>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M8 12h8M12 8v8"/></svg>
          <h3>暂无数据</h3><p>{{ emptyDesc }}</p>
        </div>
      </div>
    </div>

    <!-- 弹窗 -->
    <Teleport to="body">
      <div class="vm-modal-overlay" v-if="showModal" @click.self="showModal = false">
        <div class="vm-modal">
          <div class="vm-modal-header">
            <div class="vm-modal-title">
              <div class="vm-modal-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/></svg>
              </div>
              <div>
                <h3>{{ modalVm.vm_name }}</h3>
                <p>{{ modalVm.platform_name }} · {{ modalVm.cluster }}</p>
              </div>
            </div>
            <button class="vm-modal-close" @click="showModal = false">&times;</button>
          </div>

          <div class="vm-modal-chips">
            <span class="vm-chip"><b>平台</b> {{ modalVm.platform_name }}</span>
            <span class="vm-chip"><b>集群</b> {{ modalVm.cluster }}</span>
            <span class="vm-chip"><b>IP</b> <code>{{ modalVm.ip }}</code></span>
            <span class="vm-chip"><b>环境</b> <span :class="'env-' + getEnvClass(modalVm.environment)">{{ modalVm.environment }}</span></span>
            <span class="vm-chip"><b>电源</b> <span :class="modalVm.power_state === 'poweredOn' ? 'text-green' : 'text-red'">{{ modalVm.power_state === 'poweredOn' ? '运行中' : '已关机' }}</span></span>
            <span class="vm-chip"><b>快照</b> {{ modalVm.has_snapshot ? modalVm.snapshot_days + '天' : '无' }}</span>
          </div>

          <div class="vm-modal-grid">
            <!-- 资源分配列表 -->
            <div class="vm-modal-card resource-list-card">
              <div class="vmc-top"><span class="vmc-label">资源分配</span></div>
              <div class="resource-list">
                <div class="resource-row">
                  <span class="rl-label">CPU</span>
                  <span class="rl-value">{{ modalVm.cpu }} 核</span>
                </div>
                <div class="resource-row">
                  <span class="rl-label">内存</span>
                  <span class="rl-value">{{ modalVm.memory_gb }} GB</span>
                </div>
                <div class="resource-row">
                  <span class="rl-label">磁盘</span>
                  <span class="rl-value">{{ modalVm.disk_gb }} GB ({{ modalVm.disk_tb }} TB)</span>
                </div>
              </div>
            </div>
            <!-- 配置信息 -->
            <div class="vm-modal-card config-card">
              <div class="vmc-top">
                <span class="vmc-label">配置</span>
                <button class="edit-btn" @click="toggleEdit" v-if="!editing">{{ editing ? '取消' : '编辑' }}</button>
              </div>
              <div class="vmc-info" v-if="!editing">
                <span>系统: <b :class="modalVm.system === '未标记' ? 'text-dim' : ''">{{ modalVm.system }}</b></span>
                <span>功能: <b :class="modalVm.function === '未标记' ? 'text-dim' : ''">{{ modalVm.function }}</b></span>
                <span>负责人: <b :class="modalVm.owner === '未标记' ? 'text-dim' : ''">{{ modalVm.owner }}</b></span>
              </div>
              <div class="vmc-edit" v-else>
                <div class="edit-field">
                  <label>系统</label>
                  <input v-model="editForm.system" placeholder="如: CentOS, Windows" />
                </div>
                <div class="edit-field">
                  <label>功能</label>
                  <input v-model="editForm.function" placeholder="如: 数据库, Web服务" />
                </div>
                <div class="edit-field">
                  <label>负责人</label>
                  <input v-model="editForm.owner" placeholder="如: 张三" />
                </div>
                <div class="edit-actions">
                  <button class="edit-save" @click="saveMetadata">保存</button>
                  <button class="edit-cancel" @click="editing = false">取消</button>
                </div>
              </div>
            </div>
          </div>

          <!-- 趋势图 -->
          <div class="vm-modal-chart-section">
            <div class="chart-header">
              <span class="chart-title">资源使用率趋势</span>
              <div class="chart-range-btns">
                <button v-for="r in chartRanges" :key="r.hours" :class="{ active: chartHours === r.hours }" @click="loadVmMetrics(r.hours)">{{ r.label }}</button>
              </div>
            </div>
            <div class="chart-container" ref="chartRef"></div>
            <div class="chart-empty" v-if="!chartLoading && chartData.length === 0">
              <span>暂无历史数据，等待下次采集后显示</span>
            </div>
            <div class="chart-loading" v-if="chartLoading">
              <span>加载中...</span>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import axios from 'axios'
import * as echarts from 'echarts'

const data = ref({ total: 0, statistics: {}, data: [] })
const pageStatus = ref('loading')
const pageMessage = ref('')
const animatedTotal = ref(0)
const searchQuery = ref('')
const searchMode = ref('fuzzy')
const filterPlatform = ref('')
const filterEnvironment = ref('')
const filterSnapshot = ref('')

const showModal = ref(false)
const modalVm = ref({})
const editing = ref(false)
const editForm = ref({ system: '', function: '', owner: '' })

const chartRef = ref(null)
let chartInstance = null
const chartHours = ref(24)
const chartData = ref([])
const chartLoading = ref(false)
const chartRanges = [
  { hours: 1, label: '1小时' },
  { hours: 3, label: '3小时' },
  { hours: 24, label: '1天' },
  { hours: 72, label: '3天' },
  { hours: 168, label: '7天' },
]

let cachedData = null
let cacheTime = 0
const CACHE_TTL = 60000

const statCards = computed(() => [
  { key: 'total', label: '总虚拟机', value: animatedTotal.value, icon: 'M4 6h16M4 10h16M4 14h16M4 18h16' },
  { key: 'cpu', label: 'CPU 核数', value: data.value.statistics?.total_cpu_cores || 0, icon: 'M9 3v18M15 3v18M3 9h18M3 15h18' },
  { key: 'memory', label: '总内存', value: data.value.statistics?.total_memory_gb || 0, unit: 'GB', icon: 'M6 4v16M10 4v16M14 4v16M18 4v16' },
  { key: 'disk', label: '总磁盘', value: data.value.statistics?.total_disk_gb || 0, unit: 'GB', icon: 'M21 12a9 9 0 11-18 0 9 9 0 0118 0z' },
  { key: 'snapshot', label: '有快照', value: data.value.statistics?.with_snapshot_count || 0, icon: 'M4 4h16v16H4zM12 8v8M8 12h8' },
])

const emptyDesc = computed(() => {
  if (pageStatus.value === 'no_credentials') return '未配置可用的 API 凭证'
  if (searchQuery.value) return '没有匹配的虚拟机'
  return pageMessage.value || '当前没有虚拟机数据'
})

const filteredData = computed(() => {
  let rows = data.value.data || []
  if (filterPlatform.value) rows = rows.filter(r => r.platform === filterPlatform.value)
  if (filterEnvironment.value) rows = rows.filter(r => r.environment === filterEnvironment.value)
  if (filterSnapshot.value === 'true') rows = rows.filter(r => r.has_snapshot)
  if (filterSnapshot.value === 'false') rows = rows.filter(r => !r.has_snapshot)
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    if (searchMode.value === 'fuzzy') {
      rows = rows.filter(r => [r.vm_name, r.ip, r.owner, r.cluster, r.note].some(f => (f || '').toLowerCase().includes(q)))
    } else {
      rows = rows.filter(r => (r.vm_name || '').toLowerCase() === q || (r.ip || '').toLowerCase() === q)
    }
  }
  return rows
})

const getEnvClass = (env) => ({ '生产': 'prod', '灾备': 'dr', '测试': 'test', '临时': 'temp' }[env] || 'default')

const openDetail = async (row) => {
  modalVm.value = row
  editing.value = false
  showModal.value = true
  chartData.value = []
  await nextTick()
  loadVmMetrics(24)
}

const toggleEdit = () => {
  editForm.value = {
    system: modalVm.value.system === '未标记' ? '' : modalVm.value.system,
    function: modalVm.value.function === '未标记' ? '' : modalVm.value.function,
    owner: modalVm.value.owner === '未标记' ? '' : modalVm.value.owner,
  }
  editing.value = true
}

const saveMetadata = async () => {
  try {
    const platform = modalVm.value.platform
    const vmName = modalVm.value.vm_name
    await axios.put(`/api/ledger/vm/metadata/${platform}/${encodeURIComponent(vmName)}`, editForm.value)
    // Update local data
    if (editForm.value.system) modalVm.value.system = editForm.value.system
    if (editForm.value.function) modalVm.value.function = editForm.value.function
    if (editForm.value.owner) modalVm.value.owner = editForm.value.owner
    // Also update in the main data array
    const idx = data.value.data.findIndex(r => r.platform === platform && r.vm_name === vmName)
    if (idx >= 0) {
      if (editForm.value.system) data.value.data[idx].system = editForm.value.system
      if (editForm.value.function) data.value.data[idx].function = editForm.value.function
      if (editForm.value.owner) data.value.data[idx].owner = editForm.value.owner
    }
    editing.value = false
    alert('保存成功')
  } catch (e) {
    alert('保存失败: ' + (e.response?.data?.detail || e.message))
  }
}

const animateValue = (target, ref) => {
  const start = ref.value
  const diff = target - start
  if (diff === 0) return
  const duration = 800
  const startTime = Date.now()
  const tick = () => {
    const elapsed = Date.now() - startTime
    const progress = Math.min(elapsed / duration, 1)
    ref.value = Math.round(start + diff * progress)
    if (progress < 1) requestAnimationFrame(tick)
  }
  requestAnimationFrame(tick)
}

const loadVmMetrics = async (hours) => {
  chartHours.value = hours
  chartLoading.value = true
  try {
    const vmName = modalVm.value.vm_name
    const res = await axios.get(`/api/ledger/vm/metrics/${encodeURIComponent(vmName)}?hours=${hours}`)
    chartData.value = res.data.data || []
    renderChart()
  } catch (e) {
    chartData.value = []
  } finally {
    chartLoading.value = false
  }
}

const renderChart = () => {
  if (!chartRef.value) return
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }
  const data = chartData.value
  if (!data.length) {
    chartInstance.clear()
    return
  }

  const timestamps = data.map(d => {
    const t = new Date(d.timestamp)
    return `${t.getMonth()+1}/${t.getDate()} ${String(t.getHours()).padStart(2,'0')}:${String(t.getMinutes()).padStart(2,'0')}`
  })

  chartInstance.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(20,15,40,0.95)',
      borderColor: 'rgba(255,255,255,0.1)',
      textStyle: { color: '#fff', fontSize: 12 },
      formatter: (params) => {
        let html = `<div style="font-weight:600;margin-bottom:4px">${params[0].axisValue}</div>`
        params.forEach(p => {
          html += `<div>${p.marker} ${p.seriesName}: <b>${p.value}</b></div>`
        })
        return html
      }
    },
    legend: {
      data: ['CPU', '内存', '磁盘'],
      textStyle: { color: 'rgba(255,255,255,0.5)', fontSize: 11 },
      top: 0,
      right: 0,
    },
    grid: { left: 40, right: 16, top: 30, bottom: 30 },
    xAxis: {
      type: 'category',
      data: timestamps,
      axisLabel: { color: 'rgba(255,255,255,0.4)', fontSize: 10, rotate: 30 },
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: 'rgba(255,255,255,0.4)', fontSize: 10 },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
    },
    series: [
      { name: 'CPU', type: 'line', data: data.map(d => d.cpu), smooth: true, lineStyle: { width: 2 }, itemStyle: { color: '#818cf8' }, showSymbol: false },
      { name: '内存', type: 'line', data: data.map(d => d.memory), smooth: true, lineStyle: { width: 2 }, itemStyle: { color: '#34d399' }, showSymbol: false },
      { name: '磁盘', type: 'line', data: data.map(d => d.storage), smooth: true, lineStyle: { width: 2 }, itemStyle: { color: '#fbbf24' }, showSymbol: false },
    ],
  })
}

const loadData = async (force = false) => {
  const now = Date.now()
  if (!force && cachedData && (now - cacheTime) < CACHE_TTL) {
    data.value = cachedData
    animateValue(cachedData.total, animatedTotal)
    return
  }
  try {
    const response = await axios.get('/api/ledger/vm')
    pageStatus.value = response.data.status || 'unknown'
    pageMessage.value = response.data.message || ''
    data.value = response.data
    cachedData = response.data
    cacheTime = now
    animateValue(data.value.total, animatedTotal)
  } catch (e) {
    pageStatus.value = 'error'
    pageMessage.value = '虚拟机台账加载失败'
  }
}

const exportData = () => {
  const rows = filteredData.value
  if (!rows.length) { alert('没有数据可导出'); return }
  const csv = ['平台,集群,虚拟机名称,IP,CPU,内存,磁盘,环境,快照,电源,备注']
  rows.forEach(r => csv.push([r.platform, r.cluster, r.vm_name, r.ip, r.cpu, r.memory_gb, r.disk_gb, r.environment, r.has_snapshot ? r.snapshot_days + '天' : '无', r.power_state === 'poweredOn' ? '运行' : '关机', r.note || ''].join(',')))
  const blob = new Blob(['﻿' + csv.join('\n')], { type: 'text/csv;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `虚拟机台账_${new Date().toISOString().split('T')[0]}.csv`
  a.click()
}

watch(showModal, (val) => {
  if (val) {
    nextTick(() => {
      if (chartInstance) chartInstance.resize()
    })
  }
})

onMounted(() => loadData())
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Rubik:wght@400;500;600;700&display=swap');
.vm-ledger-page { padding: 24px; max-width: 1400px; margin: 0 auto; font-family: 'Rubik', sans-serif; }

/* Header */
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; }
.page-title { font-size: 28px; font-weight: 700; color: #fff; margin: 0; }
.page-subtitle { font-size: 14px; color: rgba(255,255,255,0.5); margin: 4px 0 0 0; }
.header-icon { width: 32px; height: 32px; color: #60a5fa; }
.export-btn { display: flex; align-items: center; gap: 8px; padding: 10px 16px; background: rgba(96,165,250,0.15); border: 1px solid rgba(96,165,250,0.25); border-radius: 10px; color: #60a5fa; cursor: pointer; font-size: 13px; font-weight: 500; transition: all 0.2s; }
.export-btn:hover { background: rgba(96,165,250,0.25); }
.export-btn svg { width: 16px; height: 16px; }

/* Filter */
.filter-section { margin-bottom: 20px; }
.filter-card { padding: 16px 20px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; }
.search-box { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; padding: 10px 14px; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1); border-radius: 10px; }
.search-icon { width: 18px; height: 18px; color: rgba(255,255,255,0.4); flex-shrink: 0; }
.search-input { flex: 1; background: none; border: none; color: #fff; font-size: 14px; font-family: 'Rubik', sans-serif; outline: none; }
.search-input::placeholder { color: rgba(255,255,255,0.3); }
.search-mode-btn { padding: 4px 10px; background: rgba(106,95,193,0.2); border: 1px solid rgba(106,95,193,0.3); border-radius: 6px; color: #a78bfa; font-size: 12px; cursor: pointer; }
.filter-row { display: flex; gap: 16px; align-items: center; flex-wrap: wrap; }
.filter-group { display: flex; align-items: center; gap: 8px; }
.filter-label { font-size: 12px; color: rgba(255,255,255,0.5); }
.filter-select { padding: 6px 28px 6px 10px; background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.12); border-radius: 8px; color: #fff; font-size: 13px; font-family: 'Rubik', sans-serif; appearance: none; background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='10' viewBox='0 0 24 24' fill='none' stroke='rgba(255,255,255,0.5)' stroke-width='2'%3E%3Cpath d='M7 10l5 5 5-5'/%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: right 8px center; cursor: pointer; }
.filter-select option { background: #1f1633; color: #fff; }
.result-count { font-size: 13px; color: rgba(255,255,255,0.5); }

/* Stats */
.stats-section { display: grid; grid-template-columns: repeat(5, 1fr); gap: 14px; margin-bottom: 20px; }
.stat-card { display: flex; align-items: center; gap: 14px; padding: 18px 20px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; transition: all 0.2s; }
.stat-card:hover { background: rgba(255,255,255,0.06); border-color: rgba(255,255,255,0.12); }
.stat-icon { width: 44px; height: 44px; border-radius: 12px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.stat-icon svg { width: 22px; height: 22px; }
.stat-icon.total { background: rgba(96,165,250,0.15); color: #60a5fa; }
.stat-icon.cpu { background: rgba(129,140,248,0.15); color: #818cf8; }
.stat-icon.memory { background: rgba(52,211,153,0.15); color: #34d399; }
.stat-icon.disk { background: rgba(251,191,36,0.15); color: #fbbf24; }
.stat-icon.snapshot { background: rgba(248,113,113,0.15); color: #f87171; }
.stat-body { display: flex; flex-direction: column; gap: 2px; }
.stat-value { font-size: 22px; font-weight: 700; color: #fff; line-height: 1.2; }
.stat-value small { font-size: 13px; font-weight: 400; color: rgba(255,255,255,0.5); }
.stat-label { font-size: 12px; color: rgba(255,255,255,0.45); }

/* Table */
.table-section { margin-bottom: 24px; }
.table-card { padding: 20px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; }
.table-wrapper { overflow-x: auto; }
.glass-table { width: 100%; border-collapse: collapse; table-layout: auto; }
.glass-table th { padding: 11px 14px; background: rgba(255,255,255,0.06); color: rgba(255,255,255,0.6); font-size: 12px; font-weight: 500; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.08); white-space: nowrap; position: sticky; top: 0; }
.glass-table td { padding: 11px 14px; color: #fff; font-size: 13px; border-bottom: 1px solid rgba(255,255,255,0.04); white-space: nowrap; }
.table-row { cursor: pointer; transition: background 0.15s; }
.table-row:hover { background: rgba(255,255,255,0.04); }

.platform-badge { padding: 3px 10px; border-radius: 6px; font-size: 11px; font-weight: 500; }
.platform-badge.vmware { background: rgba(96,165,250,0.2); color: #60a5fa; }
.platform-badge.smartx { background: rgba(52,211,153,0.2); color: #34d399; }
.vm-name-cell { font-weight: 500; }
.ip-badge { padding: 3px 8px; background: rgba(255,255,255,0.06); border-radius: 6px; font-size: 12px; font-family: monospace; }
.env-badge { padding: 3px 10px; border-radius: 6px; font-size: 11px; font-weight: 500; display: inline-block; }
.env-badge.prod { background: rgba(194,239,78,0.15); color: #c2ef4e; }
.env-badge.dr { background: rgba(96,165,250,0.15); color: #60a5fa; }
.env-badge.test { background: rgba(167,139,250,0.15); color: #a78bfa; }
.env-badge.temp { background: rgba(251,191,36,0.15); color: #fbbf24; }
.snapshot-badge { padding: 3px 10px; border-radius: 6px; font-size: 11px; }
.snapshot-badge.has { background: rgba(248,113,113,0.15); color: #f87171; }
.power-badge { padding: 3px 10px; border-radius: 6px; font-size: 11px; }
.power-badge.on { background: rgba(194,239,78,0.15); color: #c2ef4e; }
.power-badge.off { background: rgba(248,113,113,0.15); color: #f87171; }
.note-cell { max-width: 150px; overflow: hidden; text-overflow: ellipsis; color: rgba(255,255,255,0.4); }

.empty-state { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 60px 20px; color: rgba(255,255,255,0.4); }
.empty-state svg { width: 40px; height: 40px; }
.empty-state h3 { font-size: 16px; color: #fff; margin: 0; }
.empty-state p { font-size: 13px; margin: 0; }

/* Modal */
.vm-modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.6); backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center; z-index: 9999; }
.vm-modal { background: #1c1735; border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; width: 640px; max-height: 85vh; overflow-y: auto; box-shadow: 0 20px 60px rgba(0,0,0,0.5); padding: 24px; }
.vm-modal-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; }
.vm-modal-title { display: flex; align-items: center; gap: 14px; }
.vm-modal-icon { width: 42px; height: 42px; background: rgba(96,165,250,0.15); border-radius: 12px; display: flex; align-items: center; justify-content: center; color: #60a5fa; flex-shrink: 0; }
.vm-modal-icon svg { width: 22px; height: 22px; }
.vm-modal-title h3 { font-size: 18px; font-weight: 600; color: #fff; margin: 0; }
.vm-modal-title p { font-size: 13px; color: rgba(255,255,255,0.4); margin: 3px 0 0 0; }
.vm-modal-close { background: rgba(255,255,255,0.08); border: none; color: rgba(255,255,255,0.5); font-size: 22px; cursor: pointer; width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; }
.vm-modal-close:hover { background: rgba(255,255,255,0.15); color: #fff; }

.vm-modal-chips { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 20px; }
.vm-chip { padding: 8px 14px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; font-size: 13px; color: rgba(255,255,255,0.7); }
.vm-chip b { color: rgba(255,255,255,0.4); font-weight: 500; margin-right: 6px; }
.vm-chip code { font-family: monospace; color: #818cf8; }
.env-prod { color: #c2ef4e; }
.env-dr { color: #60a5fa; }
.env-test { color: #a78bfa; }
.env-temp { color: #fbbf24; }
.text-green { color: #c2ef4e; }
.text-red { color: #f87171; }

.vm-modal-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.vm-modal-card { padding: 18px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; }
.vmc-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.vmc-label { font-size: 12px; font-weight: 600; color: rgba(255,255,255,0.5); text-transform: uppercase; letter-spacing: 0.3px; }
.vmc-value { font-size: 22px; font-weight: 700; color: #fff; }
.vmc-value small { font-size: 13px; font-weight: 400; color: rgba(255,255,255,0.5); }
.resource-list-card { grid-column: span 1; }
.resource-list { display: flex; flex-direction: column; gap: 0; }
.resource-row { display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.06); }
.resource-row:last-child { border-bottom: none; }
.rl-label { font-size: 13px; color: rgba(255,255,255,0.5); }
.rl-value { font-size: 14px; font-weight: 600; color: #fff; }
.vmc-info { display: flex; flex-direction: column; gap: 8px; }
.vmc-info span { font-size: 13px; color: rgba(255,255,255,0.5); }
.vmc-info b { color: #fff; font-weight: 500; }
.text-dim { color: rgba(255,255,255,0.3) !important; }

.config-card { grid-column: span 2; }
.edit-btn { padding: 3px 10px; background: rgba(106,95,193,0.2); border: 1px solid rgba(106,95,193,0.3); border-radius: 6px; color: #a78bfa; font-size: 11px; cursor: pointer; }
.edit-btn:hover { background: rgba(106,95,193,0.3); }

.vmc-edit { display: flex; flex-direction: column; gap: 10px; margin-top: 4px; }
.edit-field { display: flex; flex-direction: column; gap: 4px; }
.edit-field label { font-size: 11px; color: rgba(255,255,255,0.4); text-transform: uppercase; letter-spacing: 0.3px; }
.edit-field input { padding: 8px 12px; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; color: #fff; font-size: 13px; font-family: 'Rubik', sans-serif; outline: none; }
.edit-field input:focus { border-color: #6a5fc1; }
.edit-field input::placeholder { color: rgba(255,255,255,0.25); }
.edit-actions { display: flex; gap: 8px; margin-top: 4px; }
.edit-save { padding: 8px 16px; background: #6a5fc1; border: none; border-radius: 8px; color: #fff; font-size: 13px; font-weight: 500; cursor: pointer; }
.edit-save:hover { background: #7a6fd1; }
.edit-cancel { padding: 8px 16px; background: rgba(255,255,255,0.08); border: none; border-radius: 8px; color: rgba(255,255,255,0.6); font-size: 13px; cursor: pointer; }
.edit-cancel:hover { background: rgba(255,255,255,0.12); }

/* Chart */
.vm-modal-chart-section { margin-top: 20px; }
.chart-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.chart-title { font-size: 14px; font-weight: 600; color: rgba(255,255,255,0.7); }
.chart-range-btns { display: flex; gap: 6px; }
.chart-range-btns button { padding: 4px 12px; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; color: rgba(255,255,255,0.5); font-size: 12px; cursor: pointer; transition: all 0.15s; }
.chart-range-btns button:hover { background: rgba(255,255,255,0.1); }
.chart-range-btns button.active { background: rgba(106,95,193,0.25); border-color: rgba(106,95,193,0.4); color: #a78bfa; }
.chart-container { width: 100%; height: 220px; }
.chart-empty, .chart-loading { display: flex; align-items: center; justify-content: center; height: 120px; color: rgba(255,255,255,0.3); font-size: 13px; }

@media (max-width: 1200px) {
  .stats-section { grid-template-columns: repeat(3, 1fr); }
  .vm-modal-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 768px) {
  .stats-section { grid-template-columns: repeat(2, 1fr); }
  .vm-modal-grid { grid-template-columns: 1fr; }
  .vm-modal { width: 95%; }
}
</style>
