import { create } from "zustand";

export interface LlmProvider {
	id: string;
	label: string;
	base_url: string;
	models: string[];
	needs_key: boolean;
}

interface LlmState {
	providers: LlmProvider[];
	providerId: string;
	model: string;
	detected: boolean;
	probing: boolean;
	setProviders: (p: LlmProvider[]) => void;
	setProviderId: (id: string) => void;
	setModel: (m: string) => void;
	setDetected: (d: boolean) => void;
	setProbing: (p: boolean) => void;
}

const savedProvider =
	typeof localStorage !== "undefined"
		? localStorage.getItem("llm_provider") || "ollama"
		: "ollama";
const savedModel =
	typeof localStorage !== "undefined"
		? localStorage.getItem("llm_model") || ""
		: "";

export const useLlmStore = create<LlmState>((set) => ({
	providers: [],
	providerId: savedProvider,
	model: savedModel,
	detected: false,
	probing: true,
	setProviders: (providers) => set({ providers }),
	setProviderId: (providerId) => {
		try {
			localStorage.setItem("llm_provider", providerId);
		} catch {
			/* storage unavailable */
		}
		set({ providerId });
	},
	setModel: (model) => {
		try {
			localStorage.setItem("llm_model", model);
		} catch {
			/* storage unavailable */
		}
		set({ model });
	},
	setDetected: (detected) => set({ detected }),
	setProbing: (probing) => set({ probing }),
}));
