import { useEffect, useRef, useState } from "react";
import { API_BASE } from "../lib/api";
import { useLlmStore } from "../store/llm";

interface Message {
	role: "user" | "assistant";
	content: string;
}

const PERSONALITIES = [
	{
		id: "concise",
		label: "Concise",
		prompt: "You are a concise Vienna transit assistant. Answer briefly.",
	},
	{
		id: "tourist",
		label: "Tourist guide",
		prompt:
			"You are a friendly Vienna tourist guide. Explain transit options for visitors, mention walking and sights.",
	},
	{
		id: "commuter",
		label: "Commuter",
		prompt:
			"You are a commuter assistant for Vienna. Focus on fastest routes, delays, and alternatives.",
	},
	{
		id: "expert",
		label: "Expert",
		prompt:
			"You are a Vienna transit expert. Give precise answers with line numbers, RBLs, and transfer details.",
	},
	{ id: "custom", label: "Custom", prompt: "" },
];

const EXAMPLES = [
	"Which lines serve Karlsplatz?",
	"How do I get from Stephansplatz to Praterstern?",
	"Are there disruptions on the U6?",
	"What is an RBL?",
	"Which night lines run from Schwedenplatz?",
	"Is the elevator at Kliebergasse working?",
];

const LS_KEY = "wl_chat";
const LS_PERSONALITY = "wl_chat_personality";
const LS_CUSTOM = "wl_chat_custom";
const CAP = 100;

