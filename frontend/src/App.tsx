import { useEffect, useState } from "react";
import { MotionConfig } from "motion/react";
import {
  BrainIcon,
  ChartPieSliceIcon,
  ChatTextIcon,
  MoonIcon,
  ShareNetworkIcon,
  SunIcon,
  type Icon,
} from "@phosphor-icons/react";
import { ThemeProvider, useTheme } from "./lib/theme";
import { getJSON } from "./lib/api";
import { cx } from "./components/ui";
import Analyze from "./pages/Analyze";
import Business from "./pages/Business";
import Social from "./pages/Social";
import Model from "./pages/Model";

const PAGES: { id: string; label: string; icon: Icon }[] = [
  { id: "analizo", label: "Testo komentin", icon: ChatTextIcon },
  { id: "biznesi", label: "Analiza e biznesit", icon: ChartPieSliceIcon },
  { id: "rrjetet", label: "Rrjetet sociale", icon: ShareNetworkIcon },
  { id: "modeli", label: "Modeli", icon: BrainIcon },
];

function currentPage() {
  const id = window.location.hash.replace("#/", "");
  return PAGES.some((p) => p.id === id) ? id : "analizo";
}

function Mark() {
  return (
    <span aria-hidden className="grid h-8 w-8 place-items-center rounded-[9px] bg-btn text-[13px] font-semibold tracking-tight text-btn-ink">
      ZK
    </span>
  );
}

function Shell() {
  const { theme, toggle } = useTheme();
  const [page, setPage] = useState(currentPage);
  const [health, setHealth] = useState<{ modeli?: string } | null>(null);

  useEffect(() => {
    const onHash = () => setPage(currentPage());
    window.addEventListener("hashchange", onHash);
    getJSON<{ modeli: string }>("/api/health").then(setHealth).catch(() => setHealth({}));
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  const ThemeIcon = theme === "dark" ? SunIcon : MoonIcon;
  const nav = (mobile: boolean) =>
    PAGES.map((p) => {
      const active = page === p.id;
      return (
        <a
          key={p.id}
          href={`#/${p.id}`}
          aria-current={active ? "page" : undefined}
          className={cx(
            "flex shrink-0 items-center gap-2.5 rounded-[10px] text-sm font-medium transition-colors",
            mobile ? "h-9 px-3" : "h-10 px-3",
            active ? "bg-surface text-ink shadow-card" : "text-ink-3 hover:bg-sunken hover:text-ink",
          )}
        >
          <p.icon size={18} weight={active ? "fill" : "regular"} />
          {p.label}
        </a>
      );
    });

  return (
    <div className="min-h-[100dvh] lg:grid lg:grid-cols-[248px_1fr]">
      {/* Navigimi anësor (desktop) */}
      <aside className="no-print sticky top-0 hidden h-[100dvh] flex-col border-r border-line px-4 py-6 lg:flex">
        <div className="flex items-center gap-2.5 px-2">
          <Mark />
          <div>
            <p className="text-[15px] font-semibold leading-tight tracking-tight text-ink">Zëri i Klientit</p>
            <p className="text-[12px] text-ink-3">Analizë sentimenti</p>
          </div>
        </div>
        <nav aria-label="Faqet" className="mt-8 flex flex-col gap-1">{nav(false)}</nav>
        <div className="mt-auto flex flex-col gap-3 px-2">
          <p className="text-[12px] leading-relaxed text-ink-3">
            {health?.modeli ? `Modeli aktiv: ${health.modeli}` : health ? "Serveri nuk u gjet" : "Duke u lidhur..."}
          </p>
          <button onClick={toggle} className="inline-flex h-9 items-center gap-2 self-start rounded-[10px] px-2 text-sm text-ink-2 transition-colors hover:bg-sunken hover:text-ink">
            <ThemeIcon size={18} /> {theme === "dark" ? "Tema e çelët" : "Tema e errët"}
          </button>
        </div>
      </aside>

      {/* Shiriti i sipërm (celular / tablet) */}
      <header className="no-print sticky top-0 z-10 border-b border-line bg-page/90 backdrop-blur lg:hidden">
        <div className="flex h-14 items-center justify-between px-4">
          <div className="flex items-center gap-2.5">
            <Mark />
            <p className="text-[15px] font-semibold tracking-tight text-ink">Zëri i Klientit</p>
          </div>
          <button onClick={toggle} aria-label="Ndrysho temën" className="grid h-9 w-9 place-items-center rounded-[10px] text-ink-2 hover:bg-sunken">
            <ThemeIcon size={18} />
          </button>
        </div>
        <nav aria-label="Faqet" className="flex gap-1 overflow-x-auto px-3 pb-2.5 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">{nav(true)}</nav>
      </header>

      <main className="print-full mx-auto w-full max-w-[1240px] px-4 py-6 md:px-8 md:py-10">
        {/* Faqet mbeten të montuara, që rezultatet të mos humbasin kur ndërron faqe */}
        {PAGES.map((p) => (
          <div key={p.id} hidden={page !== p.id}>
            {p.id === "analizo" && <Analyze />}
            {p.id === "biznesi" && <Business />}
            {p.id === "rrjetet" && <Social />}
            {p.id === "modeli" && page === "modeli" && <Model />}
          </div>
        ))}
      </main>
    </div>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <MotionConfig reducedMotion="user">
        <Shell />
      </MotionConfig>
    </ThemeProvider>
  );
}
