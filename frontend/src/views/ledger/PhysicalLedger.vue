<template>
  <div class="physical-ledger-page">
    <!-- Header Section -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-group">
          <div class="header-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="4" y="4" width="16" height="16" rx="2"/>
              <rect x="9" y="9" width="6" height="6"/>
              <path d="M9 1v3M15 1v3M9 20v3M15 20v3"/>
            </svg>
          </div>
          <div class="title-text">
            <h1 class="page-title">PHYSICAL LEDGER</h1>
            <p class="page-subtitle">Manage all physical server assets</p>
          </div>
        </div>
      </div>
      <div class="header-actions">
        <button class="btn-glass" @click="exportData">
          <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/>
          </svg>
          <span class="btn-text">EXPORT LEDGER</span>
        </button>
      </div>
    </div>

    <!-- Filter Section -->
    <div class="filter-section">
      <div class="filter-card">
        <div class="filter-group">
          <label class="filter-label">
            <svg class="filter-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="4" y="4" width="16" height="16" rx="2"/>
            </svg>
            <span class="label-text">PLATFORM</span>
          </label>
          <div class="select-wrapper">
            <select v-model="filterPlatform" @change="loadData" class="glass-select">
              <option value="">All Platforms</option>
              <option value="vmware">VMware</option>
              <option value="smartx">SmartX</option>
              <option value="huawei_cloud">Huawei Cloud</option>
              <option value="sangfor_cloud">Sangfor</option>
              <option value="tdsql">TDSQL</option>
              <option value="storage">Storage</option>
            </select>
            <svg class="select-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M7 10l5 5 5-5"/>
            </svg>
          </div>
        </div>
      </div>
    </div>

    <!-- Stats Section -->
    <div class="stats-section">
      <div class="stat-card">
        <div class="stat-icon total">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="4" y="4" width="16" height="16" rx="2"/>
            <rect x="9" y="9" width="6" height="6"/>
          </svg>
        </div>
        <div class="stat-content">
          <span class="stat-value">{{ animatedTotal }}</span>
          <span class="stat-label">TOTAL HOSTS</span>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon cpu">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="4" y="4" width="16" height="16" rx="2"/>
            <rect x="9" y="9" width="6" height="6"/>
          </svg>
        </div>
        <div class="stat-content">
          <span class="stat-value">{{ data.statistics?.total_cpu_cores || 0 }}</span>
          <span class="stat-label">CPU CORES</span>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon memory">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M4 4h16v16H4z"/>
          </svg>
        </div>
        <div class="stat-content">
          <span class="stat-value">{{ data.statistics?.total_memory_gb || 0 }}</span>
          <span class="stat-unit">GB</span>
          <span class="stat-label">TOTAL MEMORY</span>
        </div>
      </div>
    </div>

    <!-- Platform Distribution -->
    <div class="distribution-section" v-if="data.statistics?.by_platform">
      <div class="distribution-card">
        <div class="distribution-header">
          <svg viewBox="0 0 24 24" fill="none" class="dist-icon" stroke="currentColor" stroke-width="2">
            <path d="M12 2L2 7l10 5 10-5-10-5z"/>
            <path d="M2 17l10 5 10-5"/>
          </svg>
          <h3 class="distribution-title">PLATFORM DISTRIBUTION</h3>
        </div>
        <div class="platform-grid">
          <div v-for="(count, platform) in data.statistics?.by_platform" :key="platform" class="platform-item">
            <span class="platform-badge" :class="platform">{{ platform }}</span>
            <span class="platform-count">{{ count }} hosts</span>
            <div class="platform-bar">
              <div class="platform-progress" :style="{ width: count / data.total * 100 + '%' }"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Table Section -->
    <div class="table-section">
      <div class="table-card">
        <div class="table-wrapper" v-if="data.data && data.data.length > 0">
          <table class="glass-table">
            <thead>
              <tr>
                <th>PLATFORM</th>
                <th>NAME</th>
                <th>CLUSTER</th>
                <th>HOST NAME</th>
                <th>IP ADDRESS</th>
                <th>MGMT IP</th>
                <th>CPU</th>
                <th>MEMORY</th>
                <th>TYPE</th>
                <th>UPTIME</th>
                <th>STATUS</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, index) in data.data" :key="index" class="table-row" :class="{ selected: selectedHost?.host_name === row.host_name }" @click="selectedHost = selectedHost?.host_name === row.host_name ? null : row">
                <td>
                  <span class="platform-badge" :class="row.platform">{{ row.platform }}</span>
                </td>
                <td class="name-cell">{{ row.platform_name }}</td>
                <td class="cluster-cell">{{ row.cluster }}</td>
                <td class="host-cell">{{ row.host_name }}</td>
                <td>
                  <span class="ip-badge">{{ row.ip }}</span>
                </td>
                <td>
                  <span class="mgmt-badge">{{ row.mgmt_ip }}</span>
                </td>
                <td class="resource-cell">{{ row.cpu }}</td>
                <td class="resource-cell">{{ row.memory_gb }} GB</td>
                <td>
                  <span class="type-tag">{{ row.host_type }}</span>
                </td>
                <td>
                  <div class="uptime-display">
                    <span class="uptime-value">{{ row.uptime_days }}</span>
                    <span class="uptime-unit">days</span>
                  </div>
                </td>
                <td>
                  <span class="status-badge" :class="getStatusClass(row.status)">{{ row.status }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 物理机详情面板 -->
        <div class="detail-panel" v-if="selectedHost">
          <div class="detail-header">
            <div class="detail-title-group">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="detail-icon">
                <rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/>
              </svg>
              <div>
                <h3>{{ selectedHost.host_name }}</h3>
                <p class="detail-subtitle">{{ selectedHost.platform_name }} · {{ selectedHost.cluster }} · {{ selectedHost.host_type }}</p>
              </div>
            </div>
            <button class="close-btn" @click="selectedHost = null">&times;</button>
          </div>

          <!-- 基本信息行 -->
          <div class="info-row">
            <div class="info-chip"><span class="chip-label">IP</span><span class="chip-value">{{ selectedHost.ip }}</span></div>
            <div class="info-chip"><span class="chip-label">管理IP</span><span class="chip-value">{{ selectedHost.mgmt_ip }}</span></div>
            <div class="info-chip"><span class="chip-label">状态</span><span class="chip-value" :class="getStatusClass(selectedHost.status)">{{ selectedHost.status }}</span></div>
            <div class="info-chip"><span class="chip-label">运行</span><span class="chip-value">{{ selectedHost.uptime_days }} 天</span></div>
          </div>

          <!-- 资源卡片 -->
          <div class="resource-grid">
            <div class="resource-card cpu">
              <div class="resource-header">
                <span class="resource-label">CPU</span>
                <span class="resource-value">{{ selectedHost.cpu }} <small>核</small></span>
              </div>
              <div class="resource-bar"><div class="resource-bar-fill cpu" :style="{ width: Math.min(selectedHost.cpu / 128 * 100, 100) + '%' }"></div></div>
              <div class="resource-desc">分配: {{ selectedHost.cpu }} vCPU · 容量: 128 核</div>
            </div>
            <div class="resource-card memory">
              <div class="resource-header">
                <span class="resource-label">内存</span>
                <span class="resource-value">{{ selectedHost.memory_gb }} <small>GB</small></span>
              </div>
              <div class="resource-bar"><div class="resource-bar-fill memory" :style="{ width: Math.min(selectedHost.memory_gb / 1024 * 100, 100) + '%' }"></div></div>
              <div class="resource-desc">已分配: {{ selectedHost.memory_gb }} GB · 容量: 1024 GB</div>
            </div>
          </div>
        </div>

        <div class="empty-state" v-else>
          <div class="empty-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <path d="M8 12h8M12 8v8"/>
            </svg>
          </div>
          <h3 class="empty-title">NO DATA</h3>
          <p class="empty-desc">{{ emptyDesc }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'

const data = ref({
  total: 0,
  statistics: {},
  data: []
})
const selectedHost = ref(null)
const pageStatus = ref('loading')
const pageMessage = ref('')

const animatedTotal = ref(0)
const filterPlatform = ref('')

const emptyDesc = computed(() => {
  if (pageStatus.value === 'no_credentials') return 'No usable API credentials configured'
  if (pageStatus.value === 'collection_failed' || pageStatus.value === 'error') return pageMessage.value || 'Physical host collection failed'
  if (pageStatus.value === 'partial_data') return pageMessage.value || 'Some platform host data failed to collect'
  return pageMessage.value || 'No matching physical host data'
})

const animateValue = (target, currentRef) => {
  const duration = 1000
  const start = currentRef.value
  const increment = (target - start) / (duration / 16)
  let current = start

  const animate = () => {
    current += increment
    if (current < target) {
      currentRef.value = Math.round(current)
      requestAnimationFrame(animate)
    } else {
      currentRef.value = target
    }
  }

  requestAnimationFrame(animate)
}

const loadData = async () => {
  try {
    const params = {
      platform: filterPlatform.value || undefined,
    }
    const response = await axios.get('/api/ledger/physical', { params })
    pageStatus.value = response.data.status || 'unknown'
    pageMessage.value = response.data.message || ''
    data.value = response.data
    animateValue(data.value.total, animatedTotal)
  } catch (error) {
    console.error('Failed to load physical ledger:', error)
    pageStatus.value = 'error'
    pageMessage.value = 'Physical ledger load failed'
    data.value = { total: 0, statistics: {}, data: [] }
  }
}

const getStatusClass = (status) => {
  if (status === 'online' || status === '正常') return 'online'
  return 'offline'
}

const exportData = () => {
  alert('Export feature pending')
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
/* Import Rubik Font */
@import url('https://fonts.googleapis.com/css2?family=Rubik:wght@400;500;600;700&display=swap');

.physical-ledger-page {
  padding: 24px;
  min-height: calc(100vh - 64px);
  font-family: 'Rubik', -apple-system, system-ui, 'Segoe UI', Helvetica, Arial, sans-serif;
}

/* Header */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
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
  padding: 6px;
  background: rgba(251, 191, 36, 0.2);
  border-radius: 8px;
  color: #fbbf24;
}

.header-icon svg {
  width: 20px;
  height: 20px;
}

.title-text {
  display: flex;
  flex-direction: column;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #ffffff;
  letter-spacing: 0.2px;
  margin: 0;
}

.page-subtitle {
  font-size: 14px;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.5);
  margin: 0;
}

/* Glass Button */
.btn-glass {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.18);
  backdrop-filter: blur(18px) saturate(180%);
  border-radius: 8px;
  border: none;
  color: #ffffff;
  font-size: 14px;
  font-weight: 500;
  letter-spacing: 0.2px;
  text-transform: uppercase;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: rgba(0, 0, 0, 0.08) 0px 2px 8px;
}

