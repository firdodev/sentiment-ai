export type Sentiment = "pozitiv" | "negativ" | "i panjohur";
export type InsightKind = "good" | "warning" | "critical" | "info";

export interface Prediction {
  teksti: string;
  sentimenti: Sentiment;
  besueshmeria: number;
  probabilitetet: Record<string, number>;
  i_pasigurt: boolean;
  fjalet_kyce: { fjala: string; ndikimi: number }[];
  aspektet: string[];
  asistenti: { prioriteti: string; veprimi: string; pergjigja: string; burimi: string };
  llm_sentimenti?: string | null;
}

export interface CommentRow {
  koment: string;
  sentimenti: Sentiment;
  besueshmeria: number;
  aspektet: string[];
  data?: string;
  platforma?: string;
  produkti?: string;
  qyteti?: string;
  vleresimi?: number;
  klienti?: string;
  prioriteti?: string;
}

export interface DimensionRow {
  emri: string;
  gjithsej: number;
  pozitiv: number;
  negativ: number;
  perqindja_pozitive: number;
  vleresimi_mesatar?: number | null;
  ankesa_kryesore?: string | null;
}

export interface TimelinePoint {
  periudha: string;
  etiketa: string;
  pozitiv: number;
  negativ: number;
  gjithsej: number;
  perqindja_pozitive: number;
}

export interface Report {
  burimi: {
    lloji: "skedar" | "tekst" | "shembull" | "postim";
    emri: string;
    platforma?: string;
    lloji_postit?: string;
    url?: string;
    lidhja?: string;
    shenim?: string | null;
  } & Record<string, unknown>;
  shkarko: string;
  kolonat: Record<string, string>;
  kpi: {
    gjithsej: number;
    te_klasifikuara: number;
    pozitiv: number;
    negativ: number;
    perqindja_pozitive: number;
    perqindja_negative: number;
    neto_sentimenti: number;
    besueshmeria_mesatare: number;
    te_pasigurt: number;
    urgjente: number;
    vleresimi_mesatar?: number | null;
    krahasimi_30_dite?: {
      perqindja_pozitive: number;
      me_pare: number;
      ndryshimi_pp: number;
      volumi: number;
      volumi_me_pare: number;
      ndryshimi_volumit: number;
    };
  };
  periudha?: { nga: string; deri: string };
  granulariteti?: string;
  tendenca?: TimelinePoint[];
  ditet_e_javes?: { dita: string; gjithsej: number; perqindja_pozitive: number }[];
  oret?: { ora: string; gjithsej: number }[];
  dimensionet: Record<string, { titulli: string; rreshtat: DimensionRow[] }>;
  aspektet: {
    aspekti: string;
    permendje: number;
    pozitiv: number;
    negativ: number;
    perqindja_negative: number;
    pjesa_e_ankesave: number;
  }[];
  aspektet_ne_kohe: Record<string, { periudha: string; etiketa: string; ankesa: number }[]>;
  fjalet: { pozitive: { fjala: string; numri: number }[]; negative: { fjala: string; numri: number }[] };
  vleresimet?: { yje: number; numri: number }[];
  klientet?: {
    unik: number;
    te_perseritur: number;
    numri_ne_rrezik: number;
    ne_rrezik: { klienti: string; negativ: number; gjithsej: number }[];
  };
  urgjente: CommentRow[];
  deshmi: CommentRow[];
  insights: { lloji: InsightKind; titulli: string; teksti: string }[];
  rekomandime: { aspekti: string; teksti: string }[];
  permbledhja: string;
  rreshtat: CommentRow[];
}

export interface ModelInfo {
  modeli: string;
  data: string;
  madhesia_dataset: number;
  train: number;
  test: number;
  cv_f1: Record<string, number>;
  test_accuracy: number;
  test_f1: number;
  test_real_accuracy?: number;
  test_real_f1?: number;
  matrica_konfuzionit: number[][];
  test_real_gabime?: { koment: string; e_verteta: string; parashikuar: string }[];
}

export interface ApiError {
  gabim: string;
  kodi?: string;
  ndihme?: string[] | null;
}

export type SettingsStatus = Record<string, { pershkrimi: string; vendosur: boolean }>;

export interface ParsedLink {
  platforma: "instagram" | "facebook" | "linkedin" | "tiktok";
  emri: string;
  lloji: string;
  id: string | null;
  url: string;
  burimet: string[];
}
