<template>
  <div v-if="quiz.currentQuestion">
    <!-- 返回按钮 -->
    <el-button type="default" size="small" @click="goBack" style="margin-bottom: 15px">
      <el-icon><ArrowLeft /></el-icon> {{ quiz.groupMode ? '返回学习路线' : '返回首页' }}
    </el-button>

    <!-- 进度条 -->
    <div class="mb-3">
      <el-progress :percentage="quiz.progress" :stroke-width="6" />
    </div>

    <el-card shadow="never" class="question-card">
      <template #header>
        <div class="d-flex justify-between align-center">
          <div>
            <el-tag v-if="quiz.groupMode" effect="dark" type="info" style="margin-right:8px">
              {{ quiz.groupName }}
            </el-tag>
            <el-tag type="primary">{{ quiz.currentIndex + 1 }}/{{ quiz.totalQuestions }}</el-tag>
          </div>
          <el-tag size="small">{{ typeLabel }}</el-tag>
        </div>
      </template>

      <h4 class="question-content">{{ quiz.currentQuestion.content }}</h4>
      <div v-if="quiz.currentQuestion.image" class="text-center mb-3">
        <img :src="'/static/' + quiz.currentQuestion.image.replace('static/', '')" class="question-image" />
      </div>

      <!-- 单选题 -->
      <div v-if="quiz.currentQuestion.type === 'single'" class="options-list">
        <el-radio-group v-model="answer" class="w-100">
          <el-radio v-for="opt in quiz.currentQuestion.options" :key="opt" :value="opt[0]" :label="opt[0]" class="option-item">
            {{ opt }}
          </el-radio>
        </el-radio-group>
      </div>

      <!-- 多选题 -->
      <div v-if="quiz.currentQuestion.type === 'multiple'" class="options-list">
        <el-checkbox-group v-model="multiAnswer" class="w-100">
          <el-checkbox v-for="opt in quiz.currentQuestion.options" :key="opt" :value="opt[0]" :label="opt[0]" class="option-item">
            {{ opt }}
          </el-checkbox>
        </el-checkbox-group>
      </div>

      <!-- 判断题 -->
      <div v-if="quiz.currentQuestion.type === 'judge'" class="d-flex gap-3">
        <el-button :type="answer === '正确' ? 'success' : 'default'" size="large" class="judge-btn" @click="answer = '正确'">
          <el-icon><Check /></el-icon> 正确
        </el-button>
        <el-button :type="answer === '错误' ? 'danger' : 'default'" size="large" class="judge-btn" @click="answer = '错误'">
          <el-icon><Close /></el-icon> 错误
        </el-button>
      </div>

      <!-- 填空题 -->
      <div v-if="quiz.currentQuestion.type === 'fill'">
        <el-input v-model="answer" placeholder="请输入答案" size="large" />
      </div>

      <!-- 导航按钮 -->
      <div class="nav-buttons">
        <el-button @click="prevQuestion" :disabled="quiz.isFirst" size="large">
          <el-icon><ArrowLeft /></el-icon> 上一题
        </el-button>
        <div>
          <el-button v-if="!quiz.isLast" type="primary" @click="nextQuestion" size="large" :loading="quiz.loading">
            下一题 <el-icon><ArrowRight /></el-icon>
          </el-button>
          <el-button type="danger" @click="submitQuiz" size="large" :loading="quiz.submitting">
            <el-icon><Check /></el-icon> 交卷
          </el-button>
        </div>
      </div>
    </el-card>
  </div>

  <!-- 空状态 -->
  <el-empty v-else description="没有正在进行的答题" />
</template>

<script setup>
import { ref, watch, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useQuizStore } from '@/stores/quiz'

const router = useRouter()
const quiz = useQuizStore()
const answer = ref('')
const multiAnswer = ref([])

const typeLabel = computed(() => {
  const m = { single: '单选', multiple: '多选', judge: '判断', fill: '填空' }
  return m[quiz.currentQuestion?.type] || ''
})

onMounted(() => {
  if (quiz.savedAnswer) {
    if (quiz.currentQuestion?.type === 'multiple') {
      multiAnswer.value = Array.isArray(quiz.savedAnswer) ? [...quiz.savedAnswer] : []
    } else {
      answer.value = quiz.savedAnswer
    }
  }
})

watch(() => quiz.currentIndex, () => {
  if (quiz.savedAnswer) {
    if (quiz.currentQuestion?.type === 'multiple') {
      multiAnswer.value = Array.isArray(quiz.savedAnswer) ? [...quiz.savedAnswer] : []
    } else {
      answer.value = quiz.savedAnswer
    }
  } else {
    answer.value = ''
    multiAnswer.value = []
  }
})

watch(() => quiz.result, (val) => {
  if (val) {
    router.push(`/result/${val.record_id}`)
  }
})

function getCurrentAnswer() {
  return quiz.currentQuestion?.type === 'multiple' ? [...multiAnswer.value] : answer.value
}

async function nextQuestion() {
  await quiz.answer(quiz.currentQuestion.id, quiz.currentQuestion.type, getCurrentAnswer(), 'next')
}

async function prevQuestion() {
  await quiz.answer(quiz.currentQuestion.id, quiz.currentQuestion.type, getCurrentAnswer(), 'prev')
}

async function submitQuiz() {
  await quiz.answer(quiz.currentQuestion.id, quiz.currentQuestion.type, getCurrentAnswer(), 'submit')
}

function goBack() {
  quiz.reset()
  router.push('/')
}

</script>

<style scoped>
.question-card { border-radius: 1rem; }
.question-content { margin: 1rem 0 1.5rem; line-height: 1.8; font-size: 1.05rem; }
.question-image { max-height: 300px; max-width: 100%; border-radius: 0.5rem; }
.options-list { margin-bottom: 1rem; }
.option-item { display: block; margin-bottom: 8px; padding: 8px 12px; border-radius: 8px; background: rgba(0,0,0,0.02); width: 100%; }
.judge-btn { flex: 1; height: 60px; font-size: 1.1rem; }
.nav-buttons { display: flex; justify-content: space-between; margin-top: 2rem; }
.d-flex { display: flex; }
.justify-between { justify-content: space-between; }
.align-center { align-items: center; }
.gap-3 { gap: 1rem; }
.w-100 { width: 100%; }
</style>