.btn-glass:hover {
  background: rgba(54, 22, 107, 0.14);
}

.btn-icon {
  width: 16px;
  height: 16px;
}

/* Filter Section */
.filter-section {
  margin-bottom: 24px;
}

.filter-card {
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(18px) saturate(180%);
  border: 1px solid #362d59;
  border-radius: 12px;
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
  gap: 8px;
}

.filter-icon {
  width: 14px;
  height: 14px;
  color: rgba(255, 255, 255, 0.5);
}

.label-text {
  font-size: 12px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.5);
  letter-spacing: 0.2px;
  text-transform: uppercase;
}

.select-wrapper {
  position: relative;
}

.glass-select {
  padding: 8px 32px 8px 12px;
  background: #422082;
  border: none;
  border-radius: 8px;
  color: #ffffff;
  font-size: 14px;
  font-family: 'Rubik', sans-serif;
  min-width: 160px;
  cursor: pointer;
  appearance: none;
}

.glass-select:focus {
  outline: none;
  box-shadow: rgba(106, 95, 193) 0px 0px 0px 2px;
}

.glass-select option {
  background: #422082;
  color: #ffffff;
}

.select-arrow {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  width: 14px;
  height: 14px;
  color: rgba(255, 255, 255, 0.4);
}

/* Stats Section */
.stats-section {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(18px) saturate(180%);
  border: 1px solid #362d59;
  border-radius: 12px;
  transition: all 0.3s ease;
}

