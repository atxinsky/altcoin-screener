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
  ChevronUp,
  ChevronDown,
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
  createMarketOrder,
  createLimitOrder,
  getSimTradingAccounts,
  openSimPosition,
  getBalance
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
  const [tradeMode, setTradeMode] = useState('paper') // 'paper' or 'real'
  const [orderType, setOrderType] = useState('market') // 'market' or 'limit'
  const [limitPrice, setLimitPrice] = useState('')
  const [paperAccounts, setPaperAccounts] = useState([])
  const [selectedPaperAccount, setSelectedPaperAccount] = useState(null)
  const [tradeLoading, setTradeLoading] = useState(false)
  const [quantityMode, setQuantityMode] = useState('coin') // 'coin' or 'usdt'
  const [usdtAmount, setUsdtAmount] = useState('')
  const [currentPrice, setCurrentPrice] = useState(0)
  const [coinBalance, setCoinBalance] = useState(0)
  const [usdtBalance, setUsdtBalance] = useState(0)
  const [balanceLoading, setBalanceLoading] = useState(false)

  // Watchlist
  const [watchlist, setWatchlist] = useState(new Set())

  // Sorting
  const [sortColumn, setSortColumn] = useState(null)
  const [sortDirection, setSortDirection] = useState('desc') // 'asc' or 'desc'

  useEffect(() => {
    loadInitialData()
  }, [])

  // Handle sorting
  const handleSort = (column) => {
    if (sortColumn === column) {
      // Toggle direction if same column
      setSortDirection(prev => prev === 'desc' ? 'asc' : 'desc')
    } else {
      // New column, default to descending
      setSortColumn(column)
      setSortDirection('desc')
    }
  }

  // Get sorted results
  const getSortedResults = () => {
    if (!sortColumn) return results

    return [...results].sort((a, b) => {
      let aVal = a[sortColumn] || 0
      let bVal = b[sortColumn] || 0

      if (sortDirection === 'desc') {
        return bVal - aVal
      } else {
        return aVal - bVal
      }
    })
  }

  const sortedResults = getSortedResults()

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

  const handleOpenTrade = async (symbol) => {
    setTradeSymbol(symbol)
    setTradeSide('BUY')
    setTradeQuantity('')
    setUsdtAmount('')
    setLimitPrice('')
    setOrderType('market')
    setQuantityMode('coin')
    setCoinBalance(0)
    setUsdtBalance(0)
    setCurrentPrice(0)
    setTradeModalOpen(true)

    // Get current price from results
    const symbolData = results.find(r => r.symbol === symbol)
    if (symbolData?.current_price) {
      setCurrentPrice(symbolData.current_price)
    }

    // Load paper accounts
    try {
      const response = await getSimTradingAccounts()
      const accountsList = response.accounts || []
      setPaperAccounts(accountsList)
      if (accountsList.length > 0 && !selectedPaperAccount) {
        setSelectedPaperAccount(accountsList[0].id)
      }
    } catch (error) {
      console.error('Failed to load paper accounts:', error)
    }

    // Load wallet balances for real trading
    setBalanceLoading(true)
    try {
      // Extract base asset from symbol (e.g., "LUMIA/USDT" -> "LUMIA")
      const baseAsset = symbol.split('/')[0]

      // Fetch USDT and coin balances in parallel
      const [usdtRes, coinRes] = await Promise.all([
        getBalance('USDT'),
        getBalance(baseAsset)
      ])

      setUsdtBalance(usdtRes.balance?.free || 0)
      setCoinBalance(coinRes.balance?.free || 0)
    } catch (error) {
      console.error('Failed to load balances:', error)
    } finally {
      setBalanceLoading(false)
    }
  }

  const handleSubmitTrade = async () => {
    if (!tradeSymbol) return

    setTradeLoading(true)
    try {
      if (tradeMode === 'paper') {
        // Paper trading - open sim position
        if (!selectedPaperAccount) {
          alert('Please select a paper trading account')
          return
        }
        await openSimPosition(selectedPaperAccount, tradeSymbol)
        alert(`Paper trade opened: ${tradeSymbol}`)
      } else {
        // Real trading - calculate quantity based on mode
        let finalQuantity = 0

        if (quantityMode === 'usdt') {
          // Convert USDT amount to coin quantity
          if (!usdtAmount || parseFloat(usdtAmount) <= 0) {
            alert('Please enter USDT amount')
            setTradeLoading(false)
            return
          }
          const priceToUse = orderType === 'limit' && limitPrice ? parseFloat(limitPrice) : currentPrice
          if (!priceToUse || priceToUse <= 0) {
            alert('Unable to calculate quantity: price not available')
            setTradeLoading(false)
            return
          }
          finalQuantity = parseFloat(usdtAmount) / priceToUse
        } else {
          // Direct coin quantity
          if (!tradeQuantity || parseFloat(tradeQuantity) <= 0) {
            alert('Please enter quantity')
            setTradeLoading(false)
            return
          }
          finalQuantity = parseFloat(tradeQuantity)
        }

        if (orderType === 'market') {
          await createMarketOrder(tradeSymbol, tradeSide, finalQuantity, 'Quick Trade')
        } else {
          if (!limitPrice) {
            alert('Please enter limit price')
            setTradeLoading(false)
            return
          }
          await createLimitOrder(tradeSymbol, tradeSide, finalQuantity, parseFloat(limitPrice), 'Quick Trade')
        }
        alert(`${orderType === 'market' ? 'Market' : 'Limit'} order submitted (${finalQuantity.toFixed(6)} ${tradeSymbol.split('/')[0]})`)
      }
      setTradeModalOpen(false)
    } catch (error) {
      console.error('Trade failed:', error)
      alert(`Trade failed: ${error.message || 'Unknown error'}`)
    } finally {
      setTradeLoading(false)
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
            title="FEAR & GREED"
            value={marketData.fear_greed_index || 0}
            subtext={marketData.fear_greed_label || 'N/A'}
            icon={<Zap className="w-5 h-5" />}
            color={
              (marketData.fear_greed_index || 0) >= 75 ? 'green' :
              (marketData.fear_greed_index || 0) >= 55 ? 'default' :
              (marketData.fear_greed_index || 0) >= 45 ? 'orange' :
              (marketData.fear_greed_index || 0) >= 25 ? 'orange' : 'red'
            }
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
                  <SortableHeader
                    label="SCORE"
                    column="total_score"
                    sortColumn={sortColumn}
                    sortDirection={sortDirection}
                    onSort={handleSort}
                  />
                  <SortableHeader
                    label="PRICE"
                    column="current_price"
                    sortColumn={sortColumn}
                    sortDirection={sortDirection}
                    onSort={handleSort}
                  />
                  <SortableHeader
                    label="5M"
                    column="price_change_5m"
                    sortColumn={sortColumn}
                    sortDirection={sortDirection}
                    onSort={handleSort}
                  />
                  <SortableHeader
                    label="15M"
                    column="price_change_15m"
                    sortColumn={sortColumn}
                    sortDirection={sortDirection}
                    onSort={handleSort}
                  />
                  <SortableHeader
                    label="1H"
                    column="price_change_1h"
                    sortColumn={sortColumn}
                    sortDirection={sortDirection}
                    onSort={handleSort}
                  />
                  <SortableHeader
                    label="BTC RATIO"
                    column="btc_ratio_change_pct"
                    sortColumn={sortColumn}
                    sortDirection={sortDirection}
                    onSort={handleSort}
                  />
                  <SortableHeader
                    label="ETH RATIO"
                    column="eth_ratio_change_pct"
                    sortColumn={sortColumn}
                    sortDirection={sortDirection}
                    onSort={handleSort}
                  />
                  <SortableHeader
                    label="VOLUME 24H"
                    column="volume_24h"
                    sortColumn={sortColumn}
                    sortDirection={sortDirection}
                    onSort={handleSort}
                  />
                  <th>SIGNALS</th>
                  <th>ACTIONS</th>
                </tr>
              </thead>
              <tbody>
                {sortedResults.length === 0 ? (
                  <tr>
                    <td colSpan={12} className="text-center py-12 text-muted-foreground">
                      {loading ? 'Loading...' : 'No results. Click "START SCAN" to begin.'}
                    </td>
                  </tr>
                ) : (
                  sortedResults.map((item, idx) => (
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
            {/* Trade Mode Selector */}
            <div className="flex gap-2 p-1 bg-muted rounded-lg">
              <button
                className={cn(
                  "flex-1 py-2 px-4 rounded-md text-sm font-mono transition-all",
                  tradeMode === 'paper'
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:text-foreground"
                )}
                onClick={() => setTradeMode('paper')}
              >
                PAPER TRADING
              </button>
              <button
                className={cn(
                  "flex-1 py-2 px-4 rounded-md text-sm font-mono transition-all",
                  tradeMode === 'real'
                    ? "bg-[#e40046] text-white"
                    : "text-muted-foreground hover:text-foreground"
                )}
                onClick={() => setTradeMode('real')}
              >
                REAL TRADING
              </button>
            </div>

            {tradeMode === 'paper' ? (
              /* Paper Trading Options */
              <div>
                <label className="text-xs font-mono text-muted-foreground mb-2 block">
                  SELECT ACCOUNT
                </label>
                <Select
                  value={selectedPaperAccount?.toString() || ''}
                  onValueChange={(v) => setSelectedPaperAccount(parseInt(v))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select account..." />
                  </SelectTrigger>
                  <SelectContent>
                    {paperAccounts.map(acc => (
                      <SelectItem key={acc.id} value={acc.id.toString()}>
                        {acc.account_name} (${acc.current_balance?.toFixed(2) || '0.00'})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {paperAccounts.length === 0 && (
                  <p className="text-xs text-muted-foreground mt-2">
                    No paper accounts. Create one in Trading page.
                  </p>
                )}
              </div>
            ) : (
              /* Real Trading Options */
              <>
                {/* Wallet Balance Display */}
                <div className="p-3 bg-muted/50 rounded-lg border border-border">
                  <div className="text-xs font-mono text-muted-foreground mb-2">WALLET BALANCE</div>
                  {balanceLoading ? (
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <RefreshCw className="w-3 h-3 animate-spin" />
                      Loading...
                    </div>
                  ) : (
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <div className="text-xs text-muted-foreground">USDT</div>
                        <div className="font-mono font-bold text-profit">
                          {usdtBalance.toFixed(2)}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-muted-foreground">{tradeSymbol?.split('/')[0] || 'COIN'}</div>
                        <div className="font-mono font-bold">
                          {coinBalance > 0 ? coinBalance.toFixed(6) : '0'}
                        </div>
                      </div>
                    </div>
                  )}
                  {currentPrice > 0 && (
                    <div className="mt-2 pt-2 border-t border-border">
                      <div className="text-xs text-muted-foreground">Current Price</div>
                      <div className="font-mono text-sm">${formatPrice(currentPrice)}</div>
                    </div>
                  )}
                </div>

                {/* Order Type Selector */}
                <div>
                  <label className="text-xs font-mono text-muted-foreground mb-2 block">
                    ORDER TYPE
                  </label>
                  <div className="flex gap-2">
                    <button
                      className={cn(
                        "flex-1 py-2 px-4 rounded-md text-sm font-mono border transition-all",
                        orderType === 'market'
                          ? "border-primary bg-primary/10 text-primary"
                          : "border-border text-muted-foreground hover:text-foreground"
                      )}
                      onClick={() => setOrderType('market')}
                    >
                      MARKET
                    </button>
                    <button
                      className={cn(
                        "flex-1 py-2 px-4 rounded-md text-sm font-mono border transition-all",
                        orderType === 'limit'
                          ? "border-primary bg-primary/10 text-primary"
                          : "border-border text-muted-foreground hover:text-foreground"
                      )}
                      onClick={() => setOrderType('limit')}
                    >
                      LIMIT
                    </button>
                  </div>
                </div>

                {/* Side Selection */}
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

                {/* Quantity Mode Toggle */}
                <div>
                  <label className="text-xs font-mono text-muted-foreground mb-2 block">
                    INPUT MODE
                  </label>
                  <div className="flex gap-2">
                    <button
                      className={cn(
                        "flex-1 py-2 px-4 rounded-md text-sm font-mono border transition-all",
                        quantityMode === 'usdt'
                          ? "border-[#6Ec85c] bg-[#6Ec85c]/10 text-[#6Ec85c]"
                          : "border-border text-muted-foreground hover:text-foreground"
                      )}
                      onClick={() => setQuantityMode('usdt')}
                    >
                      USDT AMOUNT
                    </button>
                    <button
                      className={cn(
                        "flex-1 py-2 px-4 rounded-md text-sm font-mono border transition-all",
                        quantityMode === 'coin'
                          ? "border-[#D4A0FF] bg-[#D4A0FF]/10 text-[#D4A0FF]"
                          : "border-border text-muted-foreground hover:text-foreground"
                      )}
                      onClick={() => setQuantityMode('coin')}
                    >
                      COIN QTY
                    </button>
                  </div>
                </div>

                {/* Quantity Input - based on mode */}
                {quantityMode === 'usdt' ? (
                  <div>
                    <label className="text-xs font-mono text-muted-foreground mb-2 block">
                      USDT AMOUNT
                    </label>
                    <Input
                      type="number"
                      value={usdtAmount}
                      onChange={(e) => setUsdtAmount(e.target.value)}
                      placeholder="Enter USDT amount"
                      step={0.01}
                    />
                    {usdtAmount && currentPrice > 0 && (
                      <div className="mt-1 text-xs text-muted-foreground">
                        Est. quantity: <span className="text-foreground font-mono">
                          {(parseFloat(usdtAmount) / currentPrice).toFixed(6)} {tradeSymbol?.split('/')[0]}
                        </span>
                      </div>
                    )}
                  </div>
                ) : (
                  <div>
                    <label className="text-xs font-mono text-muted-foreground mb-2 block">
                      QUANTITY ({tradeSymbol?.split('/')[0] || 'COIN'})
                    </label>
                    <Input
                      type="number"
                      value={tradeQuantity}
                      onChange={(e) => setTradeQuantity(e.target.value)}
                      placeholder="Enter quantity"
                      step={0.0001}
                    />
                    {tradeQuantity && currentPrice > 0 && (
                      <div className="mt-1 text-xs text-muted-foreground">
                        Est. value: <span className="text-foreground font-mono">
                          ${(parseFloat(tradeQuantity) * currentPrice).toFixed(2)} USDT
                        </span>
                      </div>
                    )}
                  </div>
                )}

                {/* Limit Price (only for limit orders) */}
                {orderType === 'limit' && (
                  <div>
                    <label className="text-xs font-mono text-muted-foreground mb-2 block">
                      LIMIT PRICE
                    </label>
                    <Input
                      type="number"
                      value={limitPrice}
                      onChange={(e) => setLimitPrice(e.target.value)}
                      placeholder="Enter limit price"
                      step={0.00000001}
                    />
                  </div>
                )}
              </>
            )}

            {/* Submit Buttons */}
            <div className="flex gap-2 pt-4">
              <Button
                onClick={handleSubmitTrade}
                className="flex-1"
                variant={tradeMode === 'paper' ? 'default' : (tradeSide === 'BUY' ? 'default' : 'destructive')}
                disabled={tradeLoading}
              >
                {tradeLoading ? (
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <ShoppingCart className="w-4 h-4 mr-2" />
                )}
                {tradeMode === 'paper' ? 'OPEN POSITION' : `SUBMIT ${tradeSide}`}
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

// Sortable Header Component
function SortableHeader({ label, column, sortColumn, sortDirection, onSort }) {
  const isActive = sortColumn === column

  return (
    <th
      className="cursor-pointer select-none hover:bg-muted/50 transition-colors"
      onClick={() => onSort(column)}
    >
      <div className="flex items-center gap-1">
        <span>{label}</span>
        <div className="flex flex-col">
          {isActive ? (
            sortDirection === 'desc' ? (
              <ChevronDown className="w-3 h-3 text-primary" />
            ) : (
              <ChevronUp className="w-3 h-3 text-primary" />
            )
          ) : (
            <div className="w-3 h-3 opacity-30">
              <ChevronUp className="w-3 h-3 -mb-1" />
            </div>
          )}
        </div>
      </div>
    </th>
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
        <td>
          <span className={cn("font-mono text-xs", (item.eth_ratio_change_pct || 0) >= 0 ? "text-profit" : "text-loss")}>
            {formatPercent(item.eth_ratio_change_pct || 0)}
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
          <td colSpan={12} className="bg-muted/30 p-4">
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
