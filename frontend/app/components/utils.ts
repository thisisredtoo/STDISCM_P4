export function normalize16<T>(arr: T[]): T[] {
  if (arr.length === 16) return arr;
  if (arr.length === 0) return new Array(16).fill(undefined as any);
  if (arr.length < 16) {
    const out = arr.slice();
    for (let i = 0; i < 16 - arr.length; i++) out.push(arr[i % arr.length]);
    return out;
  }
  const pick = new Set<number>();
  while (pick.size < 16) pick.add(Math.floor(Math.random() * arr.length));
  return Array.from(pick).map(i => arr[i]);
}

export function pushLoss(buf: [number, number][], p: [number, number]) {
  buf.push(p);
  if (buf.length > 2000) buf.splice(0, buf.length - 2000);
}