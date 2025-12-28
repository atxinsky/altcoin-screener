import React, { useState, useEffect } from 'react'
import { Table, Card, Tag, Space, Button, Modal, Spin, message, Tooltip, InputNumber, Select, Form, Input, Radio } from 'antd'
import {
  LineChartOutlined,
  CheckCircleOutlined,
  FireOutlined,
  RiseOutlined,
  ReloadOutlined,
  StarOutlined,
  StarFilled,
  ShoppingCartOutlined
} from '@ant-design/icons'
import { getTopOpportunities, addToWatchlist, removeFromWatchlist, createMarketOrder } from '../services/api'
import KlineChart from './KlineChart'

const { Option } = Select

const ResultsTable = () => {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)
  const [chartModalVisible, setChartModalVisible] = useState(false)
  const [currentChartSymbol, setCurrentChartSymbol] = useState(null)
  const [currentChartTimeframe, setCurrentChartTimeframe] = useState('5m')
  const [watchlist, setWatchlist] = useState(new Set())
  const [tradeModalVisible, setTradeModalVisible] = useState(false)
  const [currentSymbol, setCurrentSymbol] = useState(null)
  const [tradeForm] = Form.useForm()

  useEffect(() => {
    loadResults()
  }, [])

  const loadResults = async () => {
    setLoading(true)
    try {
      const result = await getTopOpportunities(20, 60)
      setData(result.results || [])
    } catch (error) {
      console.error('Failed to load results:', error)
      message.error('加载结果失败')
    } finally {
      setLoading(false)
    }
  }

  const handleViewChart = (symbol, timeframe) => {
    setCurrentChartSymbol(symbol)
    setCurrentChartTimeframe(timeframe)
    setChartModalVisible(true)
  }

  const handleToggleWatchlist = async (symbol) => {
    try {
      if (watchlist.has(symbol)) {
        await removeFromWatchlist(symbol)
        setWatchlist(prev => {
          const newSet = new Set(prev)
          newSet.delete(symbol)
          return newSet
        })
        message.success('已从自选移除')
      } else {
        await addToWatchlist(symbol, '')
        setWatchlist(prev => new Set(prev).add(symbol))
        message.success('已添加到自选')
      }
    } catch (error) {
      message.error('操作失败: ' + error.message)
    }
  }

  const handleOpenTrade = (symbol) => {
    setCurrentSymbol(symbol)
    tradeForm.resetFields()
    tradeForm.setFieldsValue({ symbol, side: 'BUY', orderType: 'quantity' })
    setTradeModalVisible(true)
  }

  const handleTrade = async (values) => {
    try {
      // If user entered USDT amount, calculate quantity
      let quantity = values.quantity
      if (values.orderType === 'usdt' && values.usdtAmount) {
        // Get current price from data
        const symbolData = data.find(d => d.symbol === values.symbol)
        if (symbolData && symbolData.current_price) {
          quantity = values.usdtAmount / symbolData.current_price
        } else {
          message.error('无法获取当前价格，请使用数量模式')
          return
        }
      }

      await createMarketOrder(
        values.symbol,
        values.side,
        quantity,
        `快速交易 - ${new Date().toLocaleString()}`
      )
      message.success('订单已提交')
      setTradeModalVisible(false)
    } catch (error) {
      const errorMsg = error.response?.data?.detail || error.message
      if (errorMsg.includes('Invalid API-key') || errorMsg.includes('permissions')) {
        message.error('API密钥无交易权限，请在币安设置中启用交易权限或添加IP白名单')
      } else {
        message.error('下单失败: ' + errorMsg)
      }
    }
  }

  const getScoreColor = (score) => {
    if (score >= 80) return 'red'
    if (score >= 70) return 'orange'
    if (score >= 60) return 'green'
    return 'default'
  }

  const columns = [
    {
      title: '排名',
      key: 'rank',
      width: 60,
      render: (_, __, index) => index + 1,
      fixed: 'left',
    },
    {
      title: '交易对',
      dataIndex: 'symbol',
      key: 'symbol',
      width: 120,
      fixed: 'left',
      render: (symbol) => <strong>{symbol}</strong>,
    },
    {
      title: '总分',
      dataIndex: 'total_score',
      key: 'total_score',
      width: 100,
      sorter: (a, b) => a.total_score - b.total_score,
      render: (score) => (
        <Tag color={getScoreColor(score)} style={{ fontSize: '14px', fontWeight: 'bold' }}>
          {score.toFixed(1)}
        </Tag>
      ),
    },
    {
      title: '当前价格',
      dataIndex: 'current_price',
      key: 'current_price',
      width: 120,
      render: (price) => `$${price.toFixed(6)}`,
    },
    {
      title: 'BTC比率变化',
      dataIndex: 'btc_ratio_change_pct',
      key: 'btc_ratio_change_pct',
      width: 120,
      sorter: (a, b) => a.btc_ratio_change_pct - b.btc_ratio_change_pct,
      render: (change) => (
        <Tag color={change >= 0 ? 'green' : 'red'}>
          {change >= 0 ? '+' : ''}{change.toFixed(2)}%
        </Tag>
      ),
    },
    {
      title: 'ETH比率变化',
      dataIndex: 'eth_ratio_change_pct',
      key: 'eth_ratio_change_pct',
      width: 120,
      sorter: (a, b) => a.eth_ratio_change_pct - b.eth_ratio_change_pct,
      render: (change) => (
        <Tag color={change >= 0 ? 'green' : 'red'}>
          {change >= 0 ? '+' : ''}{change.toFixed(2)}%
        </Tag>
      ),
    },
    {
      title: '24h成交量',
      dataIndex: 'volume_24h',
      key: 'volume_24h',
      width: 120,
      sorter: (a, b) => a.volume_24h - b.volume_24h,
      render: (volume) => `$${(volume / 1000000).toFixed(2)}M`,
    },
    {
      title: '信号',
      key: 'signals',
      width: 250,
      render: (_, record) => (
        <Space size={[0, 4]} wrap>
          {record.above_sma && (
            <Tooltip title="价格在SMA 20之上">
              <Tag color="blue" className="signal-tag">
                <CheckCircleOutlined /> SMA
              </Tag>
            </Tooltip>
          )}
          {record.macd_golden_cross && (
            <Tooltip title="MACD金叉">
              <Tag color="gold" className="signal-tag">
                <RiseOutlined /> MACD
              </Tag>
            </Tooltip>
          )}
          {record.above_all_ema && (
            <Tooltip title="价格在所有EMA之上">
              <Tag color="green" className="signal-tag">
                <CheckCircleOutlined /> EMAs
              </Tag>
            </Tooltip>
          )}
          {record.volume_surge && (
            <Tooltip title="成交量激增">
              <Tag color="orange" className="signal-tag">
                <FireOutlined /> 量能
              </Tag>
            </Tooltip>
          )}
          {record.price_anomaly && (
            <Tooltip title="价格异动">
              <Tag color="red" className="signal-tag">
                <FireOutlined /> 异动
              </Tag>
            </Tooltip>
          )}
        </Space>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="查看K线图">
            <Button
              type="link"
              size="small"
              icon={<LineChartOutlined />}
              onClick={() => handleViewChart(record.symbol, record.timeframe)}
            />
          </Tooltip>
          <Tooltip title={watchlist.has(record.symbol) ? '取消自选' : '添加自选'}>
            <Button
              type="link"
              size="small"
              icon={watchlist.has(record.symbol) ? <StarFilled style={{ color: '#faad14' }} /> : <StarOutlined />}
              onClick={() => handleToggleWatchlist(record.symbol)}
            />
          </Tooltip>
          <Tooltip title="快速下单">
            <Button
              type="primary"
              size="small"
              icon={<ShoppingCartOutlined />}
              onClick={() => handleOpenTrade(record.symbol)}
            />
          </Tooltip>
        </Space>
      ),
    },
  ]

  return (
    <>
      <Card
        title="筛选结果"
        extra={
          <Button
            icon={<ReloadOutlined />}
            onClick={loadResults}
            loading={loading}
          >
            刷新
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={data}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1300 }}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条记录`,
          }}
          rowClassName={(record) =>
            record.total_score >= 80
              ? 'high-score'
              : record.total_score >= 70
              ? 'medium-score'
              : ''
          }
        />
      </Card>

      <Modal
        title="K线图"
        open={chartModalVisible}
        onCancel={() => setChartModalVisible(false)}
        footer={null}
        width={1200}
        bodyStyle={{ padding: '20px' }}
      >
        {currentChartSymbol && (
          <KlineChart
            symbol={currentChartSymbol}
            initialTimeframe={currentChartTimeframe}
          />
        )}
      </Modal>

      <Modal
        title={`快速下单 - ${currentSymbol || ''}`}
        open={tradeModalVisible}
        onCancel={() => setTradeModalVisible(false)}
        footer={null}
        width={500}
      >
        <Form
          form={tradeForm}
          layout="vertical"
          onFinish={handleTrade}
        >
          <Form.Item
            name="symbol"
            label="交易对"
          >
            <Input disabled style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item
            name="side"
            label="方向"
            rules={[{ required: true, message: '请选择方向' }]}
          >
            <Select>
              <Option value="BUY">买入 (BUY)</Option>
              <Option value="SELL">卖出 (SELL)</Option>
            </Select>
          </Form.Item>
          <Form.Item
            name="orderType"
            label="下单方式"
          >
            <Radio.Group>
              <Radio value="quantity">按数量</Radio>
              <Radio value="usdt">按USDT金额</Radio>
            </Radio.Group>
          </Form.Item>
          <Form.Item
            noStyle
            shouldUpdate={(prevValues, currentValues) => prevValues.orderType !== currentValues.orderType}
          >
            {({ getFieldValue }) =>
              getFieldValue('orderType') === 'quantity' ? (
                <Form.Item
                  name="quantity"
                  label="数量"
                  rules={[{ required: true, message: '请输入数量' }]}
                >
                  <InputNumber
                    style={{ width: '100%' }}
                    placeholder="输入交易数量"
                    min={0}
                    step={0.0001}
                  />
                </Form.Item>
              ) : (
                <Form.Item
                  name="usdtAmount"
                  label="USDT金额"
                  rules={[{ required: true, message: '请输入USDT金额' }]}
                >
                  <InputNumber
                    style={{ width: '100%' }}
                    placeholder="输入USDT金额"
                    min={0}
                    step={1}
                    prefix="$"
                  />
                </Form.Item>
              )
            }
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                提交市价单
              </Button>
              <Button onClick={() => setTradeModalVisible(false)}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </>
  )
}

export default ResultsTable
