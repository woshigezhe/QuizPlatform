<template>
  <div>
    <div class="d-flex justify-between align-center mb-3">
      <h3>题目管理</h3>
      <div class="d-flex gap-2">
        <el-select v-model="filterCategoryId" placeholder="筛选分类" clearable size="small" style="width:140px" @change="fetchData">
          <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
        </el-select>
        <el-button type="primary" size="small" @click="showAddDialog"><el-icon><Plus /></el-icon> 新增</el-button>
      </div>
    </div>
    <el-table :data="questions" v-loading="loading" stripe @selection-change="(v)=>selectedRows=v" style="border-radius:0.75rem;overflow:hidden">
      <el-table-column type="selection" width="50" />
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="content" label="题干" show-overflow-tooltip min-width="200" />
      <el-table-column prop="category_name" label="分类" width="90" />
      <el-table-column prop="group_name" label="分组" width="110" show-overflow-tooltip />
      <el-table-column label="题型" width="70">
        <template #default="{ row }">
          <el-tag size="small">{{ { single:'单选',multiple:'多选',judge:'判断',fill:'填空' }[row.type] }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button size="small" @click="showEditDialog(row)">编辑</el-button>
          <el-popconfirm title="确定删除？" @confirm="handleDelete(row.id)">
            <template #reference>
              <el-button size="small" type="danger">删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>
    <div class="mt-3" v-if="selectedRows.length">
      <el-popconfirm title="确定批量删除？" @confirm="handleBulkDelete">
        <template #reference>
          <el-button type="danger" size="small">删除选中 ({{ selectedRows.length }})</el-button>
        </template>
      </el-popconfirm>
    </div>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑题目' : '新增题目'" width="620px">
      <el-form label-width="80px">
        <el-form-item label="分类">
          <el-select v-model="form.category_id" placeholder="选择分类" style="width:100%" @change="form.group_id = null">
            <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="分组">
          <el-select v-model="form.group_id" placeholder="可选，不选则不归属分组" clearable style="width:100%">
            <el-option v-for="g in filteredGroups" :key="g.id" :label="g.name" :value="g.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="题型">
          <el-select v-model="form.type" style="width:100%">
            <el-option label="单选" value="single" /><el-option label="多选" value="multiple" />
            <el-option label="判断" value="judge" /><el-option label="填空" value="fill" />
          </el-select>
        </el-form-item>
        <el-form-item label="题干"><el-input v-model="form.content" type="textarea" :rows="3" /></el-form-item>
        <el-form-item label="配图">
          <input ref="fileInput" type="file" accept="image/*" @change="onFileChange" />
          <div v-if="previewUrl" class="mt-2">
            <img :src="previewUrl" style="max-height:100px;border-radius:6px" />
          </div>
        </el-form-item>
        <el-form-item v-if="form.type !== 'judge' && form.type !== 'fill'" label="选项">
          <el-input v-model="optionsText" type="textarea" placeholder="每行一个选项" :rows="4" />
        </el-form-item>
        <el-form-item label="答案">
          <el-input v-model="form.answer" :placeholder="answerPlaceholder" />
        </el-form-item>
        <el-form-item label="解析"><el-input v-model="form.analysis" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="难度"><el-input-number v-model="form.difficulty" :min="1" :max="5" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { adminAPI } from '@/api/admin'

const questions = ref([])
const categories = ref([])
const groups = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const editingId = ref(null)
const selectedRows = ref([])
const filterCategoryId = ref(null)
const optionsText = ref('')
const imageFile = ref(null)
const fileInput = ref(null)

const defaultForm = () => ({ category_id: null, group_id: null, type: 'single', content: '', image: null, answer: '', analysis: '', difficulty: 1 })
const form = reactive(defaultForm())

const filteredGroups = computed(() =>
  form.category_id ? groups.value.filter(g => g.category_id === form.category_id) : groups.value
)

const previewUrl = computed(() => {
  if (imageFile.value) return URL.createObjectURL(imageFile.value)
  return form.image ? '/' + String(form.image).replace(/^\/+/, '') : ''
})

const answerPlaceholder = computed(() => {
  if (form.type === 'judge') return '对 / 错（也兼容 正确 / 错误）'
  if (form.type === 'multiple') return '如 A,C'
  if (form.type === 'fill') return '多个答案用 | 分隔'
  return '如 B'
})

async function fetchData() {
  loading.value = true
  try {
    const params = {}
    if (filterCategoryId.value) params.category_id = filterCategoryId.value
    const [qr, cr, gr] = await Promise.all([adminAPI.getQuestions(params), adminAPI.getCategories(), adminAPI.getGroups()])
    questions.value = qr.data.questions
    categories.value = cr.data.categories
    groups.value = gr.data.groups
  } finally { loading.value = false }
}

onMounted(fetchData)

function resetFile() {
  imageFile.value = null
  if (fileInput.value) fileInput.value.value = ''
}

function showAddDialog() {
  Object.assign(form, defaultForm())
  optionsText.value = ''
  editingId.value = null
  resetFile()
  dialogVisible.value = true
}

function showEditDialog(row) {
  Object.assign(form, defaultForm(), row)
  optionsText.value = Array.isArray(row.options) ? row.options.join('\n') : ''
  editingId.value = row.id
  resetFile()
  dialogVisible.value = true
}

function onFileChange(e) {
  imageFile.value = e.target.files[0] || null
}

async function handleSave() {
  if (!form.content.trim()) return ElMessage.warning('请输入题干')
  const payload = { ...form }
  if (form.type !== 'judge' && form.type !== 'fill') {
    payload.options = optionsText.value.split('\n').filter(l => l.trim())
  } else {
    payload.options = []
  }

  let data = payload
  if (imageFile.value) {
    const fd = new FormData()
    Object.entries(payload).forEach(([k, v]) => {
      if (v === null || v === undefined) { fd.append(k, ''); return }
      fd.append(k, Array.isArray(v) ? v.join('\n') : v)
    })
    fd.append('question_image', imageFile.value)
    data = fd
  }

  if (editingId.value) {
    await adminAPI.updateQuestion(editingId.value, data)
  } else {
    await adminAPI.addQuestion(data)
  }
  dialogVisible.value = false
  resetFile()
  fetchData()
}

async function handleDelete(id) { await adminAPI.deleteQuestion(id); fetchData() }

async function handleBulkDelete() {
  await adminAPI.bulkDeleteQuestions(selectedRows.value.map(r => r.id))
  selectedRows.value = []
  fetchData()
}
</script>

<style scoped>
.d-flex { display: flex; } .justify-between { display: flex; justify-content: space-between; } .align-center { align-items: center; } .gap-2 { gap: 8px; }
</style>
