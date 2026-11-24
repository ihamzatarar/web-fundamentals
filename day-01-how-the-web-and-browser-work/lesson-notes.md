---
type: concept
title: "Day 1 — How the web and the browser work"
tags: [frontend, browser, rendering, dom, cssom, same-origin, cookies, caching, csr, ssr, ssg, hydration, devtools]
updated: 2026-11-23
sources: []
confidence: reported
---

# Day 1 — How the web and the browser work

2026-11-23 · about 3 h (1 h reading, 1.5 h building, 30 min self-check).
Back to [[frontend-learning-log]].

**Coming from Rails:** you build the response; today is what the browser does after the
`200` — the `Cache-Control`, `Set-Cookie` and CORS headers you set land here.

## Progress

- [x] Step 1 — URL to first byte (DNS, TCP, TLS, HTTP)
- [x] Step 2 — Bytes to pixels (critical rendering path, defer/async)
- [x] Step 3 — Inside the renderer (threads, layers, compositing)
- [x] Step 4 — Same-origin policy
- [x] Step 5 — Cookies, localStorage, HTTP cache
- [x] Step 6 — DevTools: Elements, Network, Performance, Application
- [x] Step 7 — Where HTML is rendered: MPA, CSR, SSR + hydration, SSG, ISR
- [ ] Step 8 — Tool setup: nvm, Node, Yarn, VS Code, ESLint, Prettier, React DevTools
- [ ] Step 9 — Build task
- [ ] Step 10 — Self-check (8 questions)
- [ ] Step 11 — Connect everything

## Readings

| # | Reading | Clipping |
|---|---|---|
| 1 | MDN — How browsers work: https://developer.mozilla.org/en-US/docs/Web/Performance/Guides/How_browsers_work | [[Populating the page how browsers work]] |
| 2 | Chrome — Inside a modern browser, part 3: https://developer.chrome.com/blog/inside-browser-part3 | [[Inside look at modern web browser (part 3)    Blog]] |
| 3 | web.dev — Critical rendering path: https://web.dev/articles/critical-rendering-path | — |
| 4 | Chrome — DevTools Network: https://developer.chrome.com/docs/devtools/network | — |
| 5 | MDN — Same-origin policy: https://developer.mozilla.org/en-US/docs/Web/Security/Same-origin_policy | [[Same-origin policy]] |
| 6 | MDN — Cookies: https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Cookies | [[Using HTTP cookies]] |
| 7 | web.dev — Rendering on the Web: https://web.dev/articles/rendering-on-the-web | [[Rendering on the web    Articles]] |

Videos: Bella Capilla "How Code turns into a Webpage?" https://www.youtube.com/watch?v=hau4bcfwgNM ·
BlinkOn "Life of a Pixel" https://www.youtube.com/watch?v=K2QHdgAKP-s ·
Jake Archibald "In The Loop" https://www.youtube.com/watch?v=cCOL7MC4Pl0 ·
Semicolon Guy "Critical Rendering Path (CRP) - an underrated topic" (Hindi) https://youtu.be/Tnp3yX9Z93Q ·
Prismic ft Bruno Simon "What's the difference between layout painting and compositing?" https://youtu.be/Dl2JmTjb4qk ·
Udacity "Compositing - Compositing and Painting - Browser Rendering Optimization" https://youtu.be/jTRe1tvFYdE

---

## Step 1 — URL to first byte

```
type URL → DNS → TCP handshake → TLS handshake → HTTP GET → first byte (TTFB)
```

| Term | Simple meaning |
|---|---|
| DNS | Phone book: turns `example.com` into an IP address. Cached for its TTL |
| IP address | The computer's address on the internet |
| TCP | Reliable delivery: numbers every byte, resends lost ones, keeps order |
| Handshake | SYN → SYN-ACK → ACK: both sides agree to talk (1 round trip) |
| Round trip | A message there and the reply back |
| TLS | Encryption for HTTPS; checks the server's certificate (1 round trip in TLS 1.3) |
| TTFB | Time to first byte — mostly the backend's time |
| Slow start | TCP sends ~14 KB first, then doubles each round trip while nothing is lost |
| Keep-alive | Reuse an open connection, skipping DNS + TCP + TLS next time |

**Example — see each stage's time for a real URL:**

```bash
curl -o /dev/null -s -w "dns:%{time_namelookup} tcp:%{time_connect} tls:%{time_appconnect} ttfb:%{time_starttransfer}\n" https://example.com
# dns:0.012 tcp:0.095 tls:0.190 ttfb:0.290   ← seconds, each one cumulative
```

Read it as: DNS took 12 ms, the TCP handshake ~83 ms, TLS ~95 ms, and the server
(your Rails app, for your own URL) ~100 ms to send the first byte.

**Example — DNS lookup:**

```bash
dig example.com +short    # → 93.184.216.34  (the IP the browser will connect to)
```

**More from the MDN clipping:**

- **One DNS lookup per hostname.** A page using `app.com`, `cdn.app.com`, `fonts.googleapis.com`
  and `www.google-analytics.com` needs **4 lookups**.
- **Mobile is slower:** each lookup goes phone → cell tower → phone company → DNS server.
- **Cipher suite** = the set of encryption methods both sides agree to use during TLS.
- **Total before the request:** a new connection needs **2 round trips (TLS 1.3)** or **3 (TLS 1.2)** after DNS.
  Example: 100 ms per round trip on 4G → 200–300 ms before the GET is even sent.

