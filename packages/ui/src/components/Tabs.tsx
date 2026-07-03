import { cx } from "./utils";

interface TabsProps extends React.HTMLAttributes<HTMLDivElement> {
  label?: string;
}

export function Tabs({ label, className, ...props }: TabsProps) {
  return <div className={cx("ui-tabs", className)} role="tablist" aria-label={label} {...props} />;
}

interface TabButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  active?: boolean;
}

export function TabButton({ active = false, className, ...props }: TabButtonProps) {
  return <button className={cx("ui-tab-button", active && "active", className)} role="tab" aria-selected={active} {...props} />;
}
