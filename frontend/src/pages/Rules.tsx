import { Table, Button, Modal, Form, Input, Select, Switch, message, Tabs } from 'antd'
import { useEffect, useState } from 'react'
import { getRules, createRule, getRuleSets, createRuleSet } from '../services/api'

export default function Rules() {
  const [rules, setRules] = useState<any[]>([])
  const [ruleSets, setRuleSets] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [ruleSetModalOpen, setRuleSetModalOpen] = useState(false)
  const [form] = Form.useForm()
  const [ruleSetForm] = Form.useForm()
  const [activeTab, setActiveTab] = useState('rules')

  const fetchData = async () => {
    setLoading(true)
    try {
      const [r, rs] = await Promise.all([getRules(), getRuleSets()])
      setRules(r)
      setRuleSets(rs)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchData() }, [])

  const handleCreateRule = async () => {
    try {
      await form.validateFields()
      await createRule(form.getFieldsValue())
      message.success('Rule created')
      setModalOpen(false)
      form.resetFields()
      fetchData()
    } catch (e) { /* validation */ }
  }

  const handleCreateRuleSet = async () => {
    try {
      await ruleSetForm.validateFields()
      await createRuleSet(ruleSetForm.getFieldsValue())
      message.success('Rule set created')
      setRuleSetModalOpen(false)
      ruleSetForm.resetFields()
      fetchData()
    } catch (e) { /* validation */ }
  }

  const ruleColumns = [
    { title: 'Name', dataIndex: 'name', key: 'name' },
    { title: 'Category', dataIndex: 'category', key: 'category' },
    { title: 'Severity', dataIndex: 'severity', key: 'severity' },
    { title: 'Enabled', dataIndex: 'enabled', key: 'enabled', render: (e: boolean) => e ? '✅' : '❌' },
  ]

  const ruleSetColumns = [
    { title: 'Name', dataIndex: 'name', key: 'name' },
    { title: 'Description', dataIndex: 'description', key: 'description' },
    { title: 'Default', dataIndex: 'is_default', key: 'is_default', render: (e: boolean) => e ? '⭐' : '' },
    { title: 'Rules Count', dataIndex: 'rules', key: 'rules', render: (r: any[]) => r?.length || 0 },
  ]

  return (
    <div style={{ padding: 24 }}>
      <h1>⚙️ Rules</h1>
      <Tabs activeKey={activeTab} onChange={setActiveTab} style={{ marginTop: 16 }}>
        <Tabs.TabPane tab="Rules" key="rules">
          <Button type="primary" style={{ marginBottom: 16 }} onClick={() => setModalOpen(true)}>Add Rule</Button>
          <Table dataSource={rules} columns={ruleColumns} rowKey="id" loading={loading} />
        </Tabs.TabPane>
        <Tabs.TabPane tab="Rule Sets" key="rulesets">
          <Button type="primary" style={{ marginBottom: 16 }} onClick={() => setRuleSetModalOpen(true)}>Add Rule Set</Button>
          <Table dataSource={ruleSets} columns={ruleSetColumns} rowKey="id" loading={loading} />
        </Tabs.TabPane>
      </Tabs>

      <Modal title="New Rule" open={modalOpen} onOk={handleCreateRule} onCancel={() => setModalOpen(false)}>
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="Name" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="description" label="Description"><Input.TextArea /></Form.Item>
          <Form.Item name="category" label="Category" rules={[{ required: true }]}>
            <Select>
              <Select.Option value="coding_standard">Coding Standard</Select.Option>
              <Select.Option value="logic_error">Logic Error</Select.Option>
              <Select.Option value="performance">Performance</Select.Option>
              <Select.Option value="memory_safety">Memory Safety</Select.Option>
              <Select.Option value="concurrency">Concurrency</Select.Option>
              <Select.Option value="maintainability">Maintainability</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="severity" label="Severity" initialValue="warning">
            <Select>
              <Select.Option value="error">Error</Select.Option>
              <Select.Option value="warning">Warning</Select.Option>
              <Select.Option value="info">Info</Select.Option>
              <Select.Option value="suggestion">Suggestion</Select.Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      <Modal title="New Rule Set" open={ruleSetModalOpen} onOk={handleCreateRuleSet} onCancel={() => setRuleSetModalOpen(false)}>
        <Form form={ruleSetForm} layout="vertical">
          <Form.Item name="name" label="Name" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="description" label="Description"><Input.TextArea /></Form.Item>
          <Form.Item name="is_default" label="Default" valuePropName="checked" initialValue={false}>
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}