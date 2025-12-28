import React, { useState, useEffect } from 'react'
import {
  Card,
  Tabs,
  Form,
  Input,
  InputNumber,
  Select,
  Button,
  Table,
  message,
  Statistic,
  Row,
  Col,
  Space,
  Tag,
  Popconfirm,
  Alert
} from 'antd'
import {
  WalletOutlined,
  ShoppingOutlined,
  HistoryOutlined,
  StarOutlined,
  DollarOutlined
} from '@ant-design/icons'
import {
  getAllBalances,
  createMarketOrder,
  createLimitOrder,
  getOrderHistory,
  cancelOrder,
  getWatchlist,
  addToWatchlist,
  removeFromWatchlist
} from '../services/api'

const { TabPane } = Tabs
const { Option } = Select

function TradingPanel() {
  const [marketForm] = Form.useForm()
  const [limitForm] = Form.useForm()
  const [watchlistForm] = Form.useForm()

  const [balances, setBalances] = useState([])
  const [orders, setOrders] = useState([])
  const [watchlist, setWatchlist] = useState([])
  const [loading, setLoading] = useState(false)
  const [orderLoading, setOrderLoading] = useState(false)

  useEffect(() => {
    loadBalances()
    loadOrderHistory()
    loadWatchlist()
  }, [])

  const loadBalances = async () => {
    try {
      const response = await getAllBalances()
      setBalances(response.balances || [])
    } catch (error) {
      message.error('加载余额失败: ' + error.message)
    }
  }

  const loadOrderHistory = async () => {
    try {
      const response = await getOrderHistory(null, 50)
      setOrders(response.orders || [])
    } catch (error) {
      message.error('加载订单历史失败: ' + error.message)
    }
  }

  const loadWatchlist = async () => {
    try {
      const response = await getWatchlist()
      setWatchlist(response.watchlist || [])
    } catch (error) {
      message.error('加载自选币种失败: ' + error.message)
    }
  }

  const handleMarketOrder = async (values) => {
    setOrderLoading(true)
    try {
      await createMarketOrder(
        values.symbol,
        values.side,
        values.quantity,
        values.notes
      )
      message.success('市价单创建成功!')
      marketForm.resetFields()
      loadOrderHistory()
      loadBalances()
    } catch (error) {
      message.error('创建订单失败: ' + error.message)
    } finally {
      setOrderLoading(false)
    }
  }

  const handleLimitOrder = async (values) => {
    setOrderLoading(true)
    try {
      await createLimitOrder(
        values.symbol,
        values.side,
        values.quantity,
        values.price,
        values.notes
      )
      message.success('限价单创建成功!')
      limitForm.resetFields()
      loadOrderHistory()
      loadBalances()
    } catch (error) {
      message.error('创建订单失败: ' + error.message)
    } finally {
      setOrderLoading(false)
    }
  }

  const handleCancelOrder = async (orderId) => {
    try {
      await cancelOrder(orderId)
      message.success('订单已取消')
      loadOrderHistory()
    } catch (error) {
      message.error('取消订单失败: ' + error.message)
    }
  }

  const handleAddToWatchlist = async (values) => {
    try {
      const response = await addToWatchlist(values.symbol, values.notes)
      if (response.success) {
        message.success('已添加到自选')
        watchlistForm.resetFields()
        loadWatchlist()
      } else {
        message.warning(response.message)
      }
    } catch (error) {
      message.error('添加失败: ' + error.message)
    }
  }

  const handleRemoveFromWatchlist = async (symbol) => {
    try {
      const response = await removeFromWatchlist(symbol)
      if (response.success) {
        message.success('已从自选移除')
        loadWatchlist()
      }
    } catch (error) {
      message.error('移除失败: ' + error.message)
    }
  }

  const balanceColumns = [
    {
      title: '资产',
      dataIndex: 'asset',
      key: 'asset',
      render: (text) => <strong>{text}</strong>
    },
    {
      title: '可用',
      dataIndex: 'free',
      key: 'free',
      render: (val) => val.toFixed(8)
    },
    {
      title: '冻结',
      dataIndex: 'used',
      key: 'used',
      render: (val) => val.toFixed(8)
    },
    {
      title: '总计',
      dataIndex: 'total',
      key: 'total',
      render: (val) => <strong>{val.toFixed(8)}</strong>
    }
  ]

  const orderColumns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 60
    },
    {
      title: '币种',
      dataIndex: 'symbol',
      key: 'symbol'
    },
    {
      title: '方向',
      dataIndex: 'side',
      key: 'side',
      render: (side) => (
        <Tag color={side === 'BUY' ? 'green' : 'red'}>{side}</Tag>
      )
    },
    {
      title: '类型',
      dataIndex: 'order_type',
      key: 'order_type'
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      key: 'quantity'
    },
    {
      title: '价格',
      dataIndex: 'price',
      key: 'price',
      render: (price) => price || '-'
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => {
        const colorMap = {
          PENDING: 'processing',
          FILLED: 'success',
          CANCELLED: 'default',
          FAILED: 'error'
        }
        return <Tag color={colorMap[status]}>{status}</Tag>
      }
    },
    {
      title: '成交价',
      dataIndex: 'avg_fill_price',
      key: 'avg_fill_price',
      render: (price) => price || '-'
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (time) => new Date(time).toLocaleString('zh-CN')
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => {
        if (record.status === 'PENDING' || record.status === 'OPEN') {
          return (
            <Popconfirm
              title="确定取消这个订单吗？"
              onConfirm={() => handleCancelOrder(record.id)}
            >
              <Button type="link" size="small" danger>
                取消
              </Button>
            </Popconfirm>
          )
        }
        return '-'
      }
    }
  ]

  const watchlistColumns = [
    {
      title: '币种',
      dataIndex: 'symbol',
      key: 'symbol',
      render: (text) => <strong>{text}</strong>
    },
    {
      title: '备注',
      dataIndex: 'notes',
      key: 'notes',
      render: (text) => text || '-'
    },
    {
      title: '添加时间',
      dataIndex: 'added_at',
      key: 'added_at',
      render: (time) => new Date(time).toLocaleString('zh-CN')
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Popconfirm
          title="确定移除吗？"
          onConfirm={() => handleRemoveFromWatchlist(record.symbol)}
        >
          <Button type="link" size="small" danger>
            移除
          </Button>
        </Popconfirm>
      )
    }
  ]

  // Top balances display
  const topBalances = balances.slice(0, 4)

  return (
    <Card title={<><DollarOutlined /> 实盘交易</>} className="trading-card">
      <Alert
        message="注意"
        description="本模块连接真实币安账户，下单前请确认订单参数！建议先用小额测试。"
        type="warning"
        showIcon
        style={{ marginBottom: 16 }}
      />

      {/* Top Balances Summary */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        {topBalances.map((balance) => (
          <Col span={6} key={balance.asset}>
            <Card size="small">
              <Statistic
                title={balance.asset}
                value={balance.total}
                precision={balance.asset === 'USDT' ? 2 : 6}
                prefix={<WalletOutlined />}
              />
            </Card>
          </Col>
        ))}
      </Row>

      <Tabs defaultActiveKey="market">
        {/* Market Order Tab */}
        <TabPane
          tab={
            <span>
              <ShoppingOutlined />
              市价单
            </span>
          }
          key="market"
        >
          <Form
            form={marketForm}
            layout="vertical"
            onFinish={handleMarketOrder}
          >
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="symbol"
                  label="币种"
                  rules={[{ required: true, message: '请输入币种' }]}
                >
                  <Input placeholder="例如: BTC/USDT" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="side"
                  label="方向"
                  rules={[{ required: true, message: '请选择方向' }]}
                >
                  <Select placeholder="选择买入或卖出">
                    <Option value="BUY">买入 (BUY)</Option>
                    <Option value="SELL">卖出 (SELL)</Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="quantity"
                  label="数量"
                  rules={[{ required: true, message: '请输入数量' }]}
                >
                  <InputNumber
                    style={{ width: '100%' }}
                    placeholder="输入购买数量"
                    min={0}
                    step={0.0001}
                  />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item name="notes" label="备注">
                  <Input placeholder="可选备注" />
                </Form.Item>
              </Col>
            </Row>
            <Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                loading={orderLoading}
                size="large"
              >
                提交市价单
              </Button>
            </Form.Item>
          </Form>
        </TabPane>

        {/* Limit Order Tab */}
        <TabPane
          tab={
            <span>
              <ShoppingOutlined />
              限价单
            </span>
          }
          key="limit"
        >
          <Form
            form={limitForm}
            layout="vertical"
            onFinish={handleLimitOrder}
          >
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="symbol"
                  label="币种"
                  rules={[{ required: true, message: '请输入币种' }]}
                >
                  <Input placeholder="例如: BTC/USDT" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="side"
                  label="方向"
                  rules={[{ required: true, message: '请选择方向' }]}
                >
                  <Select placeholder="选择买入或卖出">
                    <Option value="BUY">买入 (BUY)</Option>
                    <Option value="SELL">卖出 (SELL)</Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>
            <Row gutter={16}>
              <Col span={8}>
                <Form.Item
                  name="quantity"
                  label="数量"
                  rules={[{ required: true, message: '请输入数量' }]}
                >
                  <InputNumber
                    style={{ width: '100%' }}
                    placeholder="数量"
                    min={0}
                    step={0.0001}
                  />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item
                  name="price"
                  label="价格"
                  rules={[{ required: true, message: '请输入价格' }]}
                >
                  <InputNumber
                    style={{ width: '100%' }}
                    placeholder="限价"
                    min={0}
                    step={0.01}
                  />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item name="notes" label="备注">
                  <Input placeholder="可选备注" />
                </Form.Item>
              </Col>
            </Row>
            <Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                loading={orderLoading}
                size="large"
              >
                提交限价单
              </Button>
            </Form.Item>
          </Form>
        </TabPane>

        {/* Order History Tab */}
        <TabPane
          tab={
            <span>
              <HistoryOutlined />
              订单历史
            </span>
          }
          key="history"
        >
          <Button
            onClick={loadOrderHistory}
            style={{ marginBottom: 16 }}
          >
            刷新
          </Button>
          <Table
            columns={orderColumns}
            dataSource={orders}
            rowKey="id"
            pagination={{ pageSize: 10 }}
            size="small"
          />
        </TabPane>

        {/* Balances Tab */}
        <TabPane
          tab={
            <span>
              <WalletOutlined />
              账户余额
            </span>
          }
          key="balance"
        >
          <Button
            onClick={loadBalances}
            style={{ marginBottom: 16 }}
          >
            刷新
          </Button>
          <Table
            columns={balanceColumns}
            dataSource={balances}
            rowKey="asset"
            pagination={{ pageSize: 20 }}
            size="small"
          />
        </TabPane>

        {/* Watchlist Tab */}
        <TabPane
          tab={
            <span>
              <StarOutlined />
              自选币种
            </span>
          }
          key="watchlist"
        >
          <Form
            form={watchlistForm}
            layout="inline"
            onFinish={handleAddToWatchlist}
            style={{ marginBottom: 16 }}
          >
            <Form.Item
              name="symbol"
              rules={[{ required: true, message: '请输入币种' }]}
            >
              <Input placeholder="例如: BTC/USDT" style={{ width: 200 }} />
            </Form.Item>
            <Form.Item name="notes">
              <Input placeholder="备注（可选）" style={{ width: 200 }} />
            </Form.Item>
            <Form.Item>
              <Button type="primary" htmlType="submit">
                添加
              </Button>
            </Form.Item>
          </Form>
          <Table
            columns={watchlistColumns}
            dataSource={watchlist}
            rowKey="symbol"
            pagination={{ pageSize: 10 }}
            size="small"
          />
        </TabPane>
      </Tabs>
    </Card>
  )
}

export default TradingPanel