**TCP's two limits on "how much can I send before waiting for an ACK?"**

| Limit | Protects | Who sets it |
|---|---|---|
| **Receive window (RWND)** | The receiver's memory | The client, stated in every ACK ("I have 64 KB free") |
| **Congestion window (CWND)** | The network | The server's guess: starts ~14 KB, **doubles** each round trip, cuts back on loss |

- The server sends at most the **smaller** of the two.
- **ssthresh** (slow-start threshold) = the point where doubling stops and growth becomes slow (+1 packet per round trip).
- **ACK** = "I received everything up to byte N". A missing ACK = lost packet → resend.

**The 14 KB rule — example:** a 50 KB HTML page on a new connection arrives over about 3 round trips
(14 KB → 28 KB → rest). Put what's needed to **start drawing** (basic layout HTML + critical CSS) in the
first 14 KB, so the browser can begin before the rest arrives.

## Step 2 — Bytes to pixels (critical rendering path)

```
HTML → DOM ┐
           ├→ render tree → layout → paint → composite → screen
CSS → CSSOM┘
```

| Term | Simple meaning |
|---|---|
| Parse | Read text and turn it into a structure |
| DOM | Tree of elements built from HTML; what JavaScript changes |
| CSSOM | Tree of style rules built from CSS |
| Render tree | DOM + CSSOM, **only visible things** (`display: none` is left out; `visibility: hidden` stays) |
| Layout (reflow) | Work out each box's size and position |
| Paint | Fill in pixels: text, colours, borders, images |
| Composite | Stack the painted layers in the right order |
| Critical rendering path | All the steps above, bytes → pixels |
| Render-blocking | Something the browser must finish before it can show the page (CSS, plain scripts) |
| Preload scanner | Looks ahead in the HTML and starts downloads early |

Video: Semicolon Guy, "Critical Rendering Path (CRP) - an underrated topic" (Hindi) — https://youtu.be/Tnp3yX9Z93Q

