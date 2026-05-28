<template>
  <div class="alerts-page">
    <!-- Header Section -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-group">
          <div class="header-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
              <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
            </svg>
          </div>
          <div class="title-text">
            <h1 class="page-title">ALERTS MANAGEMENT</h1>
            <p class="page-subtitle">Real-time alerts monitoring and response</p>
          </div>
        </div>
      </div>
      <div class="header-stats">
        <div class="stat-badge critical" v-if="alertStats.critical > 0">
          <span class="badge-value">{{ alertStats.critical }}</span>
          <span class="badge-label">CRITICAL</span>
        </div>
        <div class="stat-badge warning" v-if="alertStats.warning > 0">
          <span class="badge-value">{{ alertStats.warning }}</span>
          <span class="badge-label">WARNING</span>
        </div>
        <div class="stat-badge active">
          <span class="badge-value">{{ alertStats.active }}</span>
          <span class="badge-label">ACTIVE</span>
        </div>
      </div>
    </div>

    <!-- Filter Section -->
    <div class="filter-section">
      <div class="filter-card">
        <div class="filter-group">
          <label class="filter-label">
            <span class="label-text">STATUS</span>
          </label>
          <div class="select-wrapper">
            <select v-model="selectedStatus" @change="loadAlerts" class="glass-select">
              <option value="">All Status</option>
              <option value="active">Active</option>
              <option value="resolved">Resolved</option>
              <option value="ignored">Ignored</option>
            </select>
            <svg class="select-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M7 10l5 5 5-5"/>
            </svg>
          </div>
        </div>

        <div class="filter-group">
          <label class="filter-label">
            <span class="label-text">LEVEL</span>
          </label>
          <div class="select-wrapper">
            <select v-model="selectedLevel" @change="loadAlerts" class="glass-select">
              <option value="">All Levels</option>
              <option value="warning">Warning</option>
              <option value="critical">Critical</option>
            </select>
            <svg class="select-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M7 10l5 5 5-5"/>
            </svg>
          </div>
        </div>

        <div class="filter-group">
          <label class="filter-label">
            <span class="label-text">PLATFORM</span>
          </label>
          <div class="select-wrapper">
            <select v-model="selectedPlatform" @change="loadAlerts" class="glass-select">
              <option value="">All Platforms</option>
              <option value="vmware">VMware</option>
              <option value="smartx">SmartX</option>
              <option value="huawei_cloud">Huawei Cloud</option>
              <option value="sangfor_cloud">Sangfor</option>
              <option value="tdsql">TDSQL</option>
              <option value="storage">Storage</option>
              <option value="backup">Backup</option>
            </select>
            <svg class="select-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M7 10l5 5 5-5"/>
            </svg>
          </div>
        </div>

        <button class="btn-glass" @click="loadAlerts">
          <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="23 4 23 10 17 10"/>
            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
          </svg>
          <span class="btn-text">REFRESH</span>
        </button>
      </div>
    </div>

    <!-- Stats Section -->
    <div class="stats-section">
      <div class="stat-card" :class="{ critical: alertStats.critical > 0 }">
        <div class="stat-icon critical">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="15" y1="9" x2="9" y2="15"/>
            <line x1="9" y1="9" x2="15" y2="15"/>
          </svg>
        </div>
        <div class="stat-content">
          <span class="stat-value" :class="{ critical: alertStats.critical > 0 }">{{ animatedStats.critical }}</span>
          <span class="stat-label">CRITICAL</span>
        </div>
        <div class="stat-pulse critical" v-if="alertStats.critical > 0"></div>
      </div>

      <div class="stat-card" :class="{ warning: alertStats.warning > 0 }">
        <div class="stat-icon warning">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94"/>
          </svg>
        </div>
        <div class="stat-content">
          <span class="stat-value" :class="{ warning: alertStats.warning > 0 }">{{ animatedStats.warning }}</span>
          <span class="stat-label">WARNING</span>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon active">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18"/>
          </svg>
        </div>
        <div class="stat-content">
          <span class="stat-value">{{ animatedStats.active }}</span>
          <span class="stat-label">ACTIVE</span>
        </div>
      </div>
    </div>

    <!-- Alerts List -->
    <div class="alerts-section">
      <div class="section-header">
        <div class="header-left">
          <span class="section-label">ALERTS LIST</span>
          <span class="alert-count">{{ alerts.length }}</span>
        </div>
        <button class="btn-primary" @click="resolveAllAlerts" v-if="alerts.length > 0">
          <span class="btn-text">RESOLVE ALL</span>
        </button>
      </div>

      <!-- Empty State -->
      <div class="empty-state success" v-if="alerts.length === 0">
        <div class="empty-icon success">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <path d="M9 12l2 2 4-4"/>
          </svg>
        </div>
        <span class="empty-text success">{{ emptyText }}</span>
      </div>

      <!-- Alerts Cards -->
      <div class="alerts-list" v-else>
        <transition-group name="alert-list">
          <div class="alert-card" v-for="alert in alerts" :key="alert.id" :class="alert.alert_level">
            <div class="alert-indicator" :class="alert.alert_level"></div>

            <div class="alert-main">
              <div class="alert-header">
                <div class="alert-platform">
                  <span class="platform-name">{{ getPlatformName(alert.platform) }}</span>
                </div>
                <span class="alert-level" :class="alert.alert_level">{{ alert.alert_level }}</span>
              </div>

              <div class="alert-body">
                <div class="alert-target">
                  <span class="target-label">HOST</span>
                  <span class="target-value">{{ alert.host_name || '--' }}</span>
                </div>
                <div class="alert-cluster" v-if="alert.cluster_name">
                  <span class="cluster-label">CLUSTER</span>
                  <span class="cluster-value">{{ alert.cluster_name }}</span>
                </div>
                <span class="type-tag" :class="alert.alert_type">{{ getAlertTypeName(alert.alert_type) }}</span>
              </div>

              <div class="alert-metrics">
                <div class="metric-item">
                  <span class="metric-label">CURRENT</span>
                  <span class="metric-value" :class="alert.alert_level">{{ alert.current_value }}%</span>
                </div>
                <div class="metric-bar">
                  <div class="bar-track">
                    <div class="bar-fill" :style="{ width: alert.current_value + '%' }" :class="alert.alert_level"></div>
                  </div>
                  <span class="threshold-mark" :style="{ left: alert.threshold_value + '%' }"></span>
                </div>
                <div class="metric-item">
                  <span class="metric-label">THRESHOLD</span>
                  <span class="metric-value threshold">{{ alert.threshold_value }}%</span>
                </div>
              </div>

              <div class="alert-footer">
                <span class="alert-time">{{ formatTime(alert.created_at) }}</span>
                <div class="alert-actions">
                  <button class="action-btn resolve" @click="resolveAlert(alert.id)">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <circle cx="12" cy="12" r="10"/>
                      <path d="M9 12l2 2 4-4"/>
                    </svg>
                    RESOLVE
                  </button>
                  <button class="action-btn ignore" @click="ignoreAlert(alert.id)">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <circle cx="12" cy="12" r="10"/>
                      <line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/>
                    </svg>
                    IGNORE
                  </button>
                </div>
              </div>
            </div>
          </div>
        </transition-group>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const selectedStatus = ref('active')
