<template>
  <div class="inspection-page">
    <!-- Header Section -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-group">
          <div class="header-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="8" x2="12" y2="12"/>
              <line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
          </div>
          <div class="title-text">
            <h1 class="page-title">DAILY INSPECTION</h1>
            <p class="page-subtitle">11 inspection items for infrastructure monitoring</p>
          </div>
        </div>
      </div>
      <button class="btn-glass" @click="loadData" :disabled="loading">
        <svg class="btn-icon" :class="{ spinning: loading }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="23 4 23 10 17 10"/>
          <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10"/>
        </svg>
        <span class="btn-text">{{ loading ? 'REFRESHING...' : 'REFRESH' }}</span>
      </button>
    </div>

    <!-- Filter Section -->
    <div class="filter-section">
      <div class="filter-card">
        <div class="filter-group">
          <label class="filter-label">
            <span class="label-text">CATEGORY</span>
          </label>
          <div class="select-wrapper">
            <select v-model="selectedCategory" @change="loadData" class="glass-select">
              <option value="">All Categories</option>
              <option value="虚拟化">Virtualization</option>
              <option value="云桌面">Cloud Desktop</option>
              <option value="数据库">Database</option>
              <option value="日志易">Log</option>
              <option value="存储">Storage</option>
              <option value="备份">Backup</option>
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
            <select v-model="selectedPlatform" @change="loadData" class="glass-select">
              <option value="">All Platforms</option>
              <option v-for="p in platforms" :key="p.code" :value="p.code">{{ p.name }}</option>
            </select>
            <svg class="select-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M7 10l5 5 5-5"/>
            </svg>
          </div>
        </div>

        <div class="filter-group">
          <label class="filter-label">
            <span class="label-text">STATUS</span>
          </label>
          <div class="select-wrapper">
            <select v-model="selectedStatus" @change="loadData" class="glass-select">
              <option value="">All Status</option>
              <option value="normal">Normal</option>
              <option value="warning">Warning</option>
              <option value="critical">Critical</option>
            </select>
            <svg class="select-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M7 10l5 5 5-5"/>
            </svg>
          </div>
        </div>

        <div class="filter-summary">
          <span class="summary-count">{{ hosts.length }} records</span>
          <span class="summary-time">{{ lastCheckTime }}</span>
        </div>
      </div>
    </div>

    <!-- Stats Section -->
    <div class="stats-section">
      <div class="stat-card">
        <div class="stat-icon total">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="2" y="3" width="20" height="14" rx="2"/>
          </svg>
        </div>
        <div class="stat-content">
          <span class="stat-value">{{ statistics.total }}</span>
          <span class="stat-label">TOTAL</span>
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
          <span class="stat-value">{{ statistics.normal }}</span>
          <span class="stat-label">NORMAL</span>
        </div>
      </div>

      <div class="stat-card" :class="{ warning: statistics.warning > 0 }">
        <div class="stat-icon warning">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94"/>
          </svg>
        </div>
        <div class="stat-content">
          <span class="stat-value" :class="{ warning: statistics.warning > 0 }">{{ statistics.warning }}</span>
          <span class="stat-label">WARNING</span>
        </div>
      </div>

      <div class="stat-card" :class="{ critical: statistics.critical > 0 }">
        <div class="stat-icon critical">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="15" y1="9" x2="9" y2="15"/>
          </svg>
        </div>
        <div class="stat-content">
          <span class="stat-value" :class="{ critical: statistics.critical > 0 }">{{ statistics.critical }}</span>
          <span class="stat-label">CRITICAL</span>
        </div>
      </div>
    </div>

    <!-- Hosts Table -->
    <div class="table-section">
      <div class="table-card">
        <div class="table-header">
          <span class="table-label">INSPECTION HOSTS</span>
        </div>

        <!-- Empty State -->
        <div class="empty-state" v-if="hosts.length === 0">
          <div class="empty-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <path d="M12 6v6"/>
              <path d="M12 16h.01"/>
            </svg>
          </div>
          <span class="empty-text">{{ emptyText }}</span>
        </div>

        <!-- Table -->
        <div class="table-wrapper" v-else>
          <table class="glass-table">
            <thead>
              <tr>
                <th style="width:80px">平台</th>
                <th style="width:100px">集群</th>
                <th style="width:140px">主机</th>
                <th style="width:70px">状态</th>
                <th style="width:260px">巡检摘要</th>
                <th style="width:100px">操作</th>
                <th style="width:140px">检查时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="host in hosts" :key="host.host_name" :class="host.status">
                <td><span class="category-tag">{{ host.platform_name }}</span></td>
                <td>{{ host.cluster_name || '--' }}</td>
                <td class="host-cell">{{ host.host_name }}</td>
                <td><span class="status-badge" :class="host.status">{{ host.status === 'normal' ? '正常' : host.status === 'warning' ? '警告' : '严重' }}</span></td>
                <td>
                  <div class="items-summary">
                    <span class="summary-chip" v-for="(value, key) in host.inspection_items" :key="key" :class="getItemClass(value)">
                      {{ key }}: {{ value.length > 20 ? value.substring(0, 20) + '...' : value }}
                    </span>
                  </div>
                </td>
                <td>
                  <button class="detail-btn" @click="openDetail(host)">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/></svg>
                    详情
                  </button>
                </td>
                <td class="time-cell">{{ formatTime(host.check_time) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 巡检详情弹窗 -->
        <div class="modal-overlay" v-if="showDetailModal" @click.self="showDetailModal = false">
          <div class="modal-content">
            <div class="modal-header">
              <div class="modal-title-group">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="modal-icon">
                  <rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/>
                </svg>
                <div>
                  <h3>{{ detailHost?.host_name }}</h3>
                  <p class="modal-subtitle">{{ detailHost?.platform_name }} · {{ detailHost?.cluster_name }}</p>
                </div>
              </div>
              <button class="modal-close" @click="showDetailModal = false">&times;</button>
            </div>

            <!-- 状态和时间 -->
            <div class="modal-status-row">
              <span class="status-badge" :class="detailHost?.status">{{ detailHost?.status === 'normal' ? '正常' : detailHost?.status === 'warning' ? '警告' : '严重' }}</span>
              <span class="modal-time">检查时间: {{ formatTime(detailHost?.check_time) }}</span>
            </div>

            <!-- 巡检项目详情 -->
            <div class="modal-section">
              <h4 class="section-title">巡检项目</h4>
              <div class="items-detail-grid">
                <div class="item-detail-card" v-for="(value, key) in detailHost?.inspection_items" :key="key">
                  <div class="item-detail-header">
                    <span class="item-detail-label" :class="getItemClass(value)">{{ key }}</span>
                  </div>
                  <div class="item-detail-value">{{ value }}</div>
                  <div class="item-detail-bar" v-if="value.includes('%')">
                    <div class="item-detail-bar-fill" :class="getItemClass(value)" :style="{ width: parseFloat(value) + '%' }"></div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 资源详情 -->
            <div class="modal-section" v-if="detailHost?.host_detail">
              <h4 class="section-title">资源详情</h4>
              <div class="resource-detail-grid">
                <div class="resource-detail-card cpu">
                  <div class="resource-detail-header">
                    <span class="resource-detail-label">CPU</span>
                    <span class="resource-detail-value">{{ detailHost.host_detail.cpu_percent.toFixed(1) }}%</span>
                  </div>
                  <div class="resource-detail-bar"><div class="resource-detail-bar-fill cpu" :style="{ width: detailHost.host_detail.cpu_percent + '%' }"></div></div>
                  <div class="resource-detail-stats">
                    <span>可用: {{ detailHost.host_detail.cpu_avail_ghz }} GHz</span>
                    <span>已用: {{ detailHost.host_detail.cpu_used_ghz }} GHz</span>
                    <span>总计: {{ detailHost.host_detail.cpu_total_ghz }} GHz</span>
                    <span>核心: {{ detailHost.host_detail.cpu_cores }} 核</span>
                  </div>
                </div>
                <div class="resource-detail-card memory">
                  <div class="resource-detail-header">
                    <span class="resource-detail-label">内存</span>
                    <span class="resource-detail-value">{{ detailHost.host_detail.mem_percent.toFixed(1) }}%</span>
                  </div>
                  <div class="resource-detail-bar"><div class="resource-detail-bar-fill memory" :style="{ width: detailHost.host_detail.mem_percent + '%' }"></div></div>
                  <div class="resource-detail-stats">
                    <span>可用: {{ (detailHost.host_detail.mem_total_gb - detailHost.host_detail.mem_used_gb).toFixed(2) }} GB</span>
                    <span>已用: {{ detailHost.host_detail.mem_used_gb }} GB</span>
                    <span>总计: {{ detailHost.host_detail.mem_total_gb }} GB</span>
                  </div>
                </div>
                <div class="resource-detail-card storage">
                  <div class="resource-detail-header">
                    <span class="resource-detail-label">存储</span>
                    <span class="resource-detail-value">{{ detailHost.host_detail.storage_percent.toFixed(1) }}%</span>
                  </div>
                  <div class="resource-detail-bar"><div class="resource-detail-bar-fill storage" :style="{ width: detailHost.host_detail.storage_percent + '%' }"></div></div>
                </div>
                <div class="resource-detail-card info">
                  <div class="resource-detail-header">
                    <span class="resource-detail-label">运行信息</span>
                  </div>
                  <div class="resource-detail-stats">
                    <span>虚拟机: {{ detailHost.host_detail.vm_count }} 台</span>
                    <span>运行天数: {{ detailHost.host_detail.uptime_days }} 天</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const route = useRoute()

const selectedCategory = ref('')
const selectedPlatform = ref(route.query.platform || '')
const selectedStatus = ref('')
const hosts = ref([])
const selectedHost = ref(null)
const showDetailModal = ref(false)
const detailHost = ref(null)
const platforms = ref([])
const statistics = ref({ total: 0, normal: 0, warning: 0, critical: 0 })
const loading = ref(false)
const lastCheckTime = ref('--')
const pageStatus = ref('loading')
const pageMessage = ref('')

const dialogVisible = ref(false)

const emptyText = computed(() => {
  if (pageStatus.value === 'no_credentials') return '未配置可用的 API 凭证'
  if (pageStatus.value === 'collection_failed' || pageStatus.value === 'error') return pageMessage.value || '巡检数据采集失败'
  if (pageStatus.value === 'partial_data') return pageMessage.value || '部分平台巡检数据采集异常'
  return pageMessage.value || '当前没有符合条件的巡检记录'
})

const loadData = async () => {
  loading.value = true
  try {
    const params = {
      category: selectedCategory.value || undefined,
      platform: selectedPlatform.value || undefined,
      status: selectedStatus.value || undefined,
    }

    const response = await axios.get('/api/inspection/list', { params })
    pageStatus.value = response.data.status || 'unknown'
    pageMessage.value = response.data.message || ''
    hosts.value = response.data.data || []
    platforms.value = response.data.platforms || []
    statistics.value = {
      total: response.data.total || 0,
      normal: hosts.value.filter(h => h.status === 'normal').length,
      warning: hosts.value.filter(h => h.status === 'warning').length,
      critical: hosts.value.filter(h => h.status === 'critical').length,
    }
    lastCheckTime.value = response.data.last_check_time ? formatTime(response.data.last_check_time) : '--'
  } catch (error) {
    console.error('Inspection load failed:', error)
    pageStatus.value = 'error'
    pageMessage.value = '巡检数据加载失败'
    hosts.value = []
    statistics.value = { total: 0, normal: 0, warning: 0, critical: 0 }
    lastCheckTime.value = '--'
  } finally {
    loading.value = false
  }
}

const openDetail = (host) => {
  detailHost.value = host
  showDetailModal.value = true
}

const getItemClass = (value) => {
  if (typeof value === 'string') {
    if (value === 'normal') return 'success'
    if (value === 'warning' || value === 'failed') return 'warning'
    if (value === 'critical') return 'critical'
    // Extract percentage from values like "使用率: 89.98%"
    const pctMatch = value.match(/(\d+\.?\d*)%/)
    if (pctMatch) {
      const pct = parseFloat(pctMatch[1])
      if (pct >= 80) return 'critical'
      if (pct >= 60) return 'warning'
      return 'success'
    }
  }
  return ''
}

const getProgressClass = (value) => {
  if (value >= 80) return 'critical'
  if (value >= 70) return 'warning'
  return 'success'
}

const formatTime = (time) => {
  if (!time) return '--'
  return new Date(time).toLocaleString('zh-CN')
}

const showHostDetail = (host) => {
  selectedHost.value = host
  dialogVisible.value = true
}

const viewHistory = () => {
  if (selectedHost.value) {
    router.push(`/history?host=${selectedHost.value.host_name}`)
    dialogVisible.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Rubik:wght@400;500;600;700&display=swap');

.inspection-page {
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
  background: rgba(194, 239, 78, 0.1);
  border-radius: 12px;
  border: 1px solid rgba(194, 239, 78, 0.25);
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
}

.btn-glass:hover:not(:disabled) {
  background: rgba(54, 22, 107, 0.14);
}

.btn-glass:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-icon {
  width: 16px;
  height: 16px;
}

.btn-icon.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
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

.filter-summary {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-left: auto;
}

.summary-count {
  font-size: 14px;
  font-weight: 500;
  color: #ffffff;
}

.summary-time {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

/* Stats Section */
.stats-section {
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

.stat-label {
  font-size: 12px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.5);
  letter-spacing: 0.2px;
  text-transform: uppercase;
}

/* Table Section */
.table-section {
  flex: 1;
}

.table-card {
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(18px) saturate(180%);
  border: 1px solid #362d59;
  border-radius: 12px;
  padding: 24px;
}

.table-header {
  margin-bottom: 16px;
}

.table-label {
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.7);
  letter-spacing: 0.2px;
  text-transform: uppercase;
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

.empty-icon svg {
  width: 32px;
  height: 32px;
}

.empty-text {
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.5);
  letter-spacing: 0.2px;
}

/* Table */
.table-wrapper {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

.glass-table {
  width: 100%;
  min-width: 1000px;
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
  white-space: nowrap;
  position: sticky;
  top: 0;
  z-index: 1;
}

.glass-table td {
  padding: 12px 10px;
  color: #ffffff;
  font-size: 13px;
  border-bottom: 1px solid rgba(54, 45, 89, 0.5);
  max-width: 280px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.glass-table tr {
  cursor: pointer;
  transition: all 0.3s ease;
}

.glass-table tr:hover {
  background: rgba(255, 255, 255, 0.05);
}

.glass-table tr.warning {
  background: rgba(251, 191, 36, 0.05);
}

.glass-table tr.critical {
  background: rgba(248, 113, 113, 0.08);
}

.category-tag {
  padding: 4px 10px;
  background: rgba(106, 95, 193, 0.2);
  border-radius: 4px;
  color: #6a5fc1;
  font-size: 12px;
}

.host-cell {
  font-weight: 500;
}

.status-badge {
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge.normal {
  background: rgba(194, 239, 78, 0.2);
  color: #c2ef4e;
}

.status-badge.warning {
  background: rgba(251, 191, 36, 0.2);
  color: #fbbf24;
}

.status-badge.critical {
  background: rgba(248, 113, 113, 0.2);
  color: #f87171;
}

.items-grid {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.item-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.item-label {
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.5);
  min-width: 50px;
  text-align: center;
}

.item-label.success { background: rgba(194, 239, 78, 0.15); color: #c2ef4e; }
.item-label.warning { background: rgba(251, 191, 36, 0.15); color: #fbbf24; }
.item-label.critical { background: rgba(248, 113, 113, 0.15); color: #f87171; }

.item-value {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
}

.time-cell {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.items-summary { display: flex; flex-wrap: wrap; gap: 4px; }
.summary-chip { padding: 2px 6px; background: rgba(255,255,255,0.06); border-radius: 4px; font-size: 10px; color: rgba(255,255,255,0.5); white-space: nowrap; }
.summary-chip.success { background: rgba(194,239,78,0.1); color: #c2ef4e; }
.summary-chip.warning { background: rgba(251,191,36,0.1); color: #fbbf24; }
.summary-chip.critical { background: rgba(248,113,113,0.1); color: #f87171; }

.detail-btn { display: flex; align-items: center; gap: 6px; padding: 5px 10px; background: rgba(106,95,193,0.15); border: 1px solid rgba(106,95,193,0.25); border-radius: 6px; color: #a78bfa; font-size: 12px; cursor: pointer; transition: all 0.2s; white-space: nowrap; }
.detail-btn:hover { background: rgba(106,95,193,0.25); }
.detail-btn svg { width: 14px; height: 14px; }

/* Modal */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.6); backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-content { background: #1c1735; border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; width: 680px; max-height: 85vh; overflow-y: auto; box-shadow: 0 20px 60px rgba(0,0,0,0.4); }
.modal-header { display: flex; justify-content: space-between; align-items: flex-start; padding: 20px 24px; border-bottom: 1px solid #362d59; }
.modal-title-group { display: flex; align-items: center; gap: 12px; }
.modal-icon { width: 36px; height: 36px; color: #6a5fc1; background: rgba(106,95,193,0.15); border-radius: 10px; padding: 8px; }
.modal-header h3 { font-size: 18px; font-weight: 600; color: #fff; margin: 0; }
.modal-subtitle { font-size: 13px; color: rgba(255,255,255,0.4); margin: 2px 0 0 0; }
.modal-close { background: rgba(255,255,255,0.08); border: none; color: rgba(255,255,255,0.5); font-size: 22px; cursor: pointer; width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; }
.modal-close:hover { background: rgba(255,255,255,0.15); color: #fff; }

.modal-status-row { display: flex; align-items: center; gap: 12px; padding: 14px 24px; border-bottom: 1px solid rgba(255,255,255,0.06); }
.modal-time { font-size: 12px; color: rgba(255,255,255,0.4); }

.modal-section { padding: 18px 24px; border-bottom: 1px solid rgba(255,255,255,0.06); }
.modal-section:last-child { border-bottom: none; }
.section-title { font-size: 13px; font-weight: 600; color: rgba(255,255,255,0.5); text-transform: uppercase; letter-spacing: 0.3px; margin: 0 0 14px 0; }

.items-detail-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 10px; }
.item-detail-card { padding: 14px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; transition: all 0.2s; }
.item-detail-card:hover { background: rgba(255,255,255,0.06); }
.item-detail-header { margin-bottom: 6px; }
.item-detail-label { padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.3px; }
.item-detail-label.success { background: rgba(194,239,78,0.15); color: #c2ef4e; }
.item-detail-label.warning { background: rgba(251,191,36,0.15); color: #fbbf24; }
.item-detail-label.critical { background: rgba(248,113,113,0.15); color: #f87171; }
.item-detail-value { font-size: 13px; color: #fff; margin-bottom: 6px; word-break: break-all; }
.item-detail-bar { width: 100%; height: 3px; background: rgba(255,255,255,0.1); border-radius: 2px; overflow: hidden; }
.item-detail-bar-fill { height: 100%; border-radius: 2px; transition: width 0.5s; }
.item-detail-bar-fill.success { background: #c2ef4e; }
.item-detail-bar-fill.warning { background: #fbbf24; }
.item-detail-bar-fill.critical { background: #f87171; }

.resource-detail-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; }
.resource-detail-card { padding: 16px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; transition: all 0.2s; }
.resource-detail-card:hover { background: rgba(255,255,255,0.06); border-color: rgba(255,255,255,0.12); }
.resource-detail-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.resource-detail-label { font-size: 12px; font-weight: 600; color: rgba(255,255,255,0.5); text-transform: uppercase; letter-spacing: 0.3px; }
.resource-detail-value { font-size: 20px; font-weight: 700; color: #fff; }
.resource-detail-bar { width: 100%; height: 8px; background: rgba(255,255,255,0.06); border-radius: 4px; overflow: hidden; margin-bottom: 10px; }
.resource-detail-bar-fill { height: 100%; border-radius: 4px; transition: width 0.6s ease; }
.resource-detail-bar-fill.cpu { background: linear-gradient(90deg, #818cf8, #6366f1); }
.resource-detail-bar-fill.memory { background: linear-gradient(90deg, #34d399, #10b981); }
.resource-detail-bar-fill.storage { background: linear-gradient(90deg, #fbbf24, #f59e0b); }
.resource-detail-stats { display: flex; flex-direction: column; gap: 3px; }
.resource-detail-stats span { font-size: 12px; color: rgba(255,255,255,0.4); }

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.detail-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #fff;
  margin: 0;
}

.close-btn {
  background: rgba(255, 255, 255, 0.08);
  border: none;
  color: rgba(255, 255, 255, 0.5);
  font-size: 20px;
  cursor: pointer;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}

.detail-card {
  padding: 16px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
}

.detail-card.cpu { border-left: 3px solid #6a5fc1; }
.detail-card.memory { border-left: 3px solid #34d399; }
.detail-card.storage { border-left: 3px solid #fbbf24; }
.detail-card.info { border-left: 3px solid #60a5fa; }

.detail-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.detail-card-label {
  font-size: 13px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.7);
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.detail-card-value {
  font-size: 20px;
  font-weight: 700;
  color: #fff;
}

.detail-bar {
  width: 100%;
  height: 6px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 10px;
}

.detail-bar-fill {
  height: 100%;
  border-radius: 3px;
  background: linear-gradient(90deg, #34d399, #fbbf24, #f87171);
  transition: width 0.5s ease;
}

.detail-stats {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-stats span {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.detail-extra {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
  margin-top: 6px;
}

.details-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 8px;
}

.detail-key {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
}

.detail-val {
  display: flex;
  align-items: center;
}

.progress-bar {
  width: 200px;
  height: 24px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  position: relative;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 6px;
}

.progress-fill.success { background: #c2ef4e; }
.progress-fill.warning { background: #fbbf24; }
.progress-fill.critical { background: #f87171; }

.progress-text {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  font-size: 12px;
  color: #ffffff;
  font-weight: 500;
}

.value-tag {
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
}

.value-tag.success {
  background: rgba(194, 239, 78, 0.2);
  color: #c2ef4e;
}

.value-tag.warning {
  background: rgba(251, 191, 36, 0.2);
  color: #fbbf24;
}

.value-tag.critical {
  background: rgba(248, 113, 113, 0.2);
  color: #f87171;
}

.data-source {
  display: flex;
  gap: 8px;
  padding: 12px;
  background: rgba(194, 239, 78, 0.1);
  border-radius: 8px;
  margin-top: 16px;
}

.source-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.source-value {
  font-size: 12px;
  color: #c2ef4e;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #362d59;
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
  .stats-section {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .filter-card {
    flex-wrap: wrap;
  }

  .stats-section {
    grid-template-columns: 1fr;
  }

  .modal-content {
    width: 100%;
    max-height: 100vh;
    border-radius: 0;
  }
}
</style>