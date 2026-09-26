import request from './request'

export const adminAPI = {
  // 分类
  getCategories: () => request.get('/admin/categories'),
  addCategory: (data) => request.post('/admin/categories', data),
  deleteCategory: (id) => request.delete(`/admin/categories/${id}`),

  // 分组
  getGroups: () => request.get('/admin/groups'),
  addGroup: (data) => request.post('/admin/groups', data),
  updateGroup: (id, data) => request.put(`/admin/groups/${id}`, data),
  deleteGroup: (id) => request.delete(`/admin/groups/${id}`),

  // 题目
  getQuestions: (params) => request.get('/admin/questions', { params }),
  addQuestion: (data) => request.post('/admin/questions', data),
  updateQuestion: (id, data) => request.put(`/admin/questions/${id}`, data),
  deleteQuestion: (id) => request.delete(`/admin/questions/${id}`),
  bulkDeleteQuestions: (ids) => request.post('/admin/questions/bulk-delete', { ids }),

  // 批量导入 / 导出
  importData: (formData) => request.post('/admin/import', formData),
  exportData: (params) => request.get('/admin/export', { params, responseType: 'blob' }),
  importPromptUrl: '/static/import_prompt.txt',

  // 用户
  getUsers: () => request.get('/admin/users'),
  toggleUser: (id) => request.post(`/admin/users/${id}/toggle`),
  clearUserHistory: (id) => request.post(`/admin/users/${id}/clear-history`),
  deleteUser: (id) => request.delete(`/admin/users/${id}`),
}
