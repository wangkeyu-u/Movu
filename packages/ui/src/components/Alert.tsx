import { cx } from "./utils";

export type AlertTone = "info" | "error" | "success" | "warning";

interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  tone?: AlertTone;
}

export function Alert({ tone = "info", className, ...props }: AlertProps) {
  return <div className={cx("ui-alert", `ui-alert-${tone}`, className)} role={tone === "error" ? "alert" : "status"} {...props} />;
}
