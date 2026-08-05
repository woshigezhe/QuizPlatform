<template>
  <div>
    <h2 class="mb-4"><el-icon><Setting /></el-icon> 管理后台</h2>
    <el-row :gutter="20">
      <el-col :xs="24" :sm="6" v-for="item in menuItems" :key="item.path" class="mb-3">
        <el-card shadow="hover" @click="$router.push(item.path)" class="admin-card" :style="{ cursor: 'pointer' }">
          <div class="text-center">
            <el-icon size="32"><component :is="item.icon" /></el-icon>
            <h5 class="mt-2">{{ item.label }}</h5>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { Grid, Collection, Document, User } from '@element-plus/icons-vue'

const menuItems = [
  { path: '/admin/categories', label: '分类管理', icon: Grid },
  { path: '/admin/groups', label: '分组管理', icon: Collection },
  { path: '/admin/questions', label: '题目管理', icon: Document },
  { path: '/admin/users', label: '用户管理', icon: User },
]
</script>

<style scoped>
.admin-card { border-radius: 1rem; transition: all 0.3s; }
.admin-card:hover { transform: translateY(-4px); box-shadow: 0 8px 20px rgba(0,0,0,0.1); }
</style>