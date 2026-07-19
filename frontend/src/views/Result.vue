<template>
  <div v-loading="loading">
    <div v-if="quiz.result" class="result-page">
      <el-alert v-if="quiz.groupMode && allCorrect !== undefined" :title="allCorrect ? '🎉 恭喜！题组全部正确！下一题组已解锁！' : '❌ 题组未通过，请复习后重新挑战'" :type="allCorrect ? 'success' : 'warning'" :closable="false" style="margin-bottom: 20px" />

      <el-card shadow="never" style="margin-bottom: 20px; text-align: center;">
        <el-row :gutter="20">
          <el-col :span="8"><div class="stat-value">{{ quiz.result.record.score }}</div><div class="stat-label">得分</div></el-col>
          <el-col :span="8"><div class="stat-value">{{ quiz.result.record.correct_count }}/{{ quiz.result.record.total_questions }}</div><div class="stat-label">正确/总题数</div></el-col>
          <el-col :span="8"><div class="stat-value">{{ quiz.result.record.minutes }}分{{ quiz.result.record.seconds_remainder }}秒</div><div class="stat-label">用时</div></el-col>
        </el-row>
        <div v-if="quiz.result.record.correct_count === quiz.result.record.total_questions" class="celebrate">🎉 恭喜全对！ 🎉</div>
        <div style="margin-top: 16px; display: flex; gap: 10px; justify-content: center;">
          <el-button type="primary" @click="$router.push('/')">返回首页</el-button>
          <el-button @click="$router.push('/history')">历史记录</el-button>
        </div>
      </el-card>

      <el-card shadow="never">
        <h4>题目详情</h4>
        <el-collapse>
          <el-collapse-item v-for="d in quiz.result.details" :key="d.id" :title="d.question.content.substring(0, 80)">
            <template #title>
              <el-icon :color="d.is_correct ? '#67c23a' : '#f56c6c'" style="margin-right:8px">
                <Check v-if="d.is_correct" /><Close v-else />
              </el-icon>
              {{ d.question.content.substring(0, 80) }}
            </template>
            <p><strong>你的答案：</strong>{{ d.user_answer || '(未答)' }} <el-tag :type="d.is_correct ? 'success' : 'danger'" size="small">{{ d.is_correct ? '正确' : '错误' }}</el-tag></p>
            <p><strong>正确答案：</strong>{{ d.question.answer }}</p>
            <p v-if="d.question.analysis"><strong>解析：</strong>{{ d.question.analysis }}</p>
          </el-collapse-item>
        </el-collapse>
      </el-card>
    </div>
    <el-empty v-else description="加载结果中..." />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useQuizStore } from '@/stores/quiz'

const route = useRoute()
const quiz = useQuizStore()
const loading = ref(false)
const allCorrect = ref(undefined)

onMounted(async () => {
  const recId = route.params.recordId
  if (recId) {
    loading.value = true
    await quiz.fetchResult(parseInt(recId))
    loading.value = false
  }
  allCorrect.value = quiz.result?.all_correct
})
</script>

<style scoped>
.stat-value { font-size: 2rem; font-weight: 700; }
.stat-label { font-size: 0.85rem; color: #6c6c6c; }
.celebrate { font-size: 1.5rem; color: #f59e0b; animation: celeb 1s ease-in-out 3; margin-top: 10px; }
@keyframes celeb {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.15); }
}
</style>