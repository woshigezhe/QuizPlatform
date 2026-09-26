<template>
  <div>
    <h3 class="mb-3">用户管理</h3>
    <el-table :data="users" v-loading="loading" stripe style="border-radius: 0.75rem; overflow: hidden">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="username" label="用户名" />
      <el-table-column prop="email" label="邮箱" />
      <el-table-column label="角色" width="80">
        <template #default="{ row }">
          <el-tag :type="row.role === 'admin' ? 'danger' : 'info'" size="small">{{ row.role }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.status ? 'success' : 'danger'" size="small">{{ row.status ? '正常' : '禁用' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="record_count" label="答题次数" width="100" />
      <el-table-column label="操作" width="250">
        <template #default="{ row }">
          <el-button size="small" :type="row.status ? 'warning' : 'success'" @click="handleToggle(row.id)" v-if="row.role !== 'admin'">
            {{ row.status ? '禁用' : '启用' }}
          </el-button>
          <el-popconfirm v-if="row.role !== 'admin'" title="确定清除该用户的所有答题历史？" @confirm="handleClear(row.id)">
            <template #reference>
              <el-button size="small" type="warning">清除历史</el-button>
            </template>
          </el-popconfirm>
          <el-popconfirm title="确定删除该用户及所有数据？此操作不可恢复！" @confirm="handleDelete(row.id)">
            <template #reference>
              <el-button size="small" type="danger" v-if="row.role !== 'admin'">删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { adminAPI } from '@/api/admin'

const users = ref([])
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try { const r = await adminAPI.getUsers(); users.value = r.data.users } finally { loading.value = false }
})

async function handleToggle(id) {
  await adminAPI.toggleUser(id)
  const r = await adminAPI.getUsers(); users.value = r.data.users
}

async function handleClear(id) {
  await adminAPI.clearUserHistory(id)
  const r = await adminAPI.getUsers(); users.value = r.data.users
}

async function handleDelete(id) {
  await adminAPI.deleteUser(id)
  const r = await adminAPI.getUsers(); users.value = r.data.users
}
</script>