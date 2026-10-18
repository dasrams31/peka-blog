# peka-blog

Peka AI blog — `blog.peka.ai.id`. A lightweight Flask blog that mirrors the
spec-sheet design of `peka.ai.id` (light theme, `#f3f3f0` background,
`#111111` ink, `#ffd60a` accent, Inter Tight + Space Mono).

## Stack

- Flask 3.1.3 (stdlib + Flask only), SQLite for comments
- Serves on `127.0.0.1:18102` locally; production traffic arrives through a
  reverse SSH tunnel (`peka-blog-tunnel.service`) → Caddy vhost
  `blog.peka.ai.id` on the edge server with automatic Let's Encrypt TLS.

## Content model

Blog posts are JSON files written by the Peka AI content engine (see
`dasrams31/peka-content`) into `/home/hatch/workspace/peka-content/blog/`:

```json
{
  "slug": "short-keywords",
  "title": "Blog title",
  "date": "2026-10-18",
  "datetime": "2026-10-18 19:36",
  "excerpt": "1-2 sentence summary",
  "image": "cover-filename.png",
  "body_html": "<p>...</p>",
  "links": {"instagram": "url", "threads": "url", "facebook": "url"}
}
```

The app scans that directory on every request, so new posts appear without a
restart. Cover images are served from
`/home/hatch/workspace/peka-content/images/` via `/covers/<file>`.

## Routes

| Route            | Description                                      |
|------------------|--------------------------------------------------|
| `/`              | Archive index (numbered 01, 02, ...)             |
| `/p/<slug>`      | Post page with cover, comment section            |
| `/covers/<file>` | Cover images from the content engine             |
| `/api/comments`  | POST new comment (rate limit 5/hour/IP, honeypot) |
| `/sitemap.xml`   | Auto-generated sitemap                           |
| `/robots.txt`    | Points to the sitemap                            |
| `/healthz`       | Health check (`{"ok": true, "posts": N}`)        |

## Services (systemd, user units)

- `peka-blog.service` — Flask on port 18102
- `peka-blog-tunnel.service` — `ssh -R 127.0.0.1:18088:127.0.0.1:18102`

Both are registered in `recover-after-reboot.sh`.

## Local run

```bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt
venv/bin/python app.py
```
