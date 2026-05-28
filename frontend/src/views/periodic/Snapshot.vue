<template>
  <div class="snapshot-page">
    <!-- Header Section -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-group">
          <svg class="header-icon" viewBox="0 0 24 24" fill="none">
            <rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" stroke-width="2"/>
            <circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="2"/>
            <path d="M12 8v-3M12 19v-3" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
          <h1 class="page-title">过期快照检查</h1>
        </div>
        <div class="schedule-badge">
          <svg viewBox="0 0 24 24" fill="none" class="badge-icon">
            <rect x="3" y="4" width="18" height="18" rx="2" stroke="currentColor" stroke-width="2"/>
            <path d="M16 2v4M8 2v4M3 10h18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
          <span>每周 - 周五执行</span>
        </div>
      </div>
      <div class="header-rules">
        <div class="rule-item">
          <span class="rule-label">阈值</span>
          <span class="rule-value">快照不超过7天</span>
        </div>
        <div class="rule-item">
          <span class="rule-label">规则</span>
          <span class="rule-value">删除过期快照(快照一律不超过7天)</span>
        </div>
      </div>
    </div>

    <!-- Stats Section -->
    <div class="stats-section">
      <div class="stat-card glass-card">
        <div class="stat-icon total">
          <svg viewBox="0 0 24 24" fill="none">
            <path d="M12 2L2 7l10 5 10-5-10-5z" stroke="currentColor" stroke-width="2"/>
            <path d="M2 17l10 5 10-5M2 12l10 5 10-5" stroke="currentColor" stroke-width="2"/>
          </svg>
        </div>
        <div class="stat-content">
          <span class="stat-value">{{ animatedTotal }}</span>
          <span class="stat-label">过期快照总数</span>
        </div>
      </div>

      <div class="stat-card glass-card critical">
        <div class="stat-icon">
          <svg viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
            <path d="M12 8v4M12 16h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </div>
        <div class="stat-content">
          <span class="stat-value critical">{{ animatedCritical }}</span>
          <span class="stat-label">严重 (>10天)</span>
        </div>
        <div class="stat-pulse"></div>
      </div>

      <div class="stat-card glass-card warning">
        <div class="stat-icon">
          <svg viewBox="0 0 24 24" fill="none">
            <path d="M12 9v2M12 15h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" stroke="currentColor" stroke-width="2"/>
          </svg>
        </div>
        <div class="stat-content">
          <span class="stat-value warning">{{ animatedWarning }}</span>
          <span class="stat-label">警告 (7-10天)</span>
        </div>
      </div>

      <div class="stat-card glass-card healthy" v-if="data.total === 0">
        <div class="stat-icon">
          <svg viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
            <path d="M9 12l2 2 4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <div class="stat-content">
          <span class="stat-value healthy">0</span>
          <span class="stat-label">所有快照正常</span>
        </div>
      </div>
    </div>

    <!-- Table Section -->
    <div class="table-section">
      <div class="table-card glass-card">
        <div class="table-header">
          <h3 class="table-title">快照详情列表</h3>
          <div class="table-actions">
            <button class="export-btn" @click="exportData">
              <svg viewBox="0 0 24 24" fill="none">
                <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <span>导出</span>
            </button>
          </div>
        </div>

        <div class="table-wrapper" v-if="data.data && data.data.length > 0">
          <table class="glass-table">
            <thead>
              <tr>
                <th style="width:90px">平台</th>
                <th style="width:180px">虚拟机名称</th>
                <th style="width:200px">快照名称</th>
                <th style="width:100px">快照天数</th>
                <th style="width:90px">阈值天数</th>
                <th style="width:80px">状态</th>
                <th style="width:180px">处理建议</th>
                <th style="width:160px">检查时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, index) in data.data" :key="index" class="table-row" :class="row.status">
                <td>
                  <div class="platform-badge" :class="row.platform">{{ row.platform }}</div>
                </td>
                <td>
                  <div class="cell-with-icon">
                    <svg viewBox="0 0 24 24" fill="none" class="cell-icon">
                      <rect x="2" y="3" width="20" height="14" rx="2" stroke="currentColor" stroke-width="2"/>
                      <path d="M8 21h8M12 17v4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                    </svg>
                    <span>{{ row.vm_name }}</span>
                  </div>
                </td>
                <td>
                  <div class="cell-with-icon">
                    <svg viewBox="0 0 24 24" fill="none" class="cell-icon snapshot">
                      <rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" stroke-width="2"/>
                      <circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="2"/>
                    </svg>
                    <span>{{ row.snapshot_name }}</span>
                  </div>
                </td>
                <td>
                  <div class="days-display" :class="{ critical: row.snapshot_days > 10, warning: row.snapshot_days > 7 }">
                    <span class="days-value">{{ row.snapshot_days }}</span>
                    <span class="days-unit">天</span>
                    <div class="days-bar">
                      <div class="days-progress" :style="{ width: Math.min(row.snapshot_days / 14 * 100, 100) + '%' }"></div>
                    </div>
                  </div>
                </td>
                <td class="threshold-cell">{{ row.threshold_days }} 天</td>
                <td>
                  <span class="status-badge" :class="row.status">
                    <svg viewBox="0 0 24 24" fill="none" class="status-icon">
                      <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                      <path v-if="row.status === 'critical'" d="M12 8v4M12 16h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                      <path v-else d="M12 9v2M12 15h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                    </svg>
                    {{ row.status === 'critical' ? '严重' : '警告' }}
                  </span>
                </td>
                <td><span class="action-text">{{ row.action }}</span></td>
                <td class="time-cell">{{ formatTime(row.check_time) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="empty-state" v-else>
          <div class="empty-icon">
            <svg viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
              <path d="M9 12l2 2 4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <h3 class="empty-title">{{ emptyTitle }}</h3>
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
  critical: 0,
  warning: 0,
  data: []
})
const pageStatus = ref('loading')
const pageMessage = ref('')

