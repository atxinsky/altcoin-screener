import React, { useState, useEffect } from 'react'
import {
  Card,
  Table,
  Select,
  Button,
  Space,
  Tag,
  Tooltip,
  Modal,
  message,
  Statistic,
  Row,
  Col
} from 'antd'
import {
  TrophyOutlined,
  ReloadOutlined,
  LineChartOutlined,
  HistoryOutlined,
  RiseOutlined,
  FallOutlined
} from '@ant-design/icons'
import { getHistoricalRankings, getSymbolHistory } from '../services/api'
import KlineChart from './KlineChart'

const { Option } = Select

function HistoricalRankings() {
  const [rankings, setRankings] = useState([])
  const [loading, setLoading] = useState(false)
  const [days, setDays] = useState(3)
  const [historyModalVisible, setHistoryModalVisible] = useState(false)
  const [currentSymbol, setCurrentSymbol] = useState(null)
  const [symbolHistory, setSymbolHistory] = useState([])
  const [historyLoading, setHistoryLoading] = useState(false)
  const [chartModalVisible, setChartModalVisible] = useState(false)
  const [chartSymbol, setChartSymbol] = useState(null)

  useEffect(() => {
    loadRankings()
  }, [days])

  const loadRankings = async () => {
    setLoading(true)
    try {
      const response = await getHistoricalRankings(days, 20)
      setRankings(response.rankings || [])
    } catch (error) {
      message.error('加载排名失败: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  const handleViewHistory = async (symbol) => {
    setCurrentSymbol(symbol)
    setHistoryModalVisible(true)
    setHistoryLoading(true)
    try {
      const response = await getSymbolHistory(symbol, 7)
      setSymbolHistory(response.history || [])
    } catch (error) {
      message.error('加载历史失败: ' + error.message)
    } finally {
      setHistoryLoading(false)
    }
  }

  const handleViewChart = (symbol) => {
    setChartSymbol(symbol)
    setChartModalVisible(true)
  }

  const getTrophyColor = (rank) => {
    if (rank === 1) return '#FFD700'  // Gold
    if (rank === 2) return '#C0C0C0'  // Silver
    if (rank === 3) return '#CD7F32'  // Bronze
    return '#666'
  }

  const columns = [
    {
      title: '排名',
      dataIndex: 'rank',
      key: 'rank',
      width: 80,
      render: (rank) => (
        <Space>
          {rank <= 3 && (
            <TrophyOutlined style={{ fontSize: '20px', color: getTrophyColor(rank) }} />
          )}
          <strong style={{ fontSize: '16px' }}>{rank}</strong>
        </Space>
      )
    },
    {
      title: '交易对',
      dataIndex: 'symbol',
      key: 'symbol',
      width: 120,
      render: (symbol) => <strong>{symbol}</strong>
    },
    {
      title: '平均分',
      dataIndex: 'avg_score',
      key: 'avg_score',
      width: 100,
      sorter: (a, b) => a.avg_score - b.avg_score,
      render: (score) => (
        <Tag color={score >= 80 ? 'red' : score >= 70 ? 'orange' : 'green'} style={{ fontSize: '14px', fontWeight: 'bold' }}>
          {score.toFixed(1)}
        </Tag>
      )
    },
    {
      title: '最高分',
      dataIndex: 'max_score',
      key: 'max_score',
      width: 100,
      render: (score) => score.toFixed(1)
    },
    {
      title: '最低分',
      dataIndex: 'min_score',
      key: 'min_score',
      width: 100,
      render: (score) => score.toFixed(1)
    },
    {
      title: '出现次数',
      dataIndex: 'appearance_count',
      key: 'appearance_count',
      width: 100,
      sorter: (a, b) => a.appearance_count - b.appearance_count,
      render: (count) => (
        <Tooltip title="在筛选中出现的次数">
          <Tag color="blue">{count}次</Tag>
        </Tooltip>
      )
    },
    {
      title: '最后出现',
      dataIndex: 'last_seen',
      key: 'last_seen',
      width: 180,
      render: (time) => new Date(time).toLocaleString('zh-CN')
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="查看历史记录">
            <Button
              type="link"
              size="small"
              icon={<HistoryOutlined />}
              onClick={() => handleViewHistory(record.symbol)}
            >
              历史
            </Button>
          </Tooltip>
          <Tooltip title="查看K线图">
            <Button
              type="link"
              size="small"
              icon={<LineChartOutlined />}
              onClick={() => handleViewChart(record.symbol)}
            >
              图表
            </Button>
          </Tooltip>
        </Space>
      )
    }
  ]

  const historyColumns = [
    {
      title: '时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (time) => new Date(time).toLocaleString('zh-CN')
    },
    {
      title: '总分',
      dataIndex: 'total_score',
      key: 'total_score',
      render: (score) => (
        <Tag color={score >= 80 ? 'red' : score >= 70 ? 'orange' : 'green'}>
          {score.toFixed(1)}
        </Tag>
      )
    },
    {
      title: 'Beta分',
      dataIndex: 'beta_score',
      key: 'beta_score',
      render: (score) => score.toFixed(1)
    },
    {
      title: '量能分',
      dataIndex: 'volume_score',
      key: 'volume_score',
      render: (score) => score.toFixed(1)
    },
    {
      title: '技术分',
      dataIndex: 'technical_score',
      key: 'technical_score',
      render: (score) => score.toFixed(1)
    },
    {
      title: '价格',
      dataIndex: 'current_price',
      key: 'current_price',
      render: (price) => `$${price.toFixed(6)}`
    },
    {
      title: 'BTC比率变化',
      dataIndex: 'btc_ratio_change_pct',
      key: 'btc_ratio_change_pct',
      render: (change) => (
        <Tag color={change >= 0 ? 'green' : 'red'} icon={change >= 0 ? <RiseOutlined /> : <FallOutlined />}>
          {change >= 0 ? '+' : ''}{change.toFixed(2)}%
        </Tag>
      )
    }
  ]

  return (
    <>
      <Card
        title={
          <Space>
            <TrophyOutlined />
            历史排名榜 ({days}天平均分)
          </Space>
        }
        extra={
          <Space>
            <Select value={days} onChange={setDays} style={{ width: 120 }}>
              <Option value={1}>1天</Option>
              <Option value={3}>3天</Option>
              <Option value={7}>7天</Option>
              <Option value={14}>14天</Option>
              <Option value={30}>30天</Option>
            </Select>
            <Button
              icon={<ReloadOutlined />}
              onClick={loadRankings}
              loading={loading}
            >
              刷新
            </Button>
          </Space>
        }
      >
        {rankings.length > 0 && (
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={8}>
              <Card size="small" style={{ background: '#fafafa' }}>
                <Statistic
                  title={
                    <Space>
                      <TrophyOutlined style={{ color: '#FFD700', fontSize: '20px' }} />
                      <span>冠军</span>
                    </Space>
                  }
                  value={rankings[0]?.symbol || '-'}
                  valueStyle={{ color: '#cf1322', fontWeight: 'bold' }}
                  suffix={rankings[0] ? `${rankings[0].avg_score.toFixed(1)}分` : ''}
                />
              </Card>
            </Col>
            {rankings[1] && (
              <Col span={8}>
                <Card size="small" style={{ background: '#fafafa' }}>
                  <Statistic
                    title={
                      <Space>
                        <TrophyOutlined style={{ color: '#C0C0C0', fontSize: '18px' }} />
                        <span>亚军</span>
                      </Space>
                    }
                    value={rankings[1].symbol}
                    valueStyle={{ color: '#faad14' }}
                    suffix={`${rankings[1].avg_score.toFixed(1)}分`}
                  />
                </Card>
              </Col>
            )}
            {rankings[2] && (
              <Col span={8}>
                <Card size="small" style={{ background: '#fafafa' }}>
                  <Statistic
                    title={
                      <Space>
                        <TrophyOutlined style={{ color: '#CD7F32', fontSize: '16px' }} />
                        <span>季军</span>
                      </Space>
                    }
                    value={rankings[2].symbol}
                    valueStyle={{ color: '#52c41a' }}
                    suffix={`${rankings[2].avg_score.toFixed(1)}分`}
                  />
                </Card>
              </Col>
            )}
          </Row>
        )}

        <Table
          columns={columns}
          dataSource={rankings}
          rowKey="symbol"
          loading={loading}
          pagination={{
            pageSize: 5,
            showSizeChanger: false,
            showTotal: (total) => `共 ${total} 个币种`
          }}
          rowClassName={(record) =>
            record.rank === 1 ? 'gold-row' : record.rank === 2 ? 'silver-row' : record.rank === 3 ? 'bronze-row' : ''
          }
        />
      </Card>

      <Modal
        title={
          <Space>
            <HistoryOutlined />
            {currentSymbol} - 历史得分记录
          </Space>
        }
        open={historyModalVisible}
        onCancel={() => setHistoryModalVisible(false)}
        footer={null}
        width={1000}
      >
        <Table
          columns={historyColumns}
          dataSource={symbolHistory}
          rowKey="timestamp"
          loading={historyLoading}
          pagination={{ pageSize: 10 }}
          size="small"
        />
      </Modal>

      <Modal
        title="K线图"
        open={chartModalVisible}
        onCancel={() => setChartModalVisible(false)}
        footer={null}
        width={1200}
        bodyStyle={{ padding: '20px' }}
      >
        {chartSymbol && (
          <KlineChart
            symbol={chartSymbol}
            initialTimeframe="5m"
          />
        )}
      </Modal>

      <style jsx>{`
        .gold-row {
          background-color: #fffbe6 !important;
        }
        .silver-row {
          background-color: #f5f5f5 !important;
        }
        .bronze-row {
          background-color: #fff7e6 !important;
        }
      `}</style>
    </>
  )
}

export default HistoricalRankings
