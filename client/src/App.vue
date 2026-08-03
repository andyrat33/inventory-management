<template>
  <div class="app">
    <aside class="sidebar" :class="{ collapsed: isSidebarCollapsed }">
      <div class="sidebar-logo">
        <template v-if="!isSidebarCollapsed">
          <h1>{{ t('nav.companyName') }}</h1>
          <span class="subtitle">{{ t('nav.subtitle') }}</span>
        </template>
        <button
          class="sidebar-toggle"
          type="button"
          @click="toggleSidebar"
          :aria-label="isSidebarCollapsed ? t('nav.expandSidebar') : t('nav.collapseSidebar')"
          :data-tooltip="isSidebarCollapsed ? t('nav.expandSidebar') : t('nav.collapseSidebar')"
        >
          <svg class="toggle-icon" :class="{ flipped: isSidebarCollapsed }" width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M10 4L6 8L10 12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>

      <nav class="sidebar-nav">
        <router-link to="/" class="sidebar-nav-item" :class="{ active: $route.path === '/' }" :data-tooltip="t('nav.overview')">
          <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5">
            <rect x="2.5" y="2.5" width="6" height="6" rx="1"/>
            <rect x="11.5" y="2.5" width="6" height="6" rx="1"/>
            <rect x="2.5" y="11.5" width="6" height="6" rx="1"/>
            <rect x="11.5" y="11.5" width="6" height="6" rx="1"/>
          </svg>
          <span v-if="!isSidebarCollapsed">{{ t('nav.overview') }}</span>
        </router-link>

        <router-link to="/inventory" class="sidebar-nav-item" :class="{ active: $route.path === '/inventory' }" :data-tooltip="t('nav.inventory')">
          <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round" stroke-linecap="round">
            <path d="M10 2.5L17.5 6.25V13.75L10 17.5L2.5 13.75V6.25L10 2.5Z"/>
            <path d="M2.5 6.25L10 10L17.5 6.25"/>
            <path d="M10 10V17.5"/>
          </svg>
          <span v-if="!isSidebarCollapsed">{{ t('nav.inventory') }}</span>
        </router-link>

        <router-link to="/orders" class="sidebar-nav-item" :class="{ active: $route.path === '/orders' }" :data-tooltip="t('nav.orders')">
          <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round" stroke-linecap="round">
            <rect x="4" y="3.5" width="12" height="14" rx="1.5"/>
            <path d="M7.5 2.5H12.5V4.5H7.5V2.5Z"/>
            <path d="M7 8.5H13"/>
            <path d="M7 11.5H13"/>
            <path d="M7 14.5H10.5"/>
          </svg>
          <span v-if="!isSidebarCollapsed">{{ t('nav.orders') }}</span>
        </router-link>

        <router-link to="/spending" class="sidebar-nav-item" :class="{ active: $route.path === '/spending' }" :data-tooltip="t('nav.finance')">
          <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round">
            <path d="M3 17V8"/>
            <path d="M8.5 17V3"/>
            <path d="M14 17V10.5"/>
            <path d="M2.5 17H17.5"/>
          </svg>
          <span v-if="!isSidebarCollapsed">{{ t('nav.finance') }}</span>
        </router-link>

        <router-link to="/demand" class="sidebar-nav-item" :class="{ active: $route.path === '/demand' }" :data-tooltip="t('nav.demandForecast')">
          <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M2.5 14.5L7.5 9.5L11 13L17.5 5.5"/>
            <path d="M13 5.5H17.5V10"/>
          </svg>
          <span v-if="!isSidebarCollapsed">{{ t('nav.demandForecast') }}</span>
        </router-link>

        <router-link to="/restocking" class="sidebar-nav-item" :class="{ active: $route.path === '/restocking' }" :data-tooltip="t('nav.restocking')">
          <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round" stroke-linecap="round">
            <path d="M10 2.5L17.5 6.25V13.75L10 17.5L2.5 13.75V6.25L10 2.5Z"/>
            <path d="M10 10.5V15"/>
            <path d="M7.75 12.75H12.25"/>
          </svg>
          <span v-if="!isSidebarCollapsed">{{ t('nav.restocking') }}</span>
        </router-link>

        <router-link to="/reports" class="sidebar-nav-item" :class="{ active: $route.path === '/reports' }" data-tooltip="Reports">
          <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round" stroke-linecap="round">
            <path d="M5.5 2.5H11.5L15 6V16C15 16.5523 14.5523 17 14 17H5.5C4.94772 17 4.5 16.5523 4.5 16V3.5C4.5 2.94772 4.94772 2.5 5.5 2.5Z"/>
            <path d="M11.5 2.5V6H15"/>
            <path d="M7 10H12"/>
            <path d="M7 12.5H12"/>
          </svg>
          <span v-if="!isSidebarCollapsed">Reports</span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <LanguageSwitcher :collapsed="isSidebarCollapsed" />
        <ProfileMenu
          :collapsed="isSidebarCollapsed"
          @show-profile-details="showProfileDetails = true"
          @show-tasks="showTasks = true"
        />
      </div>
    </aside>

    <div class="app-main">
      <FilterBar />
      <main class="main-content">
        <router-view />
      </main>
    </div>

    <ProfileDetailsModal
      :is-open="showProfileDetails"
      @close="showProfileDetails = false"
    />

    <TasksModal
      :is-open="showTasks"
      :tasks="tasks"
      @close="showTasks = false"
      @add-task="addTask"
      @delete-task="deleteTask"
      @toggle-task="toggleTask"
    />
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { api } from './api'
import { useAuth } from './composables/useAuth'
import { useI18n } from './composables/useI18n'
import FilterBar from './components/FilterBar.vue'
import ProfileMenu from './components/ProfileMenu.vue'
import ProfileDetailsModal from './components/ProfileDetailsModal.vue'
import TasksModal from './components/TasksModal.vue'
import LanguageSwitcher from './components/LanguageSwitcher.vue'

