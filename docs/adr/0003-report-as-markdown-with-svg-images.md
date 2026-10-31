---
status: accepted
date: 2026-10-31
---

# Show the report as Markdown with SVG images

## Context and Problem Statement

The report is a plain `report.md`: complete, but slow to read. A dashboard like Sonar's overview needs colours, ratings and charts. GitHub renders Markdown and the images it links in every repository, public or private, with the repository's access rights; it never renders an HTML page. GitHub Pages serves HTML, but needs a paid plan for a private repository, and its site is then public to anyone with the address. Most checked projects are private. How can the report look like Sonar's overview for every checked project?

## Considered Options

* Markdown with SVG images written by qualitycheck
* An HTML dashboard served by GitHub Pages
* An HTML dashboard on another host with access control (e.g. Cloudflare Pages and Access)
* An HTML dashboard read locally only

## Decision Outcome

Chosen option: "Markdown with SVG images written by qualitycheck", because GitHub renders it in every repository with the repository's own access rights, with no host, account or cost, the same way for every project. A mockup on a throwaway branch confirmed the rendering.

* `report.md` stays the entry point; the images go to `docs/qualitycheck-report/images/` and are published with it on the `qualitycheck-report` branch.
* The SVGs are text, written by qualitycheck itself, with no script, no external font and no external link; each one draws its own white card, so it reads the same in GitHub's light and dark themes.

### Consequences

* Good, because a private repository shows the report to its members only.
* Good, because SVG is text: written by a pure function, tested byte for byte, with no new dependency.
* Good, because the report stays complete without the images: each one carries an alternative text, and the sections below keep every finding.
* Bad, because GitHub's Markdown allows no CSS and no interaction: no hover, no filter; a tile can only link to a section of the report.
* Bad, because drawing the tiles and charts (layout, scales) is code to maintain.
* Neutral, because `htmlcov/` and `bandit.html` stay readable locally only.
