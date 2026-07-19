<template>
  <div>
    <div class="d-flex justify-between align-center mb-3">
      <h3>分组管理</h3>
      <el-button type="primary" size="small" @click="showAddDialog"><el-icon><Plus /></el-icon> 新增</el-button>
    </div>
    <el-table :data="groups" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="category_name" label="分类" width="100" />
      <el-table-column prop="unlock_order" label="解锁序号" width="100" />
      <el-table-column prop="question_count" label="题目数" width="80" />
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button size="small" @click="showEditDialog(row)">编辑</el-button>
          <el-popconfirm title="确定删除此分组？" @confirm="handleDelete(row.id)">
            <template #reference>
              <el-button size="small" type="danger">删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑分组' : '新增分组'" width="500px">
      <el-form label-width="80px">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="分类">
          <el-select v-model="form.category_id" placeholder="选择分类" style="width:100%">
            <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="排序"><el-input-number v-model="form.order" :min="0" /></el-form-item>
        <el-form-item label="解锁序号"><el-input-number v-model="form.unlock_order" :min="0" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" /></el-form-item>
        <el-form-item label="学习资料"><el-input v-model="form.study_content" type="textarea" :rows="4" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { adminAPI } from '@/api/admin'

const groups = ref([])
const categories = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const editingId = ref(null)

const defaultForm = () => ({ name: '', category_id: null, order: 0, unlock_order: 0, description: '', study_content: '' })
const form = reactive(defaultForm())

async function fetchData() {
  loading.value = true
  try {
    const [gr, cr] = await Promise.all([adminAPI.getGroups(), adminAPI.getCategories()])
    groups.value = gr.data.groups
    categories.value = cr.data.categories
  } finally { loading.value = false }
}

onMounted(fetchData)

function showAddDialog() {
  Object.assign(form, defaultForm())
  editingId.value = null
  dialogVisible.value = true
}

function showEditDialog(row) {
  Object.assign(form, row)
  editingId.value = row.id
  dialogVisible.value = true
}

async function handleSave() {
  if (!form.name.trim()) return ElMessage.warning('请输入名称')
  if (editingId.value) {
    await adminAPI.updateGroup(editingId.value, { ...form })
  } else {
    await adminAPI.addGroup({ ...form })
  }
  dialogVisible.value = false
  fetchData()
}

async function handleDelete(id) {
  await adminAPI.deleteGroup(id)
  fetchData()
}
</script>

<style scoped>
.d-flex { display: flex; } .justify-between { justify-content: space-between; } .align-center { align-items: center; }
</style>