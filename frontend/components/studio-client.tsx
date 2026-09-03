"use client";

import {
  AudioLines,
  BookOpen,
  Check,
  ChevronDown,
  Download,
  Gauge,
  GraduationCap,
  LoaderCircle,
  Megaphone,
  Newspaper,
  Radio,
  RefreshCw,
  Sparkles,
  Volume2,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api, audioUrl } from "@/lib/api";
import type { GenerationEnvelope, Preset, PresetName } from "@/lib/types";

const presetIcons = {
  normal: Volume2,
  news: Newspaper,
  announcement: Megaphone,
  story: BookOpen,
  education: GraduationCap,
  accessibility: Radio,
};

const statusSteps = ["Metin", "Model", "Üretim", "Dosya"];
const presetNames: PresetName[] = [
  "normal",
  "news",
  "announcement",
  "story",
  "education",
  "accessibility",
];

function currentStep(stage: string, completed: boolean): number {
  if (completed) return 4;
  if (stage.includes("WAV")) return 3;
  if (stage.includes("üretil") || stage.includes("parça")) return 2;
  if (stage.includes("model") || stage.includes("Chatterbox")) return 1;
  return 0;
}

export function StudioClient() {
  const draftPreset = useRef<PresetName>("normal");
  const [text, setText] = useState("");
  const [title, setTitle] = useState("");
  const [presetName, setPresetName] = useState<PresetName>("normal");
  const [presets, setPresets] = useState<Record<PresetName, Preset> | null>(null);
  const [exaggeration, setExaggeration] = useState(0.5);
  const [cfgWeight, setCfgWeight] = useState(0.5);
  const [temperature, setTemperature] = useState(0.8);
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [activeJob, setActiveJob] = useState<GenerationEnvelope | null>(null);
  const [recent, setRecent] = useState<GenerationEnvelope[]>([]);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const wordCount = useMemo(() => text.trim() ? text.trim().split(/\s+/).length : 0, [text]);
  const isRunning = activeJob?.generation.status === "queued" || activeJob?.generation.status === "processing";

  const loadRecent = useCallback(() => {
    api.listGenerations().then((data) => setRecent(data.generations.slice(0, 3))).catch(() => undefined);
  }, []);

  useEffect(() => {
    const draft = window.localStorage.getItem("seda-studio-draft");
    if (draft) {
      try {
        const parsed = JSON.parse(draft) as { text?: string; title?: string; preset?: PresetName };
        if (parsed.text) setText(parsed.text);
        if (parsed.title) setTitle(parsed.title);
        if (parsed.preset && presetNames.includes(parsed.preset)) {
          draftPreset.current = parsed.preset;
          setPresetName(parsed.preset);
        }
      } finally {
        window.localStorage.removeItem("seda-studio-draft");
      }
    }

    api.presets()
      .then((data) => {
        setPresets(data.presets);
        const selected = data.presets[draftPreset.current];
        setExaggeration(selected.exaggeration);
        setCfgWeight(selected.cfg_weight);
        setTemperature(selected.temperature);
      })
      .catch((reason: Error) => setError(reason.message));
    loadRecent();
  }, [loadRecent]);

  useEffect(() => {
    if (!isRunning || !activeJob) return;
    const timer = window.setInterval(async () => {
      try {
        const updated = await api.getGeneration(activeJob.generation.id);
        setActiveJob(updated);
        if (updated.generation.status === "completed" || updated.generation.status === "failed") {
          window.clearInterval(timer);
          loadRecent();
        }
      } catch (reason) {
        setError(reason instanceof Error ? reason.message : "İş durumu alınamadı.");
      }
    }, 900);
    return () => window.clearInterval(timer);
  }, [activeJob, isRunning, loadRecent]);

  function selectPreset(name: PresetName) {
    setPresetName(name);
    const preset = presets?.[name];
    if (preset) {
      setExaggeration(preset.exaggeration);
      setCfgWeight(preset.cfg_weight);
      setTemperature(preset.temperature);
    }
  }

  async function generate() {
    setError("");
    if (!text.trim()) {
      setError("Ses oluşturmak için bir metin girin.");
      return;
    }
    if (wordCount > 1000) {
      setError("Metin en fazla 1000 kelime olabilir.");
      return;
    }
    setSubmitting(true);
    try {
      const job = await api.createGeneration({
        text,
        title: title.trim() || undefined,
        preset: presetName,
        exaggeration,
        cfg_weight: cfgWeight,
        temperature,
      });
      setActiveJob(job);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Üretim başlatılamadı.");
    } finally {
      setSubmitting(false);
    }
  }

  const stage = activeJob?.generation.stage ?? "Metniniz üretime hazır.";
  const step = currentStep(stage, activeJob?.generation.status === "completed");
  const outputAudio = activeJob ? audioUrl(activeJob) : null;

  return (
    <div className="page studio-page">
      <header className="page-header hero-header">
        <div>
          <span className="eyebrow"><Sparkles size={14} /> YEREL YAPAY ZEKÂ STÜDYOSU</span>
          <h1>Sesi kelimelerden <em>tasarla.</em></h1>
          <p>Türkçe metninizi doğal ve etkileyici bir sese dönüştürün. Verileriniz bilgisayarınızdan ayrılmaz.</p>
        </div>
        <div className="header-badge"><span className="pulse" /> Chatterbox V3 · CUDA</div>
      </header>

      <div className="studio-grid">
        <section className="panel composer-panel">
          <div className="panel-heading">
            <div><span className="step-number">01</span><div><h2>Metninizi hazırlayın</h2><p>Başlık isteğe bağlıdır.</p></div></div>
            <span className={`word-pill ${wordCount > 1000 ? "danger" : ""}`}>{wordCount} / 1000 kelime</span>
          </div>
          <input
            className="title-input"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="Konuşma başlığı (isteğe bağlı)"
            maxLength={100}
          />
          <div className="textarea-wrap">
            <textarea
              value={text}
              onChange={(event) => setText(event.target.value)}
              placeholder="Seslendirmek istediğiniz Türkçe metni buraya yazın…"
              rows={10}
              aria-label="Seslendirilecek metin"
            />
            <div className="textarea-footer"><span>TR</span><span>{text.length} karakter</span></div>
          </div>

          <div className="section-label"><span className="step-number">02</span><div><h2>Konuşma biçimi</h2><p>İçeriğinize uygun anlatımı seçin.</p></div></div>
          <div className="preset-grid">
            {presets && Object.entries(presets).map(([key, preset]) => {
              const name = key as PresetName;
              const Icon = presetIcons[name];
              return (
                <button key={name} className={`preset-card ${presetName === name ? "selected" : ""}`} onClick={() => selectPreset(name)}>
                  <span className="preset-icon"><Icon size={20} /></span>
                  <span><strong>{preset.label}</strong><small>{preset.description}</small></span>
                  {presetName === name && <Check className="preset-check" size={16} />}
                </button>
              );
            })}
          </div>

          <button className="advanced-toggle" onClick={() => setAdvancedOpen((value) => !value)}>
            <span><Gauge size={17} /> Gelişmiş ses ayarları</span><ChevronDown className={advancedOpen ? "rotate" : ""} size={17} />
          </button>
          {advancedOpen && (
            <div className="advanced-settings">
              <Slider label="Duygu ve vurgu" value={exaggeration} setValue={setExaggeration} min={0} max={1} />
              <Slider label="Metne bağlılık" value={cfgWeight} setValue={setCfgWeight} min={0} max={1} />
              <Slider label="Yaratıcılık" value={temperature} setValue={setTemperature} min={0.5} max={1.2} />
            </div>
          )}
          {error && <div className="error-banner">{error}</div>}
          <button className="generate-button" disabled={submitting || isRunning} onClick={generate}>
            {submitting || isRunning ? <LoaderCircle className="spin" size={20} /> : <AudioLines size={21} />}
            {isRunning ? "Ses üretiliyor…" : "Sesi oluştur"}
          </button>
        </section>

        <aside className="studio-side">
          <section className="panel output-panel">
            <div className="panel-heading compact-heading"><div><span className="step-number">03</span><div><h2>Üretim</h2><p>Anlık işlem durumu</p></div></div></div>
            <div className={`sound-orb ${isRunning ? "working" : activeJob?.generation.status === "completed" ? "done" : ""}`}>
              <div className="orb-ring ring-one" /><div className="orb-ring ring-two" /><AudioLines size={38} />
            </div>
            <div className="stage-copy"><strong>{stage}</strong><span>{activeJob ? activeJob.generation.title : "Yeni bir ses oluşturduğunuzda işlem burada görünecek."}</span></div>
            <div className="progress-steps">
              {statusSteps.map((label, index) => (
                <div key={label} className={index <= step ? "progress-step complete" : "progress-step"}>
                  <span>{index < step || step === 4 ? <Check size={12} /> : index + 1}</span><small>{label}</small>
                </div>
              ))}
            </div>
            {outputAudio && (
              <div className="audio-result">
                <audio controls src={outputAudio} preload="metadata" />
                <a className="download-button" href={outputAudio} download><Download size={17} /> WAV indir</a>
                <div className="audio-meta">
                  <span>{activeJob?.generation.duration_seconds?.toFixed(1)} sn ses</span>
                  <span>{activeJob?.generation.generation_seconds?.toFixed(1)} sn üretim</span>
                </div>
              </div>
            )}
            {activeJob?.generation.status === "failed" && <div className="error-banner">{activeJob.generation.error}</div>}
          </section>

          <section className="panel recent-panel">
            <div className="mini-heading"><div><h3>Son konuşmalar</h3><p>En son oluşturulan kayıtlar</p></div><button className="icon-button" onClick={loadRecent} aria-label="Yenile"><RefreshCw size={16} /></button></div>
            <div className="recent-list">
              {recent.length === 0 && <p className="empty-copy">Henüz kayıt yok.</p>}
              {recent.map(({ generation }) => (
                <div className="recent-item" key={generation.id}>
                  <span className={`mini-status ${generation.status}`}><AudioLines size={15} /></span>
                  <div><strong>{generation.title}</strong><small>{generation.word_count} kelime · {formatDate(generation.created_at)}</small></div>
                </div>
              ))}
            </div>
          </section>
        </aside>
      </div>
    </div>
  );
}

function Slider({ label, value, setValue, min, max }: { label: string; value: number; setValue: (value: number) => void; min: number; max: number }) {
  return (
    <label className="slider-field"><span><strong>{label}</strong><output>{value.toFixed(2)}</output></span><input type="range" min={min} max={max} step="0.01" value={value} onChange={(event) => setValue(Number(event.target.value))} /></label>
  );
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("tr-TR", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" }).format(new Date(value));
}
