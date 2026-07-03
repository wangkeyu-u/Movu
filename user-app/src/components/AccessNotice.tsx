import { Alert } from "@movu/ui";
import { useTranslation } from "react-i18next";

import type { AccessIssue } from "../utils/access";
import { StatusPill } from "./StatusPill";

const statusByIssue: Record<AccessIssue, string | boolean> = {
  email_unverified: false,
  pending: "pending",
  rejected: "rejected",
  banned: "banned"
};

export function AccessNotice({ issue }: { issue: AccessIssue }) {
  const { t } = useTranslation();

  return (
    <Alert tone={issue === "pending" ? "warning" : "error"} className="access-notice">
      <div>
        <strong>{t(`access.${issue}.title`)}</strong>
        <p>{t(`access.${issue}.body`)}</p>
      </div>
      <StatusPill value={statusByIssue[issue]} />
    </Alert>
  );
}
