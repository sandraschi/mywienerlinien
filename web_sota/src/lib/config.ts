// Centralised endpoints/ports. Env-overridable for other machines -
// no hardcoded localhost ports scattered through pages (fleet P1 rule).
export const API_BASE =
	import.meta.env.VITE_API_TARGET ?? "http://127.0.0.1:11170";

// Native map app (frontend/app.py, Leaflet + sidebar). Fleet port 10722;
// runs WITHOUT Docker - only postgres stays containerized (port 5433).
export const MAP_URL = import.meta.env.VITE_MAP_URL ?? "http://localhost:10722";

export const DOCS_URL =
	import.meta.env.VITE_DOCS_URL ??
	"https://github.com/sandraschi/mywienerlinien";
