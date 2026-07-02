/**
 * AEGIS-OS Workflow Store — Zustand
 * Manages real-time workflow state and SSE event feed.
 */
import { create } from "zustand";
import type { WorkflowState, WorkflowEvent, Pod } from "@/types/lemma";
import { lemmaPods, lemmaWorkflows } from "@/lib/lemma/index";

interface WorkflowStoreState {
  pods: Pod[];
  activePodId: string | null;
  workflowStates: Record<string, WorkflowState>;
  events: WorkflowEvent[];
  isLoadingPods: boolean;
  error: string | null;

  loadPods: () => Promise<void>;
  setActivePod: (podId: string) => void;
  loadWorkflowStatus: (podId: string) => Promise<void>;
  addEvent: (event: WorkflowEvent) => void;
  loadEventSnapshot: (podId?: string) => Promise<void>;
}

export const useWorkflowStore = create<WorkflowStoreState>((set, get) => ({
  pods: [],
  activePodId: null,
  workflowStates: {},
  events: [],
  isLoadingPods: false,
  error: null,

  loadPods: async () => {
    set({ isLoadingPods: true, error: null });
    try {
      const resp = await lemmaPods.list();
      set({ pods: resp.pods, isLoadingPods: false });
    } catch (e) {
      set({ isLoadingPods: false, error: (e as Error).message });
    }
  },

  setActivePod: (podId) => set({ activePodId: podId }),

  loadWorkflowStatus: async (podId) => {
    try {
      const state = await lemmaWorkflows.status(podId);
      set((prev) => ({
        workflowStates: { ...prev.workflowStates, [podId]: state },
      }));
    } catch {}
  },

  addEvent: (event) => set((prev) => ({
    events: [event, ...prev.events].slice(0, 100), // Keep last 100
  })),

  loadEventSnapshot: async (podId) => {
    try {
      const resp = await lemmaWorkflows.feedSnapshot(podId);
      set({ events: [...resp.events].reverse() });
    } catch {}
  },
}));
