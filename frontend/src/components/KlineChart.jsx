import React, { useEffect, useRef, useState } from 'react'
import { RefreshCw } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { cn } from '@/lib/utils'
import { getHistoricalData, getIndicators } from '@/services/api'

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
          chartInstance.current = klinecharts.init(chartRef.current, {
            timezone: 'Asia/Shanghai',
            locale: 'zh-CN',
            styles: {
              grid: {
                show: true,
                horizontal: {
                  color: 'rgba(255, 255, 255, 0.05)'
                },
                vertical: {
                  color: 'rgba(255, 255, 255, 0.05)'
                }
              },
              candle: {
                bar: {
                  upColor: '#6Ec85c',
                  downColor: '#e40046',
                  upBorderColor: '#6Ec85c',
                  downBorderColor: '#e40046',
                  upWickColor: '#6Ec85c',
                  downWickColor: '#e40046'
                },
                priceMark: {
                  show: true,
                  high: { color: '#6Ec85c' },
                  low: { color: '#e40046' },
                  last: {
                    show: true,
                    upColor: '#6Ec85c',
                    downColor: '#e40046',
                    line: { show: true }
                  }
                }
              },
              indicator: {
                bars: [
                  { upColor: 'rgba(110, 200, 92, 0.6)', downColor: 'rgba(228, 0, 70, 0.6)' }
                ],
                lines: [
                  { color: '#D4A0FF' },
                  { color: '#FF5300' },
                  { color: '#6Ec85c' },
                  { color: '#00D4FF' }
                ]
              },
              xAxis: {
                axisLine: { color: 'rgba(255, 255, 255, 0.1)' },
                tickLine: { color: 'rgba(255, 255, 255, 0.1)' },
                tickText: { color: 'rgba(255, 255, 255, 0.5)' }
              },
              yAxis: {
                axisLine: { color: 'rgba(255, 255, 255, 0.1)' },
                tickLine: { color: 'rgba(255, 255, 255, 0.1)' },
                tickText: { color: 'rgba(255, 255, 255, 0.5)' }
              },
              crosshair: {
                show: true,
                horizontal: {
                  line: { color: '#D4A0FF', style: 'dashed' },
                  text: { color: '#000', backgroundColor: '#D4A0FF' }
                },
                vertical: {
                  line: { color: '#D4A0FF', style: 'dashed' },
                  text: { color: '#000', backgroundColor: '#D4A0FF' }
                }
              },
              separator: {
                color: 'rgba(255, 255, 255, 0.1)'
              }
            }
          })

          chartInstance.current.setTimezone('Asia/Shanghai')

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

          if (!indicatorsCreated.current) {
            chartInstance.current.createIndicator('VOL')
            chartInstance.current.createIndicator('EMA', false, {
              id: 'candle_pane',
              calcParams: [7, 14, 30, 52]
            })
            chartInstance.current.createIndicator('MACD')
            indicatorsCreated.current = true
          }

          loadChartData()
        }
      } catch (error) {
        console.error('Failed to load klinecharts:', error)
        if (mounted) {
          setLoading(false)
        }
      }
    }

    initChart()

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
  }, [])

  useEffect(() => {
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
          chartInstance.current.applyNewData(chartData)

          const lastCandle = chartData[chartData.length - 1]
          setCurrentPrice(lastCandle.close)

          setTimeout(() => {
            if (chartInstance.current) {
              chartInstance.current.scrollToRealTime()
              chartInstance.current.setZoomEnabled(true)
              chartInstance.current.setPriceVolumePrecision(6, 2)
            }
          }, 100)
        }

        try {
          const indicatorsResponse = await getIndicators(symbol, timeframe)
          if (indicatorsResponse.anomaly_count !== undefined) {
            setAnomalyCount(indicatorsResponse.anomaly_count)
          }
        } catch (err) {
          console.error('Failed to get indicators:', err)
        }
      }
    } catch (error) {
      console.error('Failed to load chart data:', error)
    } finally {
      setLoading(false)
    }
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

  const timeframeOptions = [
    { value: '1m', label: '1M' },
    { value: '5m', label: '5M' },
    { value: '15m', label: '15M' },
    { value: '30m', label: '30M' },
    { value: '1h', label: '1H' },
    { value: '4h', label: '4H' },
    { value: '1d', label: '1D' },
  ]

  return (
    <div className="w-full h-full">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
        <div className="flex items-center gap-3">
          <span className="text-lg font-bold font-mono">{symbol}</span>
          <Select value={timeframe} onValueChange={setTimeframe}>
            <SelectTrigger className="w-24 h-8">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {timeframeOptions.map(opt => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          {anomalyCount > 0 && (
            <Badge variant="destructive">
              {anomalyCount} ANOMALIES
            </Badge>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {currentPrice > 0 && (
            <Badge variant="purple" className="font-mono">
              ${currentPrice.toFixed(6)}
            </Badge>
          )}

          {hoverPrice && (
            <Badge variant={hoverChangePercent >= 0 ? 'success' : 'destructive'} className="font-mono">
              {hoverChangePercent >= 0 ? '+' : ''}{hoverChangePercent}%
            </Badge>
          )}

          {currentCandle && (
            <>
              <Badge variant={candleChangePercent >= 0 ? 'success' : 'destructive'} className="font-mono">
                K: {candleChangePercent >= 0 ? '+' : ''}{candleChangePercent}%
              </Badge>
              <Badge variant="outline" className="font-mono">
                AMP: {amplitude}%
              </Badge>
            </>
          )}
        </div>
      </div>

      {/* Chart Container */}
      <div className="relative border-2 border-border bg-background">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-background/80 z-10">
            <RefreshCw className="w-6 h-6 animate-spin text-primary" />
          </div>
        )}
        <div
          ref={chartRef}
          className="w-full"
          style={{ height: '500px' }}
        />
      </div>
    </div>
  )
}

export default KlineChart