**Hands-on demo** (built 2026-11-24, copies the video's setup): `~/Developer/frontend-learning/crp-demo`.
Run `python3 server.py`, open http://localhost:8000. Six pages: CSS render-blocking, script
parser-blocking, defer, async, render tree + layout, CSS blocks JS. Files are slowed with `?delay=ms`
instead of Slow 3G. **Render-blocking** (CSS: nothing is painted until all head CSS arrives) vs
**parser-blocking** (plain script: HTML after it isn't parsed until it runs).

**Example — from HTML to render tree:**

```html
<body>
  <h1>Orders</h1>
  <p class="note">3 pending</p>
  <div style="display: none">debug info</div>
</body>
```
```css
h1 { color: navy; }
.note { font-size: 12px; }
```
```
DOM:          body → h1, p.note, div          (all 3 elements)
CSSOM:        h1 → color navy;  .note → 12px
Render tree:  body → h1 (navy), p.note (12px)  ← div left out: display none
Layout:       h1 at top, 32px tall; p below it at y=40
Paint:        draw navy "Orders", then small "3 pending"
```

Scripts:

| Tag | Blocks HTML parsing? | Runs when |
|---|---|---|
| `<script>` | **Yes** | Immediately, parsing waits |
| `<script defer>` | No | After parsing, **in order** |
| `<script async>` | No | As soon as downloaded, **any order** |

**Example — which to use:**

```html
<head>
  <script src="big-app.js"></script>          <!-- ❌ page stays blank until it downloads and runs -->
  <script src="app.js" defer></script>         <!-- ✅ your app code: needs the DOM, order matters -->
  <script src="analytics.js" async></script>   <!-- ✅ independent: order doesn't matter -->
</head>
```

**More from both clippings:**

**Why a plain script stops the parser:** it could call `document.write()`, which inserts new HTML right there.
```html
<p>Before</p>
<script>document.write("<p>Inserted by JS</p>")</script>   <!-- parser must wait to know what comes next -->
<p>After</p>
```

**Other loading hints:**
```html
<script type="module" src="main.js"></script>                 <!-- modules are deferred automatically -->
<link rel="preload" href="/fonts/inter.woff2" as="font" crossorigin> <!-- "definitely needed, fetch now" -->
```

**CSS blocks JavaScript** (but not HTML parsing): a script may ask "how wide is this box?", so it
waits until the CSS has arrived.

**HTML never throws errors.** The browser repairs mistakes by rules in the HTML standard:
```
You write:        Hi! <b>I'm <i>Chrome</b>!</i>
Browser builds:   Hi! <b>I'm <i>Chrome</i></b><i>!</i>
```
So broken markup fails **silently** — check the real DOM in DevTools → Elements, not your source file.
Tokenization = splitting HTML text into pieces (start tag, end tag, attribute, text) before building the tree.

**Every element has styles, even with no CSS:** the browser's **default stylesheet** (user-agent
stylesheet) makes `<h1>` big and gives `<p>` margins. **Computed style** = the final value of every
property after all rules apply. See it: DevTools → Elements → **Computed** tab.

**Cascade** = start with the most general rule, then let more specific rules override it:
```css
p        { color: black; }   /* general */
.note    { color: gray;  }   /* more specific → wins for <p class="note"> */
```
Building the CSSOM is **fast** — usually quicker than one DNS lookup. In DevTools it is part of
**"Recalculate Style"**. Not worth optimising first.

**JavaScript compilation:** JS text → **AST** (abstract syntax tree: the code as a tree) → **bytecode**
(compact instructions) → run, mostly on the main thread. Same idea as Ruby compiling to YARV bytecode.

**Accessibility tree** (AOM, accessibility object model) = a simplified, meaning-only copy of the DOM
that **screen readers** use ("button: Save", "heading: Orders"). Built alongside the DOM; until it
exists, screen readers can't read the page.

**Layout tree ≠ DOM — example:**
```css
p::before { content: "Note: "; }   /* in the layout tree, but NOT in the DOM */
.hidden   { display: none; }        /* in the DOM, but NOT in the layout tree */
.ghost    { visibility: hidden; }   /* in both: invisible, still takes space */
```
Layout is hard because everything depends on everything: bigger font → line breaks change →
paragraph gets taller → everything below moves.

**Reflow from a missing image size — example:**
```html
<img src="car.jpg">                          <!-- ❌ size unknown: text below jumps when it loads -->
<img src="car.jpg" width="600" height="400"> <!-- ✅ space reserved: no reflow -->
```

**Paint records** = a drawing to-do list ("background, then text, then rectangle"), **not pixels yet**.
The order matters because of `z-index`:
```css
.modal   { position: fixed; z-index: 100; }  /* written first in HTML, but must be drawn on top */
.content { position: relative; z-index: 1; }
```

**First paints:** **First Contentful Paint (FCP)** = first text or image shown.
**First Meaningful Paint** = when the main content is shown (older metric).

## Step 3 — Inside the renderer

| Thread (a worker) | Job |
|---|---|
| Main thread | Parse HTML, run **your JS**, style, layout, paint records |
| Compositor thread | Stack layers into frames, handle scrolling |
| Raster threads | Turn drawing instructions into pixels (in tiles) |
| Worker threads | JS you move off the main thread (Web Workers) |

- The main thread does one thing at a time → long JS freezes the page (**jank** = skipped frames).
- 60 frames a second → about **16 ms** per frame.
- **Layer** = a transparent sheet painted separately. **Raster** = turning a sheet into pixels.
- Cost of a change:

| Change | Reruns | Cost |
|---|---|---|
| `width`, `top`, `font-size` | layout → paint → composite | high |
| `color`, `background` | paint → composite | medium |
| `transform`, `opacity` | composite only (off the main thread) | low |

Video on why `transform` and `opacity` only need compositing: Prismic ft Bruno Simon,
"What's the difference between layout painting and compositing?" — https://youtu.be/Dl2JmTjb4qk

**Example — the same slide-in animation, two ways:**

```css
/* ❌ layout + paint every frame → can stutter */
.menu { transition: left 0.3s; left: -300px; }
.menu.open { left: 0; }

/* ✅ composite only → smooth even if JS is busy */
.menu { transition: transform 0.3s; transform: translateX(-300px); }
.menu.open { transform: translateX(0); }
```

**Example — JS that freezes the page:**

```js
button.onclick = () => {
  let total = 0;
  for (let i = 0; i < 2_000_000_000; i++) total += i;  // ~2 s on the main thread
  label.textContent = total;                            // nothing can scroll or click meanwhile
};
```

Fix: move the loop into a **Web Worker** (a separate thread), like moving slow work from a
Rails request into a Sidekiq job.

**More from both clippings:**

**Processes vs threads.** A **process** = a separate running program with its own memory.
A **thread** = a worker inside a process. Chrome uses several processes:

| Process | Job |
|---|---|
| Browser process | Address bar, tabs, network requests |
| Renderer process (about one per tab) | Turns HTML/CSS/JS into the page — the threads above live here |
| GPU process | Puts the final image on screen |

They talk by **IPC** (inter-process communication: sending messages between processes).

**Every step uses the previous step's output** → change something early and everything after reruns.
Animations must redo the needed steps **every frame**.

**Split long JS so frames still happen — `requestAnimationFrame`:**
```js
function processInChunks(items) {
  const chunk = items.splice(0, 500);       // do a small piece
  chunk.forEach(render);
  if (items.length) requestAnimationFrame(() => processInChunks(items)); // continue next frame
}
```
`requestAnimationFrame(fn)` = "run `fn` just before the next frame is drawn".

**Rasterizing** = turning drawing instructions into pixels.
- Old way: draw only what's visible; on scroll, draw the new part → slow.
- Modern way: **compositing**:

```
main thread:  layout tree → layer tree ("Update Layer Tree" in DevTools) → commit
compositor:   cut each layer into tiles → send tiles to raster threads
raster:       tiles → pixels, stored in GPU memory (visible tiles first)
compositor:   draw quads → compositor frame → browser process (IPC) → GPU → screen
```

| Term | Simple meaning |
|---|---|
| Layer tree | Which parts of the page get their own sheet |
| Tile | A small square piece of a layer, rasterized separately |
| Draw quad | "Tile X goes at position Y on the page" |
| Compositor frame | All draw quads for one frame of the page |
| GPU memory | The graphics card's memory, where finished tiles are kept |

- Tiles **near the viewport** are drawn first. Layers keep tiles at several resolutions for **zoom**.
- **What gets its own layer:** `<video>`, `<canvas>`, elements with `opacity`, a 3D `transform`, or `will-change`.
  ```css
  .side-menu { will-change: transform; }   /* hint: "this will move, give it a layer" */
  ```
- **Too many layers is slower** and uses memory — measure in DevTools → **Layers** panel.
- **Scrolling** needs only the compositor → smooth even while the main thread runs JS.

Video on compositing: Udacity, "Compositing - Compositing and Painting - Browser Rendering
Optimization" — https://youtu.be/jTRe1tvFYdE

**Pixels per frame — example:** an iPad screen (2048 × 1536) has **3.1 million pixels**, and at
60 fps all frame work must finish in **16.67 ms**. That's why layers and the GPU matter.

**Interactivity:**
- **Time to Interactive (TTI)** = when the page responds to taps and clicks within **50 ms**.
- A page can **look ready but not respond**. Example: the image shows fast, but `another-script.js`
  is 2 MB on a slow connection → scrolling stutters until it is downloaded, parsed and run.
- The MDN clipping's measured example: JS execution held the main thread for **over 1.5 s**, with no
  response to clicks the whole time.

## Step 4 — Same-origin policy

**Origin** = scheme + host + port.

| URL A | URL B | Same origin? | Why |
|---|---|---|---|
| `https://app.com` | `https://app.com/orders` | ✅ | path doesn't count |
| `https://app.com` | `http://app.com` | ❌ | scheme differs |
| `https://app.com` | `https://api.app.com` | ❌ | host differs (subdomain) |
| `http://localhost:3000` | `http://localhost:5173` | ❌ | **port differs** |

**Same-origin policy** = a browser rule: JS from one origin **can't read** responses or data
from another origin unless that origin allows it.

| Allowed by default | Blocked by default |
|---|---|
| Load `<img>`, `<script>`, `<link>` CSS from anywhere | JS **reading** a `fetch` response from another origin |
| Submit a form to another origin | JS reading another origin's cookies, localStorage, or iframe page |

- Why: stops a bad site from using **your logged-in browser** to read your bank or MyApp data.
- **CORS** (Cross-Origin Resource Sharing) = the server's way to say "this other origin may read me", via headers like `Access-Control-Allow-Origin`. In Rails: `rack-cors` in `config/initializers/cors.rb`.
- **Preflight** = an automatic `OPTIONS` request the browser sends first for "non-simple" requests (JSON body, custom headers like `Authorization`) to ask the server's permission.
- Same-origin policy is enforced **by the browser only** — `curl` and Rails→API calls ignore it.

**Example — the attack it prevents:**

```js
// running on evil.com, while you are logged in to myapp.com in the same browser
fetch("https://myapp.com/api/orders", { credentials: "include" })  // your cookie is sent
  .then(r => r.json())   // ❌ blocked: evil.com may not READ myapp.com's response
```

**Example — the error you'll see in the DevTools Console:**

```
Access to fetch at 'http://localhost:3000/api/orders' from origin 'http://localhost:5173'
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present.
```

**Example — the Rails fix (`config/initializers/cors.rb`):**

```ruby
Rails.application.config.middleware.insert_before 0, Rack::Cors do
  allow do
    origins "http://localhost:5173"          # who may read our responses
    resource "/api/*", headers: :any, methods: %i[get post patch delete options]
  end
end
```

**Example — a preflight, as seen in the Network tab:**

```
OPTIONS /api/orders                       ← browser asks first
Origin: http://localhost:5173
Access-Control-Request-Method: POST
Access-Control-Request-Headers: authorization, content-type

204 No Content                            ← Rails (rack-cors) answers
Access-Control-Allow-Origin: http://localhost:5173
Access-Control-Allow-Methods: GET, POST, PATCH, DELETE, OPTIONS

POST /api/orders                          ← only now the real request is sent
```

## Step 5 — Cookies, localStorage, HTTP cache

Three places the browser keeps data. The big question: **is it sent to the server?**

| | Cookies | localStorage | HTTP cache |
|---|---|---|---|
| Stores | Small key=value (login session, preferences) | Key=value strings the JS saves | Copies of responses (JS, CSS, images, API JSON) |
| Who writes it | Server (`Set-Cookie`) or JS | JS only | Browser, following `Cache-Control` |
| **Sent to server?** | ✅ **automatically, every request** to that site | ❌ never (unless JS adds it) | ❌ — it *avoids* requests |
| JS can read it? | Yes, unless `HttpOnly` | Yes | No (not directly) |
| Size | ~4 KB per cookie | ~5 MB per origin | Large (browser decides) |
| Lifetime | Until `Expires`/`Max-Age`, or tab-session | Until deleted | Until `max-age` passes or evicted |
| Scope | Domain + path | Origin | URL |

### Cookies

**Cookie** = a small piece of data the server asks the browser to keep and send back.

```
1. Rails → Browser:   Set-Cookie: _myapp_session=abc123; Path=/; Secure; HttpOnly; SameSite=Lax
2. Browser → Rails:   Cookie: _myapp_session=abc123          ← on every later request, automatically
```

| Attribute | Simple meaning | Example |
|---|---|---|
| `Expires` / `Max-Age` | When to delete it. Without one → **session cookie** (deleted when the browser closes) | `Max-Age=86400` = 1 day |
| `Domain` | Which hosts get it | `Domain=myapp.com` → also sent to `api.myapp.com` |
| `Path` | Which URL paths get it | `Path=/admin` → only `/admin/...` |
| `Secure` | Only sent over HTTPS | |
| `HttpOnly` | **JS can't read it** (`document.cookie` won't show it) → safe from XSS theft | Rails session cookie |
| `SameSite=Strict` | Never sent when another site triggers the request | |
| `SameSite=Lax` (default) | Sent when the user clicks a link to your site, not on other sites' background `fetch`/forms | |
| `SameSite=None` | Always sent cross-site; **requires `Secure`** | Needed for a frontend on another domain using cookie login |

