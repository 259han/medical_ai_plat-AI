import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '@/views/Dashboard.vue'
import MedicalQA from '@/views/MedicalQA.vue'
import HeartDisease from '@/views/HeartDisease.vue'
import Tumor from '@/views/Tumor.vue'
import Diabetes from '@/views/Diabetes.vue'
import ChestXray from '@/views/ChestXray.vue'
import Profile from '@/views/Profile.vue'
import History from '@/views/History.vue'
import Login from '@/views/Login.vue'
import Register from '@/views/Register.vue'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard,
    meta: { requiresAuth: true }
  },
  {
    path: '/medical-qa',
    name: 'MedicalQA',
    component: MedicalQA,
    meta: { requiresAuth: true }
  },
  {
    path: '/heart-disease',
    name: 'HeartDisease',
    component: HeartDisease,
    meta: { requiresAuth: true }
  },
  {
    path: '/tumor',
    name: 'Tumor',
    component: Tumor,
    meta: { requiresAuth: true }
  },
  {
    path: '/diabetes',
    name: 'Diabetes',
    component: Diabetes,
    meta: { requiresAuth: true }
  },
  {
    path: '/chest-xray',
    name: 'ChestXray',
    component: ChestXray,
    meta: { requiresAuth: true }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: Profile,
    meta: { requiresAuth: true }
  },
  {
    path: '/history',
    name: 'History',
    component: History,
    meta: { requiresAuth: true }
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresAuth: false }
  },
  {
    path: '/register',
    name: 'Register',
    component: Register,
    meta: { requiresAuth: false }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else {
    next()
  }
})

export default router