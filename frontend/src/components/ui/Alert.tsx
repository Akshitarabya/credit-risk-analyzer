import { AlertCircle, CheckCircle2 } from "lucide-react";
import type { ReactNode } from "react";

type AlertTone = "error" | "success";

interface AlertProps {
  tone: AlertTone;
  children: ReactNode;
}

export default function Alert({ tone, children }: AlertProps) {
  const isError = tone === "error";
  const Icon = isError ? AlertCircle : CheckCircle2;

  return (
    <div
      role={isError ? "alert" : "status"}
      className={`flex items-start gap-2.5 rounded-xl border px-4 py-3 text-sm font-medium
        ${isError ? "border-coral/30 bg-coral-soft text-coral" : "border-teal/30 bg-teal-soft text-teal"}`}
    >
      <Icon className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
      <span>{children}</span>
    </div>
  );
}
