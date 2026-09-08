import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import Login from './views/Login.vue'
import { useAuth } from './composables/useAuth'

// Lazy-load the app views so the initial bundle carries only the shell + login;
// each view (and its modals) is fetched on first navigation.
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: Login, meta: { public: true } },
    { path: '/', component: () => import('./views/Dashboard.vue') },
    { path: '/inventory', component: () => import('./views/Inventory.vue') },
    { path: '/orders', component: () => import('./views/Orders.vue') },
    { path: '/demand', component: () => import('./views/Demand.vue') },
    { path: '/restocking', component: () => import('./views/Restocking.vue') },
    { path: '/spending', component: () => import('./views/Spending.vue') },
    { path: '/reports', component: () => import('./views/Reports.vue') }
  ]
})

// Demo auth gate: no real backend auth (see README). Unauthenticated visits are
// bounced to /login; an authenticated visit to /login goes home.
router.beforeEach((to) => {
  const { isAuthenticated } = useAuth()
  if (!to.meta.public && !isAuthenticated.value) {
    return { path: '/login', query: to.fullPath === '/' ? {} : { redirect: to.fullPath } }
  }
  if (to.path === '/login' && isAuthenticated.value) {
    return { path: '/' }
  }
})

const app = createApp(App)
app.use(router)
app.mount('#app')
