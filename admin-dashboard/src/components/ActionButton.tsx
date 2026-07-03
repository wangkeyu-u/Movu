import { Button } from "@movu/ui";
import type { ReactNode } from "react";

export function ActionButton({
  children,
  onClick,
  variant = "secondary",
  disabled = false
}: {
  children: ReactNode;
  onClick: () => void;
  variant?: "primary" | "secondary" | "danger";
  disabled?: boolean;
}) {
  return (
    <Button variant={variant === "primary" ? "primary" : variant === "danger" ? "danger" : "secondary"} onClick={onClick} disabled={disabled} type="button">
      {children}
    </Button>
  );
}
