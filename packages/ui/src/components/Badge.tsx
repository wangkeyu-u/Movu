import { cx } from "./utils";

export type BadgeTone = "neutral" | "positive" | "negative" | "warning" | "info";

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  tone?: BadgeTone;
}

export function Badge({ tone = "neutral", className, ...props }: BadgeProps) {
  return <span className={cx("ui-badge", `ui-badge-${tone}`, className)} {...props} />;
}
