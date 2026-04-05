import { useEffect, useState } from 'react'
import { api, type LineInfo } from '../common/api'

const TYPE_ORDER = ['metro', 'tram', 'nightbus', 'bus', 'rail', 'unknown']
const TYPE_LABELS: Record<string, string> = {
  metro:    '🚇 Metro',
  tram:     '🚋 Tram',
  nightbus: '🌙 Night Bus',
  bus:      '🚌 Bus',
  rail:     '🚂 Rail',
  unknown:  '❓ Other',
}

function normalizeType(type: string | undefined, name: string): string {
  if (!type && !name) return 'unknown'
  const n = name?.toUpperCase() ?? ''
  if (/^U\d/.test(n)) return 'metro'
  if (/^N\d/.test(n)) return 'nightbus'
  if (/^[SRNCE]\d/.test(n)) return 'rail'
  const t = (type ?? '').toLowerCase()
  if (t.includes('tram'))  return 'tram'
  if (t.includes('metro')) return 'metro'
  if (t.includes('night')) return 'nightbus'
  if (t.includes('bus'))   return 'bus'
  return 'unknown'
}

export default function LinesPage() {
  const [lines, setLines]   = useState<LineInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('')

  useEffect(() => {
    api.lines().then(d => {
      setLines(d.lines ?? [])
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [])

  const grouped = TYPE_ORDER.reduce<Record<string, LineInfo[]>>((acc, t) => {
    acc[t] = []
    return acc
  }, {})

  const q = filter.toLowerCase()
  lines
    .filter(l => !q || l.name.toLowerCase().includes(q))
    .forEach(l => {
      const t = normalizeType(l.type, l.name)
      ;(grouped[t] ?? (grouped['unknown'] ??= [])).push(l)
    })

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center gap-4">
        <h1 className="text-2xl font-bold text-white">Lines</h1>
        <input
          className="bg-gray-800 border border-gray-700 rounded px-3 py-1.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
          placeholder="Filter…"
          value={filter}
          onChange={e => setFilter(e.target.value)}
        />
      </div>

      {loading && (
        <div className="text-center py-8 text-gray-500 text-sm animate-pulse">Loading…</div>
      )}

      {TYPE_ORDER.map(type => {
        const bucket = grouped[type] ?? []
        if (bucket.length === 0) return null
        return (
          <section key={type}>
            <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-2">
              {TYPE_LABELS[type]} ({bucket.length})
            </h2>
            <div className="flex flex-wrap gap-2">
              {bucket
                .sort((a, b) => a.name.localeCompare(b.name, undefined, { numeric: true }))
                .map(l => {
                  const color = l.color?.startsWith('#') ? l.color : `#${l.color ?? '555'}`
                  return (
                    <a
                      key={l.name}
                      href={`http://localhost:3079/line/${l.name}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-gray-700 hover:border-gray-500 bg-gray-800 hover:bg-gray-750 transition-colors group"
                      title={l.description ?? l.name}
                    >
                      <span
                        className="w-3 h-3 rounded-full flex-shrink-0"
                        style={{ backgroundColor: color }}
                      />
                      <span className="text-sm font-semibold text-white group-hover:text-blue-300 transition-colors">
                        {l.name}
                      </span>
                    </a>
                  )
                })}
            </div>
          </section>
        )
      })}
    </div>
  )
}
