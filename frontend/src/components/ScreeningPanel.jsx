import React, { useState } from 'react'
import { Button, Select, InputNumber, Switch, Space, message, Form, Row, Col, Radio } from 'antd'
import { SearchOutlined, BellOutlined, RiseOutlined } from '@ant-design/icons'
import { screenAltcoins } from '../services/api'
import axios from 'axios'

const { Option } = Select

const ScreeningPanel = ({ onStatsUpdate, onResultsUpdate }) => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [screenMode, setScreenMode] = useState('regular')

  const handleScreen = async () => {
    try {
      const values = await form.validateFields()
      setLoading(true)

      let result

      if (screenMode === 'gainers') {
        // 涨幅排名模式
        const response = await axios.get('/api/top-gainers', {
          params: {
            timeframe: values.timeframe,
            limit: 20
          }
        })
        result = response.data
      } else {
        // 常规筛选模式
        const params = {
          timeframe: values.timeframe,
          min_volume: values.minVolume,
          min_price_change: values.minPriceChange,
          send_notification: values.sendNotification,
        }
        result = await screenAltcoins(params)
      }

      message.success(`筛选完成! 发现 ${result.count || result.results?.length || 0} 个机会`)

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
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={24}>
          <Space>
            <span style={{ fontWeight: 'bold' }}>筛选模式:</span>
            <Radio.Group value={screenMode} onChange={(e) => setScreenMode(e.target.value)}>
              <Radio.Button value="regular">
                <SearchOutlined /> 常规筛选
              </Radio.Button>
              <Radio.Button value="gainers">
                <RiseOutlined /> 涨幅排名
              </Radio.Button>
            </Radio.Group>
          </Space>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col xs={24} sm={12} md={6}>
          <Form.Item
            label={screenMode === 'gainers' ? '涨幅计算周期' : '时间周期'}
            name="timeframe"
            rules={[{ required: true, message: '请选择时间周期' }]}
            tooltip={screenMode === 'gainers' ? '选择计算涨幅的时间周期（如5分钟涨幅、15分钟涨幅）' : null}
          >
            <Select>
              <Option value="5m">5分钟{screenMode === 'gainers' ? '涨幅' : ''}</Option>
              <Option value="15m">15分钟{screenMode === 'gainers' ? '涨幅' : ''}</Option>
              <Option value="1h">1小时{screenMode === 'gainers' ? '涨幅' : ''}</Option>
              {screenMode === 'regular' && <Option value="4h">4小时</Option>}
            </Select>
          </Form.Item>
        </Col>

        {screenMode === 'regular' && (
          <>
            <Col xs={24} sm={12} md={6}>
              <Form.Item
                label="最小成交量 (USD)"
                name="minVolume"
                rules={[{ required: screenMode === 'regular', message: '请输入最小成交量' }]}
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
                rules={[{ required: screenMode === 'regular', message: '请输入最小价格变动' }]}
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
          </>
        )}
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
