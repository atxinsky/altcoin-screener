import React, { useState } from 'react'
import { Button, Select, InputNumber, Switch, Space, message, Form, Row, Col } from 'antd'
import { SearchOutlined, BellOutlined } from '@ant-design/icons'
import { screenAltcoins } from '../services/api'

const { Option } = Select

const ScreeningPanel = ({ onStatsUpdate, onResultsUpdate }) => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)

  const handleScreen = async () => {
    try {
      const values = await form.validateFields()
      setLoading(true)

      const params = {
        timeframe: values.timeframe,
        min_volume: values.minVolume,
        min_price_change: values.minPriceChange,
        send_notification: values.sendNotification,
      }

      const result = await screenAltcoins(params)

      message.success(`筛选完成! 发现 ${result.count} 个机会`)

      if (onResultsUpdate) {
        onResultsUpdate(result.results)
      }

      if (onStatsUpdate) {
        onStatsUpdate()
      }
    } catch (error) {
      console.error('Screening error:', error)
      message.error('筛选失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Form
      form={form}
      layout="vertical"
      initialValues={{
        timeframe: '5m',
        minVolume: 1000000,
        minPriceChange: 2.0,
        sendNotification: false,
      }}
    >
      <Row gutter={16}>
        <Col xs={24} sm={12} md={6}>
          <Form.Item
            label="时间周期"
            name="timeframe"
            rules={[{ required: true, message: '请选择时间周期' }]}
          >
            <Select>
              <Option value="5m">5分钟</Option>
              <Option value="15m">15分钟</Option>
              <Option value="1h">1小时</Option>
              <Option value="4h">4小时</Option>
            </Select>
          </Form.Item>
        </Col>

        <Col xs={24} sm={12} md={6}>
          <Form.Item
            label="最小成交量 (USD)"
            name="minVolume"
            rules={[{ required: true, message: '请输入最小成交量' }]}
          >
            <InputNumber
              style={{ width: '100%' }}
              min={0}
              step={100000}
              formatter={value => `$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
              parser={value => value.replace(/\$\s?|(,*)/g, '')}
            />
          </Form.Item>
        </Col>

        <Col xs={24} sm={12} md={6}>
          <Form.Item
            label="最小价格变动 (%)"
            name="minPriceChange"
            rules={[{ required: true, message: '请输入最小价格变动' }]}
          >
            <InputNumber
              style={{ width: '100%' }}
              min={0}
              max={100}
              step={0.5}
              formatter={value => `${value}%`}
              parser={value => value.replace('%', '')}
            />
          </Form.Item>
        </Col>

        <Col xs={24} sm={12} md={6}>
          <Form.Item label="发送通知" name="sendNotification" valuePropName="checked">
            <Switch
              checkedChildren={<BellOutlined />}
              unCheckedChildren={<BellOutlined />}
            />
          </Form.Item>
        </Col>
      </Row>

      <Form.Item>
        <Button
          type="primary"
          size="large"
          icon={<SearchOutlined />}
          onClick={handleScreen}
          loading={loading}
          block
        >
          开始筛选
        </Button>
      </Form.Item>
    </Form>
  )
}

export default ScreeningPanel
