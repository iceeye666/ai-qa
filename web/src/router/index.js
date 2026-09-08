import { createRouter, createWebHashHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  { path: '/login', component: () => import('../views/LoginView.vue'), meta: { public: true } },
  {
    path: '/',
    component: () => import('../views/LayoutView.vue'),
    children: [
      { path: '', component: () => import('../views/ChatView.vue') },
      { path: 'models', component: () => import('../views/ModelsView.vue'), meta: { admin: true } },
      { path: 'users', component: () => import('../views/UsersView.vue'), meta: { admin: true } }
    ]
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

// 路由守卫：未登录跳登录页；非管理员禁止进入管理页
router.beforeEach((to) => {
  const auth = useAuthStore()
  if (!to.meta.public && !auth.isLogin) {
    return { path: '/login' }
  }
  if (to.meta.admin && !auth.isAdmin) {
    return { path: '/' }
  }
  if (to.path === '/login' && auth.isLogin) {
    return { path: '/' }
  }
})

export default router
