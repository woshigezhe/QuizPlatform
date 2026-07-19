import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(ElementPlus)

// 注册所有 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 路由守卫：检查认证和管理员权限
router.beforeEach(async (to, from, next) => {
  const auth = useAuthStore()
  
  // 首次加载时获取用户状态
  if (auth.user === undefined) {
    await auth.fetchUser()
  }
  
  if (to.meta.requiresAuth && !auth.isLoggedIn) {
    next('/login')
  } else if (to.meta.requiresAdmin && !auth.isAdmin) {
    next('/')
  } else {
    next()
  }
})

app.mount('#app')