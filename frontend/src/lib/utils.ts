import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(date: string | Date): string {
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(date))
}

export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(amount)
}

export function formatCO2e(amount: number): string {
  if (amount >= 1000) {
    return `${(amount / 1000).toFixed(1)}k tCO₂e`
  }
  return `${amount.toFixed(1)} tCO₂e`
}

export function getStatusColor(status: string): string {
  const statusColors: Record<string, string> = {
    submitted: 'bg-blue-100 text-blue-800',
    ai_analysis_pending: 'bg-yellow-100 text-yellow-800',
    ai_analysis_in_progress: 'bg-yellow-100 text-yellow-800',
    verified: 'bg-cyan-100 text-cyan-800',
    ai_verified: 'bg-cyan-100 text-cyan-800',
    ai_rejected: 'bg-red-100 text-red-800',
    ai_analyzed: 'bg-purple-100 text-purple-800',
    authority_reviewed: 'bg-indigo-100 text-indigo-800',
    community_reviewed: 'bg-emerald-100 text-emerald-800',
    approved: 'bg-green-100 text-green-800',
    rejected: 'bg-red-100 text-red-800',
    minted: 'bg-primary-100 text-primary-800',
  }
  return statusColors[status] || 'bg-gray-100 text-gray-800'
}

export function getStatusLabel(status: string): string {
  const statusLabels: Record<string, string> = {
    submitted: 'Submitted',
    ai_analysis_pending: 'AI Analysis Pending',
    ai_analysis_in_progress: 'AI Analysis In Progress',
    verified: 'Verified',
    ai_verified: 'AI Verified',
    ai_rejected: 'AI Rejected',
    ai_analyzed: 'AI Analyzed',
    authority_reviewed: 'Authority Reviewed',
    community_reviewed: 'Community Reviewed',
    approved: 'Approved',
    rejected: 'Rejected',
    minted: 'Credits Minted',
  }
  return statusLabels[status] || status.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}