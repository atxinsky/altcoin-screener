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
  Settings,
  Activity
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
import { cn, formatNumber, formatPercent, formatPrice } from '@/lib/utils'
import axios from 'axios'

const API_BASE = '/api/sim-trading'

export default function TradingPage() {
  const [accounts, setAccounts] = useState([])
  const [selectedAccount, setSelectedAccount] = useState(null)
  const [positions, setPositions] = useState([])
  const [trades, setTrades] = useState([])
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(false)
  const [showCreateModal, setShowCreateModal] = useState(false)

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
      const response = await axios.get(`${API_BASE}/accounts`)
      const accountsList = response.data.accounts || []
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
        axios.get(`${API_BASE}/accounts/${accountId}/positions`),
        axios.get(`${API_BASE}/accounts/${accountId}/trades`),
        axios.get(`${API_BASE}/accounts/${accountId}/logs?limit=50`)
      ])
      setPositions(posRes.data.positions || [])
      setTrades(tradeRes.data.trades || [])
      setLogs(logRes.data.logs || [])
    } catch (error) {
      console.error('Failed to load account data:', error)
    }
  }

  const handleToggleAutoTrading = async () => {
    if (!selectedAccount) return
    try {
      const newStatus = !selectedAccount.auto_trading_enabled
      await axios.patch(`${API_BASE}/accounts/${selectedAccount.id}`, {
        auto_trading_enabled: newStatus
      })
      loadAccounts()
    } catch (error) {
      console.error('Failed to toggle auto trading:', error)
    }
  }

  const handleTriggerAutoTrade = async () => {
    if (!selectedAccount) return
    try {
      setLoading(true)
      await axios.post(`${API_BASE}/accounts/${selectedAccount.id}/auto-trade`)
      loadAccountData(selectedAccount.id)
      loadAccounts()
    } catch (error) {
      console.error('Failed to trigger auto trade:', error)
    } finally {
      setLoading(false)
    }
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

      {/* Account Selector & Stats */}
      {selectedAccount && (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          {/* Account Selector */}
          <Card className="md:col-span-1">
            <CardContent className="pt-6">
              <label className="text-xs font-mono text-muted-foreground mb-2 block">
                SELECT ACCOUNT
              </label>
              <Select
                value={selectedAccount?.id?.toString()}
                onValueChange={(val) => {
                  const acc = accounts.find(a => a.id.toString() === val)
                  setSelectedAccount(acc)
                }}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {accounts.map((acc) => (
                    <SelectItem key={acc.id} value={acc.id.toString()}>
                      {acc.account_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <div className="mt-4 flex items-center justify-between">
                <span className="text-xs text-muted-foreground">AUTO TRADE</span>
                <Switch
                  checked={selectedAccount.auto_trading_enabled}
                  onCheckedChange={handleToggleAutoTrading}
                />
              </div>
            </CardContent>
          </Card>

          {/* Stats */}
          <StatsCard
            title="TOTAL EQUITY"
            value={`$${formatNumber(selectedAccount.total_equity)}`}
            color="purple"
          />
          <StatsCard
            title="TOTAL P&L"
            value={`$${formatNumber(selectedAccount.total_pnl)}`}
            change={selectedAccount.total_pnl}
            color={selectedAccount.total_pnl >= 0 ? 'green' : 'red'}
          />
          <StatsCard
            title="WIN RATE"
            value={`${(selectedAccount.win_rate * 100).toFixed(1)}%`}
            color="default"
          />
          <StatsCard
            title="TRADES"
            value={selectedAccount.total_trades}
            color="default"
          />
        </div>
      )}

      {/* Control Buttons */}
      {selectedAccount && (
        <div className="flex gap-4">
          <Button
            onClick={handleTriggerAutoTrade}
            disabled={loading}
            className="min-w-[180px]"
          >
            {loading ? (
              <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Play className="w-4 h-4 mr-2" />
            )}
            TRIGGER SCAN
          </Button>

          <Button variant="outline" onClick={() => loadAccountData(selectedAccount.id)}>
            <RefreshCw className="w-4 h-4 mr-2" />
            REFRESH
          </Button>
        </div>
      )}

      {/* Tabs: Positions / Trades / Logs */}
      {selectedAccount && (
        <Tabs defaultValue="positions" className="w-full">
          <TabsList>
            <TabsTrigger value="positions">
              POSITIONS ({positions.length})
            </TabsTrigger>
            <TabsTrigger value="trades">
              TRADES ({trades.length})
            </TabsTrigger>
            <TabsTrigger value="logs">
              LOGS ({logs.length})
            </TabsTrigger>
          </TabsList>

          <TabsContent value="positions">
            <Card>
              <CardContent className="p-0">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>SYMBOL</th>
                      <th>ENTRY</th>
                      <th>CURRENT</th>
                      <th>QTY</th>
                      <th>P&L</th>
                      <th>SL / TP</th>
                    </tr>
                  </thead>
                  <tbody>
                    {positions.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="text-center py-8 text-muted-foreground">
                          No open positions
                        </td>
                      </tr>
                    ) : (
                      positions.map((pos) => (
                        <tr key={pos.id}>
                          <td className="font-bold">{pos.symbol}</td>
                          <td className="font-mono">${formatPrice(pos.entry_price)}</td>
                          <td className="font-mono">${formatPrice(pos.current_price)}</td>
                          <td className="font-mono">{pos.quantity?.toFixed(4)}</td>
                          <td>
                            <span className={cn(
                              "font-mono font-bold",
                              pos.unrealized_pnl_pct >= 0 ? "text-profit" : "text-loss"
                            )}>
                              {formatPercent(pos.unrealized_pnl_pct)}
                            </span>
                          </td>
                          <td className="font-mono text-xs">
                            <span className="text-loss">${formatPrice(pos.stop_loss_price)}</span>
                            {' / '}
                            <span className="text-profit">
                              ${formatPrice(pos.take_profit_prices?.[0])}
                            </span>
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
                    <tr>
                      <th>TIME</th>
                      <th>SYMBOL</th>
                      <th>SIDE</th>
                      <th>PRICE</th>
                      <th>QTY</th>
                      <th>P&L</th>
                      <th>TYPE</th>
                    </tr>
                  </thead>
                  <tbody>
                    {trades.length === 0 ? (
                      <tr>
                        <td colSpan={7} className="text-center py-8 text-muted-foreground">
                          No trades yet
                        </td>
                      </tr>
                    ) : (
                      trades.map((trade) => (
                        <tr key={trade.id}>
                          <td className="font-mono text-xs">
                            {new Date(trade.trade_time).toLocaleString()}
                          </td>
                          <td className="font-bold">{trade.symbol}</td>
                          <td>
                            <Badge variant={trade.side === 'BUY' ? 'success' : 'destructive'}>
                              {trade.side}
                            </Badge>
                          </td>
                          <td className="font-mono">${formatPrice(trade.price)}</td>
                          <td className="font-mono">{trade.quantity?.toFixed(4)}</td>
                          <td>
                            {trade.pnl !== null ? (
                              <span className={cn(
                                "font-mono",
                                trade.pnl >= 0 ? "text-profit" : "text-loss"
                              )}>
                                {formatPercent(trade.pnl_pct)}
                              </span>
                            ) : '-'}
                          </td>
                          <td className="text-xs text-muted-foreground">
                            {trade.trade_type}
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
                    <tr>
                      <th>TIME</th>
                      <th>ACTION</th>
                      <th>SYMBOL</th>
                      <th>SCORE</th>
                      <th>REASON</th>
                    </tr>
                  </thead>
                  <tbody>
                    {logs.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="text-center py-8 text-muted-foreground">
                          No logs yet
                        </td>
                      </tr>
                    ) : (
                      logs.map((log) => (
                        <tr key={log.id}>
                          <td className="font-mono text-xs">
                            {new Date(log.timestamp).toLocaleString()}
                          </td>
                          <td>
                            <Badge
                              variant={
                                log.action === 'OPEN_POSITION' ? 'success' :
                                log.action === 'SKIP' ? 'secondary' :
                                'destructive'
                              }
                            >
                              {log.action}
                            </Badge>
                          </td>
                          <td className="font-bold">{log.symbol || '-'}</td>
                          <td className="font-mono">
                            {log.screening_score?.toFixed(1) || '-'}
                          </td>
                          <td className="text-xs text-muted-foreground max-w-xs truncate">
                            {log.reason}
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
      )}
    </div>
  )
}

function StatsCard({ title, value, change, color = 'default' }) {
  const colorMap = {
    purple: 'border-[#D4A0FF]',
    green: 'border-[#6Ec85c]',
    red: 'border-[#e40046]',
    default: 'border-border'
  }

  return (
    <Card className={cn("", colorMap[color])}>
      <CardContent className="pt-6">
        <div className="text-xs font-mono text-muted-foreground mb-2">
          {title}
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
