import axios from 'axios'

const API_BASE_URL = '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5 minutes for screening
  headers: {
    'Content-Type': 'application/json',
  },
})

// Market endpoints
export const getMarketOverview = async () => {
  const response = await api.get('/market-overview')
  return response.data
}

export const getSymbols = async () => {
  const response = await api.get('/symbols')
  return response.data
}

// Screening endpoints
export const screenAltcoins = async (params) => {
  const response = await api.post('/screen', params)
  return response.data
}

export const getTopOpportunities = async (limit = 20, minScore = 60) => {
  const response = await api.get('/top-opportunities', {
    params: { limit, min_score: minScore }
  })
  return response.data
}

// Chart endpoints
export const generateChart = async (symbol, timeframe = '5m', showIndicators = true) => {
  const response = await api.post('/chart', {
    symbol,
    timeframe,
    show_indicators: showIndicators
  })
  return response.data
}

// Data endpoints
export const getHistoricalData = async (symbol, timeframe = '5m', days = 7) => {
  const response = await api.get('/historical', {
    params: { symbol, timeframe, days }
  })
  return response.data
}

export const getIndicators = async (symbol, timeframe = '5m') => {
  const response = await api.get('/indicators', {
    params: { symbol, timeframe }
  })
  return response.data
}

// Stats endpoints
export const getStats = async () => {
  const response = await api.get('/stats')
  return response.data
}

// Historical rankings endpoints
export const getHistoricalRankings = async (days = 3, limit = 20) => {
  const response = await api.get('/history/rankings', {
    params: { days, limit }
  })
  return response.data
}

export const getSymbolHistory = async (symbol, days = 7) => {
  const response = await api.get('/history/symbol', {
    params: { symbol, days }
  })
  return response.data
}

export const getRecentScreenings = async (hours = 24, minScore = 0) => {
  const response = await api.get('/history/recent', {
    params: { hours, min_score: minScore }
  })
  return response.data
}

// Trading endpoints
export const createMarketOrder = async (symbol, side, quantity, notes = null) => {
  const response = await api.post('/trade/market', {
    symbol,
    side,
    quantity,
    notes
  })
  return response.data
}

export const createLimitOrder = async (symbol, side, quantity, price, notes = null) => {
  const response = await api.post('/trade/limit', {
    symbol,
    side,
    quantity,
    price,
    notes
  })
  return response.data
}

export const cancelOrder = async (orderId) => {
  const response = await api.delete(`/trade/${orderId}`)
  return response.data
}

export const getOrderHistory = async (symbol = null, limit = 50) => {
  const response = await api.get('/trade/history', {
    params: { symbol, limit }
  })
  return response.data
}

export const getBalance = async (asset = 'USDT') => {
  const response = await api.get('/trade/balance', {
    params: { asset }
  })
  return response.data
}

export const getAllBalances = async () => {
  const response = await api.get('/trade/balances')
  return response.data
}

// Watchlist endpoints
export const addToWatchlist = async (symbol, notes = null) => {
  const response = await api.post('/watchlist', {
    symbol,
    notes
  })
  return response.data
}

export const getWatchlist = async () => {
  const response = await api.get('/watchlist')
  return response.data
}

export const removeFromWatchlist = async (symbol) => {
  const response = await api.delete(`/watchlist/${symbol}`)
  return response.data
}

// Top Gainers endpoint
export const getTopGainers = async (limit = 20, minVolume = 1000000) => {
  const response = await api.get('/top-gainers', {
    params: { limit, min_volume: minVolume }
  })
  return response.data
}

// Notification Settings endpoints
export const getNotificationSettings = async () => {
  const response = await api.get('/notification-settings')
  return response.data
}

export const updateNotificationSettings = async (settings) => {
  const response = await api.post('/notification-settings', settings)
  return response.data
}

export const testNotification = async () => {
  const response = await api.post('/notification-settings/test')
  return response.data
}

export const resetDailyNotificationCount = async () => {
  const response = await api.post('/notification-settings/reset-daily-count')
  return response.data
}

// Sim-Trading Account endpoints
export const getSimTradingAccounts = async () => {
  const response = await api.get('/sim-trading/accounts')
  return response.data
}

export const createSimTradingAccount = async (accountData) => {
  const response = await api.post('/sim-trading/accounts', accountData)
  return response.data
}

export const getSimTradingAccount = async (accountId) => {
  const response = await api.get(`/sim-trading/accounts/${accountId}`)
  return response.data
}

export const deleteSimTradingAccount = async (accountId) => {
  const response = await api.delete(`/sim-trading/accounts/${accountId}`)
  return response.data
}

export const toggleAutoTrading = async (accountId, enabled) => {
  // Use PATCH to update account settings (not POST which triggers auto-trade)
  const response = await api.patch(`/sim-trading/accounts/${accountId}`, {
    auto_trading_enabled: enabled
  })
  return response.data
}

export const checkAccountExits = async (accountId) => {
  const response = await api.post(`/sim-trading/accounts/${accountId}/check-exits`)
  return response.data
}

// Sim-Trading Position endpoints
export const getAccountPositions = async (accountId) => {
  const response = await api.get(`/sim-trading/accounts/${accountId}/positions`)
  return response.data
}

export const openSimPosition = async (accountId, symbol, entryPrice = null) => {
  const response = await api.post(`/sim-trading/accounts/${accountId}/positions`, {
    symbol,
    entry_price: entryPrice
  })
  return response.data
}

export const closePosition = async (positionId, exitPrice = null) => {
  const response = await api.delete(`/sim-trading/positions/${positionId}`, {
    params: exitPrice ? { exit_price: exitPrice } : {}
  })
  return response.data
}

// Sim-Trading Trade History endpoints
export const getAccountTrades = async (accountId, limit = 50) => {
  const response = await api.get(`/sim-trading/accounts/${accountId}/trades`, {
    params: { limit }
  })
  return response.data
}

// Sim-Trading Logs endpoints
export const getAccountLogs = async (accountId, limit = 100) => {
  const response = await api.get(`/sim-trading/accounts/${accountId}/logs`, {
    params: { limit }
  })
  return response.data
}

// System Logs endpoints
export const getMonitorLogs = async (lines = 200, search = null) => {
  const response = await api.get('/logs/monitor', {
    params: { lines, search }
  })
  return response.data
}

export const getBackendLogs = async (lines = 200) => {
  const response = await api.get('/logs/backend', {
    params: { lines }
  })
  return response.data
}

export const exportLogs = async (service = 'monitor', lines = 500, format = 'txt') => {
  const response = await api.get('/logs/export', {
    params: { service, lines, format },
    responseType: 'blob'
  })
  return response.data
}

export default api
