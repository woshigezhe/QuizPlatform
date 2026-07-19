<template>
  <div class="form-page">
    <h2 class="text-center mb-4">注册</h2>
    <el-form ref="formRef" :model="form" :rules="rules" label-width="80px" @submit.prevent="handleRegister">
      <el-form-item label="用户名" prop="username">
        <el-input v-model="form.username" placeholder="3-20位字母/数字/下划线/中文" />
      </el-form-item>
      <el-form-item label="邮箱" prop="email">
        <el-input v-model="form.email" placeholder="请输入邮箱" />
      </el-form-item>
      <el-form-item label="密码" prop="password">
        <el-input v-model="form.password" type="password" placeholder="至少6位" show-password />
      </el-form-item>
      <el-form-item label="确认密码" prop="password2">
        <el-input v-model="form.password2" type="password" placeholder="再次输入密码" show-password @keyup.enter="handleRegister" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleRegister" :loading="auth.loading" style="width:100%">注册</el-button>
      </el-form-item>
    </el-form>
    <div class="text-center">
      <router-link to="/login">已有账号？立即登录</router-link>
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

const form = reactive({ username: '', email: '', password: '', password2: '' })
const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '长度3-20个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' }
  ],
  password2: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: (_, v, cb) => v === form.password ? cb() : cb(new Error('两次密码不一致')), trigger: 'blur' }
  ]
}

async function handleRegister() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  const ok = await auth.register(form.username, form.email, form.password)
  if (ok) router.push('/login')
}
</script>

<style scoped>
.form-page { max-width: 400px; margin: 0 auto; }
</style>