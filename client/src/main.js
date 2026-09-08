import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import Login from './views/Login.vue'
import Dashboard from './views/Dashboard.vue'
import Inventory from './views/Inventory.vue'
import Orders from './views/Orders.vue'
import Demand from './views/Demand.vue'
import Spending from './views/Spending.vue'
import Reports from './views/Reports.vue'
import Restocking from './views/Restocking.vue'
import { useAuth } from './composables/useAuth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: Login, meta: { public: true } },
    { path: '/', component: Dashboard },
    { path: '/inventory', component: Inventory },
    { path: '/orders', component: Orders },
    { path: '/demand', component: Demand },
    { path: '/restocking', component: Restocking },
    { path: '/spending', component: Spending },
    { path: '/reports', component: Reports }
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
