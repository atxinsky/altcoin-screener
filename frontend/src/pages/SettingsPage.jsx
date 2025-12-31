import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  Settings,
  Bell,
  Mail,
  Send,
  Save,
  RefreshCw,
  Moon,
  Clock,
  FileText
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Switch } from '@/components/ui/switch'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { cn } from '@/lib/utils'
import {
  getNotificationSettings,
  updateNotificationSettings,
  testNotification
} from '@/services/api'
import LogsPanel from '@/components/LogsPanel'

export default function SettingsPage() {
  const [settings, setSettings] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)

  useEffect(() => {
    loadSettings()
  }, [])

  const loadSettings = async () => {
    setLoading(true)
    try {
      const response = await getNotificationSettings()
      if (response.success) {
        setSettings(response.settings)
      }
    } catch (error) {
      console.error('Failed to load settings:', error)
      // Set default settings so page doesn't spin forever
      setSettings({
        email_enabled: false,
        telegram_enabled: false,
        min_interval_minutes: 30,
        daily_limit: 10,
        min_score_threshold: 70,
        notify_top_n: 5,
        quiet_hours_enabled: false,
        quiet_hours_start: 22,
        quiet_hours_end: 7,
        notify_high_score: true,
        notify_new_signals: true,
        notify_position_updates: true
      })
    } finally {
      setLoading(false)
    }
  }

  const saveSettings = async () => {
    setSaving(true)
    try {
      await updateNotificationSettings(settings)
    } catch (error) {
      console.error('Failed to save settings:', error)
    } finally {
      setSaving(false)
    }
  }

  const handleTestNotification = async () => {
    setTesting(true)
    try {
      await testNotification()
    } catch (error) {
      console.error('Failed to send test notification:', error)
    } finally {
      setTesting(false)
    }
  }

  const updateSetting = (key, value) => {
    setSettings(prev => ({ ...prev, [key]: value }))
  }

  if (loading || !settings) {
    return (
      <div className="flex items-center justify-center py-20">
        <RefreshCw className="w-6 h-6 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="flex items-center gap-2 mb-2">
          <Settings className="w-5 h-5 text-primary" />
          <span className="text-xs font-mono text-muted-foreground tracking-widest">
            CONFIGURATION
          </span>
        </div>
        <h1 className="text-3xl font-bold mb-2">
          SYSTEM <span className="text-primary">SETTINGS</span>
        </h1>
        <p className="text-muted-foreground">
          Configure notifications and view system logs.
        </p>
      </motion.div>

      <Tabs defaultValue="notifications" className="space-y-6">
        <TabsList className="grid w-full grid-cols-2 max-w-[400px]">
          <TabsTrigger value="notifications" className="flex items-center gap-2">
            <Bell className="w-4 h-4" />
            Notifications
          </TabsTrigger>
          <TabsTrigger value="logs" className="flex items-center gap-2">
            <FileText className="w-4 h-4" />
            System Logs
          </TabsTrigger>
        </TabsList>

        <TabsContent value="notifications" className="space-y-6">

      {/* Notification Channels */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="w-5 h-5" />
            NOTIFICATION CHANNELS
          </CardTitle>
          <CardDescription>Enable or disable notification methods</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between py-4 border-b border-border">
            <div className="flex items-center gap-4">
              <Mail className="w-5 h-5 text-muted-foreground" />
              <div>
                <div className="font-bold">Email Notifications</div>
                <div className="text-sm text-muted-foreground">
                  Receive alerts via email
                </div>
              </div>
            </div>
            <Switch
              checked={settings.email_enabled}
              onCheckedChange={(val) => updateSetting('email_enabled', val)}
            />
          </div>

          <div className="flex items-center justify-between py-4">
            <div className="flex items-center gap-4">
              <Send className="w-5 h-5 text-muted-foreground" />
              <div>
                <div className="font-bold">Telegram Notifications</div>
                <div className="text-sm text-muted-foreground">
                  Receive alerts via Telegram bot
                </div>
              </div>
            </div>
            <Switch
              checked={settings.telegram_enabled}
              onCheckedChange={(val) => updateSetting('telegram_enabled', val)}
            />
          </div>
        </CardContent>
      </Card>

      {/* Frequency Control */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="w-5 h-5" />
            FREQUENCY CONTROL
          </CardTitle>
          <CardDescription>Control notification frequency to avoid spam</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="text-xs font-mono text-muted-foreground mb-2 block">
                MIN INTERVAL (MINUTES)
              </label>
              <Input
                type="number"
                value={settings.min_interval_minutes}
                onChange={(e) => updateSetting('min_interval_minutes', Number(e.target.value))}
                min={1}
                max={1440}
              />
            </div>
            <div>
              <label className="text-xs font-mono text-muted-foreground mb-2 block">
                DAILY LIMIT
              </label>
              <Input
                type="number"
                value={settings.daily_limit}
                onChange={(e) => updateSetting('daily_limit', Number(e.target.value))}
                min={1}
                max={100}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="text-xs font-mono text-muted-foreground mb-2 block">
                MIN SCORE THRESHOLD
              </label>
              <Input
                type="number"
                value={settings.min_score_threshold}
                onChange={(e) => updateSetting('min_score_threshold', Number(e.target.value))}
                min={0}
                max={100}
              />
            </div>
            <div>
              <label className="text-xs font-mono text-muted-foreground mb-2 block">
                TOP N RESULTS
              </label>
              <Input
                type="number"
                value={settings.notify_top_n}
                onChange={(e) => updateSetting('notify_top_n', Number(e.target.value))}
                min={1}
                max={20}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Quiet Hours */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Moon className="w-5 h-5" />
                QUIET HOURS
              </CardTitle>
              <CardDescription>No notifications during these hours (Beijing Time)</CardDescription>
            </div>
            <Switch
              checked={settings.quiet_hours_enabled}
              onCheckedChange={(val) => updateSetting('quiet_hours_enabled', val)}
            />
          </div>
        </CardHeader>
        {settings.quiet_hours_enabled && (
          <CardContent>
            <div className="grid grid-cols-2 gap-6">
              <div>
                <label className="text-xs font-mono text-muted-foreground mb-2 block">
                  START HOUR
                </label>
                <Input
                  type="number"
                  value={settings.quiet_hours_start}
                  onChange={(e) => updateSetting('quiet_hours_start', Number(e.target.value))}
                  min={0}
                  max={23}
                />
              </div>
              <div>
                <label className="text-xs font-mono text-muted-foreground mb-2 block">
                  END HOUR
                </label>
                <Input
                  type="number"
                  value={settings.quiet_hours_end}
                  onChange={(e) => updateSetting('quiet_hours_end', Number(e.target.value))}
                  min={0}
                  max={23}
                />
              </div>
            </div>
          </CardContent>
        )}
      </Card>

      {/* Notification Types */}
      <Card>
        <CardHeader>
          <CardTitle>NOTIFICATION TYPES</CardTitle>
          <CardDescription>Choose which events trigger notifications</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between py-3">
            <div>
              <div className="font-medium">High Score Opportunities</div>
              <div className="text-sm text-muted-foreground">
                Notify when high-scoring altcoins are detected
              </div>
            </div>
            <Switch
              checked={settings.notify_high_score}
              onCheckedChange={(val) => updateSetting('notify_high_score', val)}
            />
          </div>

          <div className="flex items-center justify-between py-3">
            <div>
              <div className="font-medium">New Signals</div>
              <div className="text-sm text-muted-foreground">
                Notify on new technical signals (MACD, volume surge, etc.)
              </div>
            </div>
            <Switch
              checked={settings.notify_new_signals}
              onCheckedChange={(val) => updateSetting('notify_new_signals', val)}
            />
          </div>

          <div className="flex items-center justify-between py-3">
            <div>
              <div className="font-medium">Position Updates</div>
              <div className="text-sm text-muted-foreground">
                Notify on simulated position changes (open/close)
              </div>
            </div>
            <Switch
              checked={settings.notify_position_updates}
              onCheckedChange={(val) => updateSetting('notify_position_updates', val)}
            />
          </div>
        </CardContent>
      </Card>

      {/* Save Button */}
      <div className="flex justify-end">
        <Button onClick={saveSettings} disabled={saving} className="min-w-[160px]">
          {saving ? (
            <>
              <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
              SAVING...
            </>
          ) : (
            <>
              <Save className="w-4 h-4 mr-2" />
              SAVE SETTINGS
            </>
          )}
        </Button>
      </div>

        </TabsContent>

        <TabsContent value="logs">
          <LogsPanel />
        </TabsContent>

      </Tabs>
    </div>
  )
}
