// "use client";

// import React, { useEffect, useState } from "react";

// export default function FpsMeter() {
//   const [fps, setFps] = useState(0);

//   useEffect(() => {
//     let last = performance.now(), frames = 0, acc = 0, raf = 0 as unknown as number;
//     const loop = (now: number) => {
//       frames++; acc += now - last; last = now;
//       if (acc >= 1000) { setFps(frames); frames = 0; acc = 0; }
//       raf = requestAnimationFrame(loop);
//     };
//     raf = requestAnimationFrame(loop);
//     return () => cancelAnimationFrame(raf);
//   }, []);

//   return <span className="text-sm">FPS: {fps}</span>;
// }

"use client";

import React, { useEffect, useState } from "react";

/**
 * FPSMeter
 * Measures real UI frame rate using requestAnimationFrame.
 * Updates displayed FPS once per second.
 */
export default function FPSMeter() {
  const [fps, setFps] = useState(0);

  useEffect(() => {
    let last = performance.now();
    let frames = 0;
    let rafId: number;

    const loop = (now: number) => {
      frames++;

      // If 1 second elapsed → update FPS
      if (now - last >= 1000) {
        setFps(frames);
        frames = 0;
        last = now;
      }

      rafId = requestAnimationFrame(loop);
    };

    rafId = requestAnimationFrame(loop);

    return () => cancelAnimationFrame(rafId);
  }, []);

  return (
    <span className="text-sm">
      FPS: {fps}
    </span>
  );
}
