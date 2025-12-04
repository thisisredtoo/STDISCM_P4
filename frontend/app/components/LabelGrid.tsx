"use client";
import React from "react";
import { normalize16 } from "./utils";

export default function LabelGrid({ title, items }: { title: string; items: (string | number)[] }) {
  const tiles = normalize16(items);
  return (
    <section className="mb-4">
      <h3 className="text-sm font-medium mb-2">{title}</h3>
      <div className="grid grid-cols-8 gap-2">
        {tiles.map((text, i) => (
          <div key={i} className="w-32 h-32 bg-neutral-900 text-center flex items-center justify-center text-lg font-semibold">
            {text ?? ""}
          </div>
        ))}
      </div>
    </section>
  );
}