<template>
  <div class="alerts-bell">
    <button
      ref="triggerRef"
      class="alerts-button"
      :class="{ collapsed }"
      :data-tooltip="t('alerts.triggerLabel')"
      aria-haspopup="true"
      :aria-expanded="isDropdownOpen"
      :aria-label="count > 0 ? t('alerts.triggerLabelCount', { count }) : t('alerts.triggerLabel')"
      @click="toggleDropdown"
    >
      <span class="bell-wrap">
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" class="bell-icon" aria-hidden="true">
          <path
            d="M10 3C7.23858 3 5 5.23858 5 8V11L3.5 13.5H16.5L15 11V8C15 5.23858 12.7614 3 10 3Z"
            stroke="currentColor"
            stroke-width="1.5"
            stroke-linejoin="round"
          />
          <path
            d="M8 16C8 17.1046 8.89543 18 10 18C11.1046 18 12 17.1046 12 16"
            stroke="currentColor"
            stroke-width="1.5"
          />
        </svg>
        <span v-if="count > 0" class="count-badge">{{ count }}</span>
      </span>
      <span v-if="!collapsed" class="alerts-label">{{ t('alerts.triggerLabel') }}</span>
      <svg
        v-if="!collapsed"
        class="chevron"
        :class="{ 'chevron-open': isDropdownOpen }"
        width="16"
        height="16"
        viewBox="0 0 16 16"
        fill="none"
        aria-hidden="true"
      >
        <path d="M4 6L8 10L12 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
      </svg>
    </button>

    <div v-if="isDropdownOpen" ref="menuRef" class="dropdown-menu" role="menu" @keydown.esc.prevent="closeDropdown()">
      <div class="dropdown-header">{{ t('alerts.title') }} ({{ count }})</div>

      <div v-if="error" class="dropdown-message error-message">{{ t('alerts.loadError') }}</div>
      <div v-else-if="loading" class="dropdown-message">{{ t('common.loading') }}</div>
      <div v-else-if="count === 0" class="dropdown-message">{{ t('alerts.empty') }}</div>
      <div v-else class="alerts-list">
        <button v-for="alert in alerts" :key="alert.sku" class="dropdown-item" role="menuitem" @click="goToItem(alert)">
          <span
            class="severity-dot"
            :style="{ background: alert.severity === 'critical' ? '#ef4444' : '#f59e0b' }"
            aria-hidden="true"
          ></span>
          <span class="alert-body">
            <span class="alert-name">
              <strong>{{ alert.sku }}</strong>
              <span class="alert-item-name">{{ alert.name }}</span>
            </span>
            <span class="alert-meta">
              {{ t('alerts.stockOf', { qty: alert.quantity_on_hand, reorder: alert.reorder_point }) }}
              &middot; {{ alert.warehouse }}
            </span>
          </span>
          <span :class="['badge', alert.severity === 'critical' ? 'danger' : 'warning']">
            {{ t('alerts.severity.' + alert.severity) }}
          </span>
        </button>
      </div>

      <button class="dropdown-footer" role="menuitem" @click="goToInventory">
        {{ t('alerts.viewAll') }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

defineProps({
  collapsed: { type: Boolean, default: false }
})

const { t } = useI18n()
const router = useRouter()

const isDropdownOpen = ref(false)
const triggerRef = ref(null)
const menuRef = ref(null)

const alerts = ref([])
const loading = ref(true)
const error = ref(null)

const count = computed(() => alerts.value.length)

// Poll interval id for the 60s background refresh
let refreshTimer = null

const loadAlerts = async () => {
  try {
    error.value = null
    alerts.value = await api.getLowStockAlerts()
  } catch (err) {
    console.error('Failed to load low-stock alerts:', err)
    error.value = t('alerts.loadError')
  } finally {
    loading.value = false
  }
}

// Close the menu when a click/tap lands outside both the menu and its trigger
const handleOutsideClick = (event) => {
  if (
    menuRef.value &&
    !menuRef.value.contains(event.target) &&
    triggerRef.value &&
    !triggerRef.value.contains(event.target)
  ) {
    closeDropdown()
  }
}

const openDropdown = async () => {
  isDropdownOpen.value = true
  document.addEventListener('mousedown', handleOutsideClick)
  // Refetch each time the panel opens so counts stay current
  loadAlerts()
  await nextTick()
  menuRef.value?.querySelector('[role="menuitem"]')?.focus()
}

const closeDropdown = ({ returnFocus = true } = {}) => {
  if (!isDropdownOpen.value) return
  isDropdownOpen.value = false
  document.removeEventListener('mousedown', handleOutsideClick)
  if (returnFocus) triggerRef.value?.focus()
}

const toggleDropdown = () => {
  if (isDropdownOpen.value) {
    closeDropdown()
  } else {
    openDropdown()
  }
}

const goToItem = (alert) => {
  closeDropdown({ returnFocus: false })
  router.push({ path: '/inventory', query: { item: alert.sku } })
}

const goToInventory = () => {
  closeDropdown({ returnFocus: false })
  router.push('/inventory')
}

onMounted(() => {
  loadAlerts()
  refreshTimer = setInterval(loadAlerts, 60000)
})

onUnmounted(() => {
  document.removeEventListener('mousedown', handleOutsideClick)
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>

<style scoped>
.alerts-bell {
  position: relative;
}

.alerts-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.875rem;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: inherit;
  font-size: 0.875rem;
  color: #334155;
  width: 100%;
}

.alerts-button:hover {
  background: #f8fafc;
  border-color: #cbd5e1;
}

.alerts-button:focus-visible {
  outline: 2px solid #2563eb;
  outline-offset: 2px;
}

.alerts-button.collapsed {
  justify-content: center;
  padding: 0.5rem;
  gap: 0;
}

.bell-wrap {
  position: relative;
  display: flex;
  flex-shrink: 0;
}

.bell-icon {
  color: #64748b;
  flex-shrink: 0;
}

.count-badge {
  position: absolute;
  top: -6px;
  right: -6px;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  border-radius: 8px;
  background: #ef4444;
  color: white;
  font-size: 0.625rem;
  font-weight: 700;
  line-height: 16px;
  text-align: center;
}

.alerts-label {
  font-weight: 500;
  flex: 1;
  text-align: left;
}

.chevron {
  color: #64748b;
  transition: transform 0.2s ease;
  flex-shrink: 0;
}

.chevron-open {
  transform: rotate(180deg);
}

.dropdown-menu {
  position: absolute;
  bottom: calc(100% + 0.5rem);
  left: 0;
  min-width: 300px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  overflow: hidden;
}

.dropdown-header {
  padding: 0.75rem 1rem;
  font-size: 0.875rem;
  font-weight: 700;
  color: #0f172a;
  border-bottom: 1px solid #e2e8f0;
}

.dropdown-message {
  padding: 1rem;
  font-size: 0.875rem;
  color: #64748b;
}

.dropdown-message.error-message {
  color: #991b1b;
}

.alerts-list {
  max-height: 320px;
  overflow-y: auto;
}

.dropdown-item {
  width: 100%;
  display: flex;
  align-items: flex-start;
  gap: 0.625rem;
  padding: 0.75rem 1rem;
  background: none;
  border: none;
  border-bottom: 1px solid #f1f5f9;
  text-align: left;
  cursor: pointer;
  transition: background 0.15s ease;
  font-family: inherit;
  font-size: 0.875rem;
  color: #334155;
}

.dropdown-item:hover {
  background: #f8fafc;
}

.dropdown-item:focus-visible {
  outline: 2px solid #2563eb;
  outline-offset: -2px;
  background: #f8fafc;
}

.severity-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 0.375rem;
}

.alert-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.alert-name {
  display: flex;
  gap: 0.375rem;
  align-items: baseline;
  min-width: 0;
}

.alert-item-name {
  color: #64748b;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.alert-meta {
  font-size: 0.75rem;
  color: #475569;
}

.dropdown-item .badge {
  flex-shrink: 0;
  align-self: center;
}

.dropdown-footer {
  width: 100%;
  padding: 0.75rem 1rem;
  background: none;
  border: none;
  border-top: 1px solid #e2e8f0;
  text-align: left;
  cursor: pointer;
  font-family: inherit;
  font-size: 0.875rem;
  font-weight: 600;
  color: #2563eb;
  transition: background 0.15s ease;
}

.dropdown-footer:hover {
  background: #f8fafc;
}

.dropdown-footer:focus-visible {
  outline: 2px solid #2563eb;
  outline-offset: -2px;
  background: #f8fafc;
}
</style>