// Animated numbers
const animatedTotal = ref(0)
const animatedCritical = ref(0)
const animatedWarning = ref(0)

const emptyTitle = computed(() => {
  if (pageStatus.value === 'collection_failed' || pageStatus.value === 'error') return '采集失败'
  if (pageStatus.value === 'no_credentials') return '未配置凭证'
  return '所有快照正常'
})

const emptyDesc = computed(() => {
  if (pageStatus.value === 'no_credentials') return '未配置可用的 API 凭证'
  if (pageStatus.value === 'collection_failed' || pageStatus.value === 'error') return pageMessage.value || '快照巡检数据采集失败'
  if (pageStatus.value === 'partial_data') return pageMessage.value || '部分平台快照数据采集异常'
  return pageMessage.value || '当前没有超过阈值的过期快照'
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
    const response = await axios.get('/api/inspection/periodic/snapshot')
    pageStatus.value = response.data.status || 'unknown'
    pageMessage.value = response.data.message || ''
    data.value = response.data
    animateValue(data.value.total, animatedTotal)
    animateValue(data.value.critical, animatedCritical)
    animateValue(data.value.warning, animatedWarning)
  } catch (error) {
    console.error('加载快照检查数据失败:', error)
    pageStatus.value = 'error'
    pageMessage.value = '快照检查数据加载失败'
    data.value = { total: 0, critical: 0, warning: 0, data: [] }
  }
}

const formatTime = (time) => new Date(time).toLocaleString('zh-CN')

const exportData = () => {
  // CSV export logic
  const csv = data.value.data.map(row =>
    [row.platform, row.vm_name, row.snapshot_name, row.snapshot_days, row.threshold_days, row.status, row.action, formatTime(row.check_time)].join(',')
  )
  const blob = new Blob(['平台,虚拟机名称,快照名称,快照天数,阈值天数,状态,处理建议,检查时间\n' + csv.join('\n')], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `snapshot-check-${new Date().toISOString().split('T')[0]}.csv`
  a.click()
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.snapshot-page {
  padding: 24px;
  min-height: calc(100vh - 80px);
  background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 50%, #0d0d1f 100%);
}

/* Header */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 32px;
  flex-wrap: wrap;
  gap: 20px;
}

.header-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.title-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-icon {
  width: 32px;
  height: 32px;
  color: #a78bfa;
}

.page-title {
  font-size: 28px;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: 0.5px;
}

.schedule-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(167, 139, 250, 0.15);
  border: 1px solid rgba(167, 139, 250, 0.25);
  border-radius: 8px;
  color: #a78bfa;
  font-size: 14px;
}

.badge-icon {
  width: 18px;
  height: 18px;
}

.header-rules {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.rule-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.rule-label {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.5);
  padding: 4px 8px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 4px;
}

.rule-value {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.8);
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
  transform: translateY(-4px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
}

/* Stats Section */
.stats-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  position: relative;
}

.stat-card.critical {
  border-color: rgba(248, 113, 113, 0.25);
}

