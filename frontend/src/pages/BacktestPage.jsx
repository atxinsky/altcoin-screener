import React from 'react'
import { motion } from 'framer-motion'
import { BarChart3, ExternalLink } from 'lucide-react'
import { Button } from '@/components/ui/button'

export default function BacktestPage() {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center"
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
        <p className="text-muted-foreground max-w-xl mx-auto mb-8">
          Import your trading history and analyze performance with advanced metrics.
        </p>
        <Button
          size="lg"
          onClick={() => window.open('http://localhost:8501', '_blank')}
        >
          <ExternalLink className="w-4 h-4 mr-2" />
          OPEN IN NEW TAB
        </Button>
      </motion.div>
    </div>
  )
}