const selectedLevel = ref('')
const selectedPlatform = ref('')
const alerts = ref([])
const alertStats = ref({ active: 0, warning: 0, critical: 0 })
const animatedStats = ref({ active: 0, warning: 0, critical: 0 })
const pageStatus = ref('loading')
const pageMessage = ref('')

const emptyText = computed(() => {
  if (pageStatus.value === 'no_credentials') return 'NO API CREDENTIALS CONFIGURED'
  if (pageStatus.value === 'collection_failed' || pageStatus.value === 'error') return pageMessage.value || 'ALERT DATA COLLECTION FAILED'
  if (pageStatus.value === 'partial_data') return pageMessage.value || 'PARTIAL ALERT DATA AVAILABLE'
  return 'ALL SYSTEMS OPERATIONAL'
})

const platformNames = {
  vmware: 'VMware',
  smartx: 'SmartX',
  huawei_cloud: 'Huawei Cloud',
  sangfor_cloud: 'Sangfor',
  tdsql: 'TDSQL',
  storage: 'Storage',
  backup: 'Backup'
}

const alertTypeNames = {
  cpu: 'CPU',
  memory: 'MEMORY',
  storage: 'STORAGE',
  snapshot: 'SNAPSHOT'
}

const animateNumbers = (target) => {
  const duration = 800
  const start = { ...animatedStats.value }
  const startTime = Date.now()

  const animate = () => {
    const elapsed = Date.now() - startTime
    const progress = Math.min(elapsed / duration, 1)
    const eased = 1 - Math.pow(1 - progress, 3)

    animatedStats.value = {
      active: Math.round(start.active + (target.active - start.active) * eased),
      warning: Math.round(start.warning + (target.warning - start.warning) * eased),
      critical: Math.round(start.critical + (target.critical - start.critical) * eased),
    }

    if (progress < 1) {
      requestAnimationFrame(animate)
    }
  }

  requestAnimationFrame(animate)
}

