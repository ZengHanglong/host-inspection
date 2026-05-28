<template>
  <div class="space-selector">
    <!-- 触发按钮 -->
    <button class="space-trigger" @click="toggleDropdown" :class="{ active: isOpen }">
      <div class="space-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <path d="M12 2a10 10 0 0 1 10 10"/>
          <path d="M12 12l4-4"/>
        </svg>
      </div>
      <span class="space-name">{{ currentSpace.name }}</span>
      <svg class="chevron" :class="{ rotated: isOpen }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polyline points="6 9 12 15 18 9"/>
      </svg>
    </button>

    <!-- 下拉弹窗 -->
    <Teleport to="body">
      <Transition name="dropdown">
        <div v-if="isOpen" class="space-dropdown-overlay" @click="closeDropdown">
          <div class="space-dropdown" @click.stop :style="dropdownStyle">
            <div class="dropdown-header">
              <span class="dropdown-title">选择空间</span>
            </div>
            <div class="space-list">
              <button
                v-for="space in spaces"
                :key="space.id"
                class="space-item"
                :class="{ active: currentSpace.id === space.id }"
                @click="selectSpace(space)"
              >
                <div class="item-icon" :style="{ background: space.color }">
                  <component :is="space.icon" />
                </div>
                <div class="item-content">
                  <span class="item-title">{{ space.name }}</span>
                  <span class="item-desc">{{ space.description }}</span>
                </div>
                <div class="item-arrow" v-if="currentSpace.id === space.id">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="9 18 15 12 9 6"/>
                  </svg>
                </div>
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, h } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const isOpen = ref(false)
const triggerRect = ref({ left: 0, bottom: 0 })

// 空间定义
const spaces = [
  {
    id: 'virtualization',
    name: '虚拟化',
    description: 'VMware、SmartX超融合巡检',
    color: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    route: '/virtualization',
    icon: {
      render() {
        return h('svg', { viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2' }, [
          h('rect', { x: '2', y: '3', width: '20', height: '14', rx: '2' }),
          h('line', { x1: '8', y1: '21', x2: '16', y2: '21' }),
          h('line', { x1: '12', y1: '17', x2: '12', y2: '21' })
        ])
      }
    }
  },
  {
    id: 'database',
    name: '数据库',
    description: 'Oracle、MySQL、SQL Server巡检',
    color: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
    route: '/database',
    icon: {
      render() {
        return h('svg', { viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2' }, [
          h('ellipse', { cx: '12', cy: '5', rx: '9', ry: '3' }),
          h('path', { d: 'M21 5v14c0 1.66-4 3-9 3s-9-1.34-9-3V5' }),
          h('path', { d: 'M3 12c0 1.66 4 3 9 3s9-1.34 9-3' })
        ])
      }
    }
  },
  {
    id: 'backup',
    name: '备份系统',
    description: 'NBU、Veeam、鼎甲、Zerto巡检',
    color: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    route: '/backup',
    icon: {
      render() {
        return h('svg', { viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2' }, [
          h('path', { d: 'M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4' }),
          h('polyline', { points: '7 10 12 15 17 10' }),
          h('line', { x1: '12', y1: '15', x2: '12', y2: '3' })
        ])
      }
    }
  },
  {
    id: 'storage',
    name: '存储系统',
    description: '华为、华瑞、XSKY、SmartX ZBS巡检',
    color: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
    route: '/storage',
    icon: {
      render() {
        return h('svg', { viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2' }, [
          h('rect', { x: '2', y: '2', width: '20', height: '8', rx: '2' }),
          h('rect', { x: '2', y: '14', width: '20', height: '8', rx: '2' }),
          h('line', { x1: '6', y1: '6', x2: '6.01', y2: '6' }),
          h('line', { x1: '6', y1: '18', x2: '6.01', y2: '18' })
        ])
      }
    }
  }
]

const currentSpace = ref(spaces[0])

const dropdownStyle = computed(() => ({
  position: 'fixed',
  left: `${triggerRect.value.left}px`,
  top: `${triggerRect.value.bottom + 8}px`,
  zIndex: 9999
}))

const toggleDropdown = () => {
  if (!isOpen.value) {
    updateTriggerRect()
  }
  isOpen.value = !isOpen.value
}

const closeDropdown = () => {
  isOpen.value = false
}

const updateTriggerRect = () => {
  const trigger = document.querySelector('.space-trigger')
  if (trigger) {
    const rect = trigger.getBoundingClientRect()
    triggerRect.value = {
      left: rect.left,
      bottom: rect.bottom
    }
  }
}

const selectSpace = (space) => {
  currentSpace.value = space
  closeDropdown()
  router.push(space.route)
}

// 点击外部关闭
const handleClickOutside = (e) => {
  if (isOpen.value) {
    const dropdown = document.querySelector('.space-dropdown')
    const trigger = document.querySelector('.space-trigger')
    if (dropdown && trigger && !dropdown.contains(e.target) && !trigger.contains(e.target)) {
      closeDropdown()
    }
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  window.addEventListener('resize', updateTriggerRect)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  window.removeEventListener('resize', updateTriggerRect)
})
</script>

<style scoped>
.space-selector {
  position: relative;
}

.space-trigger {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 14px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 10px;
  color: #ffffff;
  cursor: pointer;
  transition: all 0.25s ease;
}

.space-trigger:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.2);
}

.space-trigger.active {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.25);
}

.space-icon {
  width: 20px;
  height: 20px;
  color: #c2ef4e;
}

.space-icon svg {
  width: 100%;
  height: 100%;
}

.space-name {
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 0.3px;
}

.chevron {
  width: 16px;
  height: 16px;
  opacity: 0.6;
  transition: transform 0.25s ease;
}

.chevron.rotated {
  transform: rotate(180deg);
}

/* 下拉弹窗遮罩 */
.space-dropdown-overlay {
  position: fixed;
  inset: 0;
  z-index: 9998;
}

/* 下拉弹窗 */
.space-dropdown {
  width: 320px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px) saturate(180%);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2), 0 0 0 1px rgba(255, 255, 255, 0.1);
  overflow: hidden;
}

.dropdown-header {
  padding: 16px 20px 12px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.dropdown-title {
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.space-list {
  padding: 8px;
}

.space-item {
  display: flex;
  align-items: center;
  gap: 14px;
  width: 100%;
  padding: 12px 14px;
  background: transparent;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
}

.space-item:hover {
  background: rgba(0, 0, 0, 0.04);
}

.space-item.active {
  background: rgba(106, 95, 193, 0.08);
}

.item-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.item-icon svg {
  width: 22px;
  height: 22px;
}

.item-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.item-title {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
}

.item-desc {
  font-size: 12px;
  color: #64748b;
  line-height: 1.4;
}

.item-arrow {
  width: 20px;
  height: 20px;
  color: #6a5fc1;
}

.item-arrow svg {
  width: 100%;
  height: 100%;
}

/* 动画 */
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.25s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-8px) scale(0.96);
}
</style>
