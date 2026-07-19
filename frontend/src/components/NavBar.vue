<template>
  <nav class="nav-container">
    <div class="nav-inner">
      <router-link to="/" class="nav-brand">
        <el-icon><EditPen /></el-icon> 在线答题
      </router-link>
      <div class="nav-links">
        <template v-if="auth.isLoggedIn">
          <span class="nav-user">
            <el-icon><User /></el-icon> {{ auth.user?.username }}
          </span>
          <router-link v-if="auth.isAdmin" to="/admin" class="nav-link">管理后台</router-link>
          <router-link to="/leaderboard" class="nav-link">排行榜</router-link>
          <router-link to="/history" class="nav-link">历史记录</router-link>
          <a class="nav-link" @click="handleLogout">退出</a>
        </template>
        <template v-else>
          <router-link to="/login" class="nav-link">登录</router-link>
          <router-link to="/register" class="nav-link">注册</router-link>
        </template>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

async function handleLogout() {
  await auth.logout()
  router.push('/')
}
</script>

<style scoped>
.nav-container {
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  box-shadow: 0 2px 20px rgba(0, 0, 0, 0.06);
  border-bottom: 1px solid rgba(255, 255, 255, 0.5);
  position: sticky;
  top: 0;
  z-index: 100;
}
.nav-inner {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1.5rem;
}
.nav-brand {
  font-weight: 700;
  font-size: 1.1rem;
  color: #1a1a1a;
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}
.nav-brand:hover { color: #000; }
.nav-links {
  display: flex;
  align-items: center;
  gap: 1rem;
}
.nav-link, .nav-user {
  color: #4a4a4a;
  text-decoration: none;
  font-weight: 500;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 0.3rem;
  transition: all 0.25s;
  cursor: pointer;
}
.nav-link:hover { color: #000; transform: translateY(-2px); }
.nav-user {
  color: #1a1a1a;
  font-weight: 600;
}
</style>