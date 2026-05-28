<template>
  <div class="idle-vm-page">
    <!-- Header Section -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-group">
          <svg class="header-icon" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
            <path d="M8 12h8M12 8v8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
          <h1 class="page-title">闲置资产排查</h1>
        </div>
        <div class="schedule-badge">
          <svg viewBox="0 0 24 24" fill="none" class="badge-icon">
            <rect x="3" y="4" width="18" height="18" rx="2" stroke="currentColor" stroke-width="2"/>
            <path d="M16 2v4M8 2v4M3 10h18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
          <span>每月 - 最后一个工作日</span>
        </div>
      </div>
    </div>

    <!-- Rule Banner -->
    <div class="rule-banner glass-card">
      <svg viewBox="0 0 24 24" fill="none" class="banner-icon">
        <path d="M12 2L2 7l10 5 10-5-10-5z" stroke="currentColor" stroke-width="2"/>
        <path d="M2 17l10 5 10-5" stroke="currentColor" stroke-width="2"/>
      </svg>
      <div class="banner-content">
        <span class="banner-label">管理规则</span>
        <p class="banner-text">涉及克隆、备份恢复的虚拟机，如果不是长期使用，虚拟机名一律tmp-开头，备注一律临时-开头</p>
      </div>
    </div>

    <!-- Stats Section -->
    <div class="stats-section">
      <div class="stat-card glass-card">
        <div class="stat-icon idle">
          <svg viewBox="0 0 24 24" fill="none">
            <rect x="2" y="3" width="20" height="14" rx="2" stroke="currentColor" stroke-width="2"/>
            <path d="M8 21h8M12 17v4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            <circle cx="12" cy="10" r="2" stroke="currentColor" stroke-width="2"/>
          </svg>
        </div>
        <div class="stat-content">
          <span class="stat-value">{{ animatedTotal }}</span>
          <span class="stat-label">闲置虚拟机数</span>
        </div>
        <div class="stat-pulse" v-if="data.total > 0"></div>
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
          <span class="stat-label">所有资产正常使用</span>
        </div>
      </div>
    </div>

    <!-- Table Section -->
    <div class="table-section">
      <div class="table-card glass-card">
        <div class="table-header">
          <h3 class="table-title">闲置虚拟机列表</h3>
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
                <th style="width:160px">虚拟机名称</th>
                <th style="width:120px">IP地址</th>
                <th style="width:150px">备注</th>
                <th style="width:60px">CPU</th>
                <th style="width:70px">内存</th>
                <th style="width:70px">磁盘</th>
                <th style="width:80px">电源状态</th>
                <th style="width:80px">创建天数</th>
                <th style="width:180px">处理建议</th>
                <th style="width:140px">检查时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, index) in data.data" :key="index" class="table-row warning">
                <td class="vm-cell">
                  <svg viewBox="0 0 24 24" fill="none" class="vm-icon warning">
                    <rect x="2" y="3" width="20" height="14" rx="2" stroke="currentColor" stroke-width="2"/>
                    <path d="M8 21h8M12 17v4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                  </svg>
                  <span class="vm-name">{{ row.vm_name }}</span>
                </td>
                <td class="ip-cell">
                  <span class="ip-badge">{{ row.ip }}</span>
                </td>
                <td class="note-cell">
                  <span class="note-text">{{ row.note || '无备注' }}</span>
                </td>
                <td class="resource-cell">
                  <span class="resource-value">{{ row.cpu }}</span>
                </td>
                <td class="resource-cell">
                  <span class="resource-value">{{ row.memory_gb }} GB</span>
                </td>
                <td class="resource-cell">
                  <span class="resource-value">{{ row.disk_gb }} GB</span>
                </td>
                <td>
                  <span class="power-badge" :class="row.power_state === 'poweredOn' ? 'on' : 'off'">
                    <svg viewBox="0 0 24 24" fill="none" class="power-icon">
                      <path d="M12 2v10M18.4 6.6a9 9 0 11-12.77.04" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                    </svg>
                    {{ row.power_state === 'poweredOn' ? '运行' : '关机' }}
                  </span>
                </td>
                <td>
                  <div class="days-display">
                    <span class="days-value">{{ row.created_days }}</span>
                    <span class="days-unit">天</span>
                  </div>
                </td>
                <td class="action-cell">
                  <span class="action-text">{{ row.action }}</span>
                </td>
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
          <h3 class="empty-title">所有资产正常使用</h3>
          <p class="empty-desc">当前没有发现闲置的虚拟机资产</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const data = ref({
  total: 0,
  rule: '',
  data: []
})

