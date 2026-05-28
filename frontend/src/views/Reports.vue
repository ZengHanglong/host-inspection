<template>
  <div class="reports-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">
          <span class="title-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
              <line x1="16" y1="13" x2="8" y2="13"/>
              <line x1="16" y1="17" x2="8" y2="17"/>
            </svg>
          </span>
          {{ t('reports.title') }}
        </h1>
        <p class="page-desc">
          {{ t('reports.desc') }}
        </p>
      </div>
      <div class="header-badge" :class="hasCredentials ? 'ready' : 'warning'">
        <span class="badge-icon">
          <svg v-if="hasCredentials" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <path d="M9 12l2 2 4-4"/>
          </svg>
          <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
        </span>
        <span class="badge-text">{{ hasCredentials ? t('reports.ready') : t('reports.needsConfig') }}</span>
      </div>
    </div>

    <!-- 未配置提示 -->
    <transition name="slide-down">
      <div class="warning-banner" v-if="!hasCredentials">
        <div class="banner-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
            <line x1="12" y1="9" x2="12" y2="13"/>
            <line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
        </div>
        <div class="banner-content">
          <span class="banner-title">{{ t('reports.warningTitle') }}</span>
          <span class="banner-desc">{{ t('reports.warningDesc') }}</span>
        </div>
        <button class="banner-btn" @click="goToCredentials">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5"/>
          </svg>
          {{ t('reports.goCredentials') }}
        </button>
      </div>
    </transition>

    <!-- 报告配置卡片 -->
    <div class="config-card" v-if="hasCredentials">
      <div class="card-decoration">
        <div class="decoration-line"></div>
      </div>

      <div class="card-body">
        <!-- 数据来源展示 -->
        <div class="source-section">
          <div class="source-header">
            <span class="source-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              </svg>
            </span>
            <span class="source-title">{{ t('reports.dataSources') }}</span>
          </div>
          <div class="source-list">
            <div class="source-item" v-for="(source, index) in dataSources" :key="index">
              <span class="source-dot"></span>
              <span class="source-text">{{ source }}</span>
            </div>
            <div class="source-item empty" v-if="dataSources.length === 0">
              <span class="source-text">{{ t('reports.noSources') }}</span>
            </div>
          </div>
        </div>

        <!-- 报告配置表单 -->
        <div class="form-section">
          <div class="form-group">
            <label class="form-label">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
                <polyline points="9 22 9 12 15 12 15 22"/>
              </svg>
              {{ t('reports.companyName') }}
            </label>
            <input class="form-input" v-model="reportForm.company_name" :placeholder="t('reports.companyName')" />
          </div>

          <div class="form-group">
            <label class="form-label">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
              </svg>
              {{ t('reports.reportFormat') }}
            </label>
            <div class="format-options">
              <button class="format-btn" :class="{ active: reportForm.format === 'docx' }" @click="reportForm.format = 'docx'">
                <span class="format-icon docx">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/>
                    <path d="M9 13h6"/>
                    <path d="M9 17h6"/>
                  </svg>
                </span>
                <span class="format-name">{{ t('reports.format.docx') }}</span>
                <span class="format-desc">{{ t('reports.format.docxDesc') }}</span>
              </button>
              <button class="format-btn" :class="{ active: reportForm.format === 'html' }" @click="reportForm.format = 'html'">
                <span class="format-icon html">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="16 18 22 12 16 6"/>
                    <polyline points="8 6 2 12 8 18"/>
                  </svg>
                </span>
                <span class="format-name">{{ t('reports.format.html') }}</span>
                <span class="format-desc">{{ t('reports.format.htmlDesc') }}</span>
              </button>
              <button class="format-btn" :class="{ active: reportForm.format === 'json' }" @click="reportForm.format = 'json'">
                <span class="format-icon json">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="4 7 4 4 20 4 20 7"/>
                    <polyline points="4 17 4 20 20 20 20 17"/>
                    <line x1="4" y1="12" x2="20" y2="12"/>
                  </svg>
                </span>
                <span class="format-name">{{ t('reports.format.json') }}</span>
                <span class="format-desc">{{ t('reports.format.jsonDesc') }}</span>
              </button>
            </div>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="action-section">
          <button class="generate-btn" @click="downloadReport" :disabled="loading">
            <span class="btn-icon" :class="{ loading: loading }">
              <svg v-if="!loading" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="7 10 12 15 17 10"/>
                <line x1="12" y1="15" x2="12" y2="3"/>
              </svg>
              <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <path d="M12 6v6l4 2"/>
              </svg>
            </span>
            <span class="btn-text">{{ loading ? t('reports.actions.generating') : t('reports.actions.download') }}</span>
          </button>
          <button class="preview-btn" @click="previewReport" :disabled="loading">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
              <circle cx="12" cy="12" r="3"/>
            </svg>
            {{ t('reports.actions.preview') }}
          </button>
        </div>
      </div>
    </div>

    <!-- 数据预览 -->
    <transition name="slide-up">
      <div class="preview-card" v-if="previewData">
        <div class="preview-header">
          <span class="preview-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
              <circle cx="8.5" cy="8.5" r="1.5"/>
              <polyline points="21 15 16 10 5 21"/>
            </svg>
            {{ t('reports.preview.title') }}
          </span>
          <span class="preview-time">{{ previewTime }}</span>
        </div>

        <!-- 统计概览 -->
        <div class="stats-grid">
          <div class="stat-box">
            <span class="stat-value">{{ previewData.overall_statistics?.total_hosts || 0 }}</span>
            <span class="stat-label">{{ t('reports.preview.totalHosts') }}</span>
          </div>
          <div class="stat-box success">
            <span class="stat-value">{{ previewData.overall_statistics?.normal_hosts || 0 }}</span>
            <span class="stat-label">{{ t('reports.preview.normal') }}</span>
          </div>
          <div class="stat-box warning">
            <span class="stat-value">{{ previewData.overall_statistics?.warning_hosts || 0 }}</span>
            <span class="stat-label">{{ t('reports.preview.warning') }}</span>
          </div>
          <div class="stat-box danger">
            <span class="stat-value">{{ previewData.overall_statistics?.critical_hosts || 0 }}</span>
            <span class="stat-label">{{ t('reports.preview.critical') }}</span>
          </div>
        </div>

        <!-- 平台详情 -->
        <div class="platforms-preview">
          <div class="platform-row" v-for="platform in previewData.platforms" :key="platform.platform">
            <div class="platform-info">
              <span class="platform-name">{{ platform.display_name }}</span>
              <span class="platform-status" :class="normalizeStatus(platform.status) === 'normal' ? 'success' : 'warning'">{{ translateStatus(platform.status) }}</span>
            </div>
            <div class="platform-stats">
              <span class="stat">{{ platform.statistics?.total || 0 }} {{ t('reports.preview.hosts') }}</span>
              <span class="stat">{{ platform.statistics?.normal || 0 }} {{ t('reports.preview.normal') }}</span>
            </div>
            <div class="platform-source">{{ platform.data_source }}</div>
          </div>
        </div>

        <!-- 告警列表 -->
        <div class="alerts-preview" v-if="previewData.warnings?.length > 0">
          <span class="alerts-title">{{ t('reports.preview.alertsTitle', { count: previewData.warnings.length }) }}</span>
          <div class="alert-row" v-for="(alert, index) in previewData.warnings" :key="index" :class="alert.alert_level">
            <span class="alert-host">{{ alert.host_name }}</span>
            <span class="alert-type">{{ alert.alert_type }}</span>
            <span class="alert-level" :class="alert.alert_level">{{ translateStatus(alert.alert_level) }}</span>
          </div>
        </div>
      </div>
    </transition>

    <!-- 报告模板说明 -->
    <div class="template-info">
      <div class="info-header">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="16" x2="12" y2="12"/>
          <line x1="12" y1="8" x2="12.01" y2="8"/>
        </svg>
        {{ t('reports.template.title') }}
      </div>
      <div class="info-list">
        <div class="info-item" v-for="item in templateItems" :key="item">
          <span class="item-icon check"></span>
          <span class="item-text">{{ item }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const router = useRouter()
const { t, locale, tm } = useI18n()

const hasCredentials = ref(false)
const dataSources = ref([])
const loading = ref(false)
const previewData = ref(null)

const reportForm = ref({
  company_name: '厦门国际信托',
  format: 'docx'
})

const templateItems = computed(() => tm('reports.template.items'))
const previewTime = computed(() => new Date().toLocaleString(locale.value))

const normalizeStatus = (status) => {
  if (status === 'normal' || status === '正常') return 'normal'
  if (status === 'critical' || status === '严重') return 'critical'
  if (status === 'warning' || status === '警告') return 'warning'
  return status
}

const translateStatus = (status) => t(`common.status.${normalizeStatus(status)}`, status)

const checkCredentials = async () => {
  try {
    const response = await axios.get('/api/dashboard')
    hasCredentials.value = response.data.status === 'real_data'
    if (hasCredentials.value) {
      dataSources.value = response.data.overall?.data_sources || []
    }
  } catch (error) {
    hasCredentials.value = false
  }
}

const downloadReport = async () => {
  loading.value = true
  try {
    const format = reportForm.value.format
    const company_name = reportForm.value.company_name

    let url = ''
    if (format === 'docx') {
      url = `/api/report/download/docx?company_name=${encodeURIComponent(company_name)}`
    } else if (format === 'html') {
      url = '/api/report/download/html'
    } else {
      url = '/api/report/daily?format=json'
    }

    if (format === 'json') {
      const response = await axios.get(url)
      previewData.value = response.data
      ElMessage.success(t('reports.messages.jsonLoaded'))
    } else {
      const response = await axios.get(url, { responseType: 'blob' })
      const blob = new Blob([response.data])
      const link = document.createElement('a')
      link.href = window.URL.createObjectURL(blob)

      const filename = format === 'docx'
        ? `${t('reports.file.docxPrefix')}_${new Date().toISOString().slice(0,10).replace(/-/g,'')}.docx`
        : `inspection_report_${new Date().toISOString().slice(0,10)}.html`

      link.download = filename
      link.click()
      window.URL.revokeObjectURL(link.href)
      ElMessage.success(t('reports.messages.downloadSuccess'))
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || t('reports.messages.generateFailed'))
  } finally {
    loading.value = false
  }
}

const previewReport = async () => {
  loading.value = true
  try {
    const response = await axios.get('/api/report/daily?format=json')
    previewData.value = response.data
    ElMessage.success(t('reports.messages.previewLoaded'))
  } catch (error) {
    ElMessage.error(t('reports.messages.previewFailed'))
  } finally {
    loading.value = false
  }
}

const goToCredentials = () => {
  router.push('/credentials')
}

onMounted(() => {
  checkCredentials()
})
</script>

<style scoped>
.reports-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* 页面头部 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 32px;
  background: linear-gradient(135deg, rgba(168, 85, 247, 0.1) 0%, rgba(102, 126, 234, 0.1) 100%);
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.header-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 24px;
  font-weight: 700;
  color: white;
}

