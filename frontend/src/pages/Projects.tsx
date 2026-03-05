import { Table, Button, Modal, Form, Input, message } from 'antd'
import { useEffect, useState } from 'react'
import { getProjects, createProject, deleteProject } from '../services/api'

export default function Projects() {
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [form] = Form.useForm()

  const fetchProjects = async () => {
    setLoading(true)
    try {
      const res = await getProjects()
      setData(res)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchProjects() }, [])

  const handleCreate = async () => {
    try {
      await form.validateFields()
      await createProject(form.getFieldsValue())
      message.success('Project created')
      setModalOpen(false)
      form.resetFields()
      fetchProjects()
    } catch (e) { /* validation error */ }
  }

  const handleDelete = async (id: number) => {
    await deleteProject(id)
    message.success('Project deleted')
    fetchProjects()
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id' },
    { title: 'Name', dataIndex: 'name', key: 'name' },
    { title: 'GitHub Repo', dataIndex: 'github_repo', key: 'github_repo' },
    { title: 'AI Provider', dataIndex: 'ai_provider', key: 'ai_provider' },
    { title: 'Created', dataIndex: 'created_at', key: 'created_at', render: (t: string) => new Date(t).toLocaleString() },
    { title: 'Action', key: 'action', render: (_: any, r: any) => (
      <Button danger size="small" onClick={() => handleDelete(r.id)}>Delete</Button>
    )},
  ]

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <h1>📁 Projects</h1>
        <Button type="primary" onClick={() => setModalOpen(true)}>Add Project</Button>
      </div>
      <Table dataSource={data} columns={columns} rowKey="id" loading={loading} />

      <Modal title="New Project" open={modalOpen} onOk={handleCreate} onCancel={() => setModalOpen(false)}>
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="Name" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="description" label="Description"><Input.TextArea /></Form.Item>
          <Form.Item name="github_repo" label="GitHub Repo"><Input placeholder="https://github.com/user/repo" /></Form.Item>
          <Form.Item name="default_branch" label="Default Branch" initialValue="main"><Input /></Form.Item>
          <Form.Item name="ai_provider" label="AI Provider" initialValue="anthropic"><Input /></Form.Item>
        </Form>
      </Modal>
    </div>
  )
}