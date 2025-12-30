import React from 'react'
import { motion } from 'framer-motion'
import { BarChart3, ExternalLink } from 'lucide-react'
import { Button } from '@/components/ui/button'

export default function BacktestPage() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center py-8"
      >
        <div className="inline-flex items-center gap-2 mb-4">
          <BarChart3 className="w-5 h-5 text-primary" />
          <span className="text-xs font-mono text-muted-foreground tracking-widest">
            BACKTEST ANALYSIS
          </span>
        </div>
        <h1 className="text-4xl font-bold mb-4">
          TRADING <span className="text-primary">BACKTEST</span>
        </h1>
        <p className="text-muted-foreground max-w-xl mx-auto mb-6">
          Import your trading history and analyze performance with advanced metrics.
        </p>
        <Button
          variant="outline"
          onClick={() => window.open('http://localhost:8502', '_blank')}
        >
          <ExternalLink className="w-4 h-4 mr-2" />
          OPEN IN NEW TAB
        </Button>
      </motion.div>

      {/* Embedded Streamlit */}
      <div className="border-2 border-border overflow-hidden" style={{ height: 'calc(100vh - 300px)' }}>
        <iframe
          src="http://localhost:8502"
          className="w-full h-full border-0"
          title="Backtest Analysis"
        />
      </div>
    </div>
  )
}
