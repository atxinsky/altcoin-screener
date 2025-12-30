import { clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs) {
  return twMerge(clsx(inputs))
}

// Format number with commas
export function formatNumber(num, decimals = 2) {
  if (num === null || num === undefined) return '-'
  return num.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  })
}

// Format percentage
export function formatPercent(num, decimals = 2) {
  if (num === null || num === undefined) return '-'
  const sign = num >= 0 ? '+' : ''
  return `${sign}${num.toFixed(decimals)}%`
}

// Format price with appropriate decimals
export function formatPrice(price) {
  if (price === null || price === undefined) return '-'
  if (price < 0.0001) return price.toFixed(8)
  if (price < 0.01) return price.toFixed(6)
  if (price < 1) return price.toFixed(4)
  if (price < 100) return price.toFixed(2)
  return price.toFixed(2)
}

// Format volume
export function formatVolume(vol) {
  if (vol === null || vol === undefined) return '-'
  if (vol >= 1e9) return `${(vol / 1e9).toFixed(2)}B`
  if (vol >= 1e6) return `${(vol / 1e6).toFixed(2)}M`
  if (vol >= 1e3) return `${(vol / 1e3).toFixed(2)}K`
  return vol.toFixed(2)
}

// Time ago formatter
export function timeAgo(date) {
  const now = new Date()
  const past = new Date(date)
  const diff = Math.floor((now - past) / 1000)

  if (diff < 60) return `${diff}s ago`
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}
