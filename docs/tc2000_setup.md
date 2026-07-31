# TC2000 EasyScan Setup and File Handoff

This is the operator-verification draft. TC2000 supplies candidates only. Independent market data recomputes every execution-critical rule.

## Base universe

Select and record one named TC2000 WatchList representing the intended US-listed stock universe. The exact list must be approved before SHADOW begins because top-2% membership changes with the base universe. ETFs, ADRs, SPACs, preferred shares, warrants, units, rights, and OTC symbols remain unresolved and cannot be silently included or excluded.

Record with each operating configuration:

- Exact WatchList name and symbol count
- TC2000 edition and data subscription
- Real-time or delayed status
- Split/adjustment behavior shown by TC2000
- Operator timezone and scan refresh timestamp

## Personal Criteria Formulas

Create these daily-timeframe numeric PCFs. TC2000 documents percent change as `(current - prior) / prior * 100`, ADR primitives as `AVG(H-L, period)`, and dollar volume as `C * V`.

| Name | Daily PCF | Use |
|---|---|---|
| `SWING_STRENGTH_20` | `100 * (C / C20 - 1)` | Approximate one-month return |
| `SWING_STRENGTH_60` | `100 * (C / C60 - 1)` | Approximate three-month return |
| `SWING_STRENGTH_120` | `100 * (C / C120 - 1)` | Approximate six-month return |
| `SWING_ADR20_PCT_PREVCLOSE` | `AVG(100 * (H - L) / C1, 20)` | Provisional fast-movement definition |
| `SWING_AVG_DOLLAR_VOLUME_20` | `AVG(C * V, 20)` | Provisional liquidity definition |

The code must reproduce these formulas from independent bars and also evaluate ATR20% in research. One-day gain greater than 5% is not the default volatility filter.

## Create the three EasyScans

For each scan below:

1. Use the same recorded base WatchList.
2. Add the matching `SWING_STRENGTH_*` PCF as a daily numeric condition.
3. Use the TC2000 value/rank control to retain the 98th percentile through maximum, meaning the top 2% relative to the selected base universe.
4. Add daily price condition `C > 1`.
5. Add `SWING_ADR20_PCT_PREVCLOSE >= 5`.
6. Add `SWING_AVG_DOLLAR_VOLUME_20 >= 30000000`.
7. Save and refresh the scan. Record the visible refresh timestamp and result count.

| EasyScan name | Strength PCF | Required export tag |
|---|---|---|
| `SWING_TOP2_20D` | `SWING_STRENGTH_20` | `strength20` |
| `SWING_TOP2_60D` | `SWING_STRENGTH_60` | `strength60` |
| `SWING_TOP2_120D` | `SWING_STRENGTH_120` | `strength120` |

For a reviewed small-account paper experiment, the dollar-volume threshold may be lowered in TC2000 and the matching versioned system configuration. It can never be lower than $5,000,000. A mismatch between the TC2000 threshold and active configuration rejects the batch.

TC2000's help states that EasyScan conditions can use a value slider relative to market rank. The operator must verify that the current UI displays the intended 98-to-Max rank against the chosen base WatchList. If the UI cannot do this reproducibly, export the PCF value column and sort manually under a documented procedure. The importer must never infer that a symbol-only export proves its rank.

## Daily export procedure

Run the procedure after refreshing all three scans:

1. Confirm all scans show the same market date and that each result list is non-empty.
2. In each EasyScan WatchList, right-click a symbol, choose `Copy All Symbols To...`, then `Copy to Clipboard`.
3. Paste symbols only into a plain-text UTF-8 file, one symbol per line. No header, ranks, prices, commas, or notes.
4. Save all files using the names below with the same export timestamp.
5. Upload all three files in one dashboard action or one CLI command. Individual-file activation is forbidden.

Filename convention:

```text
tc2000_YYYY-MM-DD_strength20_YYYYMMDDTHHMMSS±HHMM.txt
tc2000_YYYY-MM-DD_strength60_YYYYMMDDTHHMMSS±HHMM.txt
tc2000_YYYY-MM-DD_strength120_YYYYMMDDTHHMMSS±HHMM.txt
```

Example for July 31, 2026 at 4:05 p.m. New York daylight time:

```text
tc2000_2026-07-31_strength20_20260731T160500-0400.txt
tc2000_2026-07-31_strength60_20260731T160500-0400.txt
tc2000_2026-07-31_strength120_20260731T160500-0400.txt
```

The importer will preserve raw bytes, filenames, SHA-256 hashes, received time, stated market date, and operator identity. It rejects a missing scan kind, filename/content mismatch, duplicate symbol, invalid symbol, empty file, market-date mismatch, stale date, or partial upload. The configured maximum timestamp skew and freshness period remain provisional and require operator approval before SHADOW.

## Candidate products

One accepted transaction derives:

- `intersection_3_of_3`: present in all three lists; initial execution-eligible mode.
- `agreement_2_of_3`: present in at least two; shadow only.
- `union_ranked`: present in any list; shadow only. A composite score uses independently recomputed strength when symbol-only exports contain no source rank.

Dashboard import status must show counts, agreement, file hashes, freshness, errors, and the configuration expected by the importer.

## Optional Windows companion

The future companion may watch one configured export directory, wait until all three matching files are stable, hash them, and send one authenticated batch with retries. It must be auditable, use an import-only credential, pin the service identity, never store Alpaca credentials, never automate TC2000 UI, and never expose broker endpoints. Installation, credential rotation, retry queue, logs, and uninstall require separate documentation and tests.

## Operator validation checklist

- [ ] Enter the three PCFs and confirm TC2000 accepts them on the daily timeframe.
- [ ] Verify `AAPL` on a chosen historical date by hand for 20-, 60-, and 120-bar percent change.
- [ ] Verify ADR20% for one liquid stock by exporting at least 21 daily bars and recomputing the formula in a spreadsheet.
- [ ] Verify average dollar volume for the same date from 20 daily closes and volumes.
- [ ] Confirm the rank control retains the 98th percentile through maximum against the recorded base WatchList.
- [ ] Confirm all three exports contain symbols only and preserve dots/hyphens used by valid share classes.
- [ ] Attempt a missing-file, duplicate-symbol, stale-date, and wrong-date batch once importer tests exist; confirm atomic rejection.
- [ ] Save labeled screenshots in `docs/images/tc2000/` for the base universe, each EasyScan, the rank control, and a successful export.

Screenshot placeholders:

- `docs/images/tc2000/01-base-universe.png`
- `docs/images/tc2000/02-strength20-scan.png`
- `docs/images/tc2000/03-strength60-scan.png`
- `docs/images/tc2000/04-strength120-scan.png`
- `docs/images/tc2000/05-export-menu.png`

Chart angle is scale-dependent. The automation never converts a visible 45-degree angle into a literal measurement. It uses versioned normalized slopes.

Official TC2000 references: [EasyScan rank/value control](https://help.tc2000.com/m/69401/l/1695424-how-to-use-the-easyscan-condition-library-menu), [percent-change PCF example](https://help.tc2000.com/m/69445/l/1737175-parameters-and-constants), [ADR formula](https://help.tc2000.com/m/69445/l/1993818-average-daily-range-adr), [dollar-volume formula](https://help.tc2000.com/m/69445/l/755854-dollar-volume), [copying WatchList symbols](https://help.tc2000.com/m/69401/l/325597-how-to-copy-watchlist-symbols-to-microsoft-excel-or-word).
