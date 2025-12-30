import React from 'react'
import Navigation from './Navigation'

export default function Layout({ children }) {
  return (
    <div className="min-h-screen bg-background text-foreground dark">
      {/* Grid background */}
      <div className="fixed inset-0 bg-grid pointer-events-none opacity-30"></div>

      {/* Light rays effect */}
      <div className="fixed inset-0 bg-light-rays pointer-events-none"></div>

      {/* Navigation */}
      <Navigation />

      {/* Main content */}
      <main className="relative pt-20 pb-8 min-h-screen">
        <div className="container mx-auto px-6">
          {children}
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t-2 border-border py-6">
        <div className="container mx-auto px-6">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span className="font-mono">TRETRA TRADING STATION v2.0</span>
            <span className="font-mono">Powered by Ledger Design System</span>
          </div>
        </div>
      </footer>
    </div>
  )
}
