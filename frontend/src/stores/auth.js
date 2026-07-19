import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getMe, login as apiLogin, register as apiRegister, logout as apiLogout } from '@/api/auth'
import { ElMessage } from 'element-plus'

export const useAuthStore = defineStore('auth', () => {
const user = ref(undefined)
  const loading = ref(false)

  const isLoggedIn = computed(() => !!user.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  async function fetchUser() {
    try {
      const res = await getMe()
      user.value = res.data?.user || null
    } catch {
      user.value = null
    }
  }

  async function login(username, password, remember = false) {
    loading.value = true
    try {
      const res = await apiLogin(username, password, remember)
      user.value = res.data.user
      ElMessage.success('登录成功')
      return true
    } catch {
      return false
    } finally {
      loading.value = false
    }
  }

  async function register(username, email, password) {
    loading.value = true
    try {
      await apiRegister(username, email, password)
      ElMessage.success('注册成功，请登录')
      return true
    } catch {
      return false
    } finally {
      loading.value = false
    }
  }

  async function logout() {
    try {
      await apiLogout()
    } catch {
      // ignore
    }
    user.value = null
    ElMessage.success('已退出登录')
  }

  return { user, loading, isLoggedIn, isAdmin, fetchUser, login, register, logout }
})