const loadAlerts = async () => {
  try {
    const params = {
      status: selectedStatus.value || undefined,
      level: selectedLevel.value || undefined,
      platform: selectedPlatform.value || undefined,
    }

    const response = await axios.get('/api/alerts/', { params })
    pageStatus.value = response.data.status || 'unknown'
    pageMessage.value = response.data.message || ''
    alerts.value = response.data.alerts || []
    alertStats.value = response.data.statistics || { active: 0, warning: 0, critical: 0 }
    animateNumbers(alertStats.value)
  } catch (error) {
    console.error('Alerts load failed:', error)
    pageStatus.value = 'error'
    pageMessage.value = 'ALERT DATA LOAD FAILED'
    alerts.value = []
    alertStats.value = { active: 0, warning: 0, critical: 0 }
  }
}

const getPlatformName = (platform) => platformNames[platform] || platform
const getAlertTypeName = (type) => alertTypeNames[type] || type
const formatTime = (time) => new Date(time).toLocaleString('zh-CN')

const resolveAlert = async (alertId) => {
  try {
    await axios.put(`/api/alerts/${alertId}/resolve`)
    ElMessage.success('Alert resolved')
    loadAlerts()
  } catch (error) {
    ElMessage.error('Failed to resolve alert')
  }
}

const ignoreAlert = async (alertId) => {
  try {
    await axios.put(`/api/alerts/${alertId}/ignore`)
    ElMessage.success('Alert ignored')
    loadAlerts()
  } catch (error) {
    ElMessage.error('Failed to ignore alert')
  }
}

const resolveAllAlerts = async () => {
  try {
    for (const alert of alerts.value) {
      await axios.put(`/api/alerts/${alert.id}/resolve`)
    }
    ElMessage.success('All alerts resolved')
    loadAlerts()
  } catch (error) {
    ElMessage.error('Batch resolve failed')
  }
}

watch(alertStats, (newVal) => animateNumbers(newVal))
onMounted(() => loadAlerts())
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Rubik:wght@400;500;600;700&display=swap');

.alerts-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
  font-family: 'Rubik', -apple-system, system-ui, 'Segoe UI', Helvetica, Arial, sans-serif;
}

/* Header */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  background: rgba(248, 113, 113, 0.1);
  border-radius: 12px;
  border: 1px solid rgba(248, 113, 113, 0.25);
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
  color: rgba(255, 255, 255, 0.5);
  margin: 0;
}

.header-stats {
  display: flex;
  gap: 12px;
}

.stat-badge {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
}

.stat-badge.critical {
  background: rgba(248, 113, 113, 0.2);
  border: 1px solid rgba(248, 113, 113, 0.3);
}

.stat-badge.warning {
  background: rgba(251, 191, 36, 0.2);
  border: 1px solid rgba(251, 191, 36, 0.3);
}

.badge-value {
  font-size: 18px;
  font-weight: 600;
  color: #ffffff;
}