.title-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #a855f7 0%, #667eea 100%);
}

.title-icon svg {
  width: 22px;
  height: 22px;
  color: white;
}

.page-desc {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
}

.header-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  border-radius: 12px;
}

.header-badge.ready {
  background: rgba(34, 197, 94, 0.2);
  border: 1px solid rgba(34, 197, 94, 0.3);
}

.header-badge.warning {
  background: rgba(251, 191, 36, 0.2);
  border: 1px solid rgba(251, 191, 36, 0.3);
}

.badge-icon svg {
  width: 18px;
  height: 18px;
}

.header-badge.ready .badge-icon svg {
  color: #22c55e;
}

.header-badge.warning .badge-icon svg {
  color: #fbbf24;
}

.badge-text {
  font-size: 14px;
  font-weight: 500;
}

.header-badge.ready .badge-text {
  color: #22c55e;
}

.header-badge.warning .badge-text {
  color: #fbbf24;
}

/* 警告Banner */
.warning-banner {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 24px;
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.1) 0%, rgba(245, 158, 11, 0.1) 100%);
  border-radius: 16px;
  border: 1px solid rgba(251, 191, 36, 0.3);
}

.banner-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(251, 191, 36, 0.2);
}

.banner-icon svg {
  width: 24px;
  height: 24px;
  color: #fbbf24;
}

