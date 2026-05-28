<template>
  <div class="credentials-page">
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">API 凭证配置</h1>
        <p class="page-desc">配置各平台 API 连接信息，支持同平台多节点</p>
      </div>
      <div class="header-stats">
        <div class="stat-item">
          <span class="stat-value">{{ configuredCount }}/{{ totalCount }}</span>
          <span class="stat-label">已配置</span>
        </div>
        <div class="stat-item">
          <span class="stat-value connected">{{ connectedCount }}</span>
          <span class="stat-label">已连接</span>
        </div>
      </div>
    </div>

    <!-- 分类展示 -->
    <div class="category-section" v-for="cat in categories" :key="cat.key">
      <div class="category-header">
        <div class="category-icon" :class="cat.key">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="2" y="3" width="20" height="14" rx="2"/>
            <line x1="8" y1="21" x2="16" y2="21"/>
            <line x1="12" y1="17" x2="12" y2="21"/>
          </svg>
        </div>
        <div class="category-info">
          <h2 class="category-name">{{ cat.name }}</h2>
          <span class="category-count">{{ getCategoryInstances(cat.platforms).length }} 个节点</span>
        </div>
      </div>

      <div class="instance-grid">
        <!-- 已有实例 -->
        <div class="instance-card" v-for="inst in getCategoryInstances(cat.platforms)" :key="inst.id" :class="{ connected: inst.is_connected, configured: inst.is_configured && !inst.is_connected }">
          <div class="card-top">
            <div class="card-status">
              <span class="status-dot" :class="inst.is_connected ? 'connected' : inst.is_configured ? 'error' : 'pending'"></span>
              <span class="status-text">{{ inst.is_connected ? '已连接' : inst.is_configured ? '连接失败' : '未配置' }}</span>
            </div>
            <div class="card-env" :class="inst.environment">{{ envName(inst.environment) }}</div>
          </div>

          <h3 class="card-name">{{ inst.display_name }}</h3>
          <p class="card-url">{{ inst.api_url || '未配置地址' }}</p>

          <div class="card-form" v-if="editingId === inst.id">
            <input class="form-input" v-model="form.api_url" placeholder="API 地址" />
            <input class="form-input" type="number" v-model="form.api_port" placeholder="端口" />
            <input class="form-input" v-model="form.api_username" placeholder="用户名" />
            <input class="form-input" type="password" v-model="form.api_password" placeholder="密码" />
            <div class="form-actions">
              <button class="btn-save" @click="saveInstance(inst)" :disabled="saving">保存</button>
              <button class="btn-cancel" @click="editingId = null">取消</button>
            </div>
          </div>

          <div class="card-actions" v-else>
            <button class="btn-config" @click="startEdit(inst)">配置</button>
            <button class="btn-test" @click="testInstance(inst)" :disabled="testingId === inst.id">
              {{ testingId === inst.id ? '测试中...' : '测试' }}
            </button>
            <button class="btn-delete" @click="deleteInstance(inst)" title="删除此节点">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
              </svg>
            </button>
          </div>
        </div>

        <!-- 添加新节点按钮 -->
        <div class="instance-card add-card" @click="showAddForm(cat)">
          <div class="add-icon">+</div>
          <span class="add-text">添加 {{ cat.name }} 节点</span>
        </div>
      </div>
    </div>

    <!-- 添加节点弹窗 -->
    <div class="modal-overlay" v-if="showAdd" @click.self="showAdd = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>添加 {{ addCategoryName }} 节点</h3>
          <button class="modal-close" @click="showAdd = false">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>平台类型</label>
            <select class="form-select" v-model="addForm.platform_code">
              <option v-for="p in addPlatforms" :key="p.code" :value="p.code">{{ p.name }}</option>
            </select>
          </div>
          <div class="form-group">
            <label>节点名称</label>
            <input class="form-input" v-model="addForm.instance_name" placeholder="如: 生产vCenter-02" />
          </div>
          <div class="form-group">
            <label>环境</label>
            <select class="form-select" v-model="addForm.environment">
              <option value="ser">生产</option>
              <option value="pre">准生产</option>
              <option value="dev">测试</option>
            </select>
          </div>
          <div class="form-group">
            <label>API 地址</label>
            <input class="form-input" v-model="addForm.api_url" placeholder="vcenter.example.com" />
          </div>
          <div class="form-group">
            <label>端口</label>
            <input class="form-input" type="number" v-model="addForm.api_port" placeholder="443" />
          </div>
          <div class="form-group">
            <label>用户名</label>
            <input class="form-input" v-model="addForm.api_username" placeholder="administrator@vsphere.local" />
          </div>
          <div class="form-group">
            <label>密码</label>
            <input class="form-input" type="password" v-model="addForm.api_password" placeholder="密码" />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="showAdd = false">取消</button>
          <button class="btn-save" @click="createInstance" :disabled="saving">{{ saving ? '创建中...' : '创建' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

const credentials = ref([])
const editingId = ref(null)
const saving = ref(false)
const testingId = ref(null)
const showAdd = ref(false)
const addCategoryName = ref('')
const addPlatforms = ref([])

const form = ref({ api_url: '', api_port: 443, api_username: '', api_password: '' })
const addForm = ref({ platform_code: '', instance_name: '', environment: 'ser', api_url: '', api_port: 443, api_username: '', api_password: '' })

const categories = [
  { key: 'virtualization', name: '虚拟化', platforms: ['vmware', 'smartx'] },
  { key: 'database', name: '数据库', platforms: ['oracle', 'mysql', 'sqlserver', 'gbase', 'tdsql'] },
  { key: 'backup', name: '备份系统', platforms: ['netbackup', 'veeam', 'dingjia', 'zerto'] },
  { key: 'storage', name: '存储系统', platforms: ['hwstorage', 'huarui', 'xsky', 'smartxzbs'] },
]

const envName = (code) => ({ dev: '测试', pre: '准生产', ser: '生产' }[code] || code)
const platformNames = {
  vmware: 'VMware vCenter', smartx: 'SmartX 超融合',
  oracle: 'Oracle', mysql: 'MySQL', sqlserver: 'SQL Server', gbase: 'Gbase', tdsql: 'TDSQL',
  netbackup: 'Veritas NetBackup', veeam: 'Veeam', dingjia: '鼎甲', zerto: 'Zerto',
  hwstorage: '华为存储', huarui: '华瑞存储', xsky: 'XSKY', smartxzbs: 'SmartX ZBS',
  huawei_cd: '华为云桌面', sangfor_cd: '深信服云桌面', rizhiyi: '日志易',
}

const configuredCount = computed(() => credentials.value.filter(c => c.is_configured).length)
const connectedCount = computed(() => credentials.value.filter(c => c.is_connected).length)
const totalCount = computed(() => credentials.value.length)

const getCategoryInstances = (platforms) => credentials.value.filter(c => platforms.includes(c.platform))

const loadCredentials = async () => {
  try {
    const res = await axios.get('/api/credentials/list')
    credentials.value = res.data.credentials || []
  } catch (e) { console.error(e) }
}

const startEdit = (inst) => {
  editingId.value = inst.id
  form.value = { api_url: inst.api_url || '', api_port: inst.api_port || 443, api_username: inst.api_username || '', api_password: '' }
}

const saveInstance = async (inst) => {
  saving.value = true
  try {
    await axios.put(`/api/credentials/instances/${inst.id}`, form.value)
    editingId.value = null
    await loadCredentials()
  } catch (e) { alert('保存失败: ' + (e.response?.data?.detail || e.message)) }
  finally { saving.value = false }
}

const testInstance = async (inst) => {
  testingId.value = inst.id
  try {
    const res = await axios.post(`/api/credentials/instances/${inst.id}/test`)
    alert(res.data.success ? `${inst.display_name}: ${res.data.message}` : `${inst.display_name}: ${res.data.message}`)
    await loadCredentials()
  } catch (e) { alert('测试失败: ' + (e.response?.data?.detail || e.message)) }
  finally { testingId.value = null }
}

const deleteInstance = async (inst) => {
  if (!confirm(`确定删除 "${inst.display_name}" 吗？`)) return
  try {
    await axios.delete(`/api/credentials/instances/${inst.id}`)
    await loadCredentials()
  } catch (e) { alert('删除失败: ' + (e.response?.data?.detail || e.message)) }
}

const showAddForm = (cat) => {
  addCategoryName.value = cat.name
  addPlatforms.value = cat.platforms.map(code => ({ code, name: platformNames[code] || code }))
  addForm.value = { platform_code: cat.platforms[0], instance_name: '', environment: 'ser', api_url: '', api_port: 443, api_username: '', api_password: '' }
  showAdd.value = true
}

const createInstance = async () => {
  if (!addForm.value.instance_name) { alert('请输入节点名称'); return }
  if (!addForm.value.platform_code) { alert('请选择平台类型'); return }
  saving.value = true
  try {
    await axios.post('/api/credentials/instances', addForm.value)
    showAdd.value = false
    await loadCredentials()
  } catch (e) { alert('创建失败: ' + (e.response?.data?.detail || e.message)) }
  finally { saving.value = false }
}

onMounted(loadCredentials)
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Rubik:wght@400;500;600;700&display=swap');

.credentials-page { padding: 24px; max-width: 1200px; margin: 0 auto; font-family: 'Rubik', sans-serif; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 32px; }
.page-title { font-size: 28px; font-weight: 700; color: #fff; margin: 0 0 4px 0; }
.page-desc { font-size: 14px; color: rgba(255,255,255,0.5); margin: 0; }
.header-stats { display: flex; gap: 24px; }
.stat-item { display: flex; flex-direction: column; align-items: center; gap: 4px; }
.stat-value { font-size: 24px; font-weight: 700; color: #fff; }
.stat-value.connected { color: #c2ef4e; }
.stat-label { font-size: 12px; color: rgba(255,255,255,0.5); text-transform: uppercase; letter-spacing: 0.5px; }

.category-section { margin-bottom: 32px; }
.category-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.08); }
.category-icon { width: 36px; height: 36px; border-radius: 10px; display: flex; align-items: center; justify-content: center; }
.category-icon svg { width: 18px; height: 18px; }
.category-icon.virtualization { background: rgba(106,95,193,0.2); color: #6a5fc1; }
.category-icon.database { background: rgba(52,211,153,0.2); color: #34d399; }
.category-icon.backup { background: rgba(96,165,250,0.2); color: #60a5fa; }
.category-icon.storage { background: rgba(251,191,36,0.2); color: #fbbf24; }
.category-name { font-size: 16px; font-weight: 600; color: #fff; margin: 0; }
.category-count { font-size: 12px; color: rgba(255,255,255,0.4); }

.instance-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }
.instance-card { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; padding: 18px; transition: all 0.25s; }
.instance-card:hover { background: rgba(255,255,255,0.06); }
.instance-card.connected { border-color: rgba(194,239,78,0.25); }
.instance-card.configured { border-color: rgba(248,113,113,0.2); }

.card-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.card-status { display: flex; align-items: center; gap: 6px; }
.status-dot { width: 8px; height: 8px; border-radius: 50%; }
.status-dot.connected { background: #c2ef4e; }
.status-dot.error { background: #f87171; }
.status-dot.pending { background: #fbbf24; }
.status-text { font-size: 12px; color: rgba(255,255,255,0.6); }
.card-env { padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; text-transform: uppercase; }
.card-env.ser { background: rgba(194,239,78,0.15); color: #c2ef4e; }
.card-env.pre { background: rgba(251,191,36,0.15); color: #fbbf24; }
.card-env.dev { background: rgba(106,95,193,0.15); color: #6a5fc1; }

.card-name { font-size: 15px; font-weight: 600; color: #fff; margin: 0 0 4px 0; }
.card-url { font-size: 12px; color: rgba(255,255,255,0.4); margin: 0 0 14px 0; word-break: break-all; }

.card-form { display: flex; flex-direction: column; gap: 8px; margin-bottom: 12px; }
.form-input, .form-select { padding: 8px 12px; background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.12); border-radius: 8px; color: #fff; font-size: 13px; font-family: 'Rubik', sans-serif; width: 100%; box-sizing: border-box; }
.form-input::placeholder { color: rgba(255,255,255,0.3); }
.form-input:focus, .form-select:focus { outline: none; border-color: #6a5fc1; }
.form-select { appearance: none; -webkit-appearance: none; background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='rgba(255,255,255,0.5)' stroke-width='2'%3E%3Cpath d='M7 10l5 5 5-5'/%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: right 12px center; padding-right: 36px; cursor: pointer; }
.form-select option { background: #1f1633; color: #fff; padding: 8px; }
.form-actions { display: flex; gap: 8px; }

.card-actions { display: flex; gap: 8px; }
.btn-config, .btn-test, .btn-save, .btn-cancel { padding: 6px 14px; border-radius: 8px; font-size: 12px; font-weight: 500; cursor: pointer; border: 1px solid rgba(255,255,255,0.12); transition: all 0.2s; font-family: 'Rubik', sans-serif; }
.btn-config { background: rgba(106,95,193,0.2); color: #a78bfa; border-color: rgba(106,95,193,0.3); }
.btn-config:hover { background: rgba(106,95,193,0.3); }
.btn-test { background: rgba(96,165,250,0.2); color: #60a5fa; border-color: rgba(96,165,250,0.3); }
.btn-test:hover { background: rgba(96,165,250,0.3); }
.btn-test:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-save { background: #6a5fc1; color: #fff; border-color: #6a5fc1; }
.btn-save:hover { background: #7a6fd1; }
.btn-save:disabled { opacity: 0.5; }
.btn-cancel { background: rgba(255,255,255,0.08); color: rgba(255,255,255,0.6); }
.btn-cancel:hover { background: rgba(255,255,255,0.12); }
.btn-delete { background: transparent; border: none; color: rgba(248,113,113,0.5); cursor: pointer; padding: 6px; border-radius: 6px; transition: all 0.2s; }
.btn-delete:hover { color: #f87171; background: rgba(248,113,113,0.1); }
.btn-delete svg { width: 14px; height: 14px; }

.add-card { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px; min-height: 140px; border-style: dashed; cursor: pointer; }
.add-card:hover { border-color: #6a5fc1; background: rgba(106,95,193,0.05); }
.add-icon { font-size: 28px; color: rgba(255,255,255,0.3); }
.add-text { font-size: 13px; color: rgba(255,255,255,0.4); }

.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.6); backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-content { background: #1f1633; border: 1px solid #362d59; border-radius: 16px; width: 420px; max-height: 80vh; overflow-y: auto; }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 18px 24px; border-bottom: 1px solid #362d59; }
.modal-header h3 { font-size: 16px; font-weight: 600; color: #fff; margin: 0; }
.modal-close { background: none; border: none; color: rgba(255,255,255,0.5); font-size: 24px; cursor: pointer; }
.modal-body { padding: 20px 24px; display: flex; flex-direction: column; gap: 14px; }
.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-group label { font-size: 12px; font-weight: 500; color: rgba(255,255,255,0.6); text-transform: uppercase; letter-spacing: 0.3px; }
.modal-footer { display: flex; justify-content: flex-end; gap: 10px; padding: 16px 24px; border-top: 1px solid #362d59; }
</style>
