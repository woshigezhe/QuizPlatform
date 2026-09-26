<template>
  <div>
    <h3 class="mb-3">导出记录</h3>
    <el-card shadow="never">
      <el-form label-width="90px" style="max-width:520px">
        <el-form-item label="分类">
          <el-select v-model="filters.category_id" clearable placeholder="全部" style="width:100%">
            <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="用户名">
          <el-input v-model="filters.username" placeholder="模糊匹配，可留空" />
        </el-form-item>
        <el-form-item label="开始日期">
          <el-date-picker v-model="filters.start_date" type="date" value-format="YYYY-MM-DD" placeholder="不限" style="width:100%" />
        </el-form-item>
        <el-form-item label="结束日期">
          <el-date-picker v-model="filters.end_date" type="date" value-format="YYYY-MM-DD" placeholder="不限" style="width:100%" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="doExport">导出 Excel</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { adminAPI } from '@/api/admin'

const categories = ref([])
const loading = ref(false)
const filters = reactive({ category_id: null, username: '', start_date: '', end_date: '' })

onMounted(async () => {
  const r = await adminAPI.getCategories()
  categories.value = r.data.categories
})

async function doExport() {
  loading.value = true
  try {
    const params = {}
    Object.entries(filters).forEach(([k, v]) => { if (v) params[k] = v })
    const blob = await adminAPI.exportData(params)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `答题记录_${new Date().toISOString().slice(0, 10)}.xlsx`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    ElMessage.success('导出已开始下载')
  } finally {
    loading.value = false
  }
}
</script>
