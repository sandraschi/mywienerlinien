import { useEffect, useState } from 'react'
import { api, type Alert } from '../common/api'

const SEV_STYLES: Record<string, string> = {
  high:   'border-red-600 bg-red-950/40',
  medium: 'border-orange-500 bg-orange-950/30',
  low:    'border-yellow-600 bg-yellow-950/20',
  info:   'border-blue-600 bg-blue-950/20',
}

const SEV_BADGE: Record<string, string> = {
  high:   'bg-red-700 text-white',
  medium: 'bg-orange-600 text-white',
  low:    'bg-yellow-700 text-white',
  info:   'bg-blue-700 text-white',
}

function fmtTime(iso: string | undefined): string {
  if (!iso) return ''
  try {
    return new Date(iso).toLocaleString('de-AT', {
      day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit'
    })
  } catch { return iso }
}

export default function DisruptionsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [updated, setUpdated] = useState<Date | null>(null)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const data = await api.trafficInfo()
      setAlerts(data.alerts ?? [])
      setUpdated(new Date())
    } catch (e) {
      setError(String(e))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    const id = setInterval(load, 5 * 60_000)
    return () => clearInterval(id)
  }, [])

  return (
    <div className="max-w-2xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">Service Disruptions</h1>
        <div className="flex items-center gap-2">
          {updated && (
            <span className="text-xs text-gray-500">
              {updated.toLocaleTimeString()}
            </span>
          )}
          <button
            onClick={load}
            className="text-xs px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded text-gray-300 transition-colors"
          >
            ↻ Refresh
          </button>
        </div>
      </div>

      {loading && (
        <div className="text-center py-8 text-gray-500 text-sm animate-pulse">Loading…</div>
      )}
      {error && (
        <div className="bg-red-900/30 border border-red-800 rounded-lg px-4 py-3 text-red-300 text-sm">
          {error}
        </div>
      )}
      {!loading && alerts.length === 0 && !error && (
        <div className="text-center py-16 text-gray-600">
          <div className="text-4xl mb-3">✅</div>
          <div className="text-sm">No active service disruptions</div>
        </div>
      )}

      {alerts.map((a, i) => {
        const sev = (a.severity ?? 'info').toLowerCase()
        const borderCls = SEV_STYLES[sev] ?? SEV_STYLES.info
        const badgeCls  = SEV_BADGE[sev]  ?? SEV_BADGE.info
        return (
          <div key={a.id ?? i} className={`border rounded-lg p-4 space-y-2 ${borderCls}`}>
            {/* Title row */}
            <div className="flex items-start gap-3">
              <span className={`text-xs font-bold px-2 py-0.5 rounded uppercase ${badgeCls}`}>
                {sev}
              </span>
              <span className="text-white font-semibold text-sm leading-snug flex-1">
                {a.title || '(no title)'}
              </span>
            </div>

            {/* Description */}
            {a.description && (
              <p className="text-gray-300 text-sm leading-relaxed">{a.description}</p>
            )}

            {/* Affected lines */}
            {a.lines?.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {a.lines.map(l => (
                  <span
                    key={l}
                    className="px-2 py-0.5 bg-gray-700 text-gray-200 text-xs font-mono rounded"
                  >
                    {l}
                  </span>
                ))}
              </div>
            )}

            {/* Times */}
            {(a.start_time || a.end_time) && (
              <div className="text-xs text-gray-500 flex gap-4">
                {a.start_time && <span>From: {fmtTime(a.start_time)}</span>}
                {a.end_time   && <span>Until: {fmtTime(a.end_time)}</span>}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
