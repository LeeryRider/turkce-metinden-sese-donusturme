"use client";

import { ArrowRight, BookOpen, GraduationCap, LoaderCircle, Megaphone, Newspaper, Radio, Sparkles } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { SpeechTemplate } from "@/lib/types";

const icons = { news: Newspaper, announcement: Megaphone, story: BookOpen, education: GraduationCap, accessibility: Radio, normal: Sparkles };

export function TemplatesClient() {
  const router = useRouter();
  const [templates, setTemplates] = useState<SpeechTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api.templates().then((data) => setTemplates(data.templates)).catch((reason: Error) => setError(reason.message)).finally(() => setLoading(false));
  }, []);

  function applyTemplate(template: SpeechTemplate) {
    window.localStorage.setItem("seda-studio-draft", JSON.stringify({ text: template.text, title: template.title, preset: template.preset }));
    router.push("/studio");
  }

  return (
    <div className="page">
      <header className="page-header"><div><span className="eyebrow">HAZIR BAŞLANGIÇLAR</span><h1>Konuşma şablonları</h1><p>Sık kullanılan senaryolardan birini seçin ve metni dilediğiniz gibi düzenleyin.</p></div></header>
      {error && <div className="error-banner page-error">{error}</div>}
      {loading ? <div className="loading-state"><LoaderCircle className="spin" /> Şablonlar yükleniyor…</div> : (
        <div className="template-grid">
          {templates.map((template, index) => {
            const Icon = icons[template.preset];
            return (
              <article className={`panel template-card template-${index + 1}`} key={template.id}>
                <div className="template-top"><span className="template-icon"><Icon size={24} /></span><span className="template-category">{template.category}</span></div>
                <h2>{template.title}</h2><p>{template.text}</p>
                <button onClick={() => applyTemplate(template)}>Stüdyoda kullan <ArrowRight size={17} /></button>
              </article>
            );
          })}
        </div>
      )}
    </div>
  );
}
