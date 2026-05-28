import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue')
  },
  {
    path: '/virtualization',
    name: 'Virtualization',
    component: () => import('@/views/Virtualization.vue')
  },
  {
    path: '/esxi-logs',
    name: 'EsxiLogs',
    component: () => import('@/views/EsxiLogs.vue')
  },
  {
    path: '/database',
    name: 'Database',
    component: () => import('@/views/Dashboard.vue')
  },
  {
    path: '/backup',
    name: 'Backup',
    component: () => import('@/views/Dashboard.vue')
  },
  {
    path: '/storage',
    name: 'Storage',
    component: () => import('@/views/Dashboard.vue')
  },
  {
    path: '/inspection',
    name: 'Inspection',
    component: () => import('@/views/Inspection.vue')
  },
  {
    path: '/credentials',
    name: 'Credentials',
    component: () => import('@/views/Credentials.vue')
  },
  {
    path: '/periodic/snapshot',
    name: 'PeriodicSnapshot',
    component: () => import('@/views/periodic/Snapshot.vue')
  },
  {
    path: '/periodic/naming',
    name: 'PeriodicNaming',
    component: () => import('@/views/periodic/Naming.vue')
  },
  {
    path: '/periodic/idle',
    name: 'PeriodicIdle',
    component: () => import('@/views/periodic/IdleVM.vue')
  },
  {
    path: '/periodic/large',
    name: 'PeriodicLarge',
    component: () => import('@/views/periodic/LargeVM.vue')
  },
  {
    path: '/alerts',
    name: 'Alerts',
    component: () => import('@/views/Alerts.vue')
  },
  {
    path: '/ledger/vm',
    name: 'VmLedger',
    component: () => import('@/views/ledger/VmLedger.vue')
  },
  {
    path: '/ledger/physical',
    name: 'PhysicalLedger',
    component: () => import('@/views/ledger/PhysicalLedger.vue')
  },
  {
    path: '/ledger/database',
    name: 'DbLedger',
    component: () => import('@/views/ledger/DbLedger.vue')
  },
  {
    path: '/history',
    name: 'History',
    component: () => import('@/views/History.vue')
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/Settings.vue')
  },
  {
    path: '/reports',
    name: 'Reports',
    component: () => import('@/views/Reports.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router