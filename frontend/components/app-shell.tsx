"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Activity, BookOpenText, Cpu, History, Menu, Sparkles, X } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

const navigation = [
  { href: "/studio", label: "Stüdyo", icon: Sparkles },
  { href: "/history", label: "Geçmiş", icon: History },
  { href: "/templates", label: "Şablonlar", icon: BookOpenText },
  { href: "/system", label: "Sistem", icon: Cpu },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);
  const [online, setOnline] = useState<boolean | null>(null);

  useEffect(() => {
    let active = true;
    const check = () => api.health().then(() => active && setOnline(true)).catch(() => active && setOnline(false));
    check();
    const timer = window.setInterval(check, 10000);
    return () => { active = false; window.clearInterval(timer); };
  }, []);

  return (
    <div className="app-shell">
      <div className="ambient ambient-one" />
      <div className="ambient ambient-two" />
      <aside className={`sidebar ${menuOpen ? "sidebar-open" : ""}`}>
        <div className="brand">
          <div className="brand-mark"><span>S</span></div>
          <div><strong>SEDA</strong><small>Türkçe TTS Studio</small></div>
        </div>
        <nav className="nav-list" aria-label="Ana menü">
          {navigation.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              className={pathname === href ? "nav-link active" : "nav-link"}
              onClick={() => setMenuOpen(false)}
            >
              <Icon size={19} strokeWidth={1.8} />
              <span>{label}</span>
            </Link>
          ))}
        </nav>
        <div className="privacy-card">
          <div className="privacy-icon"><Activity size={18} /></div>
          <div><strong>Tamamen yerel</strong><p>Metin ve sesler bu bilgisayarda kalır.</p></div>
        </div>
        <div className="sidebar-footer">
          <span className={`status-dot ${online ? "online" : online === false ? "offline" : ""}`} />
          {online === null ? "Bağlanıyor" : online ? "API çevrimiçi" : "API çevrimdışı"}
          <span className="version">v2.0</span>
        </div>
      </aside>
      {menuOpen && <button className="sidebar-backdrop" aria-label="Menüyü kapat" onClick={() => setMenuOpen(false)} />}
      <main className="main-area">
        <header className="mobile-header">
          <div className="brand compact"><div className="brand-mark"><span>S</span></div><strong>SEDA</strong></div>
          <button className="icon-button" onClick={() => setMenuOpen((value) => !value)} aria-label="Menü">
            {menuOpen ? <X /> : <Menu />}
          </button>
        </header>
        {children}
      </main>
    </div>
  );
}
