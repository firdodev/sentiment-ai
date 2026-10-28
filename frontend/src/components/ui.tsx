import type { ButtonHTMLAttributes, ReactNode } from "react";
import {
  CheckCircleIcon,
  CircleNotchIcon,
  InfoIcon,
  WarningIcon,
  WarningOctagonIcon,
  type Icon,
} from "@phosphor-icons/react";
import type { InsightKind, Sentiment } from "../types";

/* Rregulli i formave: kontejnerët 14px, kontrollet 10px, etiketat të plota (pill). */

export function cx(...parts: (string | false | null | undefined)[]) {
  return parts.filter(Boolean).join(" ");
}

export function Card({
  title,
  description,
  actions,
  children,
  className,
  bodyClassName,
}: {
  title?: ReactNode;
  description?: ReactNode;
  actions?: ReactNode;
  children?: ReactNode;
  className?: string;
  bodyClassName?: string;
}) {
  return (
    <section
      className={cx(
        "break-avoid rounded-[14px] border border-line bg-surface shadow-card",
        className,
      )}
    >
      {(title || actions) && (
        <header className="flex flex-wrap items-start justify-between gap-3 px-5 pt-5 md:px-6">
          <div className="min-w-0">
            {title && <h2 className="text-[15px] font-semibold tracking-tight text-ink">{title}</h2>}
            {description && <p className="mt-1 max-w-[65ch] text-sm text-ink-3">{description}</p>}
          </div>
          {actions && <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div>}
        </header>
      )}
      <div className={cx("p-5 md:p-6", (title || actions) ? "pt-4 md:pt-4" : null, bodyClassName)}>
        {children}
      </div>
    </section>
  );
}

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost";
  icon?: Icon;
  loading?: boolean;
  size?: "md" | "sm";
};

export function Button({
  variant = "primary",
  icon: IconCmp,
  loading,
  size = "md",
  className,
  children,
  disabled,
  ...rest
}: ButtonProps) {
  return (
    <button
      {...rest}
      disabled={disabled || loading}
      className={cx(
        "inline-flex select-none items-center justify-center gap-2 whitespace-nowrap rounded-[10px] font-medium",
        "transition-[transform,background-color,border-color,opacity] duration-150 active:scale-[0.98] disabled:opacity-50 disabled:active:scale-100",
        size === "md" ? "h-10 px-4 text-sm" : "h-8 px-3 text-[13px]",
        variant === "primary" && "bg-btn text-btn-ink hover:opacity-90",
        variant === "secondary" && "border border-line bg-surface text-ink hover:border-line-2 hover:bg-sunken",
        variant === "ghost" && "text-ink-2 hover:bg-sunken hover:text-ink",
        className,
      )}
    >
      {loading ? (
        <CircleNotchIcon size={16} weight="bold" className="animate-spin motion-reduce:animate-none" />
      ) : (
        IconCmp && <IconCmp size={16} weight="bold" />
      )}
      {children}
    </button>
  );
}