const animatedTotal = ref(0)

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
    const response = await axios.get('/api/inspection/periodic/idle-vm')
    data.value = response.data
    animateValue(data.value.total, animatedTotal)
  } catch (error) {
    console.error('加载闲置资产数据失败:', error)
  }
}

const formatTime = (time) => new Date(time).toLocaleString('zh-CN')

const exportData = () => {
  const csv = data.value.data.map(row =>
    [row.vm_name, row.ip, row.note, row.cpu, row.memory_gb, row.disk_gb, row.power_state, row.created_days, row.action, formatTime(row.check_time)].join(',')
  )
  const blob = new Blob(['虚拟机名称,IP地址,备注,CPU,内存GB,磁盘GB,电源状态,创建天数,处理建议,检查时间\n' + csv.join('\n')], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `idle-vm-check-${new Date().toISOString().split('T')[0]}.csv`
  a.click()
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.idle-vm-page {
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
  color: #fbbf24;
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
  background: rgba(251, 191, 36, 0.15);
  border: 1px solid rgba(251, 191, 36, 0.25);
  border-radius: 8px;
  color: #fbbf24;
  font-size: 14px;
}

.badge-icon {
  width: 18px;
  height: 18px;
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

/* Rule Banner */
.rule-banner {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 24px;
  margin-bottom: 24px;
}

.banner-icon {
  width: 40px;
  height: 40px;
  padding: 10px;
  background: rgba(96, 165, 250, 0.2);
  border-radius: 10px;
  color: #60a5fa;
}

.banner-icon svg {
  width: 20px;
  height: 20px;
}

.banner-content {
  flex: 1;
}

.banner-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  padding: 2px 8px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
}

.banner-text {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
  margin: 4px 0 0 0;
  line-height: 1.5;
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

.stat-icon {
  width: 48px;
  height: 48px;
  padding: 12px;
  border-radius: 12px;
  background: rgba(251, 191, 36, 0.2);
  color: #fbbf24;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-icon.idle {
  background: rgba(167, 139, 250, 0.2);
  color: #a78bfa;
}

.stat-icon svg {
  width: 24px;
  height: 24px;
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
  color: #fbbf24;
}

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
  background: radial-gradient(circle at top right, rgba(251, 191, 36, 0.15), transparent 50%);
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
  transition: all 0.3s ease;
}

.table-row:hover {
  background: rgba(255, 255, 255, 0.05);
}

.table-row.warning {
  background: rgba(251, 191, 36, 0.05);
}

.table-row.warning:hover {
  background: rgba(251, 191, 36, 0.08);
}

.vm-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.vm-icon {
  width: 18px;
  height: 18px;
  color: rgba(255, 255, 255, 0.4);
}

.vm-icon.warning { color: #fbbf24; }

.vm-name {
  color: #fbbf24;
  font-weight: 500;
}

.ip-badge {
  padding: 4px 8px;
  background: rgba(52, 211, 153, 0.15);
  border-radius: 4px;
  color: #34d399;
  font-size: 12px;
}

.note-cell {
  max-width: 150px;
}

.note-text {
  color: rgba(255, 255, 255, 0.6);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.resource-cell {
  color: rgba(255, 255, 255, 0.8);
}

.resource-value {
  font-size: 13px;
}

.power-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 12px;
}

.power-badge.on {
  background: rgba(52, 211, 153, 0.2);
  color: #34d399;
}

.power-badge.off {
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.6);
}

.power-icon {
  width: 12px;
  height: 12px;
}

.days-display {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.days-value {
  font-size: 16px;
  font-weight: 600;
  color: #fbbf24;
}

.days-unit {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.action-cell {
  max-width: 120px;
}

.action-text {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
}

.time-cell {
  color: rgba(255, 255, 255, 0.4);
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
</style>