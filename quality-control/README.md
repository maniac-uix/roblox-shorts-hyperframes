# quality-control/

See `qc-checklist.md` for the full gate list. Run:

```bash
bash quality-control/qc.sh output/<video>.mp4
```

Exit 0 = technical QC passed. Visual QC (subtitle legibility, motion,
mobile preview) is manual and mandatory — a script cannot see what you see.
