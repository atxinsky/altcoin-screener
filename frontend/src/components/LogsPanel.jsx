import React, { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import {
  FileText,
  RefreshCw,
  Download,
  Search,
  Server,
  Activity,
  ChevronDown
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'
import { getMonitorLogs, getBackendLogs, exportLogs } from '@/services/api'

export default function LogsPanel() {
  const [activeService, setActiveService] = useState('monitor')
  const [logs, setLogs] = useState('')
  const [loading, setLoading] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [lineCount, setLineCount] = useState(200)
  const [autoRefresh, setAutoRefresh] = useState(false)
  const logContainerRef = useRef(null)
  const intervalRef = useRef(null)

  useEffect(() => {
    loadLogs()
  }, [activeService])

  useEffect(() => {
    if (autoRefresh) {
      intervalRef.current = setInterval(loadLogs, 10000) // 10 seconds
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [autoRefresh, activeService])

  const loadLogs = async () => {
    setLoading(true)
    try {
      let response
      if (activeService === 'monitor') {
        response = await getMonitorLogs(lineCount, searchTerm || null)
      } else {
        response = await getBackendLogs(lineCount)
      }
      if (response.success) {
        setLogs(response.logs)
        // Scroll to bottom
        if (logContainerRef.current) {
          logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight
        }
      }
    } catch (error) {
      console.error('Failed to load logs:', error)
      setLogs('Error loading logs: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  const handleExport = async (format) => {
    try {
      const blob = await exportLogs(activeService, 500, format)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
      a.download = `${activeService}_logs_${timestamp}.${format}`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Failed to export logs:', error)
    }
  }

  const handleSearch = (e) => {
    e.preventDefault()
    loadLogs()
  }

  // Highlight log lines
  const renderLogs = () => {
    if (!logs) return null

    return logs.split('\n').map((line, index) => {
      let lineClass = 'text-muted-foreground'

      // Color coding based on log content
      if (line.includes('ERROR') || line.includes('error') || line.includes('Error')) {
        lineClass = 'text-red-400'
      } else if (line.includes('WARNING') || line.includes('warning')) {
        lineClass = 'text-yellow-400'
      } else if (line.includes('SUCCESS') || line.includes('Opened') || line.includes('Entry:')) {
        lineClass = 'text-green-400'
      } else if (line.includes('Running screening') || line.includes('北京时间')) {
        lineClass = 'text-blue-400'
      } else if (line.includes('score:') || line.includes('Score')) {
        lineClass = 'text-cyan-400'
      }

      return (
        <div key={index} className={cn('font-mono text-xs whitespace-pre', lineClass)}>
          {line}
        </div>
      )
    })
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5" />
              SYSTEM LOGS
            </CardTitle>
            <CardDescription>View real-time system logs</CardDescription>
          </div>

          {/* Service Selector */}
          <div className="flex items-center gap-2">
            <Button
              variant={activeService === 'monitor' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setActiveService('monitor')}
            >
              <Activity className="w-4 h-4 mr-1" />
              Monitor
            </Button>
            <Button
              variant={activeService === 'backend' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setActiveService('backend')}
            >
              <Server className="w-4 h-4 mr-1" />
              Backend
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Controls */}
        <div className="flex items-center gap-4 flex-wrap">
          {/* Search (only for monitor) */}
          {activeService === 'monitor' && (
            <form onSubmit={handleSearch} className="flex items-center gap-2 flex-1 min-w-[200px]">
              <Input
                type="text"
                placeholder="Search logs..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="flex-1"
              />
              <Button type="submit" size="sm" variant="outline">
                <Search className="w-4 h-4" />
              </Button>
            </form>
          )}

          {/* Line count selector */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">Lines:</span>
            <select
              value={lineCount}
              onChange={(e) => setLineCount(Number(e.target.value))}
              className="bg-background border border-border rounded px-2 py-1 text-sm"
            >
              <option value={100}>100</option>
              <option value={200}>200</option>
              <option value={500}>500</option>
              <option value={1000}>1000</option>
            </select>
          </div>

          {/* Auto refresh toggle */}
          <Button
            variant={autoRefresh ? 'default' : 'outline'}
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            <RefreshCw className={cn('w-4 h-4 mr-1', autoRefresh && 'animate-spin')} />
            {autoRefresh ? 'Auto' : 'Manual'}
          </Button>

          {/* Refresh button */}
          <Button
            variant="outline"
            size="sm"
            onClick={loadLogs}
            disabled={loading}
          >
            <RefreshCw className={cn('w-4 h-4 mr-1', loading && 'animate-spin')} />
            Refresh
          </Button>

          {/* Export buttons */}
          <div className="flex items-center gap-1">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleExport('txt')}
            >
              <Download className="w-4 h-4 mr-1" />
              TXT
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleExport('md')}
            >
              <Download className="w-4 h-4 mr-1" />
              MD
            </Button>
          </div>
        </div>

        {/* Log display area */}
        <div
          ref={logContainerRef}
          className="bg-[#0d1117] border border-border rounded-lg p-4 h-[500px] overflow-auto"
        >
          {loading && !logs ? (
            <div className="flex items-center justify-center h-full">
              <RefreshCw className="w-6 h-6 animate-spin text-primary" />
            </div>
          ) : (
            <div className="space-y-0.5">
              {renderLogs()}
            </div>
          )}
        </div>

        {/* Status bar */}
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>
            Service: {activeService.toUpperCase()} |
            Lines: {logs ? logs.split('\n').length : 0}
          </span>
          <span>
            {autoRefresh ? 'Auto-refreshing every 10s' : 'Manual refresh mode'}
          </span>
        </div>
      </CardContent>
    </Card>
  )
}
