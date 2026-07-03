import { cx } from "./utils";

interface CardProps extends React.HTMLAttributes<HTMLElement> {
  as?: React.ElementType;
  tone?: "default" | "strong" | "dark" | "accent";
}

export function Card({ as: Element = "section", tone = "default", className, ...props }: CardProps) {
  return <Element className={cx("ui-card", `ui-card-${tone}`, className)} {...props} />;
}
