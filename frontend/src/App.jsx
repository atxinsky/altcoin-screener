import React, { useState, useEffect } from 'react'
import { Layout, Typography, Space, Card, Row, Col, Spin, Menu } from 'antd'
import { RocketOutlined, LineChartOutlined, BarChartOutlined, ThunderboltOutlined, SettingOutlined } from '@ant-design/icons'
import ScreeningPanel from './components/ScreeningPanel'
import ResultsTable from './components/ResultsTable'
import MarketOverview from './components/MarketOverview'
import StatsPanel from './components/StatsPanel'
import TradingPanel from './components/TradingPanel'
import HistoricalRankings from './components/HistoricalRankings'
import SimTradingPanel from './components/SimTradingPanel'
import NotificationSettingsPanel from './components/NotificationSettingsPanel'
import { getMarketOverview, getStats } from './services/api'

const { Header, Content } = Layout
const { Title } = Typography

function App() {
  const [marketData, setMarketData] = useState(null)
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [currentView, setCurrentView] = useState('screener')
  const [screeningResults, setScreeningResults] = useState(null)  // 新增：存储筛选结果

  useEffect(() => {
    loadInitialData()
  }, [])

  const loadInitialData = async () => {
    setLoading(true)
    try {
      const [market, statsData] = await Promise.all([
        getMarketOverview(),
        getStats()
      ])
      setMarketData(market)
      setStats(statsData.stats)
    } catch (error) {
      console.error('Failed to load initial data:', error)
    } finally {
      setLoading(false)
    }
  }

  const menuItems = [
    {
      key: 'screener',
      icon: <LineChartOutlined />,
      label: '山寨币筛选器',
    },
    {
      key: 'backtest',
      icon: <BarChartOutlined />,
      label: '交易回测分析',
    },
    {
      key: 'sim-trading',
      icon: <ThunderboltOutlined />,
      label: '模拟交易',
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '通知设置',
    },
  ]

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{
        background: '#001529',
        padding: '0 50px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        height: '80px'
      }}>
        <div>
          <Space align="center">
            <RocketOutlined style={{ fontSize: '32px', color: '#1890ff' }} />
            <div>
              <Title level={2} style={{ color: 'white', margin: 0, lineHeight: '1.2' }}>
                Tretra Trading Station
              </Title>
              <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.65)', marginTop: '-5px' }}>
                专业交易分析平台
              </div>
            </div>
          </Space>
        </div>
        <Menu
          theme="dark"
          mode="horizontal"
          selectedKeys={[currentView]}
          items={menuItems}
          onClick={({ key }) => setCurrentView(key)}
          style={{
            background: 'transparent',
            borderBottom: 'none',
            fontSize: '16px',
            minWidth: '300px'
          }}
        />
      </Header>

      <Content
        className={currentView === 'screener' ? "app-container" : ""}
        style={currentView === 'backtest' ? {
          padding: 0,
          maxWidth: '100%',
          margin: 0,
          width: '100%'
        } : {}}
      >
        {currentView === 'screener' ? (
          loading ? (
            <div style={{ textAlign: 'center', padding: '100px 0' }}>
              <Spin size="large" />
            </div>
          ) : (
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              {/* Market Overview */}
              <MarketOverview data={marketData} />

              {/* Stats */}
              {stats && <StatsPanel stats={stats} />}

              {/* Historical Rankings */}
              <HistoricalRankings />

              {/* Trading Panel */}
              <TradingPanel />

              {/* Screening Panel */}
              <Card className="screening-card">
                <ScreeningPanel
                  onStatsUpdate={loadInitialData}
                  onResultsUpdate={setScreeningResults}
                />
              </Card>

              {/* Results Table */}
              <ResultsTable screeningResults={screeningResults} />
            </Space>
          )
        ) : currentView === 'sim-trading' ? (
          <SimTradingPanel />
        ) : currentView === 'settings' ? (
          <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
            <NotificationSettingsPanel />
          </div>
        ) : (
          <div style={{
            width: '100%',
            height: 'calc(100vh - 80px)',
            padding: 0,
            margin: 0
          }}>
            <iframe
              src="http://localhost:8501"
              style={{
                width: '100%',
                height: '100%',
                border: 'none',
                display: 'block'
              }}
              title="交易回测分析"
            />
          </div>
        )}
      </Content>
    </Layout>
  )
}

export default App
