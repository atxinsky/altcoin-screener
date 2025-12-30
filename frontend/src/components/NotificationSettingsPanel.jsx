import React, { useState, useEffect } from 'react'
import {
  Card,
  Form,
  Switch,
  InputNumber,
  Slider,
  Button,
  Space,
  message,
  Divider,
  Row,
  Col,
  Statistic,
  Tag,
  Tooltip,
  Alert
} from 'antd'
import {
  MailOutlined,
  BellOutlined,
  ClockCircleOutlined,
  SettingOutlined,
  ReloadOutlined,
  SendOutlined,
  MoonOutlined
} from '@ant-design/icons'
import axios from 'axios'

const NotificationSettingsPanel = () => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)
  const [settings, setSettings] = useState(null)

  useEffect(() => {
    loadSettings()
  }, [])

  const loadSettings = async () => {
    setLoading(true)
    try {
      const response = await axios.get('/api/notification-settings')
      if (response.data.success) {
        setSettings(response.data.settings)
        form.setFieldsValue(response.data.settings)
      }
    } catch (error) {
      message.error('加载通知设置失败: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async (values) => {
    setSaving(true)
    try {
      const response = await axios.patch('/api/notification-settings', values)
      if (response.data.success) {
        message.success('设置已保存')
        setSettings(response.data.settings)
      }
    } catch (error) {
      message.error('保存失败: ' + error.message)
    } finally {
      setSaving(false)
    }
  }

  const handleTest = async () => {
    setTesting(true)
    try {
      const response = await axios.post('/api/notification-settings/test')
      if (response.data.success) {
        message.success('测试通知已发送')
      } else {
        message.warning(response.data.message)
      }
    } catch (error) {
      message.error('发送测试通知失败: ' + error.message)
    } finally {
      setTesting(false)
    }
  }

  const handleResetDailyCount = async () => {
    try {
      await axios.post('/api/notification-settings/reset-daily-count')
      message.success('每日计数已重置')
      loadSettings()
    } catch (error) {
      message.error('重置失败: ' + error.message)
    }
  }

  return (
    <Card
      title={
        <Space>
          <SettingOutlined />
          通知设置
        </Space>
      }
      extra={
        <Space>
          <Button
            icon={<SendOutlined />}
            onClick={handleTest}
            loading={testing}
          >
            发送测试通知
          </Button>
          <Button
            icon={<ReloadOutlined />}
            onClick={loadSettings}
            loading={loading}
          >
            刷新
          </Button>
        </Space>
      }
      loading={loading}
    >
      {settings && (
        <Alert
          message={
            <Space>
              <span>今日已发送: <Tag color="blue">{settings.daily_count || 0} / {settings.daily_limit}</Tag></span>
              {settings.last_notification_time && (
                <span>上次通知: <Tag>{new Date(settings.last_notification_time).toLocaleString('zh-CN')}</Tag></span>
              )}
              <Button size="small" onClick={handleResetDailyCount}>重置计数</Button>
            </Space>
          }
          type="info"
          style={{ marginBottom: 16 }}
        />
      )}

      <Form
        form={form}
        layout="vertical"
        onFinish={handleSave}
        initialValues={{
          email_enabled: true,
          telegram_enabled: true,
          min_interval_minutes: 30,
          daily_limit: 10,
          min_score_threshold: 75,
          notify_top_n: 5,
          notify_high_score: true,
          notify_new_signals: true,
          notify_position_updates: true,
          quiet_hours_enabled: true,
          quiet_hours_start: 22,
          quiet_hours_end: 7
        }}
      >
        <Divider orientation="left">
          <Space><BellOutlined /> 通知渠道</Space>
        </Divider>

        <Row gutter={24}>
          <Col span={12}>
            <Form.Item
              name="email_enabled"
              label={<Space><MailOutlined /> 邮件通知</Space>}
              valuePropName="checked"
            >
              <Switch checkedChildren="开启" unCheckedChildren="关闭" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="telegram_enabled"
              label={<Space><SendOutlined /> Telegram通知</Space>}
              valuePropName="checked"
            >
              <Switch checkedChildren="开启" unCheckedChildren="关闭" />
            </Form.Item>
          </Col>
        </Row>

        <Divider orientation="left">
          <Space><ClockCircleOutlined /> 频率控制</Space>
        </Divider>

        <Row gutter={24}>
          <Col span={12}>
            <Form.Item
              name="min_interval_minutes"
              label="最小通知间隔（分钟）"
              tooltip="两次通知之间的最小间隔时间"
            >
              <InputNumber
                min={5}
                max={1440}
                style={{ width: '100%' }}
                addonAfter="分钟"
              />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="daily_limit"
              label="每日通知上限"
              tooltip="每天最多发送多少次通知"
            >
              <InputNumber
                min={1}
                max={100}
                style={{ width: '100%' }}
                addonAfter="次"
              />
            </Form.Item>
          </Col>
        </Row>

        <Divider orientation="left">
          <Space><MoonOutlined /> 静默时段（北京时间）</Space>
        </Divider>

        <Row gutter={24}>
          <Col span={8}>
            <Form.Item
              name="quiet_hours_enabled"
              label="启用静默时段"
              valuePropName="checked"
            >
              <Switch checkedChildren="开启" unCheckedChildren="关闭" />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item
              name="quiet_hours_start"
              label="静默开始时间"
              tooltip="从几点开始不发送通知"
            >
              <InputNumber
                min={0}
                max={23}
                style={{ width: '100%' }}
                addonAfter="点"
              />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item
              name="quiet_hours_end"
              label="静默结束时间"
              tooltip="几点结束静默"
            >
              <InputNumber
                min={0}
                max={23}
                style={{ width: '100%' }}
                addonAfter="点"
              />
            </Form.Item>
          </Col>
        </Row>

        <Divider orientation="left">
          <Space><SettingOutlined /> 通知内容</Space>
        </Divider>

        <Row gutter={24}>
          <Col span={12}>
            <Form.Item
              name="min_score_threshold"
              label="最低分数阈值"
              tooltip="只有分数高于此值的机会才会触发通知"
            >
              <Slider
                min={50}
                max={95}
                marks={{
                  50: '50',
                  60: '60',
                  70: '70',
                  75: '75',
                  80: '80',
                  90: '90'
                }}
              />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="notify_top_n"
              label="每次通知前N个机会"
              tooltip="每次通知最多包含多少个高分机会"
            >
              <InputNumber
                min={1}
                max={20}
                style={{ width: '100%' }}
                addonAfter="个"
              />
            </Form.Item>
          </Col>
        </Row>

        <Divider orientation="left">
          <Space><BellOutlined /> 通知类型</Space>
        </Divider>

        <Row gutter={24}>
          <Col span={8}>
            <Form.Item
              name="notify_high_score"
              label="高分机会通知"
              valuePropName="checked"
              tooltip="发现高分机会时发送通知"
            >
              <Switch checkedChildren="开启" unCheckedChildren="关闭" />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item
              name="notify_new_signals"
              label="新信号通知"
              valuePropName="checked"
              tooltip="出现新的技术信号时通知"
            >
              <Switch checkedChildren="开启" unCheckedChildren="关闭" />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item
              name="notify_position_updates"
              label="持仓更新通知"
              valuePropName="checked"
              tooltip="模拟交易开仓/平仓时通知"
            >
              <Switch checkedChildren="开启" unCheckedChildren="关闭" />
            </Form.Item>
          </Col>
        </Row>

        <Divider />

        <Form.Item>
          <Button
            type="primary"
            htmlType="submit"
            loading={saving}
            size="large"
            icon={<SettingOutlined />}
            block
          >
            保存设置
          </Button>
        </Form.Item>
      </Form>
    </Card>
  )
}

export default NotificationSettingsPanel
