import { useEffect, useState } from "react";
import { ArrowsClockwiseIcon } from "@phosphor-icons/react";
import { getJSON, postJSON, RequestError } from "../lib/api";
import { num, pct, shortDate } from "../lib/format";
import type { ModelInfo } from "../types";
import { Button, Card, ErrorNote, PageHeader, SentimentTag, Skeleton } from "../components/ui";

const LABELS = ["negativ", "pozitiv"] as const;
const RAMP = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95"]; // sekuenciale blu

function Confusion({ m }: { m: number[][] }) {
  const max = Math.max(1, ...m.flat());
  return (
    <div className="grid grid-cols-[auto_1fr_1fr] gap-[2px] text-sm">
      <span />
      {LABELS.map((l) => <span key={l} className="pb-2 text-center text-[12px] text-ink-3">parashikuar {l}</span>)}
      {m.map((row, i) => (
        <div key={i} className="contents">
          <span className="flex items-center pr-3 text-[12px] text-ink-3">e vërtetë {LABELS[i]}</span>
          {row.map((v, j) => {
            const step = Math.min(RAMP.length - 1, Math.round((v / max) * (RAMP.length - 1)));
            return (
              <div key={j} className="tnum grid h-20 place-items-center rounded-[6px] text-[20px] font-semibold"
                style={{ background: RAMP[step], color: step >= 3 ? "#ffffff" : "#0b0b0b" }}>
                {num(v)}
              </div>
            );
          })}
        </div>
      ))}
    </div>
  );
}

export default function Model() {
  const [info, setInfo] = useState<ModelInfo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [stamp, setStamp] = useState(Date.now());

  const load = () => getJSON<ModelInfo>("/api/model").then(setInfo).catch((e: RequestError) => setError(e.message));
  useEffect(() => {
    load();
  }, []);

  async function retrain() {
    setBusy(true);
    setMsg(null);
    try {
      const r = await postJSON<{ modeli: string; test_real_accuracy?: number }>("/api/retrain");
      setMsg(`U ritrajnua. Saktësia në komentet reale: ${pct((r.test_real_accuracy ?? 0) * 100)}.`);
      await load();
      setStamp(Date.now());
    } catch (e) {
      setMsg((e as RequestError).message);
    } finally {
      setBusy(false);
    }
  }

  if (error) return <ErrorNote message={error} />;

  return (
    <>
      <PageHeader
        title="Modeli"
        text="Si është trajnuar modeli dhe sa i saktë është. Korrigjimet që bën te “Testo një koment” përdoren në ritrajnim."
        actions={<Button variant="secondary" icon={ArrowsClockwiseIcon} loading={busy} onClick={retrain}>Ritrajno modelin</Button>}
      />
      {msg && <p className="-mt-3 mb-5 text-sm text-ink-2">{msg}</p>}
      {!info ? (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">{[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-28 rounded-[14px]" />)}</div>
      ) : (
        <div className="flex flex-col gap-5">
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            {[
              ["Algoritmi", info.modeli, `Trajnuar ${shortDate(info.data)}`],
              ["Komente trajnimi", num(info.madhesia_dataset), `${num(info.train)} trajnim, ${num(info.test)} test`],
              ["Saktësia në test", pct(info.test_accuracy * 100), "Pjesa 20% e datasetit"],
              ["Saktësia në komente reale", info.test_real_accuracy != null ? pct(info.test_real_accuracy * 100) : "-", "Komente të shkruara me dorë"],
            ].map(([label, value, sub]) => (
              <Card key={label}>
                <p className="text-[13px] text-ink-3">{label}</p>
                <p className="mt-1 truncate text-[24px] font-semibold tracking-tight text-ink">{value}</p>
                <p className="mt-1.5 text-[12px] text-ink-3">{sub}</p>
              </Card>
            ))}
          </div>

          <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
            <Card title="Krahasimi i algoritmeve" description="F1 mesatar me 5-fold cross-validation. Fiton më i miri dhe ruhet si modeli aktiv.">
              <ol className="flex flex-col divide-y divide-line">
                {Object.entries(info.cv_f1)
                  .sort((a, b) => b[1] - a[1])
                  .map(([name, f1], i) => (
                    <li key={name} className="flex items-center justify-between gap-3 py-3 first:pt-0 last:pb-0">
                      <span className="flex items-center gap-3">
                        <span className="tnum grid h-7 w-7 place-items-center rounded-full bg-sunken text-[13px] font-semibold text-ink">{i + 1}</span>
                        <span className="font-medium text-ink">{name}</span>
                        {name === info.modeli && <span className="rounded-full bg-btn px-2 py-0.5 text-[11px] font-medium text-btn-ink">aktiv</span>}
                      </span>
                      <span className="tnum text-[17px] font-semibold text-ink">{(f1 * 100).toFixed(2)}%</span>
                    </li>
                  ))}
              </ol>
            </Card>
            <Card title="Matrica e konfuzionit" description="Sa komente u klasifikuan saktë në test set.">
              <Confusion m={info.matrica_konfuzionit} />
            </Card>
          </div>

          <Card
            title="Gabimet në komentet reale"
            description="Komentet e shkruara me dorë që modeli i klasifikoi gabim. Këto tregojnë ku duhen më shumë të dhëna."
          >
            {info.test_real_gabime?.length ? (
              <ul className="flex flex-col divide-y divide-line">
                {info.test_real_gabime.map((g) => (
                  <li key={g.koment} className="flex flex-col gap-2 py-3 first:pt-0 last:pb-0 sm:flex-row sm:items-center sm:justify-between">
                    <span className="text-ink">{g.koment}</span>
                    <span className="flex shrink-0 items-center gap-2 text-[13px] text-ink-3">
                      tha <SentimentTag s={g.parashikuar as "pozitiv"} /> duhej <SentimentTag s={g.e_verteta as "pozitiv"} />
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-ink-3">Asnjë gabim në komentet reale.</p>
            )}
          </Card>

          <Card title="Të dhënat e trajnimit" description="Grafikë të gjeneruar me matplotlib gjatë trajnimit.">
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {[
                ["shperndarja.png", "Shpërndarja e komenteve pozitive dhe negative"],
                ["gjatesia.png", "Gjatësia e komenteve sipas klasës"],
                ["fjalet_kryesore.png", "Fjalët më të shpeshta në secilën klasë"],
              ].map(([f, alt], i) => (
                <img key={f} src={`/reports/${f}?t=${stamp}`} alt={alt} loading="lazy"
                  className={`w-full rounded-[10px] border border-line bg-white ${i === 2 ? "md:col-span-2" : ""}`} />
              ))}
            </div>
          </Card>
        </div>
      )}
    </>
  );
}