.stat-card:hover {
  background: rgba(255, 255, 255, 0.08);
}

.stat-icon {
  width: 40px;
  height: 40px;
  padding: 10px;
  border-radius: 10px;
  background: rgba(251, 191, 36, 0.2);
  color: #fbbf24;
}

.stat-icon.total { background: rgba(251, 191, 36, 0.2); color: #fbbf24; }
.stat-icon.cpu { background: rgba(106, 95, 193, 0.2); color: #6a5fc1; }
.stat-icon.memory { background: rgba(167, 139, 250, 0.2); color: #a78bfa; }

.stat-icon svg {
  width: 20px;
  height: 20px;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #ffffff;
}

.stat-unit {
  font-size: 14px;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.5);
}

.stat-label {
  font-size: 12px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.5);
  letter-spacing: 0.2px;
  text-transform: uppercase;
}

/* Distribution Section */
.distribution-section {
  margin-bottom: 24px;
}

.distribution-card {
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(18px) saturate(180%);
  border: 1px solid #362d59;
  border-radius: 12px;
  padding: 24px;
}

.distribution-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.dist-icon {
  width: 24px;
  height: 24px;
  color: #6a5fc1;
}

.distribution-title {
  font-size: 16px;
  font-weight: 600;
  color: #ffffff;
  letter-spacing: 0.2px;
  margin: 0;
}

.platform-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 16px;
}