- **First-party cookie** = from the site in the address bar. **Third-party** = from another domain on that page (ads, trackers); browsers increasingly block these.
- **XSS** (cross-site scripting) = attacker's JS running on your page. It can read anything JS can read → `HttpOnly` protects cookies, nothing protects localStorage.
- **CSRF** (cross-site request forgery) = another site making your browser send a request with your cookie. `SameSite` + Rails CSRF tokens protect against it.

Rails example:
```ruby
cookies[:theme] = { value: "dark", expires: 1.year }                  # readable by JS
cookies.encrypted[:user_id] = { value: user.id, httponly: true, secure: true, same_site: :lax }
session[:user_id] = user.id     # stored inside the encrypted _app_session cookie
```

### localStorage and sessionStorage

```js
localStorage.setItem("theme", "dark");
localStorage.getItem("theme");                        // "dark"
localStorage.setItem("cart", JSON.stringify([1, 2])); // strings only → JSON for objects
JSON.parse(localStorage.getItem("cart"));             // [1, 2]
```

| | localStorage | sessionStorage |
|---|---|---|
| Lives until | Deleted by JS or the user | The tab is closed |
| Shared between tabs | Yes (same origin) | No, one tab only |

- One box **per origin** (Step 4): `localhost:5173` and `localhost:3000` have different boxes.
- **Synchronous**: reading/writing blocks the main thread briefly → keep it small.
- **IndexedDB** = a bigger, asynchronous browser database for lots of structured data (offline apps).
- **Token storage trade-off:** a JWT in localStorage is easy to send (`Authorization: Bearer ...`) but **stealable by XSS**; a JWT in an `HttpOnly` cookie can't be read by JS but needs `SameSite`/CSRF care.

