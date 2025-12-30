import React, { useEffect, useRef, useState } from 'react'
import { Spin, Select, Space, Tag, message } from 'antd'
import { getHistoricalData, getIndicators } from '../services/api'

const { Option } = Select

const KlineChart = ({ symbol, initialTimeframe = '5m' }) => {
  const chartRef = useRef(null)
  const chartInstance = useRef(null)
  const indicatorsCreated = useRef(false)
  const [loading, setLoading] = useState(true)
  const [timeframe, setTimeframe] = useState(initialTimeframe)
  const [anomalyCount, setAnomalyCount] = useState(0)
  const [currentPrice, setCurrentPrice] = useState(0)
  const [hoverPrice, setHoverPrice] = useState(null)
  const [currentCandle, setCurrentCandle] = useState(null)

  useEffect(() => {
    let mounted = true

    const initChart = async () => {
      try {
        const klinecharts = await import('klinecharts')

        if (chartRef.current && !chartInstance.current && mounted) {
          // 创建图表实例（只创建一次）
          chartInstance.current = klinecharts.init(chartRef.current, {
            timezone: 'Asia/Shanghai',  // 设置为北京时间 (UTC+8)
            locale: 'zh-CN'
          })

          // 再次确保时区设置生效
          chartInstance.current.setTimezone('Asia/Shanghai')

          // 设置十字光标监听
          chartInstance.current.subscribeAction('onCrosshairChange', (data) => {
            if (!mounted) return
            if (data && data.dataIndex !== undefined && data.kLineData) {
              setHoverPrice(data.kLineData.close)
              setCurrentCandle(data.kLineData)
            } else {
              setHoverPrice(null)
              setCurrentCandle(null)
            }
          })

          // 只在第一次创建时添加指标
          if (!indicatorsCreated.current) {
            // VOL指标
            chartInstance.current.createIndicator('VOL')

            // EMA指标 - 固定参数
            chartInstance.current.createIndicator('EMA', false, {
              id: 'candle_pane',
              calcParams: [7, 14, 30, 52]
            })

            // MACD指标
            chartInstance.current.createIndicator('MACD')

            indicatorsCreated.current = true
          }

          // 加载初始数据
          loadChartData()
        }
      } catch (error) {
        console.error('Failed to load klinecharts:', error)
        if (mounted) {
          message.error('图表库加载失败')
          setLoading(false)
        }
      }
    }

    initChart()

    // 清理函数
    return () => {
      mounted = false
      if (chartInstance.current) {
        try {
          chartInstance.current.dispose()
        } catch (e) {
          console.error('Error disposing chart:', e)
        }
        chartInstance.current = null
        indicatorsCreated.current = false
      }
    }
  }, []) // 空依赖数组，只在mount时执行

  useEffect(() => {
    // 当symbol或timeframe变化时，只更新数据，不重建图表
    if (chartInstance.current) {
      loadChartData()
    }
  }, [symbol, timeframe])

  const loadChartData = async () => {
    setLoading(true)
    try {
      const response = await getHistoricalData(symbol, timeframe, 7)

      if (response.data && response.data.length > 0) {
        const chartData = response.data.map(item => {
          // 后端返回的是 UTC 时间，需要加 'Z' 后缀确保正确解析
          let ts = item.timestamp
          if (!ts.endsWith('Z') && !ts.includes('+')) {
            ts = ts + 'Z'
          }
          return {
            timestamp: new Date(ts).getTime(),
            open: item.open,
            high: item.high,
            low: item.low,
            close: item.close,
            volume: item.volume
          }
        })

        if (chartInstance.current) {
          // 使用applyNewData更新数据，不重新创建指标
          chartInstance.current.applyNewData(chartData)

          const lastCandle = chartData[chartData.length - 1]
          setCurrentPrice(lastCandle.close)

          // 自动缩放
          setTimeout(() => {
            if (chartInstance.current) {
              chartInstance.current.scrollToRealTime()
              chartInstance.current.setZoomEnabled(true)
              chartInstance.current.setPriceVolumePrecision(6, 2)
            }
          }, 100)
        }

        // 获取异常点数量
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

      if (error.response && error.response.status === 404) {
        message.warning(`${symbol} 可能已从币安下架，无法获取K线数据`)
      } else {
        message.error('加载图表数据失败: ' + error.message)
      }
    } finally {
      setLoading(false)
    }
  }

  const handleTimeframeChange = (value) => {
    setTimeframe(value)
  }

  const calculateChangePercent = (price1, price2) => {
    if (!price1 || !price2) return 0
    return ((price2 - price1) / price1 * 100).toFixed(2)
  }

  const calculateAmplitude = (candle) => {
    if (!candle) return 0
    return ((candle.high - candle.low) / candle.low * 100).toFixed(2)
  }

  const candleChangePercent = currentCandle
    ? calculateChangePercent(currentCandle.open, currentCandle.close)
    : 0

  const hoverChangePercent = hoverPrice
    ? calculateChangePercent(currentPrice, hoverPrice)
    : 0

  const amplitude = currentCandle ? calculateAmplitude(currentCandle) : 0

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
