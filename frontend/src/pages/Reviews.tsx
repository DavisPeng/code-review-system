import { Table, Tag, Button } from 'antd'
import { useEffect, useState } from 'react'
import { getReviews } from '../services/api'
import { useNavigate } from 'react-router-dom'

export default function Reviews() {
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20, total: 0 })
  const navigate = useNavigate()

  const fetchReviews = async (page = 1) => {
    setLoading(true)
    try {
      const res = await getReviews({ page, page_size: pagination.pageSize })
      setData(res)
      setPagination({ ...pagination, current: page })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchReviews()
  }, [])

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id' },
    { title: 'Commit', dataIndex: 'commit_sha', key: 'commit_sha', render: (s: string) => s?.slice(0, 8) },
    { title: 'Branch', dataIndex: 'branch', key: 'branch' },
    { title: 'Status', dataIndex: 'status', key: 'status', render: (s: string) => (
      <Tag color={s === 'completed' ? 'green' : s === 'failed' ? 'red' : 'blue'}>{s}</Tag>
    )},
    { title: 'Issues', dataIndex: 'issues_count', key: 'issues_count' },
    { title: 'Created', dataIndex: 'created_at', key: 'created_at', render: (t: string) => new Date(t).toLocaleString() },
    { title: 'Action', key: 'action', render: (_: any, r: any) => (
      <Button type="link" onClick={() => navigate(`/reviews/${r.id}`)}>View</Button>
    )},
  ]

  return (
    <div style={{ padding: 24 }}>
      <h1>📝 Reviews</h1>
      <Table
        dataSource={data}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={{ ...pagination, onChange: fetchReviews }}
        style={{ marginTop: 16 }}
      />
    </div>
  )
}