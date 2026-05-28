<template>
  <div class="dashboard">
    <!-- Hero Section -->
    <div class="hero-section">
      <div class="hero-content">
        <span class="hero-label">{{ t('dashboard.hero.label') }}</span>
        <h1 class="hero-title">{{ t('dashboard.hero.title') }}</h1>
        <p class="hero-subtitle">{{ t('dashboard.hero.subtitle') }}</p>
      </div>
      <div class="hero-status" :class="dataStatus">
        <div class="status-ring">
          <div class="status-dot"></div>
        </div>
        <span class="status-text">{{ statusText }}</span>
      </div>
    </div>

    <!-- Data Banner -->
    <transition name="fade">
      <div class="banner info" v-if="dataStatus === 'loading'">
        <div class="banner-icon spinning">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
          </svg>
        </div>
        <div class="banner-text">
          <span class="banner-title">数据采集中</span>
          <span class="banner-desc">正在从已配置的平台采集数据，请稍候...</span>
        </div>
      </div>
    </transition>

    <transition name="fade">
      <div class="banner success" v-if="dataStatus === 'real_data'">
        <div class="banner-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            <path d="M9 12l2 2 4-4"/>
          </svg>
        </div>
        <div class="banner-text">
          <span class="banner-title">{{ t('dashboard.banner.verified') }}</span>
          <span class="banner-desc">{{ t('dashboard.banner.lastUpdate', { time: lastCheckTime }) }}</span>
        </div>
      </div>
    </transition>

    <transition name="fade">
      <div class="banner warning" v-if="dataStatus === 'no_credentials'">
        <div class="banner-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
        </div>
        <div class="banner-text">
          <span class="banner-title">{{ t('dashboard.banner.credentialsRequired') }}</span>
          <span class="banner-desc">{{ t('dashboard.banner.credentialsHint') }}</span>
        </div>
        <button class="btn-primary" @click="goToCredentials">
          <span class="btn-text">{{ t('dashboard.banner.configure') }}</span>
        </button>
      </div>
    </transition>

    <transition name="fade">
      <div class="banner warning" v-if="dataStatus === 'collection_failed' || dataStatus === 'partial_data' || dataStatus === 'error'">
        <div class="banner-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
        </div>
        <div class="banner-text">
          <span class="banner-title">数据采集异常</span>
          <span class="banner-desc">{{ pageMessage || '已连接平台暂未返回可用数据' }}</span>
        </div>
        <button class="btn-primary" @click="goToCredentials">
          <span class="btn-text">查看凭证</span>
        </button>
      </div>
    </transition>

    <!-- Stats Grid -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon total">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="2" y="3" width="20" height="14" rx="2"/>
            <line x1="8" y1="21" x2="16" y2="21"/>
            <line x1="12" y1="17" x2="12" y2="21"/>
          </svg>
        </div>
        <div class="stat-content">
          <span class="stat-value">{{ animatedStats.total_hosts }}</span>
          <span class="stat-unit">{{ t('dashboard.stats.hostsUnit') }}</span>
          <span class="stat-label">{{ t('dashboard.stats.totalHosts') }}</span>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon normal">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <path d="M9 12l2 2 4-4"/>
          </svg>
        </div>
        <div class="stat-content">
          <span class="stat-value">{{ animatedStats.normal }}</span>
          <span class="stat-unit">{{ t('dashboard.stats.hostsUnit') }}</span>
          <span class="stat-label">{{ t('dashboard.stats.normal') }}</span>
        </div>
        <span class="stat-percent" v-if="overall.total_hosts > 0">{{ Math.round((overall.normal / overall.total_hosts) * 100) }}%</span>
      </div>

      <div class="stat-card" :class="{ warning: overall.warning > 0 }">
        <div class="stat-icon warning">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
            <line x1="12" y1="9" x2="12" y2="13"/>
          </svg>
        </div>
        <div class="stat-content">
          <span class="stat-value" :class="{ warning: overall.warning > 0 }">{{ animatedStats.warning }}</span>
          <span class="stat-unit">{{ t('dashboard.stats.hostsUnit') }}</span>
          <span class="stat-label">{{ t('dashboard.stats.warning') }}</span>
        </div>
        <div class="stat-pulse" v-if="overall.warning > 0"></div>
      </div>

      <div class="stat-card" :class="{ critical: overall.critical > 0 }">
        <div class="stat-icon critical">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="15" y1="9" x2="9" y2="15"/>
            <line x1="9" y1="9" x2="15" y2="15"/>
          </svg>
        </div>
        <div class="stat-content">
          <span class="stat-value" :class="{ critical: overall.critical > 0 }">{{ animatedStats.critical }}</span>
          <span class="stat-unit">{{ t('dashboard.stats.hostsUnit') }}</span>
          <span class="stat-label">{{ t('dashboard.stats.critical') }}</span>
        </div>
        <div class="stat-pulse critical" v-if="overall.critical > 0"></div>
      </div>
    </div>

    <!-- Platform Section -->
    <div class="section-card">
      <div class="section-header">
        <div class="header-left">
          <span class="section-label">{{ t('dashboard.platform.title') }}</span>
        </div>
        <span class="section-tag" :class="dataStatus">{{ platformTagText }}</span>
      </div>

      <!-- Empty State -->
      <div class="empty-state" v-if="!platforms || Object.keys(platforms).length === 0">
        <div class="empty-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <path d="M12 6v6"/>
            <path d="M12 16h.01"/>
          </svg>
        </div>
        <span class="empty-text">{{ platformEmptyText }}</span>
        <button class="btn-primary" v-if="dataStatus === 'no_credentials'" @click="goToCredentials">
          <span class="btn-text">{{ t('dashboard.platform.addCredentials') }}</span>
        </button>
      </div>

      <!-- Platform Grid -->
      <div class="platform-grid" v-else>
        <div class="platform-card" v-for="(info, key) in platforms" :key="key" :class="{ connected: info.connected }">
          <div class="platform-header">
            <div class="platform-icon" :class="key">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="2" y="3" width="20" height="14" rx="2"/>
              </svg>
            </div>
            <div class="platform-info">
              <span class="platform-name">{{ info.name }}</span>
              <span class="platform-status" :class="info.connected ? 'connected' : 'disconnected'">
                {{ info.connected ? t('dashboard.platform.connected') : t('dashboard.platform.offline') }}
              </span>
            </div>
          </div>
          <div class="platform-stats">
            <div class="stat-item">
              <span class="item-value">{{ info.statistics?.clusters || 0 }}</span>
              <span class="item-label">{{ t('dashboard.platform.clusters') }}</span>
            </div>
            <div class="stat-item">
              <span class="item-value">{{ info.statistics?.hosts || 0 }}</span>
              <span class="item-label">{{ t('dashboard.platform.hosts') }}</span>
            </div>
            <div class="stat-item">
              <span class="item-value">{{ info.statistics?.vms || 0 }}</span>
              <span class="item-label">{{ t('dashboard.platform.vms') }}</span>
            </div>
          </div>
          <div class="platform-source">
            <span class="source-label">{{ t('dashboard.platform.source') }}</span>
            <span class="source-value">{{ info.data_source }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Alerts Section -->
    <div class="section-card">
      <div class="section-header">
        <div class="header-left">
          <span class="section-label">{{ t('dashboard.alerts.title') }}</span>
        </div>
        <span class="alert-badge" v-if="alerts.length > 0">{{ alerts.length }}</span>
      </div>

      <!-- No Alerts -->
      <div class="empty-state success" v-if="!alerts || alerts.length === 0">
        <div class="empty-icon success">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <path d="M9 12l2 2 4-4"/>
          </svg>
        </div>
        <span class="empty-text success">{{ alertsEmptyText }}</span>
      </div>

      <!-- Alerts List -->
      <div class="alerts-list" v-else>
        <div class="alert-item" v-for="(alert, index) in alerts" :key="index" :class="alert.alert_level">
          <div class="alert-icon" :class="alert.alert_level">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="8" x2="12" y2="12"/>
            </svg>
          </div>
          <div class="alert-content">
            <div class="alert-header">
              <span class="alert-platform">{{ alert.platform_name }}</span>
              <span class="alert-level" :class="alert.alert_level">{{ translateStatus(alert.alert_level) }}</span>
            </div>
            <span class="alert-host">{{ alert.host_name }}</span>
            <span class="alert-message">{{ alert.message }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Periodic Section -->
    <div class="section-card" v-if="periodicStatus && Object.keys(periodicStatus).length > 0">
      <div class="section-header">
        <div class="header-left">
          <span class="section-label">{{ t('dashboard.periodic.title') }}</span>
        </div>
      </div>

      <div class="periodic-grid">
        <div class="periodic-item" v-for="(info, key) in periodicStatus" :key="key">
          <div class="periodic-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <polyline points="12 6 12 12 16 14"/>
            </svg>
          </div>
          <div class="periodic-content">
            <span class="periodic-name">{{ info.name }}</span>
            <span class="periodic-count" :class="{ 'has-items': getPeriodicCount(info) > 0 }">
              {{ getPeriodicCount(info) }} {{ t('dashboard.periodic.items') }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import axios from 'axios'

const router = useRouter()
const { t } = useI18n()

const dataStatus = ref('loading')
const pageMessage = ref('')
const lastCheckTime = ref('')
const overall = ref({ total_hosts: 0, normal: 0, warning: 0, critical: 0 })
const platforms = ref({})
const alerts = ref([])
const periodicStatus = ref({})
const animatedStats = ref({ total_hosts: 0, normal: 0, warning: 0, critical: 0 })

const statusText = computed(() => {
  if (dataStatus.value === 'loading') return '数据采集中...'
  if (dataStatus.value === 'real_data' || dataStatus.value === 'partial_data') return t('dashboard.hero.connected')
  if (dataStatus.value === 'collection_failed' || dataStatus.value === 'error') return '采集失败'
  return t('dashboard.hero.notConfigured')
})

const platformTagText = computed(() => {
  if (dataStatus.value === 'loading') return '采集中'
  if (dataStatus.value === 'real_data') return t('dashboard.platform.realData')
  if (dataStatus.value === 'partial_data') return '部分数据'
  if (dataStatus.value === 'collection_failed' || dataStatus.value === 'error') return '采集失败'
  return t('dashboard.platform.noData')
})

const platformEmptyText = computed(() => {
  if (dataStatus.value === 'loading') return '正在采集平台数据，请稍候...'
  if (dataStatus.value === 'no_credentials') return t('dashboard.platform.empty')
  if (pageMessage.value) return pageMessage.value
  if (dataStatus.value === 'collection_failed' || dataStatus.value === 'error') return '已连接平台暂未返回可用数据'
  return '当前暂无平台数据'
})

const alertsEmptyText = computed(() => {
  if (dataStatus.value === 'loading') return '数据加载中...'
  if (dataStatus.value === 'collection_failed' || dataStatus.value === 'error') return '当前无法判断告警状态，数据采集中断'
  if (dataStatus.value === 'partial_data') return '当前无告警，部分平台采集异常'
  return t('dashboard.alerts.allOperational')
})

const getPeriodicCount = (info) => info?.expired_count || info?.large_count || info?.issue_count || 0
const translateStatus = (status) => t(`common.status.${status}`, status)

const animateNumbers = (target) => {
  const duration = 1000
  const start = { ...animatedStats.value }
  const startTime = Date.now()

  const animate = () => {
    const elapsed = Date.now() - startTime
    const progress = Math.min(elapsed / duration, 1)
    const eased = 1 - Math.pow(1 - progress, 3)

    animatedStats.value = {
      total_hosts: Math.round(start.total_hosts + (target.total_hosts - start.total_hosts) * eased),
      normal: Math.round(start.normal + (target.normal - start.normal) * eased),
      warning: Math.round(start.warning + (target.warning - start.warning) * eased),
      critical: Math.round(start.critical + (target.critical - start.critical) * eased),
    }

    if (progress < 1) {
      requestAnimationFrame(animate)
    }
  }

  requestAnimationFrame(animate)
}

const loadDashboard = async () => {
  try {
    const response = await axios.get('/api/dashboard')
    dataStatus.value = response.data.status || 'unknown'
    pageMessage.value = response.data.message || ''
    lastCheckTime.value = response.data.overall?.data_cutoff_time || response.data.overall?.last_check_time || ''
    overall.value = response.data.overall || { total_hosts: 0, normal: 0, warning: 0, critical: 0 }
    platforms.value = response.data.platforms || {}
    alerts.value = response.data.alerts || []
    periodicStatus.value = response.data.periodic_status || {}
    animateNumbers(overall.value)
  } catch (error) {
    console.error('Dashboard load failed:', error)
    dataStatus.value = 'error'
    pageMessage.value = '仪表盘数据加载失败'
    overall.value = { total_hosts: 0, normal: 0, warning: 0, critical: 0 }
    platforms.value = {}
    alerts.value = []
    periodicStatus.value = {}
  }
}

const goToCredentials = () => {
  router.push('/credentials')
}

let refreshTimer = null

onMounted(() => {
  loadDashboard()
  refreshTimer = setInterval(loadDashboard, 30000)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Rubik:wght@400;500;600;700&display=swap');

.dashboard {
  display: flex;
  flex-direction: column;
  gap: 24px;
  font-family: 'Rubik', -apple-system, system-ui, 'Segoe UI', Helvetica, Arial, sans-serif;
}

/* Hero Section */
.hero-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 32px 40px;
  background: linear-gradient(135deg, rgba(106, 95, 193, 0.15) 0%, rgba(66, 32, 130, 0.15) 100%);
  border-radius: 12px;
  border: 1px solid #362d59;
}

.hero-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.hero-label {
  font-size: 12px;
  font-weight: 500;
  color: #c2ef4e;
  letter-spacing: 0.25px;
  text-transform: uppercase;
}

.hero-title {
  font-size: 30px;
  font-weight: 600;
  color: #ffffff;
  margin: 0;
}

.hero-subtitle {
  font-size: 14px;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.5);
}

.hero-status {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  background: rgba(255, 255, 255, 0.18);
  backdrop-filter: blur(18px) saturate(180%);
  border-radius: 8px;
}

.status-ring {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(251, 191, 36, 0.2);
}

.hero-status.real_data .status-ring {
  background: rgba(194, 239, 78, 0.2);
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #fbbf24;
}

.hero-status.real_data .status-dot {
  background: #c2ef4e;
}

.status-text {
  font-size: 14px;
  font-weight: 500;
  color: #ffffff;
  letter-spacing: 0.2px;
}

/* Banner */
.banner {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 24px;
  border-radius: 8px;
}

.banner.success {
  background: rgba(194, 239, 78, 0.1);
  border: 1px solid rgba(194, 239, 78, 0.3);
}

.banner.warning {
  background: rgba(251, 191, 36, 0.1);
  border: 1px solid rgba(251, 191, 36, 0.3);
}

.banner.info {
  background: rgba(106, 95, 193, 0.1);
  border: 1px solid rgba(106, 95, 193, 0.3);
}

.banner.info .banner-icon {
  color: #6a5fc1;
}

.banner.info .banner-title {
  color: #6a5fc1;
}

.spinning {
  animation: spin 1.5s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.banner-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #c2ef4e;
}

.banner.warning .banner-icon {
  color: #fbbf24;
}

.banner-icon svg {
  width: 20px;
  height: 20px;
}

.banner-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.banner-title {
  font-size: 14px;
  font-weight: 600;
  color: #c2ef4e;
  letter-spacing: 0.2px;
}

.banner.warning .banner-title {
  color: #fbbf24;
}

.banner-desc {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

/* Primary Button */
.btn-primary {
  padding: 8px 16px;
  background: #79628c;
  border: 1px solid #584674;
  border-radius: 13px;
  color: #ffffff;
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.2px;
  text-transform: uppercase;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: rgba(0, 0, 0, 0.1) 0px 1px 3px 0px inset;
}

.btn-primary:hover {
  box-shadow: rgba(0, 0, 0, 0.18) 0px 0.5rem 1.5rem;
  transform: translateY(-1px);
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
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

.stat-card:hover {
  background: rgba(255, 255, 255, 0.08);
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
  background: rgba(194, 239, 78, 0.2);
  color: #c2ef4e;
}

.stat-icon.total { background: rgba(194, 239, 78, 0.2); color: #c2ef4e; }
.stat-icon.normal { background: rgba(106, 95, 193, 0.2); color: #6a5fc1; }
.stat-icon.warning { background: rgba(251, 191, 36, 0.2); color: #fbbf24; }
.stat-icon.critical { background: rgba(248, 113, 113, 0.2); color: #f87171; }

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

.stat-unit {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.stat-label {
  font-size: 12px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.5);
  letter-spacing: 0.2px;
  text-transform: uppercase;
}

.stat-percent {
  padding: 4px 8px;
  background: rgba(106, 95, 193, 0.2);
  border-radius: 4px;
  color: #6a5fc1;
  font-size: 12px;
  font-weight: 500;
}

.stat-pulse {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #fbbf24;
  animation: pulse 1s infinite;
}

.stat-pulse.critical {
  background: #f87171;
  animation: pulse-critical 0.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.5); }
}

@keyframes pulse-critical {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.3; transform: scale(2); }
}

/* Section Card */
.section-card {
  padding: 24px;
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(18px) saturate(180%);
  border: 1px solid #362d59;
  border-radius: 12px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-label {
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.7);
  letter-spacing: 0.2px;
  text-transform: uppercase;
}

.section-tag {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  letter-spacing: 0.2px;
}

.section-tag.real_data {
  background: rgba(194, 239, 78, 0.2);
  color: #c2ef4e;
}

.section-tag.no_credentials {
  background: rgba(251, 191, 36, 0.2);
  color: #fbbf24;
}

.alert-badge {
  padding: 4px 8px;
  background: rgba(248, 113, 113, 0.2);
  border-radius: 4px;
  color: #f87171;
  font-size: 12px;
  font-weight: 600;
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 40px 20px;
}

.empty-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.4);
}

.empty-icon svg {
  width: 32px;
  height: 32px;
}

.empty-icon.success {
  color: #c2ef4e;
}

.empty-text {
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.5);
  letter-spacing: 0.2px;
}

.empty-text.success {
  color: #c2ef4e;
}

/* Platform Grid */
.platform-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.platform-card {
  padding: 20px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 10px;
  border: 1px solid #362d59;
  transition: all 0.3s ease;
}

.platform-card:hover {
  background: rgba(255, 255, 255, 0.08);
}

.platform-card.connected {
  border-color: rgba(194, 239, 78, 0.25);
}

.platform-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.platform-icon {
  width: 36px;
  height: 36px;
  padding: 8px;
  border-radius: 8px;
  background: rgba(106, 95, 193, 0.2);
  color: #6a5fc1;
}

.platform-icon svg {
  width: 20px;
  height: 20px;
}

.platform-info {
  display: flex;
  flex-direction: column;
}

.platform-name {
  font-size: 14px;
  font-weight: 500;
  color: #ffffff;
}

.platform-status {
  font-size: 12px;
  font-weight: 500;
  letter-spacing: 0.2px;
}

.platform-status.connected {
  color: #c2ef4e;
}

.platform-status.disconnected {
  color: #f87171;
}

.platform-stats {
  display: flex;
  gap: 24px;
  margin-bottom: 12px;
}

.stat-item {
  display: flex;
  flex-direction: column;
}

.item-value {
  font-size: 18px;
  font-weight: 600;
  color: #ffffff;
}

.item-label {
  font-size: 10px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.5);
  letter-spacing: 0.25px;
  text-transform: uppercase;
}

.platform-source {
  display: flex;
  gap: 8px;
  font-size: 12px;
}

.source-label {
  color: rgba(255, 255, 255, 0.4);
}

.source-value {
  color: #6a5fc1;
}

/* Alerts List */
.alerts-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.alert-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 10px;
  border: 1px solid #362d59;
}

.alert-item.warning {
  border-color: rgba(251, 191, 36, 0.25);
}

.alert-item.critical {
  border-color: rgba(248, 113, 113, 0.25);
  background: rgba(248, 113, 113, 0.08);
}

.alert-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.5);
}

.alert-icon.warning { color: #fbbf24; }
.alert-icon.critical { color: #f87171; }

.alert-icon svg {
  width: 18px;
  height: 18px;
}

.alert-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.alert-header {
  display: flex;
  gap: 8px;
}

.alert-platform {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.alert-level {
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.alert-level.warning {
  background: rgba(251, 191, 36, 0.2);
  color: #fbbf24;
}

.alert-level.critical {
  background: rgba(248, 113, 113, 0.2);
  color: #f87171;
}

.alert-host {
  font-size: 14px;
  font-weight: 500;
  color: #ffffff;
}

.alert-message {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
}

/* Periodic Grid */
.periodic-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.periodic-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 8px;
}

.periodic-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6a5fc1;
}

.periodic-icon svg {
  width: 18px;
  height: 18px;
}

.periodic-content {
  flex: 1;
}

.periodic-name {
  font-size: 14px;
  font-weight: 500;
  color: #ffffff;
}

.periodic-count {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.periodic-count.has-items {
  color: #fbbf24;
}

/* Transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Responsive */
@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .platform-grid,
  .periodic-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .hero-section {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>