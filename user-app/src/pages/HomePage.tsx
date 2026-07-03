import { Card } from "@movu/ui";
import { ArrowRight, CarFront, MapPinned, ShieldCheck } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { AccessNotice } from "../components/AccessNotice";
import { StatusPill } from "../components/StatusPill";
import { useDepthTilt } from "../components/useDepthTilt";
import { useAuth } from "../routes/AuthProvider";
import { getAccessIssue } from "../utils/access";

export function HomePage() {
  const { user } = useAuth();
  const { t } = useTranslation();
  const firstName = user?.name.split(" ")[0] ?? "MovU";
  const accessIssue = getAccessIssue(user);
  const identityDepth = useDepthTilt(3.8);
  const serviceDepth = useDepthTilt(2.6);

  return (
    <div className="page-stack">
      <Card className="home-card identity-card depth-surface" tone="dark" {...identityDepth}>
        <div>
          <span className="quiet-label">{t("home.today")}</span>
          <h1>{t("home.greeting", { name: firstName })}</h1>
          <p>{t("home.intro")}</p>
        </div>
        <div className="home-scene" aria-hidden="true">
          <img src="/assets/images/bg-campus-path-students.jpg" alt="" />
        </div>
        <div className="trust-grid">
          <div>
            <span>{t("common.email")}</span>
            <StatusPill value={Boolean(user?.email_verified)} />
          </div>
          <div>
            <span>{t("common.account")}</span>
            <StatusPill value={user?.verification_status ?? "pending"} />
          </div>
        </div>
      </Card>

      {accessIssue ? (
        <AccessNotice issue={accessIssue} />
      ) : (
        <section className="quick-grid">
          <Link className="quick-action primary" to="/ride">
            <MapPinned size={22} aria-hidden="true" />
            <span>{t("home.requestRide")}</span>
            <ArrowRight size={18} aria-hidden="true" />
          </Link>
          <Link className="quick-action" to="/drive">
            <CarFront size={22} aria-hidden="true" />
            <span>{t("home.postTrip")}</span>
            <ArrowRight size={18} aria-hidden="true" />
          </Link>
          <Link className="quick-action" to="/safety">
            <ShieldCheck size={22} aria-hidden="true" />
            <span>{t("home.safetyTools")}</span>
            <ArrowRight size={18} aria-hidden="true" />
          </Link>
        </section>
      )}

      <Card className="service-band depth-surface" tone="accent" {...serviceDepth}>
        <div>
          <strong>{t("home.serviceTitle")}</strong>
          <p>{t("home.serviceBody")}</p>
        </div>
        <img className="service-illustration" src="/assets/images/ill-map.svg" alt="" aria-hidden="true" />
        <span>{t("home.serviceNote")}</span>
      </Card>

      <Card className="timeline-panel">
        <div className="panel-title timeline-title">
          <h2>{t("home.howItWorks")}</h2>
          <img src="/assets/images/ill-carpooling-public-domain.png" alt="" aria-hidden="true" />
        </div>
        <ol>
          <li>
            <strong>{t("home.verifyTitle")}</strong>
            <span>{t("home.verifyBody")}</span>
          </li>
          <li>
            <strong>{t("home.matchTitle")}</strong>
            <span>{t("home.matchBody")}</span>
          </li>
          <li>
            <strong>{t("home.safeTitle")}</strong>
            <span>{t("home.safeBody")}</span>
          </li>
        </ol>
      </Card>
    </div>
  );
}
