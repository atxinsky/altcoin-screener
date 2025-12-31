import React, { useState, useEffect } from 'react';
// ATR_BUILD_MARKER_20251231_1825
console.log('SimTradingPanel loaded with ATR support v1.0');
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
  Divider,
  Tooltip,
  Descriptions,
  Collapse,
  Select
} from 'antd';
import {
  DollarOutlined,
  RiseOutlined,
  FallOutlined,
  TrophyOutlined,
  ThunderboltOutlined,
  PlusOutlined,
  InfoCircleOutlined,
  ExpandOutlined
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

  const API_BASE = '/api';

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
      // 转换止盈字段为数组格式
      const payload = {
        ...values,
        take_profit_levels: [
          values.take_profit_1 || 6.0,
          values.take_profit_2 || 10.0,
          values.take_profit_3 || 15.0
        ],
        // ATR take profit multipliers
        atr_tp_multipliers: [
          values.atr_tp_1 || 2.5,
          values.atr_tp_2 || 3.5,
          values.atr_tp_3 || 5.0
        ],
        // 策略配置JSON
        strategy_config: {
          require_macd_golden: values.require_macd_golden,
          require_volume_surge: values.require_volume_surge,
          trailing_stop_enabled: values.trailing_stop_enabled,
          trailing_stop_pct: values.trailing_stop_pct,
          max_holding_hours: values.max_holding_hours
        }
      };
      // 删除单独的字段
      delete payload.take_profit_1;
      delete payload.take_profit_2;
      delete payload.take_profit_3;
      delete payload.atr_tp_1;
      delete payload.atr_tp_2;
      delete payload.atr_tp_3;
      delete payload.require_macd_golden;
      delete payload.require_volume_surge;
      delete payload.trailing_stop_enabled;
      delete payload.trailing_stop_pct;
      delete payload.max_holding_hours;

      await axios.post(`${API_BASE}/sim-trading/accounts`, payload);
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

  // 展开行渲染详细信息
  const expandedRowRender = (record) => {
    if (!record.screening_data) return null;
    const data = record.screening_data;
    return (
      <Descriptions size="small" column={4} bordered>
        <Descriptions.Item label="时间级别">
          <Tag color="purple">{data.timeframe || '-'}</Tag>
        </Descriptions.Item>
        <Descriptions.Item label="总分">{data.total_score?.toFixed(1)}</Descriptions.Item>
        <Descriptions.Item label="Beta分">{data.beta_score?.toFixed(1)}</Descriptions.Item>
        <Descriptions.Item label="成交量分">{data.volume_score?.toFixed(1)}</Descriptions.Item>
        <Descriptions.Item label="技术分">{data.technical_score?.toFixed(1)}</Descriptions.Item>
        <Descriptions.Item label="当前价格">${data.price?.toFixed(6)}</Descriptions.Item>
        <Descriptions.Item label="24h成交量">${data.volume_24h ? (data.volume_24h/1000000)?.toFixed(2) + 'M' : '-'}</Descriptions.Item>
        <Descriptions.Item label="5m涨跌">{data.change_5m?.toFixed(2) || '-'}%</Descriptions.Item>
        <Descriptions.Item label="15m涨跌">{data.change_15m?.toFixed(2) || '-'}%</Descriptions.Item>
        <Descriptions.Item label="1h涨跌">{data.change_1h?.toFixed(2) || '-'}%</Descriptions.Item>
        <Descriptions.Item label="MACD金叉">
          <Tag color={data.macd_golden_cross ? 'green' : 'default'}>
            {data.macd_golden_cross ? '是' : '否'}
          </Tag>
        </Descriptions.Item>
        <Descriptions.Item label="RSI">{data.rsi?.toFixed(1) || '-'}</Descriptions.Item>
        <Descriptions.Item label="成交量激增">
          <Tag color={data.volume_surge ? 'orange' : 'default'}>
            {data.volume_surge ? '是' : '否'}
          </Tag>
        </Descriptions.Item>
        <Descriptions.Item label="价格异动">
          <Tag color={data.price_anomaly ? 'red' : 'default'}>
            {data.price_anomaly ? '是' : '否'}
          </Tag>
        </Descriptions.Item>
        <Descriptions.Item label="仓位金额">${data.position_size_usdt?.toFixed(2) || '-'}</Descriptions.Item>
        <Descriptions.Item label="买入数量">{data.quantity?.toFixed(4) || '-'}</Descriptions.Item>
        {data.signals && (
          <Descriptions.Item label="技术信号" span={4}>
            {Object.entries(data.signals || {}).map(([key, val]) => (
              <Tag key={key} color={val ? 'blue' : 'default'} style={{marginBottom: 4}}>
                {key}: {val ? '✓' : '✗'}
              </Tag>
            ))}
          </Descriptions.Item>
        )}
      </Descriptions>
    );
  };

  const logColumns = [
    {
      title: '时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 160,
      render: (time) => new Date(time).toLocaleString('zh-CN')
    },
    {
      title: '操作',
      dataIndex: 'action',
      key: 'action',
      width: 80,
      render: (action) => {
        const actionMap = {
          'OPEN_POSITION': { text: '开仓', color: 'green' },
          'CLOSE_POSITION': { text: '平仓', color: 'red' },
          'PARTIAL_EXIT': { text: '部分平仓', color: 'orange' },
          'STOP_LOSS': { text: '止损', color: 'volcano' },
          'TAKE_PROFIT': { text: '止盈', color: 'cyan' },
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
      width: 110
    },
    {
      title: '总分',
      dataIndex: 'screening_score',
      key: 'screening_score',
      width: 60,
      render: (score) => score ? <span style={{fontWeight: score >= 75 ? 'bold' : 'normal', color: score >= 80 ? '#52c41a' : score >= 75 ? '#1890ff' : '#999'}}>{score.toFixed(1)}</span> : '-'
    },
    {
      title: '价格',
      dataIndex: ['screening_data', 'price'],
      key: 'price',
      width: 100,
      render: (price) => price ? `$${price.toFixed(6)}` : '-'
    },
    {
      title: '数量',
      dataIndex: ['screening_data', 'quantity'],
      key: 'quantity',
      width: 80,
      render: (qty) => qty ? qty.toFixed(2) : '-'
    },
    {
      title: '决策原因',
      dataIndex: 'reason',
      key: 'reason',
      ellipsis: true,
      render: (reason) => (
        <Tooltip title={reason}>
          <span>{reason}</span>
        </Tooltip>
      )
    },
    {
      title: '状态',
      dataIndex: 'success',
      key: 'success',
      width: 70,
      render: (success) => (
        <Tag color={success ? 'success' : 'error'}>
          {success ? '成功' : '失败'}
        </Tag>
      )
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
                    expandable={{
                      expandedRowRender,
                      rowExpandable: (record) => record.screening_data != null,
                    }}
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
        width={700}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreateAccount}
          initialValues={{
            initial_balance: 10000,
            max_positions: 5,
            position_size_pct: 2.0,
            entry_timeframe: '15m',
            entry_score_min: 75.0,
            entry_technical_min: 60.0,
            // Exit mode settings
            exit_mode: 'fixed',
            stop_loss_pct: 3.0,
            hard_stop_pct: 5.0,
            // ATR settings
            atr_stop_multiplier: 2.0,
            atr_tp_1: 2.5,
            atr_tp_2: 3.5,
            atr_tp_3: 5.0,
            // Fixed percentage TP
            take_profit_1: 6.0,
            take_profit_2: 10.0,
            take_profit_3: 15.0,
            require_macd_golden: true,
            require_volume_surge: false,
            trailing_stop_enabled: false,
            trailing_stop_pct: 2.0,
            max_holding_hours: 24
          }}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="account_name"
                label="账户名称"
                rules={[{ required: true, message: '请输入账户名称' }]}
              >
                <Input placeholder="例如: 保守策略A" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="initial_balance"
                label="初始资金 (USDT)"
                rules={[{ required: true, message: '请输入初始资金' }]}
              >
                <InputNumber min={1000} max={1000000} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="max_positions" label="最大持仓数">
                <InputNumber min={1} max={20} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="position_size_pct" label="单仓位资金占比 (%)">
                <InputNumber min={0.5} max={20} step={0.5} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Divider orientation="left">入场条件</Divider>

          <Row gutter={16}>
            <Col span={6}>
              <Form.Item name="entry_timeframe" label={
                <span>入场时间级别 <Tooltip title="使用该时间周期的筛选评分，扫描频率也跟随此设置"><InfoCircleOutlined /></Tooltip></span>
              }>
                <Select>
                  <Select.Option value="5m">5分钟</Select.Option>
                  <Select.Option value="15m">15分钟</Select.Option>
                  <Select.Option value="1h">1小时</Select.Option>
                  <Select.Option value="4h">4小时</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="entry_score_min" label="最低总分">
                <InputNumber min={0} max={100} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="entry_technical_min" label="最低技术分">
                <InputNumber min={0} max={100} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="max_holding_hours" label={
                <span>最大持仓时间 <Tooltip title="超过此时间自动平仓"><InfoCircleOutlined /></Tooltip></span>
              }>
                <InputNumber min={1} max={168} addonAfter="小时" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="require_macd_golden" valuePropName="checked" label={
                <span>要求MACD金叉 <Tooltip title="只有MACD金叉时才开仓"><InfoCircleOutlined /></Tooltip></span>
              }>
                <Switch checkedChildren="是" unCheckedChildren="否" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="require_volume_surge" valuePropName="checked" label={
                <span>要求成交量激增 <Tooltip title="只有成交量激增时才开仓"><InfoCircleOutlined /></Tooltip></span>
              }>
                <Switch checkedChildren="是" unCheckedChildren="否" />
              </Form.Item>
            </Col>
          </Row>

          <Divider orientation="left">止盈止损模式</Divider>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="exit_mode" label={
                <span>止损模式 <Tooltip title="Fixed: 固定百分比; ATR: 根据波动率动态调整"><InfoCircleOutlined /></Tooltip></span>
              }>
                <Select>
                  <Select.Option value="fixed">Fixed 固定百分比</Select.Option>
                  <Select.Option value="atr">ATR 动态波动率</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="hard_stop_pct" label={
                <span>保底止损 (%) <Tooltip title="无论ATR计算结果如何，止损不会低于此百分比"><InfoCircleOutlined /></Tooltip></span>
              }>
                <InputNumber min={1} max={20} step={0.5} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="stop_loss_pct" label="固定止损 (%)">
                <InputNumber min={0.5} max={20} step={0.5} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Divider orientation="left" style={{ fontSize: '12px', color: '#888' }}>ATR动态止损配置 (仅ATR模式生效)</Divider>

          <Row gutter={16}>
            <Col span={6}>
              <Form.Item name="atr_stop_multiplier" label={
                <span>止损ATR倍数 <Tooltip title="止损价 = 入场价 - (ATR × 倍数)"><InfoCircleOutlined /></Tooltip></span>
              }>
                <InputNumber min={0.5} max={5} step={0.5} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="atr_tp_1" label={
                <span>TP1 ATR倍数 <Tooltip title="止盈1 = 入场价 + (ATR × 倍数)"><InfoCircleOutlined /></Tooltip></span>
              }>
                <InputNumber min={1} max={10} step={0.5} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="atr_tp_2" label={
                <span>TP2 ATR倍数 <Tooltip title="止盈2 = 入场价 + (ATR × 倍数)"><InfoCircleOutlined /></Tooltip></span>
              }>
                <InputNumber min={1} max={15} step={0.5} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="atr_tp_3" label={
                <span>TP3 ATR倍数 <Tooltip title="止盈3 = 入场价 + (ATR × 倍数)"><InfoCircleOutlined /></Tooltip></span>
              }>
                <InputNumber min={1} max={20} step={0.5} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="trailing_stop_enabled" valuePropName="checked" label="启用追踪止损">
                <Switch checkedChildren="是" unCheckedChildren="否" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="trailing_stop_pct" label={
                <span>追踪止损 (%) <Tooltip title="从最高点回撤此比例触发止损"><InfoCircleOutlined /></Tooltip></span>
              }>
                <InputNumber min={0.5} max={10} step={0.5} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Divider orientation="left">固定百分比止盈 (仅Fixed模式生效)</Divider>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="take_profit_1" label={
                <span>止盈1 (%) <Tooltip title="到达后平仓1/3"><InfoCircleOutlined /></Tooltip></span>
              }>
                <InputNumber min={1} max={50} step={0.5} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="take_profit_2" label={
                <span>止盈2 (%) <Tooltip title="到达后再平仓1/3"><InfoCircleOutlined /></Tooltip></span>
              }>
                <InputNumber min={1} max={100} step={0.5} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="take_profit_3" label={
                <span>止盈3 (%) <Tooltip title="到达后全部平仓"><InfoCircleOutlined /></Tooltip></span>
              }>
                <InputNumber min={1} max={200} step={1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <div style={{ background: '#e6f7ff', padding: '12px', borderRadius: '4px', marginTop: '8px', border: '1px solid #91d5ff' }}>
            <small style={{ color: '#0050b3' }}>
              <strong>ATR模式说明：</strong> ATR(平均真实波幅)根据币种波动率动态计算止盈止损价位。
              高波动币种会有更宽的止损空间，低波动币种则止损更紧。保底止损确保最大亏损不超过设定百分比。
            </small>
          </div>
        </Form>
      </Modal>
    </div>
  );
};

export default SimTradingPanel;
