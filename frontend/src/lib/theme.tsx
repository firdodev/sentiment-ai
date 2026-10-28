import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";

type Theme = "light" | "dark";

/* Ngjyrat e grafikëve (Recharts kërkon vlera konkrete, jo var()).
   Të njëjtat vlera si tokenat në index.css. */
const CHART = {
  light: {
    pos: "#2a78d6", neg: "#e34948", neutral: "#a3a199", surface: "#fcfcfb",
    grid: "#e1e0d9", axis: "#898781", baseline: "#c3c2b7", ink: "#0b0b0b", ink2: "#52514e",
    posWash: "rgba(42,120,214,0.10)", negWash: "rgba(227,73,72,0.10)", cursor: "rgba(11,11,11,0.04)",
  },
  dark: {
    pos: "#3987e5", neg: "#e66767", neutral: "#6b6a65", surface: "#1a1a19",
    grid: "#2c2c2a", axis: "#898781", baseline: "#383835", ink: "#f0efec", ink2: "#c3c2b7",
    posWash: "rgba(57,135,229,0.12)", negWash: "rgba(230,103,103,0.12)", cursor: "rgba(255,255,255,0.05)",
  },
};
export type ChartColors = (typeof CHART)["light"];

const Ctx = createContext<{ theme: Theme; toggle: () => void; c: ChartColors }>({
  theme: "light",
  toggle: () => {},
  c: CHART.light,
});

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>(
    () => (document.documentElement.dataset.theme as Theme) || "light",
  );
  const toggle = useCallback(() => {
    setTheme((t) => {
      const next = t === "light" ? "dark" : "light";
      document.documentElement.dataset.theme = next;
      try {
        localStorage.setItem("tema", next);
      } catch {
        // ruajtja mund të jetë e bllokuar; tema vlen vetëm për këtë seancë
      }
      return next;
    });
  }, []);
  const value = useMemo(() => ({ theme, toggle, c: CHART[theme] }), [theme, toggle]);
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export const useTheme = () => useContext(Ctx);