export function Segmented<T extends string>({
  options,
  value,
  onChange,
  label,
}: {
  options: { value: T; label: string }[];
  value: T;
  onChange: (v: T) => void;
  label: string;
}) {
  return (
    <div role="tablist" aria-label={label} className="inline-flex max-w-full overflow-x-auto rounded-[10px] bg-sunken p-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
      {options.map((o) => (
        <button
          key={o.value}
          role="tab"
          aria-selected={value === o.value}
          onClick={() => onChange(o.value)}
          className={cx(
            "h-8 shrink-0 rounded-[8px] px-3 text-[13px] font-medium transition-colors",
            value === o.value ? "bg-surface text-ink shadow-card" : "text-ink-3 hover:text-ink",
          )}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}

export function Field({
  label,
  htmlFor,
  help,
  error,
  children,
}: {
  label: string;
  htmlFor: string;
  help?: ReactNode;
  error?: string | null;
  children: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-2">
      <label htmlFor={htmlFor} className="text-sm font-medium text-ink">
        {label}
      </label>
      {children}
      {help && !error && <p className="text-[13px] text-ink-3">{help}</p>}
      {error && (
        <p role="alert" className="text-[13px] font-medium text-critical">
          {error}
        </p>
      )}
    </div>
  );
}

export const inputClass =
  "w-full rounded-[10px] border border-line bg-page px-3.5 py-2.5 text-[15px] text-ink placeholder:text-ink-3 " +
  "transition-colors hover:border-line-2 focus:border-ink focus:outline-none";

const STATUS: Record<InsightKind, { icon: Icon; label: string; color: string }> = {
  good: { icon: CheckCircleIcon, label: "Mirë", color: "text-good" },
  warning: { icon: WarningIcon, label: "Kujdes", color: "text-warning" },
  critical: { icon: WarningOctagonIcon, label: "Kritike", color: "text-critical" },
  info: { icon: InfoIcon, label: "Info", color: "text-ink-3" },
};

export function StatusLabel({ kind }: { kind: InsightKind }) {
  const s = STATUS[kind];
  const IconCmp = s.icon;
  return (
    <span className="inline-flex items-center gap-1.5 text-[12px] font-medium text-ink-2">
      <IconCmp size={16} weight="fill" className={s.color} aria-hidden />
      {s.label}
    </span>
  );
}

export function StatusIcon({ kind, size = 20 }: { kind: InsightKind; size?: number }) {
  const s = STATUS[kind];
  const IconCmp = s.icon;
  return <IconCmp size={size} weight="fill" className={s.color} aria-label={s.label} />;
}

export function SentimentTag({ s, className }: { s: Sentiment; className?: string }) {
  const label = s === "pozitiv" ? "Pozitiv" : s === "negativ" ? "Negativ" : "I panjohur";
  return (
    <span
      className={cx(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[12px] font-medium text-ink",
        s === "pozitiv" ? "bg-pos-soft" : s === "negativ" ? "bg-neg-soft" : "bg-sunken",
        className,
      )}
    >
      <span
        aria-hidden
        className={cx("h-2 w-2 rounded-[2px]", s === "pozitiv" ? "bg-pos" : s === "negativ" ? "bg-neg" : "bg-neutral")}
      />
      {label}
    </span>
  );
}

export function Chip({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <span className={cx("inline-flex items-center gap-1 rounded-full border border-line px-2.5 py-0.5 text-[12px] text-ink-2", className)}>
      {children}
    </span>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return <div aria-hidden className={cx("skeleton", className)} />;
}

export function EmptyState({
  icon: IconCmp,
  title,
  text,
  children,
}: {
  icon: Icon;
  title: string;
  text: ReactNode;
  children?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-start gap-3 py-2">
      <span className="grid h-11 w-11 place-items-center rounded-[12px] bg-sunken text-ink-2">
        <IconCmp size={22} weight="duotone" />
      </span>
      <div>
        <p className="font-medium text-ink">{title}</p>
        <p className="mt-1 max-w-[52ch] text-sm text-ink-3">{text}</p>
      </div>
      {children}
    </div>
  );
}

export function ErrorNote({ message, children }: { message: string; children?: ReactNode }) {
  return (
    <div role="alert" className="flex gap-3 rounded-[12px] border border-line bg-neg-soft/60 p-4">
      <WarningOctagonIcon size={20} weight="fill" className="mt-0.5 shrink-0 text-critical" />
      <div className="min-w-0 text-sm">
        <p className="font-medium text-ink">{message}</p>
        {children}
      </div>
    </div>
  );
}

export function PageHeader({ title, text, actions }: { title: string; text: string; actions?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-col gap-4 md:mb-8 md:flex-row md:items-end md:justify-between">
      <div>
        <h1 className="text-[26px] font-semibold leading-tight tracking-tight text-ink md:text-[30px]">{title}</h1>
        <p className="mt-2 max-w-[62ch] text-[15px] leading-relaxed text-ink-3">{text}</p>
      </div>
      {actions && <div className="no-print flex flex-wrap gap-2">{actions}</div>}
    </div>
  );
}
