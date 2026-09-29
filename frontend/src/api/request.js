import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

const request = axios.create({
  baseURL: '/api',
  timeout: 30000,
  withCredentials: true
})

// 响应拦截器
request.interceptors.response.use(
  (response) => {
    const data = response.data
    if (data.success === false) {
      ElMessage.error(data.message || '请求失败')
      return Promise.reject(new Error(data.message))
    }
    return data
  },
  (error) => {
    if (error.response) {
      const status = error.response.status
      const serverMsg = error.response.data?.message
      const url = error.config?.url || ''
      if (status === 401) {
        ElMessage.error(serverMsg || '请先登录')
        // 登录/注册接口自身报 401 属正常（凭证错误），不跳转
        const isAuthEndpoint = url.includes('/auth/login') || url.includes('/auth/register')
        if (!isAuthEndpoint && router.currentRoute.value.path !== '/login') {
          router.push('/login')
        }
      } else if (status === 403) {
        ElMessage.error(serverMsg || '权限不足')
      } else if (status === 404) {
        ElMessage.error(serverMsg || '资源不存在')
      } else {
        ElMessage.error(serverMsg || '服务器错误')
      }
    } else {
      ElMessage.error('网络错误，请检查连接')
    }
    return Promise.reject(error)
  }
)

export default request