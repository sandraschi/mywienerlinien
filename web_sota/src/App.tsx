import { BrowserRouter, NavLink, Route, Routes } from "react-router-dom";
import FloatingChat from "./components/FloatingChat";
import { useBackendStatus } from "./hooks/useBackendStatus";
import { MAP_URL } from "./lib/config";
import ChatPage from "./pages/ChatPage";
import Dashboard from "./pages/Dashboard";
import DeparturePage from "./pages/DeparturePage";
import DisruptionsPage from "./pages/DisruptionsPage";
import HelpPage from "./pages/HelpPage";
import InboxPage from "./pages/InboxPage";
import LinesPage from "./pages/LinesPage";
import Logging from "./pages/Logging";
import AppsPage from "./pages/AppsPage";
import SettingsPage from "./pages/SettingsPage";
import SkillsPage from "./pages/SkillsPage";
import ToolsPage from "./pages/ToolsPage";

const NAV = [
	{ to: "/", label: "Dashboard" },
	{ to: "/departures", label: "Departures" },
	{ to: "/disruptions", label: "Disruptions" },
	{ to: "/lines", label: "Lines" },
	{ to: "/inbox", label: "Inbox" },
	{ to: "/chat", label: "Chat" },
	{ to: "/tools", label: "Tools" },
	{ to: "/skills", label: "Skills" },
	{ to: "/apps", label: "Apps" },
	{ to: "/logs", label: "Logs" },
	{ to: "/settings", label: "Settings" },
	{ to: "/help", label: "Help" },
];

function Shell() {
	const backend = useBackendStatus();
	const dot =
		backend === "up"
			? "bg-emerald-500"
			: backend === "down"
				? "bg-red-500"
				: "bg-amber-400 animate-pulse";

	return (
		<div
			className="min-h-screen flex flex-col bg-slate-950"
			data-testid="app-shell"
		>
			{/* Header */}
			<header className="bg-gray-900 border-b border-gray-800 px-6 py-3 flex items-center gap-6 flex-wrap">
				<div className="flex items-center gap-2">
					<span className="text-xl font-bold text-white">Wiener Linien</span>
					<span className="text-sm text-slate-300 font-mono">dashboard</span>
					<span
						className="inline-flex items-center gap-1.5 text-sm text-slate-300"
						data-testid="backend-dot"
					>
						<span className={`h-2 w-2 rounded-full ${dot}`} />
						{backend}
					</span>
				</div>
				<nav className="flex gap-1 ml-4 flex-wrap" data-testid="main-nav">
					{NAV.map(({ to, label }) => (
						<NavLink
							key={to}
							to={to}
							end={to === "/"}
							className={({ isActive }) =>
								`px-3 py-1.5 rounded text-sm font-medium transition-colors ` +
								(isActive
									? "bg-blue-600 text-white"
									: "text-slate-300 hover:text-white hover:bg-gray-800")
							}
						>
							{label}
						</NavLink>
					))}
				</nav>
				<a
					href={MAP_URL}
					target="_blank"
					rel="noopener noreferrer"
					className="ml-auto text-sm text-slate-300 hover:text-blue-400 transition-colors"
				>
					Open Live Map
				</a>
			</header>

			{/* Content */}
			<main className="flex-1 p-6">
				<Routes>
					<Route path="/" element={<Dashboard />} />
					<Route path="/departures" element={<DeparturePage />} />
					<Route path="/disruptions" element={<DisruptionsPage />} />
					<Route path="/lines" element={<LinesPage />} />
					<Route path="/inbox" element={<InboxPage />} />
					<Route path="/chat" element={<ChatPage />} />
					<Route path="/tools" element={<ToolsPage />} />
					<Route path="/skills" element={<SkillsPage />} />
					<Route path="/apps" element={<AppsPage />} />
					<Route path="/logs" element={<Logging />} />
					<Route path="/settings" element={<SettingsPage />} />
					<Route path="/help" element={<HelpPage />} />
				</Routes>
			</main>

			<footer className="text-center text-sm text-slate-400 py-2">
				Data: Wiener Linien OGD realtime + GTFS reference snapshot
			</footer>
			<FloatingChat />
		</div>
	);
}

export default function App() {
	return (
		<BrowserRouter>
			<Shell />
		</BrowserRouter>
	);
}