.stat-card.warning {
  border-color: rgba(251, 191, 36, 0.25);
}

.stat-card.healthy {
  border-color: rgba(52, 211, 153, 0.25);
}

.stat-icon {
  width: 48px;
  height: 48px;
  padding: 12px;
  border-radius: 12px;
  background: rgba(167, 139, 250, 0.2);
  color: #a78bfa;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-icon svg {
  width: 24px;
  height: 24px;
}

.stat-card.critical .stat-icon {
  background: rgba(248, 113, 113, 0.2);
  color: #f87171;
}

.stat-card.warning .stat-icon {
  background: rgba(251, 191, 36, 0.2);
  color: #fbbf24;
}

.stat-card.healthy .stat-icon {
  background: rgba(52, 211, 153, 0.2);
  color: #34d399;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #a78bfa;
}

.stat-value.critical { color: #f87171; }
.stat-value.warning { color: #fbbf24; }
.stat-value.healthy { color: #34d399; }

.stat-label {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
}

.stat-pulse {
  position: absolute;
  top: 0;
  right: 0;
  width: 100%;
  height: 100%;
  border-radius: 16px;
  background: radial-gradient(circle at top right, rgba(248, 113, 113, 0.2), transparent 50%);
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
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
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.table-title {
  font-size: 18px;
  font-weight: 600;
  color: #ffffff;
  margin: 0;
}

.table-actions {
  display: flex;
  gap: 12px;
}

.export-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: rgba(96, 165, 250, 0.2);
  border: 1px solid rgba(96, 165, 250, 0.3);
  border-radius: 8px;
  color: #60a5fa;
  cursor: pointer;
  transition: all 0.3s ease;
}

.export-btn:hover {
  background: rgba(96, 165, 250, 0.3);
  transform: translateY(-2px);
}

.export-btn svg {
  width: 18px;
  height: 18px;
}

.table-wrapper {
  overflow-x: auto;
}

.glass-table {
  width: 100%;
  min-width: 800px;
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
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.table-row {
  transition: background 0.2s ease;
}

.table-row:hover {
  background: rgba(255, 255, 255, 0.05);
}

.table-row.critical {
  background: rgba(248, 113, 113, 0.08);
}

.table-row.critical:hover {
  background: rgba(248, 113, 113, 0.12);
}

.table-row.warning {
  background: rgba(251, 191, 36, 0.05);
}

.table-row.warning:hover {
  background: rgba(251, 191, 36, 0.08);
}

.platform-badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  background: rgba(96, 165, 250, 0.2);
  color: #60a5fa;
}

.platform-badge.vmware { background: rgba(96, 165, 250, 0.2); color: #60a5fa; }
.platform-badge.smartx { background: rgba(52, 211, 153, 0.2); color: #34d399; }

.cell-with-icon {
  display: flex;
  align-items: center;
  gap: 8px;
}

.cell-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  color: rgba(255, 255, 255, 0.4);
}

.cell-icon.snapshot {
  color: rgba(167, 139, 250, 0.6);
}

.days-display {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.days-value {
  font-size: 18px;
  font-weight: 600;
  color: #34d399;
}

.days-value.critical { color: #f87171; }
.days-value.warning { color: #fbbf24; }

.days-unit {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.days-bar {
  width: 60px;
  height: 4px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
  overflow: hidden;
}

.days-progress {
  height: 100%;
  border-radius: 2px;
  background: linear-gradient(90deg, #34d399, #fbbf24, #f87171);
}

.threshold-cell {
  color: rgba(255, 255, 255, 0.6);
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge.critical {
  background: rgba(248, 113, 113, 0.2);
  color: #f87171;
}

.status-badge.warning {
  background: rgba(251, 191, 36, 0.2);
  color: #fbbf24;
}

.status-icon {
  width: 14px;
  height: 14px;
}

.action-text {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.7);
}

.time-cell {
  color: rgba(255, 255, 255, 0.5);
  font-size: 12px;
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.empty-icon {
  width: 64px;
  height: 64px;
  padding: 16px;
  background: rgba(52, 211, 153, 0.2);
  border-radius: 16px;
  color: #34d399;
  margin-bottom: 16px;
}

.empty-icon svg {
  width: 32px;
  height: 32px;
}

.empty-title {
  font-size: 18px;
  font-weight: 600;
  color: #ffffff;
  margin: 0 0 8px 0;
}

.empty-desc {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
  margin: 0;
}

/* Responsive */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
  }

  .stats-section {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>