.banner-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.banner-title {
  font-size: 16px;
  font-weight: 600;
  color: #fbbf24;
}

.banner-desc {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
}

.banner-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 12px;
  color: white;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.banner-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
}

.banner-btn svg {
  width: 18px;
  height: 18px;
}

/* 配置卡片 */
.config-card {
  position: relative;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  overflow: hidden;
}

.card-decoration {
  height: 4px;
  background: linear-gradient(90deg, #a855f7 0%, #667eea 50%, #4ade80 100%);
}

.card-body {
  padding: 24px;
}

/* 数据来源 */
.source-section {
  margin-bottom: 24px;
}

.source-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.source-icon svg {
  width: 20px;
  height: 20px;
  color: #22c55e;
}

.source-title {
  font-size: 14px;
  font-weight: 600;
  color: white;
}

.source-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.source-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
}

.source-item.empty {
  background: rgba(255, 255, 255, 0.05);
}

.source-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #22c55e;
}

.source-text {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.8);
}

/* 表单 */
.form-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-bottom: 24px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
}

.form-label svg {
  width: 18px;
  height: 18px;
  color: rgba(255, 255, 255, 0.5);
}

.form-input {
  padding: 14px 18px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  color: white;
  font-size: 15px;
  transition: all 0.3s ease;
}

