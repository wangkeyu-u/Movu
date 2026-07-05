import { Button, Card } from "@movu/ui";
import { Gauge, Route, Sparkles } from "lucide-react";
import type { CSSProperties } from "react";
import { useTranslation } from "react-i18next";

import type { Match } from "../api/types";

interface MatchInsightCardProps {
  match: Match;
  label: string;
  actionLabel: string;
  onAction: () => void;
}

const visibleScores = ["route_alignment_score", "route_order_score", "passenger_convenience_score", "driver_detour_score"];

export function MatchInsightCard({ match, label, actionLabel, onAction }: MatchInsightCardProps) {
  const { t } = useTranslation();
  const score = Math.round(match.match_score);
  const scoreStyle = { "--score": score / 100 } as CSSProperties & Record<string, number>;

  return (
    <Card as="article" tone="strong" className="match-insight-card">
      <div className="match-score-orb" style={scoreStyle} aria-label={`${score}%`}>
        <Gauge size={18} aria-hidden="true" />
        <strong>{score}%</strong>
      </div>
      <div className="match-insight-body">
        <div>
          <span className="quiet-label">{t("match.recommended")}</span>
          <strong>{label}</strong>
        </div>
        <div className="score-rails">
          {visibleScores.map((key) => (
            <span key={key} style={{ "--score": match.score_breakdown[key] ?? 0 } as CSSProperties & Record<string, number>}>
              {t(`match.scores.${key}`, { defaultValue: key.split("_").join(" ") })}
            </span>
          ))}
        </div>
        {match.reasons.length > 0 && (
          <ul className="reason-list">
            {match.reasons.slice(0, 3).map((reason) => (
              <li key={reason}>
                <Route size={13} aria-hidden="true" />
                <span>{reason}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
      <Button variant="secondary" type="button" onClick={onAction}>
        <Sparkles size={16} aria-hidden="true" />
        {actionLabel}
      </Button>
    </Card>
  );
}