### HTTP cache

**HTTP cache** = the browser keeps a copy of a response and reuses it instead of downloading again.
The server controls it with **response headers**.

| `Cache-Control` value | Meaning | Use for |
|---|---|---|
| `max-age=31536000, immutable` | Reuse for a year, never re-check | Fingerprinted assets: `app-3f9a1c.js` |
| `max-age=60` | Reuse for 60 s, then ask again | Data that can be a minute old |
| `no-cache` | Keep a copy, but **ask the server first** every time | Pages that change; uses ETag |
| `no-store` | **Never** save a copy | Bank pages, sensitive data |
| `private` | Only the user's browser may cache (not a CDN/proxy) | Per-user API responses |
| `public` | CDNs and proxies may cache too | Public images, assets |

**Revalidation with ETag** (you already did this in Rails with `fresh_when`):
```
1st:  Rails → 200 OK, ETag: "v42", body (50 KB)
2nd:  Browser → If-None-Match: "v42"
      Rails  → 304 Not Modified, no body     ← "your copy is still good"
```
- **ETag** = a fingerprint of the response content. **304** = "use your copy".
- `Last-Modified` / `If-Modified-Since` = the same idea with a date.
- **Fingerprinting** = putting a content hash in the filename (`app-3f9a1c.js`). New content → new name → the cache can't serve an old file. Vite and the Rails asset pipeline both do this.
- **Memory cache vs disk cache**: DevTools Network shows `(memory cache)` or `(disk cache)` in the Size column for responses that never hit the network.

Rails examples:
```ruby
expires_in 1.hour, public: true                 # Cache-Control: max-age=3600, public
fresh_when etag: @order, last_modified: @order.updated_at   # 304 if unchanged
response.headers["Cache-Control"] = "no-store"  # never cache
```

**Coming from Rails:** `Set-Cookie`, `Cache-Control` and `ETag` are headers you already send — the browser is what stores and obeys them.

## Step 6 — DevTools: Elements, Network, Performance, Application

Open: right-click → **Inspect**, or `Cmd + Option + I`. Command menu: `Cmd + Shift + P`.

| Panel | Shows | Day 1 concept |
|---|---|---|
| Elements | The **live DOM** + styles | DOM, CSSOM, computed style, layout |
| Network | Every request, in time order | DNS/TCP/TLS, TTFB, caching, CORS, cookies |
| Performance | What the main thread did, frame by frame | Parse, layout, paint, long JS, jank |
| Application | Stored data | Cookies, localStorage, cache |

### Elements

- Left: the **DOM tree** (live, after JS ran and HTML errors were repaired). Double-click to edit text or attributes.
- **Styles** tab: every CSS rule that matches, crossed-out = overridden (the cascade). Click a value to change it live.
- **Computed** tab: final values, including browser defaults.
- **Box model** diagram: content → padding → border → margin, with sizes (layout).
- **Event Listeners** tab: which JS handlers are attached to the element.
- `:hov` button: force `:hover`/`:focus` to inspect those styles.
- **View Page Source** (`Cmd + Option + U`) = the HTML the **server sent**. Elements = the DOM **now**.
  Empty `<div id="root"></div>` in source but a full tree in Elements → JS built the page (CSR).

### Network

Tick **Disable cache** (while DevTools is open) and **Preserve log** (keep requests across reloads).

