import { Card, Row, Col, Statistic, Table } from 'antd'
import { Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { useEffect, useState } from 'react'
import { getStats } from '../services/api'

const COLORS = ['#ff4d4f', '#faad14', '#1677ff', '#52c41a']

export default function Dashboard() {
  const [stats, setStats] = useState<any>(null)

  useEffect(() => {
    getStats().then(setStats).catch(console.error)
  }, [])

  if (!stats) {
    return <div style={{ padding: 24 }}>Loading...</div>
  }

  const severityData = Object.entries(stats.issues_by_severity || {}).map(([name, value]: [string, any]) => ({
    name,
    value
  }))

  return (
    <div style={{ padding: 24 }}>
      <h1 style={{ marginBottom: 24 }}>📊 Dashboard</h1>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic title="Total Projects" value={stats.total_projects} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="Total Reviews" value={stats.total_reviews} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="Completed" value={stats.reviews_by_status?.completed || 0} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="Pending" value={stats.reviews_by_status?.pending || 0} />
          </Card>
        </Col>
      </Row>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={12}>
          <Card title="Issue Distribution">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={severityData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {severityData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col span={12}>
          <Card title="Recent Reviews">
            <Table
              dataSource={stats.recent_reviews}
              columns={[
                { title: 'Commit', dataIndex: 'commit_sha', key: 'commit_sha' },
                { title: 'Status', dataIndex: 'status', key: 'status' },
                { title: 'Issues', dataIndex: 'issues_count', key: 'issues_count' },
              ]}
              rowKey="id"
              size="small"
              pagination={false}
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}