export default function ChatPage() {
	const [chat, setChat] = useState<Message[]>([]);
	const [input, setInput] = useState("");
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState<string | null>(null);
	const [skill, setSkill] = useState("");
	const [personality, setPersonality] = useState(
		() => localStorage.getItem(LS_PERSONALITY) || "concise",
	);
	const [customPrompt, setCustomPrompt] = useState(
		() => localStorage.getItem(LS_CUSTOM) || "",
	);
	const { providers, providerId, model, detected } = useLlmStore();
	const bottomRef = useRef<HTMLDivElement>(null);

	useEffect(() => {
		try {
			const saved = localStorage.getItem(LS_KEY);
			if (saved) {
				const parsed = JSON.parse(saved) as Message[];
				setChat(parsed.slice(-CAP));
			}
		} catch {
			/* corrupted history - start fresh */
		}
	}, []);

	useEffect(() => {
		if (chat.length > 0) {
			localStorage.setItem(LS_KEY, JSON.stringify(chat.slice(-CAP)));
		} else {
			localStorage.removeItem(LS_KEY);
		}
		bottomRef.current?.scrollIntoView({ behavior: "smooth" });
	}, [chat]);

	useEffect(() => {
		fetch(`${API_BASE}/api/skills`)
			.then((r) => r.json())
			.then((d) => {
				const names = (d.skills ?? [])
					.map((s: { name: string }) => s.name)
					.join(", ");
				if (names) setSkill(`Available skills: ${names}.`);
			})
			.catch(() => {});
	}, []);

	function pickPersonality(id: string) {
		setPersonality(id);
		localStorage.setItem(LS_PERSONALITY, id);
	}

	async function send(text?: string) {
		const content = (text ?? input).trim();
		if (!content || loading) return;
		setError(null);
		const persona =
			PERSONALITIES.find((p) => p.id === personality)?.prompt || customPrompt;
		const system = [skill, persona].filter(Boolean).join("\n");
		const next: Message[] = [...chat, { role: "user" as const, content }].slice(
			-CAP,
		);
		setChat(next);
		setInput("");
		setLoading(true);
		try {
			// Prefer the streaming endpoint, fall back to the plain proxy.
			let reply = "";
			try {
				const r = await fetch(`${API_BASE}/api/chat/stream`, {
					method: "POST",
					headers: { "Content-Type": "application/json" },
					body: JSON.stringify({
						provider: providerId,
						model,
						prompt: `${system}\n\n${content}`,
					}),
				});
				if (r.ok && r.body) {
					const reader = r.body.getReader();
					const decoder = new TextDecoder();
					let buf = "";
					for (;;) {
						const { done, value } = await reader.read();
						if (done) break;
						buf += decoder.decode(value, { stream: true });
						for (const chunk of buf.split("\n\n")) {
							const line = chunk.trim();
							if (!line.startsWith("data:")) continue;
							const payload = line.slice(5).trim();
							if (payload === "[DONE]") continue;
							try {
								const evt = JSON.parse(payload);
								if (evt.error) throw new Error(evt.error);
								const delta =
									evt.choices?.[0]?.delta?.content ?? evt.response ?? "";
								if (delta) {
									reply += delta;
									setChat(
										[
											...next,
											{ role: "assistant" as const, content: reply },
										].slice(-CAP),
									);
								}
							} catch (e) {
								if (
									e instanceof Error &&
									!e.message.startsWith("Unexpected token")
								)
									throw e;
							}
						}
						buf = buf.split("\n\n").pop() ?? "";
					}
				}
			} catch {
				/* stream failed - plain proxy below */
			}
			if (!reply) {
				const r = await fetch(`${API_BASE}/api/llm/chat`, {
					method: "POST",
					headers: { "Content-Type": "application/json" },
					body: JSON.stringify({
						provider: providerId,
						model,
						prompt: `${system}\n\n${content}`,
					}),
				});
				const d = await r.json();
				reply = d.response ?? "(empty response)";
			}
			setChat(
				[...next, { role: "assistant" as const, content: reply }].slice(-CAP),
			);
		} catch (e) {
			setError(String(e));
		} finally {
			setLoading(false);
		}
	}

	function exportChat() {
		const blob = new Blob(
			[chat.map((m) => `${m.role.toUpperCase()}: ${m.content}`).join("\n\n")],
			{ type: "text/plain" },
		);
		const url = URL.createObjectURL(blob);
		const a = document.createElement("a");
		a.href = url;
		a.download = "chat-export.txt";
		a.click();
		URL.revokeObjectURL(url);
	}

	function clearChat() {
		setChat([]);
		localStorage.removeItem(LS_KEY);
	}

	return (
		<div className="mx-auto max-w-3xl space-y-4" data-testid="chat-page">
			<h1 className="text-2xl font-bold text-white">Chat</h1>

			<div
				className="flex flex-wrap items-center gap-2 rounded-xl border border-white/10 bg-slate-900/60 p-3"
				data-testid="chat-controls"
			>
				<select
					data-testid="personality-select"
					value={personality}
					onChange={(e) => pickPersonality(e.target.value)}
					className="rounded border border-slate-700 bg-slate-800 px-2 py-1.5 text-sm text-slate-100"
				>
					{PERSONALITIES.map((p) => (
						<option key={p.id} value={p.id}>
							{p.label}
						</option>
					))}
				</select>
				{personality === "custom" && (
					<input
						value={customPrompt}
						onChange={(e) => {
							setCustomPrompt(e.target.value);
							localStorage.setItem(LS_CUSTOM, e.target.value);
						}}
						placeholder="Custom system prompt…"
						className="min-w-48 flex-1 rounded border border-slate-700 bg-slate-800 px-2 py-1.5 text-sm text-slate-100 placeholder:text-slate-400"
					/>
				)}
				<span className="ml-auto flex items-center gap-2 text-sm text-slate-300">
					<span
						className={`h-2 w-2 rounded-full ${detected ? "bg-emerald-500" : "bg-amber-400"}`}
					/>
					{providerId}
					{model ? ` / ${model}` : ""}
				</span>
				<button
					type="button"
					data-testid="chat-export"
					onClick={exportChat}
					disabled={chat.length === 0}
					className="rounded border border-slate-700 px-2 py-1 text-sm text-slate-300 hover:bg-slate-800 disabled:opacity-40"
				>
					Export
				</button>
				<button
					type="button"
					data-testid="chat-clear"
					onClick={clearChat}
					disabled={chat.length === 0}
					className="rounded border border-slate-700 px-2 py-1 text-sm text-slate-300 hover:bg-slate-800 disabled:opacity-40"
				>
					Clear
				</button>
			</div>

			{chat.length === 0 && (
				<div className="rounded-xl border border-white/10 bg-slate-900/60 p-6 text-center">
					<p className="text-sm text-slate-300">
						Ask about Vienna transit. Answers come from your local LLM via the
						backend proxy.
					</p>
					<div
						className="mt-3 flex flex-wrap justify-center gap-2"
						data-testid="example-prompts"
					>
						{EXAMPLES.map((ex) => (
							<button
								type="button"
								key={ex}
								onClick={() => send(ex)}
								className="rounded-full border border-slate-700 bg-slate-800 px-3 py-1 text-sm text-slate-200 hover:bg-slate-700"
							>
								{ex}
							</button>
						))}
					</div>
				</div>
			)}

			<div className="space-y-3" data-testid="chat-messages">
				{chat.map((m, i) => (
					<div
						key={i}
						className={`rounded-xl border px-4 py-3 text-sm whitespace-pre-line ${
							m.role === "user"
								? "border-blue-800 bg-blue-950/40 text-blue-100"
								: "border-white/10 bg-slate-900/60 text-slate-100"
						}`}
					>
						{m.content}
					</div>
				))}
				{loading && (
					<div className="animate-pulse text-sm text-slate-400">Thinking…</div>
				)}
				<div ref={bottomRef} />
			</div>

			{error && (
				<div className="rounded-lg border border-red-800 bg-red-900/30 px-4 py-3 text-sm text-red-300">
					{error}
				</div>
			)}

			<div className="flex gap-2">
				<input
					data-testid="chat-input"
					value={input}
					onChange={(e) => setInput(e.target.value)}
					onKeyDown={(e) => {
						if (e.key === "Enter") send();
					}}
					placeholder="Ask about Vienna transit…"
					className="flex-1 rounded-lg border border-slate-700 bg-slate-800 px-4 py-2.5 text-sm text-white placeholder:text-slate-400 focus:border-blue-500 focus:outline-none"
				/>
				<button
					type="button"
					data-testid="chat-send"
					onClick={() => send()}
					disabled={loading || !input.trim()}
					className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500 disabled:opacity-40"
				>
					Send
				</button>
			</div>
		</div>
	);
}
