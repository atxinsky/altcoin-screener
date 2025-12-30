import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  Wallet,
  TrendingUp,
  TrendingDown,
  Plus,
  RefreshCw,
  Play,
  Pause,
  ChevronDown,
  ChevronRight,
  Settings,
  Activity,
  Zap,
  Trophy,
  X,
  Trash2,
  AlertTriangle,
  DollarSign,
  Coins,
  ShoppingCart,
  BarChart3
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Switch } from '@/components/ui/switch'
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
  DialogFooter,
} from '@/components/ui/dialog'
import { cn, formatNumber, formatPercent, formatPrice, formatVolume } from '@/lib/utils'
import {
  getSimTradingAccounts,
  createSimTradingAccount,
  deleteSimTradingAccount,
  toggleAutoTrading,
  getAccountPositions,
  getAccountTrades,
  getAccountLogs,
  closePosition,
  getAllBalances,
  getOrderHistory,
  createMarketOrder
} from '@/services/api'

export default function TradingPage() {
  const [tradingMode, setTradingMode] = useState('paper')

  return (
    <div className="space-y-6">
      {/* Mode Selector */}
      <div className="flex items-center justify-center">
        <div className="inline-flex bg-muted p-1 rounded-none border-2 border-border">
          <button
            onClick={() => setTradingMode('paper')}
            className={cn(
              "px-6 py-2 text-sm font-bold tracking-wider transition-all",
              tradingMode === 'paper'
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            <Play className="w-4 h-4 inline mr-2" />
            PAPER TRADING
          </button>
          <button
            onClick={() => setTradingMode('real')}
            className={cn(
              "px-6 py-2 text-sm font-bold tracking-wider transition-all",
              tradingMode === 'real'
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            <DollarSign className="w-4 h-4 inline mr-2" />
            REAL TRADING
          </button>
        </div>
      </div>

      {tradingMode === 'paper' ? <PaperTradingSection /> : <RealTradingSection />}
    </div>
  )
}

// ==================== PAPER TRADING SECTION ====================
function PaperTradingSection() {
  const [accounts, setAccounts] = useState([])
  const [selectedAccount, setSelectedAccount] = useState(null)
  const [positions, setPositions] = useState([])
  const [trades, setTrades] = useState([])
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const [formData, setFormData] = useState({
    account_name: '',
    initial_balance: 10000,
    max_positions: 5,
    position_size_pct: 2.0,
    entry_timeframe: '15m',
    entry_score_min: 75.0,
    entry_technical_min: 60.0,
    stop_loss_pct: 3.0,
    take_profit_1: 6.0,
    take_profit_2: 10.0,
    take_profit_3: 15.0,
    require_macd_golden: true,
    require_volume_surge: false,
    trailing_stop_enabled: false,
    trailing_stop_pct: 2.0,
    max_holding_hours: 24
  })

  useEffect(() => {
    loadAccounts()
  }, [])

  useEffect(() => {
    if (selectedAccount) {
      loadAccountData(selectedAccount.id)
    }
  }, [selectedAccount])

  const loadAccounts = async () => {
    try {
      setLoading(true)
      const response = await getSimTradingAccounts()
      const accountsList = response.accounts || []
      setAccounts(accountsList)
      if (accountsList.length > 0 && !selectedAccount) {
        setSelectedAccount(accountsList[0])
      }
    } catch (error) {
      console.error('Failed to load accounts:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadAccountData = async (accountId) => {
    try {
      const [posRes, tradeRes, logRes] = await Promise.all([
        getAccountPositions(accountId),
        getAccountTrades(accountId),
        getAccountLogs(accountId, 100)
      ])
      setPositions(posRes.positions || [])
      setTrades(tradeRes.trades || [])
      setLogs(logRes.logs || [])
    } catch (error) {
      console.error('Failed to load account data:', error)
    }
  }

  const handleCreateAccount = async () => {
    try {
      setLoading(true)
      const payload = {
        ...formData,
        take_profit_levels: [formData.take_profit_1, formData.take_profit_2, formData.take_profit_3],
        strategy_config: {
          require_macd_golden: formData.require_macd_golden,
          require_volume_surge: formData.require_volume_surge,
          trailing_stop_enabled: formData.trailing_stop_enabled,
          trailing_stop_pct: formData.trailing_stop_pct,
          max_holding_hours: formData.max_holding_hours
        }
      }
      delete payload.take_profit_1
      delete payload.take_profit_2
      delete payload.take_profit_3
      delete payload.require_macd_golden
      delete payload.require_volume_surge
      delete payload.trailing_stop_enabled
      delete payload.trailing_stop_pct
      delete payload.max_holding_hours

      await createSimTradingAccount(payload)
      setShowCreateModal(false)
      setFormData({
        account_name: '', initial_balance: 10000, max_positions: 5, position_size_pct: 2.0,
        entry_timeframe: '15m', entry_score_min: 75.0, entry_technical_min: 60.0,
        stop_loss_pct: 3.0, take_profit_1: 6.0, take_profit_2: 10.0, take_profit_3: 15.0,
        require_macd_golden: true, require_volume_surge: false, trailing_stop_enabled: false,
        trailing_stop_pct: 2.0, max_holding_hours: 24
      })
      await loadAccounts()
    } catch (error) {
      console.error('Failed to create account:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleToggleAutoTrading = async () => {
    if (!selectedAccount) return
    try {
      const newStatus = !selectedAccount.auto_trading_enabled
      await toggleAutoTrading(selectedAccount.id, newStatus)
      loadAccounts()
    } catch (error) {
      console.error('Failed to toggle auto trading:', error)
    }
  }

  const handleTriggerAutoTrade = async () => {
    if (!selectedAccount) return
    try {
      setLoading(true)
      await toggleAutoTrading(selectedAccount.id, true)
      loadAccountData(selectedAccount.id)
      loadAccounts()
    } catch (error) {
      console.error('Failed to trigger auto trade:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleClosePosition = async (positionId) => {
    try {
      setLoading(true)
      await closePosition(positionId)
      loadAccountData(selectedAccount.id)
      loadAccounts()
    } catch (error) {
      console.error('Failed to close position:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteAccount = async () => {
    if (!selectedAccount) return
    try {
      setDeleting(true)
      await deleteSimTradingAccount(selectedAccount.id)
      setShowDeleteModal(false)
      setSelectedAccount(null)
      setPositions([])
      setTrades([])
      setLogs([])
      await loadAccounts()
    } catch (error) {
      console.error('Failed to delete account:', error)
    } finally {
      setDeleting(false)
    }
  }

  const updateForm = (key, value) => {
    setFormData(prev => ({ ...prev, [key]: value }))
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <div className="flex items-center gap-2 mb-2">
            <div className="w-3 h-3 bg-primary animate-pulse"></div>
            <span className="text-xs font-mono text-muted-foreground tracking-widest">
              SIMULATION TRADING
            </span>
          </div>
          <h1 className="text-3xl font-bold">
            PAPER <span className="text-primary">TRADING</span>
          </h1>
        </div>

        <div className="flex items-center gap-4">
          <Button variant="outline" onClick={() => setShowCreateModal(true)}>
            <Plus className="w-4 h-4 mr-2" />
            NEW ACCOUNT
          </Button>
        </div>
      </motion.div>

      {/* Loading State */}
      {loading && accounts.length === 0 && (
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="w-6 h-6 animate-spin text-primary mr-2" />
          <span className="text-muted-foreground">Loading accounts...</span>
        </div>
      )}

      {/* Empty State */}
      {!loading && accounts.length === 0 && (
        <Card className="text-center py-12">
          <CardContent>
            <Wallet className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-xl font-bold mb-2">NO ACCOUNTS</h3>
            <p className="text-muted-foreground mb-4">
              Create your first simulation trading account to get started.
            </p>
            <Button onClick={() => setShowCreateModal(true)}>
              <Plus className="w-4 h-4 mr-2" />
              CREATE ACCOUNT
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Account Selector & Stats */}
      {selectedAccount && (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <Card className="md:col-span-1">
            <CardContent className="pt-6">
              <label className="text-xs font-mono text-muted-foreground mb-2 block">SELECT ACCOUNT</label>
              <Select
                value={selectedAccount?.id?.toString()}
                onValueChange={(val) => {
                  const acc = accounts.find(a => a.id.toString() === val)
                  setSelectedAccount(acc)
                }}
              >
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {accounts.map((acc) => (
                    <SelectItem key={acc.id} value={acc.id.toString()}>{acc.account_name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <div className="mt-4 flex items-center justify-between">
                <span className="text-xs text-muted-foreground">AUTO TRADE</span>
                <Switch checked={selectedAccount.auto_trading_enabled} onCheckedChange={handleToggleAutoTrading} />
              </div>
              <Button variant="destructive" size="sm" className="w-full mt-4" onClick={() => setShowDeleteModal(true)}>
                <Trash2 className="w-4 h-4 mr-2" />DELETE ACCOUNT
              </Button>
            </CardContent>
          </Card>

          <StatsCard title="TOTAL EQUITY" value={`$${formatNumber(selectedAccount.total_equity)}`} icon={<Wallet className="w-5 h-5" />} color="purple" />
          <StatsCard title="TOTAL P&L" value={`$${formatNumber(selectedAccount.total_pnl)}`} change={selectedAccount.total_pnl} icon={selectedAccount.total_pnl >= 0 ? <TrendingUp className="w-5 h-5" /> : <TrendingDown className="w-5 h-5" />} color={selectedAccount.total_pnl >= 0 ? 'green' : 'red'} />
          <StatsCard title="WIN RATE" value={`${(selectedAccount.win_rate * 100).toFixed(1)}%`} icon={<Trophy className="w-5 h-5" />} color="default" />
          <StatsCard title="TRADES" value={selectedAccount.total_trades} icon={<Activity className="w-5 h-5" />} color="default" />
        </div>
      )}

      {/* Control Buttons */}
      {selectedAccount && (
        <div className="flex gap-4">
          <Button onClick={handleTriggerAutoTrade} disabled={loading} className="min-w-[180px]">
            {loading ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <Zap className="w-4 h-4 mr-2" />}
            TRIGGER SCAN
          </Button>
          <Button variant="outline" onClick={() => loadAccountData(selectedAccount.id)}>
            <RefreshCw className="w-4 h-4 mr-2" />REFRESH
          </Button>
        </div>
      )}

      {/* Tabs: Positions / Trades / Logs */}
      {selectedAccount && (
        <Tabs defaultValue="positions" className="w-full">
          <TabsList>
            <TabsTrigger value="positions">POSITIONS ({positions.length})</TabsTrigger>
            <TabsTrigger value="trades">TRADES ({trades.length})</TabsTrigger>
            <TabsTrigger value="logs">LOGS ({logs.length})</TabsTrigger>
          </TabsList>

          <TabsContent value="positions">
            <Card>
              <CardContent className="p-0">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>SYMBOL</th><th>ENTRY</th><th>CURRENT</th><th>QTY</th><th>P&L</th><th>SL / TP</th><th>ACTION</th>
                    </tr>
                  </thead>
                  <tbody>
                    {positions.length === 0 ? (
                      <tr><td colSpan={7} className="text-center py-8 text-muted-foreground">No open positions</td></tr>
                    ) : (
                      positions.map((pos) => (
                        <tr key={pos.id}>
                          <td className="font-bold">{pos.symbol}</td>
                          <td className="font-mono">${formatPrice(pos.entry_price)}</td>
                          <td className="font-mono">${formatPrice(pos.current_price)}</td>
                          <td className="font-mono">{pos.quantity?.toFixed(4)}</td>
                          <td>
                            <div className={cn("font-mono font-bold", pos.unrealized_pnl_pct >= 0 ? "text-profit" : "text-loss")}>
                              {formatPercent(pos.unrealized_pnl_pct)}
                              <div className="text-xs opacity-70">${pos.unrealized_pnl?.toFixed(2) || '0.00'}</div>
                            </div>
                          </td>
                          <td className="font-mono text-xs">
                            <span className="text-loss">${formatPrice(pos.stop_loss_price)}</span>
                            {' / '}
                            <span className="text-profit">${formatPrice(pos.take_profit_prices?.[0])}</span>
                          </td>
                          <td>
                            <Button variant="destructive" size="sm" onClick={() => handleClosePosition(pos.id)} disabled={loading}>CLOSE</Button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="trades">
            <Card>
              <CardContent className="p-0">
                <table className="data-table">
                  <thead>
                    <tr><th>TIME</th><th>SYMBOL</th><th>SIDE</th><th>PRICE</th><th>QTY</th><th>P&L</th><th>TYPE</th></tr>
                  </thead>
                  <tbody>
                    {trades.length === 0 ? (
                      <tr><td colSpan={7} className="text-center py-8 text-muted-foreground">No trades yet</td></tr>
                    ) : (
                      trades.map((trade) => (
                        <tr key={trade.id}>
                          <td className="font-mono text-xs">{new Date(trade.trade_time).toLocaleString()}</td>
                          <td className="font-bold">{trade.symbol}</td>
                          <td><Badge variant={trade.side === 'BUY' ? 'success' : 'destructive'}>{trade.side}</Badge></td>
                          <td className="font-mono">${formatPrice(trade.price)}</td>
                          <td className="font-mono">{trade.quantity?.toFixed(4)}</td>
                          <td>
                            {trade.pnl !== null ? (
                              <div className={cn("font-mono", trade.pnl >= 0 ? "text-profit" : "text-loss")}>
                                {formatPercent(trade.pnl_pct)}
                                <div className="text-xs opacity-70">${trade.pnl?.toFixed(2)}</div>
                              </div>
                            ) : '-'}
                          </td>
                          <td>
                            <Badge variant={trade.trade_type === 'ENTRY' ? 'success' : trade.trade_type === 'PARTIAL_EXIT' ? 'warning' : 'destructive'}>{trade.trade_type}</Badge>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="logs">
            <Card>
              <CardContent className="p-0">
                <table className="data-table">
                  <thead>
                    <tr><th>TIME</th><th>ACTION</th><th>SYMBOL</th><th>SCORE</th><th>REASON</th><th>STATUS</th></tr>
                  </thead>
                  <tbody>
                    {logs.length === 0 ? (
                      <tr><td colSpan={6} className="text-center py-8 text-muted-foreground">No logs yet</td></tr>
                    ) : (
                      logs.map((log) => <LogRow key={log.id} log={log} />)
                    )}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}

      {/* Create Account Modal */}
      <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="font-mono">CREATE NEW ACCOUNT</DialogTitle>
          </DialogHeader>
          <div className="space-y-6 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-mono text-muted-foreground mb-2 block">ACCOUNT NAME</label>
                <Input value={formData.account_name} onChange={(e) => updateForm('account_name', e.target.value)} placeholder="Strategy A" />
              </div>
              <div>
                <label className="text-xs font-mono text-muted-foreground mb-2 block">INITIAL BALANCE (USDT)</label>
                <Input type="number" value={formData.initial_balance} onChange={(e) => updateForm('initial_balance', Number(e.target.value))} />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-mono text-muted-foreground mb-2 block">MAX POSITIONS</label>
                <Input type="number" value={formData.max_positions} onChange={(e) => updateForm('max_positions', Number(e.target.value))} />
              </div>
              <div>
                <label className="text-xs font-mono text-muted-foreground mb-2 block">POSITION SIZE (%)</label>
                <Input type="number" step={0.5} value={formData.position_size_pct} onChange={(e) => updateForm('position_size_pct', Number(e.target.value))} />
              </div>
            </div>
            <div className="border-t border-border pt-4">
              <h4 className="text-sm font-mono text-muted-foreground mb-4">ENTRY CONDITIONS</h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <label className="text-xs font-mono text-muted-foreground mb-2 block">TIMEFRAME</label>
                  <Select value={formData.entry_timeframe} onValueChange={(v) => updateForm('entry_timeframe', v)}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="5m">5M</SelectItem>
                      <SelectItem value="15m">15M</SelectItem>
                      <SelectItem value="1h">1H</SelectItem>
                      <SelectItem value="4h">4H</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-xs font-mono text-muted-foreground mb-2 block">MIN SCORE</label>
                  <Input type="number" value={formData.entry_score_min} onChange={(e) => updateForm('entry_score_min', Number(e.target.value))} />
                </div>
                <div>
                  <label className="text-xs font-mono text-muted-foreground mb-2 block">MIN TECH SCORE</label>
                  <Input type="number" value={formData.entry_technical_min} onChange={(e) => updateForm('entry_technical_min', Number(e.target.value))} />
                </div>
                <div>
                  <label className="text-xs font-mono text-muted-foreground mb-2 block">MAX HOLD (H)</label>
                  <Input type="number" value={formData.max_holding_hours} onChange={(e) => updateForm('max_holding_hours', Number(e.target.value))} />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4 mt-4">
                <div className="flex items-center justify-between p-3 border border-border">
                  <span className="text-sm">REQUIRE MACD GOLDEN</span>
                  <Switch checked={formData.require_macd_golden} onCheckedChange={(v) => updateForm('require_macd_golden', v)} />
                </div>
                <div className="flex items-center justify-between p-3 border border-border">
                  <span className="text-sm">REQUIRE VOLUME SURGE</span>
                  <Switch checked={formData.require_volume_surge} onCheckedChange={(v) => updateForm('require_volume_surge', v)} />
                </div>
              </div>
            </div>
            <div className="border-t border-border pt-4">
              <h4 className="text-sm font-mono text-muted-foreground mb-4">STOP LOSS</h4>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="text-xs font-mono text-muted-foreground mb-2 block">STOP LOSS (%)</label>
                  <Input type="number" step={0.5} value={formData.stop_loss_pct} onChange={(e) => updateForm('stop_loss_pct', Number(e.target.value))} />
                </div>
                <div className="flex items-center justify-between p-3 border border-border">
                  <span className="text-sm">TRAILING STOP</span>
                  <Switch checked={formData.trailing_stop_enabled} onCheckedChange={(v) => updateForm('trailing_stop_enabled', v)} />
                </div>
                <div>
                  <label className="text-xs font-mono text-muted-foreground mb-2 block">TRAIL (%)</label>
                  <Input type="number" step={0.5} value={formData.trailing_stop_pct} onChange={(e) => updateForm('trailing_stop_pct', Number(e.target.value))} />
                </div>
              </div>
            </div>
            <div className="border-t border-border pt-4">
              <h4 className="text-sm font-mono text-muted-foreground mb-4">TAKE PROFIT (SCALED)</h4>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="text-xs font-mono text-muted-foreground mb-2 block">TP1 (%) - 33%</label>
                  <Input type="number" step={0.5} value={formData.take_profit_1} onChange={(e) => updateForm('take_profit_1', Number(e.target.value))} />
                </div>
                <div>
                  <label className="text-xs font-mono text-muted-foreground mb-2 block">TP2 (%) - 33%</label>
                  <Input type="number" step={0.5} value={formData.take_profit_2} onChange={(e) => updateForm('take_profit_2', Number(e.target.value))} />
                </div>
                <div>
                  <label className="text-xs font-mono text-muted-foreground mb-2 block">TP3 (%) - 34%</label>
                  <Input type="number" step={0.5} value={formData.take_profit_3} onChange={(e) => updateForm('take_profit_3', Number(e.target.value))} />
                </div>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateModal(false)}>CANCEL</Button>
            <Button onClick={handleCreateAccount} disabled={loading || !formData.account_name}>
              {loading ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <Plus className="w-4 h-4 mr-2" />}
              CREATE ACCOUNT
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Account Confirmation Modal */}
      <Dialog open={showDeleteModal} onOpenChange={setShowDeleteModal}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="font-mono flex items-center gap-2 text-destructive">
              <AlertTriangle className="w-5 h-5" />DELETE ACCOUNT
            </DialogTitle>
          </DialogHeader>
          <div className="py-4">
            <p className="text-muted-foreground mb-4">
              Are you sure you want to delete <span className="font-bold text-foreground">{selectedAccount?.account_name}</span>?
            </p>
            <p className="text-sm text-muted-foreground">This will permanently delete:</p>
            <ul className="text-sm text-muted-foreground mt-2 space-y-1 ml-4">
              <li>• All positions ({positions.length} current)</li>
              <li>• All trade history ({trades.length} trades)</li>
              <li>• All auto-trading logs ({logs.length} logs)</li>
              <li>• Account settings and statistics</li>
            </ul>
            <p className="text-destructive text-sm font-bold mt-4">This action cannot be undone.</p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDeleteModal(false)}>CANCEL</Button>
            <Button variant="destructive" onClick={handleDeleteAccount} disabled={deleting}>
              {deleting ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <Trash2 className="w-4 h-4 mr-2" />}
              DELETE ACCOUNT
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

// ==================== REAL TRADING SECTION ====================
function RealTradingSection() {
  const [balances, setBalances] = useState([])
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadRealData()
  }, [])

  const loadRealData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [balanceRes, ordersRes] = await Promise.all([
        getAllBalances(),
        getOrderHistory(null, 50)
      ])
      setBalances(balanceRes.balances || [])
      setOrders(ordersRes.orders || [])
    } catch (err) {
      console.error('Failed to load real trading data:', err)
      setError('Failed to load data. Please check your API keys.')
    } finally {
      setLoading(false)
    }
  }

  // Calculate total value
  const totalUSDT = balances.find(b => b.asset === 'USDT')?.free || 0

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <div className="flex items-center gap-2 mb-2">
            <div className="w-3 h-3 bg-[#6Ec85c] animate-pulse"></div>
            <span className="text-xs font-mono text-muted-foreground tracking-widest">
              BINANCE SPOT
            </span>
          </div>
          <h1 className="text-3xl font-bold">
            REAL <span className="text-[#6Ec85c]">TRADING</span>
          </h1>
        </div>

        <Button variant="outline" onClick={loadRealData} disabled={loading}>
          <RefreshCw className={cn("w-4 h-4 mr-2", loading && "animate-spin")} />
          REFRESH
        </Button>
      </motion.div>

      {/* Error State */}
      {error && (
        <Card className="border-destructive">
          <CardContent className="py-4">
            <div className="flex items-center gap-2 text-destructive">
              <AlertTriangle className="w-5 h-5" />
              <span>{error}</span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="w-6 h-6 animate-spin text-primary mr-2" />
          <span className="text-muted-foreground">Loading account data...</span>
        </div>
      )}

      {/* Balances */}
      {!loading && !error && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <StatsCard
              title="USDT BALANCE"
              value={`$${formatNumber(totalUSDT)}`}
              icon={<DollarSign className="w-5 h-5" />}
              color="green"
            />
            <StatsCard
              title="TOTAL ASSETS"
              value={balances.filter(b => parseFloat(b.free) > 0 || parseFloat(b.locked) > 0).length}
              icon={<Coins className="w-5 h-5" />}
              color="purple"
            />
            <StatsCard
              title="LOCAL ORDERS"
              value={orders.length}
              icon={<ShoppingCart className="w-5 h-5" />}
              color="default"
            />
            <StatsCard
              title="EXCHANGE"
              value="BINANCE"
              icon={<BarChart3 className="w-5 h-5" />}
              color="default"
            />
          </div>

          {/* Tabs: Balances / Orders */}
          <Tabs defaultValue="balances" className="w-full">
            <TabsList>
              <TabsTrigger value="balances">
                SPOT BALANCES ({balances.filter(b => parseFloat(b.free) > 0 || parseFloat(b.locked) > 0).length})
              </TabsTrigger>
              <TabsTrigger value="orders">
                LOCAL ORDERS ({orders.length})
              </TabsTrigger>
            </TabsList>

            <TabsContent value="balances">
              <Card>
                <CardContent className="p-0">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>ASSET</th>
                        <th>FREE</th>
                        <th>LOCKED</th>
                        <th>TOTAL</th>
                      </tr>
                    </thead>
                    <tbody>
                      {balances.filter(b => parseFloat(b.free) > 0 || parseFloat(b.locked) > 0).length === 0 ? (
                        <tr>
                          <td colSpan={4} className="text-center py-8 text-muted-foreground">
                            No balances found
                          </td>
                        </tr>
                      ) : (
                        balances
                          .filter(b => parseFloat(b.free) > 0 || parseFloat(b.locked) > 0)
                          .sort((a, b) => (parseFloat(b.free) + parseFloat(b.locked)) - (parseFloat(a.free) + parseFloat(a.locked)))
                          .map((bal) => (
                            <tr key={bal.asset}>
                              <td className="font-bold">
                                <div className="flex items-center gap-2">
                                  <div className="w-6 h-6 bg-muted flex items-center justify-center text-xs font-bold">
                                    {bal.asset.slice(0, 2)}
                                  </div>
                                  {bal.asset}
                                </div>
                              </td>
                              <td className="font-mono">{parseFloat(bal.free).toFixed(8)}</td>
                              <td className="font-mono text-muted-foreground">{parseFloat(bal.locked).toFixed(8)}</td>
                              <td className="font-mono font-bold">
                                {(parseFloat(bal.free) + parseFloat(bal.locked)).toFixed(8)}
                              </td>
                            </tr>
                          ))
                      )}
                    </tbody>
                  </table>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="orders">
              <Card>
                <CardHeader className="pb-2">
                  <p className="text-xs text-muted-foreground">
                    Local order attempts through this application. For complete exchange history, check Binance directly.
                  </p>
                </CardHeader>
                <CardContent className="p-0">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>TIME</th>
                        <th>SYMBOL</th>
                        <th>SIDE</th>
                        <th>TYPE</th>
                        <th>QTY</th>
                        <th>STATUS</th>
                        <th>NOTE</th>
                      </tr>
                    </thead>
                    <tbody>
                      {orders.length === 0 ? (
                        <tr>
                          <td colSpan={7} className="text-center py-8 text-muted-foreground">
                            No local orders found
                          </td>
                        </tr>
                      ) : (
                        orders.map((order) => (
                          <tr key={order.id} className={order.status === 'FAILED' ? 'opacity-60' : ''}>
                            <td className="font-mono text-xs">
                              {order.created_at ? new Date(order.created_at).toLocaleString() : '-'}
                            </td>
                            <td className="font-bold">{order.symbol}</td>
                            <td>
                              <Badge variant={order.side === 'BUY' ? 'success' : 'destructive'}>
                                {order.side}
                              </Badge>
                            </td>
                            <td className="font-mono text-xs">{order.order_type}</td>
                            <td className="font-mono">{order.quantity?.toFixed(4)}</td>
                            <td>
                              <Badge variant={
                                order.status === 'FILLED' ? 'success' :
                                order.status === 'FAILED' ? 'destructive' :
                                order.status === 'CANCELLED' ? 'warning' :
                                'secondary'
                              }>
                                {order.status}
                              </Badge>
                            </td>
                            <td className="text-xs text-muted-foreground max-w-[200px] truncate">
                              {order.notes?.split('\n')[0] || '-'}
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </>
      )}
    </div>
  )
}

// ==================== SHARED COMPONENTS ====================
function StatsCard({ title, value, change, icon, color = 'default' }) {
  const colorMap = {
    purple: 'border-[#D4A0FF]',
    green: 'border-[#6Ec85c]',
    red: 'border-[#e40046]',
    default: 'border-border'
  }

  return (
    <Card className={cn("", colorMap[color])}>
      <CardContent className="pt-6">
        <div className="flex items-start justify-between mb-2">
          <div className="text-xs font-mono text-muted-foreground">{title}</div>
          <div className="text-muted-foreground">{icon}</div>
        </div>
        <div className={cn(
          "text-2xl font-bold font-mono",
          change !== undefined && (change >= 0 ? "text-profit" : "text-loss")
        )}>
          {value}
        </div>
      </CardContent>
    </Card>
  )
}

function LogRow({ log }) {
  const [expanded, setExpanded] = useState(false)

  const getActionBadge = (action) => {
    const actionMap = {
      'OPEN_POSITION': { variant: 'success', text: 'OPEN' },
      'CLOSE_POSITION': { variant: 'destructive', text: 'CLOSE' },
      'PARTIAL_EXIT': { variant: 'warning', text: 'PARTIAL' },
      'STOP_LOSS': { variant: 'destructive', text: 'SL' },
      'TAKE_PROFIT': { variant: 'success', text: 'TP' },
      'SKIP': { variant: 'secondary', text: 'SKIP' },
      'ERROR': { variant: 'destructive', text: 'ERROR' }
    }
    const config = actionMap[action] || { variant: 'secondary', text: action }
    return <Badge variant={config.variant}>{config.text}</Badge>
  }

  return (
    <>
      <tr className="cursor-pointer hover:bg-muted/30" onClick={() => log.screening_data && setExpanded(!expanded)}>
        <td className="font-mono text-xs">{new Date(log.timestamp).toLocaleString()}</td>
        <td>{getActionBadge(log.action)}</td>
        <td className="font-bold">{log.symbol || '-'}</td>
        <td className="font-mono">
          {log.screening_score ? (
            <span className={cn(
              log.screening_score >= 80 ? 'text-profit font-bold' :
              log.screening_score >= 75 ? 'text-primary font-bold' :
              'text-muted-foreground'
            )}>
              {log.screening_score.toFixed(1)}
            </span>
          ) : '-'}
        </td>
        <td className="text-xs text-muted-foreground max-w-xs truncate">{log.reason}</td>
        <td>
          <Badge variant={log.success ? 'success' : 'destructive'}>
            {log.success ? 'OK' : 'FAIL'}
          </Badge>
        </td>
      </tr>
      {expanded && log.screening_data && (
        <tr>
          <td colSpan={6} className="bg-muted/30 p-4">
            <div className="grid grid-cols-3 md:grid-cols-6 gap-4 text-sm">
              <div><span className="text-muted-foreground">Timeframe</span><div className="font-mono">{log.screening_data.timeframe || '-'}</div></div>
              <div><span className="text-muted-foreground">Total Score</span><div className="font-mono font-bold">{log.screening_data.total_score?.toFixed(1)}</div></div>
              <div><span className="text-muted-foreground">Beta</span><div className="font-mono">{log.screening_data.beta_score?.toFixed(1)}</div></div>
              <div><span className="text-muted-foreground">Volume</span><div className="font-mono">{log.screening_data.volume_score?.toFixed(1)}</div></div>
              <div><span className="text-muted-foreground">Technical</span><div className="font-mono">{log.screening_data.technical_score?.toFixed(1)}</div></div>
              <div><span className="text-muted-foreground">Price</span><div className="font-mono">${log.screening_data.price?.toFixed(6)}</div></div>
            </div>
          </td>
        </tr>
      )}
    </>
  )
}