export default {
  name: 'App',
  components: {
    FilterBar,
    ProfileMenu,
    ProfileDetailsModal,
    TasksModal,
    LanguageSwitcher
  },
  setup() {
    const { currentUser } = useAuth()
    const { t } = useI18n()
    const showProfileDetails = ref(false)
    const showTasks = ref(false)
    const apiTasks = ref([])

    const STORAGE_KEY = 'sidebar-collapsed'
    const COLLAPSE_QUERY = '(max-width: 1024px)'

    const storedPref = localStorage.getItem(STORAGE_KEY)
    const userCollapsed = ref(storedPref === null ? null : storedPref === 'true')

    const mql = window.matchMedia(COLLAPSE_QUERY)
    const isBelowBreakpoint = ref(mql.matches)
    const handleBreakpointChange = (e) => { isBelowBreakpoint.value = e.matches }

    const isSidebarCollapsed = computed(() =>
      userCollapsed.value !== null ? userCollapsed.value : isBelowBreakpoint.value
    )

    const toggleSidebar = () => {
      const next = !isSidebarCollapsed.value
      userCollapsed.value = next
      localStorage.setItem(STORAGE_KEY, String(next))
    }

    // Merge mock tasks from currentUser with API tasks
    const tasks = computed(() => {
      return [...currentUser.value.tasks, ...apiTasks.value]
    })

    const loadTasks = async () => {
      try {
        apiTasks.value = await api.getTasks()
      } catch (err) {
        console.error('Failed to load tasks:', err)
      }
    }

    const addTask = async (taskData) => {
      try {
        const newTask = await api.createTask(taskData)
        // Add new task to the beginning of the array
        apiTasks.value.unshift(newTask)
      } catch (err) {
        console.error('Failed to add task:', err)
      }
    }

    const deleteTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const isMockTask = currentUser.value.tasks.some(t => t.id === taskId)

        if (isMockTask) {
          // Remove from mock tasks
          const index = currentUser.value.tasks.findIndex(t => t.id === taskId)
          if (index !== -1) {
            currentUser.value.tasks.splice(index, 1)
          }
        } else {
          // Remove from API tasks
          await api.deleteTask(taskId)
          apiTasks.value = apiTasks.value.filter(t => t.id !== taskId)
        }
      } catch (err) {
        console.error('Failed to delete task:', err)
      }
    }

    const toggleTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const mockTask = currentUser.value.tasks.find(t => t.id === taskId)

        if (mockTask) {
          // Toggle mock task status
          mockTask.status = mockTask.status === 'pending' ? 'completed' : 'pending'
        } else {
          // Toggle API task
          const updatedTask = await api.toggleTask(taskId)
          const index = apiTasks.value.findIndex(t => t.id === taskId)
          if (index !== -1) {
            apiTasks.value[index] = updatedTask
          }
        }
      } catch (err) {
        console.error('Failed to toggle task:', err)
      }
    }

    onMounted(() => {
      loadTasks()
      mql.addEventListener('change', handleBreakpointChange)
    })

    onUnmounted(() => {
      mql.removeEventListener('change', handleBreakpointChange)
    })

    return {
      t,
      showProfileDetails,
      showTasks,
      tasks,
      addTask,
      deleteTask,
      toggleTask,
      isSidebarCollapsed,
      toggleSidebar
    }
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

:root {
  --sidebar-width: 260px;
  --sidebar-collapsed-width: 72px;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background: #f8fafc;
  color: #1e293b;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.app {
  display: flex;
  flex-direction: row;
  min-height: 100vh;
}

.sidebar {
  width: var(--sidebar-width);
  flex-shrink: 0;
  position: sticky;
  top: 0;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #ffffff;
  border-right: 1px solid #e2e8f0;
  transition: width 0.2s ease;
}

.sidebar.collapsed {
  width: var(--sidebar-collapsed-width);
}

