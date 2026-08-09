import Badge from "@/components/ui/Badge";
import type { DocumentStatus } from "@/types/document";

const STATUS_CONFIG: Record<
  DocumentStatus,
  { label: string; tone: "navy" | "teal" | "amber" | "coral" | "neutral" }
> = {
  uploaded: { label: "Uploaded", tone: "navy" },
  ocr_failed: { label: "Needs review", tone: "amber" },
  verified: { label: "Verified", tone: "teal" },
  rejected: { label: "Rejected", tone: "coral" },
};

export default function DocumentStatusBadge({
  status,
}: {
  status: DocumentStatus;
}) {
  const config = STATUS_CONFIG[status];
  return <Badge tone={config.tone}>{config.label}</Badge>;
}