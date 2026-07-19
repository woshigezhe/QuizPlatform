<template>
  <div>
    <h2 class="mb-4"><el-icon><Clock /></el-icon> 答题历史</h2>
    <el-table :data="records" v-loading="loading" stripe empty-text="暂无答题记录" style="border-radius: 0.75rem; overflow: hidden;">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="category_name" label="分类" />
      <el-table-column label="得分/总题" width="120">
        <template #default="{ row }">{{ row.score }} / {{ row.total_questions }}</template>
      </el-table-column>
      <el-table-column label="正确" width="80">
        <template #default="{ row }">{{ row.correct_count }}</template>
      </el-table-column>
      <el-table-column label="时间" width="180">
        <template #default="{ row }">{{ row.start_time?.substring(0, 19) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="100">
        <template #default="{ row }">
          <el-button size="small" type="primary" @click="$router.push(`/result/${row.id}`)">查看</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getHistory } from '@/api/quiz'

const records = ref([])
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    const res = await getHistory()
    records.value = res.data.records
  } finally {
    loading.value = false
  }
})
</script>