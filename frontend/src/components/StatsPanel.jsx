import React from 'react'
import { Card, Row, Col } from 'antd'
import { DatabaseOutlined, FilterOutlined, BellOutlined, ClockCircleOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

const StatsPanel = ({ stats }) => {
  if (!stats) return null

  const statItems = [
    {
      icon: <DatabaseOutlined style={{ fontSize: '24px', color: '#1890ff' }} />,
      value: stats.total_klines?.toLocaleString() || '0',
      label: 'K线数据',
    },
    {
      icon: <FilterOutlined style={{ fontSize: '24px', color: '#52c41a' }} />,
      value: stats.total_screenings?.toLocaleString() || '0',
      label: '筛选次数',
    },
    {
      icon: <BellOutlined style={{ fontSize: '24px', color: '#faad14' }} />,
      value: stats.total_alerts?.toLocaleString() || '0',
      label: '发送警报',
    },
    {
      icon: <ClockCircleOutlined style={{ fontSize: '24px', color: '#722ed1' }} />,
      value: stats.latest_screening ? dayjs(stats.latest_screening).fromNow() : '未筛选',
      label: '最近筛选',
    },
  ]

  return (
    <Row gutter={16}>
      {statItems.map((item, index) => (
        <Col xs={24} sm={12} md={6} key={index}>
          <Card>
            <div className="stats-card">
              {item.icon}
              <div className="stats-value">{item.value}</div>
              <div className="stats-label">{item.label}</div>
            </div>
          </Card>
        </Col>
      ))}
    </Row>
  )
}

export default StatsPanel
