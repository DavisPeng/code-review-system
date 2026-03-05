import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
})

// Stats
export const getStats = () => api.get('/stats/overview').then(res => res.data)

// Projects
export const getProjects = () => api.get('/projects').then(res => res.data)
export const getProject = (id: number) => api.get(`/projects/${id}`).then(res => res.data)
export const createProject = (data: any) => api.post('/projects', data).then(res => res.data)
export const updateProject = (id: number, data: any) => api.put(`/projects/${id}`, data).then(res => res.data)
export const deleteProject = (id: number) => api.delete(`/projects/${id}`)

// Reviews
export const getReviews = (params?: any) => api.get('/reviews', { params }).then(res => res.data)
export const getReview = (id: number) => api.get(`/reviews/${id}`).then(res => res.data)
export const getReviewIssues = (id: number, params?: any) =>
  api.get(`/reviews/${id}/issues`, { params }).then(res => res.data)

// Rules
export const getRules = (params?: any) => api.get('/rules', { params }).then(res => res.data)
export const getRule = (id: number) => api.get(`/rules/${id}`).then(res => res.data)
export const createRule = (data: any) => api.post('/rules', data).then(res => res.data)
export const updateRule = (id: number, data: any) => api.put(`/rules/${id}`, data).then(res => res.data)
export const deleteRule = (id: number) => api.delete(`/rules/${id}`)

// Rule Sets
export const getRuleSets = () => api.get('/rulesets').then(res => res.data)
export const getRuleSet = (id: number) => api.get(`/rulesets/${id}`).then(res => res.data)
export const createRuleSet = (data: any) => api.post('/rulesets', data).then(res => res.data)
export const applyRuleSet = (rulesetId: number, projectId: number) =>
  api.post(`/rulesets/${rulesetId}/apply`, null, { params: { project_id: projectId } }).then(res => res.data)

// Notifications
export const getNotificationConfig = (projectId: number) =>
  api.get(`/notifications/config/${projectId}`).then(res => res.data)
export const createNotificationConfig = (data: any) =>
  api.post('/notifications/config', data).then(res => res.data)
export const updateNotificationConfig = (projectId: number, data: any) =>
  api.put(`/notifications/config/${projectId}`, data).then(res => res.data)
export const testNotification = (webhookUrl: string, channel: string = 'feishu') =>
  api.post('/notifications/test', null, { params: { webhook_url: webhookUrl, channel } }).then(res => res.data)

export default api