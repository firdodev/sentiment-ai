import { useMemo, useState, type ReactNode } from "react";
import { motion } from "motion/react";
import {
  ArrowDownIcon,
  ArrowUpIcon,
  CaretLeftIcon,
  CaretRightIcon,
  ChatsCircleIcon,
  DownloadSimpleIcon,
  FileCsvIcon,
  LightbulbIcon,
  LinkSimpleIcon,
  MagnifyingGlassIcon,
  PrinterIcon,
  QuotesIcon,
  StarIcon,
  UsersThreeIcon,
} from "@phosphor-icons/react";
import type { CommentRow, Report } from "../types";
import { num, pct, plural, shortDate, signed } from "../lib/format";
import { useTheme } from "../lib/theme";
import {
  AspectDiverging,
  DimensionTable,
  KeywordList,
  Legend,
  MiniTrend,
  SimpleBars,
  SplitBar,
  TimelineSatisfaction,
  TimelineVolume,
} from "./charts";
import { Button, Card, Chip, SentimentTag, Segmented, StatusIcon, StatusLabel, cx, inputClass } from "./ui";

function Reveal({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: 12 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.15 }}
      transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
    >
      {children}
    </motion.div>
  );
}

function Stat({ label, value, sub }: { label: string; value: ReactNode; sub?: ReactNode }) {
  return (
    <div className="rounded-[12px] bg-sunken px-4 py-3.5">
      <p className="text-[13px] text-ink-3">{label}</p>
      <p className="mt-1 text-[26px] font-semibold leading-none tracking-tight text-ink">{value}</p>
      {sub && <p className="mt-2 text-[12px] text-ink-3">{sub}</p>}
    </div>
  );
}

function Stars({ value }: { value: number }) {
  return (
    <span className="inline-flex items-center gap-0.5" aria-label={`${value.toFixed(1)} nga 5 yje`}>
      {[1, 2, 3, 4, 5].map((i) => (
        <StarIcon key={i} size={13} weight={value >= i - 0.25 ? "fill" : "regular"} className="text-ink-2" />
      ))}
    </span>
  );
}

function SourceLine({ report }: { report: Report }) {
  const b = report.burimi;
  const Icon = b.lloji === "postim" ? LinkSimpleIcon : b.lloji === "tekst" ? ChatsCircleIcon : FileCsvIcon;
  return (
    <div className="flex min-w-0 items-center gap-3">
      <span className="grid h-10 w-10 shrink-0 place-items-center rounded-[10px] bg-sunken text-ink-2">
        <Icon size={20} weight="duotone" />
      </span>
      <div className="min-w-0">
        <p className="truncate font-medium text-ink">
          {b.lloji === "postim" && b.url ? (
            <a href={b.url} target="_blank" rel="noreferrer" className="underline decoration-line-2 underline-offset-4 hover:decoration-ink">
              Postim në {b.emri}
            </a>
          ) : (
            b.emri
          )}
        </p>
        <p className="text-[13px] text-ink-3">
          {plural(report.kpi.gjithsej, "koment", "komente")}
          {report.periudha && `, ${shortDate(report.periudha.nga)} deri ${shortDate(report.periudha.deri)}`}
        </p>
      </div>
    </div>
  );
}

function CommentCard({ row }: { row: CommentRow }) {
  return (
    <li className="rounded-[12px] border border-line bg-page p-4">
      <p className="text-[15px] leading-relaxed text-ink">{row.koment}</p>
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <SentimentTag s={row.sentimenti} />
        {row.data && <Chip>{shortDate(row.data)}</Chip>}
        {row.platforma && <Chip>{row.platforma}</Chip>}
        {row.produkti && <Chip>{row.produkti}</Chip>}
        {row.qyteti && <Chip>{row.qyteti}</Chip>}
        {row.vleresimi != null && (
          <Chip>
            <Stars value={row.vleresimi} />
          </Chip>
        )}
        {row.klienti && <Chip>{row.klienti}</Chip>}
      </div>
    </li>
  );
}

const FILTERS = [
  { value: "all", label: "Të gjitha" },
  { value: "pozitiv", label: "Pozitive" },
  { value: "negativ", label: "Negative" },
  { value: "urgjent", label: "Urgjente" },
] as const;
type Filter = (typeof FILTERS)[number]["value"];
const PAGE = 20;

