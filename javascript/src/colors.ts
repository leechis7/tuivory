/** Internal color math shared by independent painters. Not a public package entry. */
const ansiRGB = [
  [0, 0, 0],
  [128, 0, 0],
  [0, 128, 0],
  [128, 128, 0],
  [0, 0, 128],
  [128, 0, 128],
  [0, 128, 128],
  [192, 192, 192],
  [128, 128, 128],
  [255, 0, 0],
  [0, 255, 0],
  [255, 255, 0],
  [0, 0, 255],
  [255, 0, 255],
  [0, 255, 255],
  [255, 255, 255],
];
export function colorRGB(value: string): number[] {
  if (/^#[0-9a-f]{6}$/i.test(value))
    return [1, 3, 5].map((i) => parseInt(value.slice(i, i + 2), 16));
  const n = Number(value);
  if (!Number.isInteger(n) || n < 0 || n > 255)
    throw new Error("invalid color");
  if (n < 16) return [...ansiRGB[n]];
  if (n >= 232) return Array(3).fill(8 + (n - 232) * 10);
  const i = n - 16,
    cube = [0, 95, 135, 175, 215, 255];
  return [cube[Math.floor(i / 36)], cube[Math.floor(i / 6) % 6], cube[i % 6]];
}
export function colorContrast(a: string, b: string): number {
  const luma = (color: string) => {
    const [r, g, b] = colorRGB(color).map((n) => {
      const v = n / 255;
      return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
    });
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  };
  const x = luma(a),
    y = luma(b);
  return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05);
}
