import type { PointerEvent } from "react";

export function useDepthTilt(strength = 5) {
  function move(event: PointerEvent<HTMLElement>) {
    if (event.pointerType === "touch") return;
    const target = event.currentTarget;
    const rect = target.getBoundingClientRect();
    const x = (event.clientX - rect.left) / rect.width - 0.5;
    const y = (event.clientY - rect.top) / rect.height - 0.5;
    target.style.setProperty("--tilt-x", `${(-y * strength).toFixed(2)}deg`);
    target.style.setProperty("--tilt-y", `${(x * strength).toFixed(2)}deg`);
    target.style.setProperty("--glow-x", `${((x + 0.5) * 100).toFixed(1)}%`);
    target.style.setProperty("--glow-y", `${((y + 0.5) * 100).toFixed(1)}%`);
  }

  function leave(event: PointerEvent<HTMLElement>) {
    const target = event.currentTarget;
    target.style.setProperty("--tilt-x", "0deg");
    target.style.setProperty("--tilt-y", "0deg");
    target.style.setProperty("--glow-x", "50%");
    target.style.setProperty("--glow-y", "20%");
  }

  return {
    onPointerMove: move,
    onPointerLeave: leave
  };
}
