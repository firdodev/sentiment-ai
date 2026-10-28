import { useEffect, useRef, useState } from "react";
import { motion } from "motion/react";
import {
  ArrowCounterClockwiseIcon,
  ArrowRightIcon,
  CheckCircleIcon,
  CircleDashedIcon,
  FacebookLogoIcon,
  InfoIcon,
  InstagramLogoIcon,
  KeyIcon,
  LinkSimpleIcon,
  LinkedinLogoIcon,
  TiktokLogoIcon,
  type Icon,
} from "@phosphor-icons/react";
import { getJSON, postJSON, RequestError } from "../lib/api";
import type { ApiError, ParsedLink, Report, SettingsStatus } from "../types";
import { Dashboard } from "../components/Dashboard";
import { DashboardSkeleton } from "./Business";
import { Button, Card, ErrorNote, Field, PageHeader, cx, inputClass } from "../components/ui";

const PLATFORMS: { key: ParsedLink["platforma"]; name: string; icon: Icon; kinds: string; example: string }[] = [
  { key: "instagram", name: "Instagram", icon: InstagramLogoIcon, kinds: "Post, reel, link Shpërndaj", example: "instagram.com/reel/..." },
  { key: "facebook", name: "Facebook", icon: FacebookLogoIcon, kinds: "Postim, video, reel", example: "facebook.com/faqja/posts/..." },
  { key: "linkedin", name: "LinkedIn", icon: LinkedinLogoIcon, kinds: "Postim", example: "linkedin.com/posts/..." },
  { key: "tiktok", name: "TikTok", icon: TiktokLogoIcon, kinds: "Video", example: "tiktok.com/@emri/video/..." },
];
const ICONS = Object.fromEntries(PLATFORMS.map((p) => [p.key, p.icon])) as Record<string, Icon>;
const KIND_LABEL: Record<string, string> = { post: "Post", reel: "Reel", video: "Video", foto: "Foto" };
const KEYS: { key: string; label: string; help: string }[] = [
  { key: "APIFY_TOKEN", label: "Apify API token", help: "Për postime publike në të katër platformat. apify.com, Settings, API & Integrations." },
  { key: "META_ACCESS_TOKEN", label: "Meta access token", help: "Opsionale. API zyrtare për faqen ose llogarinë tuaj." },
  { key: "FB_PAGE_ID", label: "Facebook Page ID", help: "Opsionale, bashkë me token-in e Meta." },
  { key: "IG_USER_ID", label: "Instagram Business ID", help: "Opsionale, bashkë me token-in e Meta." },
];

