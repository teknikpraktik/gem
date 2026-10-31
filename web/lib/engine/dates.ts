/**
 * Calendar helpers on ISO dates (YYYY-MM-DD), timezone-free.
 *
 * Mirrors the pandas/numpy semantics used by the Python reference engine
 * (research/src/gem/live.py): weekday business days, no holiday calendar.
 */

export type ISODate = string; // "YYYY-MM-DD"

const DAY_MS = 86_400_000;

export function toUTC(d: ISODate): number {
  const [y, m, dd] = d.split("-").map(Number);
  return Date.UTC(y, m - 1, dd);
}

export function fromUTC(ms: number): ISODate {
  return new Date(ms).toISOString().slice(0, 10);
}

export function addDays(d: ISODate, n: number): ISODate {
  return fromUTC(toUTC(d) + n * DAY_MS);
}

/** 0 = Monday ... 6 = Sunday (pandas weekday convention). */
export function weekday(d: ISODate): number {
  return (new Date(toUTC(d)).getUTCDay() + 6) % 7;
}

/** Last day of the given month (month 1-12; may be <1 or >12, normalised). */
export function monthEnd(year: number, month: number): ISODate {
  return fromUTC(Date.UTC(year, month, 0)); // day 0 of next month
}

export function monthEndOf(d: ISODate): ISODate {
  const [y, m] = d.split("-").map(Number);
  return monthEnd(y, m);
}

/** Month end `n` months before a month-end date (pd.offsets.MonthEnd(n) from a month end). */
export function monthEndMinus(me: ISODate, n: number): ISODate {
  const [y, m] = me.split("-").map(Number);
  return monthEnd(y, m - n);
}

/** Last calendar month end strictly before `asOf`. */
export function previousMonthEnd(asOf: ISODate): ISODate {
  const [y, m] = asOf.split("-").map(Number);
  return monthEnd(y, m - 1);
}

/** Last weekday on or before d (pandas: d if weekday<5 else d - BDay(1)). */
export function lastBusinessDayOnOrBefore(d: ISODate): ISODate {
  let x = d;
  while (weekday(x) >= 5) x = addDays(x, -1);
  return x;
}

/**
 * numpy.busday_count(a, b): number of weekdays in [a, b). Negative if b < a.
 */
export function busdayCount(a: ISODate, b: ISODate): number {
  if (a === b) return 0;
  if (toUTC(b) < toUTC(a)) return -busdayCount(b, a);
  let n = 0;
  for (let x = a; toUTC(x) < toUTC(b); x = addDays(x, 1)) if (weekday(x) < 5) n++;
  return n;
}

export function monthKey(d: ISODate): string {
  return d.slice(0, 7);
}
