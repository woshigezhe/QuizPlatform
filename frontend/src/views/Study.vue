<template>
  <div v-loading="loading" class="study-page">
    <div v-if="studyData">
      <div class="breadcrumb">
        <router-link to="/">首页</router-link> ›
        <router-link :to="`/roadmap/${studyData.group.category_id}`">{{ studyData.category?.name }}</router-link> ›
        <span>{{ studyData.group.name }}</span>
      </div>
      <h2 class="text-center mb-3">{{ studyData.group.name }}</h2>
      <p v-if="studyData.group.description" class="text-center text-muted">{{ studyData.group.description }}</p>
      <el-card v-if="studyData.group.study_content" shadow="never" class="study-card">
        <div class="study-content" v-html="studyData.group.study_content"></div>
      </el-card>
      <el-empty v-else description="该题组暂未添加学习资料" />
      <div class="text-center mt-3">
        <el-button @click="$router.push(`/roadmap/${studyData.group.category_id}`)">返回路线图</el-button>
        <el-button type="primary" @click="startQuiz">开始答题</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useQuizStore } from '@/stores/quiz'
import { getStudy } from '@/api/quiz'

const route = useRoute()
const router = useRouter()
const quiz = useQuizStore()
const studyData = ref(null)
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    const res = await getStudy(parseInt(route.params.groupId))
    studyData.value = res.data
  } finally {
    loading.value = false
  }
})

async function startQuiz() {
  await quiz.startGroup(studyData.value.group.category_id, parseInt(route.params.groupId))
  router.push('/quiz')
}
</script>

<style scoped>
.breadcrumb { margin-bottom: 16px; color: #6c6c6c; font-size: 0.9rem; }
.breadcrumb a { color: #4a4a4a; text-decoration: none; }
.study-card { border-radius: 1rem; margin: 1rem 0; }
.study-content { line-height: 1.8; }
.text-muted { color: #6c6c6c; }
</style>