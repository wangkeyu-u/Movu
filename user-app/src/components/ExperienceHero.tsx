import type { ReactNode } from "react";

import { useDepthTilt } from "./useDepthTilt";

interface ExperienceHeroProps {
  title: string;
  subtitle: string;
  label?: string;
  image: string;
  icon: ReactNode;
  variant?: "ride" | "drive" | "home";
}

export function ExperienceHero({ title, subtitle, label, image, icon, variant = "ride" }: ExperienceHeroProps) {
  const depth = useDepthTilt(3.4);

  return (
    <section className={`experience-hero ${variant} depth-surface`} {...depth}>
      <div className="hero-copy">
        {label && <span className="quiet-label">{label}</span>}
        <h1>{title}</h1>
        <p>{subtitle}</p>
      </div>
      <div className="hero-emblem" aria-hidden="true">
        {icon}
      </div>
      <img src={image} alt="" aria-hidden="true" />
    </section>
  );
}
