import { Card, Form, Input, Select, Button, message, Switch } from 'antd'
import { useEffect, useState } from 'react'
import { getProjects, getNotificationConfig, createNotificationConfig, testNotification } from '../services/api'

export default function Notifications() {
  const [projects, setProjects] = useState<any[]>([])
  const [selectedProject, setSelectedProject] = useState<number | null>(null)
  const [config, setConfig] = useState<any>(null)
  const [form] = Form.useForm()
  const [testing, setTesting] = useState(false)

  useEffect(() => {
    getProjects().then(setProjects).catch(console.error)
  }, [])

  useEffect(() => {
    if (!selectedProject) {
      setConfig(null)
      return
    }
    getNotificationConfig(selectedProject)
      .then(setConfig)
      .catch(() => setConfig(null))
  }, [selectedProject])

  const handleSave = async () => {
    try {
      const values = await form.validateFields()
      await createNotificationConfig({ project_id: selectedProject, ...values })
      message.success('Notification config saved')
    } catch (e) { /* validation */ }
  }

  const handleTest = async () => {
    const webhookUrl = form.getFieldValue('webhook_url')
    if (!webhookUrl) {
      message.error('Please enter a webhook URL first')
      return
    }
    setTesting(true)
    try {
      await testNotification(webhookUrl, form.getFieldValue('channel') || 'feishu')
      message.success('Test notification sent!')
    } catch (e: any) {
      message.error(e.response?.data?.detail || 'Failed to send test notification')
    } finally {
      setTesting(false)
    }
  }

  return (
    <div style={{ padding: 24 }}>
      <h1>🔔 Notification Settings</h1>

      <Card style={{ marginTop: 16, maxWidth: 600 }}>
        <Form form={form} layout="vertical">
          <Form.Item label="Project">
            <Select
              placeholder="Select a project"
              onChange={setSelectedProject}
              value={selectedProject}
            >
              {projects.map(p => (
                <Select.Option key={p.id} value={p.id}>{p.name}</Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item label="Channel" name="channel" initialValue="feishu">
            <Select>
              <Select.Option value="feishu">Feishu</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item label="Webhook URL" name="webhook_url"
            rules={[{ required: true, message: 'Please enter webhook URL' }]}
          >
            <Input placeholder="https://open.feishu.cn/open-apis/bot/v2/hook/xxx" />
          </Form.Item>

          <Form.Item label="Notify on Completed" name="notify_on_completed" valuePropName="checked" initialValue={true}>
            <Switch />
          </Form.Item>

          <Form.Item label="Notify on Failed" name="notify_on_failed" valuePropName="checked" initialValue={false}>
            <Switch />
          </Form.Item>

          <Form.Item>
            <Button type="primary" onClick={handleSave} style={{ marginRight: 8 }}>Save</Button>
            <Button onClick={handleTest} loading={testing}>Test</Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}