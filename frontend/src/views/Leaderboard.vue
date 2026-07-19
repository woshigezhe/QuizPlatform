<template>
  <div>
    <h2 class="mb-4"><el-icon><Trophy /></el-icon> 排行榜</h2>
    <el-table :data="rankedUsers" v-loading="loading" stripe empty-text="暂无数据" style="border-radius: 0.75rem; overflow: hidden">
      <el-table-column label="排名" width="80">
        <template #default="{ row }">
          <el-tag v-if="row.rank <= 3" :type="['', 'danger', 'warning', 'primary'][row.rank]" size="small">{{ row.rank }}</el-tag>
          <span v-else>{{ row.rank }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="username" label="用户名" />
      <el-table-column prop="total_score" label="总分" sortable />
      <el-table-column prop="total_correct" label="正确数" />
      <el-table-column prop="total_questions" label="总题数" />
      <el-table-column label="正确率" sortable :sort-method="(a,b)=>a.accuracy - b.accuracy">
        <template #default="{ row }">{{ row.accuracy }}%</template>
      </el-table-column>
      <el-table-column prop="total_records" label="答题次数" />
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getLeaderboard } from '@/api/quiz'

const rankedUsers = ref([])
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    const res = await getLeaderboard()
    rankedUsers.value = res.data.ranked_users
  } finally {
    loading.value = false
  }
})
</script>