import type { ReactNode } from "react";

import LedgerlineMark from "@/components/ui/LedgerlineMark";

interface AuthLayoutProps {
  eyebrow: string;
  title: string;
  subtitle: string;
  children: ReactNode;
}

/**
 * Split-screen layout shared by Login and Register: a brand/narrative panel
 * on the left (hidden on small screens to keep mobile focused on the form),
 * and the form itself on the right.
 */
export default function AuthLayout({ eyebrow, title, subtitle, children }: AuthLayoutProps) {
  return (
    <div className="flex min-h-screen">
      <aside className="relative hidden w-1/2 flex-col justify-between overflow-hidden bg-navy px-12 py-10 text-white lg:flex">
        <div className="flex items-center gap-2.5">
          <LedgerlineMark className="h-5 w-16 text-white" />
          <span className="font-display text-lg font-semibold tracking-tight">Ledgerline</span>
        </div>

        <div className="max-w-md">
          <p className="mb-3 text-xs font-semibold uppercase tracking-[0.2em] text-teal">
            {eyebrow}
          </p>
          <h1 className="font-display text-4xl font-semibold leading-[1.15] tracking-tight">
            {title}
          </h1>
          <p className="mt-4 text-base leading-relaxed text-white/70">{subtitle}</p>
        </div>

        <div className="flex items-center gap-8 text-sm text-white/50">
          <div>
            <p className="font-display text-2xl font-semibold text-white">ML</p>
            <p>risk scoring</p>
          </div>
          <div className="h-8 w-px bg-white/15" />
          <div>
            <p className="font-display text-2xl font-semibold text-white">SHAP</p>
            <p>explainability</p>
          </div>
          <div className="h-8 w-px bg-white/15" />
          <div>
            <p className="font-display text-2xl font-semibold text-white">AI</p>
            <p>plain-English reasons</p>
          </div>
        </div>

        {/* Large decorative ledgerline mark, purely atmospheric */}
        <LedgerlineMark className="pointer-events-none absolute -bottom-10 -right-10 h-40 w-96 text-white/[0.06]" />
      </aside>

      <div className="flex w-full items-center justify-center px-6 py-12 lg:w-1/2">
        <div className="w-full max-w-sm">
          <div className="mb-8 lg:hidden">
            <div className="flex items-center gap-2.5 text-navy">
              <LedgerlineMark className="h-5 w-16" />
              <span className="font-display text-lg font-semibold tracking-tight">Ledgerline</span>
            </div>
          </div>
          {children}
        </div>
      </div>
    </div>
  );
}
