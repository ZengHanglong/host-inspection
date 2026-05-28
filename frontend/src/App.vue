<template>
  <div class="app-container">
    <header class="app-header">
      <div class="header-left">
        <div class="logo-group" @click="showSpaceMenu = !showSpaceMenu">
          <div class="logo-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <ellipse cx="12" cy="5" rx="9" ry="3"/>
              <path d="M21 5v14c0 1.66-4 3-9 3s-9-1.34-9-3V5"/>
              <path d="M3 12c0 1.66 4 3 9 3s9-1.34 9-3"/>
            </svg>
          </div>
          <div class="logo-text">
            <span class="logo-title">{{ t('app.logo.title') }}</span>
            <span class="logo-subtitle">{{ t('app.logo.subtitle') }}</span>
          </div>
          <svg class="space-arrow" :class="{ rotated: showSpaceMenu }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </div>
        <Teleport to="body">
          <Transition name="fade">
            <div v-if="showSpaceMenu" class="space-overlay" @click="showSpaceMenu = false">
              <div class="space-dropdown" @click.stop>
                <div class="space-item" v-for="space in spaces" :key="space.id" :class="{ active: currentSpace === space.id }" @click="selectSpace(space.id)">
                  <div class="space-icon" :style="{ background: space.color }">{{ space.icon }}</div>
                  <div class="space-info">
                    <span class="space-name">{{ space.name }}</span>
                    <span class="space-desc">{{ space.desc }}</span>
                  </div>
                </div>
              </div>
            </div>
          </Transition>
        </Teleport>
      </div>
      <nav class="header-nav">
        <router-link to="/" class="nav-link" :class="{ active: activeMenu === '/' }"><span class="nav-label">{{ t('app.nav.dashboard') }}</span></router-link>
        <router-link to="/inspection" class="nav-link" :class="{ active: activeMenu === '/inspection' }"><span class="nav-label">{{ t('app.nav.inspection') }}</span></router-link>
        <router-link to="/alerts" class="nav-link" :class="{ active: activeMenu === '/alerts' }"><span class="nav-label">{{ t('app.nav.alerts') }}</span><span class="nav-badge" v-if="activeAlertCount > 0">{{ activeAlertCount }}</span></router-link>
        <router-link to="/reports" class="nav-link" :class="{ active: activeMenu === '/reports' }"><span class="nav-label">{{ t('app.nav.reports') }}</span></router-link>
      </nav>
      <div class="header-right">
        <div class="locale-switcher">
          <button type="button" class="locale-btn" :class="{ active: currentLocale === 'zh-CN' }" @click="changeLocale('zh-CN')">{{ t('app.locale.zh') }}</button>
          <span class="locale-divider">|</span>
          <button type="button" class="locale-btn" :class="{ active: currentLocale === 'en-US' }" @click="changeLocale('en-US')">{{ t('app.locale.en') }}</button>
        </div>
        <button class="btn-primary" @click="runInspection" :disabled="inspecting"><span class="btn-text">{{ inspecting ? t('app.actions.running') : t('app.actions.runInspection') }}</span></button>
        <div class="collection-summary" v-if="collectionSummaryText">{{ collectionSummaryText }}</div>
        <div class="status-indicator" :class="connectionStatus"><div class="status-dot"></div><span class="status-label">{{ connectionText }}</span></div>
      </div>
    </header>
    <div class="main-layout">
      <aside class="sidebar">
        <div class="sidebar-content">
          <div class="sidebar-section"><div class="section-title"><span class="section-label">{{ t('app.sections.periodicChecks') }}</span></div>
            <nav class="sidebar-nav">
              <router-link to="/periodic/snapshot" class="sidebar-link" :class="{ active: activeMenu.startsWith('/periodic/snapshot') }"><svg class="link-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg><span class="link-text">{{ t('app.links.snapshot') }}</span></router-link>
              <router-link to="/periodic/naming" class="sidebar-link" :class="{ active: activeMenu.startsWith('/periodic/naming') }"><svg class="link-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg><span class="link-text">{{ t('app.links.naming') }}</span></router-link>
              <router-link to="/periodic/idle" class="sidebar-link" :class="{ active: activeMenu.startsWith('/periodic/idle') }"><svg class="link-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg><span class="link-text">{{ t('app.links.idle') }}</span></router-link>
              <router-link to="/periodic/large" class="sidebar-link" :class="{ active: activeMenu.startsWith('/periodic/large') }"><svg class="link-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 2a10 10 0 0 1 10 10"/></svg><span class="link-text">{{ t('app.links.large') }}</span></router-link>
            </nav>
          </div>
          <div class="sidebar-section"><div class="section-title"><span class="section-label">{{ t('app.sections.ledgerManagement') }}</span></div>
            <nav class="sidebar-nav">
              <router-link to="/ledger/vm" class="sidebar-link" :class="{ active: activeMenu.startsWith('/ledger/vm') }"><svg class="link-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg><span class="link-text">{{ t('app.links.vmLedger') }}</span></router-link>
              <router-link to="/ledger/physical" class="sidebar-link" :class="{ active: activeMenu.startsWith('/ledger/physical') }"><svg class="link-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/></svg><span class="link-text">{{ t('app.links.physicalLedger') }}</span></router-link>
              <router-link to="/ledger/database" class="sidebar-link" :class="{ active: activeMenu.startsWith('/ledger/database') }"><svg class="link-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 5v14c0 1.66-4 3-9 3s-9-1.34-9-3V5"/></svg><span class="link-text">{{ t('app.links.databaseLedger') }}</span></router-link>
            </nav>
          </div>
          <div class="sidebar-section"><div class="section-title"><span class="section-label">{{ t('app.sections.settings') }}</span></div>
            <nav class="sidebar-nav">
              <router-link to="/credentials" class="sidebar-link" :class="{ active: activeMenu === '/credentials' }"><svg class="link-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L7.5 15.5"/></svg><span class="link-text">{{ t('app.links.credentials') }}</span><span class="link-badge" v-if="unconfiguredCount > 0">{{ unconfiguredCount }}</span></router-link>
              <router-link to="/esxi-logs" class="sidebar-link" :class="{ active: activeMenu === '/esxi-logs' }"><svg class="link-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg><span class="link-text">ESXi日志</span></router-link>
              <router-link to="/history" class="sidebar-link" :class="{ active: activeMenu === '/history' }"><svg class="link-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg><span class="link-text">{{ t('app.links.history') }}</span></router-link>
              <router-link to="/settings" class="sidebar-link" :class="{ active: activeMenu === '/settings' }"><svg class="link-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/><line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/></svg><span class="link-text">{{ t('app.links.thresholdConfig') }}</span></router-link>
            </nav>
          </div>
        </div>
        <div class="sidebar-footer"><div class="footer-stats"><span class="stats-label">{{ t('app.footer.configured') }}</span><span class="stats-value">{{ configuredCount }}/{{ totalCount }}</span></div></div>
      </aside>
      <main class="main-content">
        <router-view v-slot="{ Component }"><transition name="fade" mode="out-in"><component :is="Component" /></transition></router-view>
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import axios from 'axios'
import { getLocale, setLocale } from './i18n'

