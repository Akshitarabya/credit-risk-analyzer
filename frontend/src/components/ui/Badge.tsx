import type { ReactNode } from "react";

type BadgeTone = "navy" | "teal" | "amber" | "coral" | "neutral";

interface BadgeProps {
  tone?: BadgeTone;
  children: ReactNode;
}

const toneClasses: Record<BadgeTone, string> = {
  navy: "bg-navy/10 text-navy",
  teal: "bg-teal-soft text-teal",
  amber: "bg-amber-soft text-amber",
  coral: "bg-coral-soft text-coral",
  neutral: "bg-line/60 text-muted",
};

export default function Badge({ tone = "neutral", children }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ${toneClasses[tone]}`}
    >
      {children}
    </span>
  );
}