.form-input:focus {
  outline: none;
  border-color: #a855f7;
  box-shadow: 0 0 0 3px rgba(168, 85, 247, 0.2);
}

.form-input::placeholder {
  color: rgba(255, 255, 255, 0.3);
}

/* 格式选项 */
.format-options {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.format-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.format-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  transform: translateY(-2px);
}

.format-btn.active {
  background: rgba(168, 85, 247, 0.1);
  border-color: rgba(168, 85, 247, 0.3);
}

.format-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.1);
}

.format-icon svg {
  width: 20px;
  height: 20px;
  color: rgba(255, 255, 255, 0.7);
}

.format-btn.active .format-icon {
  background: rgba(168, 85, 247, 0.2);
}

.format-btn.active .format-icon svg {
  color: #a855f7;
}

.format-name {
  font-size: 14px;
  font-weight: 600;
  color: white;
}

.format-desc {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

/* 操作按钮 */
.action-section {
  display: flex;
  gap: 16px;
}

.generate-btn {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 32px;
  background: linear-gradient(135deg, #a855f7 0%, #667eea 100%);
  border: none;
  border-radius: 12px;
  color: white;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.generate-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 12px 30px rgba(168, 85, 247, 0.4);
}

.generate-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.btn-icon svg {
  width: 20px;
  height: 20px;
}

.btn-icon.loading svg {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.preview-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px 24px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  color: white;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.preview-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.2);
}

.preview-btn:disabled {
  opacity: 0.5;
}

.preview-btn svg {
  width: 18px;
  height: 18px;
}

/* 预览卡片 */
.preview-card {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 24px;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.preview-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  font-weight: 600;
  color: white;
}

.preview-title svg {
  width: 22px;
  height: 22px;
  color: #a855f7;
}

.preview-time {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

/* 统计网格 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.stat-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
}

.stat-box.success {
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.2);
}

.stat-box.warning {
  background: rgba(251, 191, 36, 0.1);
  border: 1px solid rgba(251, 191, 36, 0.2);
}

.stat-box.danger {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: white;
  font-family: 'SF Mono', 'Consolas', monospace;
}

.stat-box.success .stat-value {
  color: #22c55e;
}

.stat-box.warning .stat-value {
  color: #fbbf24;
}

.stat-box.danger .stat-value {
  color: #ef4444;
}

.stat-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
}

/* 平台预览 */
.platforms-preview {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 20px;
}

.platform-row {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
}

.platform-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.platform-name {
  font-size: 14px;
  font-weight: 600;
  color: white;
}

.platform-status {
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 6px;
}

.platform-status.success {
  background: rgba(34, 197, 94, 0.2);
  color: #22c55e;
}

.platform-status.warning {
  background: rgba(251, 191, 36, 0.2);
  color: #fbbf24;
}

.platform-stats {
  display: flex;
  gap: 12px;
}

.stat {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
}

.platform-source {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
}

/* 告警预览 */
.alerts-preview {
  margin-top: 20px;
}

.alerts-title {
  font-size: 14px;
  font-weight: 600;
  color: white;
  margin-bottom: 12px;
}

.alert-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
}

.alert-row.warning {
  background: rgba(251, 191, 36, 0.1);
}

.alert-row.critical {
  background: rgba(239, 68, 68, 0.1);
}

.alert-host {
  font-size: 14px;
  color: white;
  flex: 1;
}

.alert-type {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
}

.alert-level {
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 6px;
}

.alert-level.warning {
  background: rgba(251, 191, 36, 0.2);
  color: #fbbf24;
}

.alert-level.critical {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

/* 模板说明 */
.template-info {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 20px;
}

.info-header {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 600;
  color: white;
  margin-bottom: 16px;
}

.info-header svg {
  width: 20px;
  height: 20px;
  color: #a855f7;
}

.info-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.item-icon.check {
  width: 20px;
  height: 20px;
  border-radius: 6px;
  background: rgba(34, 197, 94, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
}

.item-icon.check::after {
  content: '';
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #22c55e;
}

.item-text {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
}

/* 过渡动画 */
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.4s ease;
}

.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.4s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

/* 响应式 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }

  .format-options {
    grid-template-columns: 1fr;
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .action-section {
    flex-direction: column;
  }
}
</style>