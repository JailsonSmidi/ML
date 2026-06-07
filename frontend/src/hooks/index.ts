import { useState, useEffect, useCallback } from 'react'
import { getSession, getBatches, getUnreadCount, getNotifications } from '../api'
import type { Session, Batch, Notification } from '../types'

// ─── useSession — polling de status ──────────────────────────────────────────

export function useSession(id: string | null, intervalMs = 8000) {
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetch = useCallback(async () => {
    if (!id) return
    try {
      const data = await getSession(id)
      setSession(data)
      setError(null)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => {
    fetch()
    const timer = setInterval(fetch, intervalMs)
    return () => clearInterval(timer)
  }, [fetch, intervalMs])

  return { session, loading, error, refetch: fetch }
}

// ─── useBatches — polling de lotes ───────────────────────────────────────────

export function useBatches(sessionId: string | null, intervalMs = 8000) {
  const [batches, setBatches] = useState<Batch[]>([])
  const [loading, setLoading] = useState(true)

  const fetch = useCallback(async () => {
    if (!sessionId) return
    try {
      const data = await getBatches(sessionId)
      setBatches(data)
    } finally {
      setLoading(false)
    }
  }, [sessionId])

  useEffect(() => {
    fetch()
    const timer = setInterval(fetch, intervalMs)
    return () => clearInterval(timer)
  }, [fetch, intervalMs])

  return { batches, loading, refetch: fetch }
}

// ─── useNotifications — polling do sino ──────────────────────────────────────

export function useNotifications(intervalMs = 30000) {
  const [unreadCount, setUnreadCount] = useState(0)
  const [notifications, setNotifications] = useState<Notification[]>([])

  const fetchCount = useCallback(async () => {
    try {
      const { count } = await getUnreadCount()
      setUnreadCount(count)
    } catch { /* silencioso */ }
  }, [])

  const fetchAll = useCallback(async () => {
    try {
      const data = await getNotifications()
      setNotifications(data)
      setUnreadCount(data.filter(n => !n.read).length)
    } catch { /* silencioso */ }
  }, [])

  useEffect(() => {
    fetchCount()
    const timer = setInterval(fetchCount, intervalMs)
    return () => clearInterval(timer)
  }, [fetchCount, intervalMs])

  return { unreadCount, notifications, fetchAll }
}