.stat-badge.critical .badge-value { color: #f87171; }
.stat-badge.warning .badge-value { color: #fbbf24; }

.badge-label {
  font-size: 10px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.5);
  letter-spacing: 0.25px;
  text-transform: uppercase;
}

/* Filter Section */
.filter-section {
  margin-bottom: 0;
}

.filter-card {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 16px 24px;
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(18px) saturate(180%);
  border: 1px solid #362d59;
  border-radius: 12px;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.filter-label {
  display: flex;
  align-items: center;
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
  padding: 8px 28px 8px 12px;
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
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  width: 14px;
  height: 14px;
  color: rgba(255, 255, 255, 0.4);
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
}

.btn-glass:hover {
  background: rgba(54, 22, 107, 0.14);
}

.btn-icon {
  width: 16px;
  height: 16px;
}

/* Primary Button */
.btn-primary {
  padding: 8px 16px;
  background: rgba(194, 239, 78, 0.2);
  border: 1px solid rgba(194, 239, 78, 0.3);
  border-radius: 13px;
  color: #c2ef4e;
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.2px;
  text-transform: uppercase;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-primary:hover {
  background: rgba(194, 239, 78, 0.3);
}

/* Stats Section */
.stats-section {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
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

.stat-card.warning {
  border-color: rgba(251, 191, 36, 0.25);
}

.stat-card.critical {
  border-color: rgba(248, 113, 113, 0.25);
}

.stat-icon {
  width: 40px;
  height: 40px;
  padding: 10px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.5);
}

.stat-icon.critical { background: rgba(248, 113, 113, 0.2); color: #f87171; }
.stat-icon.warning { background: rgba(251, 191, 36, 0.2); color: #fbbf24; }
.stat-icon.active { background: rgba(106, 95, 193, 0.2); color: #6a5fc1; }

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

.stat-value.warning { color: #fbbf24; }
.stat-value.critical { color: #f87171; }

.stat-label {
  font-size: 12px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.5);
  letter-spacing: 0.2px;
  text-transform: uppercase;
}

.stat-pulse {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #f87171;
  animation: pulse-critical 0.5s infinite;
}

@keyframes pulse-critical {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.3; transform: scale(2); }
}

/* Alerts Section */
.alerts-section {
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(18px) saturate(180%);
  border: 1px solid #362d59;
  border-radius: 12px;
  padding: 24px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.section-label {
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.7);
  letter-spacing: 0.2px;
  text-transform: uppercase;
}

.alert-count {
  padding: 4px 8px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 40px;
}

.empty-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.4);
}

.empty-icon.success { color: #c2ef4e; }

.empty-icon svg {
  width: 32px;
  height: 32px;
}

.empty-text {
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.5);
}

.empty-text.success { color: #c2ef4e; }

/* Alerts List */
.alerts-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.alert-card {
  display: flex;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid #362d59;
  overflow: hidden;
  transition: all 0.3s ease;
}

.alert-card:hover {
  background: rgba(255, 255, 255, 0.08);
}

.alert-card.critical {
  border-color: rgba(248, 113, 113, 0.25);
  background: rgba(248, 113, 113, 0.08);
}

.alert-card.warning {
  border-color: rgba(251, 191, 36, 0.25);
  background: rgba(251, 191, 36, 0.08);
}

.alert-indicator {
  width: 4px;
  background: rgba(255, 255, 255, 0.3);
}

.alert-indicator.critical { background: #f87171; }
.alert-indicator.warning { background: #fbbf24; }

.alert-main {
  flex: 1;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.alert-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.alert-platform {
  display: flex;
  align-items: center;
  gap: 8px;
}

.platform-name {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.7);
}

.alert-level {
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.alert-level.critical {
  background: rgba(248, 113, 113, 0.2);
  color: #f87171;
}

.alert-level.warning {
  background: rgba(251, 191, 36, 0.2);
  color: #fbbf24;
}

.alert-body {
  display: flex;
  align-items: center;
  gap: 16px;
}

.alert-target, .alert-cluster {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.target-label, .cluster-label {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
  letter-spacing: 0.2px;
  text-transform: uppercase;
}

.target-value {
  font-size: 14px;
  font-weight: 500;
  color: #ffffff;
}

.cluster-value {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.7);
}

.type-tag {
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
}

.type-tag.cpu { background: rgba(106, 95, 193, 0.2); color: #6a5fc1; }
.type-tag.memory { background: rgba(167, 139, 250, 0.2); color: #a78bfa; }
.type-tag.storage { background: rgba(194, 239, 78, 0.2); color: #c2ef4e; }
.type-tag.snapshot { background: rgba(236, 72, 153, 0.2); color: #ec4899; }

.alert-metrics {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 8px;
}

.metric-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.metric-label {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
  letter-spacing: 0.2px;
  text-transform: uppercase;
}

.metric-value {
  font-size: 14px;
  font-weight: 500;
  color: #ffffff;
}

.metric-value.critical { color: #f87171; }
.metric-value.warning { color: #fbbf24; }
.metric-value.threshold { color: rgba(255, 255, 255, 0.5); }

.metric-bar {
  flex: 1;
  position: relative;
  height: 24px;
}

.bar-track {
  width: 100%;
  height: 8px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
}

.bar-fill {
  height: 100%;
  border-radius: 4px;
}

.bar-fill.critical { background: #f87171; }
.bar-fill.warning { background: #fbbf24; }

.threshold-mark {
  position: absolute;
  top: -4px;
  width: 2px;
  height: 16px;
  background: #ffffff;
  border-radius: 2px;
  transform: translateX(-50%);
}

.alert-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.alert-time {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
}

.alert-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  letter-spacing: 0.2px;
  text-transform: uppercase;
  cursor: pointer;
  transition: all 0.3s ease;
}

.action-btn.resolve {
  background: rgba(194, 239, 78, 0.2);
  border: 1px solid rgba(194, 239, 78, 0.3);
  color: #c2ef4e;
}

.action-btn.resolve:hover {
  background: rgba(194, 239, 78, 0.3);
}

.action-btn.ignore {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: rgba(255, 255, 255, 0.7);
}

.action-btn.ignore:hover {
  background: rgba(255, 255, 255, 0.2);
}

.action-btn svg {
  width: 14px;
  height: 14px;
}

/* Transitions */
.alert-list-move,
.alert-list-enter-active,
.alert-list-leave-active {
  transition: all 0.5s ease;
}

.alert-list-enter-from,
.alert-list-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

.alert-list-leave-active {
  position: absolute;
}

/* Responsive */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 16px;
  }

  .stats-section {
    grid-template-columns: 1fr;
  }

  .filter-card {
    flex-wrap: wrap;
  }
}
</style>