<template>
  <div>
    <div class="d-flex justify-between align-center mb-3">
      <h3>分类管理</h3>
      <el-button type="primary" size="small" @click="showAddDialog"><el-icon><Plus /></el-icon> 新增</el-button>
    </div>
    <el-table :data="categories" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="question_count" label="题目数" width="100" />
      <el-table-column prop="group_count" label="题组数" width="100" />
      <el-table-column label="操作" width="100">
        <template #default="{ row }">
          <el-popconfirm title="确定删除此分类？" @confirm="handleDelete(row.id)">
            <template #reference>
              <el-button size="small" type="danger">删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" title="新增分类" width="400px">
      <el-form @submit.prevent="handleAdd">
        <el-form-item label="分类名称">
          <el-input v-model="newName" placeholder="请输入分类名称" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleAdd">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { adminAPI } from '@/api/admin'

const categories = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const newName = ref('')

onMounted(fetchCategories)

async function fetchCategories() {
  loading.value = true
  try { const r = await adminAPI.getCategories(); categories.value = r.data.categories } finally { loading.value = false }
}

function showAddDialog() { newName.value = ''; dialogVisible.value = true }

async function handleAdd() {
  if (!newName.value.trim()) return ElMessage.warning('请输入名称')
  await adminAPI.addCategory({ name: newName.value.trim() })
  dialogVisible.value = false
  fetchCategories()
}

async function handleDelete(id) {
  await adminAPI.deleteCategory(id)
  fetchCategories()
}
</script>

<style scoped>
.d-flex { display: flex; } .justify-between { justify-content: space-between; } .align-center { align-items: center; }
</style>