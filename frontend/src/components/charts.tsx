import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useTheme, type ChartColors } from "../lib/theme";
import { compact, num, pct } from "../lib/format";
import type { DimensionRow, Report, TimelinePoint } from "../types";
import { cx } from "./ui";

/* Specifikat e shenjave: shtylla <= 24px me cep 4px vetëm në fund të vlerës, vija 2px,
   grila 1px solide horizontale, hapësirë 2px me ngjyrën e sipërfaqes mes segmenteve. */

const TICK = { fontSize: 12 };

interface TipRow {
  label: string;
  value: string;
  color?: string;
}

export function TooltipBox({ title, rows }: { title?: string; rows: TipRow[] }) {
  return (
    <div className="min-w-[160px] rounded-[10px] border border-line bg-surface px-3 py-2.5 text-[13px] shadow-card">
      {title && <p className="mb-1.5 font-medium text-ink">{title}</p>}
      <div className="flex flex-col gap-1">
        {rows.map((r) => (
          <div key={r.label} className="flex items-center justify-between gap-4">
            <span className="flex items-center gap-2 text-ink-2">
              {r.color && <span aria-hidden className="h-2.5 w-2.5 rounded-[3px]" style={{ background: r.color }} />}
              {r.label}
            </span>
            <span className="tnum font-medium text-ink">{r.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* Recharts i kalon këto props përmbajtjes së tooltip-it */
type TipProps = { active?: boolean; payload?: readonly { payload?: unknown }[] };
function tip<T>(render: (d: T) => { title?: string; rows: TipRow[] }) {
  return (props: TipProps) => {
    const d = props.payload?.[0]?.payload;
    if (!props.active || !d) return null;
    return <TooltipBox {...render(d as T)} />;
  };
}

export function Legend({ items }: { items: { label: string; color: string }[] }) {
  return (
    <div className="flex flex-wrap items-center gap-4 text-[13px] text-ink-2">
      {items.map((i) => (
        <span key={i.label} className="inline-flex items-center gap-2">
          <span aria-hidden className="h-2.5 w-2.5 rounded-[3px]" style={{ background: i.color }} />
          {i.label}
        </span>
      ))}
    </div>
  );
}

/* Rrumbullakon maksimumin në një numër "të pastër" (1, 2, 2.5, 5 × 10^n), që boshti të ketë vlera të lexueshme */
function niceMax(v: number) {
  const p = 10 ** Math.floor(Math.log10(v));
  return ([1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10].find((m) => m * p >= v) ?? 10) * p;
}

function axisProps(c: ChartColors) {
  return { tick: { ...TICK, fill: c.axis }, tickLine: false, axisLine: false } as const;
}

export function TimelineVolume({ data, height = 280 }: { data: TimelinePoint[]; height?: number }) {
  const { c } = useTheme();
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 8, right: 4, left: -12, bottom: 0 }}>
        <CartesianGrid vertical={false} stroke={c.grid} />
        <XAxis dataKey="etiketa" {...axisProps(c)} interval="preserveStartEnd" minTickGap={12} />
        <YAxis {...axisProps(c)} tickFormatter={compact} width={44} allowDecimals={false} />
        <ReferenceLine y={0} stroke={c.baseline} />
        <Tooltip
          cursor={{ fill: c.cursor }}
          content={tip<TimelinePoint>((d) => ({
            title: d.etiketa,
            rows: [
              { label: "Pozitive", value: num(d.pozitiv), color: c.pos },
              { label: "Negative", value: num(d.negativ), color: c.neg },
              { label: "Kënaqësia", value: pct(d.perqindja_pozitive) },
            ],
          }))}
        />
        <Bar dataKey="pozitiv" stackId="s" fill={c.pos} maxBarSize={24} stroke={c.surface} strokeWidth={2} isAnimationActive={false} />
        <Bar dataKey="negativ" stackId="s" fill={c.neg} maxBarSize={24} stroke={c.surface} strokeWidth={2} radius={[4, 4, 0, 0]} isAnimationActive={false} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function TimelineSatisfaction({ data, average, height = 280 }: { data: TimelinePoint[]; average: number; height?: number }) {
  const { c } = useTheme();
  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
        <CartesianGrid vertical={false} stroke={c.grid} />
        <XAxis dataKey="etiketa" {...axisProps(c)} interval="preserveStartEnd" minTickGap={12} />
        <YAxis {...axisProps(c)} domain={[0, 100]} ticks={[0, 25, 50, 75, 100]} tickFormatter={(v) => `${v}%`} width={44} />
        <ReferenceLine
          y={average}
          stroke={c.axis}
          label={{ value: `mesatarja ${pct(average)}`, position: "insideTopRight", fill: c.ink2, fontSize: 12 }}
        />
        <Tooltip
          cursor={{ stroke: c.baseline }}
          content={tip<TimelinePoint>((d) => ({
            title: d.etiketa,
            rows: [
              { label: "Kënaqësia", value: pct(d.perqindja_pozitive), color: c.pos },
              { label: "Komente", value: num(d.gjithsej) },
            ],
          }))}
        />
        <Area
          type="monotone"
          dataKey="perqindja_pozitive"
          stroke={c.pos}
          strokeWidth={2}
          fill={c.pos}
          fillOpacity={0.1}
          dot={false}
          activeDot={{ r: 5, fill: c.pos, stroke: c.surface, strokeWidth: 2 }}
          isAnimationActive={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

type AspectRow = Report["aspektet"][number];

export function AspectDiverging({ data }: { data: AspectRow[] }) {
  const { c } = useTheme();
  const rows = data.map((a) => ({ ...a, neg: -a.negativ }));
  const max = niceMax(Math.max(1, ...data.map((a) => Math.max(a.negativ, a.pozitiv))));
  const ticks = [-max, -max / 2, 0, max / 2, max];
  return (
    <ResponsiveContainer width="100%" height={Math.max(160, rows.length * 40 + 30)}>
      <BarChart data={rows} layout="vertical" stackOffset="sign" margin={{ top: 0, right: 12, left: 0, bottom: 0 }} barCategoryGap={10}>
        <CartesianGrid horizontal={false} stroke={c.grid} />
        <XAxis type="number" domain={[-max, max]} ticks={ticks} {...axisProps(c)} tickFormatter={(v) => compact(Math.abs(v))} />
        <YAxis type="category" dataKey="aspekti" {...axisProps(c)} tick={{ ...TICK, fill: c.ink2 }} width={96} />
        <ReferenceLine x={0} stroke={c.baseline} />
        <Tooltip
          cursor={{ fill: c.cursor }}
          content={tip<AspectRow>((d) => ({
            title: d.aspekti,
            rows: [
              { label: "Ankesa", value: num(d.negativ), color: c.neg },
              { label: "Lëvdata", value: num(d.pozitiv), color: c.pos },
              { label: "Pjesa e ankesave", value: pct(d.pjesa_e_ankesave) },
            ],
          }))}
        />
        <Bar dataKey="neg" stackId="d" fill={c.neg} maxBarSize={20} radius={[4, 0, 0, 4]} isAnimationActive={false} />
        <Bar dataKey="pozitiv" stackId="d" fill={c.pos} maxBarSize={20} radius={[0, 4, 4, 0]} isAnimationActive={false} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function MiniTrend({
  data,
  color,
  height = 96,
}: {
  data: { etiketa: string; ankesa: number }[];
  color: string;
  height?: number;
}) {
  const { c } = useTheme();
  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 6, right: 4, left: 4, bottom: 0 }}>
        <XAxis dataKey="etiketa" {...axisProps(c)} interval="preserveStartEnd" minTickGap={40} />
        <YAxis hide domain={[0, "dataMax"]} />
        <Tooltip
          cursor={{ stroke: c.baseline }}
          content={tip<{ etiketa: string; ankesa: number }>((d) => ({
            title: d.etiketa,
            rows: [{ label: "Ankesa", value: num(d.ankesa), color }],
          }))}
        />
        <Area type="monotone" dataKey="ankesa" stroke={color} strokeWidth={2} fill={color} fillOpacity={0.1} dot={false}
          activeDot={{ r: 4, fill: color, stroke: c.surface, strokeWidth: 2 }} isAnimationActive={false} />
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function SimpleBars<T extends object>({
  data,
  x,
  y,
  color,
  height = 200,
  tipRows,
  title,
}: {
  data: T[];
  x: keyof T & string;
  y: keyof T & string;
  color: string;
  height?: number;
  title: (d: T) => string;
  tipRows: (d: T) => TipRow[];
}) {
  const { c } = useTheme();
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 8, right: 4, left: -12, bottom: 0 }}>
        <CartesianGrid vertical={false} stroke={c.grid} />
        <XAxis dataKey={x as string} {...axisProps(c)} interval="preserveStartEnd" />
        <YAxis {...axisProps(c)} tickFormatter={compact} width={44} allowDecimals={false} />
        <ReferenceLine y={0} stroke={c.baseline} />
        <Tooltip cursor={{ fill: c.cursor }} content={tip<T>((d) => ({ title: title(d), rows: tipRows(d) }))} />
        <Bar dataKey={y as string} fill={color} maxBarSize={24} radius={[4, 4, 0, 0]} isAnimationActive={false} />
      </BarChart>
    </ResponsiveContainer>
  );
}

/* Shtyllë 100% (pozitiv | negativ) për tabelat. Pa sfond "track": vetë dy segmentet e mbushin. */
export function SplitBar({ pos, neg, className }: { pos: number; neg: number; className?: string }) {
  const total = pos + neg || 1;
  return (
    <div className={cx("flex h-2 w-full gap-[2px]", className)} role="img" aria-label={`${pct((pos / total) * 100)} pozitive`}>
      {pos > 0 && <span className="bg-pos first:rounded-l-[4px] last:rounded-r-[4px]" style={{ width: `${(pos / total) * 100}%` }} />}
      {neg > 0 && <span className="bg-neg first:rounded-l-[4px] last:rounded-r-[4px]" style={{ width: `${(neg / total) * 100}%` }} />}
    </div>
  );
}

export function KeywordList({ items, tone }: { items: { fjala: string; numri: number }[]; tone: "pos" | "neg" }) {
  const max = Math.max(1, ...items.map((i) => i.numri));
  if (!items.length) return <p className="text-sm text-ink-3">Nuk ka mjaftueshëm të dhëna.</p>;
  return (
    <ul className="grid grid-cols-1 gap-x-6 gap-y-2.5 sm:grid-cols-2">
      {items.map((i) => (
        <li key={i.fjala} className="grid grid-cols-[minmax(0,7.5rem)_1fr_auto] items-center gap-3 text-sm">
          <span className="truncate text-ink">{i.fjala}</span>
          <span className="h-2">
            <span
              className={cx("block h-2 rounded-r-[4px]", tone === "pos" ? "bg-pos" : "bg-neg")}
              style={{ width: `${Math.max(4, (i.numri / max) * 100)}%` }}
            />
          </span>
          <span className="tnum w-10 text-right text-[13px] text-ink-3">{num(i.numri)}</span>
        </li>
      ))}
    </ul>
  );
}

export function DimensionTable({ rows, showRating }: { rows: DimensionRow[]; showRating: boolean }) {
  return (
    <div className="-mx-5 overflow-x-auto md:-mx-6">
      <table className="w-full min-w-[620px] text-left text-sm">
        <thead>
          <tr className="text-[12px] text-ink-3">
            <th className="px-5 py-2 font-medium md:px-6">Emri</th>
            <th className="py-2 text-right font-medium">Komente</th>
            <th className="w-[34%] px-4 py-2 font-medium">Pozitive / negative</th>
            <th className="py-2 text-right font-medium">Kënaqësia</th>
            {showRating && <th className="py-2 pl-4 text-right font-medium">Yje</th>}
            <th className="px-5 py-2 font-medium md:px-6">Ankesa kryesore</th>
          </tr>
        </thead>
        <tbody className="tnum">
          {rows.map((r) => (
            <tr key={r.emri} className="border-t border-line">
              <td className="px-5 py-3 font-medium text-ink md:px-6">{r.emri}</td>
              <td className="py-3 text-right text-ink-2">{num(r.gjithsej)}</td>
              <td className="px-4 py-3">
                <SplitBar pos={r.pozitiv} neg={r.negativ} />
              </td>
              <td className="py-3 text-right font-medium text-ink">{pct(r.perqindja_pozitive)}</td>
              {showRating && <td className="py-3 pl-4 text-right text-ink-2">{r.vleresimi_mesatar?.toFixed(1) ?? "-"}</td>}
              <td className="px-5 py-3 text-ink-2 md:px-6">{r.ankesa_kryesore ?? "-"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
