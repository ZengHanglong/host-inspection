<template>
  <div class="settings-page">
    <div class="page-header">
      <div class="header-content">
        <div class="title-group">
          <svg class="header-icon" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="2"/>
            <path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
          <h1 class="page-title">系统配置</h1>
        </div>
        <p class="page-subtitle">配置巡检阈值、平台连接和采集策略</p>
      </div>
      <div class="header-actions">
        <button class="glass-btn refresh-btn" @click="refreshAll">
          <svg viewBox="0 0 24 24" fill="none" class="btn-icon">
            <path d="M21 12a9 9 0 11-6.219-8.56" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            <path d="M21 3v6h-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span>刷新配置</span>
        </button>
      </div>
    </div>

    <div class="glass-tabs">
      <button class="tab-btn" :class="{ active: activeTab === 'thresholds' }" @click="activeTab = 'thresholds'">
        <svg viewBox="0 0 24 24" fill="none">
          <path d="M12 2L2 7l10 5 10-5-10-5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M2 17l10 5 10-5M2 12l10 5 10-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span>阈值配置</span>
      </button>
      <button class="tab-btn" :class="{ active: activeTab === 'platforms' }" @click="activeTab = 'platforms'">
        <svg viewBox="0 0 24 24" fill="none">
          <rect x="2" y="3" width="20" height="14" rx="2" stroke="currentColor" stroke-width="2"/>
          <path d="M8 21h8M12 17v4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        <span>平台配置</span>
      </button>
      <button class="tab-btn" :class="{ active: activeTab === 'collection' }" @click="activeTab = 'collection'">
        <svg viewBox="0 0 24 24" fill="none">
          <path d="M12 6v6l4 2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
        </svg>
        <span>采集设置</span>
      </button>
      <button class="tab-btn" :class="{ active: activeTab === 'info' }" @click="activeTab = 'info'">
        <svg viewBox="0 0 24 24" fill="none">
          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
          <path d="M12 16v-4M12 8h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        <span>系统信息</span>
      </button>
    </div>

    <div v-show="activeTab === 'thresholds'" class="tab-content">
      <div class="threshold-grid">
        <div v-for="threshold in thresholds" :key="threshold.resource_type" class="threshold-card">
          <div class="card-header">
            <div class="resource-icon" :class="getResourceClass(threshold.resource_type)">
              <svg v-if="threshold.resource_type === 'cpu'" viewBox="0 0 24 24" fill="none">
                <rect x="4" y="4" width="16" height="16" rx="2" stroke="currentColor" stroke-width="2"/>
                <rect x="9" y="9" width="6" height="6" stroke="currentColor" stroke-width="2"/>
                <path d="M9 1v3M15 1v3M9 20v3M15 20v3M20 9h3M20 15h3M1 9h3M1 15h3" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
              <svg v-else-if="threshold.resource_type === 'memory'" viewBox="0 0 24 24" fill="none">
                <path d="M4 4h16v16H4z" stroke="currentColor" stroke-width="2"/>
                <path d="M4 8h16M4 12h16M4 16h16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
              <svg v-else-if="threshold.resource_type === 'storage'" viewBox="0 0 24 24" fill="none">
                <ellipse cx="12" cy="5" rx="9" ry="3" stroke="currentColor" stroke-width="2"/>
                <path d="M21 5v14c0 1.66-4 3-9 3s-9-1.34-9-3V5" stroke="currentColor" stroke-width="2"/>
                <path d="M3 12c0 1.66 4 3 9 3s9-1.34 9-3" stroke="currentColor" stroke-width="2"/>
              </svg>
              <svg v-else viewBox="0 0 24 24" fill="none">
                <rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" stroke-width="2"/>
                <circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="2"/>
                <path d="M12 8v-3M12 19v-3" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </div>
            <div class="resource-info">
              <h3 class="resource-name">{{ getResourceTypeName(threshold.resource_type) }}</h3>
              <span class="status-badge" :class="{ active: threshold.is_active }">{{ threshold.is_active ? '已启用' : '已禁用' }}</span>
            </div>
          </div>

          <div class="threshold-controls">
            <div class="threshold-row">
              <label class="threshold-label"><span class="label-dot warning"></span>警告阈值</label>
              <div class="threshold-input-group">
                <input type="number" class="threshold-input warning" :value="threshold.warning_threshold" @input="updateThresholdValue(threshold, 'warning', $event.target.value)" min="0" max="100" />
                <span class="threshold-unit">{{ threshold.resource_type === 'snapshot_days' ? '天' : '%' }}</span>
              </div>
            </div>
            <div class="threshold-row">
              <label class="threshold-label"><span class="label-dot critical"></span>严重阈值</label>
              <div class="threshold-input-group">
                <input type="number" class="threshold-input critical" :value="threshold.critical_threshold" @input="updateThresholdValue(threshold, 'critical', $event.target.value)" min="0" max="100" />
                <span class="threshold-unit">{{ threshold.resource_type === 'snapshot_days' ? '天' : '%' }}</span>
              </div>
            </div>
          </div>

          <div class="threshold-bar">
            <div class="bar-track">
              <div class="bar-segment warning" :style="{ width: threshold.warning_threshold + '%' }"></div>
              <div class="bar-segment critical" :style="{ width: threshold.critical_threshold + '%' }"></div>
            </div>
            <div class="bar-labels">
              <span>0</span>
              <span>{{ threshold.warning_threshold }}{{ threshold.resource_type === 'snapshot_days' ? '天' : '%' }}</span>
              <span>{{ threshold.critical_threshold }}{{ threshold.resource_type === 'snapshot_days' ? '天' : '%' }}</span>
              <span>100{{ threshold.resource_type === 'snapshot_days' ? '天' : '%' }}</span>
            </div>
          </div>

          <div class="card-footer">
            <div class="toggle-wrapper">
              <label class="glass-toggle">
                <input type="checkbox" :checked="threshold.is_active" @change="toggleThreshold(threshold)" />
                <span class="toggle-slider"></span>
              </label>
              <span class="toggle-label">启用监控</span>
            </div>
            <button class="save-btn" @click="saveThreshold(threshold)">
              <svg viewBox="0 0 24 24" fill="none"><path d="M5 12l5 5L20 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </button>
          </div>
        </div>
      </div>
    </div>

    <div v-show="activeTab === 'platforms'" class="tab-content">
      <div class="platform-grid">
        <div v-for="platform in platforms" :key="platform.id" class="platform-card">
          <div class="card-header">
            <div class="platform-logo" :class="platform.platform">
              <svg v-if="platform.platform === 'vmware'" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                <path d="M8 12l4 4 4-4M12 8v8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <svg v-else viewBox="0 0 24 24" fill="none">
                <rect x="2" y="3" width="20" height="14" rx="2" stroke="currentColor" stroke-width="2"/>
                <path d="M8 21h8M12 17v4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </div>
            <div class="platform-info">
              <h3 class="platform-name">{{ getPlatformName(platform.platform) }}</h3>
              <div class="platform-status">
                <span class="status-dot" :class="{ active: platform.is_active }"></span>
                <span class="status-text">{{ platform.is_active ? '已启用' : '已停用' }}</span>
              </div>
            </div>
          </div>

          <div class="platform-form">
            <div class="form-group">
              <label class="form-label">API地址</label>
              <input type="text" class="form-input" v-model="platform.api_url" placeholder="vcenter.example.com" @change="updatePlatform(platform)" />
            </div>
            <div class="form-group">
              <label class="form-label">端口</label>
              <input type="number" class="form-input" v-model="platform.api_port" placeholder="443" @change="updatePlatform(platform)" />
            </div>
            <div class="form-group">
              <label class="form-label">用户名</label>
              <input type="text" class="form-input" v-model="platform.api_username" placeholder="输入API用户名" @change="updatePlatform(platform)" />
            </div>
            <div class="form-group">
              <label class="form-label">密码</label>
              <input type="password" class="form-input" v-model="platform.api_password" placeholder="留空表示不修改密码" @change="updatePlatform(platform)" />
            </div>
          </div>

          <div class="platform-toggles">
            <div class="toggle-row">
              <span class="toggle-label-text">启用平台</span>
              <label class="glass-toggle">
                <input type="checkbox" :checked="platform.is_active" @change="toggleActive(platform)" />
                <span class="toggle-slider"></span>
              </label>
            </div>
          </div>

          <div class="card-footer">
            <div class="sync-info">
              <svg viewBox="0 0 24 24" fill="none" class="sync-icon">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                <path d="M12 6v6l4 2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
              <span class="sync-text">{{ platform.last_test_at ? formatTime(platform.last_test_at) : '未测试' }}</span>
            </div>
            <button class="test-btn" @click="testConnection(platform)">
              <svg viewBox="0 0 24 24" fill="none">
                <path d="M22 11.08V12a10 10 0 11-5.93-9.14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                <path d="M22 4L12 14.01l-3-3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <span>测试连接</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <div v-show="activeTab === 'collection'" class="tab-content">
      <div class="info-grid collection-grid">
        <div class="info-card system-card">
          <div class="card-header">
            <h3 class="card-title">采集控制</h3>
          </div>
          <div class="info-list">
            <div class="info-row">
              <span class="info-label">自动采集</span>
              <label class="glass-toggle">
                <input type="checkbox" v-model="collectionConfig.auto_enabled" @change="saveCollectionConfig" />
                <span class="toggle-slider"></span>
              </label>
            </div>
            <div class="info-row">
              <span class="info-label">采集间隔</span>
              <div class="threshold-input-group">
                <input type="number" class="threshold-input" v-model="collectionConfig.interval_minutes" min="1" max="1440" @change="saveCollectionConfig" />
                <span class="threshold-unit">分钟</span>
              </div>
            </div>
            <div class="info-row collection-action-row">
              <button class="glass-btn" :disabled="collectionStatus.is_running" @click="runCollectionNow">
                <span>{{ collectionStatus.is_running ? '采集中...' : '立即采集' }}</span>
              </button>
            </div>
          </div>
        </div>

        <div class="info-card guide-card">
          <div class="card-header">
            <h3 class="card-title">采集状态</h3>
          </div>
          <div class="collection-status-panel">
            <div class="status-progress-row">
              <div class="progress-track">
                <div class="progress-fill" :style="{ width: `${collectionStatus.progress_percent || 0}%` }"></div>
              </div>
              <span class="progress-value">{{ collectionStatus.progress_percent || 0 }}%</span>
            </div>
            <div class="info-row">
              <span class="info-label">当前状态</span>
              <span class="info-value">{{ collectionStatus.progress_message || '等待下一次采集' }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">触发方式</span>
              <span class="info-value">{{ triggerSourceText }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">最近成功采集</span>
              <span class="info-value">{{ formatMaybeTime(collectionStatus.last_success_at) }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">当前数据截止</span>
              <span class="info-value">{{ formatMaybeTime(collectionStatus.last_data_cutoff_at) }}</span>
            </div>
            <div class="info-row" v-if="collectionStatus.last_error">
              <span class="info-label">最近错误</span>
              <span class="info-value error-text">{{ collectionStatus.last_error }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-show="activeTab === 'info'" class="tab-content">
      <div class="info-grid">
        <div class="info-card system-card">
          <div class="card-header">
            <h3 class="card-title">系统信息</h3>
          </div>
          <div class="info-list">
            <div class="info-row"><span class="info-label">系统名称</span><span class="info-value">主机巡检系统</span></div>
            <div class="info-row"><span class="info-label">版本</span><span class="info-value version">v1.0.0</span></div>
            <div class="info-row"><span class="info-label">数据库</span><span class="info-value">SQLite</span></div>
            <div class="info-row"><span class="info-label">巡检间隔</span><span class="info-value">{{ collectionConfig.interval_minutes }}分钟</span></div>
            <div class="info-row"><span class="info-label">API文档</span><a class="api-link" href="/docs" target="_blank">Swagger UI</a></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import axios from 'axios'

const activeTab = ref('thresholds')
const thresholds = ref([])
const platforms = ref([])
const collectionConfig = reactive({ interval_minutes: 5, auto_enabled: true })
const collectionStatus = reactive({
  is_running: false,
  trigger_source: null,
  progress_percent: 0,
  progress_message: '等待下一次采集',
  last_success_at: null,
  last_data_cutoff_at: null,
  last_error: null,
})

const resourceTypeNames = {
  cpu: 'CPU使用率',
  memory: '内存使用率',
  storage: '存储使用率',
  snapshot_days: '快照天数',
  table_space: '表空间使用率',
}

const platformNames = {
  vmware: 'VMware vCenter',
  smartx: 'SmartX 超融合',
  huawei_cd: '华为云桌面',
  sangfor_cd: '深信服云桌面',
  oracle: 'Oracle',
  mysql: 'MySQL',
  sqlserver: 'SQL Server',
  gbase: 'Gbase',
  tdsql: 'TDSQL',
  hwstorage: '华为存储',
  xsky: 'XSKY 存储',
  huarui: '华瑞存储',
  smartxzbs: 'SmartX ZBS',
  veeam: 'Veeam 备份',
  dingjia: '鼎甲备份',
  zerto: 'Zerto 容灾',
  netbackup: 'Veritas NetBackup',
  rizhiyi: '日志易',
}

const triggerSourceText = computed(() => {
  if (collectionStatus.trigger_source === 'manual') return '手动触发'
  if (collectionStatus.trigger_source === 'scheduled') return '定时触发'
  return '暂无'
})

const getResourceClass = (type) => ({
  cpu: 'resource-cpu',
  memory: 'resource-memory',
  storage: 'resource-storage',
  snapshot_days: 'resource-snapshot',
}[type] || 'resource-default')

const getResourceTypeName = (type) => resourceTypeNames[type] || type
const getPlatformName = (platform) => platformNames[platform] || platform

const formatTime = (time) => new Date(time).toLocaleString('zh-CN')
const formatMaybeTime = (time) => time ? formatTime(time) : '暂无'

const loadThresholds = async () => {
  const response = await axios.get('/api/config/thresholds')
  thresholds.value = response.data.thresholds || []
}

const loadPlatforms = async () => {
  const response = await axios.get('/api/config/platforms')
  platforms.value = (response.data.platforms || []).map(platform => ({ ...platform, api_password: '' }))
}

const applyCollectionPayload = (payload) => {
  collectionConfig.interval_minutes = payload.interval_minutes || 5
  collectionConfig.auto_enabled = payload.auto_enabled ?? true
  Object.assign(collectionStatus, payload.status || {})
}

const loadCollectionConfig = async () => {
  const response = await axios.get('/api/config/collection')
  applyCollectionPayload(response.data)
}

const loadCollectionStatus = async () => {
  const response = await axios.get('/api/inspection/status')
  Object.assign(collectionStatus, response.data || {})
}

const refreshAll = async () => {
  await Promise.all([loadThresholds(), loadPlatforms(), loadCollectionConfig()])
}

const updateThresholdValue = (threshold, type, value) => {
  if (type === 'warning') threshold.warning_threshold = parseInt(value, 10) || 0
  else threshold.critical_threshold = parseInt(value, 10) || 0
}

const toggleThreshold = (threshold) => {
  threshold.is_active = !threshold.is_active
  saveThreshold(threshold)
}

const saveThreshold = async (threshold) => {
  await axios.put(`/api/config/thresholds/${threshold.resource_type}`, {
    warning_threshold: threshold.warning_threshold,
    critical_threshold: threshold.critical_threshold,
    is_active: threshold.is_active,
  })
}

const updatePlatform = async (platform) => {
  await axios.put(`/api/config/platforms/${platform.id}`, {
    api_url: platform.api_url,
    api_port: Number(platform.api_port) || null,
    api_username: platform.api_username,
    api_password: platform.api_password || null,
    is_active: platform.is_active,
  })
  platform.api_password = ''
}

const toggleActive = (platform) => {
  platform.is_active = !platform.is_active
  updatePlatform(platform)
}

const testConnection = async (platform) => {
  const response = await axios.post(`/api/config/platforms/${platform.id}/test`)
  window.alert(response.data.message || (response.data.success ? '连接测试成功' : '连接测试失败'))
  await loadPlatforms()
}

const saveCollectionConfig = async () => {
  const response = await axios.put('/api/config/collection', {
    interval_minutes: Number(collectionConfig.interval_minutes) || 5,
    auto_enabled: !!collectionConfig.auto_enabled,
  })
  collectionConfig.interval_minutes = response.data.interval_minutes
  collectionConfig.auto_enabled = response.data.auto_enabled
  await loadCollectionStatus()
}

const runCollectionNow = async () => {
  await axios.post('/api/inspection/run')
  await loadCollectionStatus()
}

let refreshTimer = null

onMounted(async () => {
  await refreshAll()
  refreshTimer = setInterval(() => {
    loadCollectionStatus()
  }, 3000)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>

<style scoped>
.settings-page {
  padding: 24px;
  min-height: calc(100vh - 80px);
  background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 50%, #0d0d1f 100%);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
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
  color: #60a5fa;
}

.page-title {
  font-size: 28px;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: 0.5px;
}

.page-subtitle {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
}

.header-actions {
  display: flex;
  gap: 12px;
}

.glass-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 8px;
  color: #ffffff;
  cursor: pointer;
  transition: all 0.3s ease;
}

.glass-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.25);
  transform: translateY(-2px);
}

.glass-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-icon {
  width: 18px;
  height: 18px;
}

.glass-tabs {
  display: flex;
  gap: 4px;
  padding: 8px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  margin-bottom: 24px;
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: transparent;
  border: none;
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.6);
  cursor: pointer;
  transition: all 0.3s ease;
}

.tab-btn svg {
  width: 20px;
  height: 20px;
}

.tab-btn.active {
  color: #60a5fa;
  background: rgba(96, 165, 250, 0.15);
}

.tab-content {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.threshold-grid,
.platform-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.threshold-card,
.platform-card,
.info-card {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 24px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.resource-icon,
.platform-logo {
  width: 48px;
  height: 48px;
  padding: 12px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.resource-icon svg,
.platform-logo svg {
  width: 24px;
  height: 24px;
}

.resource-cpu { background: rgba(96, 165, 250, 0.2); color: #60a5fa; }
.resource-memory { background: rgba(251, 191, 36, 0.2); color: #fbbf24; }
.resource-storage { background: rgba(52, 211, 153, 0.2); color: #34d399; }
.resource-snapshot { background: rgba(167, 139, 250, 0.2); color: #a78bfa; }

.platform-logo.vmware { background: rgba(96, 165, 250, 0.2); color: #60a5fa; }
.platform-logo.smartx { background: rgba(52, 211, 153, 0.2); color: #34d399; }
.platform-logo { background: rgba(255, 255, 255, 0.08); color: #cbd5e1; }

.resource-name,
.platform-name,
.card-title {
  font-size: 18px;
  font-weight: 600;
  color: #ffffff;
  margin: 0;
}

.status-badge,
.status-text,
.toggle-label,
.toggle-label-text,
.info-label,
.threshold-unit,
.sync-text {
  color: rgba(255, 255, 255, 0.65);
}

.status-badge {
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.1);
}

.status-badge.active {
  background: rgba(52, 211, 153, 0.2);
  color: #34d399;
}

.threshold-controls,
.info-list,
.collection-status-panel,
.platform-form,
.platform-toggles {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.threshold-row,
.info-row,
.toggle-row,
.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.collection-action-row {
  justify-content: flex-start;
}

.threshold-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
}

.label-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.label-dot.warning { background: #fbbf24; }
.label-dot.critical { background: #f87171; }

.threshold-input-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.threshold-input,
.form-input {
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  color: #ffffff;
}

.threshold-input {
  width: 88px;
  text-align: center;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-label,
.info-value,
.resource-info,
.platform-info {
  color: #ffffff;
}

.platform-info,
.resource-info {
  flex: 1;
}

.platform-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgba(255,255,255,0.4);
}

.status-dot.active {
  background: #34d399;
}

.glass-toggle {
  position: relative;
  width: 44px;
  height: 24px;
  cursor: pointer;
}

.glass-toggle input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider {
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.12);
  border-radius: 12px;
  transition: all 0.3s ease;
}

.toggle-slider::before {
  position: absolute;
  content: '';
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background: rgba(255, 255, 255, 0.75);
  border-radius: 50%;
  transition: all 0.3s ease;
}

.glass-toggle input:checked + .toggle-slider {
  background: rgba(52, 211, 153, 0.3);
}

.glass-toggle input:checked + .toggle-slider::before {
  transform: translateX(20px);
  background: #34d399;
}

.threshold-bar {
  margin-bottom: 20px;
}

.bar-track,
.progress-track {
  height: 8px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  position: relative;
  overflow: hidden;
}

.bar-segment,
.progress-fill {
  position: absolute;
  left: 0;
  height: 100%;
  border-radius: 4px;
}

.bar-segment.warning { background: linear-gradient(90deg, #34d399 0%, #fbbf24 100%); opacity: 0.6; }
.bar-segment.critical { background: linear-gradient(90deg, #fbbf24 0%, #f87171 100%); opacity: 0.8; }
.progress-fill { background: linear-gradient(90deg, #60a5fa 0%, #34d399 100%); }

.bar-labels,
.progress-value {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.5);
}

.bar-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 4px;
}

.save-btn,
.test-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 14px;
  background: rgba(52, 211, 153, 0.2);
  border: 1px solid rgba(52, 211, 153, 0.3);
  border-radius: 8px;
  color: #34d399;
  cursor: pointer;
}

.save-btn svg,
.test-btn svg,
.sync-icon {
  width: 18px;
  height: 18px;
}

.info-grid,
.collection-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 20px;
}

.status-progress-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.progress-track {
  flex: 1;
}

.error-text {
  color: #f87171;
}

.api-link {
  color: #60a5fa;
  text-decoration: none;
}
</style>
