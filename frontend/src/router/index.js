import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import LoginView from '../views/LoginView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { public: true },
    },
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/events',
      name: 'events',
      component: () => import('../views/EventsView.vue'),
    },
    {
      path: '/reports',
      name: 'reports',
      component: () => import('../views/ReportsView.vue'),
    },
    {
      path: '/ml',
      name: 'ml',
      component: () => import('../views/MLView.vue'),
    },
    {
      path: '/map',
      name: 'map',
      component: () => import('../views/GeoMapView.vue'),
    },
  ],
})

// Guard de autenticación
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('vigia_token')

  if (to.meta.public) {
    if (token && to.name === 'login') {
      next({ name: 'home' })
    } else {
      next()
    }
  } else if (!token) {
    next({ name: 'login' })
  } else {
    next()
  }
})

export default router
