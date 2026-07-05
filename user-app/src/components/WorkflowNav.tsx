import type { ReactNode } from "react";

import { NavLink } from "react-router-dom";

interface WorkflowNavItem {
  to: string;
  label: string;
  icon: ReactNode;
  end?: boolean;
}

interface WorkflowNavProps {
  label: string;
  items: WorkflowNavItem[];
}

export function WorkflowNav({ label, items }: WorkflowNavProps) {
  return (
    <nav className="workflow-nav" aria-label={label}>
      {items.map((item) => (
        <NavLink key={item.to} to={item.to} end={item.end}>
          {item.icon}
          <span>{item.label}</span>
        </NavLink>
      ))}
    </nav>
  );
}
