import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Card, Tag, Descriptions, Table, Spin } from 'antd'
import { getReview, getReviewIssues } from '../services/api'

export default function ReviewDetail() {
  const { id } = useParams<{ id: string }>()
  const [task, setTask] = useState<any>(null)
  const [issues, setIssues] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!id) return
    Promise.all([
      getReview(parseInt(id)),
      getReviewIssues(parseInt(id))
    ]).then(([taskData, issuesData]) => {
      setTask(taskData.task)
      setIssues(issuesData)
    }).finally(() => setLoading(false))
  }, [id])

  if (loading) return <div style={{ padding: 24, textAlign: 'center' }}><Spin /></div>
  if (!task) return <div style={{ padding: 24 }}>Review not found</div>

  const columns = [
    { title: 'File', dataIndex: 'file_path', key: 'file_path' },
    { title: 'Line', dataIndex: 'line_number', key: 'line_number' },
    { title: 'Severity', dataIndex: 'severity', key: 'severity', render: (s: string) => (
      <Tag color={s === 'error' ? 'red' : s === 'warning' ? 'orange' : 'blue'}>{s}</Tag>
    )},
    { title: 'Category', dataIndex: 'category', key: 'category' },
    { title: 'Message', dataIndex: 'message', key: 'message', ellipsis: true },
    { title: 'Source', dataIndex: 'source', key: 'source' },
  ]

  return (
    <div style={{ padding: 24 }}>
      <h1>🔍 Review #{id}</h1>
      <Card style={{ marginTop: 16 }}>
        <Descriptions>
          <Descriptions.Item label="Commit">{task.commit_sha}</Descriptions.Item>
          <Descriptions.Item label="Branch">{task.branch}</Descriptions.Item>
          <Descriptions.Item label="Status">
            <Tag color={task.status === 'completed' ? 'green' : task.status === 'failed' ? 'red' : 'blue'}>
              {task.status}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Issues">{task.issues_count}</Descriptions.Item>
          <Descriptions.Item label="Created">{new Date(task.created_at).toLocaleString()}</Descriptions.Item>
        </Descriptions>
      </Card>
      <Card title="Issues" style={{ marginTop: 16 }}>
        <Table dataSource={issues} columns={columns} rowKey="id" pagination={false} />
      </Card>
    </div>
  )
}