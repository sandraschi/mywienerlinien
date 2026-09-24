// Centralised endpoints/ports. Env-overridable for other machines -
// no hardcoded localhost ports scattered through pages (fleet P1 rule).
export const API_BASE =
	import.meta.env.VITE_API_TARGET ?? "http://127.0.0.1:11170";

export const DOCS_URL =
	import.meta.env.VITE_DOCS_URL ??
	"https://github.com/sandraschi/mywienerlinien";
