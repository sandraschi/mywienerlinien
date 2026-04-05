import { BrowserRouter, NavLink, Route, Routes } from 'react-router-dom'
import DeparturePage from './pages/DeparturePage'
import DisruptionsPage from './pages/DisruptionsPage'
import LinesPage from './pages/LinesPage'

const NAV = [
  { to: '/',            label: '🚉 Departures' },
  { to: '/disruptions', label: '⚠️ Disruptions' },
  { to: '/lines',       label: '🗺️ Lines' },
]

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen flex flex-col">
        {/* Header */}
        <header className="bg-gray-900 border-b border-gray-800 px-6 py-3 flex items-center gap-6">
          <div>
            <span className="text-xl font-bold text-white">🚊 Wiener Linien</span>
            <span className="ml-2 text-xs text-gray-500 font-mono">dashboard</span>
          </div>
          <nav className="flex gap-1 ml-4">
            {NAV.map(({ to, label }) => (
              <NavLink
                key={to}
                to={to}
                end={to === '/'}
                className={({ isActive }) =>
                  `px-3 py-1.5 rounded text-sm font-medium transition-colors ` +
                  (isActive
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-400 hover:text-white hover:bg-gray-800')
                }
              >
                {label}
              </NavLink>
            ))}
          </nav>
          <a
            href="http://localhost:3079"
            target="_blank"
            rel="noopener noreferrer"
            className="ml-auto text-xs text-gray-500 hover:text-blue-400 transition-colors"
          >
            Open Live Map ↗
          </a>
        </header>

        {/* Content */}
        <main className="flex-1 p-6">
          <Routes>
            <Route path="/"            element={<DeparturePage />} />
            <Route path="/disruptions" element={<DisruptionsPage />} />
            <Route path="/lines"       element={<LinesPage />} />
          </Routes>
        </main>

        <footer className="text-center text-xs text-gray-700 py-2">
          Data: Wiener Linien OGD Realtime V1.4 • Dashboard port 10896
        </footer>
      </div>
    </BrowserRouter>
  )
}
