# Problems and solutions

Every pitfall hit and its fix (or OPEN). Never delete an entry.

## P1 Pixel tool warnings on the site palette (OPEN, harmless)

`pixel_tool.py` warns `palette has no named 'floor' subset` and `ramp 'action' has no visible hue shift`. Both checks come from the game the tool was copied from; the action ramp is a flat brand colour on purpose. Ignore them for site art.

## P2 Browser pane refuses localhost for this repo (OPEN)

The in-app browser denied http://localhost:4321 while the session's main folder was the bot repo. The dev server answers (curl 200). Check pages in a normal browser, or start a session rooted in this repo.
