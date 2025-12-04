import React, { useEffect, useState } from "react";

export default function FPSMeter() {
  const [fps, setFps] = useState(60);
  let lastTime = performance.now();
  let frameCount = 0;

  const updateFPS = () => {
    const currentTime = performance.now();
    const deltaTime = currentTime - lastTime;

    if (deltaTime >= 1000) {  
      setFps(frameCount);  
      frameCount = 0;  
      lastTime = currentTime;  
    }

    frameCount += 1; 
    requestAnimationFrame(updateFPS); 
  };

  useEffect(() => {
    requestAnimationFrame(updateFPS); 
  }, []);

  return <div>FPS: {fps}</div>;
}