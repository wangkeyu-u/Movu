import { cx } from "./utils";

export function Select({ className, ...props }: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return <select className={cx("ui-input", "ui-select", className)} {...props} />;
}
