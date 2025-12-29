import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Button,
  Table,
  Form,
  Input,
  InputNumber,
  Modal,
  message,
  Switch,
  Tabs,
  Tag,
  Space,
  Divider
} from 'antd';
import {
  DollarOutlined,
  RiseOutlined,
  FallOutlined,
  TrophyOutlined,
  ThunderboltOutlined,
  PlusOutlined
} from '@ant-design/icons';
import axios from 'axios';

const { TabPane } = Tabs;

const SimTradingPanel = () => {
  const [accounts, setAccounts] = useState([]);
  const [selectedAccount, setSelectedAccount] = useState(null);
  const [positions, setPositions] = useState([]);
  const [trades, setTrades] = useState([]);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [form] = Form.useForm();

  const API_BASE = 'http://localhost:8001/api';

  // Load accounts on mount
  useEffect(() => {
    loadAccounts();
  }, []);

  // Load positions, trades and logs when account is selected
  useEffect(() => {
    if (selectedAccount) {
      loadPositions(selectedAccount.id);
      loadTrades(selectedAccount.id);
      loadLogs(selectedAccount.id);
    }
  }, [selectedAccount]);

  const loadAccounts = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE}/sim-trading/accounts`);
      const accountsList = response.data.accounts || [];
      setAccounts(accountsList);
      if (accountsList.length > 0 && !selectedAccount) {
        setSelectedAccount(accountsList[0]);
      }
    } catch (error) {
      message.error('加载账户失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const loadPositions = async (accountId) => {
    try {
      const response = await axios.get(`${API_BASE}/sim-trading/accounts/${accountId}/positions`);
      setPositions(response.data.positions || []);
    } catch (error) {
      message.error('加载持仓失败: ' + error.message);
    }
  };

  const loadTrades = async (accountId) => {
    try {
      const response = await axios.get(`${API_BASE}/sim-trading/accounts/${accountId}/trades`);
      setTrades(response.data.trades || []);
    } catch (error) {
      message.error('加载交易历史失败: ' + error.message);
    }
  };

  const loadLogs = async (accountId) => {
    try {
      const response = await axios.get(`${API_BASE}/sim-trading/accounts/${accountId}/logs?limit=100`);
      setLogs(response.data.logs || []);
    } catch (error) {
      message.error('加载日志失败: ' + error.message);
    }
  };

  const handleCreateAccount = async (values) => {
    try {
      setLoading(true);
      await axios.post(`${API_BASE}/sim-trading/accounts`, values);
      message.success('账户创建成功');
      setCreateModalVisible(false);
      form.resetFields();
      await loadAccounts();
    } catch (error) {
      message.error('创建账户失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleAutoTrading = async () => {
    if (!selectedAccount) return;
    try {
      const newStatus = !selectedAccount.auto_trading_enabled;
      await axios.patch(`${API_BASE}/sim-trading/accounts/${selectedAccount.id}`, {
        auto_trading_enabled: newStatus
      });
      message.success(newStatus ? '自动交易已启用' : '自动交易已停止');
      await loadAccounts();
    } catch (error) {
      message.error('切换自动交易失败: ' + error.message);
    }
  };

  const handleTriggerAutoTrade = async () => {
    if (!selectedAccount) return;
    try {
      setLoading(true);
      const response = await axios.post(`${API_BASE}/sim-trading/accounts/${selectedAccount.id}/auto-trade`);
      const result = response.data;

      if (result.actions_taken && result.actions_taken.length > 0) {
        message.success(`执行了 ${result.actions_taken.length} 个交易操作`);
      } else {
        message.info('未找到符合条件的交易信号');
      }

      await loadAccounts();
      await loadPositions(selectedAccount.id);
      await loadTrades(selectedAccount.id);
      await loadLogs(selectedAccount.id);
    } catch (error) {
      message.error('触发自动交易失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleClosePosition = async (positionId) => {
    try {
      setLoading(true);
      await axios.delete(`${API_BASE}/sim-trading/positions/${positionId}`);
      message.success('持仓已平仓');
      await loadAccounts();
      await loadPositions(selectedAccount.id);
      await loadTrades(selectedAccount.id);
      await loadLogs(selectedAccount.id);
    } catch (error) {
      message.error('平仓失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const positionColumns = [
    {
      title: '币种',
      dataIndex: 'symbol',
      key: 'symbol',
      render: (symbol) => <Tag color="blue">{symbol}</Tag>
    },
    {
      title: '入场价格',
      dataIndex: 'entry_price',
      key: 'entry_price',
      render: (price) => `$${price.toFixed(6)}`
    },
    {
      title: '当前价格',
      dataIndex: 'current_price',
      key: 'current_price',
      render: (price) => price ? `$${price.toFixed(6)}` : '-'
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      key: 'quantity',
      render: (qty) => qty.toFixed(4)
    },
    {
      title: '未实现盈亏',
      dataIndex: 'unrealized_pnl_pct',
      key: 'unrealized_pnl_pct',
      render: (pct, record) => {
        const color = pct >= 0 ? '#3f8600' : '#cf1322';
        return (
          <span style={{ color }}>
            {pct >= 0 ? '+' : ''}{pct.toFixed(2)}%
            <br />
            <small>${record.unrealized_pnl ? record.unrealized_pnl.toFixed(2) : '0.00'}</small>
          </span>
        );
      }
    },
    {
      title: '止损/止盈',
      key: 'stops',
      render: (_, record) => (
        <div>
          <div style={{ color: '#cf1322' }}>
            SL: ${record.stop_loss_price ? record.stop_loss_price.toFixed(6) : '-'}
          </div>
          {record.take_profit_prices && record.take_profit_prices.length > 0 && (
            <div style={{ color: '#3f8600' }}>
              TP: ${record.take_profit_prices[0].toFixed(6)}
            </div>
          )}
        </div>
      )
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Button
          size="small"
          danger
          onClick={() => handleClosePosition(record.id)}
          loading={loading}
        >
          平仓
        </Button>
      )
    }
  ];

  const tradeColumns = [
    {
      title: '时间',
      dataIndex: 'trade_time',
      key: 'trade_time',
      render: (time) => new Date(time).toLocaleString('zh-CN')
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
        <Tag color={side === 'BUY' ? 'green' : 'red'}>
          {side === 'BUY' ? '买入' : '卖出'}
        </Tag>
      )
    },
    {
      title: '价格',
      dataIndex: 'price',
      key: 'price',
      render: (price) => `$${price.toFixed(6)}`
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      key: 'quantity',
      render: (qty) => qty.toFixed(4)
    },
    {
      title: '盈亏',
      dataIndex: 'pnl_pct',
      key: 'pnl_pct',
      render: (pct, record) => {
        if (pct === null || pct === undefined) return '-';
        const color = pct >= 0 ? '#3f8600' : '#cf1322';
        return (
          <span style={{ color }}>
            {pct >= 0 ? '+' : ''}{pct.toFixed(2)}%
            <br />
            <small>${record.pnl ? record.pnl.toFixed(2) : '0.00'}</small>
          </span>
        );
      }
    },
    {
      title: '类型',
      dataIndex: 'trade_type',
      key: 'trade_type',
      render: (type) => {
        const typeMap = {
          'ENTRY': '开仓',
          'PARTIAL_EXIT': '部分平仓',
          'FULL_EXIT': '全部平仓'
        };
        return typeMap[type] || type;
      }
    }
  ];

  const logColumns = [
    {
      title: '时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 180,
      render: (time) => new Date(time).toLocaleString('zh-CN')
    },
    {
      title: '操作',
      dataIndex: 'action',
      key: 'action',
      width: 120,
      render: (action) => {
        const actionMap = {
          'OPEN_POSITION': { text: '开仓', color: 'green' },
          'CLOSE_POSITION': { text: '平仓', color: 'red' },
          'SKIP': { text: '跳过', color: 'default' },
          'ERROR': { text: '错误', color: 'red' }
        };
        const config = actionMap[action] || { text: action, color: 'default' };
        return <Tag color={config.color}>{config.text}</Tag>;
      }
    },
    {
      title: '币种',
      dataIndex: 'symbol',
      key: 'symbol',
      width: 100
    },
    {
      title: '分数',
      dataIndex: 'screening_score',
      key: 'screening_score',
      width: 80,
      render: (score) => score ? score.toFixed(1) : '-'
    },
    {
      title: '原因',
      dataIndex: 'reason',
      key: 'reason',
      ellipsis: true
    },
    {
      title: '状态',
      dataIndex: 'success',
      key: 'success',
      width: 80,
      render: (success) => (
        <Tag color={success ? 'success' : 'error'}>
          {success ? '成功' : '失败'}
        </Tag>
      )
    },
    {
      title: '错误信息',
      dataIndex: 'error_message',
      key: 'error_message',
      ellipsis: true,
      render: (msg) => msg ? <span style={{ color: '#cf1322' }}>{msg}</span> : '-'
    }
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <Space style={{ marginBottom: 16 }}>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setCreateModalVisible(true)}
            >
              创建账户
            </Button>

            {selectedAccount && (
              <>
                <Button
                  type={selectedAccount.auto_trading_enabled ? 'default' : 'primary'}
                  danger={selectedAccount.auto_trading_enabled}
                  onClick={handleToggleAutoTrading}
                >
                  {selectedAccount.auto_trading_enabled ? '停止自动交易' : '启动自动交易'}
                </Button>

                <Button
                  icon={<ThunderboltOutlined />}
                  onClick={handleTriggerAutoTrade}
                  loading={loading}
                >
                  手动触发交易
                </Button>
              </>
            )}
          </Space>
        </Col>

        {selectedAccount && (
          <>
            <Col span={6}>
              <Card>
                <Statistic
                  title="账户净值"
                  value={selectedAccount.total_equity}
                  precision={2}
                  prefix={<DollarOutlined />}
                  suffix="USDT"
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="可用余额"
                  value={selectedAccount.current_balance}
                  precision={2}
                  prefix={<DollarOutlined />}
                  suffix="USDT"
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="总盈亏"
                  value={selectedAccount.total_pnl}
                  precision={2}
                  valueStyle={{
                    color: selectedAccount.total_pnl >= 0 ? '#3f8600' : '#cf1322'
                  }}
                  prefix={selectedAccount.total_pnl >= 0 ? <RiseOutlined /> : <FallOutlined />}
                  suffix="USDT"
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="胜率"
                  value={
                    selectedAccount.total_trades > 0
                      ? ((selectedAccount.winning_trades / selectedAccount.total_trades) * 100)
                      : 0
                  }
                  precision={1}
                  prefix={<TrophyOutlined />}
                  suffix="%"
                />
              </Card>
            </Col>
          </>
        )}

        <Col span={24}>
          <Card
            title={selectedAccount ? `${selectedAccount.account_name} - 交易详情` : '选择账户'}
            extra={
              selectedAccount && (
                <Tag color={selectedAccount.auto_trading_enabled ? 'green' : 'default'}>
                  {selectedAccount.auto_trading_enabled ? '自动交易中' : '手动模式'}
                </Tag>
              )
            }
          >
            {selectedAccount && (
              <Tabs defaultActiveKey="positions">
                <TabPane tab={`持仓 (${positions.length})`} key="positions">
                  <Table
                    columns={positionColumns}
                    dataSource={positions}
                    rowKey="id"
                    loading={loading}
                    pagination={{ pageSize: 10 }}
                  />
                </TabPane>
                <TabPane tab={`交易历史 (${trades.length})`} key="trades">
                  <Table
                    columns={tradeColumns}
                    dataSource={trades}
                    rowKey="id"
                    loading={loading}
                    pagination={{ pageSize: 20 }}
                  />
                </TabPane>
                <TabPane tab={`交易日志 (${logs.length})`} key="logs">
                  <Table
                    columns={logColumns}
                    dataSource={logs}
                    rowKey="id"
                    loading={loading}
                    pagination={{ pageSize: 50 }}
                    size="small"
                  />
                </TabPane>
              </Tabs>
            )}
          </Card>
        </Col>
      </Row>

      <Modal
        title="创建模拟账户"
        open={createModalVisible}
        onCancel={() => setCreateModalVisible(false)}
        onOk={() => form.submit()}
        confirmLoading={loading}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreateAccount}
          initialValues={{
            initial_balance: 10000,
            max_positions: 5,
            position_size_pct: 2.0,
            entry_score_min: 75.0,
            entry_technical_min: 60.0,
            stop_loss_pct: 3.0,
            take_profit_levels: [6.0, 9.0, 12.0]
          }}
        >
          <Form.Item
            name="account_name"
            label="账户名称"
            rules={[{ required: true, message: '请输入账户名称' }]}
          >
            <Input placeholder="例如: 保守策略A" />
          </Form.Item>

          <Form.Item
            name="initial_balance"
            label="初始资金 (USDT)"
            rules={[{ required: true, message: '请输入初始资金' }]}
          >
            <InputNumber min={1000} max={1000000} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="max_positions"
            label="最大持仓数"
          >
            <InputNumber min={1} max={20} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="position_size_pct"
            label="单仓位资金占比 (%)"
          >
            <InputNumber min={0.5} max={20} step={0.5} style={{ width: '100%' }} />
          </Form.Item>

          <Divider>策略参数</Divider>

          <Form.Item
            name="entry_score_min"
            label="最低总分"
          >
            <InputNumber min={0} max={100} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="entry_technical_min"
            label="最低技术分"
          >
            <InputNumber min={0} max={100} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="stop_loss_pct"
            label="止损 (%)"
          >
            <InputNumber min={0.5} max={10} step={0.5} style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default SimTradingPanel;
