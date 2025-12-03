"use client";

import React, { useEffect, useState } from "react";

export default function FpsMeter() {
  const [fps, setFps] = useState(0);

  useEffect(() => {
    let last = performance.now(), frames = 0, acc = 0, raf = 0 as unknown as number;
    const loop = (now: number) => {
      frames++; acc += now - last; last = now;
      if (acc >= 1000) { setFps(frames); frames = 0; acc = 0; }
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, []);

  return <span className="text-sm">FPS: {fps}</span>;
}