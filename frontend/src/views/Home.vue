<template>
  <div>
    <div class="page-header">
      <h2><el-icon><Grid /></el-icon> 题库分类</h2>
      <p class="text-muted">选择分类开始学习，解锁题组逐步进阶</p>
    </div>
    <el-row :gutter="20" v-loading="loading">
      <el-col v-for="cat in categories" :key="cat.id" :xs="24" :sm="12" :md="8" style="margin-bottom: 20px">
        <el-card shadow="hover" class="cat-card">
          <template #header>
            <div class="cat-header">
              <span><el-icon><Folder /></el-icon> {{ cat.name }}</span>
            </div>
          </template>
          <div class="cat-stats">
            <el-tag size="small" type="info">题目: {{ cat.question_count }}</el-tag>
            <el-tag v-if="cat.group_count" size="small" type="info" style="margin-left: 6px">题组: {{ cat.group_count }}</el-tag>
          </div>
          <div v-if="auth.isLoggedIn && cat.progress && cat.group_count" class="cat-progress">
            <div class="progress-text">解锁进度 {{ cat.progress.unlocked_order }}/{{ cat.group_count }}</div>
            <el-progress 
              :percentage="cat.group_count ? Math.round(cat.progress.unlocked_order / cat.group_count * 100) : 0" 
              :stroke-width="6" 
              :show-text="false"
            />
          </div>
          <div class="cat-actions">
            <el-button v-if="cat.group_count" type="primary" @click="goRoadmap(cat.id)">
              <el-icon><MapLocation /></el-icon> 学习路线
            </el-button>
            <el-button v-else type="primary" @click="goQuiz(cat.id)" :disabled="!auth.isLoggedIn">
              <el-icon><VideoPlay /></el-icon> 随机答题
            </el-button>
          </div>
        </el-card>
      </el-col>
      <el-empty v-if="!loading && categories.length === 0" description="暂无分类" />
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useQuizStore } from '@/stores/quiz'
import { getCategories } from '@/api/quiz'

const router = useRouter()
const auth = useAuthStore()
const quiz = useQuizStore()
const categories = ref([])
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    const res = await getCategories()
    categories.value = res.data.categories
  } finally {
    loading.value = false
  }
})

async function goQuiz(catId) {
  await quiz.start(catId)
  router.push('/quiz')
}

function goRoadmap(catId) {
  router.push(`/roadmap/${catId}`)
}
</script>

<style scoped>
.page-header { margin-bottom: 1.5rem; }
.page-header h2 { display: flex; align-items: center; gap: 0.5rem; font-weight: 700; }
.text-muted { color: #6c6c6c; }
.cat-card { border-radius: 1rem; }
.cat-header { font-weight: 600; font-size: 1.05rem; }
.cat-stats { margin-bottom: 10px; }
.cat-progress { margin: 12px 0; }
.progress-text { font-size: 0.8rem; color: #6c6c6c; margin-bottom: 4px; }
.cat-actions { margin-top: 12px; }
</style>