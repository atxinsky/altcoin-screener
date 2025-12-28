import React, { useEffect, useRef, useState } from 'react'
import { init, dispose } from 'klinecharts'
import { Spin, Select, Space, Tag, message } from 'antd'
import { getHistoricalData, getIndicators } from '../services/api'

const { Option } = Select

const KlineChart = ({ symbol, initialTimeframe = '5m', onClose }) => {
  const chartRef = useRef(null)
  const chartInstance = useRef(null)
  const [loading, setLoading] = useState(true)
  const [timeframe, setTimeframe] = useState(initialTimeframe)
  const [anomalyCount, setAnomalyCount] = useState(0)

  useEffect(() => {
    // Initialize chart
    if (chartRef.current && !chartInstance.current) {
      chartInstance.current = init(chartRef.current, {
        grid: {
          show: true,
          horizontal: {
            show: true,
            color: '#393939',
            style: 'dashed'
          },
          vertical: {
            show: true,
            color: '#393939',
            style: 'dashed'
          }
        },
        candle: {
          type: 'candle_solid',
          priceMark: {
            show: true,
            high: {
              show: true,
              color: '#26A69A',
              textMargin: 5,
              textSize: 10
            },
            low: {
              show: true,
              color: '#EF5350',
              textMargin: 5,
              textSize: 10
            }
          },
          tooltip: {
            showRule: 'always',
            showType: 'standard',
            labels: ['时间', '开', '收', '高', '低', '成交量'],
            text: {
              size: 12,
              color: '#D9D9D9'
            }
          }
        },
        indicator: {
          tooltip: {
            showRule: 'always',
            showType: 'standard'
          }
        }
      })

      // Create main pane indicators
      chartInstance.current.createIndicator('MA', false, { id: 'candle_pane' })
      chartInstance.current.createIndicator('EMA', false, { id: 'candle_pane' })

      // Create sub panes for other indicators
      chartInstance.current.createIndicator('VOL')
      chartInstance.current.createIndicator('MACD')
      chartInstance.current.createIndicator('RSI')
    }

    return () => {
      if (chartInstance.current) {
        dispose(chartRef.current)
        chartInstance.current = null
      }
    }
  }, [])

  useEffect(() => {
    loadChartData()
  }, [symbol, timeframe])

  const loadChartData = async () => {
    if (!chartInstance.current) return

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
        chartInstance.current.applyNewData(chartData)

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
      message.error('加载图表数据失败')
    } finally {
      setLoading(false)
    }
  }

  const handleTimeframeChange = (value) => {
    setTimeframe(value)
  }

  return (
    <div style={{ width: '100%', height: '100%' }}>
      <Space style={{ marginBottom: 16, width: '100%', justifyContent: 'space-between' }}>
        <Space>
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
        </Space>
        {anomalyCount > 0 && (
          <Tag color="red">检测到 {anomalyCount} 个价格异动点</Tag>
        )}
      </Space>

      <Spin spinning={loading}>
        <div
          ref={chartRef}
          style={{
            width: '100%',
            height: '600px',
            backgroundColor: '#1e1e1e'
          }}
        />
      </Spin>
    </div>
  )
}

export default KlineChart
