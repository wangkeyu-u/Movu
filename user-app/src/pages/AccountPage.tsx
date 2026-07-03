import { Button, Card } from "@movu/ui";
import { MailCheck, RefreshCw } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { api } from "../api/client";
import { StatusPill } from "../components/StatusPill";
import { Toast } from "../components/Toast";
import { useAuth } from "../routes/AuthProvider";

export function AccountPage() {
  const { user, refresh, logout } = useAuth();
  const { t } = useTranslation();
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function resend() {
    if (!user) return;
    setError(null);
    setMessage(null);
    try {
      const response = await api.resendVerification(user.email);
      setMessage(response.message);
    } catch (err) {
      setError(err instanceof Error ? err.message : t("accountPage.resendFailed"));
    }
  }

  return (
    <div className="page-stack">
      <Card className="account-card">
        <div className="avatar">{user?.name.slice(0, 1)}</div>
        <div>
          <h1>{user?.name}</h1>
          <p>{user?.email}</p>
        </div>
      </Card>

      <Card className="records-panel">
        <div className="panel-title">
          <h2>{t("accountPage.trustStatus")}</h2>
          <Button variant="icon" type="button" onClick={refresh} aria-label={t("common.refreshAccount")}>
            <RefreshCw size={17} aria-hidden="true" />
          </Button>
        </div>
        <div className="settings-list">
          <div>
            <span>{t("common.emailVerified")}</span>
            <StatusPill value={Boolean(user?.email_verified)} />
          </div>
          <div>
            <span>{t("common.accountVerification")}</span>
            <StatusPill value={user?.verification_status ?? "pending"} />
          </div>
          <div>
            <span>{t("common.role")}</span>
            <strong>{t(`roles.${user?.role}`, { defaultValue: user?.role })}</strong>
          </div>
          <div>
            <span>{t("common.rating")}</span>
            <strong>{user?.rating.toFixed(1)}</strong>
          </div>
        </div>
        {!user?.email_verified && (
          <Button variant="secondary" type="button" onClick={resend}>
            <MailCheck size={17} aria-hidden="true" />
            {t("accountPage.resendVerification")}
          </Button>
        )}
      </Card>

      <Card className="service-band compact" tone="accent">
        <strong>{t("accountPage.paymentTitle")}</strong>
        <p>{t("accountPage.paymentBody")}</p>
      </Card>

      <Button variant="ghost" wide type="button" onClick={logout}>
        {t("common.logout")}
      </Button>
      <Toast message={error} tone="error" />
      <Toast message={message} tone="success" />
    </div>
  );
}