const router = useRouter()
const { t } = useI18n()
const activeMenu = computed(() => router.currentRoute.value.path)
const connectionStatus = ref('pending')
const configuredCount = ref(0)
const totalCount = ref(10)
const unconfiguredCount = ref(0)
const activeAlertCount = ref(0)
const inspecting = ref(false)
const currentLocale = ref(getLocale())
const collectionStatus = ref({ is_running: false, progress_percent: 0, progress_message: '', last_data_cutoff_at: null })

const showSpaceMenu = ref(false)
const currentSpace = ref('virtualization')
const spaces = [
  { id: 'virtualization', name: '虚拟化', desc: 'VMware、SmartX', icon: 'V', color: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' },
  { id: 'database', name: '数据库', desc: 'Oracle、MySQL、SQL Server', icon: 'D', color: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)' },
  { id: 'backup', name: '备份系统', desc: 'NBU、Veeam、鼎甲', icon: 'B', color: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)' },
  { id: 'storage', name: '存储系统', desc: '华为、XSKY、SmartX ZBS', icon: 'S', color: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)' },
]

const selectSpace = (spaceId) => { currentSpace.value = spaceId; showSpaceMenu.value = false }
const connectionText = computed(() => connectionStatus.value === 'connected' ? t('app.status.connected') : connectionStatus.value === 'partial' ? t('app.status.partial') : connectionStatus.value === 'error' ? t('app.status.failed') : t('app.status.notConfigured'))
const changeLocale = (locale) => { setLocale(locale); currentLocale.value = getLocale() }
const formatMaybeTime = (value) => value ? new Date(value).toLocaleString(currentLocale.value === 'en-US' ? 'en-US' : 'zh-CN') : ''
const collectionSummaryText = computed(() => collectionStatus.value?.is_running ? '采集中 ' + (collectionStatus.value.progress_percent || 0) + '%' : collectionStatus.value?.last_data_cutoff_at ? '数据截至 ' + formatMaybeTime(collectionStatus.value.last_data_cutoff_at) : '')
const loadOverview = async () => {
  try {
    const r = await axios.get('/api/overview')
    const d = r.data
    connectionStatus.value = d.connection_status || 'pending'
    totalCount.value = d.total_count || 0
    configuredCount.value = d.configured_count || 0
    unconfiguredCount.value = d.unconfigured_count || 0
    activeAlertCount.value = d.active_alert_count || 0
    collectionStatus.value = d.collection_status || collectionStatus.value
    inspecting.value = !!d.collection_status?.is_running
  } catch (e) { console.error(e) }
}
const runInspection = async () => {
  try {
    const r = await axios.post('/api/inspection/run')
    if (r.data?.collection_status) {
      collectionStatus.value = r.data.collection_status
      inspecting.value = !!r.data.collection_status.is_running
    } else { inspecting.value = true }
  } catch (e) { console.error(e) }
}
let refreshTimer = null
onMounted(() => { loadOverview(); refreshTimer = setInterval(loadOverview, 30000) })
onUnmounted(() => { if (refreshTimer) clearInterval(refreshTimer) })
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Rubik:wght@400;500;600;700&display=swap');
.app-container{min-height:100vh;background:#1f1633;font-family:'Rubik',sans-serif}
.app-header{position:sticky;top:0;z-index:100;height:64px;background:rgba(21,15,35,0.85);backdrop-filter:blur(18px);border-bottom:1px solid #362d59;display:flex;align-items:center;justify-content:space-between;padding:0 24px}
.header-left{display:flex;align-items:center}
.logo-group{display:flex;align-items:center;gap:12px;padding:6px 12px;background:rgba(255,255,255,0.06);border-radius:10px;cursor:pointer;transition:all .25s}
.logo-group:hover{background:rgba(255,255,255,0.1)}
.logo-icon{width:36px;height:36px;background:#362d59;border-radius:8px;display:flex;align-items:center;justify-content:center;color:#c2ef4e}
.logo-icon svg{width:20px;height:20px}
.logo-text{display:flex;flex-direction:column}
.logo-title{font-size:15px;font-weight:600;color:#fff;letter-spacing:.2px;text-transform:uppercase}
.logo-subtitle{font-size:12px;color:rgba(255,255,255,0.5)}
.space-arrow{width:16px;height:16px;color:rgba(255,255,255,0.5);transition:transform .25s}
.space-arrow.rotated{transform:rotate(180deg)}
.space-overlay{position:fixed;inset:0;z-index:9998}
.space-dropdown{width:280px;background:rgba(255,255,255,0.95);backdrop-filter:blur(20px);border-radius:12px;box-shadow:0 8px 32px rgba(0,0,0,0.2);padding:8px;z-index:9999;position:fixed;left:24px;top:72px}
.space-item{display:flex;align-items:center;gap:12px;padding:12px;border-radius:8px;cursor:pointer;transition:background .2s}
.space-item:hover{background:rgba(0,0,0,0.05)}
.space-item.active{background:rgba(106,95,193,0.1)}
.space-icon{width:40px;height:40px;border-radius:10px;display:flex;align-items:center;justify-content:center;color:#fff;font-size:16px;font-weight:700}
.space-info{display:flex;flex-direction:column;gap:2px}
.space-name{font-size:14px;font-weight:600;color:#1e293b}
.space-desc{font-size:12px;color:#64748b}
.header-nav{display:flex;align-items:center;gap:8px}
.nav-link{padding:8px 12px;border-radius:8px;color:#fff;font-size:15px;font-weight:500;text-decoration:none;transition:all .3s}
.nav-link:hover{color:#6a5fc1}
.nav-link.active{color:#6a5fc1;background:rgba(106,95,193,0.1)}
.nav-badge{padding:2px 6px;background:#c2ef4e;border-radius:4px;color:#1f1633;font-size:11px;font-weight:700}
.header-right{display:flex;align-items:center;gap:16px}
.locale-switcher{display:flex;align-items:center;gap:8px;padding:6px 10px;background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.1);border-radius:10px}
.locale-btn{background:transparent;border:none;color:rgba(255,255,255,0.5);font-size:13px;font-weight:600;cursor:pointer}
.locale-btn.active{color:#fff}
.locale-divider{color:rgba(255,255,255,0.35);font-size:12px}
.btn-primary{padding:8px 16px;background:#79628c;border:1px solid #584674;border-radius:13px;color:#fff;font-size:14px;font-weight:700;cursor:pointer;transition:all .3s}
.btn-primary:hover:not(:disabled){transform:translateY(-1px)}
.btn-primary:disabled{opacity:.6;cursor:not-allowed}
.collection-summary{max-width:240px;padding:6px 10px;border-radius:10px;background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.1);color:rgba(255,255,255,0.82);font-size:12px}
.status-indicator{display:flex;align-items:center;gap:8px;padding:6px 12px;background:rgba(255,255,255,0.18);border-radius:8px}
.status-dot{width:8px;height:8px;border-radius:50%;background:#fbbf24}
.status-indicator.connected .status-dot{background:#c2ef4e}
.status-indicator.partial .status-dot{background:#f97316}
.status-indicator.error .status-dot{background:#f87171}
.status-label{font-size:12px;font-weight:500;color:#fff}
.main-layout{display:flex;min-height:calc(100vh - 64px)}
.sidebar{width:240px;background:#150f23;border-right:1px solid #362d59;display:flex;flex-direction:column}
.sidebar-content{padding:16px;flex:1;overflow-y:auto}
.sidebar-section{margin-bottom:24px}
.section-title{padding:8px 12px}
.section-label{font-size:12px;font-weight:500;color:rgba(255,255,255,0.5);text-transform:uppercase}
.sidebar-nav{display:flex;flex-direction:column;gap:4px}
.sidebar-link{display:flex;align-items:center;gap:12px;padding:10px 12px;border-radius:8px;color:rgba(255,255,255,0.7);font-size:14px;text-decoration:none;transition:all .3s}
.sidebar-link:hover{background:rgba(255,255,255,0.06);color:#fff}
.sidebar-link.active{background:#422082;color:#fff}
.link-icon{width:16px;height:16px;opacity:.7}
.sidebar-link.active .link-icon{opacity:1;color:#c2ef4e}
.link-text{flex:1}
.link-badge{padding:2px 6px;background:rgba(248,113,113,0.2);border-radius:4px;color:#f87171;font-size:11px;font-weight:600}
.sidebar-footer{padding:16px;border-top:1px solid #362d59}
.footer-stats{display:flex;flex-direction:column;gap:4px}
.stats-label{font-size:12px;font-weight:500;color:rgba(255,255,255,0.5);text-transform:uppercase}
.stats-value{font-size:20px;font-weight:600;color:#c2ef4e}
.main-content{flex:1;padding:24px;overflow-y:auto;background:#1f1633}
.fade-enter-active,.fade-leave-active{transition:opacity .2s}
.fade-enter-from,.fade-leave-to{opacity:0}
</style>
