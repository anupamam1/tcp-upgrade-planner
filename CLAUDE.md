# CLAUDE.md — Project context for the TCP Upgrade Planner

Context for Claude Code (and humans). Open this repo in Claude Code on any machine and this file is
auto-loaded, so you can continue building from anywhere after `git clone`.

## What this is
A static web **VMware Telco Cloud Platform (TCP) Upgrade Planner** (vanilla HTML/CSS/ES-module JS +
JSON, **no build step**). The user picks their environment (source → destination version, workload,
components) and the tool generates *their* exact ordered, trackable upgrade runbook, linking each
phase to the authoritative Broadcom doc. It's a personalized plan + execution tracker that bridges to
the docs — not a docs replacement. Inspired by VMware's VCF upgrade planner.

## Hosting / URLs (live)
- **Live tool:** https://tcp-upgrade-tools.github.io/tcp-upgrade-planner/
- **Repo:** https://github.com/tcp-upgrade-tools/tcp-upgrade-planner (GitHub **org**, no personal
  username in the URL; repo was transferred off the personal account).
- GitHub Pages via Actions (`.github/workflows/pages.yml`), auto-deploys on push to `main`.
- **Deploy gotcha:** the workflow uses `concurrency: cancel-in-progress`, and Pages cancels a
  re-deploy of an already-deployed commit SHA → re-running the *same* commit shows "Deployment
  cancelled" (harmless). A real new commit deploys green. Don't manually re-trigger the same SHA.
- **Run locally:** `python3 -m http.server 8080` then open the printed localhost URL.

## Design — VMware Clarity language
- Font: authentic **Clarity City** via `@cds/city@1.1.0` CDN (see `<link>` in index.html), with
  Inter/system fallback.
- **Light** Clarity header (white bar, colored brand mark, accent-underline nav tabs).
- Palette: action-blue `#0072a3`, cool-gray neutrals, green `#318700`/amber status; tuned dark theme.
  Uppercase Clarity buttons, 4px radii. No emojis in the GUI (inline SVG icons only).

## UX flow
- **Progressive wizard** (each step reveals the next): Source → Destination → Workload → Components →
  Generate. Nothing pre-selected. Source dropdown lists all sources grouped (TCP releases +
  TCI – Cloud Director Edition). Workload is derived from source (TCI-CDE sources are VNF-only).
- **Component selection** grouped by layer: mandatory (locked) + optional toggles with flowchart gate
  questions, plus an "Infrastructure layer — full-stack upgrade" master toggle (the flowchart's
  Full-Stack Yes/No; all-or-nothing). Multi-version source cells (e.g. NSX `4.1.0.2 / 4.1.1`) render
  a dropdown to pick the current version; single-value cells show plain text.
- **Runbook**: H2 title is the **upgrade path** (e.g. `TCP 3.0 → TCP 5.0.2`), workload as subtitle;
  then compact "Your selection"; a horizontal stepper; then one phase panel at a time. Back/Next swap
  ONLY the phase panel in place (`renderWalkthrough` builds the static top once; `renderPhase` swaps
  `#phaseHost`) — no jump to top.
- **Finish**: completion = the final phase marked done (not every phase). Shows the "Upgrade complete"
  banner + "Start a new plan".
- Per-phase content (single-source model): summary + Prerequisites (bullets) + Service impact +
  Rollback + Key considerations (bullets) + Reference snippets (commands) + "View Documentation".
- Exports: PDF (html2pdf.js), Copy Markdown, Print. Components matrix + Upgrade Path views. Light
  default theme + dark toggle. Progress resets on each Generate.

## Data model (destination = 5.0.2; target-keyed for future versions)
Only TCP 5.0.2 is documented, so it's the only destination. Data is keyed `byTarget` so adding "5.1"
= one block + a `docs.json` versionSlug entry. Component **target versions come from the 5.0.2 matrix
column** (NSX 4.2.1.3, TKG 2.5.2, Avi 30.2.2, AKO 1.12.3, TCA 3.3.0.1, VCD 10.6.1, ESXi/vCenter/vSAN
8.0 U3d, Aria Ops 8.18.6, Logs 8.18.3, Networks 6.13, vSphere Rep/LSR 9.0.2). TKG is split into
`tkg-mgmt`/`tkg-workload`; their source version aliases to the `tkg` matrix row (`VERSION_ALIAS` in
planner.js) so e.g. TCP 3.0 shows `2.1.1 → 2.5.2`.

