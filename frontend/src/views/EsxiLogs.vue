<template>
  <div class="esxi-logs-page">
    <!-- Header -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-group">
          <svg class="header-icon" viewBox="0 0 24 24" fill="none">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="2"/>
            <polyline points="14 2 14 8 20 8" stroke="currentColor" stroke-width="2"/>
          </svg>
          <h1 class="page-title">ESXi 主机日志</h1>
        </div>
        <p class="page-subtitle">ESXi 主机系统日志 SSH 直连采集与分类</p>
      </div>
    </div>

    <!-- Filter -->
    <div class="filter-section">
      <div class="filter-card glass-card">
        <div class="filter-row">
          <div class="filter-group">
            <label class="filter-label">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
              时间范围
            </label>
            <div class="time-buttons">
              <button v-for="r in timeRanges" :key="r.hours" class="time-btn" :class="{ active: hours === r.hours }" @click="loadLogs(r.hours)">{{ r.label }}</button>
            </div>
          </div>
          <div class="filter-group">
            <label class="filter-label">分类</label>
            <div class="select-wrapper">
              <select v-model="filterCategory" @change="loadLogs()" class="glass-select">
                <option value="">全部</option>
                <option value="system">系统</option>
                <option value="virtualization">虚拟化</option>
                <option value="ssh">SSH</option>
                <option value="storage">存储</option>
                <option value="network">网络</option>
              </select>
              <svg class="select-arrow" viewBox="0 0 24 24" fill="none"><path d="M7 10l5 5 5-5" stroke="currentColor" stroke-width="2"/></svg>
            </div>
          </div>
          <div class="filter-group">
            <label class="filter-label">级别</label>
            <div class="select-wrapper">
              <select v-model="filterSeverity" @change="loadLogs()" class="glass-select">
                <option value="">全部</option>
                <option value="info">Info</option>
                <option value="warning">Warning</option>
                <option value="error">Error</option>
                <option value="critical">Critical</option>
              </select>
              <svg class="select-arrow" viewBox="0 0 24 24" fill="none"><path d="M7 10l5 5 5-5" stroke="currentColor" stroke-width="2"/></svg>
            </div>
          </div>
          <div class="filter-group">
            <label class="filter-label">主机</label>
            <div class="select-wrapper">
              <select v-model="filterHost" @change="loadLogs()" class="glass-select" :disabled="hosts.length === 0">
                <option value="">全部主机</option>
                <option v-for="h in hosts" :key="h" :value="h">{{ h }}</option>
              </select>
              <svg class="select-arrow" viewBox="0 0 24 24" fill="none"><path d="M7 10l5 5 5-5" stroke="currentColor" stroke-width="2"/></svg>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Stats -->
    <div class="stats-section">
      <div class="stat-card glass-card" :class="{ active: !filterSeverity }" @click="filterSeverity = ''; loadLogs()">
        <div class="stat-icon total"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/></svg></div>
        <div class="stat-content"><span class="stat-value">{{ total }}</span><span class="stat-label">全部</span></div>
      </div>
      <div class="stat-card glass-card" :class="{ active: filterSeverity === 'info' }" @click="filterSeverity = 'info'; loadLogs()">
        <div class="stat-icon info"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg></div>
        <div class="stat-content"><span class="stat-value">{{ severityCounts.info || 0 }}</span><span class="stat-label">Info</span></div>
      </div>
      <div class="stat-card glass-card" :class="{ active: filterSeverity === 'warning' }" @click="filterSeverity = 'warning'; loadLogs()">
        <div class="stat-icon warning"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/></svg></div>
        <div class="stat-content"><span class="stat-value">{{ severityCounts.warning || 0 }}</span><span class="stat-label">Warning</span></div>
      </div>
      <div class="stat-card glass-card" :class="{ active: filterSeverity === 'error' }" @click="filterSeverity = 'error'; loadLogs()">
        <div class="stat-icon error"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg></div>
        <div class="stat-content"><span class="stat-value">{{ severityCounts.error || 0 }}</span><span class="stat-label">Error</span></div>
      </div>
      <div class="stat-card glass-card" :class="{ active: filterSeverity === 'critical' }" @click="filterSeverity = 'critical'; loadLogs()">
        <div class="stat-icon critical"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg></div>
        <div class="stat-content"><span class="stat-value">{{ severityCounts.critical || 0 }}</span><span class="stat-label">Critical</span></div>
      </div>
    </div>

    <!-- Log Table -->
    <div class="table-section">
      <div class="table-card glass-card">
        <div class="table-header">
          <h3 class="table-title">日志列表</h3>
          <span class="table-info">{{ logs.length }} 条</span>
        </div>
        <div class="table-wrapper" v-if="logs.length > 0">
          <table class="glass-table">
            <thead>
              <tr>
                <th style="width:80px">级别</th>
                <th style="width:80px">分类</th>
                <th style="width:100px">服务</th>
                <th style="width:130px">主机</th>
                <th>消息</th>
                <th style="width:140px">来源文件</th>
                <th style="width:150px">时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="log in logs" :key="log.id" class="table-row" :class="log.severity">
                <td><span class="severity-badge" :class="log.severity">{{ log.severity }}</span></td>
                <td><span class="category-tag">{{ categoryName(log.category) }}</span></td>
                <td class="service-cell">{{ log.service }}</td>
                <td class="host-cell">{{ log.host_name || '--' }}</td>
                <td class="message-cell">{{ log.message }}</td>
                <td class="file-cell">{{ log.log_file || '--' }}</td>
                <td class="time-cell">{{ formatTime(log.event_time) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="empty-state" v-else>
          <div class="empty-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M9 12l2 2 4-4"/></svg>
          </div>
          <h3 class="empty-title">暂无日志数据</h3>
          <p class="empty-desc">等待下次采集后显示</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const logs = ref([])
const total = ref(0)
const severityCounts = ref({})
const hosts = ref([])
const hours = ref(24)
const filterCategory = ref('')
const filterSeverity = ref('')
const filterHost = ref('')

const timeRanges = [
  { hours: 1, label: '1小时' },
  { hours: 3, label: '3小时' },
  { hours: 24, label: '1天' },
  { hours: 72, label: '3天' },
  { hours: 168, label: '7天' },
]

const categoryName = (cat) => ({ system: '系统', virtualization: '虚拟化', ssh: 'SSH', storage: '存储', network: '网络' }[cat] || cat)

const formatTime = (t) => {
  if (!t) return '--'
  const d = new Date(t)
  return `${d.getMonth()+1}/${d.getDate()} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}:${String(d.getSeconds()).padStart(2,'0')}`
}

const loadLogs = async (h) => {
  if (h) hours.value = h
  try {
    const params = { hours: hours.value, limit: 500 }
    if (filterCategory.value) params.category = filterCategory.value
    if (filterSeverity.value) params.severity = filterSeverity.value
    if (filterHost.value) params.host_name = filterHost.value
    const res = await axios.get('/api/inspection/esxi-logs', { params })
    logs.value = res.data.data || []
    total.value = res.data.total || 0
    severityCounts.value = res.data.by_severity || {}
    const hostSet = new Set(logs.value.map(l => l.host_name).filter(Boolean))
    hosts.value = [...hostSet].sort()
  } catch (e) {
    console.error('Load ESXi logs failed:', e)
    logs.value = []
  }
}

onMounted(() => loadLogs(24))
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Rubik:wght@400;500;600;700&display=swap');
.esxi-logs-page { padding: 24px; max-width: 1400px; margin: 0 auto; font-family: 'Rubik', sans-serif; }

.page-header { margin-bottom: 24px; }
.title-group { display: flex; align-items: center; gap: 12px; }
.header-icon { width: 32px; height: 32px; color: #60a5fa; }
.page-title { font-size: 28px; font-weight: 700; color: #fff; margin: 0; }
.page-subtitle { font-size: 14px; color: rgba(255,255,255,0.5); margin: 4px 0 0 44px; }

/* Glass Card */
.glass-card { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; }

/* Filter */
.filter-section { margin-bottom: 20px; }
.filter-card { padding: 16px 20px; }
.filter-row { display: flex; gap: 20px; align-items: center; flex-wrap: wrap; }
.filter-group { display: flex; align-items: center; gap: 10px; }
.filter-label { font-size: 12px; color: rgba(255,255,255,0.5); display: flex; align-items: center; gap: 6px; white-space: nowrap; }
.filter-label svg { width: 16px; height: 16px; }
.time-buttons { display: flex; gap: 6px; }
.time-btn { padding: 6px 14px; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; color: rgba(255,255,255,0.5); font-size: 13px; cursor: pointer; transition: all 0.2s; font-family: 'Rubik', sans-serif; }
.time-btn:hover { background: rgba(255,255,255,0.1); }
.time-btn.active { background: rgba(106,95,193,0.2); border-color: rgba(106,95,193,0.3); color: #a78bfa; }
.select-wrapper { position: relative; }
.glass-select { padding: 6px 32px 6px 12px; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; color: #fff; font-size: 13px; font-family: 'Rubik', sans-serif; appearance: none; cursor: pointer; }
.glass-select option { background: #1f1633; color: #fff; }
.select-arrow { position: absolute; right: 10px; top: 50%; transform: translateY(-50%); width: 14px; height: 14px; color: rgba(255,255,255,0.4); pointer-events: none; }

/* Stats */
.stats-section { display: grid; grid-template-columns: repeat(5, 1fr); gap: 14px; margin-bottom: 20px; }
.stat-card { display: flex; align-items: center; gap: 14px; padding: 16px 20px; cursor: pointer; transition: all 0.2s; }
.stat-card:hover { background: rgba(255,255,255,0.06); }
.stat-card.active { border-color: rgba(106,95,193,0.4); background: rgba(106,95,193,0.1); }
.stat-icon { width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; }
.stat-icon svg { width: 20px; height: 20px; }
.stat-icon.total { background: rgba(96,165,250,0.15); color: #60a5fa; }
.stat-icon.info { background: rgba(96,165,250,0.15); color: #60a5fa; }
.stat-icon.warning { background: rgba(251,191,36,0.15); color: #fbbf24; }
.stat-icon.error { background: rgba(249,115,22,0.15); color: #f97316; }
.stat-icon.critical { background: rgba(248,113,113,0.15); color: #f87171; }
.stat-content { display: flex; flex-direction: column; gap: 2px; }
.stat-value { font-size: 20px; font-weight: 700; color: #fff; }
.stat-label { font-size: 12px; color: rgba(255,255,255,0.5); }

/* Table */
.table-section { margin-bottom: 24px; }
.table-card { padding: 24px; }
.table-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.06); }
.table-title { font-size: 16px; font-weight: 600; color: #fff; margin: 0; }
.table-info { font-size: 13px; color: rgba(255,255,255,0.4); }
.table-wrapper { overflow-x: auto; }
.glass-table { width: 100%; border-collapse: collapse; table-layout: auto; }
.glass-table th { padding: 11px 14px; background: rgba(255,255,255,0.06); color: rgba(255,255,255,0.6); font-size: 12px; font-weight: 500; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.08); white-space: nowrap; }
.glass-table td { padding: 11px 14px; color: #fff; font-size: 13px; border-bottom: 1px solid rgba(255,255,255,0.04); }
.table-row { transition: background 0.15s; }
.table-row:hover { background: rgba(255,255,255,0.03); }
.table-row.critical { background: rgba(248,113,113,0.06); }
.table-row.error { background: rgba(249,115,22,0.04); }

.severity-badge { padding: 3px 10px; border-radius: 6px; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.3px; }
.severity-badge.info { background: rgba(96,165,250,0.15); color: #60a5fa; }
.severity-badge.warning { background: rgba(251,191,36,0.15); color: #fbbf24; }
.severity-badge.error { background: rgba(249,115,22,0.15); color: #f97316; }
.severity-badge.critical { background: rgba(248,113,113,0.2); color: #f87171; }

.category-tag { padding: 3px 10px; background: rgba(106,95,193,0.15); border-radius: 6px; font-size: 11px; color: #a78bfa; }
.service-cell { font-family: monospace; font-size: 12px; color: rgba(255,255,255,0.6); }
.host-cell { font-weight: 500; }
.message-cell { max-width: 400px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.file-cell { font-family: monospace; font-size: 11px; color: rgba(255,255,255,0.4); max-width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.time-cell { font-size: 12px; color: rgba(255,255,255,0.4); white-space: nowrap; }

.empty-state { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 60px 20px; }
.empty-icon { width: 48px; height: 48px; background: rgba(194,239,78,0.15); border-radius: 12px; display: flex; align-items: center; justify-content: center; color: #c2ef4e; }
.empty-icon svg { width: 24px; height: 24px; }
.empty-title { font-size: 16px; font-weight: 600; color: #fff; margin: 0; }
.empty-desc { font-size: 13px; color: rgba(255,255,255,0.4); margin: 0; }
</style>
