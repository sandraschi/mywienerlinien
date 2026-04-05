// All API calls proxy through Vite to the live map backend on port 3079
const BASE = '/api'

export interface Departure {
  id: string
  line: string
  type: string
  countdown: number
  towards: string
  next_station: string
  delay: number
  interpolated?: boolean
}

export interface Alert {
  id: string
  title: string
  description: string
  description_html?: string
  lines: string[]
  severity?: string
  status?: string
  start_time?: string
  end_time?: string
  priority?: string
}

export interface Station {
  name: string
  rbl: string
  lat: number
  lng: number
  type: string
}

export interface LineInfo {
  name: string
  type: string
  color: string
  description?: string
}

async function get<T>(path: string): Promise<T> {
  const r = await fetch(`${BASE}${path}`)
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`)
  return r.json()
}

export const api = {
  /** Departures at a stop by RBL */
  arrivals: (rbl: string) =>
    get<{ vehicles: Departure[] }>(`/arrivals?rbl=${encodeURIComponent(rbl)}`),

  /** All stops nearby lat/lon */
  nearbyStops: (lat: number, lng: number, limit = 5) =>
    get<{ stops: Station[] }>(`/stops/nearby?lat=${lat}&lon=${lng}&limit=${limit}`),

  /** Traffic disruptions */
  trafficInfo: () =>
    get<{ alerts: Alert[]; count: number; timestamp: string }>('/traffic-info'),

  /** All lines catalog */
  lines: () =>
    get<{ lines: LineInfo[] }>('/lines'),

  /** Stations list */
  stations: () =>
    get<{ stations: Station[] }>('/stations'),

  /** Nearby stops by free-text search (uses backend station list) */
  searchStations: async (query: string): Promise<Station[]> => {
    const { stations } = await get<{ stations: Station[] }>('/stations')
    const q = query.toLowerCase()
    return stations
      .filter(s => s.name.toLowerCase().includes(q))
      .slice(0, 12)
  },

  /** Health */
  health: () =>
    get<{ status: string; database?: string }>('/health'),
}
