# CRP demo

Hands-on version of the Semicolon Guy "Critical Rendering Path" video (Day 1, Step 2).

## Run

```bash
cd day-01-how-the-web-and-browser-work/crp-demo
python3 server.py
```

Open http://localhost:8000 and open DevTools (Cmd + Option + I) on the Console and Network tabs.
Stop the server with Ctrl + C.

`server.py` delays any file with `?delay=<ms>` (e.g. `css/index2.css?delay=5000`) and sends
`Cache-Control: no-store`, so you don't need Slow 3G throttling and you never see a cached result.

## Experiments

| Page | Shows |
|---|---|
| 1-css-render-blocking | Blank for 5 s, then blue — CSS is render-blocking, red never shows |
| 2-script-parser-blocking | Text after a plain `<script>` waits for it — scripts are parser-blocking; downloads still run in parallel |
| 3-defer | Page shows at once; scripts run after parsing, in written order, before DOMContentLoaded |
| 4-async | Page shows at once; each script runs as soon as it arrives, any order |
| 5-render-tree-and-layout | `display: none` vs `visibility: hidden`, `::before`, layout width changing with the window, paint flashing |
| 6-css-blocks-js | An inline script waits for a slow stylesheet |

Change the `?delay=` numbers in the HTML and reload to experiment.

## Files

```
server.py           static server with ?delay
css/index.css       h1 red (fast)
css/index2.css      h1 blue (overrides by the cascade)
js/index.js         turns h1 green, logs whether #after exists yet
js/index2.js        appends text to h1, logs the same
```
