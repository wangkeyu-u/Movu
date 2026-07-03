import { Badge, type BadgeTone } from "@movu/ui";
import { useTranslation } from "react-i18next";

import { statusKey } from "../utils/format";

const toneMap: Record<string, BadgeTone> = {
  approved: "positive",
  completed: "positive",
  resolved: "positive",
  confirmed: "positive",
  true: "positive",
  rejected: "negative",
  banned: "negative",
  cancelled: "negative",
  false: "warning",
  pending: "warning",
  reviewing: "warning",
  ongoing: "info",
  matched: "info",
  posted: "neutral",
  recommended: "neutral",
  full: "neutral"
};

export function StatusPill({ value }: { value: string | boolean }) {
  const key = String(value);
  const { t } = useTranslation();
  return <Badge tone={toneMap[key] ?? "neutral"}>{t(`status.${statusKey(value)}`, { defaultValue: key })}</Badge>;
}
