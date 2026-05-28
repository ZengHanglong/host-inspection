<template>
  <div class="naming-page">
    <!-- Header Section -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-group">
          <svg class="header-icon" viewBox="0 0 24 24" fill="none">
            <path d="M17 3a2.83 2.83 0 114 4L7.5 20.5 2 22l1.5-5.5L17 3z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <h1 class="page-title">备注字段/虚拟机命名维护</h1>
        </div>
        <div class="schedule-badge">
          <svg viewBox="0 0 24 24" fill="none" class="badge-icon">
            <rect x="3" y="4" width="18" height="18" rx="2" stroke="currentColor" stroke-width="2"/>
            <path d="M16 2v4M8 2v4M3 10h18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
          <span>每周 - 周五执行</span>
        </div>
      </div>
    </div>

    <!-- Rules Section -->
    <div class="rules-section">
      <div class="rules-card glass-card">
        <div class="rules-header">
          <svg viewBox="0 0 24 24" fill="none" class="rules-icon">
            <path d="M12 2L2 7l10 5 10-5-10-5z" stroke="currentColor" stroke-width="2"/>
            <path d="M2 17l10 5 10-5" stroke="currentColor" stroke-width="2"/>
            <path d="M2 12l10 5 10-5" stroke="currentColor" stroke-width="2"/>
          </svg>
          <h3 class="rules-title">命名规则说明</h3>
        </div>
        <div class="rules-grid">
          <div class="rule-box">
            <div class="rule-label">
              <svg viewBox="0 0 24 24" fill="none" class="label-icon">
                <rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" stroke-width="2"/>
                <path d="M7 7h10M7 12h10M7 17h4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
              <span>备注格式</span>
            </div>
            <div class="rule-content">{{ data.rules?.备注格式 || '待配置' }}</div>
          </div>
          <div class="rule-box">
            <div class="rule-label">
              <svg viewBox="0 0 24 24" fill="none" class="label-icon">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                <path d="M8 12h8M12 8v8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
              <span>命名格式</span>
            </div>
            <div class="rule-content">{{ data.rules?.命名格式 || '待配置' }}</div>
          </div>
          <div class="rule-box wide">
            <div class="rule-label">
              <svg viewBox="0 0 24 24" fill="none" class="label-icon">
                <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" stroke="currentColor" stroke-width="2"/>
                <path d="M14 2v6h6M16 13H8M16 17H8M10 9H8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
              <span>命名规则</span>
            </div>
            <div class="rule-content">{{ data.rules?.命名规则 || '待配置' }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Stats Section -->
    <div class="stats-section">
      <div class="stat-card glass-card">
        <div class="stat-icon">
          <svg viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
            <path d="M12 8v4M12 16h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </div>
        <div class="stat-content">
          <span class="stat-value">{{ animatedTotal }}</span>
          <span class="stat-label">问题虚拟机数</span>
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
          <span class="stat-label">所有命名符合规范</span>
        </div>
      </div>
    </div>

    <!-- Table Section -->
    <div class="table-section">
      <div class="table-card glass-card">
        <div class="table-header">
          <h3 class="table-title">问题虚拟机列表</h3>
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
                <th style="width:180px">虚拟机名称</th>
                <th style="width:130px">IP地址</th>
                <th style="width:200px">当前备注</th>
                <th style="width:200px">问题项</th>
                <th style="width:160px">检查时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, index) in data.data" :key="index" class="table-row warning">
                <td class="vm-cell">
                  <svg viewBox="0 0 24 24" fill="none" class="vm-icon">
                    <rect x="2" y="3" width="20" height="14" rx="2" stroke="currentColor" stroke-width="2"/>
                    <path d="M8 21h8M12 17v4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                  </svg>
                  {{ row.vm_name }}
                </td>
                <td class="ip-cell">
                  <span class="ip-badge">{{ row.ip }}</span>
                </td>
                <td class="note-cell">
                  <div class="note-content">
                    <svg viewBox="0 0 24 24" fill="none" class="note-icon">
                      <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" stroke="currentColor" stroke-width="2"/>
                      <path d="M14 2v6h6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                    </svg>
                    <span class="note-text">{{ row.current_note || '无备注' }}</span>
                  </div>
                </td>
                <td class="issues-cell">
                  <div class="issues-tags">
                    <span v-for="issue in row.issues" :key="issue" class="issue-tag">
                      <svg viewBox="0 0 24 24" fill="none" class="issue-icon">
                        <path d="M12 9v2M12 15h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                        <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" stroke="currentColor" stroke-width="2"/>
                      </svg>
                      {{ issue }}
                    </span>
                  </div>
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
          <h3 class="empty-title">所有命名符合规范</h3>
          <p class="empty-desc">当前没有发现命名或备注问题的虚拟机</p>
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
  rules: {},
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
    const response = await axios.get('/api/inspection/periodic/naming')
    data.value = response.data
    animateValue(data.value.total, animatedTotal)
  } catch (error) {
    console.error('加载命名检查数据失败:', error)
  }
}

const formatTime = (time) => new Date(time).toLocaleString('zh-CN')

const exportData = () => {
  const csv = data.value.data.map(row =>
    [row.vm_name, row.ip, row.current_note, row.issues.join('|'), formatTime(row.check_time)].join(',')
  )
  const blob = new Blob(['虚拟机名称,IP地址,当前备注,问题项,检查时间\n' + csv.join('\n')], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `naming-check-${new Date().toISOString().split('T')[0]}.csv`
  a.click()
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.naming-page {
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

/* Rules Section */
.rules-section {
  margin-bottom: 24px;
}

.rules-card {
  padding: 24px;
}

.rules-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.rules-icon {
  width: 32px;
  height: 32px;
  padding: 8px;
  background: rgba(96, 165, 250, 0.2);
  border-radius: 8px;
  color: #60a5fa;
}

.rules-icon svg {
  width: 16px;
  height: 16px;
}

.rules-title {
  font-size: 18px;
  font-weight: 600;
  color: #ffffff;
  margin: 0;
}

.rules-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.rule-box {
  padding: 16px;
  background: rgba(255, 255, 255, 0.04);
  border-radius: 12px;
}

.rule-box.wide {
  grid-column: span 2;
}

.rule-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.5);
  margin-bottom: 8px;
}

.label-icon {
  width: 16px;
  height: 16px;
}

.rule-content {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.8);
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
  background: rgba(251, 191, 36, 0.2);
  color: #fbbf24;
  display: flex;
  align-items: center;
  justify-content: center;
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

.ip-cell {
  width: 150px;
}

.ip-badge {
  padding: 4px 10px;
  background: rgba(52, 211, 153, 0.15);
  border-radius: 4px;
  color: #34d399;
  font-size: 13px;
}

.note-cell {
  max-width: 300px;
}

.note-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

.note-icon {
  width: 16px;
  height: 16px;
  color: rgba(255, 255, 255, 0.3);
}

.note-text {
  color: rgba(255, 255, 255, 0.7);
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.issues-cell {
  max-width: 200px;
}

.issues-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.issue-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background: rgba(251, 191, 36, 0.2);
  border-radius: 6px;
  color: #fbbf24;
  font-size: 12px;
}

.issue-icon {
  width: 12px;
  height: 12px;
}

.time-cell {
  color: rgba(255, 255, 255, 0.5);
  font-size: 13px;
  width: 180px;
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

  .rules-grid {
    grid-template-columns: 1fr;
  }

  .rule-box.wide {
    grid-column: span 1;
  }
}
</style>