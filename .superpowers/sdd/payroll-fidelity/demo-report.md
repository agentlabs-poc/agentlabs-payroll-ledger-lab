# Payroll fidelity demo report

Implemented an actual two-employee SQLite journey for October 2026 through March 2027. The 18 chronological snapshots contain complete rows from all five tables and expose employee/month/draft context, selected draft totals, cumulative liability totals, and operation outcomes.

Evidence from the generated flow:

- All 12 expected employee-month totals match the reviewed fixture.
- E101 has exactly five loan applications, October through February, and none in March.
- Reused local source and draft IDs remain employee-qualified.
- The cancelled November draft remains immutable while its replacement is posted.
- Two December correction instructions reference the exact prior posted entries.
- Employer A obligations total INR 27,000, employer B totals INR 9,000, and final outstanding liability is zero.
- The catalogue proof reports all 15 canonical kinds with complete reference closure.

Commands run:

```text
python3 -m sqlite_lab.demo --output public/canonical-flow.json
python3 -m unittest sqlite_lab.test_demo
python3 -m sqlite_lab.prove
npm run build
node .../impeccable/scripts/detect.mjs --json src/main.ts src/styles.css
```

Results: demo tests `3/3 OK`; proof catalogue `15/15`; TypeScript/Vite build passed; UI detector returned no findings. Browser reloads on ports 5174 and 4174 displayed the current 18-stage flow.

Source hashes:

```text
demo.py     6a5def8b888869fbbeccc73dc424eb246ffdecec11c8ab311818d7816d8a621b
prove.py    dbe49a388797ad9ba676bb1057d92427c28b0df5461f21a82a5d2162031d64b1
payroll.py  ef023c9ee6f518c5566c34e7ebd28a967353b480887a217e8765f0f36b65b775
records.py  40af24d2625527963ccac46df387dc598b45df0143896b1b7d451d3a7ba9ebf5
schema.sql  8939bde5852b61e4c61cfc24cbe39e89901275747cf52019f5f208ec0e8eae1f
canonical-flow.json 66b8b218ad19603ea98925493f775db8a250dc81deae250da0f3d4f178e25a0a
```