function Settings({ status, onSaved }: { status: SettingsStatus | null; onSaved: (s: SettingsStatus) => void }) {
  const [values, setValues] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  async function save(clearKey?: string) {
    setSaving(true);
    setMsg(null);
    try {
      const body = clearKey ? { [clearKey]: "" } : Object.fromEntries(Object.entries(values).filter(([, v]) => v.trim()));
      const s = await postJSON<SettingsStatus>("/api/settings", body);
      onSaved(s);
      setValues({});
      setMsg(clearKey ? "Çelësi u hoq." : "U ruajt në skedarin .env të projektit.");
    } catch (e) {
      setMsg((e as RequestError).message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card
      title="Lidhjet"
      description="Çelësat ruhen vetëm në kompjuterin tuaj (skedari .env) dhe nuk i dërgohen kurrë shfletuesit."
    >
      <form
        className="flex flex-col gap-4"
        onSubmit={(e) => {
          e.preventDefault();
          save();
        }}
      >
        {KEYS.map((k) => {
          const set = status?.[k.key]?.vendosur;
          return (
            <Field key={k.key} label={k.label} htmlFor={k.key} help={k.help}>
              <div className="flex gap-2">
                <input
                  id={k.key}
                  type="password"
                  autoComplete="off"
                  spellCheck={false}
                  value={values[k.key] ?? ""}
                  onChange={(e) => setValues((v) => ({ ...v, [k.key]: e.target.value }))}
                  placeholder={set ? "I vendosur. Shkruaj për ta ndryshuar." : "Jo i vendosur"}
                  className={cx(inputClass, "h-10 py-0 text-sm")}
                />
                {set && (
                  <Button type="button" variant="ghost" size="sm" className="h-10" onClick={() => save(k.key)} disabled={saving}>
                    Hiq
                  </Button>
                )}
              </div>
            </Field>
          );
        })}
        <div className="flex flex-wrap items-center gap-3">
          <Button type="submit" icon={KeyIcon} loading={saving} disabled={!Object.values(values).some((v) => v.trim())}>Ruaj çelësat</Button>
          {msg && <span className="text-[13px] text-ink-3">{msg}</span>}
        </div>
      </form>
    </Card>
  );
}

export default function Social() {
  const [url, setUrl] = useState("");
  const [limit, setLimit] = useState(200);
  const [parsed, setParsed] = useState<ParsedLink | null>(null);
  const [parseError, setParseError] = useState<string | null>(null);
  const [status, setStatus] = useState<SettingsStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const [report, setReport] = useState<Report | null>(null);
  const settingsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getJSON<SettingsStatus>("/api/settings").then(setStatus).catch(() => setStatus(null));
  }, []);

  // Njohja e platformës gjatë shkrimit
  useEffect(() => {
    setParseError(null);
    if (!url.trim()) {
      setParsed(null);
      return;
    }
    const t = setTimeout(() => {
      postJSON<ParsedLink>("/api/social/parse", { url })
        .then(setParsed)
        .catch((e: RequestError) => {
          setParsed(null);
          setParseError(e.message);
        });
    }, 350);
    return () => clearTimeout(t);
  }, [url, status]);

  async function fetchComments() {
    if (!url.trim()) {
      setParseError("Ngjit linkun e postimit.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      setReport(await postJSON<Report>("/api/social/fetch", { url, limit }));
    } catch (e) {
      setError((e as RequestError).detail);
    } finally {
      setLoading(false);
    }
  }

  const DetectedIcon = parsed ? ICONS[parsed.platforma] : LinkSimpleIcon;
  const connected = !!status?.APIFY_TOKEN?.vendosur || !!status?.META_ACCESS_TOKEN?.vendosur;

  return (
    <>
      <PageHeader
        title="Komentet e një postimi"
        text="Ngjit linkun e një postimi në Instagram, Facebook, LinkedIn ose TikTok. Komentet lexohen dhe analizohen automatikisht."
        actions={report && !loading && (
          <Button variant="secondary" icon={ArrowCounterClockwiseIcon} onClick={() => setReport(null)}>Postim tjetër</Button>
        )}
      />

      {loading ? (
        <div className="flex flex-col gap-4">
          <p className="text-sm text-ink-2">Duke lexuar komentet. Përmes Apify zakonisht zgjat 20 deri 90 sekonda.</p>
          <DashboardSkeleton />
        </div>
      ) : report ? (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.3 }}>
          {report.burimi.shenim && (
            <p className="mb-5 flex items-start gap-2.5 rounded-[12px] border border-line bg-sunken px-4 py-3 text-sm text-ink-2">
              <InfoIcon size={18} weight="fill" className="mt-0.5 shrink-0 text-ink-3" />
              {report.burimi.shenim}
            </p>
          )}
          <Dashboard report={report} />
        </motion.div>
      ) : (
        <div className="grid grid-cols-1 items-start gap-5 lg:grid-cols-[1.35fr_1fr]">
          <div className="flex flex-col gap-5">
            <Card>
              <form
                className="flex flex-col gap-5"
                onSubmit={(e) => {
                  e.preventDefault();
                  fetchComments();
                }}
              >
                <Field
                  label="Linku i postimit"
                  htmlFor="link"
                  error={parseError}
                  help={parsed ? (
                    <span className="inline-flex items-center gap-1.5 text-ink-2">
                      <DetectedIcon size={16} weight="fill" />
                      <span>
                        {parsed.emri}, {KIND_LABEL[parsed.lloji] ?? parsed.lloji}
                        {parsed.burimet.length === 0 && <span className="text-ink-3">. Nevojitet një lidhje (shiko panelin “Lidhjet”).</span>}
                      </span>
                    </span>
                  ) : "P.sh. https://www.instagram.com/reel/..."}
                >
                  <div className="relative">
                    <DetectedIcon size={18} className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-ink-3" />
                    <input
                      id="link"
                      type="url"
                      inputMode="url"
                      value={url}
                      onChange={(e) => setUrl(e.target.value)}
                      placeholder="https://"
                      className={cx(inputClass, "pl-10")}
                    />
                  </div>
                </Field>
                <div className="flex flex-wrap items-end justify-between gap-4">
                  <Field label="Sa komente" htmlFor="limit">
                    <select id="limit" value={limit} onChange={(e) => setLimit(Number(e.target.value))} className={cx(inputClass, "h-10 w-40 py-0 text-sm")}>
                      {[50, 100, 200, 500, 1000].map((n) => <option key={n} value={n}>Deri në {n}</option>)}
                    </select>
                  </Field>
                  <Button type="submit" icon={ArrowRightIcon} disabled={!url.trim()}>Lexo komentet</Button>
                </div>
              </form>
              {error && (
                <div className="mt-5">
                  <ErrorNote message={error.gabim}>
                    {error.ndihme && (
                      <ol className="mt-2 list-decimal space-y-1 pl-5 text-ink-2">
                        {error.ndihme.map((h) => <li key={h}>{h}</li>)}
                      </ol>
                    )}
                    {error.kodi === "pa_konfigurim" && (
                      <Button variant="secondary" size="sm" className="mt-3" icon={KeyIcon}
                        onClick={() => {
                          settingsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
                          document.getElementById("APIFY_TOKEN")?.focus({ preventScroll: true });
                        }}>
                        Vendos çelësin
                      </Button>
                    )}
                  </ErrorNote>
                </div>
              )}
            </Card>

            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              {PLATFORMS.map((p) => {
                const active = parsed?.platforma === p.key;
                return (
                  <div key={p.key} className={cx("flex items-center gap-3 rounded-[12px] border bg-surface p-4 transition-colors", active ? "border-ink" : "border-line")}>
                    <p.icon size={26} weight={active ? "fill" : "regular"} className="shrink-0 text-ink" />
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-ink">{p.name}</p>
                      <p className="truncate text-[13px] text-ink-3">{p.kinds}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div ref={settingsRef} className="flex scroll-mt-6 flex-col gap-5">
            <div className={cx("flex items-start gap-3 rounded-[12px] border border-line p-4 text-sm", connected ? "bg-surface" : "bg-sunken")}>
              {connected ? (
                <CheckCircleIcon size={20} weight="fill" className="mt-0.5 shrink-0 text-good" />
              ) : (
                <CircleDashedIcon size={20} className="mt-0.5 shrink-0 text-ink-3" />
              )}
              <p className="text-ink-2">
                {connected
                  ? "Lidhja është gati. Mund të lexosh komentet e postimeve publike."
                  : "Ende pa lidhje. Vendos një token Apify (ka plan falas) që të lexosh komentet e postimeve publike."}
              </p>
            </div>
            <Settings status={status} onSaved={setStatus} />
          </div>
        </div>
      )}
    </>
  );
}
