/**
 * Centralized EVM math. Use ONLY these helpers — never inline.
 *
 *   SV  = EV - PV
 *   CV  = EV - AC
 *   SPI = EV / PV    (PV = 0 → 1)
 *   CPI = EV / AC    (AC = 0 → 1)
 *   EAC = BAC / CPI
 *   VAC = BAC - EAC
 */
export const sv  = (ev: number, pv: number) => ev - pv;
export const cv  = (ev: number, ac: number) => ev - ac;
export const spi = (ev: number, pv: number) => (pv === 0 ? 1 : ev / pv);
export const cpi = (ev: number, ac: number) => (ac === 0 ? 1 : ev / ac);
export const eac = (bac: number, cpiV: number) => (cpiV === 0 ? bac : bac / cpiV);
export const vac = (bac: number, eacV: number) => bac - eacV;

export const fmtUsd = (n: number | null | undefined) =>
  n == null || Number.isNaN(Number(n)) ? "—" : `$${Number(n).toLocaleString(undefined, { maximumFractionDigits: 0 })}`;

export const fmtIdx = (n: number | null | undefined) =>
  n == null || Number.isNaN(Number(n)) ? "—" : Number(n).toFixed(2);

export const idxTone = (n: number | null | undefined) => {
  if (n == null) return "text-muted-foreground";
  if (n >= 1.0) return "text-success";
  if (n >= 0.85) return "text-warning";
  return "text-destructive";
};