| Column | Meaning | Example |
|---|---|---|
| Status | HTTP status | `200`, `304`, `(failed)`, `(blocked:...)`, `CORS error` |
| Type | Resource type | `document`, `script`, `stylesheet`, `fetch`, `preflight` |
| Initiator | What caused the request | `index.html:12`, `app.js:88` |
| Size | Transferred size, or where it came from | `14.2 kB`, `(memory cache)`, `(disk cache)` |
| Time | Total time | `230 ms` |
| Waterfall | When it started and how long each phase took | the bar chart |

**Waterfall** = a bar chart of requests over time. A bar that starts late because it waited for
another file shows a **dependency chain**. Lines on it: **blue = DOMContentLoaded** (HTML parsed,
`defer` scripts ran), **red = load** (all images, CSS, scripts finished).

Click a request → tabs: **Headers** (request/response headers: `Set-Cookie`, `Cache-Control`,
`Access-Control-Allow-Origin`), **Payload** (params/body sent), **Preview**/**Response** (body),
**Timing**:

| Timing phase | Meaning |
|---|---|
| Queueing / Stalled | Waiting in the browser (too many connections to one host, lower priority) |
| DNS Lookup | Step 1 DNS |
| Initial connection | TCP handshake |
| SSL | TLS handshake |
| Request sent | Uploading the request |
| **Waiting for server response** | **TTFB** — your Rails time |
| Content Download | Receiving the body |

Other tools: filter bar (`Fetch/XHR`, `JS`, `CSS`, `Img`, `Doc`), **throttling** (`Fast 4G`, `Slow 4G`
to feel slow networks), right-click → **Copy as cURL** (replay a request in the terminal),
`Cmd + Shift + P` → "Show request blocking" to block a file and see what breaks.

**Find a render-blocking file:** in the Performance panel's Network track, a request marked
**Render blocking: blocking**, or a `<script>` without `defer`/`async` and the CSS files in `<head>`
that start before the first paint.

### Performance

1. Click **Record and reload** (circular arrow), wait for the load, stop.
2. Read the tracks top to bottom:

| Track | Shows |
|---|---|
| Timings | **FCP** (first text/image), **LCP** (largest content element shown), DCL, L |
| Network | Downloads, render-blocking marked |
| Frames | Each frame; red = dropped (jank) |
| **Main** | Flame chart of main-thread work: what ran, and what it called |

Colours in Main: **yellow = scripting (JS)**, **purple = rendering (Recalculate Style, Layout)**,
**green = painting**, grey = other.
A **long task** = > 50 ms on the main thread, marked with a **red triangle** — that's what makes
the page unresponsive (TTI, Step 3).

- **Flame chart** = bars stacked by "who called whom", wider bar = took longer.
- **LCP** (Largest Contentful Paint) = when the biggest image/text block appeared; a Core Web Vital.
- Use **CPU throttling** (4× slowdown) to see what a cheap phone feels.
- Bottom **Summary** tab: time split into Loading, Scripting, Rendering, Painting.

### Application

| Section | Shows | Example |
|---|---|---|
| Cookies | Each cookie with Domain, Path, Expires, **HttpOnly**, **Secure**, **SameSite** | `_myapp_session` ✓HttpOnly ✓Secure Lax |
| Local Storage / Session Storage | Key/value per origin | `theme: dark` |
| IndexedDB | Browser databases | |
| Cache Storage / Service Workers | Offline caches (PWAs) | |
| Storage → **Clear site data** | Wipe everything for this origin | test logged-out state |

Note: `HttpOnly` cookies **are visible here** (DevTools is not page JS) but not to `document.cookie`.

**Coming from Rails:** Network → request → Headers is where your `Set-Cookie`, `Cache-Control`,
`ETag` and CORS headers show up; "Waiting for server response" is your controller + SQL time.

## Step 7 — Where the HTML is rendered

Clipping: [[Rendering on the web    Articles]]. Every page ends up as HTML — the question is
**who builds it, and when**.

### The simple rule

| Mode | In one line |
|---|---|
| **CSR** | "Give me the JavaScript and I'll build the page in the browser." |
| **SSR** | "Build the initial page on the server, send it to me, then make it interactive." |
| **SSG** | "Build the page ahead of time and serve the generated HTML." |
| **Hydration** | "The HTML already exists; React now attaches its behavior to it." |

For a public, SEO-sensitive listings site, SSR/SSG is usually valuable. For a private, highly
interactive admin dashboard, CSR is often simpler and completely adequate.

### Terms

| Term | Simple meaning |
|---|---|
| Rendering (here) | Turning data + templates/components into HTML |
| Bundle | The big JS file(s) your app is compiled into (`assets/index-3f9a.js`) |
| SPA (single-page application) | One HTML page; JS swaps the content when you navigate |
| MPA (multi-page application) | Every URL is a fresh HTML page from the server |
| CDN | Servers around the world that keep copies of files close to users |
| Edge caching | A CDN serving a cached response from the server nearest the user |
| SEO | Search engine optimisation — making Google able to read and rank your pages |
| Crawler | Google's bot that downloads and reads pages |

**Performance metrics used in the article:**

| Metric | Meaning | Good when |
|---|---|---|
| TTFB | Click → first byte of HTML | Server answers fast |
| FCP | First text/image shown | Content shows early |
| TBT (Total Blocking Time) | Total time the main thread was blocked by long tasks during load | Little JS at load |
| INP (Interaction to Next Paint) | How fast the page reacts to taps/clicks, across the visit | Main thread is free |

### The modes

| Mode | Who builds the HTML, when | User sees first | Typical use |
|---|---|---|---|
| **MPA / server pages** | Server, every request | Full page, no JS needed | Rails ERB, classic sites |
| **CSR** | JS in the browser, after the bundle runs | Blank page / spinner | Dashboards behind login |
| **SSR + hydration** | React on a Node server per request, then hydrated in the browser | Real content before JS | Public pages needing SEO (Next.js) |
| **SSG / static** | Once, at **build** time | Real content from a CDN | Docs, blogs, marketing |
| **ISR** | Static pages rebuilt in the background on a timer/event | Real content, maybe slightly stale | Big catalogues |
| **Prerendering** | Run the SPA at build time, save the first screen as HTML | First screen as HTML, then the SPA boots | SPA with faster FCP |

### Examples

**MPA (Rails ERB)** — the server sends finished HTML:
```erb
<%# app/views/orders/index.html.erb %>
<% @orders.each do |order| %>
  <li><%= order.number %></li>
<% end %>
```

**CSR (a typical `myapp-react`: Vite + React 18)** — server sends an empty shell:
```html
<!-- index.html: View Page Source shows only this -->
<div id="root"></div>
<script type="module" src="/src/index.jsx"></script>
```
```jsx
// src/index.jsx:68
ReactDOM.createRoot(document.getElementById('root')).render(<App />)  // builds the DOM from nothing
```
Rails only sends JSON (`/api/orders`); the browser builds every page.

**SSR + hydration** — server sends HTML **and** the same React code:
```jsx
// browser side
hydrateRoot(document.getElementById('root'), <App />)  // attach to existing HTML, don't rebuild
```

**SSG** — build output is plain files:
```
dist/index.html
dist/blog/how-to-sell-a-car/index.html
dist/blog/car-inspection-checklist/index.html
```

**ISR (Next.js)**:
```js
export const revalidate = 60   // serve the static page, rebuild it in the background at most every 60 s
```

### Each mode's trade-offs (from the clipping)

**SSR**
- ✅ Fast FCP; less JS sent → lower TBT and INP; works on slow phones; browser can parse HTML as it streams in.
- ❌ Server does work on **every** request → higher TTFB and compute cost.
- React's old `renderToString()` is **synchronous** (blocks until the whole page is built).
  Newer `renderToPipeableStream()` **streams** chunks; handles **backpressure** (slowing down when the browser can't receive fast enough).
- Making it fast may need **component caching**, **memoization** (remember a result instead of recomputing), **HTML caching**.
- Good for **personalised** pages (per-user data) — static can't do those.
- **Hybrid** is fine: Netflix server-renders landing pages and **prefetches** (downloads early) JS for interactive pages.
- Tools: React (Next.js), Vue (Nuxt), Angular (Universal).

**Static (SSG)**
- ✅ Fast **and consistent** TTFB (no work per request), fast FCP, can be served from CDNs worldwide.
- ❌ One HTML file **per URL**, made in advance — hard when there are millions of URLs or you can't predict them.
- Tools: Gatsby, Next.js static export, 11ty, Jekyll.
- **Static vs prerendered — test:** disable JS (`Cmd+Shift+P` → "Disable JavaScript") and reload.
  Static page: mostly still works. Prerendered SPA: links work, most of the page is dead.
- **Progressive enhancement** = build a page that works with plain HTML first, then add JS on top.

**CSR**
- ✅ Simple hosting, smooth app-like navigation after load.
- ❌ JS grows as the app grows (libraries, **polyfills** = code adding missing features to old browsers, **third-party** scripts = analytics/ads), hurting TBT/INP and FCP.
- Fixes:
  - **JS budget** = a size limit you agree to stay under
  - `<link rel="preload">` for critical scripts/data
  - **Code splitting** = break the bundle into pieces per page: `const Reports = lazy(() => import('./Reports'))`
  - **Lazy loading** = download a piece only when needed
  - **PRPL** pattern = **P**reload important resources, **R**ender the first route fast, **P**re-cache the rest, **L**azy-load later routes
  - **App shell caching** = cache the common frame (header, sidebar) with a **service worker** in **CacheStorage**, so repeat visits open instantly
- **Service worker** = a script the browser runs in the background between your page and the network; can serve cached responses (offline). **PWA** (progressive web app) = a site using these to behave like an installed app.

**SSR + rehydration — the problem: "one app for the price of two"**

The server sends three things in one document:
```html
<div id="root"><h1>Toyota Corolla 2019</h1><button>Call seller</button></div>  <!-- 1. the HTML -->
<script>window.__DATA__ = {"car":{"title":"Toyota Corolla 2019","price":3500000}}</script> <!-- 2. the data, again -->
<script src="/bundle.js"></script>                                              <!-- 3. the whole app, again -->
```
- **Serialize** = turn data into text (JSON) so it can be embedded in the page.
- The page **looks ready** but the button does nothing until `bundle.js` downloads and runs —
  on a slow phone that can be a long time (the article says minutes on mobile).
- **Hydration** = React attaches event handlers and state to the existing HTML. Assumes the DOM won't change.
- **Rehydration** = often used to mean the same, but implies updating the DOM again later with new state.
- **Hydration mismatch** = server and browser produced different HTML; React must throw that part away and re-render:
  ```jsx
  <p>{new Date().toLocaleTimeString()}</p>                  // server time ≠ browser time
  <p>{Math.random()}</p>                                     // different number each run
  <p>{typeof window === "undefined" ? "server" : "client"}</p> // different on purpose
  ```
- A common pitfall: the client's first render needs data that isn't ready (an unresolved **Promise**
  = a value that will arrive later) → the server DOM is destroyed and rebuilt.

**Newer improvements**

| Technique | Simple meaning |
|---|---|
| **Streaming SSR** | Send HTML in chunks; the shell arrives first, slow parts fill in as their **Suspense boundaries** (React's "loading…" placeholders) resolve |
| **Progressive hydration** | Hydrate important parts first, low-priority parts later |
| **Partial hydration** | Don't ship JS at all for parts that never change (hard to do) |
| **Trisomorphic rendering** | Streaming SSR for the first load; then a **service worker** renders later pages in the browser, sharing the same templates |
| **React Server Components** | Components that run **only on the server**; their code never reaches the browser (needs Next.js-style framework) |

A plain **Vite SPA** (like `myapp-react`) is CSR and uses none of these.

### SEO

- Crawlers **can** run JS, but with limits (delays, timeouts) → SSR/SSG are safer for public pages.
- **Dynamic rendering** = send crawlers a server-rendered version and users the CSR version.

### Choosing — example

| Site | Pick | Why |
|---|---|---|
| Public car listings (classifieds site) | **SSR or SSG/ISR** | Google must read every listing; users arrive on slow phones from search; fast FCP sells |
| Internal admin tool (MyApp admin) | **CSR** | Behind login → no SEO; same users daily → bundle cached; heavy interaction |
| Blog / docs | **SSG** | Rarely changes, cheapest and fastest from a CDN |
| User dashboard with live data | **CSR or SSR** | Personalised → can't be static |

The article's conclusion: **measure first**, prefer static or server rendering where it gets you most
of the way, and ship HTML with as little JS as possible.

**Coming from Rails:** ERB (and Turbo) = server rendering. A Vite React app flips it: Rails sends only JSON.

---

## Clipping coverage

**[[Populating the page how browsers work]] (MDN)**

- [x] Overview: latency, single-threaded browser → Steps 1, 3
- [x] DNS lookup, per-hostname lookups, mobile latency → Step 1
- [x] TCP handshake (SYN, SYN-ACK, ACK) → Step 1
- [x] TLS negotiation, cipher suite, round-trip counts → Step 1
- [x] Response, TTFB, first 14 KB → Step 1
- [x] Congestion control: RWND, CWND, slow start, ssthresh → Step 1
- [x] Parsing, DOM, tokenization, blocking scripts → Step 2
- [x] Preload scanner, async/defer, CSS blocks JS → Step 2
- [x] CSSOM, cascade, user-agent styles, "Recalculate Style" → Step 2
- [x] JavaScript compilation (AST, bytecode), web workers → Steps 2, 3
- [x] Accessibility tree (AOM) → Step 2
- [x] Style / render tree, `display: none` vs `visibility: hidden` → Step 2
- [x] Layout and reflow, missing image dimensions → Step 2
- [x] Paint, First Meaningful Paint, 16.67 ms, layers (video, canvas, opacity, transform, will-change) → Steps 2, 3
- [x] Compositing, layer memory cost → Step 3
- [x] Interactivity, TTI, FCP, 50 ms, 2 MB script example → Step 3

**[[Inside look at modern web browser (part 3)    Blog]] (Chrome)**

- [x] Renderer process and its threads (main, worker, compositor, raster) → Step 3
- [x] DOM construction, forgiving HTML parsing → Step 2
- [x] Subresource loading, preload scanner → Step 2
- [x] JS blocks parsing (`document.write`) → Step 2
- [x] Hints: async, defer, modules, `<link rel="preload">` → Step 2
- [x] Style calculation, computed style, default stylesheet → Step 2
- [x] Layout tree (pseudo-elements, `display: none`) → Step 2
- [x] Paint records, z-index order → Step 2
- [x] Pipeline cost, jank, `requestAnimationFrame`, Web Workers → Step 3
- [x] Compositing vs naive rasterizing → Step 3
- [x] Layer tree, `will-change`, too many layers → Step 3
- [x] Tiles, raster threads, GPU memory, viewport priority, zoom tilings → Step 3
- [x] Draw quads, compositor frame, IPC to browser process, GPU → Step 3
- [x] Compositor-only animations → Step 3

**[[Rendering on the web    Articles]] (web.dev)**

- [x] Terminology: SSR, CSR, prerendering, hydration, rehydration → Step 7
- [x] Metrics: TTFB, FCP, INP, TBT → Step 7
- [x] SSR: fast FCP, less JS, higher TTFB, streaming parsing, hybrid (Netflix), Next/Nuxt/Angular → Step 7
- [x] Static rendering: build time, CDN, one file per URL, static vs prerendering test, progressive enhancement → Step 7
- [x] SSR vs static: compute cost, `renderToString` vs streaming, component caching, memoization, HTML caching, personalisation, PWA → Step 7
- [x] CSR: JS budget, preload, PRPL, code splitting, lazy loading, app shell, service worker, CacheStorage → Step 7
- [x] Rehydration: one app for the price of two, serialized data, looks-ready-but-isn't → Step 7
- [x] Streaming SSR, progressive / partial rehydration, trisomorphic rendering → Step 7
- [x] SEO, dynamic rendering, conclusion → Step 7

**[[Same-origin policy]] and [[Using HTTP cookies]] (MDN)** — coverage check pending.

## Step 11 — Connect everything

_To be written at the end of the day._
