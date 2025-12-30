import React from 'react'
import { Routes, Route } from 'react-router-dom'
import Layout from './components/layout/Layout'
import ScreenerPage from './pages/ScreenerPage'
import TradingPage from './pages/TradingPage'
import BacktestPage from './pages/BacktestPage'
import SettingsPage from './pages/SettingsPage'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<ScreenerPage />} />
        <Route path="/trading" element={<TradingPage />} />
        <Route path="/backtest" element={<BacktestPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Routes>
    </Layout>
  )
}

export default App
