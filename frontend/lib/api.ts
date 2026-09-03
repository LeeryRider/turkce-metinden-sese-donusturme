import type {
  GenerationEnvelope,
  Preset,
  PresetName,
  SpeechTemplate,
  SystemInfo,
} from "@/lib/types";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? `İstek başarısız oldu (${response.status}).`);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export function audioUrl(envelope: GenerationEnvelope): string | null {
  return envelope.audio_url ? `${API_URL}${envelope.audio_url}` : null;
}

export const api = {
  health: () => request<{ status: string; version: string }>("/api/health"),
  system: () => request<SystemInfo>("/api/system"),
  presets: () => request<{ presets: Record<PresetName, Preset> }>("/api/presets"),
  templates: () => request<{ templates: SpeechTemplate[] }>("/api/templates"),
  createGeneration: (payload: {
    text: string;
    title?: string;
    preset: PresetName;
    exaggeration: number;
    cfg_weight: number;
    temperature: number;
  }) =>
    request<GenerationEnvelope>("/api/generations", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getGeneration: (id: string) =>
    request<GenerationEnvelope>(`/api/generations/${id}`),
  listGenerations: (search = "", favorite = false) =>
    request<{ generations: GenerationEnvelope[] }>(
      `/api/generations?search=${encodeURIComponent(search)}&favorite=${favorite}`,
    ),
  favorite: (id: string, isFavorite: boolean) =>
    request<GenerationEnvelope>(`/api/generations/${id}/favorite`, {
      method: "PATCH",
      body: JSON.stringify({ is_favorite: isFavorite }),
    }),
  deleteGeneration: (id: string) =>
    request<void>(`/api/generations/${id}`, { method: "DELETE" }),
};
