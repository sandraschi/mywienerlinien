// Typed client for the web_sota FastAPI backend (port 11170).
// Live OGD data: departures/disruptions. Reference snapshots: major stops, lines.
import { API_BASE } from "../lib/api";

export interface Departure {
	line: string;
	destination: string;
	countdown: number | null;
	time_planned?: string | null;
	time_real?: string | null;
	platform?: string | null;
	stop?: string | null;
}

export interface Alert {
	id: string;
	title: string;
	description: string;
	reason?: string;
	lines: string[];
	severity?: string;
	status?: string;
	start_time?: string;
	end_time?: string;
}

export interface Station {
	name: string;
	rbl: string;
	lat?: number;
	lon?: number;
}

export interface LineInfo {
	name: string;
	type: string;
	color: string;
	description?: string;
}

async function get<T>(path: string): Promise<T> {
	const r = await fetch(`${API_BASE}${path}`);
	if (!r.ok) {
		let detail = `${r.status} ${r.statusText}`;
		try {
			const body = await r.json();
			if (body?.error) detail += ` - ${body.error}`;
		} catch {
			/* non-JSON error body */
		}
		throw new Error(detail);
	}
	return r.json();
}

let majorCache: Station[] | null = null;

export const api = {
	/** Live departures for one stop (RBL) via the OGD monitor API. */
	departures: (rbl: string) =>
		get<{ rbl: string; departures: Departure[]; count: number }>(
			`/api/departures?rbl=${encodeURIComponent(rbl)}`,
		),

	/** Curated major-stop table (verified RBLs + GTFS coords). */
	majorStops: async (): Promise<Station[]> => {
		if (!majorCache) {
			const d = await get<{ stops: Station[] }>("/api/stops/major");
			majorCache = d.stops ?? [];
		}
		return majorCache;
	},

	/** Live service disruptions via OGD trafficInfoList. */
	trafficInfo: () =>
		get<{ alerts: Alert[]; count: number; timestamp: string }>(
			"/api/disruptions",
		),

	/** Line catalog (GTFS reference snapshot). */
	lines: async (): Promise<{ lines: LineInfo[] }> => {
		const d = await get<{
			lines: Array<{
				name: string;
				long_name: string;
				type: string;
				color: string;
			}>;
		}>("/api/lines");
		return {
			lines: (d.lines ?? []).map((l) => ({
				name: l.name,
				type: l.type,
				color: l.color,
				description: l.long_name,
			})),
		};
	},

	/** Name search over the major-stop table (client-side filter). */
	searchStations: async (query: string): Promise<Station[]> => {
		const stations = await api.majorStops();
		const q = query.toLowerCase();
		return stations
			.filter((s) => s.name.toLowerCase().includes(q))
			.slice(0, 12);
	},

	/** Backend liveness. */
	health: () => get<{ status: string }>("/api/health"),

	/** Backend status (uptime, version). */
	status: () =>
		get<{
			status: string;
			service: string;
			version: string;
			uptime_seconds: number;
		}>("/api/status"),
};
