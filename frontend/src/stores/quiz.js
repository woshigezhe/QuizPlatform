import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { startQuiz, startGroupQuiz, getQuestion, answerQuestion, getResult } from '@/api/quiz'

export const useQuizStore = defineStore('quiz', () => {
  const recordId = ref(null)
  const groupMode = ref(false)
  const groupName = ref('')
  const currentQuestion = ref(null)
  const currentIndex = ref(0)
  const totalQuestions = ref(0)
  const savedAnswer = ref(null)
  const loading = ref(false)
  const submitting = ref(false)
  const result = ref(null)

  const progress = computed(() => {
    if (totalQuestions.value === 0) return 0
    return Math.round((currentIndex.value / totalQuestions.value) * 100)
  })

  const isLast = computed(() => currentIndex.value >= totalQuestions.value - 1)
  const isFirst = computed(() => currentIndex.value === 0)

  async function start(categoryId) {
    loading.value = true
    try {
      const res = await startQuiz(categoryId)
      const d = res.data
      recordId.value = d.record_id
      groupMode.value = false
      groupName.value = ''
      currentQuestion.value = d.question
      currentIndex.value = d.index
      totalQuestions.value = d.total
      savedAnswer.value = null
      result.value = null
    } catch {
      // handled by interceptor
    } finally {
      loading.value = false
    }
  }

  async function startGroup(categoryId, groupId = null) {
    loading.value = true
    try {
      const res = await startGroupQuiz(categoryId, groupId)
      const d = res.data
      recordId.value = d.record_id
      groupMode.value = true
      groupName.value = d.group_name
      currentQuestion.value = d.question
      currentIndex.value = d.index
      totalQuestions.value = d.total
      savedAnswer.value = null
      result.value = null
    } catch {
      // handled by interceptor
    } finally {
      loading.value = false
    }
  }

  async function answer(qid, type, answer, action) {
    if (action === 'submit') submitting.value = true
    else loading.value = true
    try {
      const res = await answerQuestion(qid, type, answer, action)
      const d = res.data
      if (action === 'submit') {
        result.value = d
        currentQuestion.value = null
      } else {
        currentQuestion.value = d.question
        currentIndex.value = d.index
        savedAnswer.value = d.saved_answer
      }
      return d
    } catch {
      return null
    } finally {
      loading.value = false
      submitting.value = false
    }
  }

  async function fetchResult(recId) {
    loading.value = true
    try {
      const res = await getResult(recId)
      result.value = res.data
    } finally {
      loading.value = false
    }
  }

  function reset() {
    recordId.value = null
    groupMode.value = false
    groupName.value = ''
    currentQuestion.value = null
    currentIndex.value = 0
    totalQuestions.value = 0
    savedAnswer.value = null
    result.value = null
  }

  return {
    recordId, groupMode, groupName,
    currentQuestion, currentIndex, totalQuestions, savedAnswer,
    loading, submitting, result,
    progress, isLast, isFirst,
    start, startGroup, answer, fetchResult, reset
  }
})