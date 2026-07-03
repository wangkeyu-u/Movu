import { cx } from "./utils";

export type ButtonVariant = "primary" | "secondary" | "ghost" | "danger" | "icon";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  wide?: boolean;
}

export function Button({ className, variant = "primary", wide = false, ...props }: ButtonProps) {
  return <button className={cx("ui-button", `ui-button-${variant}`, wide && "ui-button-wide", className)} {...props} />;
}
