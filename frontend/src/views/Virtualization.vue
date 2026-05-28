<template>
  <div class="virtualization-page">
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">虚拟化巡检</h1>
        <p class="page-desc">VMware vCenter · SmartX 超融合平台</p>
      </div>
      <div class="header-actions">
        <button class="action-btn" @click="refreshData">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M23 4v6h-6"/><path d="M1 20v-6h6"/>
            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
          </svg>
          <span>刷新</span>
        </button>
        <button class="action-btn primary" @click="runInspection" :disabled="inspecting">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="5 3 19 12 5 21 5 3"/>
          </svg>
          <span>{{ inspecting ? '巡检中...' : '立即巡检' }}</span>
        </button>
      </div>
    </div>

    <!-- 采集状态 -->
    <div class="status-banner" :class="collectionStatus.is_running ? 'running' : 'idle'">
      <div class="status-icon">
        <svg v-if="collectionStatus.is_running" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
        </svg>
        <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/><path d="M9 12l2 2 4-4"/>
        </svg>
      </div>
      <div class="status-text">
        <span class="status-label">{{ collectionStatus.is_running ? '采集中 ' + (collectionStatus.progress_percent || 0) + '%' : collectionStatus.last_result_status === 'success' ? '上次采集成功' : '等待采集' }}</span>
        <span class="status-detail" v-if="collectionStatus.last_data_cutoff_at">数据截至 {{ formatTime(collectionStatus.last_data_cutoff_at) }}</span>
      </div>
    </div>

    <!-- 平台卡片 -->
    <div class="platform-section">
      <div class="section-header">
        <span class="section-title">虚拟化平台</span>
        <span class="section-count">{{ vmwareInstances.length + smartxInstances.length }} 个实例</span>
      </div>
      <div class="platform-grid">
        <!-- VMware 实例 -->
        <div class="platform-card" v-for="inst in vmwareInstances" :key="'vmware-' + inst.id" :class="{ connected: inst.is_connected }">
          <div class="card-header">
            <div class="platform-icon vmware">V</div>
            <div class="platform-status" :class="inst.is_connected ? 'connected' : inst.is_configured ? 'error' : 'pending'">
              <span class="status-dot"></span>
              <span class="status-text">{{ inst.is_connected ? '已连接' : inst.is_configured ? '连接失败' : '未配置' }}</span>
            </div>
          </div>
          <div class="card-body">
            <h3 class="platform-name">{{ inst.display_name }}</h3>
            <p class="platform-host">{{ inst.api_url || '未配置地址' }}</p>
            <span class="platform-env" :class="inst.environment">{{ envName(inst.environment) }}</span>
          </div>
          <div class="card-stats" v-if="inst.is_connected">
            <div class="stat-item">
              <span class="stat-value">{{ inst.statistics?.hosts || 0 }}</span>
              <span class="stat-label">主机</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ inst.statistics?.vms || 0 }}</span>
              <span class="stat-label">虚拟机</span>
            </div>
            <div class="stat-item">
              <span class="stat-value" :class="(inst.statistics?.warning || 0) + (inst.statistics?.critical || 0) > 0 ? 'danger' : ''">{{ (inst.statistics?.warning || 0) + (inst.statistics?.critical || 0) }}</span>
              <span class="stat-label">告警</span>
            </div>
          </div>
          <div class="card-actions">
            <button class="card-btn" @click="testConnection(inst)">测试连接</button>
            <router-link to="/credentials" class="card-btn">配置</router-link>
          </div>
        </div>

        <!-- SmartX 实例 -->
        <div class="platform-card" v-for="inst in smartxInstances" :key="'smartx-' + inst.id" :class="{ connected: inst.is_connected }">
          <div class="card-header">
            <div class="platform-icon smartx">S</div>
            <div class="platform-status" :class="inst.is_connected ? 'connected' : inst.is_configured ? 'error' : 'pending'">
              <span class="status-dot"></span>
              <span class="status-text">{{ inst.is_connected ? '已连接' : inst.is_configured ? '连接失败' : '未配置' }}</span>
            </div>
          </div>
          <div class="card-body">
            <h3 class="platform-name">{{ inst.display_name }}</h3>
            <p class="platform-host">{{ inst.api_url || '未配置地址' }}</p>
            <span class="platform-env" :class="inst.environment">{{ envName(inst.environment) }}</span>
          </div>
          <div class="card-actions">
            <button class="card-btn" @click="testConnection(inst)">测试连接</button>
            <router-link to="/credentials" class="card-btn">配置</router-link>
          </div>
        </div>

        <!-- 添加实例按钮 -->
        <router-link to="/credentials" class="platform-card add-card">
          <div class="add-icon">+</div>
          <span class="add-text">添加平台实例</span>
        </router-link>
      </div>
    </div>

    <!-- 巡检功能菜单 -->
    <div class="menu-section">
      <div class="section-header">
        <span class="section-title">巡检功能</span>
      </div>
      <div class="menu-grid">
        <router-link to="/" class="menu-card">
          <div class="menu-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
              <rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>
            </svg>
          </div>
          <div class="menu-content">
            <h4 class="menu-title">资源概览</h4>
            <p class="menu-desc">主机资源使用率、集群健康状态</p>
          </div>
          <div class="menu-arrow"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg></div>
        </router-link>
        <router-link to="/inspection" class="menu-card">
          <div class="menu-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
            </svg>
          </div>
          <div class="menu-content">
            <h4 class="menu-title">每日巡检</h4>
            <p class="menu-desc">CPU、内存、存储使用率检查</p>
          </div>
          <div class="menu-arrow"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg></div>
        </router-link>
        <router-link to="/periodic/snapshot" class="menu-card">
          <div class="menu-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/>
            </svg>
          </div>
          <div class="menu-content">
            <h4 class="menu-title">过期快照</h4>
            <p class="menu-desc">检查超过保留期的快照</p>
          </div>
          <div class="menu-arrow"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg></div>
        </router-link>
        <router-link to="/periodic/large" class="menu-card">
          <div class="menu-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/><path d="M12 2a10 10 0 0 1 10 10"/>
            </svg>
          </div>
          <div class="menu-content">
            <h4 class="menu-title">大容量虚拟机</h4>
            <p class="menu-desc">容量超过 1TB 的虚拟机排查</p>
          </div>
          <div class="menu-arrow"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg></div>
        </router-link>
        <router-link to="/periodic/naming" class="menu-card">
          <div class="menu-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>
          </div>
          <div class="menu-content">
            <h4 class="menu-title">命名规范</h4>
            <p class="menu-desc">VM 命名与备注规范检查</p>
          </div>
          <div class="menu-arrow"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg></div>
        </router-link>
        <router-link to="/periodic/idle" class="menu-card">
          <div class="menu-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>
            </svg>
          </div>
          <div class="menu-content">
            <h4 class="menu-title">闲置资产</h4>
            <p class="menu-desc">长期关机或临时用途虚拟机</p>
          </div>
          <div class="menu-arrow"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg></div>
        </router-link>
        <router-link to="/ledger/vm" class="menu-card">
          <div class="menu-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/>
            </svg>
          </div>
          <div class="menu-content">
            <h4 class="menu-title">虚拟机台账</h4>
            <p class="menu-desc">虚拟机资产清单管理</p>
          </div>
          <div class="menu-arrow"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg></div>
        </router-link>
        <router-link to="/ledger/physical" class="menu-card">
          <div class="menu-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/>
            </svg>
          </div>
          <div class="menu-content">
            <h4 class="menu-title">物理主机台账</h4>
            <p class="menu-desc">ESXi 物理主机资产清单</p>
          </div>
          <div class="menu-arrow"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg></div>
        </router-link>
        <router-link to="/reports" class="menu-card">
          <div class="menu-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
            </svg>
          </div>
          <div class="menu-content">
            <h4 class="menu-title">巡检报告</h4>
            <p class="menu-desc">生成和下载巡检报告</p>
          </div>
          <div class="menu-arrow"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg></div>
        </router-link>
      </div>
    </div>

    <!-- 告警列表 -->
    <div class="alert-section">
      <div class="section-header">
        <span class="section-title">最新告警</span>
        <router-link to="/alerts" class="view-all">查看全部</router-link>
      </div>
      <div class="empty-state" v-if="recentAlerts.length === 0">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/><path d="M9 12l2 2 4-4"/>
        </svg>
        <span>当前没有告警</span>
      </div>
      <div class="alert-list" v-else>
        <div class="alert-item" v-for="(alert, idx) in recentAlerts" :key="idx" :class="alert.alert_level">
          <div class="alert-level">
            <span class="level-icon">!</span>
          </div>
          <div class="alert-content">
            <span class="alert-message">{{ alert.message }}</span>
            <span class="alert-meta">{{ alert.platform_name }} · {{ formatTime(alert.created_at) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'

const inspecting = ref(false)
const vmwareInstances = ref([])
const smartxInstances = ref([])
const recentAlerts = ref([])
const collectionStatus = ref({ is_running: false, progress_percent: 0, last_result_status: 'idle', last_data_cutoff_at: null })

const envName = (code) => ({ dev: '测试', pre: '准生产', ser: '生产' }[code] || code)
const formatTime = (t) => t ? new Date(t).toLocaleString('zh-CN') : ''

const loadData = async () => {
  try {
    const res = await axios.get('/api/credentials/list')
    const instances = res.data.credentials || []
    vmwareInstances.value = instances.filter(i => i.platform === 'vmware')
    smartxInstances.value = instances.filter(i => i.platform === 'smartx')
  } catch (e) { console.error('Load credentials failed:', e) }

  try {
    const statusRes = await axios.get('/api/inspection/status')
    Object.assign(collectionStatus.value, statusRes.data || {})
  } catch (e) { console.error('Load status failed:', e) }

  try {
    const dashRes = await axios.get('/api/dashboard')
    recentAlerts.value = (dashRes.data.alerts || []).slice(0, 5)
  } catch (e) { console.error('Load dashboard failed:', e) }
}

const refreshData = () => loadData()

const runInspection = async () => {
  inspecting.value = true
  try {
    const res = await axios.post('/api/inspection/run')
    if (res.data?.collection_status) {
      Object.assign(collectionStatus.value, res.data.collection_status)
    }
  } catch (e) { console.error(e) }
  finally { setTimeout(() => inspecting.value = false, 3000) }
}

const testConnection = async (inst) => {
  try {
    const res = await axios.post(`/api/config/platforms/${inst.id}/test`)
    alert(res.data.success ? `${inst.display_name}: ${res.data.message}` : `${inst.display_name}: ${res.data.message}`)
    loadData()
  } catch (e) { alert('测试失败: ' + (e.response?.data?.detail || e.message)) }
}

let refreshTimer = null
onMounted(() => { loadData(); refreshTimer = setInterval(loadData, 30000) })
onUnmounted(() => { if (refreshTimer) clearInterval(refreshTimer) })
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Rubik:wght@400;500;600;700&display=swap');

.virtualization-page { padding: 24px; max-width: 1400px; margin: 0 auto; font-family: 'Rubik', sans-serif; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; }
.header-left { display: flex; flex-direction: column; gap: 4px; }
.page-title { font-size: 28px; font-weight: 700; color: #fff; margin: 0; }
.page-desc { font-size: 14px; color: rgba(255,255,255,0.5); margin: 0; }
.header-actions { display: flex; gap: 12px; }
.action-btn { display: flex; align-items: center; gap: 8px; padding: 10px 18px; background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.12); border-radius: 10px; color: #fff; font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.25s; }
.action-btn:hover { background: rgba(255,255,255,0.12); }
.action-btn.primary { background: #6a5fc1; border-color: #6a5fc1; }
.action-btn.primary:hover { background: #7a6fd1; }
.action-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.action-btn svg { width: 16px; height: 16px; }

.status-banner { display: flex; align-items: center; gap: 12px; padding: 14px 20px; border-radius: 12px; margin-bottom: 24px; }
.status-banner.idle { background: rgba(194,239,78,0.08); border: 1px solid rgba(194,239,78,0.2); }
.status-banner.running { background: rgba(106,95,193,0.1); border: 1px solid rgba(106,95,193,0.3); }
.status-icon { width: 32px; height: 32px; color: #c2ef4e; }
.status-banner.running .status-icon { color: #6a5fc1; animation: spin 2s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.status-icon svg { width: 100%; height: 100%; }
.status-text { display: flex; flex-direction: column; gap: 2px; }
.status-label { font-size: 14px; font-weight: 600; color: #fff; }
.status-detail { font-size: 12px; color: rgba(255,255,255,0.5); }

.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.section-title { font-size: 14px; font-weight: 600; color: rgba(255,255,255,0.6); text-transform: uppercase; letter-spacing: 0.5px; }
.section-count { font-size: 13px; color: rgba(255,255,255,0.4); }
.view-all { font-size: 13px; color: #c2ef4e; text-decoration: none; }
.view-all:hover { text-decoration: underline; }

.platform-section { margin-bottom: 32px; }
.platform-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; }
.platform-card { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 16px; padding: 20px; transition: all 0.25s; cursor: default; }
.platform-card:hover { background: rgba(255,255,255,0.06); }
.platform-card.connected { border-color: rgba(194,239,78,0.25); }
.card-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 14px; }
.platform-icon { width: 44px; height: 44px; border-radius: 12px; display: flex; align-items: center; justify-content: center; color: white; font-size: 18px; font-weight: 700; }
.platform-icon.vmware { background: linear-gradient(135deg, #667eea, #764ba2); }
.platform-icon.smartx { background: linear-gradient(135deg, #4facfe, #00f2fe); }
.platform-status { display: flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: 500; }
.platform-status.connected { background: rgba(194,239,78,0.15); color: #c2ef4e; }
.platform-status.error { background: rgba(248,113,113,0.15); color: #f87171; }
.platform-status.pending { background: rgba(251,191,36,0.15); color: #fbbf24; }
.status-dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
.card-body { margin-bottom: 14px; }
.platform-name { font-size: 16px; font-weight: 600; color: #fff; margin: 0 0 4px 0; }
.platform-host { font-size: 13px; color: rgba(255,255,255,0.5); margin: 0 0 8px 0; }
.platform-env { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; text-transform: uppercase; }
.platform-env.ser { background: rgba(194,239,78,0.15); color: #c2ef4e; }
.platform-env.pre { background: rgba(251,191,36,0.15); color: #fbbf24; }
.platform-env.dev { background: rgba(106,95,193,0.15); color: #6a5fc1; }
.card-stats { display: flex; gap: 24px; padding-top: 14px; border-top: 1px solid rgba(255,255,255,0.08); margin-bottom: 14px; }
.stat-item { display: flex; flex-direction: column; gap: 2px; }
.stat-value { font-size: 20px; font-weight: 700; color: #fff; }
.stat-value.danger { color: #f87171; }
.stat-label { font-size: 12px; color: rgba(255,255,255,0.4); }
.card-actions { display: flex; gap: 8px; }
.card-btn { padding: 6px 14px; background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.12); border-radius: 8px; color: rgba(255,255,255,0.7); font-size: 12px; font-weight: 500; cursor: pointer; text-decoration: none; transition: all 0.2s; }
.card-btn:hover { background: rgba(255,255,255,0.15); color: #fff; }
.add-card { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px; min-height: 200px; border-style: dashed; cursor: pointer; text-decoration: none; }
.add-card:hover { border-color: #6a5fc1; background: rgba(106,95,193,0.05); }
.add-icon { font-size: 32px; color: rgba(255,255,255,0.3); }
.add-text { font-size: 14px; color: rgba(255,255,255,0.4); }

.menu-section { margin-bottom: 32px; }
.menu-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; }
.menu-card { display: flex; align-items: center; gap: 16px; padding: 16px 20px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; cursor: pointer; transition: all 0.25s; text-decoration: none; }
.menu-card:hover { background: rgba(255,255,255,0.08); }
.menu-icon { width: 40px; height: 40px; background: rgba(106,95,193,0.15); border-radius: 10px; display: flex; align-items: center; justify-content: center; color: #c2ef4e; flex-shrink: 0; }
.menu-icon svg { width: 20px; height: 20px; }
.menu-content { flex: 1; }
.menu-title { font-size: 14px; font-weight: 600; color: #fff; margin: 0 0 2px 0; }
.menu-desc { font-size: 12px; color: rgba(255,255,255,0.5); margin: 0; }
.menu-arrow { width: 20px; height: 20px; color: rgba(255,255,255,0.3); }
.menu-arrow svg { width: 100%; height: 100%; }

.alert-section { margin-bottom: 32px; }
.empty-state { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 40px; color: rgba(255,255,255,0.4); }
.empty-state svg { width: 32px; height: 32px; color: #c2ef4e; }
.alert-list { display: flex; flex-direction: column; gap: 8px; }
.alert-item { display: flex; align-items: flex-start; gap: 14px; padding: 14px 18px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; border-left: 3px solid; }
.alert-item.critical { border-left-color: #f87171; }
.alert-item.warning { border-left-color: #fbbf24; }
.alert-level { width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: 700; flex-shrink: 0; }
.alert-item.critical .alert-level { color: #f87171; }
.alert-item.warning .alert-level { color: #fbbf24; }
.alert-content { flex: 1; display: flex; flex-direction: column; gap: 4px; }
.alert-message { font-size: 14px; color: #fff; }
.alert-meta { font-size: 12px; color: rgba(255,255,255,0.4); }
</style>
