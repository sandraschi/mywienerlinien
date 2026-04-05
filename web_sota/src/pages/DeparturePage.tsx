import { useCallback, useEffect, useRef, useState } from 'react'
import { api, type Departure, type Station } from '../common/api'

const LINE_COLORS: Record<string, string> = {
  metro:    'bg-red-600',
  tram:     'bg-orange-500',
  bus:      'bg-blue-600',
  nightbus: 'bg-indigo-900',
  rail:     'bg-green-700',
}

function lineColor(type: string, name: string): string {
  if (/^U\d/i.test(name)) return LINE_COLORS.metro
  if (/^N\d/i.test(name)) return LINE_COLORS.nightbus
  if (/^[SRNCE]\d/.test(name)) return LINE_COLORS.rail
  return LINE_COLORS[type?.toLowerCase()] ?? 'bg-gray-600'
}

function countdown(cd: number): { text: string; cls: string } {
  if (cd <= 0) return { text: 'now', cls: 'text-green-400 font-bold' }
  if (cd === 1) return { text: '1 min', cls: 'text-green-300 font-bold' }
  if (cd <= 3)  return { text: `${cd} min`, cls: 'text-yellow-300 font-semibold' }
  return { text: `${cd} min`, cls: 'text-gray-200' }
}

interface FavStop { name: string; rbl: string }

const LS_FAVS = 'wl_fav_stops'
const LS_LAST = 'wl_last_stop'

function loadFavs(): FavStop[] {
  try { return JSON.parse(localStorage.getItem(LS_FAVS) ?? '[]') } catch { return [] }
}
function saveFavs(f: FavStop[]) {
  localStorage.setItem(LS_FAVS, JSON.stringify(f))
}