.platform-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.platform-badge {
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.platform-badge.vmware { background: rgba(106, 95, 193, 0.2); color: #6a5fc1; }
.platform-badge.smartx { background: rgba(194, 239, 78, 0.2); color: #c2ef4e; }
.platform-badge.huawei_cloud { background: rgba(251, 191, 36, 0.2); color: #fbbf24; }
.platform-badge.sangfor_cloud { background: rgba(167, 139, 250, 0.2); color: #a78bfa; }
.platform-badge.tdsql { background: rgba(248, 113, 113, 0.2); color: #f87171; }
.platform-badge.storage { background: rgba(106, 95, 193, 0.2); color: #6a5fc1; }

.platform-count {
  font-size: 14px;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.8);
}

.platform-bar {
  height: 4px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
  overflow: hidden;
}

.platform-progress {
  height: 100%;
  border-radius: 2px;
  background: linear-gradient(90deg, #6a5fc1, #c2ef4e);
}

/* Table Section */
.table-section {
  margin-bottom: 24px;
}

.table-card {
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(18px) saturate(180%);
  border: 1px solid #362d59;
  border-radius: 12px;
  padding: 24px;
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
  padding: 12px 10px;
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.7);
  font-size: 12px;
  font-weight: 500;
  letter-spacing: 0.2px;
  text-transform: uppercase;
  text-align: left;
  border-bottom: 1px solid #362d59;
}

.glass-table td {
  padding: 12px 10px;
  color: #ffffff;
  font-size: 14px;
  font-weight: 400;
  border-bottom: 1px solid rgba(54, 45, 89, 0.5);
  max-width: 250px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.glass-table tr {
  transition: all 0.3s ease;
}

.glass-table tr:hover {
  background: rgba(255, 255, 255, 0.05);
}

.name-cell, .cluster-cell {
  color: rgba(255, 255, 255, 0.7);
}

.host-cell {
  color: #ffffff;
}

.ip-badge {
  padding: 2px 8px;
  background: rgba(194, 239, 78, 0.15);
  border-radius: 4px;
  color: #c2ef4e;
  font-size: 12px;
}

.mgmt-badge {
  padding: 2px 8px;
  background: rgba(106, 95, 193, 0.15);
  border-radius: 4px;
  color: #6a5fc1;
  font-size: 12px;
}

.resource-cell {
  color: rgba(255, 255, 255, 0.8);
  font-size: 13px;
}

.type-tag {
  padding: 2px 8px;
  background: rgba(167, 139, 250, 0.15);
  border-radius: 4px;
  color: #a78bfa;
  font-size: 12px;
}

.uptime-display {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.uptime-value {
  font-size: 14px;
  font-weight: 600;
  color: #c2ef4e;
}

.uptime-unit {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

/* Status Badge */
.status-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  text-transform: uppercase;
}

.status-badge.online { background: rgba(194, 239, 78, 0.2); color: #c2ef4e; }
.status-badge.offline { background: rgba(248, 113, 113, 0.2); color: #f87171; }

/* Table Row Click */
.table-row { cursor: pointer; transition: background 0.15s; }
.table-row:hover { background: rgba(255, 255, 255, 0.04); }
.table-row.selected { background: rgba(106, 95, 193, 0.12); }

/* Detail Panel */
.detail-panel { margin-top: 20px; padding: 24px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 16px; }
.detail-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; }
.detail-title-group { display: flex; align-items: center; gap: 12px; }
.detail-icon { width: 36px; height: 36px; color: #60a5fa; background: rgba(96,165,250,0.15); border-radius: 10px; padding: 8px; }
.detail-header h3 { font-size: 18px; font-weight: 600; color: #fff; margin: 0; }
.detail-subtitle { font-size: 13px; color: rgba(255,255,255,0.4); margin: 2px 0 0 0; }
.close-btn { background: rgba(255,255,255,0.08); border: none; color: rgba(255,255,255,0.5); font-size: 20px; cursor: pointer; width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; }
.close-btn:hover { background: rgba(255,255,255,0.15); color: #fff; }

.info-row { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 16px; }
.info-chip { display: flex; align-items: center; gap: 6px; padding: 8px 14px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; transition: all 0.2s; }
.info-chip:hover { background: rgba(255,255,255,0.06); }
.chip-label { font-size: 11px; color: rgba(255,255,255,0.4); text-transform: uppercase; letter-spacing: 0.3px; }
.chip-value { font-size: 13px; font-weight: 500; color: #fff; }
.chip-value.online { color: #c2ef4e; }
.chip-value.offline { color: #f87171; }

.resource-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 14px; }
.resource-card { padding: 16px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; transition: all 0.2s; }
.resource-card:hover { background: rgba(255,255,255,0.06); border-color: rgba(255,255,255,0.12); }
.resource-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.resource-label { font-size: 12px; font-weight: 600; color: rgba(255,255,255,0.5); text-transform: uppercase; letter-spacing: 0.3px; }
.resource-value { font-size: 24px; font-weight: 700; color: #fff; }
.resource-value small { font-size: 14px; font-weight: 400; color: rgba(255,255,255,0.5); }
.resource-bar { width: 100%; height: 8px; background: rgba(255,255,255,0.06); border-radius: 4px; overflow: hidden; margin-bottom: 10px; }
.resource-bar-fill { height: 100%; border-radius: 4px; transition: width 0.6s ease; }
.resource-bar-fill.cpu { background: linear-gradient(90deg, #818cf8, #6366f1); }
.resource-bar-fill.memory { background: linear-gradient(90deg, #34d399, #10b981); }
.resource-desc { font-size: 12px; color: rgba(255,255,255,0.4); }

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60px 20px;
  text-align: center;
}

.empty-icon {
  width: 64px;
  height: 64px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  color: rgba(255, 255, 255, 0.4);
}

.empty-icon svg {
  width: 32px;
  height: 32px;
}

.empty-title {
  font-size: 20px;
  font-weight: 600;
  color: #ffffff;
  margin: 16px 0 8px 0;
  letter-spacing: 0.2px;
}

.empty-desc {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.5);
  margin: 0;
}

/* Responsive */
@media (max-width: 768px) {
  .stats-section {
    grid-template-columns: 1fr;
  }
}
</style>