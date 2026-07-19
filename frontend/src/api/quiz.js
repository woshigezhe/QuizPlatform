import request from './request'

// 获取分类列表
export function getCategories() {
  return request.get('/categories')
}

// 开始随机答题
export function startQuiz(categoryId) {
  return request.post('/quiz/start', { category_id: categoryId })
}

// 开始题组答题
export function startGroupQuiz(categoryId, groupId = null) {
  return request.post('/quiz/group/start', { category_id: categoryId, group_id: groupId })
}

// 获取当前题目
export function getQuestion() {
  return request.get('/quiz/question')
}

// 保存答案并操作（next/prev/submit）
export function answerQuestion(questionId, type, answer, action = 'next') {
  return request.post('/quiz/answer', {
    question_id: questionId,
    type: type,
    answer: answer,
    action: action
  })
}

// 获取答题结果
export function getResult(recordId) {
  return request.get(`/quiz/result/${recordId}`)
}

// 获取路线图
export function getRoadmap(categoryId) {
  return request.get(`/roadmap/${categoryId}`)
}

// 获取学习资料
export function getStudy(groupId) {
  return request.get(`/study/${groupId}`)
}

// 获取排行榜
export function getLeaderboard() {
  return request.get('/leaderboard')
}

// 获取历史记录
export function getHistory() {
  return request.get('/history')
}