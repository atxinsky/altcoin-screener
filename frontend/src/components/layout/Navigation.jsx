import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { cn } from '@/lib/utils'
import {
  Activity,
  TrendingUp,
  Settings,
  BarChart3,
  Wallet,
  Github
} from 'lucide-react'

const navItems = [
  { path: '/', label: 'SCREENER', icon: Activity },
  { path: '/trading', label: 'TRADING', icon: TrendingUp },
  { path: '/backtest', label: 'BACKTEST', icon: BarChart3 },
  { path: '/settings', label: 'SETTINGS', icon: Settings },
]

export default function Navigation() {
  const location = useLocation()

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-background/95 backdrop-blur-sm border-b-2 border-border">
      <div className="container mx-auto px-6">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-3">
            <div className="w-8 h-8 bg-foreground flex items-center justify-center">
              <div className="w-4 h-4 bg-primary"></div>
            </div>
            <span className="font-bold text-sm tracking-widest">TRETRA</span>
          </Link>

          {/* Navigation Links */}
          <div className="flex items-center gap-1">
            {navItems.map((item) => {
              const isActive = location.pathname === item.path
              const Icon = item.icon
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={cn(
                    "flex items-center gap-2 px-4 py-2 text-xs font-bold tracking-wider transition-all duration-200",
                    isActive
                      ? "text-primary border-b-2 border-primary"
                      : "text-muted-foreground hover:text-foreground"
                  )}
                >
                  <Icon className="w-4 h-4" />
                  {item.label}
                </Link>
              )
            })}
          </div>

          {/* Right side - Status indicator & GitHub */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-[#6Ec85c] rounded-full animate-pulse"></div>
              <span className="text-xs font-mono text-muted-foreground">LIVE</span>
            </div>
            <a
              href="https://github.com/atxinsky/altcoin-screener-V2"
              target="_blank"
              rel="noopener noreferrer"
              className="text-muted-foreground hover:text-foreground transition-colors"
              title="View on GitHub"
            >
              <Github className="w-5 h-5" />
            </a>
          </div>
        </div>
      </div>
    </nav>
  )
}