Paths (guide p239): CNF sources 3.0/4.0/4.0.1/5.0/5.0.1 → 5.0.2. VNF same + TCI-CDE 3.0 (direct),
2.7 (→ 3.0 → 5.0.2 platform hop), 2.2 (direct; VCD component chain `10.3.3.x → 10.4.3 → 10.6.1` shown
as a caveat in the Cloud Director phase).

Upgrade order (from the guide's flowchart images):
- **CNF:** Airgap → TCA → Harbor → Avi → TKG Mgmt → AKO → TKG Workload → [Full Stack?] → Aria
  Orchestrator → NSX → vCenter → ESXi → vSAN.
- **VNF:** VCD → vSphere Replication → LSR → NSX → vCenter → ESXi → vSAN → Aria → Avi.

## Doc links — version-aware deep links (all verified 200)
`data/docs.json` + `docUrl(data, target, id)` build per-phase URLs: base + versionSlug (5.0.2 →
`5-0-2`) + guidePath + `upgrading-...-from-2-0-to-2-1` + component page slug. Guide **home** =
`.../{guidePath}.html` (sits beside the guide dir; special-cased). Cross-cutting: prerequisites →
Overview, snapshot-backup → overview/snapshot-and-backup-requirements.html, post-upgrade →
post-upgrade-checklist.html. NOTE: Avi Load Balancer's real slug is `upgrade-ako-for-non-airgap.html`
(a Broadcom quirk, verified).

## Files
- `index.html` · `assets/css/style.css` · `assets/js/planner.js` (loadData, availableComponents,
  buildPlan, sourcesFor/intermediatesFor/allSourcesFor/editionsFor/componentCaveat/targets/docUrl,
  sourceVersion + VERSION_ALIAS) · `assets/js/app.js` (wizard, walkthrough, exports, views).
- `data/`: `versions.json` (matrix + targets), `components.json` (meta + mandatory + gate),
  `sequence.json` (CNF/VNF order + fullStack flags), `paths.json` (byTarget + componentCaveats +
  sourceLabels + sourceGroups), `steps.json` (per-phase single-source content), `docs.json`
  (version-aware doc URLs).
- `tools/extract.py` + `tools/upgrade_guide_text.txt` (source text from the PDF via `pdftotext
  -layout`; the PDF is not committed). `.github/workflows/pages.yml`, `.nojekyll`, `README.md`.

## Conventions / gotchas
- **Cache busting:** index.html references style.css/app.js with `?v=N`; app.js imports planner.js
  with `?v=N`; bump N on any JS/CSS change (currently **v31**). `data/*.json` fetched with
  `cache: "no-store"`.
- CSS MUST keep `[hidden]{display:none!important}` — otherwise `display:flex/grid` overrides the HTML
  `hidden` attribute (this bug made the toolbar show on the landing page).
- All external doc links open a new tab (`target="_blank" rel="noopener"`).
- Content source-of-truth: `tools/upgrade_guide_text.txt` (from the TCP 5.1 PDF) + the version matrix.
- **Core principle (user-enforced): NEVER invent steps, versions, or tables — everything must trace
  to the TCP upgrade guide.** Confirm design choices before building. Prefer generic wording (avoid
  "Tanzu" / "Cloud Director" in UI labels and README).

## Continuing from another computer
1. `git clone https://github.com/tcp-upgrade-tools/tcp-upgrade-planner`
2. Open the folder in Claude Code (this `CLAUDE.md` loads automatically).
3. `python3 -m http.server 8080` to preview; edit; commit; push to `main` → auto-deploys to Pages.
4. You need write access to the `tcp-upgrade-tools` org repo and `gh auth login` (or a PAT) to push.
