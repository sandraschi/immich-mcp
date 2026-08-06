import { create } from "zustand";
import { persist } from "zustand/middleware";

interface LlmState {
  selectedProvider: string;
  selectedModel: string;
  setProvider: (provider: string) => void;
  setModel: (model: string) => void;
  reset: () => void;
}

export const useLlmStore = create<LlmState>()(
  persist(
    (set) => ({
      selectedProvider: "ollama",
      selectedModel: "",
      setProvider: (provider) => set({ selectedProvider: provider }),
      setModel: (model) => set({ selectedModel: model }),
      reset: () => set({ selectedProvider: "ollama", selectedModel: "" }),
    }),
    {
      name: "llm-provider-model",
      partialize: (state) => ({
        selectedProvider: state.selectedProvider,
        selectedModel: state.selectedModel,
      }),
    },
  ),
);
