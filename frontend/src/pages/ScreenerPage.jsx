import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  Activity,
  TrendingUp,
  TrendingDown,
  Search,
  RefreshCw,
  Star,
  StarOff,
  ChevronRight,
  Zap,
  BarChart3,
  ShoppingCart,
  X
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
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { cn, formatNumber, formatPercent, formatPrice, formatVolume } from '@/lib/utils'
import {
  getMarketOverview,
  getStats,
  screenAltcoins,
  getTopOpportunities,
  addToWatchlist,
  removeFromWatchlist,
  createMarketOrder
} from '@/services/api'
import KlineChart from '@/components/KlineChart'

export default function ScreenerPage() {
  const [loading, setLoading] = useState(false)
  const [screening, setScreening] = useState(false)
  const [marketData, setMarketData] = useState(null)
  const [stats, setStats] = useState(null)
  const [results, setResults] = useState([])
  const [dataSource, setDataSource] = useState('default')

  // Screening params
  const [screenMode, setScreenMode] = useState('regular')
  const [timeframe, setTimeframe] = useState('15m')
  const [minScore, setMinScore] = useState(60)
  const [minVolume, setMinVolume] = useState(1000000)
  const [minPriceChange, setMinPriceChange] = useState(2.0)

  // Modals
  const [chartModalOpen, setChartModalOpen] = useState(false)
  const [chartSymbol, setChartSymbol] = useState(null)
  const [chartTimeframe, setChartTimeframe] = useState('15m')
  const [tradeModalOpen, setTradeModalOpen] = useState(false)
  const [tradeSymbol, setTradeSymbol] = useState(null)
  const [tradeSide, setTradeSide] = useState('BUY')
  const [tradeQuantity, setTradeQuantity] = useState('')

  // Watchlist
  const [watchlist, setWatchlist] = useState(new Set())

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
      if (topResults.success !== false) {
        setResults(topResults.results || topResults.opportunities || [])
        setDataSource('default')
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
        min_score: minScore,
        min_volume: minVolume,
        min_price_change: minPriceChange
      })
      if (response.success !== false) {
        setResults(response.results || [])
        setDataSource('screening')
      }
    } catch (error) {
      console.error('Screening failed:', error)
    } finally {
      setScreening(false)
    }
  }

  const handleViewChart = (symbol, tf = '15m') => {
    setChartSymbol(symbol)
    setChartTimeframe(tf)
    setChartModalOpen(true)
  }

  const handleToggleWatchlist = async (symbol) => {
    try {
      if (watchlist.has(symbol)) {
        await removeFromWatchlist(symbol)
        setWatchlist(prev => {
          const newSet = new Set(prev)
          newSet.delete(symbol)
          return newSet
        })
      } else {
        await addToWatchlist(symbol, '')
        setWatchlist(prev => new Set(prev).add(symbol))
      }
    } catch (error) {
      console.error('Watchlist operation failed:', error)
    }
  }

  const handleOpenTrade = (symbol) => {
    setTradeSymbol(symbol)
    setTradeSide('BUY')
    setTradeQuantity('')
    setTradeModalOpen(true)
  }

  const handleSubmitTrade = async () => {
    if (!tradeQuantity || !tradeSymbol) return
    try {
      await createMarketOrder(tradeSymbol, tradeSide, parseFloat(tradeQuantity), 'Quick Trade')
      setTradeModalOpen(false)
    } catch (error) {
      console.error('Trade failed:', error)
    }
  }

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-[#e40046]'
    if (score >= 70) return 'text-[#FF5300]'
    if (score >= 60) return 'text-primary'
    return 'text-muted-foreground'
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
            <Badge variant={dataSource === 'screening' ? 'success' : 'purple'} className="font-mono">
              {dataSource === 'screening' ? 'LIVE SCAN' : 'TOP OPPORTUNITIES'} • {results.length}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="pt-6">
          <div className="flex flex-wrap items-end gap-4">
            <div className="min-w-[120px]">
              <label className="text-xs font-mono text-muted-foreground mb-2 block">
                MODE
              </label>
              <Select value={screenMode} onValueChange={setScreenMode}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="regular">Regular Screen</SelectItem>
                  <SelectItem value="gainers">Top Gainers</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="min-w-[120px]">
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

            <div className="min-w-[100px]">
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

            {screenMode === 'regular' && (
              <>
                <div className="min-w-[120px]">
                  <label className="text-xs font-mono text-muted-foreground mb-2 block">
                    MIN VOLUME ($)
                  </label>
                  <Input
                    type="number"
                    value={minVolume}
                    onChange={(e) => setMinVolume(Number(e.target.value))}
                    min={0}
                  />
                </div>

                <div className="min-w-[100px]">
                  <label className="text-xs font-mono text-muted-foreground mb-2 block">
                    MIN CHANGE %
                  </label>
                  <Input
                    type="number"
                    value={minPriceChange}
                    onChange={(e) => setMinPriceChange(Number(e.target.value))}
                    step={0.1}
                  />
                </div>
              </>
            )}

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
          <CardTitle>SCREENING RESULTS</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>SYMBOL</th>
                  <th>SCORE</th>
                  <th>PRICE</th>
                  <th>5M</th>
                  <th>15M</th>
                  <th>1H</th>
                  <th>BTC RATIO</th>
                  <th>VOLUME 24H</th>
                  <th>SIGNALS</th>
                  <th>ACTIONS</th>
                </tr>
              </thead>
              <tbody>
                {results.length === 0 ? (
                  <tr>
                    <td colSpan={11} className="text-center py-12 text-muted-foreground">
                      {loading ? 'Loading...' : 'No results. Click "START SCAN" to begin.'}
                    </td>
                  </tr>
                ) : (
                  results.map((item, idx) => (
                    <ResultRow
                      key={item.symbol || idx}
                      item={item}
                      rank={idx + 1}
                      onViewChart={handleViewChart}
                      onToggleWatchlist={handleToggleWatchlist}
                      onOpenTrade={handleOpenTrade}
                      isWatchlisted={watchlist.has(item.symbol)}
                      getScoreColor={getScoreColor}
                    />
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* K-line Chart Modal */}
      <Dialog open={chartModalOpen} onOpenChange={setChartModalOpen}>
        <DialogContent className="max-w-6xl">
          <DialogHeader>
            <DialogTitle className="font-mono">K-LINE CHART</DialogTitle>
          </DialogHeader>
          {chartSymbol && (
            <KlineChart
              symbol={chartSymbol}
              initialTimeframe={chartTimeframe}
            />
          )}
        </DialogContent>
      </Dialog>

      {/* Quick Trade Modal */}
      <Dialog open={tradeModalOpen} onOpenChange={setTradeModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="font-mono">QUICK TRADE - {tradeSymbol}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 pt-4">
            <div>
              <label className="text-xs font-mono text-muted-foreground mb-2 block">
                SIDE
              </label>
              <Select value={tradeSide} onValueChange={setTradeSide}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="BUY">BUY</SelectItem>
                  <SelectItem value="SELL">SELL</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-xs font-mono text-muted-foreground mb-2 block">
                QUANTITY
              </label>
              <Input
                type="number"
                value={tradeQuantity}
                onChange={(e) => setTradeQuantity(e.target.value)}
                placeholder="Enter quantity"
                step={0.0001}
              />
            </div>
            <div className="flex gap-2 pt-4">
              <Button
                onClick={handleSubmitTrade}
                className="flex-1"
                variant={tradeSide === 'BUY' ? 'default' : 'destructive'}
              >
                <ShoppingCart className="w-4 h-4 mr-2" />
                SUBMIT {tradeSide}
              </Button>
              <Button variant="outline" onClick={() => setTradeModalOpen(false)}>
                CANCEL
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
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
function ResultRow({ item, rank, onViewChart, onToggleWatchlist, onOpenTrade, isWatchlisted, getScoreColor }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <>
      <tr className="cursor-pointer hover:bg-muted/30" onClick={() => setExpanded(!expanded)}>
        <td className="font-mono text-muted-foreground">#{rank}</td>
        <td className="font-bold">{item.symbol}</td>
        <td>
          <span className={cn("font-bold font-mono text-lg", getScoreColor(item.total_score))}>
            {item.total_score?.toFixed(1)}
          </span>
        </td>
        <td className="font-mono">${formatPrice(item.current_price)}</td>
        <td>
          <span className={cn("font-mono", (item.price_change_5m || 0) >= 0 ? "text-profit" : "text-loss")}>
            {formatPercent(item.price_change_5m || 0)}
          </span>
        </td>
        <td>
          <span className={cn("font-mono", (item.price_change_15m || 0) >= 0 ? "text-profit" : "text-loss")}>
            {formatPercent(item.price_change_15m || 0)}
          </span>
        </td>
        <td>
          <span className={cn("font-mono", (item.price_change_1h || 0) >= 0 ? "text-profit" : "text-loss")}>
            {formatPercent(item.price_change_1h || 0)}
          </span>
        </td>
        <td>
          <span className={cn("font-mono text-xs", (item.btc_ratio_change_pct || 0) >= 0 ? "text-profit" : "text-loss")}>
            {formatPercent(item.btc_ratio_change_pct || 0)}
          </span>
        </td>
        <td className="font-mono">{formatVolume(item.volume_24h || 0)}</td>
        <td>
          <div className="flex flex-wrap gap-1">
            {item.above_sma && <Badge variant="secondary">SMA</Badge>}
            {item.macd_golden_cross && <Badge variant="warning">MACD</Badge>}
            {item.above_all_ema && <Badge variant="success">EMA</Badge>}
            {item.volume_surge && <Badge variant="orange">VOL</Badge>}
            {item.price_anomaly && <Badge variant="destructive">ALERT</Badge>}
          </div>
        </td>
        <td onClick={(e) => e.stopPropagation()}>
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onViewChart(item.symbol, item.timeframe || '15m')}
            >
              <BarChart3 className="w-4 h-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onToggleWatchlist(item.symbol)}
            >
              {isWatchlisted ? (
                <Star className="w-4 h-4 fill-yellow-500 text-yellow-500" />
              ) : (
                <StarOff className="w-4 h-4" />
              )}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onOpenTrade(item.symbol)}
            >
              <ShoppingCart className="w-4 h-4" />
            </Button>
            <ChevronRight className={cn(
              "w-4 h-4 transition-transform",
              expanded && "rotate-90"
            )} />
          </div>
        </td>
      </tr>
      {expanded && (
        <tr>
          <td colSpan={11} className="bg-muted/30 p-4">
            <div className="grid grid-cols-2 md:grid-cols-6 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Beta Score</span>
                <div className="font-mono font-bold">{item.beta_score?.toFixed(1) || '-'}</div>
              </div>
              <div>
                <span className="text-muted-foreground">Volume Score</span>
                <div className="font-mono font-bold">{item.volume_score?.toFixed(1) || '-'}</div>
              </div>
              <div>
                <span className="text-muted-foreground">Technical Score</span>
                <div className="font-mono font-bold">{item.technical_score?.toFixed(1) || '-'}</div>
              </div>
              <div>
                <span className="text-muted-foreground">ETH Ratio</span>
                <div className={cn("font-mono", (item.eth_ratio_change_pct || 0) >= 0 ? "text-profit" : "text-loss")}>
                  {formatPercent(item.eth_ratio_change_pct || 0)}
                </div>
              </div>
              <div>
                <span className="text-muted-foreground">RSI</span>
                <div className="font-mono font-bold">{item.rsi?.toFixed(1) || '-'}</div>
              </div>
              <div>
                <span className="text-muted-foreground">Timeframe</span>
                <div className="font-mono font-bold">{item.timeframe || '-'}</div>
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  )
}
