export type GenerationStatus = "queued" | "processing" | "completed" | "failed";

export type PresetName =
  | "normal"
  | "news"
  | "announcement"
  | "story"
  | "education"
  | "accessibility";

export interface Preset {
  label: string;
  description: string;
  exaggeration: number;
  cfg_weight: number;
  temperature: number;
}

export interface Generation {
  id: string;
  title: string;
  text: string;
  preset: PresetName;
  exaggeration: number;
  cfg_weight: number;
  temperature: number;
  word_count: number;
  status: GenerationStatus;
  stage: string;
  output_filename: string | null;
  duration_seconds: number | null;
  generation_seconds: number | null;
  is_favorite: boolean;
  error: string | null;
  created_at: string;
  updated_at: string;
}

export interface GenerationEnvelope {
  generation: Generation;
  audio_url: string | null;
}

export interface SpeechTemplate {
  id: string;
  title: string;
  category: string;
  preset: PresetName;
  text: string;
}

export interface SystemInfo {
  python_version: string;
  torch_version: string;
  cuda_available: boolean;
  device: string;
  device_name: string;
  model_loaded: boolean;
  gpu_memory_allocated_mb: number;
  gpu_memory_reserved_mb: number;
  queue_size: number;
  statistics: {
    total: number;
    total_words: number;
    total_audio_seconds: number;
    average_generation_seconds: number;
  };
}
