<template>
  <div v-loading="loading">
    <div v-if="roadmapData">
      <h2 class="text-center mb-3"><el-icon><MapLocation /></el-icon> {{ roadmapData.category.name }}</h2>
      <p class="text-center text-muted mb-4">按顺序学习，每组全对才能解锁下一组</p>
      
<div class="roadmap-grid">
        <div v-for="g in roadmapData.groups" :key="g.id" :class="['group-node', g.node_class]">
          <div class="node-badge" :class="'badge-' + g.node_class">
            {{ statusLabel(g.node_class) }}
          </div>
          <div class="node-icon">{{ iconMap[g.node_class] }}</div>
          <div class="node-name">{{ g.name }}</div>
          <div v-if="g.description" class="node-desc">{{ g.description.substring(0, 80) }}</div>
          <div class="node-actions">
            <el-button v-if="g.node_class !== 'locked' && g.has_study_content" size="small" @click.stop="$router.push(`/study/${g.id}`)">学习</el-button>
            <el-button v-if="g.node_class !== 'locked'" type="primary" size="small" @click.stop="startGroupQuiz(g.id)">答题</el-button>
          </div>
        </div>
      </div>
      
      <div style="text-align: center; margin-top: 20px">
        <el-button @click="$router.push('/')"><el-icon><ArrowLeft /></el-icon> 返回首页</el-button>
      </div>
    </div>
    <el-empty v-else description="加载中..." />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useQuizStore } from '@/stores/quiz'
import { getRoadmap } from '@/api/quiz'

const route = useRoute()
const router = useRouter()
const quiz = useQuizStore()
const roadmapData = ref(null)
const loading = ref(false)

const iconMap = { locked: '🔒', unlocked: '📚', completed: '🏆', current: '🎯' }
function statusLabel(cls) {
  return { locked: '🔒 未解锁', unlocked: '📖 开放', completed: '✅ 已完成', current: '📍 当前' }[cls] || ''
}

onMounted(async () => {
  loading.value = true
  try {
    const res = await getRoadmap(parseInt(route.params.categoryId))
    roadmapData.value = res.data
  } finally {
    loading.value = false
  }
})

async function startGroupQuiz(groupId) {
  await quiz.startGroup(parseInt(route.params.categoryId), groupId)
  router.push('/quiz')
}
</script>

<style scoped>
.roadmap-grid { display: flex; flex-wrap: wrap; justify-content: center; gap: 20px; padding: 1rem; }
.group-node { width: 220px; border-radius: 1rem; padding: 1.2rem; text-align: center; cursor: pointer; transition: all 0.3s; border: 2px solid #e0e0e0; background: rgba(255,255,255,0.85); }
.group-node:hover { transform: translateY(-4px); box-shadow: 0 10px 20px rgba(0,0,0,0.08); }
.group-node.unlocked { border-color: #2c2c2c; }
.group-node.locked { opacity: 0.45; cursor: not-allowed; filter: grayscale(0.6); }
.group-node.current { border-color: #f59e0b; border-width: 3px; animation: pulse 2s ease-in-out infinite; }
.group-node.completed { border-color: #10b981; background: rgba(236,253,245,0.8); }
@keyframes pulse { 0%,100% { box-shadow: 0 0 0 0 rgba(245,158,11,0.3); } 50% { box-shadow: 0 0 0 12px rgba(245,158,11,0); } }
.node-icon { font-size: 2rem; margin: 0.5rem 0; }
.node-name { font-weight: 700; font-size: 1rem; margin-bottom: 0.3rem; }
.node-desc { font-size: 0.75rem; color: #666; margin-bottom: 0.8rem; }
.node-badge { font-size: 0.7rem; padding: 2px 10px; border-radius: 1rem; margin-bottom: 0.5rem; display: inline-block; }
.badge-locked { background: #f3f4f6; color: #9ca3af; } .badge-current { background: #fef3c7; color: #d97706; }
.badge-completed { background: #d1fae5; color: #059669; } .badge-unlocked { background: #e5e7eb; color: #4b5563; }
.node-actions { display: flex; gap: 6px; justify-content: center; flex-wrap: wrap; }
.text-muted { color: #6c6c6c; }
</style>