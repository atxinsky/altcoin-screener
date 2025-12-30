import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  Activity,
  TrendingUp,
  TrendingDown,
  Search,
  RefreshCw,
  Star,
  ChevronRight,
  Zap
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { cn, formatNumber, formatPercent, formatPrice, formatVolume } from '@/lib/utils'
import {
  getMarketOverview,
  getStats,
  screenAltcoins,
  getTopOpportunities
} from '@/services/api'

export default function ScreenerPage() {
  const [loading, setLoading] = useState(false)
  const [screening, setScreening] = useState(false)
  const [marketData, setMarketData] = useState(null)
  const [stats, setStats] = useState(null)
  const [results, setResults] = useState([])
  const [timeframe, setTimeframe] = useState('15m')
  const [minScore, setMinScore] = useState(60)

  useEffect(() => {
    loadInitialData()
  }, [])

  const loadInitialData = async () => {
    setLoading(true)
    try {
      const [market, statsData, topResults] = await Promise.all([
        getMarketOverview(),
        getStats(),
        getTopOpportunities(20, minScore)
      ])
      setMarketData(market)
      setStats(statsData.stats)
      if (topResults.success) {
        setResults(topResults.opportunities || [])
      }
    } catch (error) {
      console.error('Failed to load data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleScreen = async () => {
    setScreening(true)
    try {
      const response = await screenAltcoins({
        timeframe,
        limit: 50,
        min_score: minScore
      })
      if (response.success) {
        setResults(response.results || [])
      }
    } catch (error) {
      console.error('Screening failed:', error)
    } finally {
      setScreening(false)
    }
  }

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center py-8"
      >
        <div className="inline-flex items-center gap-2 mb-4">
          <div className="w-3 h-3 bg-primary animate-pulse"></div>
          <span className="text-xs font-mono text-muted-foreground tracking-widest">
            ALTCOIN SCREENER
          </span>
        </div>
        <h1 className="text-4xl md:text-5xl font-bold mb-4">
          FIND YOUR NEXT
          <br />
          <span className="text-primary">OPPORTUNITY</span>
        </h1>
        <p className="text-muted-foreground max-w-xl mx-auto">
          Multi-dimensional scoring system with technical indicators, volume analysis, and beta strength.
        </p>
      </motion.div>

      {/* Market Overview Cards */}
      {marketData && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatsCard
            title="BTC"
            value={formatPrice(marketData.btc_price)}
            change={marketData.btc_change_24h}
            icon={<Activity className="w-5 h-5" />}
            color="purple"
          />
          <StatsCard
            title="ETH"
            value={formatPrice(marketData.eth_price)}
            change={marketData.eth_change_24h}
            icon={<Activity className="w-5 h-5" />}
            color="orange"
          />
          <StatsCard
            title="TOTAL MARKET"
            value={formatVolume(marketData.total_volume || 0)}
            subtext="24h Volume"
            icon={<TrendingUp className="w-5 h-5" />}
            color="green"
          />
          <StatsCard
            title="ACTIVE PAIRS"
            value={stats?.total_symbols || '-'}
            subtext="Tracking"
            icon={<Zap className="w-5 h-5" />}
            color="default"
          />
        </div>
      )}

      {/* Screening Controls */}
      <Card>
        <CardHeader className="border-b border-border">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Search className="w-5 h-5 text-primary" />
              SCREENING PARAMETERS
            </CardTitle>
            <Badge variant="purple" className="font-mono">
              {results.length} RESULTS
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="pt-6">
          <div className="flex flex-wrap items-end gap-4">
            <div className="flex-1 min-w-[150px]">
              <label className="text-xs font-mono text-muted-foreground mb-2 block">
                TIMEFRAME
              </label>
              <Select value={timeframe} onValueChange={setTimeframe}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="5m">5 Minutes</SelectItem>
                  <SelectItem value="15m">15 Minutes</SelectItem>
                  <SelectItem value="1h">1 Hour</SelectItem>
                  <SelectItem value="4h">4 Hours</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex-1 min-w-[150px]">
              <label className="text-xs font-mono text-muted-foreground mb-2 block">
                MIN SCORE
              </label>
              <Input
                type="number"
                value={minScore}
                onChange={(e) => setMinScore(Number(e.target.value))}
                min={0}
                max={100}
              />
            </div>

            <Button
              onClick={handleScreen}
              disabled={screening}
              className="min-w-[160px]"
            >
              {screening ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  SCREENING...
                </>
              ) : (
                <>
                  <Search className="w-4 h-4 mr-2" />
                  START SCAN
                </>
              )}
            </Button>

            <Button
              variant="outline"
              onClick={loadInitialData}
              disabled={loading}
            >
              <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Results Table */}
      <Card>
        <CardHeader>
          <CardTitle>TOP OPPORTUNITIES</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>SYMBOL</th>
                  <th>PRICE</th>
                  <th>CHANGE</th>
                  <th>VOLUME 24H</th>
                  <th>TOTAL SCORE</th>
                  <th>TECH SCORE</th>
                  <th>SIGNALS</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {results.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="text-center py-12 text-muted-foreground">
                      {loading ? 'Loading...' : 'No results yet. Click "START SCAN" to begin.'}
                    </td>
                  </tr>
                ) : (
                  results.map((item, idx) => (
                    <ResultRow key={item.symbol} item={item} rank={idx + 1} />
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// Stats Card Component
function StatsCard({ title, value, change, subtext, icon, color = 'default' }) {
  const colorMap = {
    purple: 'border-[#D4A0FF]',
    orange: 'border-[#FF5300]',
    green: 'border-[#6Ec85c]',
    red: 'border-[#e40046]',
    default: 'border-border'
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        "trading-card",
        colorMap[color]
      )}
    >
      <div className="flex items-start justify-between mb-4">
        <span className="text-xs font-mono text-muted-foreground tracking-wider">
          {title}
        </span>
        <div className="text-muted-foreground">{icon}</div>
      </div>
      <div className="text-2xl font-bold font-mono mb-1">{value}</div>
      {change !== undefined && (
        <div className={cn(
          "text-sm font-mono",
          change >= 0 ? "text-profit" : "text-loss"
        )}>
          {formatPercent(change)}
        </div>
      )}
      {subtext && (
        <div className="text-xs text-muted-foreground">{subtext}</div>
      )}
    </motion.div>
  )
}

// Result Row Component
function ResultRow({ item, rank }) {
  const [expanded, setExpanded] = useState(false)

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-profit'
    if (score >= 70) return 'text-primary'
    if (score >= 60) return 'text-[#FF5300]'
    return 'text-muted-foreground'
  }

  return (
    <>
      <tr
        className="cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <td>
          <div className="flex items-center gap-3">
            <span className="text-xs text-muted-foreground font-mono w-6">
              #{rank}
            </span>
            <div>
              <div className="font-bold">{item.symbol}</div>
            </div>
          </div>
        </td>
        <td className="font-mono">${formatPrice(item.current_price)}</td>
        <td>
          <span className={cn(
            "font-mono",
            (item.price_change_15m || 0) >= 0 ? "text-profit" : "text-loss"
          )}>
            {formatPercent(item.price_change_15m || 0)}
          </span>
        </td>
        <td className="font-mono">{formatVolume(item.volume_24h || 0)}</td>
        <td>
          <span className={cn("font-bold font-mono text-lg", getScoreColor(item.total_score))}>
            {item.total_score?.toFixed(1)}
          </span>
        </td>
        <td className="font-mono">{item.technical_score?.toFixed(1)}</td>
        <td>
          <div className="flex flex-wrap gap-1">
            {item.macd_golden_cross && <Badge variant="success">MACD</Badge>}
            {item.above_all_ema && <Badge variant="purple">EMA</Badge>}
            {item.volume_surge && <Badge variant="warning">VOL</Badge>}
          </div>
        </td>
        <td>
          <ChevronRight className={cn(
            "w-4 h-4 transition-transform",
            expanded && "rotate-90"
          )} />
        </td>
      </tr>
      {expanded && (
        <tr>
          <td colSpan={8} className="bg-muted/30 p-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Beta Score</span>
                <div className="font-mono font-bold">{item.beta_score?.toFixed(1)}</div>
              </div>
              <div>
                <span className="text-muted-foreground">Volume Score</span>
                <div className="font-mono font-bold">{item.volume_score?.toFixed(1)}</div>
              </div>
              <div>
                <span className="text-muted-foreground">5m Change</span>
                <div className={cn("font-mono", (item.price_change_5m || 0) >= 0 ? "text-profit" : "text-loss")}>
                  {formatPercent(item.price_change_5m || 0)}
                </div>
              </div>
              <div>
                <span className="text-muted-foreground">1h Change</span>
                <div className={cn("font-mono", (item.price_change_1h || 0) >= 0 ? "text-profit" : "text-loss")}>
                  {formatPercent(item.price_change_1h || 0)}
                </div>
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  )
}
