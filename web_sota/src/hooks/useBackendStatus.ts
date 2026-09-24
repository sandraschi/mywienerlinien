import { useEffect, useState } from "react";
import { API_BASE } from "../lib/api";

const BACKOFF = [1000, 2000, 4000, 8000, 16000];

/** Backend liveness: Tauri `backend-status` event when hosted, HTTP poll fallback. */
export function useBackendStatus(): "up" | "down" | "probing" {
	const [status, setStatus] = useState<"up" | "down" | "probing">("probing");

	useEffect(() => {
		let cancelled = false;
		let timer: ReturnType<typeof setTimeout> | undefined;

		async function tryTauriListen() {
			try {
				const mod = await import("@tauri-apps/api/event");
				await mod.listen("backend-status", (e) => {
					if (!cancelled && e.payload === "ready") setStatus("up");
				});
			} catch {
				/* not in Tauri WebView - HTTP fallback below */
			}
		}

		async function poll(attempt: number) {
			if (cancelled) return;
			try {
				const r = await fetch(`${API_BASE}/api/health`);
				if (r.ok) {
					setStatus("up");
					return;
				}
			} catch {
				/* offline - back off */
			}
			if (attempt >= BACKOFF.length - 1) {
				setStatus("down");
				return;
			}
			timer = setTimeout(() => poll(attempt + 1), BACKOFF[attempt]);
		}

		void tryTauriListen();
		void poll(0);
		return () => {
			cancelled = true;
			if (timer) clearTimeout(timer);
		};
	}, []);

	return status;
}
