import { Badge, type BadgeTone } from "@movu/ui";
import { useTranslation } from "react-i18next";

const toneMap: Record<string, BadgeTone> = {
  approved: "positive",
  paid: "positive",
  completed: "positive",
  resolved: "positive",
  confirmed: "positive",
  rejected: "negative",
  failed: "negative",
  cancelled: "negative",
  new: "negative",
  false_alarm: "neutral",
  pending: "warning",
  reviewing: "warning",
  ongoing: "info",
  matched: "info",
  posted: "neutral",
  recommended: "neutral",
  full: "neutral",
  refunded: "neutral"
};

export function StatusBadge({ value }: { value: string | boolean }) {
  const { t } = useTranslation();
  const key = String(value);
  const tone = toneMap[key] || "neutral";
  return <Badge tone={tone}>{t(`status.${key}`)}</Badge>;
}
