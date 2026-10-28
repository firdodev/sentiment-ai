import { useRef, useState, type DragEvent } from "react";
import { motion } from "motion/react";
import {
  ArrowCounterClockwiseIcon,
  ChartLineUpIcon,
  ClipboardTextIcon,
  DownloadSimpleIcon,
  UploadSimpleIcon,
} from "@phosphor-icons/react";
import { postFile, postJSON, RequestError } from "../lib/api";
import type { Report } from "../types";
import { Dashboard } from "../components/Dashboard";
import { Button, Card, ErrorNote, Field, PageHeader, Skeleton, cx, inputClass } from "../components/ui";

const COLUMNS = [
  ["koment", "e detyrueshme", "teksti i komentit"],
  ["data", "opsionale", "tendenca, ditët, orët"],
  ["platforma", "opsionale", "Instagram, Google..."],
  ["produkti / kategoria", "opsionale", "krahasim produktesh"],
  ["qyteti / dega", "opsionale", "krahasim degësh"],
  ["vleresimi", "opsionale", "yjet 1 deri 5"],
  ["klienti", "opsionale", "klientë në rrezik"],
];

export function DashboardSkeleton() {
  return (
    <div className="flex flex-col gap-5" aria-label="Duke analizuar">
      <Skeleton className="h-[72px] w-full rounded-[14px]" />
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-12">
        <Skeleton className="h-[280px] rounded-[14px] lg:col-span-5" />
        <div className="grid grid-cols-2 gap-4 lg:col-span-7">
          {[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-[130px] rounded-[12px]" />)}
        </div>
      </div>
      <Skeleton className="h-[340px] w-full rounded-[14px]" />
    </div>
  );
}

export default function Business() {
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [drag, setDrag] = useState(false);
  const [paste, setPaste] = useState("");
  const [showPaste, setShowPaste] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  async function run(task: () => Promise<Report>) {
    setLoading(true);
    setError(null);
    try {
      setReport(await task());
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (e) {
      setError((e as RequestError).message);
    } finally {
      setLoading(false);
    }
  }

  const onFile = (file?: File | null) => file && run(() => postFile<Report>("/api/business/analyze", file));
  const onDrop = (e: DragEvent) => {
    e.preventDefault();
    setDrag(false);
    onFile(e.dataTransfer.files?.[0]);
  };

  return (
    <>
      <PageHeader
        title="Analiza e biznesit"
        text="Ngarko komentet e klientëve dhe merr një raport të plotë: kënaqësia, tendenca, çfarë i shqetëson klientët dhe çfarë të përmirësosh."
        actions={report && !loading && (
          <Button variant="secondary" icon={ArrowCounterClockwiseIcon} onClick={() => setReport(null)}>Analizë e re</Button>
        )}
      />

      {loading ? (
        <DashboardSkeleton />
      ) : report ? (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.3 }}>
          <Dashboard report={report} />
        </motion.div>
      ) : (
        <div className="grid grid-cols-1 items-start gap-5 lg:grid-cols-[1.35fr_1fr]">
          <div className="flex flex-col gap-5">
            <Card>
              <div
                onDragOver={(e) => {
                  e.preventDefault();
                  setDrag(true);
                }}
                onDragLeave={() => setDrag(false)}
                onDrop={onDrop}
                className={cx(
                  "flex flex-col items-start gap-4 rounded-[12px] border border-dashed p-6 transition-colors md:p-8",
                  drag ? "border-ink bg-sunken" : "border-line-2 bg-page",
                )}
              >
                <span className="grid h-12 w-12 place-items-center rounded-[12px] bg-surface text-ink shadow-card">
                  <UploadSimpleIcon size={24} weight="bold" />
                </span>
                <div>
                  <p className="text-[17px] font-semibold text-ink">Tërhiq skedarin këtu</p>
                  <p className="mt-1 text-sm text-ink-3">CSV, Excel (.xlsx), JSON, TXT ose PDF. Deri në 25 MB.</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button icon={UploadSimpleIcon} onClick={() => fileRef.current?.click()}>Zgjidh skedarin</Button>
                  <Button variant="secondary" icon={ChartLineUpIcon} onClick={() => run(() => postJSON<Report>("/api/business/sample"))}>
                    Provo me shembullin
                  </Button>
                </div>
                <input
                  ref={fileRef}
                  type="file"
                  className="sr-only"
                  accept=".csv,.xlsx,.xls,.json,.txt,.pdf"
                  onChange={(e) => {
                    onFile(e.target.files?.[0]);
                    e.target.value = "";
                  }}
                />
              </div>
              {error && <div className="mt-4"><ErrorNote message={error} /></div>}
            </Card>

            <Card
              title="Ose ngjit komentet"
              description="Një koment për rresht, p.sh. të kopjuara nga Google Maps ose nga emaili."
              actions={!showPaste && <Button variant="ghost" size="sm" icon={ClipboardTextIcon} onClick={() => setShowPaste(true)}>Hap</Button>}
            >
              {showPaste ? (
                <form
                  className="flex flex-col gap-4"
                  onSubmit={(e) => {
                    e.preventDefault();
                    if (paste.trim()) run(() => postJSON<Report>("/api/business/analyze", { komente: paste }));
                  }}
                >
                  <Field label="Komentet" htmlFor="ngjit" help={`${paste.split("\n").filter((l) => l.trim()).length} komente`}>
                    <textarea id="ngjit" rows={7} value={paste} onChange={(e) => setPaste(e.target.value)} className={cx(inputClass, "leading-relaxed")}
                      placeholder={"Shërbim i shpejtë, faleminderit!\nPorosia vonoi një orë"} />
                  </Field>
                  <div><Button type="submit" disabled={!paste.trim()}>Analizo komentet</Button></div>
                </form>
              ) : (
                <p className="text-sm text-ink-3">Mjafton teksti. Pa datë, platformë apo produkt, raporti përqendrohet te sentimenti dhe temat.</p>
              )}
            </Card>
          </div>

          <Card title="Si duhet të duket skedari" description="Emrat e kolonave njihen në shqip ose anglisht. Sa më shumë kolona, aq më i pasur raporti.">
            <ul className="flex flex-col divide-y divide-line text-sm">
              {COLUMNS.map(([name, need, what]) => (
                <li key={name} className="grid grid-cols-[minmax(0,1fr)_auto] gap-x-3 gap-y-0.5 py-2.5 first:pt-0">
                  <code className="font-medium text-ink">{name}</code>
                  <span className={cx("text-right text-[12px]", need === "e detyrueshme" ? "font-medium text-ink" : "text-ink-3")}>{need}</span>
                  <span className="col-span-2 text-[13px] text-ink-3">{what}</span>
                </li>
              ))}
            </ul>
            <a
              href="/api/business/sample"
              className="mt-5 inline-flex items-center gap-2 text-sm font-medium text-ink underline decoration-line-2 underline-offset-4 hover:decoration-ink"
            >
              <DownloadSimpleIcon size={16} weight="bold" /> Shkarko datasetin shembull (2 600 komente)
            </a>
          </Card>
        </div>
      )}
    </>
  );
}
