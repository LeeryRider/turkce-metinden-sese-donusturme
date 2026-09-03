"use client";

import { Activity, CheckCircle2, Cpu, Database, Gauge, LoaderCircle, MemoryStick, RefreshCw, Server, Timer, Volume2, XCircle } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { SystemInfo } from "@/lib/types";

export function SystemClient() {
  const [info, setInfo] = useState<SystemInfo | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try { setInfo(await api.system()); setError(""); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Sistem bilgisi alınamadı."); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => {
    const initialTimer = window.setTimeout(load, 0);
    const refreshTimer = window.setInterval(load, 5000);
    return () => {
      window.clearTimeout(initialTimer);
      window.clearInterval(refreshTimer);
    };
  }, [load]);

  return (
    <div className="page">
      <header className="page-header header-with-action"><div><span className="eyebrow">ÇALIŞMA ORTAMI</span><h1>Sistem durumu</h1><p>Model, GPU ve üretim istatistiklerini canlı izleyin.</p></div><button className="secondary-button" onClick={load}><RefreshCw size={17} /> Yenile</button></header>
      {error && <div className="error-banner page-error">{error}</div>}
      {loading && !info ? <div className="loading-state"><LoaderCircle className="spin" /> Sistem okunuyor…</div> : info && <>
        <div className="system-status panel"><div className={`system-orb ${info.cuda_available ? "healthy" : "warning"}`}>{info.cuda_available ? <CheckCircle2 size={30} /> : <XCircle size={30} />}</div><div><span className="eyebrow">GENEL DURUM</span><h2>{info.cuda_available ? "Sistem üretime hazır" : "CUDA kullanılamıyor"}</h2><p>{info.cuda_available ? `${info.device_name} başarıyla algılandı.` : "Üretimler CPU üzerinde daha yavaş çalışacak."}</p></div><span className="live-badge"><span className="pulse" /> CANLI</span></div>
        <div className="metric-grid">
          <Metric icon={Cpu} label="Hesaplama aygıtı" value={info.device_name} detail={info.device.toUpperCase()} />
          <Metric icon={MemoryStick} label="Ayrılan GPU belleği" value={`${info.gpu_memory_allocated_mb.toFixed(0)} MB`} detail={`${info.gpu_memory_reserved_mb.toFixed(0)} MB rezerve`} />
          <Metric icon={Server} label="Chatterbox modeli" value={info.model_loaded ? "Bellekte" : "Beklemede"} detail={info.model_loaded ? "İlk üretim tamamlandı" : "İlk istekte yüklenecek"} />
          <Metric icon={Activity} label="Üretim kuyruğu" value={`${info.queue_size} iş`} detail="Tek GPU işçisi" />
        </div>
        <section className="panel stats-panel"><div className="section-heading"><div><span className="eyebrow">YEREL İSTATİSTİKLER</span><h2>Üretim özeti</h2></div><Database size={22} /></div><div className="stats-grid"><Stat icon={Volume2} label="Tamamlanan ses" value={String(info.statistics.total)} /><Stat icon={Gauge} label="Toplam kelime" value={String(info.statistics.total_words)} /><Stat icon={Timer} label="Toplam ses" value={formatDuration(info.statistics.total_audio_seconds)} /><Stat icon={Activity} label="Ortalama üretim" value={`${info.statistics.average_generation_seconds.toFixed(1)} sn`} /></div></section>
        <section className="panel tech-panel"><div><span>Python</span><strong>{info.python_version}</strong></div><div><span>PyTorch</span><strong>{info.torch_version}</strong></div><div><span>CUDA</span><strong>{info.cuda_available ? "Kullanılabilir" : "Yok"}</strong></div><div><span>API</span><strong>FastAPI 2.0</strong></div></section>
      </>}
    </div>
  );
}

function Metric({ icon: Icon, label, value, detail }: { icon: typeof Cpu; label: string; value: string; detail: string }) { return <article className="panel metric-card"><span className="metric-icon"><Icon size={22} /></span><div><small>{label}</small><strong>{value}</strong><p>{detail}</p></div></article>; }
function Stat({ icon: Icon, label, value }: { icon: typeof Cpu; label: string; value: string }) { return <div className="stat"><Icon size={18} /><span><small>{label}</small><strong>{value}</strong></span></div>; }
function formatDuration(seconds: number) { if (seconds < 60) return `${seconds.toFixed(0)} sn`; return `${Math.floor(seconds / 60)} dk ${Math.round(seconds % 60)} sn`; }
