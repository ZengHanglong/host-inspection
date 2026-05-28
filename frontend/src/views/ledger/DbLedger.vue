<template>
  <div class="db-ledger-page">
    <!-- Header Section -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-group">
          <div class="header-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <ellipse cx="12" cy="5" rx="9" ry="3"/>
              <path d="M21 5v14c0 1.66-4 3-9 3s-9-1.34-9-3V5"/>
              <path d="M3 12c0 1.66 4 3 9 3s9-1.34 9-3"/>
            </svg>
          </div>
          <div class="title-text">
            <h1 class="page-title">DATABASE LEDGER</h1>
            <p class="page-subtitle">Manage all database system assets</p>
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
              <ellipse cx="12" cy="5" rx="9" ry="3"/>
              <path d="M21 5v14c0 1.66-4 3-9 3s-9-1.34-9-3V5"/>
            </svg>
            <span class="label-text">DATABASE TYPE</span>
          </label>
          <div class="select-wrapper">
            <select v-model="filterDbName" @change="loadData" class="glass-select">
              <option value="">All Types</option>
              <option value="TDSQL">TDSQL</option>
              <option value="Gbase">Gbase</option>
              <option value="CDH">CDH</option>
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
            <ellipse cx="12" cy="5" rx="9" ry="3"/>
            <path d="M21 5v14c0 1.66-4 3-9 3s-9-1.34-9-3V5"/>
          </svg>
        </div>
        <div class="stat-content">
          <span class="stat-value">{{ animatedTotal }}</span>
          <span class="stat-label">TOTAL HOSTS</span>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon space">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <ellipse cx="12" cy="5" rx="9" ry="3"/>
            <path d="M21 5v14c0 1.66-4 3-9 3s-9-1.34-9-3V5"/>
          </svg>
        </div>
        <div class="stat-content">
          <span class="stat-value">{{ data.statistics?.total_space_gb || 0 }}</span>
          <span class="stat-unit">GB</span>
          <span class="stat-label">TOTAL SPACE</span>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon used">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2L2 7l10 5 10-5-10-5z"/>
            <path d="M2 17l10 5 10-5"/>
          </svg>
        </div>
        <div class="stat-content">
          <span class="stat-value">{{ data.statistics?.used_space_gb || 0 }}</span>
          <span class="stat-unit">GB</span>
          <span class="stat-label">USED SPACE</span>
        </div>
      </div>

      <div class="stat-card" :class="usageClass">
        <div class="stat-icon usage">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <path d="M12 6v6l4 2"/>
          </svg>
        </div>
        <div class="stat-content">
          <span class="stat-value" :class="usageClass">{{ data.statistics?.avg_space_usage || 0 }}</span>
          <span class="stat-unit">%</span>
          <span class="stat-label">AVG USAGE</span>
        </div>
        <div class="usage-bar">
          <div class="usage-progress" :style="{ width: (data.statistics?.avg_space_usage || 0) + '%' }"></div>
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
                <th>DB TYPE</th>
                <th>CLUSTER</th>
                <th>HOST NAME</th>
                <th>IP ADDRESS</th>
                <th>TYPE</th>
                <th>VERSION</th>
                <th>TOTAL SPACE</th>
                <th>USED SPACE</th>
                <th>USAGE</th>
                <th>STATUS</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, index) in data.data" :key="index" :class="getRowClass(row.space_usage)">
                <td>
                  <span class="db-badge" :class="getDbClass(row.db_name)">{{ row.db_name }}</span>
                </td>
                <td class="cluster-cell">{{ row.cluster }}</td>
                <td class="host-cell">{{ row.host_name }}</td>
                <td>
                  <span class="ip-badge">{{ row.ip }}</span>
                </td>
                <td>
                  <span class="type-tag">{{ row.db_type }}</span>
                </td>
                <td class="version-cell">{{ row.version }}</td>
                <td class="space-cell">{{ row.total_space_gb }} GB</td>
                <td class="space-cell">{{ row.used_space_gb }} GB</td>
                <td>
                  <div class="usage-cell">
                    <div class="mini-bar">
                      <div class="mini-progress" :class="getProgressClass(row.space_usage)" :style="{ width: row.space_usage + '%' }"></div>
                    </div>
                    <span class="usage-value" :class="getUsageClass(row.space_usage)">{{ row.space_usage }}%</span>
                  </div>
                </td>
                <td>
                  <span class="status-badge" :class="getStatusClass(row.status)">{{ row.status }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="empty-state" v-else>
          <div class="empty-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <path d="M8 12h8M12 8v8"/>
            </svg>
          </div>
          <h3 class="empty-title">NO DATA</h3>
          <p class="empty-desc">Add API configuration to get database data</p>
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

const animatedTotal = ref(0)
const filterDbName = ref('')

const usageClass = computed(() => {
  const avg = data.value.statistics?.avg_space_usage || 0
  if (avg >= 70) return 'critical'
  if (avg >= 60) return 'warning'
  return 'normal'
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
      db_name: filterDbName.value || undefined,
    }
    const response = await axios.get('/api/ledger/database', { params })
    data.value = response.data
    animateValue(data.value.total, animatedTotal)
  } catch (error) {
    console.error('Failed to load database ledger:', error)
  }
}

