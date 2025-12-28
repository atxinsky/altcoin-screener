import React, { useEffect, useRef, useState } from 'react'
import { Spin, Select, Space, Tag, message, InputNumber, Tooltip, Button, Popover } from 'antd'
import { SettingOutlined } from '@ant-design/icons'
import { getHistoricalData, getIndicators } from '../services/api'

const { Option } = Select

const KlineChart = ({ symbol, initialTimeframe = '5m' }) => {
  const chartRef = useRef(null)
  const chartInstance = useRef(null)
  const [loading, setLoading] = useState(true)
  const [timeframe, setTimeframe] = useState(initialTimeframe)
  const [anomalyCount, setAnomalyCount] = useState(0)
  const [currentPrice, setCurrentPrice] = useState(0)
  const [hoverPrice, setHoverPrice] = useState(null)
  const [currentCandle, setCurrentCandle] = useState(null)

  // 均线参数设置
  const [maParams, setMaParams] = useState([5, 10, 20, 60])
  const [emaParams, setEmaParams] = useState([7, 14, 30])
  const [settingsVisible, setSettingsVisible] = useState(false)

  useEffect(() => {
    // Dynamically import klinecharts
    const initChart = async () => {
      try {
        const klinecharts = await import('klinecharts')

        if (chartRef.current && !chartInstance.current) {
          // 初始化图表
          chartInstance.current = klinecharts.init(chartRef.current)

          // 设置十字光标监听
          chartInstance.current.subscribeAction('onCrosshairChange', (data) => {
            if (data && data.dataIndex !== undefined && data.kLineData) {
              setHoverPrice(data.kLineData.close)
              setCurrentCandle(data.kLineData)
            } else {
              setHoverPrice(null)
              setCurrentCandle(null)
            }
          })

          // Load initial data
          loadChartData()
        }

        return () => {
          if (chartInstance.current) {
            klinecharts.dispose(chartRef.current)
            chartInstance.current = null
          }
        }
      } catch (error) {
        console.error('Failed to load klinecharts:', error)
        message.error('图表库加载失败')
        setLoading(false)
      }
    }

    initChart()
  }, [])

  useEffect(() => {
    if (chartInstance.current) {
      loadChartData()
    }
  }, [symbol, timeframe])

  useEffect(() => {
    if (chartInstance.current) {
      updateIndicators()
    }
  }, [maParams, emaParams])

  const updateIndicators = () => {
    if (!chartInstance.current) return

    // 移除所有旧指标
    chartInstance.current.removeIndicator({ name: 'MA' })
    chartInstance.current.removeIndicator({ name: 'EMA' })

    // 添加MA指标
    chartInstance.current.createIndicator('MA', false, {
      id: 'candle_pane',
      calcParams: maParams
    })

    // 添加EMA指标
    chartInstance.current.createIndicator('EMA', false, {
      id: 'candle_pane',
      calcParams: emaParams
    })

    // 添加成交量指标
    chartInstance.current.createIndicator('VOL')
  }

  const loadChartData = async () => {
    setLoading(true)
    try {
      // Fetch historical K-line data
      const response = await getHistoricalData(symbol, timeframe, 7)

      if (response.data && response.data.length > 0) {
        // Transform data to klinecharts format
        const chartData = response.data.map(item => ({
          timestamp: new Date(item.timestamp).getTime(),
          open: item.open,
          high: item.high,
          low: item.low,
          close: item.close,
          volume: item.volume
        }))

        // Apply data to chart
        if (chartInstance.current) {
          chartInstance.current.applyNewData(chartData)

          // 设置当前价格
          const lastCandle = chartData[chartData.length - 1]
          setCurrentPrice(lastCandle.close)

          // 更新指标
          updateIndicators()

          // 自动缩放Y轴以适应数据
          chartInstance.current.zoomAtDataIndex(chartData.length - 1, 1)
        }

        // Get indicators data for anomaly detection
        try {
          const indicatorsResponse = await getIndicators(symbol, timeframe)
          if (indicatorsResponse.anomaly_count !== undefined) {
            setAnomalyCount(indicatorsResponse.anomaly_count)
          }
        } catch (err) {
          console.error('Failed to get indicators:', err)
        }
      } else {
        message.warning('暂无K线数据')
      }
    } catch (error) {
      console.error('Failed to load chart data:', error)
      message.error('加载图表数据失败: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  const handleTimeframeChange = (value) => {
    setTimeframe(value)
  }

  // 计算涨跌幅
  const calculateChangePercent = (price1, price2) => {
    if (!price1 || !price2) return 0
    return ((price2 - price1) / price1 * 100).toFixed(2)
  }

  // 计算振幅
  const calculateAmplitude = (candle) => {
    if (!candle) return 0
    return ((candle.high - candle.low) / candle.low * 100).toFixed(2)
  }

  // K线涨跌幅
  const candleChangePercent = currentCandle
    ? calculateChangePercent(currentCandle.open, currentCandle.close)
    : 0

  // 当前价格与鼠标位置涨跌幅
  const hoverChangePercent = hoverPrice
    ? calculateChangePercent(currentPrice, hoverPrice)
    : 0

  // 振幅
  const amplitude = currentCandle ? calculateAmplitude(currentCandle) : 0

  const settingsContent = (
    <div style={{ width: 300 }}>
      <div style={{ marginBottom: 16 }}>
        <h4>MA均线参数</h4>
        <Space>
          {maParams.map((param, index) => (
            <InputNumber
              key={`ma-${index}`}
              size="small"
              min={1}
              max={200}
              value={param}
              onChange={(value) => {
                const newParams = [...maParams]
                newParams[index] = value
                setMaParams(newParams)
              }}
              style={{ width: 60 }}
            />
          ))}
        </Space>
        <Button
          size="small"
          style={{ marginLeft: 8 }}
          onClick={() => setMaParams([...maParams, 30])}
        >
          +
        </Button>
      </div>

      <div>
        <h4>EMA均线参数</h4>
        <Space>
          {emaParams.map((param, index) => (
            <InputNumber
              key={`ema-${index}`}
              size="small"
              min={1}
              max={200}
              value={param}
              onChange={(value) => {
                const newParams = [...emaParams]
                newParams[index] = value
                setEmaParams(newParams)
              }}
              style={{ width: 60 }}
            />
          ))}
        </Space>
        <Button
          size="small"
          style={{ marginLeft: 8 }}
          onClick={() => setEmaParams([...emaParams, 20])}
        >
          +
        </Button>
      </div>
    </div>
  )

  return (
    <div style={{ width: '100%', height: '100%' }}>
      <Space style={{ marginBottom: 16, width: '100%', justifyContent: 'space-between', flexWrap: 'wrap' }}>
        <Space wrap>
          <span style={{ fontWeight: 'bold', fontSize: '16px' }}>{symbol}</span>
          <Select
            value={timeframe}
            onChange={handleTimeframeChange}
            style={{ width: 100 }}
            size="small"
          >
            <Option value="1m">1分钟</Option>
            <Option value="5m">5分钟</Option>
            <Option value="15m">15分钟</Option>
            <Option value="30m">30分钟</Option>
            <Option value="1h">1小时</Option>
            <Option value="4h">4小时</Option>
            <Option value="1d">1天</Option>
          </Select>

          {anomalyCount > 0 && (
            <Tag color="red">检测到 {anomalyCount} 个价格异动点</Tag>
          )}
        </Space>

        <Space wrap>
          {currentPrice > 0 && (
            <Tag color="blue">当前价: ${currentPrice.toFixed(6)}</Tag>
          )}

          {hoverPrice && (
            <Tag color={hoverChangePercent >= 0 ? 'green' : 'red'}>
              相对涨跌: {hoverChangePercent >= 0 ? '+' : ''}{hoverChangePercent}%
            </Tag>
          )}

          {currentCandle && (
            <>
              <Tag color={candleChangePercent >= 0 ? 'green' : 'red'}>
                K线涨跌: {candleChangePercent >= 0 ? '+' : ''}{candleChangePercent}%
              </Tag>
              <Tag color="purple">
                振幅: {amplitude}%
              </Tag>
            </>
          )}

          <Popover
            content={settingsContent}
            title="均线参数设置"
            trigger="click"
            open={settingsVisible}
            onOpenChange={setSettingsVisible}
          >
            <Button size="small" icon={<SettingOutlined />}>
              均线设置
            </Button>
          </Popover>
        </Space>
      </Space>

      <Spin spinning={loading}>
        <div
          ref={chartRef}
          style={{
            width: '100%',
            height: '600px'
          }}
        />
      </Spin>
    </div>
  )
}

export default KlineChart
