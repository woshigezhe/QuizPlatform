import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'Home', component: () => import('@/views/Home.vue') },
  { path: '/login', name: 'Login', component: () => import('@/views/Login.vue') },
  { path: '/register', name: 'Register', component: () => import('@/views/Register.vue') },
  { path: '/quiz', name: 'Quiz', component: () => import('@/views/Quiz.vue'), meta: { requiresAuth: true } },
  { path: '/result/:recordId', name: 'Result', component: () => import('@/views/Result.vue'), meta: { requiresAuth: true } },
  { path: '/roadmap/:categoryId', name: 'Roadmap', component: () => import('@/views/Roadmap.vue'), meta: { requiresAuth: true } },
  { path: '/study/:groupId', name: 'Study', component: () => import('@/views/Study.vue'), meta: { requiresAuth: true } },
  { path: '/history', name: 'History', component: () => import('@/views/History.vue'), meta: { requiresAuth: true } },
  { path: '/leaderboard', name: 'Leaderboard', component: () => import('@/views/Leaderboard.vue') },
  { path: '/admin', name: 'AdminDashboard', component: () => import('@/views/admin/Dashboard.vue'), meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/admin/categories', name: 'AdminCategories', component: () => import('@/views/admin/Categories.vue'), meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/admin/groups', name: 'AdminGroups', component: () => import('@/views/admin/Groups.vue'), meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/admin/questions', name: 'AdminQuestions', component: () => import('@/views/admin/Questions.vue'), meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/admin/users', name: 'AdminUsers', component: () => import('@/views/admin/Users.vue'), meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/:pathMatch(.*)*', redirect: '/' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router