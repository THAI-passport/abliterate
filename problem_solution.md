# Problems and solutions

Every pitfall hit and its fix (or OPEN). Never delete an entry.

## P1 Pixel tool warnings on the site palette (OPEN, harmless)

`pixel_tool.py` warns `palette has no named 'floor' subset` and `ramp 'action' has no visible hue shift`. Both checks come from the game the tool was copied from; the action ramp is a flat brand colour on purpose. Ignore them for site art.

## P2 Browser pane refuses localhost for this repo (OPEN)

The in-app browser denied http://localhost:4321 while the session's main folder was the bot repo. The dev server answers (curl 200). Check pages in a normal browser, or start a session rooted in this repo.

## P3 Redaction bar hides its text in forced-colors mode (OPEN)

`.redact` in `src/styles/global.css` uses `color: transparent` over a background. In Windows high contrast (`forced-colors: active`) backgrounds are dropped, so the text vanishes with no bar. Fix: inside `@media (forced-colors: active)` set `.redact { color: CanvasText; background: none; outline: 2px solid CanvasText; }`. Keep the word in the markup so screen readers read it. Rule: at most one bar per page, never in headings, titles, alt text, buttons, links, labels or errors (docs/DESIGN.md).

## P4 Waitlist tags conflict with the AGENTS.md privacy rule (OPEN)

AGENTS.md says mailing-list signup stores only the email and consent time. `website-v1.md` and `grill-v1.md` Q20 tag signups `plan:<name>` and `source:<page>` in Buttondown. The privacy copy in `dialogue.md` currently follows AGENTS.md (email and consent time only). Decide: drop the tags, or amend AGENTS.md and the privacy text to say a plan tag is stored.