const getDbClass = (name) => {
  const classes = {
    'TDSQL': 'tdsql',
    'Gbase': 'gbase',
    'CDH': 'cdh'
  }
  return classes[name] || 'default'
}

const getRowClass = (usage) => {
  if (usage >= 80) return 'critical-row'
  if (usage >= 70) return 'warning-row'
  return ''
}

const getProgressClass = (usage) => {
  if (usage >= 80) return 'critical'
  if (usage >= 70) return 'warning'
  return 'normal'
}

const getUsageClass = (usage) => {
  if (usage >= 80) return 'critical'
  if (usage >= 70) return 'warning'
  return 'normal'
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

.db-ledger-page {
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
  background: rgba(194, 239, 78, 0.2);
  border-radius: 8px;
  color: #c2ef4e;
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
  min-width: 140px;
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
  grid-template-columns: repeat(4, 1fr);
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
  position: relative;
  transition: all 0.3s ease;
}

.stat-card:hover {
  background: rgba(255, 255, 255, 0.08);
}

.stat-card.critical {
  border-color: rgba(248, 113, 113, 0.25);
}

.stat-card.warning {
  border-color: rgba(251, 191, 36, 0.25);
}

.stat-icon {
  width: 40px;
  height: 40px;
  padding: 10px;
  border-radius: 10px;
  background: rgba(194, 239, 78, 0.2);
  color: #c2ef4e;
}

.stat-icon.total { background: rgba(194, 239, 78, 0.2); color: #c2ef4e; }
.stat-icon.space { background: rgba(106, 95, 193, 0.2); color: #6a5fc1; }
.stat-icon.used { background: rgba(167, 139, 250, 0.2); color: #a78bfa; }
.stat-icon.usage { background: rgba(251, 191, 36, 0.2); color: #fbbf24; }

.stat-card.critical .stat-icon.usage { background: rgba(248, 113, 113, 0.2); color: #f87171; }

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

.stat-value.critical { color: #f87171; }
.stat-value.warning { color: #fbbf24; }

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

.usage-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 0 0 12px 12px;
  overflow: hidden;
}

.usage-progress {
  height: 100%;
  border-radius: 0 0 12px 0;
  background: #c2ef4e;
}

.stat-card.critical .usage-progress { background: #f87171; }
.stat-card.warning .usage-progress { background: #fbbf24; }

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
}

.glass-table tr {
  transition: all 0.3s ease;
}

.glass-table tr:hover {
  background: rgba(255, 255, 255, 0.05);
}

.glass-table tr.warning-row {
  background: rgba(251, 191, 36, 0.05);
}

.glass-table tr.critical-row {
  background: rgba(248, 113, 113, 0.08);
}

/* Badge Styles */
.db-badge {
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.db-badge.tdsql { background: rgba(194, 239, 78, 0.2); color: #c2ef4e; }
.db-badge.gbase { background: rgba(106, 95, 193, 0.2); color: #6a5fc1; }
.db-badge.cdh { background: rgba(251, 191, 36, 0.2); color: #fbbf24; }

.cluster-cell {
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

.type-tag {
  padding: 2px 8px;
  background: rgba(106, 95, 193, 0.15);
  border-radius: 4px;
  color: #6a5fc1;
  font-size: 12px;
}

.version-cell {
  color: rgba(255, 255, 255, 0.6);
}

.space-cell {
  color: rgba(255, 255, 255, 0.8);
  font-size: 13px;
}

/* Usage Cell */
.usage-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.mini-bar {
  width: 60px;
  height: 6px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
  overflow: hidden;
}

.mini-progress {
  height: 100%;
  border-radius: 3px;
}

.mini-progress.normal { background: #c2ef4e; }
.mini-progress.warning { background: #fbbf24; }
.mini-progress.critical { background: #f87171; }

.usage-value {
  font-size: 12px;
  font-weight: 500;
}

.usage-value.normal { color: #c2ef4e; }
.usage-value.warning { color: #fbbf24; }
.usage-value.critical { color: #f87171; }

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
@media (max-width: 1200px) {
  .stats-section {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .stats-section {
    grid-template-columns: 1fr;
  }
}
</style>