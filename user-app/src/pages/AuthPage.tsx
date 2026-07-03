import { Button, Card, TabButton, Tabs } from "@movu/ui";
import { MailCheck } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { api } from "../api/client";
import { Field } from "../components/Field";
import { SelectField } from "../components/SelectField";
import { Toast } from "../components/Toast";
import { useDepthTilt } from "../components/useDepthTilt";
import { useAuth } from "../routes/AuthProvider";

type AuthMode = "login" | "register" | "verify";

export function AuthPage() {
  const { login } = useAuth();
  const { t } = useTranslation();
  const [mode, setMode] = useState<AuthMode>("login");
  const [email, setEmail] = useState("admin@taylors.edu.my");
  const [password, setPassword] = useState("Password123");
  const [name, setName] = useState("");
  const [studentId, setStudentId] = useState("");
  const [role, setRole] = useState("rider");
  const [gender, setGender] = useState("prefer_not_to_say");
  const [token, setToken] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const authDepth = useDepthTilt(3.2);

  async function handleLogin(event: React.FormEvent) {
    event.preventDefault();
    await run(async () => {
      await login(email, password);
    });
  }

  async function handleRegister(event: React.FormEvent) {
    event.preventDefault();
    await run(async () => {
      await api.register({
        name,
        email,
        student_id: studentId || null,
        password,
        role,
        gender
      });
      setMode("verify");
      setMessage(t("auth.accountCreated"));
    });
  }

  async function handleVerify(event: React.FormEvent) {
    event.preventDefault();
    await run(async () => {
      await api.verifyEmail(token);
      setMode("login");
      setMessage(t("auth.emailVerified"));
    });
  }

  async function resend() {
    await run(async () => {
      const response = await api.resendVerification(email);
      setMessage(response.message);
    });
  }

  async function run(action: () => Promise<void>) {
    setSubmitting(true);
    setError(null);
    setMessage(null);
    try {
      await action();
    } catch (err) {
      setError(err instanceof Error ? readableAuthError(err.message, t) : t("common.somethingWrong"));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="auth-screen">
      <div className="auth-shell">
        <section className="auth-hero">
          <div className="brand-mark large">M</div>
          <div>
            <h1>MovU</h1>
            <p>{t("auth.hero")}</p>
          </div>
        </section>

        <Card className="auth-panel depth-surface" {...authDepth}>
          <Tabs label={t("auth.mode")}>
            <TabButton active={mode === "login"} onClick={() => setMode("login")} type="button">
              {t("common.login")}
            </TabButton>
            <TabButton active={mode === "register"} onClick={() => setMode("register")} type="button">
              {t("common.register")}
            </TabButton>
            <TabButton active={mode === "verify"} onClick={() => setMode("verify")} type="button">
              {t("common.verify")}
            </TabButton>
          </Tabs>

          {mode === "login" && (
            <form className="form-stack" onSubmit={handleLogin}>
              <Field label={t("common.campusEmail")} type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
              <Field label={t("common.password")} type="password" value={password} onChange={(event) => setPassword(event.target.value)} required />
              <Button disabled={submitting} type="submit">
                {t("auth.signIn")}
              </Button>
            </form>
          )}

          {mode === "register" && (
            <form className="form-stack" onSubmit={handleRegister}>
              <Field label={t("auth.fullName")} value={name} onChange={(event) => setName(event.target.value)} required />
              <Field label={t("common.campusEmail")} type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
              <Field label={t("auth.studentId")} value={studentId} onChange={(event) => setStudentId(event.target.value)} />
              <Field label={t("common.password")} type="password" value={password} onChange={(event) => setPassword(event.target.value)} required minLength={8} />
              <SelectField
                label={t("auth.iWantTo")}
                value={role}
                onChange={(event) => setRole(event.target.value)}
                options={[
                  { label: t("auth.requestRides"), value: "rider" },
                  { label: t("auth.driveOthers"), value: "driver" }
                ]}
              />
              <SelectField
                label={t("common.gender")}
                value={gender}
                onChange={(event) => setGender(event.target.value)}
                options={[
                  { label: t("auth.preferNotSay"), value: "prefer_not_to_say" },
                  { label: t("auth.female"), value: "female" },
                  { label: t("auth.male"), value: "male" }
                ]}
              />
              <Button disabled={submitting} type="submit">
                {t("common.createAccount")}
              </Button>
            </form>
          )}

          {mode === "verify" && (
            <form className="form-stack" onSubmit={handleVerify}>
              <div className="notice">
                <MailCheck size={18} aria-hidden="true" />
                <span>{t("auth.verifyNotice")}</span>
              </div>
              <Field label={t("common.campusEmail")} type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
              <Field label={t("auth.verificationToken")} value={token} onChange={(event) => setToken(event.target.value)} required />
              <Button disabled={submitting} type="submit">
                {t("auth.verifyEmail")}
              </Button>
              <Button variant="secondary" disabled={submitting} onClick={resend} type="button">
                {t("auth.resendEmail")}
              </Button>
            </form>
          )}

          <Toast message={error} tone="error" />
          <Toast message={message} tone="success" />
        </Card>
      </div>
    </main>
  );
}

function readableAuthError(message: string, t: (key: string) => string): string {
  if (message === "Email is not verified") return t("access.email_unverified.title");
  if (message === "User is banned") return t("access.banned.title");
  if (message === "Account is not approved") return t("access.pending.title");
  return message;
}
