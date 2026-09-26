<template>
  <div>
    <h3 class="mb-3">批量导入</h3>
    <el-card shadow="never">
      <p>支持 <b>.xlsx</b> / <b>.xls</b> / <b>.csv</b>，或包含数据文件与配图的 <b>.zip</b> 压缩包。</p>
      <p>
        格式说明与 AI 转换提示词：
        <a :href="promptUrl" target="_blank" rel="noopener">下载导入提示词</a>
      </p>
      <div class="mt-3">
        <input ref="fileInput" type="file" accept=".xlsx,.xls,.csv,.zip" @change="onFile" />
      </div>
      <div class="mt-3">
        <el-button type="primary" :loading="loading" :disabled="!file" @click="doImport">开始导入</el-button>
      </div>
      <el-alert v-if="result" :title="result" type="success" :closable="false" class="mt-3" />
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { adminAPI } from '@/api/admin'

const promptUrl = adminAPI.importPromptUrl
const file = ref(null)
const fileInput = ref(null)
const loading = ref(false)
const result = ref('')

function onFile(e) {
  file.value = e.target.files[0] || null
}

async function doImport() {
  if (!file.value) return
  loading.value = true
  result.value = ''
  try {
    const fd = new FormData()
    fd.append('file', file.value)
    const res = await adminAPI.importData(fd)
    result.value = res.message || '导入完成'
    ElMessage.success(result.value)
    file.value = null
    if (fileInput.value) fileInput.value.value = ''
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.mt-3 { margin-top: 12px; }
</style>
