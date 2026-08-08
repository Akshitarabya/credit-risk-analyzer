import Badge from "@/components/ui/Badge";
import type { RiskCategory } from "@/types/loan";

const RISK_CONFIG: Record<RiskCategory, { label: string; tone: "teal" | "amber" | "coral" }> = {
  low: { label: "Low", tone: "teal" },
  medium: { label: "Medium", tone: "amber" },
  high: { label: "High", tone: "coral" },
};

export default function RiskCategoryBadge({ category }: { category: RiskCategory | null }) {
  if (category === null) {
    return <Badge tone="neutral">—</Badge>;
  }
  const config = RISK_CONFIG[category];
  return <Badge tone={config.tone}>{config.label}</Badge>;
}