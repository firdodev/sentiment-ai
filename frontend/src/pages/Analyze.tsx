import { useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import {
  ArrowRightIcon,
  ChatTextIcon,
  CheckIcon,
  CopyIcon,
  RobotIcon,
  ThumbsDownIcon,
  ThumbsUpIcon,
} from "@phosphor-icons/react";
import { postJSON, RequestError } from "../lib/api";
import { pct } from "../lib/format";
import { useTheme } from "../lib/theme";
import type { Prediction } from "../types";
import { Legend, SplitBar } from "../components/charts";
import { Button, Card, Chip, EmptyState, ErrorNote, Field, PageHeader, SentimentTag, Skeleton, cx, inputClass } from "../components/ui";

const EXAMPLES = [
  "Stafi shumë i sjellshëm, do kthehem prapë!",
  "Porosia vonoi dy orë dhe erdhi e ftohtë",
  "Nuk kisha asnjë problem, gjithçka në rregull",
  "Aplikacioni bllokohet sa herë paguaj me kartë",
];

export default function Analyze() {
  const { c } = useTheme();
  const [text, setText] = useState("");
  const [useLlm, setUseLlm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<Prediction | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  async function analyze(value = text) {
    if (!value.trim()) {
      setError("Shkruaj një koment për ta analizuar.");
      return;
    }
    setLoading(true);
    setError(null);
    setFeedback(null);
    try {
      setResult(await postJSON<Prediction>("/api/predict", { text: value, llm: useLlm }));
    } catch (e) {
      setError((e as RequestError).message);
    } finally {
      setLoading(false);
    }
  }

  async function sendFeedback(label: "pozitiv" | "negativ") {
    if (!result) return;
    try {
      const r = await postJSON<{ mesazhi: string }>("/api/feedback", { text: result.teksti, sentimenti: label });
      setFeedback(r.mesazhi);
    } catch (e) {
      setFeedback((e as RequestError).message);
    }
  }

  async function copyReply() {
    if (!result) return;
    try {
      await navigator.clipboard.writeText(result.asistenti.pergjigja);
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    } catch {
      setCopied(false);
    }
  }

  const p = result?.probabilitetet ?? {};

  return (
    <>
      <PageHeader
        title="Testo një koment"
        text="Shkruaj ose ngjit një koment në shqip. Modeli tregon nëse është pozitiv apo negativ, pse, dhe si t'i përgjigjesh."
      />
      <div className="grid grid-cols-1 items-start gap-5 lg:grid-cols-[1fr_1.1fr]">
        <Card>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              analyze();
            }}
            className="flex flex-col gap-5"
          >
            <Field label="Komenti" htmlFor="koment" help="Ctrl + Enter për ta analizuar shpejt." error={error}>
              <textarea
                id="koment"
                value={text}
                onChange={(e) => setText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) analyze();
                }}
                rows={6}
                maxLength={5000}
                placeholder="P.sh. Dërgesa erdhi shpejt dhe pica ishte e nxehtë"
                className={cx(inputClass, "resize-y leading-relaxed")}
              />
            </Field>
            <div>
              <p className="mb-2 text-[13px] text-ink-3">Ose provo një shembull:</p>
              <div className="flex flex-wrap gap-2">
                {EXAMPLES.map((ex) => (
                  <button
                    key={ex}
                    type="button"
                    onClick={() => {
                      setText(ex);
                      analyze(ex);
                    }}
                    className="rounded-full border border-line bg-page px-3 py-1.5 text-left text-[13px] text-ink-2 transition-colors hover:border-line-2 hover:text-ink active:scale-[0.98]"
                  >
                    {ex}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex flex-wrap items-center justify-between gap-3 border-t border-line pt-5">
              <label className="inline-flex cursor-pointer items-center gap-2.5 text-sm text-ink-2">
                <input type="checkbox" checked={useLlm} onChange={(e) => setUseLlm(e.target.checked)} className="h-4 w-4 accent-[var(--ink)]" />
                Përgjigje me LLM lokal (Ollama)
              </label>
              <Button type="submit" icon={ArrowRightIcon} loading={loading}>Analizo</Button>
            </div>
          </form>
        </Card>

        <div aria-live="polite">
          <AnimatePresence mode="wait">
            {loading && !result ? (
              <motion.div key="sk" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <Card>
                  <Skeleton className="h-8 w-40" />
                  <Skeleton className="mt-5 h-2.5 w-full" />
                  <Skeleton className="mt-6 h-4 w-3/4" />
                  <Skeleton className="mt-2 h-4 w-1/2" />
                  <Skeleton className="mt-6 h-20 w-full" />
                </Card>
              </motion.div>
            ) : result ? (
              <motion.div
                key={result.teksti}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
                className={cx("flex flex-col gap-5", loading && "opacity-60")}
              >
                <Card>
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <p className="text-sm text-ink-3">Rezultati</p>
                      <p className="mt-1 text-[34px] font-semibold capitalize leading-none tracking-tight text-ink">{result.sentimenti}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-ink-3">Siguria e modelit</p>
                      <p className="tnum mt-1 text-[22px] font-semibold text-ink">{pct(result.besueshmeria * 100)}</p>
                    </div>
                  </div>
                  <SplitBar pos={p.pozitiv ?? 0} neg={p.negativ ?? 0} className="mt-5 h-2.5" />
                  <div className="mt-2.5 flex justify-between">
                    <Legend items={[{ label: `Pozitiv ${pct((p.pozitiv ?? 0) * 100)}`, color: c.pos }]} />
                    <Legend items={[{ label: `Negativ ${pct((p.negativ ?? 0) * 100)}`, color: c.neg }]} />
                  </div>
                  {result.i_pasigurt && (
                    <p className="mt-4 rounded-[10px] bg-sunken px-3 py-2 text-sm text-ink-2">
                      Modeli nuk është shumë i sigurt. Ky koment mund të jetë neutral ose i përzier.
                    </p>
                  )}

                  {result.fjalet_kyce.length > 0 && (
                    <div className="mt-6">
                      <p className="mb-2 text-sm font-medium text-ink">Fjalët që vendosën</p>
                      <div className="flex flex-wrap gap-2">
                        {result.fjalet_kyce.map((k) => (
                          <span key={k.fjala} className={cx("inline-flex items-center gap-2 rounded-full px-3 py-1 text-[13px] text-ink", k.ndikimi > 0 ? "bg-pos-soft" : "bg-neg-soft")}>
                            {k.fjala}
                            <span className="tnum text-ink-3">{k.ndikimi > 0 ? "+" : "−"}{Math.abs(k.ndikimi).toFixed(2)}</span>
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  {result.aspektet.length > 0 && (
                    <div className="mt-5">
                      <p className="mb-2 text-sm font-medium text-ink">Tema</p>
                      <div className="flex flex-wrap gap-2">{result.aspektet.map((a) => <Chip key={a}>{a}</Chip>)}</div>
                    </div>
                  )}
                </Card>

                <Card title="Asistenti" description={`${result.asistenti.prioriteti === "i ulët" ? "Prioritet i ulët" : `Prioritet ${result.asistenti.prioriteti}`}. ${result.asistenti.veprimi}.`}>
                  <div className="rounded-[12px] bg-sunken p-4">
                    <p className="text-[15px] leading-relaxed text-ink">{result.asistenti.pergjigja}</p>
                    <div className="mt-3 flex items-center justify-between gap-3">
                      <span className="inline-flex items-center gap-1.5 text-[12px] text-ink-3">
                        <RobotIcon size={14} /> {result.asistenti.burimi === "shabllon" ? "Përgjigje nga shablloni" : result.asistenti.burimi}
                      </span>
                      <Button variant="ghost" size="sm" icon={copied ? CheckIcon : CopyIcon} onClick={copyReply}>{copied ? "U kopjua" : "Kopjo"}</Button>
                    </div>
                  </div>
                  {"llm_sentimenti" in result && (
                    <p className="mt-3 text-[13px] text-ink-3">Mendimi i LLM: {result.llm_sentimenti ?? "LLM lokal nuk është i ndezur"}</p>
                  )}
                  <div className="mt-5 flex flex-wrap items-center gap-2 border-t border-line pt-4">
                    <span className="mr-1 text-sm text-ink-2">A gaboi modeli? Vendose ti:</span>
                    <Button variant="secondary" size="sm" icon={ThumbsUpIcon} onClick={() => sendFeedback("pozitiv")}>Pozitiv</Button>
                    <Button variant="secondary" size="sm" icon={ThumbsDownIcon} onClick={() => sendFeedback("negativ")}>Negativ</Button>
                    {feedback && <span className="text-[13px] text-ink-3">{feedback}</span>}
                  </div>
                </Card>
              </motion.div>
            ) : error && !result ? (
              <motion.div key="err" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                <ErrorNote message={error} />
              </motion.div>
            ) : (
              <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <Card>
                  <EmptyState
                    icon={ChatTextIcon}
                    title="Rezultati shfaqet këtu"
                    text="Do shohësh sentimentin, sigurinë e modelit, fjalët që ndikuan dhe një përgjigje të gatshme për klientin."
                  />
                  <div className="mt-6 flex flex-wrap gap-2">
                    <SentimentTag s="pozitiv" />
                    <SentimentTag s="negativ" />
                  </div>
                </Card>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </>
  );
}