function CommentsTable({ rows, total }: { rows: CommentRow[]; total: number }) {
  const [q, setQ] = useState("");
  const [filter, setFilter] = useState<Filter>("all");
  const [page, setPage] = useState(0);
  const filtered = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return rows.filter(
      (r) =>
        (filter === "all" || (filter === "urgjent" ? r.prioriteti === "urgjent" : r.sentimenti === filter)) &&
        (!needle || r.koment.toLowerCase().includes(needle) || r.aspektet.join(" ").toLowerCase().includes(needle)),
    );
  }, [rows, q, filter]);
  const pages = Math.max(1, Math.ceil(filtered.length / PAGE));
  const current = Math.min(page, pages - 1);
  const slice = filtered.slice(current * PAGE, current * PAGE + PAGE);
  const extra = ["data", "platforma", "produkti", "qyteti"].filter((k) => rows.some((r) => r[k as keyof CommentRow]));

  return (
    <Card
      title="Të gjitha komentet"
      description={rows.length < total ? `Shfaqen ${num(rows.length)} të parat nga ${num(total)}. Skedari CSV i ka të gjitha.` : undefined}
    >
      <div className="no-print mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div className="relative md:w-80">
          <label htmlFor="kerko" className="sr-only">Kërko në komente</label>
          <MagnifyingGlassIcon size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ink-3" />
          <input
            id="kerko"
            value={q}
            onChange={(e) => {
              setQ(e.target.value);
              setPage(0);
            }}
            placeholder="Kërko fjalë ose aspekt, p.sh. dërgesa"
            className={cx(inputClass, "h-10 py-0 pl-9 text-sm")}
          />
        </div>
        <Segmented
          label="Filtro sipas sentimentit"
          options={FILTERS.map((f) => ({ ...f }))}
          value={filter}
          onChange={(v) => {
            setFilter(v);
            setPage(0);
          }}
        />
      </div>
      <div className="-mx-5 overflow-x-auto md:-mx-6">
        <table className="w-full min-w-[720px] text-left text-sm">
          <thead>
            <tr className="text-[12px] text-ink-3">
              <th className="px-5 py-2 font-medium md:px-6">Komenti</th>
              <th className="py-2 font-medium">Sentimenti</th>
              <th className="py-2 pr-4 text-right font-medium">Siguria</th>
              <th className="py-2 pr-4 font-medium">Aspektet</th>
              {extra.map((k) => (
                <th key={k} className="py-2 pr-5 font-medium capitalize">{k}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {slice.map((r, i) => (
              <tr key={`${current}-${i}`} className="border-t border-line align-top">
                <td className="max-w-[420px] px-5 py-3 text-ink md:px-6">{r.koment}</td>
                <td className="py-3"><SentimentTag s={r.sentimenti} /></td>
                <td className="tnum py-3 pr-4 text-right text-ink-2">{pct(r.besueshmeria * 100, 0)}</td>
                <td className="py-3 pr-4 text-ink-2">{r.aspektet.join(", ") || "-"}</td>
                {extra.map((k) => (
                  <td key={k} className="whitespace-nowrap py-3 pr-5 text-ink-2">
                    {k === "data" ? shortDate(r.data) : String(r[k as keyof CommentRow] ?? "-")}
                  </td>
                ))}
              </tr>
            ))}
            {!slice.length && (
              <tr><td colSpan={4 + extra.length} className="px-6 py-8 text-center text-ink-3">Asnjë koment nuk përputhet me filtrin.</td></tr>
            )}
          </tbody>
        </table>
      </div>
      <div className="no-print mt-4 flex items-center justify-between text-[13px] text-ink-3">
        <span className="tnum">{plural(filtered.length, "rezultat", "rezultate")}</span>
        <div className="flex items-center gap-1">
          <Button variant="ghost" size="sm" icon={CaretLeftIcon} disabled={current === 0} onClick={() => setPage(current - 1)} aria-label="Faqja e mëparshme" />
          <span className="tnum px-2">{current + 1} / {pages}</span>
          <Button variant="ghost" size="sm" icon={CaretRightIcon} disabled={current >= pages - 1} onClick={() => setPage(current + 1)} aria-label="Faqja tjetër" />
        </div>
      </div>
    </Card>
  );
}

export function Dashboard({ report }: { report: Report }) {
  const { c } = useTheme();
  const k = report.kpi;
  const delta = k.krahasimi_30_dite;
  const [mode, setMode] = useState<"volume" | "pct">("volume");
  const dims = Object.entries(report.dimensionet);
  const [dim, setDim] = useState(dims[0]?.[0] ?? "");
  const activeDim = report.dimensionet[dim] ?? dims[0]?.[1];
  const hasRating = report.vleresimet != null;
  const trends = Object.entries(report.aspektet_ne_kohe);

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-col gap-4 rounded-[14px] border border-line bg-surface p-4 shadow-card md:flex-row md:items-center md:justify-between md:px-5">
        <SourceLine report={report} />
        <div className="no-print flex flex-wrap gap-2">
          <a href={report.shkarko} className="inline-flex h-10 items-center gap-2 rounded-[10px] border border-line bg-surface px-4 text-sm font-medium text-ink transition-colors hover:border-line-2 hover:bg-sunken active:scale-[0.98]">
            <DownloadSimpleIcon size={16} weight="bold" /> Shkarko CSV
          </a>
          <Button variant="secondary" icon={PrinterIcon} onClick={() => window.print()}>Printo raportin</Button>
        </div>
      </div>

      {/* KPI */}
      <Reveal className="grid grid-cols-1 gap-5 lg:grid-cols-12">
        <Card className="lg:col-span-5" bodyClassName="flex h-full flex-col">
          <p className="text-sm text-ink-3">Kënaqësia e klientëve</p>
          <div className="mt-2 flex flex-wrap items-end gap-x-4 gap-y-2">
            <span className="text-[56px] font-semibold leading-none tracking-tighter text-ink">{pct(k.perqindja_pozitive)}</span>
            {delta && (
              <span className="mb-1.5 inline-flex items-center gap-1 text-sm text-ink-2">
                {delta.ndryshimi_pp >= 0 ? (
                  <ArrowUpIcon size={16} weight="bold" className="text-good-ink" aria-label="rritje" />
                ) : (
                  <ArrowDownIcon size={16} weight="bold" className="text-critical" aria-label="rënie" />
                )}
                <span className="tnum font-medium text-ink">{signed(delta.ndryshimi_pp)} pikë</span>
                <span>në 30 ditët e fundit</span>
              </span>
            )}
          </div>
          <SplitBar pos={k.pozitiv} neg={k.negativ} className="mt-5 h-2.5" />
          <div className="mt-2.5 flex justify-between text-[13px] text-ink-2">
            <Legend items={[{ label: `${num(k.pozitiv)} pozitive`, color: c.pos }]} />
            <Legend items={[{ label: `${num(k.negativ)} negative`, color: c.neg }]} />
          </div>
          <p className="mt-5 border-t border-line pt-4 text-[15px] leading-relaxed text-ink-2">{report.permbledhja}</p>
        </Card>
        <div className="grid grid-cols-2 gap-3 lg:col-span-7 lg:gap-4 [&>*:last-child:nth-child(odd)]:col-span-2">
          <Stat label="Komente të analizuara" value={num(k.gjithsej)} sub={k.te_pasigurt ? `${num(k.te_pasigurt)} të pasigurta për modelin` : `Siguria mesatare ${pct(k.besueshmeria_mesatare)}`} />
          <Stat label="Neto sentimenti" value={signed(k.neto_sentimenti)} sub="Pozitive minus negative, në pikë" />
          {k.vleresimi_mesatar != null ? (
            <Stat label="Vlerësimi mesatar" value={<span className="inline-flex items-baseline gap-2">{k.vleresimi_mesatar.toFixed(2)}<span className="text-sm font-normal text-ink-3">/ 5</span></span>} sub={<Stars value={k.vleresimi_mesatar} />} />
          ) : (
            <Stat label="Ankesa" value={num(k.negativ)} sub={`${pct(k.perqindja_negative)} e komenteve`} />
          )}
          <Stat label="Urgjente" value={num(k.urgjente)} sub="Ankesa të fundit ose të rënda" />
          {report.klientet && (
            <Stat label="Klientë unikë" value={num(report.klientet.unik)} sub={`${num(report.klientet.te_perseritur)} kanë shkruar më shumë se një herë`} />
          )}
          {delta && (
            <Stat label="Komente, 30 ditët e fundit" value={num(delta.volumi)} sub={`${signed(delta.ndryshimi_volumit)}% kundrejt 30 ditëve më parë`} />
          )}
        </div>
      </Reveal>

      {/* Insight-et dhe rekomandimet */}
      <Reveal className="grid grid-cols-1 items-start gap-5 lg:grid-cols-[1.55fr_1fr]">
        <Card title="Çfarë tregojnë të dhënat" description="Gjetje të nxjerra automatikisht nga komentet.">
          <ul className="flex flex-col divide-y divide-line">
            {report.insights.map((i) => (
              <li key={i.titulli} className="flex gap-3 py-3 first:pt-0 last:pb-0">
                <StatusIcon kind={i.lloji} />
                <div className="min-w-0">
                  <p className="font-medium text-ink">{i.titulli}</p>
                  <p className="mt-0.5 text-sm text-ink-3">{i.teksti}</p>
                </div>
                <span className="ml-auto hidden shrink-0 sm:block"><StatusLabel kind={i.lloji} /></span>
              </li>
            ))}
          </ul>
        </Card>
        <Card title="Çfarë të bësh" description="Hapat me më shumë ndikim, sipas ankesave kryesore.">
          {report.rekomandime.length ? (
            <ol className="flex flex-col gap-4">
              {report.rekomandime.map((r, idx) => (
                <li key={r.aspekti} className="flex gap-3">
                  <span className="tnum grid h-7 w-7 shrink-0 place-items-center rounded-full bg-sunken text-[13px] font-semibold text-ink">{idx + 1}</span>
                  <div>
                    <p className="font-medium text-ink">{r.aspekti}</p>
                    <p className="mt-0.5 text-sm leading-relaxed text-ink-3">{r.teksti}</p>
                  </div>
                </li>
              ))}
            </ol>
          ) : (
            <p className="flex items-center gap-2 text-sm text-ink-3"><LightbulbIcon size={18} /> Nuk u gjetën ankesa të përsëritura.</p>
          )}
        </Card>
      </Reveal>

      {/* Tendenca */}
      {report.tendenca && report.tendenca.length > 1 && (
        <Reveal>
          <Card
            title="Tendenca në kohë"
            description={`Sipas ${report.granulariteti}.`}
            actions={
              <Segmented
                label="Mënyra e grafikut"
                options={[{ value: "volume", label: "Volumi" }, { value: "pct", label: "Kënaqësia %" }]}
                value={mode}
                onChange={setMode}
              />
            }
          >
            {mode === "volume" && <div className="mb-3"><Legend items={[{ label: "Pozitive", color: c.pos }, { label: "Negative", color: c.neg }]} /></div>}
            {mode === "volume" ? <TimelineVolume data={report.tendenca} /> : <TimelineSatisfaction data={report.tendenca} average={k.perqindja_pozitive} />}
          </Card>
        </Reveal>
      )}

      {/* Aspektet */}
      {report.aspektet.length > 0 && (
        <Reveal className={cx("grid grid-cols-1 gap-5", trends.length > 0 && "lg:grid-cols-[1.3fr_1fr]")}>
          <Card title="Për çfarë flasin klientët" description="Aspektet e përmendura: ankesat majtas, lëvdatat djathtas.">
            <div className="mb-3"><Legend items={[{ label: "Ankesa", color: c.neg }, { label: "Lëvdata", color: c.pos }]} /></div>
            <AspectDiverging data={report.aspektet} />
          </Card>
          {trends.length > 0 && (
            <Card title="Ankesat kryesore në kohë" description="Kur u shfaqën problemet.">
              <div className="flex flex-col gap-4">
                {trends.map(([name, series]) => {
                  const total = series.reduce((s, p) => s + p.ankesa, 0);
                  return (
                    <div key={name}>
                      <div className="flex items-baseline justify-between text-sm">
                        <span className="font-medium text-ink">{name}</span>
                        <span className="tnum text-[13px] text-ink-3">{plural(total, "ankesë", "ankesa")}</span>
                      </div>
                      <MiniTrend data={series} color={c.neg} />
                    </div>
                  );
                })}
              </div>
            </Card>
          )}
        </Reveal>
      )}

      {/* Dimensionet */}
      {activeDim && (
        <Reveal>
          <Card
            title="Krahasim sipas grupit"
            description="Ku janë klientët më të kënaqur dhe ku më pak."
            actions={dims.length > 1 && (
              <Segmented label="Zgjidh dimensionin" options={dims.map(([key, d]) => ({ value: key, label: d.titulli }))} value={dim} onChange={setDim} />
            )}
          >
            <DimensionTable rows={activeDim.rreshtat} showRating={hasRating} />
          </Card>
        </Reveal>
      )}

      {/* Kur shkruajnë dhe vlerësimet */}
      {(report.ditet_e_javes || report.vleresimet) && (
        <Reveal className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-3">
          {report.ditet_e_javes && (
            <Card title="Ditët e javës" description="Numri i komenteve sipas ditës.">
              <SimpleBars data={report.ditet_e_javes.map((d) => ({ ...d, shkurt: d.dita.replace("E ", "").slice(0, 3) }))} x="shkurt" y="gjithsej" color={c.neutral}
                title={(d) => d.dita} tipRows={(d) => [{ label: "Komente", value: num(d.gjithsej) }, { label: "Kënaqësia", value: pct(d.perqindja_pozitive) }]} />
            </Card>
          )}
          {report.oret && (
            <Card title="Orët e ditës" description="Kur shkruajnë klientët.">
              <SimpleBars data={report.oret} x="ora" y="gjithsej" color={c.neutral}
                title={(d) => `Ora ${d.ora}:00`} tipRows={(d) => [{ label: "Komente", value: num(d.gjithsej) }]} />
            </Card>
          )}
          {report.vleresimet && (
            <Card title="Vlerësimet me yje" description="Shpërndarja nga 1 deri 5 yje.">
              <SimpleBars data={report.vleresimet.map((r) => ({ ...r, yjet: `${r.yje}★` }))} x="yjet" y="numri" color={c.neutral}
                title={(d) => `${d.yje} yje`} tipRows={(d) => [{ label: "Komente", value: num(d.numri) }]} />
            </Card>
          )}
        </Reveal>
      )}

      {/* Fjalët */}
      <Reveal>
        <Card title="Fjalët që dallojnë" description="Fjalët më karakteristike në ankesa dhe në lëvdata.">
          <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
            <div>
              <p className="mb-3 text-sm font-medium text-ink">Në ankesa</p>
              <KeywordList items={report.fjalet.negative} tone="neg" />
            </div>
            <div>
              <p className="mb-3 text-sm font-medium text-ink">Në lëvdata</p>
              <KeywordList items={report.fjalet.pozitive} tone="pos" />
            </div>
          </div>
        </Card>
      </Reveal>

      {/* Urgjente, klientët, dëshmitë */}
      <Reveal className="grid grid-cols-1 items-start gap-5 lg:grid-cols-[1.4fr_1fr]">
        <Card title="Kërkojnë përgjigje tani" description="Ankesat më të fundit ose më të rënda.">
          {report.urgjente.length ? (
            <ul className="flex flex-col gap-3">{report.urgjente.slice(0, 6).map((r, i) => <CommentCard key={i} row={r} />)}</ul>
          ) : (
            <p className="text-sm text-ink-3">Asnjë koment urgjent.</p>
          )}
        </Card>
        <div className="flex flex-col gap-5">
          {report.klientet && report.klientet.ne_rrezik.length > 0 && (
            <Card title="Klientë në rrezik" description={`${plural(report.klientet.numri_ne_rrezik, "klient ka", "klientë kanë")} 2 ose më shumë ankesa.`}>
              <ul className="flex flex-col divide-y divide-line">
                {report.klientet.ne_rrezik.map((cl) => (
                  <li key={cl.klienti} className="flex items-center justify-between py-2.5 text-sm first:pt-0 last:pb-0">
                    <span className="inline-flex items-center gap-2 font-medium text-ink"><UsersThreeIcon size={16} className="text-ink-3" />{cl.klienti}</span>
                    <span className="tnum text-ink-3">{cl.negativ} ankesa nga {cl.gjithsej}</span>
                  </li>
                ))}
              </ul>
            </Card>
          )}
          {report.deshmi.length > 0 && (
            <Card title="Komente për t'u ndarë" description="Lëvdata të qarta, të mira për faqen ose rrjetet sociale.">
              <ul className="flex flex-col gap-4">
                {report.deshmi.slice(0, 3).map((r, i) => (
                  <li key={i} className="flex gap-3">
                    <QuotesIcon size={18} weight="fill" className="mt-0.5 shrink-0 text-ink-3" />
                    <div>
                      <p className="text-[15px] leading-relaxed text-ink">{r.koment}</p>
                      <p className="mt-1 text-[13px] text-ink-3">{[r.klienti, r.platforma, r.qyteti].filter(Boolean).join(", ")}</p>
                    </div>
                  </li>
                ))}
              </ul>
            </Card>
          )}
        </div>
      </Reveal>

      <CommentsTable rows={report.rreshtat} total={k.gjithsej} />
    </div>
  );
}
