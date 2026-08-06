import Badge from "@/components/ui/Badge";
import type { LoanStatus } from "@/types/loan";

const statusConfig: Record<LoanStatus, { label: string; tone: "navy" | "teal" | "amber" | "coral" | "neutral" }> = {
  submitted: { label: "Submitted", tone: "navy" },
  scored: { label: "Scored", tone: "amber" },
  manual_review: { label: "In review", tone: "amber" },
  approved: { label: "Approved", tone: "teal" },
  rejected: { label: "Rejected", tone: "coral" },
};

export default function LoanStatusBadge({ status }: { status: LoanStatus }) {
  const config = statusConfig[status];
  return <Badge tone={config.tone}>{config.label}</Badge>;
}