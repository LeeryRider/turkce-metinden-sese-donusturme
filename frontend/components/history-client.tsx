"use client";

import { Download, FileAudio, Heart, LoaderCircle, RefreshCw, Search, Sparkles, Trash2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { api, audioUrl } from "@/lib/api";
import type { GenerationEnvelope } from "@/lib/types";

export function HistoryClient() {
  const router = useRouter();
  const [items, setItems] = useState<GenerationEnvelope[]>([]);
  const [search, setSearch] = useState("");
  const [favoriteOnly, setFavoriteOnly] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await api.listGenerations(search, favoriteOnly);
      setItems(data.generations);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Geçmiş yüklenemedi.");
    } finally {
      setLoading(false);
    }
  }, [search, favoriteOnly]);

  useEffect(() => { const timer = window.setTimeout(load, 250); return () => window.clearTimeout(timer); }, [load]);

  async function toggleFavorite(item: GenerationEnvelope) {
    const updated = await api.favorite(item.generation.id, !item.generation.is_favorite);
    setItems((current) => current.map((entry) => entry.generation.id === updated.generation.id ? updated : entry));
  }

  function reuse(item: GenerationEnvelope) {
    window.localStorage.setItem("seda-studio-draft", JSON.stringify({
      text: item.generation.text,
      title: `${item.generation.title} — kopya`,
      preset: item.generation.preset,
    }));
    router.push("/studio");
  }

  async function remove(item: GenerationEnvelope) {
    if (!window.confirm(`“${item.generation.title}” kaydı ve ses dosyası silinsin mi?`)) return;
    try {
      await api.deleteGeneration(item.generation.id);
      setItems((current) => current.filter((entry) => entry.generation.id !== item.generation.id));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Kayıt silinemedi.");
    }
  }

  return (
    <div className="page">
      <header className="page-header"><div><span className="eyebrow">SES ARŞİVİ</span><h1>Konuşma geçmişi</h1><p>Ürettiğiniz sesleri bulun, dinleyin ve yeniden kullanın.</p></div></header>
      <section className="panel history-toolbar">
        <label className="search-field"><Search size={18} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Başlık veya metinde ara…" /></label>
        <button className={favoriteOnly ? "filter-button active" : "filter-button"} onClick={() => setFavoriteOnly((value) => !value)}><Heart size={17} fill={favoriteOnly ? "currentColor" : "none"} /> Favoriler</button>
        <button className="icon-button" onClick={load} aria-label="Yenile"><RefreshCw size={18} /></button>
      </section>
      {error && <div className="error-banner page-error">{error}</div>}
      {loading ? <div className="loading-state"><LoaderCircle className="spin" /> Kayıtlar yükleniyor…</div> : (
        <div className="history-list">
          {items.length === 0 && <EmptyState />}
          {items.map((item) => {
            const generation = item.generation;
            const source = audioUrl(item);
            return (
              <article className="panel history-card" key={generation.id}>
                <div className={`history-art ${generation.preset}`}><FileAudio size={27} /><span>{generation.duration_seconds ? `${generation.duration_seconds.toFixed(1)} sn` : "—"}</span></div>
                <div className="history-content">
                  <div className="history-title-row"><div><span className={`status-label ${generation.status}`}>{statusLabel(generation.status)}</span><h2>{generation.title}</h2></div><button className="heart-button" onClick={() => toggleFavorite(item)} aria-label="Favori"><Heart size={19} fill={generation.is_favorite ? "currentColor" : "none"} /></button></div>
                  <p>{generation.text}</p>
                  {source && <audio controls src={source} preload="none" />}
                  <div className="history-meta"><span>{generation.word_count} kelime</span><span>{presetLabel(generation.preset)}</span><span>{formatFullDate(generation.created_at)}</span>{generation.generation_seconds && <span>{generation.generation_seconds.toFixed(1)} sn üretim</span>}</div>
                </div>
                <div className="history-actions">
                  <button onClick={() => reuse(item)}><Sparkles size={16} /> Yeniden kullan</button>
                  {source && <a href={source} download><Download size={16} /> İndir</a>}
                  <button className="danger-action" onClick={() => remove(item)} disabled={generation.status === "processing" || generation.status === "queued"}><Trash2 size={16} /> Sil</button>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </div>
  );
}

function EmptyState() { return <div className="panel empty-state"><div><FileAudio size={30} /></div><h2>Henüz konuşma yok</h2><p>Stüdyoda oluşturduğunuz sesler burada saklanacak.</p></div>; }
function statusLabel(status: string) { return ({ queued: "Sırada", processing: "Üretiliyor", completed: "Hazır", failed: "Hatalı" } as Record<string, string>)[status] ?? status; }
function presetLabel(name: string) { return ({ normal: "Doğal", news: "Haber", announcement: "Duyuru", story: "Hikâye", education: "Eğitim", accessibility: "Erişilebilir" } as Record<string, string>)[name] ?? name; }
function formatFullDate(value: string) { return new Intl.DateTimeFormat("tr-TR", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value)); }