export default function DeparturePage() {
  const [query, setQuery]             = useState('')
  const [suggestions, setSuggestions] = useState<Station[]>([])
  const [selected, setSelected]       = useState<Station | null>(null)
  const [deps, setDeps]               = useState<Departure[]>([])
  const [loading, setLoading]         = useState(false)
  const [error, setError]             = useState<string | null>(null)
  const [favs, setFavs]               = useState<FavStop[]>(loadFavs)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  const intervalRef                   = useRef<ReturnType<typeof setInterval> | null>(null)

  // Restore last stop on mount
  useEffect(() => {
    const last = localStorage.getItem(LS_LAST)
    if (last) {
      try {
        const s: Station = JSON.parse(last)
        setSelected(s)
        setQuery(s.name)
      } catch {}
    }
  }, [])

  // Fetch departures
  const fetchDeps = useCallback(async (stop: Station) => {
    if (!stop.rbl) return
    setLoading(true)
    setError(null)
    try {
      const data = await api.arrivals(stop.rbl)
      const sorted = [...(data.vehicles ?? [])].sort(
        (a, b) => (a.countdown ?? 99) - (b.countdown ?? 99)
      )
      setDeps(sorted)
      setLastUpdated(new Date())
    } catch (e) {
      setError(String(e))
    } finally {
      setLoading(false)
    }
  }, [])

  // Auto-refresh every 30s
  useEffect(() => {
    if (!selected) return
    fetchDeps(selected)
    intervalRef.current = setInterval(() => fetchDeps(selected), 30_000)
    return () => { if (intervalRef.current) clearInterval(intervalRef.current) }
  }, [selected, fetchDeps])

  // Stop search
  useEffect(() => {
    if (query.length < 2) { setSuggestions([]); return }
    const tid = setTimeout(async () => {
      const results = await api.searchStations(query)
      setSuggestions(results)
    }, 250)
    return () => clearTimeout(tid)
  }, [query])

  function selectStop(s: Station) {
    setSelected(s)
    setQuery(s.name)
    setSuggestions([])
    localStorage.setItem(LS_LAST, JSON.stringify(s))
  }

  function toggleFav(stop: Station) {
    const current = loadFavs()
    const exists = current.find(f => f.rbl === stop.rbl)
    const next = exists
      ? current.filter(f => f.rbl !== stop.rbl)
      : [...current, { name: stop.name, rbl: stop.rbl }]
    saveFavs(next)
    setFavs(next)
  }

  const isFav = selected ? favs.some(f => f.rbl === selected.rbl) : false

  return (
    <div className="max-w-2xl mx-auto space-y-4">
      <h1 className="text-2xl font-bold text-white">Departure Board</h1>

      {/* Search */}
      <div className="relative">
        <input
          className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
          placeholder="Search stop name (e.g. Karlsplatz, Schwedenplatz)…"
          value={query}
          onChange={e => setQuery(e.target.value)}
        />
        {suggestions.length > 0 && (
          <ul className="absolute z-20 w-full mt-1 bg-gray-800 border border-gray-700 rounded-lg overflow-hidden shadow-xl">
            {suggestions.map(s => (
              <li
                key={s.rbl ?? s.name}
                className="px-4 py-2.5 hover:bg-gray-700 cursor-pointer text-sm flex items-center gap-2"
                onClick={() => selectStop(s)}
              >
                <span className="text-gray-400 text-xs">RBL {s.rbl}</span>
                <span className="text-white">{s.name}</span>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Favourites */}
      {favs.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {favs.map(f => (
            <button
              key={f.rbl}
              onClick={() => selectStop({ name: f.name, rbl: f.rbl } as Station)}
              className="px-3 py-1 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-full text-sm text-gray-300 transition-colors"
            >
              ★ {f.name}
            </button>
          ))}
        </div>
      )}

      {/* Selected stop header */}
      {selected && (
        <div className="flex items-center justify-between">
          <div>
            <span className="text-lg font-semibold text-white">{selected.name}</span>
            {selected.rbl && (
              <span className="ml-2 text-xs text-gray-500 font-mono">RBL {selected.rbl}</span>
            )}
          </div>
          <div className="flex items-center gap-2">
            {lastUpdated && (
              <span className="text-xs text-gray-500">
                Updated {lastUpdated.toLocaleTimeString()}
              </span>
            )}
            <button
              onClick={() => toggleFav(selected)}
              className={`text-lg transition-colors ${isFav ? 'text-yellow-400' : 'text-gray-600 hover:text-yellow-400'}`}
              title={isFav ? 'Remove from favourites' : 'Add to favourites'}
            >
              {isFav ? '★' : '☆'}
            </button>
            <button
              onClick={() => fetchDeps(selected)}
              className="text-xs px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded text-gray-300 transition-colors"
            >
              ↻ Refresh
            </button>
          </div>
        </div>
      )}

      {/* Departure list */}
      {loading && (
        <div className="text-center py-8 text-gray-500 text-sm animate-pulse">Loading…</div>
      )}
      {error && (
        <div className="bg-red-900/30 border border-red-800 rounded-lg px-4 py-3 text-red-300 text-sm">
          {error}
        </div>
      )}
      {!loading && selected && deps.length === 0 && !error && (
        <div className="text-center py-8 text-gray-500 text-sm">No upcoming departures.</div>
      )}
      {!loading && deps.length > 0 && (
        <ul className="space-y-2">
          {deps.slice(0, 20).map((d, i) => {
            const { text, cls } = countdown(d.countdown ?? 99)
            return (
              <li
                key={d.id ?? i}
                className="bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 flex items-center gap-3"
              >
                {/* Line badge */}
                <span
                  className={`${lineColor(d.type, d.line)} text-white font-bold text-sm rounded px-2 py-0.5 min-w-[3rem] text-center`}
                >
                  {d.line}
                </span>

                {/* Destination */}
                <div className="flex-1 min-w-0">
                  <div className="text-white text-sm truncate">{d.towards || d.next_station}</div>
                  {d.delay > 0 && (
                    <div className="text-xs text-orange-400">+{d.delay} min delay</div>
                  )}
                </div>

                {/* Countdown */}
                <span className={`text-sm tabular-nums ${cls}`}>{text}</span>
              </li>
            )
          })}
        </ul>
      )}

      {!selected && !loading && (
        <div className="text-center py-16 text-gray-600">
          <div className="text-4xl mb-3">🚉</div>
          <div className="text-sm">Search for a stop above to see live departures</div>
        </div>
      )}
    </div>
  )
}
