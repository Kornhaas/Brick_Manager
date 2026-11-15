---
name: brick-manager-ux
description: Evaluate Brick Manager usability and accessibility or design user flows and interface changes in Jinja, CSS, and vanilla JavaScript. Use for task-based UX reviews and design, not backend-only work.
---

# Brick Manager Usability and UX

Read the affected templates, JavaScript, CSS, routes, and `docs/guides/user-guide.md`. Trace real collection tasks such as finding parts, changing quantities, assigning storage, importing catalogs, and printing labels.

For usability evaluation, identify the user goal and reproducible steps. Inspect navigation, terminology, keyboard access, focus, labels, error recovery, loading/empty states, and touch interactions. Separate observed issues from hypotheses. Report task impact, affected file or element, and a concrete recommendation; do not claim user testing or browser verification without performing it.

For UX design, describe the intended flow and states before editing. Reuse existing visual conventions and Jinja/vanilla JavaScript. Keep quantity editing, storage selection, and collection status understandable on narrow screens and touch devices. Provide semantic controls, associated labels, visible focus, meaningful validation, and announcements for asynchronous feedback where needed. Avoid conveying status by color alone.

Distinguish usability evaluation from design: evaluation documents friction in the current flow; design specifies the improved flow, content, layout, and interaction states. Check destructive or bulk actions for understandable consequences and recovery.

Use available browser tooling against an isolated local environment for keyboard, viewport, and interaction checks. If unavailable, report source inspection and a precise manual verification checklist. Do not start the production app casually: startup can touch data and schedule jobs. Use `brick-manager-development` for implementation and `brick-manager-regression-tests` for behavioral regressions. Keep UI field names synchronized with routes and JSON consumers.
