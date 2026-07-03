import { Button, Input } from "@movu/ui";
import { FormEvent, useState } from "react";
import { Navigate } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { LanguageSwitcher } from "../components/LanguageSwitcher";
import { useAuth } from "../routes/AuthProvider";

export function LoginPage() {
  const { t } = useTranslation();
  const { user, login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (user) return <Navigate to="/" replace />;

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await login(email, password);
    } catch (err) {
      const message = err instanceof Error && err.message === "login.adminOnly" ? t("login.adminOnly") : t("common.error");
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="login-screen">
      <div className="login-panel">
        <div className="login-header">
          <div className="brand-mark">M</div>
          <LanguageSwitcher />
        </div>
        <h1>{t("login.title")}</h1>
        <p>{t("login.subtitle")}</p>
        <form onSubmit={handleSubmit} className="login-form">
          <label>
            <span>{t("login.email")}</span>
            <Input value={email} onChange={(event) => setEmail(event.target.value)} type="email" required />
          </label>
          <label>
            <span>{t("login.password")}</span>
            <Input value={password} onChange={(event) => setPassword(event.target.value)} type="password" required />
          </label>
          {error && <div className="form-error">{error}</div>}
          <Button disabled={loading} type="submit">
            {loading ? t("common.loading") : t("login.submit")}
          </Button>
        </form>
      </div>
      <div className="login-map">
        <div className="route-line" />
        <div className="dispatch-card top">
          <strong>{t("dashboard.attention")}</strong>
          <span>{t("dashboard.attentionCopy")}</span>
        </div>
        <div className="dispatch-card bottom">
          <strong>{t("sos.title")}</strong>
          <span>{t("sos.subtitle")}</span>
        </div>
      </div>
    </main>
  );
}
