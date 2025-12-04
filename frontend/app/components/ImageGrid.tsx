// "use client";
// import React from "react";
// import { normalize16 } from "./utils";

// export default function ImageGrid({ title, images }: { title: string; images: string[] }) {
//   const tiles = normalize16(images);
//   return (
//     <section className="mb-4">
//       <h3 className="text-sm font-medium mb-2">{title}</h3>
//       <div className="grid grid-cols-8 gap-2">
//         {tiles.map((src, i) => (
//           <div key={i} className="tile w-32 h-32 bg-neutral-900 flex items-center justify-center overflow-hidden">
//             {src ? <img src={src} className="pixelated w-32] h-32" alt="tile" /> : null}
//           </div>
//         ))}
//       </div>
//     </section>
//   );
// }

// components/ImageGrid.tsx
"use client";
import React from "react";

export default function ImageGrid({ title, images }: { title: string; images: string[] }) {
  return (
    <section className="mb-4">
      <h3 className="text-sm font-medium mb-2">{title}</h3>
      <div className="grid grid-cols-8 gap-2">
        {images.slice(0, 16).map((src, i) => (
          <div key={i} className="w-16 h-16 bg-neutral-900 flex items-center justify-center">
            {/* width/height attributes make the browser upscale 32→64 smoothly */}
            <img
              src={src}
              alt={`tile-${i}`}
              width={64}
              height={64}
              className="block"
              style={{ imageRendering: "auto" }} // smooth interpolation (default)
            />
          </div>
        ))}
      </div>
    </section>
  );
}
