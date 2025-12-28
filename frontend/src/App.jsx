import React, { useState, useEffect } from 'react'
import { Layout, Typography, Space, Card, Row, Col, Spin } from 'antd'
import { RocketOutlined } from '@ant-design/icons'
import ScreeningPanel from './components/ScreeningPanel'
import ResultsTable from './components/ResultsTable'
import MarketOverview from './components/MarketOverview'
import StatsPanel from './components/StatsPanel'
import TradingPanel from './components/TradingPanel'
import HistoricalRankings from './components/HistoricalRankings'
import { getMarketOverview, getStats } from './services/api'

const { Header, Content } = Layout
const { Title } = Typography

function App() {
  const [marketData, setMarketData] = useState(null)
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

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

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header className="app-header">
        <Space align="center">
          <RocketOutlined style={{ fontSize: '32px' }} />
          <Title level={2} style={{ color: 'white', margin: 0 }}>
            币安山寨币筛选器
          </Title>
        </Space>
        <div style={{ fontSize: '14px', marginTop: '5px', opacity: 0.9 }}>
          抓取BTC/ETH上涨时的Beta机会
        </div>
      </Header>

      <Content className="app-container">
        {loading ? (
          <div style={{ textAlign: 'center', padding: '100px 0' }}>
            <Spin size="large" />
          </div>
        ) : (
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            {/* Market Overview & Stats - Full Width Top */}
            <Row gutter={[16, 16]}>
              <Col span={24}>
                <MarketOverview data={marketData} />
              </Col>
              {stats && (
                <Col span={24}>
                  <StatsPanel stats={stats} />
                </Col>
              )}
            </Row>

            {/* Trading Panel - Full Width */}
            <Row gutter={[16, 16]}>
              <Col span={24}>
                <TradingPanel />
              </Col>
            </Row>

            {/* Main Content Grid */}
            <Row gutter={[16, 16]}>
              {/* Left Sidebar - Historical Rankings */}
              <Col xs={24} xl={8}>
                <HistoricalRankings />
              </Col>

              {/* Right Column - Screening & Results */}
              <Col xs={24} xl={16}>
                <Space direction="vertical" size="large" style={{ width: '100%' }}>
                  {/* Screening Panel */}
                  <Card className="screening-card">
                    <ScreeningPanel onStatsUpdate={loadInitialData} />
                  </Card>

                  {/* Results Table */}
                  <ResultsTable />
                </Space>
              </Col>
            </Row>
          </Space>
        )}
      </Content>
    </Layout>
  )
}

export default App