.sidebar-logo {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 1.5rem 1.25rem;
  border-bottom: 1px solid #e2e8f0;
}

.sidebar.collapsed .sidebar-logo {
  justify-content: center;
  padding: 1.5rem 0.75rem;
}

.sidebar-logo h1 {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.subtitle {
  font-size: 0.813rem;
  color: #64748b;
  font-weight: 400;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 1rem 0.75rem;
  overflow-y: auto;
}

.sidebar-nav-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem 0.75rem;
  color: #64748b;
  text-decoration: none;
  font-weight: 500;
  font-size: 0.938rem;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.sidebar-nav-item:hover {
  color: #0f172a;
  background: #f1f5f9;
}

.sidebar-nav-item.active {
  color: #2563eb;
  background: #eff6ff;
}

.nav-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.sidebar-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  flex-shrink: 0;
  background: none;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s ease;
}

.sidebar-toggle:hover {
  background: #f1f5f9;
  color: #0f172a;
}

.toggle-icon {
  transition: transform 0.2s ease;
}

.toggle-icon.flipped {
  transform: rotate(180deg);
}

.sidebar.collapsed .sidebar-nav-item {
  justify-content: center;
  padding: 0.625rem;
  gap: 0;
}

.sidebar.collapsed [data-tooltip] {
  position: relative;
}

.sidebar.collapsed [data-tooltip]::after {
  content: attr(data-tooltip);
  position: absolute;
  left: calc(100% + 0.75rem);
  top: 50%;
  transform: translateY(-50%);
  background: #0f172a;
  color: #fff;
  padding: 0.375rem 0.625rem;
  border-radius: 6px;
  font-size: 0.813rem;
  font-weight: 500;
  white-space: nowrap;
  opacity: 0;
  visibility: hidden;
  pointer-events: none;
  transition: opacity 0.15s ease, visibility 0.15s ease;
  z-index: 1100;
}

.sidebar.collapsed [data-tooltip]:hover::after {
  opacity: 1;
  visibility: visible;
}

.sidebar-footer {
  margin-top: auto;
  padding: 1rem 0.75rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
}

.app-main {
  flex: 1;
  min-width: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
  max-width: 1600px;
  width: 100%;
  margin: 0 auto;
  padding: 1.5rem 2rem;
}

.page-header {
  margin-bottom: 1.5rem;
}

.page-header h2 {
  font-size: 1.875rem;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 0.375rem;
  letter-spacing: -0.025em;
}

.page-header p {
  color: #64748b;
  font-size: 0.938rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.25rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  background: white;
  padding: 1.25rem;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  transition: all 0.2s ease;
}

.stat-card:hover {
  border-color: #cbd5e1;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
}

.stat-label {
  color: #64748b;
  font-size: 0.875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 0.625rem;
}

.stat-value {
  font-size: 2.25rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.stat-card.warning .stat-value {
  color: #ea580c;
}

.stat-card.success .stat-value {
  color: #059669;
}

.stat-card.danger .stat-value {
  color: #dc2626;
}

.stat-card.info .stat-value {
  color: #2563eb;
}

.card {
  background: white;
  border-radius: 10px;
  padding: 1.25rem;
  border: 1px solid #e2e8f0;
  margin-bottom: 1.25rem;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.875rem;
  border-bottom: 1px solid #e2e8f0;
}

.card-title {
  font-size: 1.125rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.table-container {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
  border-bottom: 1px solid #e2e8f0;
}

th {
  text-align: left;
  padding: 0.5rem 0.75rem;
  font-weight: 600;
  color: #475569;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

td {
  padding: 0.5rem 0.75rem;
  border-top: 1px solid #f1f5f9;
  color: #334155;
  font-size: 0.875rem;
}

tbody tr {
  transition: background-color 0.15s ease;
}

tbody tr:hover {
  background: #f8fafc;
}

.badge {
  display: inline-block;
  padding: 0.313rem 0.75rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.badge.success {
  background: #d1fae5;
  color: #065f46;
}

.badge.warning {
  background: #fed7aa;
  color: #92400e;
}

.badge.danger {
  background: #fecaca;
  color: #991b1b;
}

.badge.info {
  background: #dbeafe;
  color: #1e40af;
}

.badge.increasing {
  background: #d1fae5;
  color: #065f46;
}

.badge.decreasing {
  background: #fecaca;
  color: #991b1b;
}

.badge.stable {
  background: #e0e7ff;
  color: #3730a3;
}

.badge.high {
  background: #fecaca;
  color: #991b1b;
}

.badge.medium {
  background: #fed7aa;
  color: #92400e;
}

.badge.low {
  background: #dbeafe;
  color: #1e40af;
}

.loading {
  text-align: center;
  padding: 3rem;
  color: #64748b;
  font-size: 0.938rem;
}

.error {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
  padding: 1rem;
  border-radius: 8px;
  margin: 1rem 0;
  font-size: 0.938rem;
}
</style>
