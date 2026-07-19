<template>
  <div class="form-page">
    <h2 class="text-center mb-4">登录</h2>
    <el-form ref="formRef" :model="form" :rules="rules" label-width="80px" @submit.prevent="handleLogin">
      <el-form-item label="用户名" prop="username">
        <el-input v-model="form.username" placeholder="请输入用户名" />
      </el-form-item>
      <el-form-item label="密码" prop="password">
        <el-input v-model="form.password" type="password" placeholder="请输入密码" show-password @keyup.enter="handleLogin" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleLogin" :loading="auth.loading" style="width:100%">登录</el-button>
      </el-form-item>
    </el-form>
    <div class="text-center">
      <router-link to="/register">还没有账号？立即注册</router-link>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()
const formRef = ref(null)

const form = reactive({ username: '', password: '' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

async function handleLogin() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  const ok = await auth.login(form.username, form.password)
  if (ok) router.push('/')
}
</script>

<style scoped>
.form-page { max-width: 400px; margin: 0 auto; }
</style>