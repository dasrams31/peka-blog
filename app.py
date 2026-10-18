#!/usr/bin/env python3
"""Peka AI blog — blog.peka.ai.id. Spec-sheet aesthetic mirroring peka.ai.id."""
import html
import json
import os
import re
import sqlite3
import time
from datetime import datetime

from flask import Flask, Response, abort, redirect, request, send_from_directory

BASE = os.path.dirname(os.path.abspath(__file__))
BLOG_DIR = "/home/hatch/workspace/peka-content/blog"
IMG_DIR = "/home/hatch/workspace/peka-content/images"
DB = os.path.join(BASE, "comments.db")

app = Flask(__name__)

SLUG_RE = re.compile(r"^[a-z0-9-]{1,80}$")
FILE_RE = re.compile(r"^[A-Za-z0-9._-]{1,80}$")

CSS = """
:root{
  --bg:#f3f3f0; --fg:#111111; --muted:#5c5c5a; --line:#d6d6d2;
  --accent:#ffd60a; --neu:#b8b8b4; --radius:2px;
  --font:"Inter Tight",system-ui,-apple-system,"Segoe UI",sans-serif;
  --mono:ui-monospace,"SF Mono","Cascadia Mono",Menlo,Consolas,monospace;
  --frame-w:1120px; --gutter:28px;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font-family:var(--font);font-size:16px;line-height:1.6;-webkit-font-smoothing:antialiased}
h1,h2,h3{margin:0;font-weight:500;line-height:1.02;letter-spacing:-0.04em}
h1{font-size:clamp(2.4rem,6vw,4.5rem)}
h2{font-size:clamp(1.5rem,3.5vw,2.4rem)}
p{margin:0 0 1em}
a{color:inherit}
.mono{font-family:var(--mono);font-size:.75rem;text-transform:uppercase;letter-spacing:.04em}
.muted{color:var(--muted)}
.frame{width:min(100%,var(--frame-w));margin:0 auto;border-left:1px solid var(--line);border-right:1px solid var(--line)}
.nav{position:sticky;top:0;z-index:50;background:var(--bg);border-bottom:1px solid var(--line)}
.nav-inner{display:flex;align-items:center;gap:20px;height:60px;padding:0 var(--gutter)}
.brand{display:inline-flex;align-items:center;gap:10px;font-weight:600;letter-spacing:-0.03em;text-decoration:none;font-size:1.05rem}
.brand .logo{width:30px;height:30px;border-radius:50%;border:1px solid var(--line);background:#111}
.nav-links{margin-left:auto;display:flex;gap:18px;align-items:center}
.nav-links a{text-decoration:none;font-size:.9rem;color:var(--muted)}
.nav-links a:hover{color:var(--fg)}
.btn-site{display:inline-flex;align-items:center;min-height:38px;padding:0 16px;background:var(--accent);color:var(--fg)!important;border:1px solid var(--fg);border-radius:var(--radius);font-weight:600;font-size:.85rem!important}
.btn-site:hover{background:var(--fg);color:var(--bg)!important}
section.block{padding:56px var(--gutter);border-bottom:1px solid var(--line);position:relative}
.eyebrow{display:flex;align-items:center;gap:10px;color:var(--muted);margin-bottom:18px}
.eyebrow .tick{width:8px;height:8px;background:var(--accent);border:1px solid var(--fg)}
.lead{font-size:1.15rem;max-width:60ch;color:var(--muted);margin-top:16px}
.btn{display:inline-flex;align-items:center;gap:10px;min-height:44px;padding:0 20px;background:var(--fg);color:var(--bg);border:1px solid var(--fg);border-radius:var(--radius);font:inherit;font-weight:500;font-size:.95rem;text-decoration:none;cursor:pointer}
.btn:hover{background:transparent;color:var(--fg)}
.postrow{display:grid;grid-template-columns:64px 1fr 200px;gap:20px;align-items:center;padding:26px 0;border-bottom:1px solid var(--line);text-decoration:none}
.postrow:hover .ptitle{text-decoration:underline;text-underline-offset:4px}
.pnum{font-family:var(--mono);font-size:.85rem;color:var(--muted)}
.ptitle{display:block;font-size:1.5rem;letter-spacing:-0.03em;font-weight:500;margin:6px 0}
.pexcerpt{display:block;color:var(--muted);font-size:.95rem}
.pthumb{width:200px;height:120px;object-fit:cover;border:1px solid var(--line);border-radius:var(--radius);background:#fff}
.cover{width:100%;aspect-ratio:16/9;max-height:360px;object-fit:cover;border:1px solid var(--line);border-radius:var(--radius);margin:28px 0;background:#fff}
.body{font-size:1.08rem;max-width:68ch}
.body p{margin-bottom:1.1em}
.links-row{display:flex;flex-wrap:wrap;gap:12px;margin-top:28px}
.tag{display:inline-block;padding:6px 12px;border:1px solid var(--fg);border-radius:var(--radius);font-family:var(--mono);font-size:.72rem;text-transform:uppercase;letter-spacing:.04em;text-decoration:none;background:var(--accent)}
.tag.ghost{background:transparent}
.cmt{border:1px solid var(--line);border-radius:var(--radius);padding:16px 18px;margin-bottom:12px;background:#fff}
.cmt-head{display:flex;gap:12px;align-items:baseline;margin-bottom:6px}
.cmt-name{font-weight:600}
.cmt-date{font-family:var(--mono);font-size:.7rem;color:var(--muted);text-transform:uppercase}
form.cform{display:grid;gap:12px;max-width:560px;margin-top:20px}
input,textarea{font:inherit;padding:12px 14px;border:1px solid var(--fg);border-radius:var(--radius);background:#fff;color:var(--fg);width:100%}
textarea{min-height:120px;resize:vertical}
.hp{position:absolute;left:-9999px;top:-9999px}
.footer{padding:36px var(--gutter);display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap;color:var(--muted)}
.back{display:inline-block;margin-bottom:16px;text-decoration:none;font-size:.78rem;color:var(--muted)}
.back:hover{color:var(--fg);text-decoration:underline;text-underline-offset:4px}
.rate{border:1px solid var(--line);border-radius:var(--radius);background:#fff;padding:20px 22px;margin-top:28px}
.rate-top{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-bottom:10px}
.stars{display:flex;gap:4px}
.stars button{background:none;border:0;padding:8px;cursor:pointer;line-height:0;min-width:44px;min-height:44px}
.stars button:disabled{cursor:default}
.stars svg{width:28px;height:28px;stroke:var(--fg);stroke-width:1.4}
.stars button.on svg{fill:var(--accent)}
.stars button:not(.on) svg{fill:none}
.rate-info{font-size:.72rem}
@media(max-width:680px){
  .postrow{grid-template-columns:44px 1fr}
  .pthumb{display:none}
  section.block{padding:36px var(--gutter)}
  .nav-links a.hide-m{display:none}
  .nav-links{gap:14px}
  .brand{font-size:.95rem}
}
"""

def db():
    c = sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS comments(
      id INTEGER PRIMARY KEY AUTOINCREMENT, slug TEXT NOT NULL,
      name TEXT NOT NULL, body TEXT NOT NULL, ip TEXT, created_at TEXT NOT NULL)""")
    c.execute("CREATE INDEX IF NOT EXISTS idx_cslug ON comments(slug)")
    c.execute("""CREATE TABLE IF NOT EXISTS ratings(
      slug TEXT NOT NULL, ip TEXT NOT NULL, stars INTEGER NOT NULL,
      created_at TEXT NOT NULL, PRIMARY KEY (slug, ip))""")
    return c

def client_ip():
    return request.headers.get("X-Forwarded-For", request.remote_addr or "").split(",")[0].strip()

BULAN = ["", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
         "Juli", "Agustus", "September", "Oktober", "November", "Desember"]

def fmt_date(d):
    """'2026-10-18' -> '18 Oktober 2026' (no dashes, human readable)."""
    try:
        y, m, dd = str(d).split("-")
        return f"{int(dd)} {BULAN[int(m)]} {y}"
    except (ValueError, AttributeError, IndexError):
        return d or ""

def rating_stats(c, slug, ip):
    row = c.execute("SELECT AVG(stars), COUNT(*) FROM ratings WHERE slug=?", (slug,)).fetchone()
    mine = c.execute("SELECT stars FROM ratings WHERE slug=? AND ip=?", (slug, ip)).fetchone()
    avg = round(row[0], 1) if row[0] else 0
    return avg, row[1], (mine[0] if mine else 0)

def rating_map():
    c = db()
    rows = c.execute("SELECT slug, AVG(stars), COUNT(*) FROM ratings GROUP BY slug").fetchall()
    c.close()
    return {s: (round(a, 1), n) for s, a, n in rows}

def load_posts():
    posts = []
    if not os.path.isdir(BLOG_DIR):
        return posts
    for fn in os.listdir(BLOG_DIR):
        if not fn.endswith(".json"):
            continue
        try:
            with open(os.path.join(BLOG_DIR, fn), encoding="utf-8") as f:
                p = json.load(f)
            if SLUG_RE.match(p.get("slug", "")):
                posts.append(p)
        except (OSError, ValueError):
            continue
    posts.sort(key=lambda p: p.get("datetime", ""), reverse=True)
    return posts

def get_post(slug):
    for p in load_posts():
        if p["slug"] == slug:
            return p
    return None

def shell(title, body_html):
    t = f"{html.escape(title)} · Peka AI Blog" if title != "Arsip" else "Peka AI Blog · info AI & bansos harian"
    return f"""<!doctype html><html lang="id"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#f3f3f0">
<meta name="description" content="Arsip tulisan Peka AI: info AI terbaru, tools, project, dan info bansos.">
<link rel="icon" href="/static/favicon.ico" sizes="48x48">
<link rel="icon" type="image/png" sizes="32x32" href="/static/favicon-32.png">
<link rel="icon" type="image/png" sizes="96x96" href="/static/favicon-96.png">
<link rel="apple-touch-icon" href="/static/apple-touch-icon.png">
<title>{t}</title>
<style>{CSS}</style></head><body>
<nav class="nav"><div class="frame"><div class="nav-inner">
<a class="brand" href="/"><img class="logo" src="/static/logo.png" alt="Logo Peka AI">peka.ai.id <span class="muted mono">/ blog</span></a>
<div class="nav-links"><a class="hide-m" href="https://www.instagram.com/peka.ai.id">Instagram</a><a class="hide-m" href="https://www.threads.com/@peka.ai.id">Threads</a><a class="btn-site" href="https://peka.ai.id">Website resmi</a></div>
</div></div></nav>
<div class="frame">{body_html}
<footer class="footer"><span class="mono">peka.ai.id / blog</span><span class="mono muted">info ai &amp; bansos, dikurasi tiap hari</span></footer>
</div></body></html>"""

@app.route("/")
def index():
    posts = load_posts()
    rmap = rating_map()
    rows = []
    for i, p in enumerate(posts, 1):
        img = ""
        if FILE_RE.match(p.get("image", "")):
            img = f'<img class="pthumb" src="/covers/{p["image"]}" alt="" loading="lazy">'
        meta = fmt_date(p.get("date", ""))
        if p["slug"] in rmap:
            avg, n = rmap[p["slug"]]
            meta += f" · {avg}/5 ({n} penilaian)"
        rows.append(f"""<a class="postrow" href="/p/{p['slug']}">
<span class="pnum">{i:02d}</span>
<span><span class="mono muted" style="display:block;margin-bottom:6px">{html.escape(meta)}</span>
<span class="ptitle">{html.escape(p.get('title',''))}</span>
<span class="pexcerpt">{html.escape(p.get('excerpt',''))}</span></span>
{img}</a>""")
    body = f"""<section class="block">
<p class="mono eyebrow"><span class="tick"></span><span>peka.ai.id / blog</span></p>
<h1>Sinyal AI,<br>dikutip <span style="background:var(--accent);padding:0 .1em">peka</span>.</h1>
<p class="lead">Arsip setiap postingan Peka AI: info AI terbaru, tools, project, dan info bansos. Sama dengan yang tayang di Instagram dan Threads. Di sini versi lengkapnya, plus kolom komentar.</p>
</section>
<section class="block"><p class="mono muted" style="margin-bottom:8px">arsip / {len(posts)} tulisan</p>
{''.join(rows) if rows else '<p class="muted">Belum ada tulisan.</p>'}</section>"""
    return shell("Arsip", body)

@app.route("/p/<slug>")
def post(slug):
    if not SLUG_RE.match(slug):
        abort(404)
    p = get_post(slug)
    if not p:
        abort(404)
    img = ""
    if FILE_RE.match(p.get("image", "")):
        img = f'<img class="cover" src="/covers/{p["image"]}" alt="{html.escape(p.get("title",""))}">'
    links = []
    for label, url in (p.get("links") or {}).items():
        if url and url.startswith("http"):
            links.append(f'<a class="tag ghost" href="{html.escape(url)}">{html.escape(label)}</a>')
    ip = client_ip()
    c = db()
    rav, rcount, mine = rating_stats(c, slug, ip)
    cmts = c.execute("SELECT name, body, created_at FROM comments WHERE slug=? ORDER BY id ASC", (slug,)).fetchall()
    c.close()
    chtml = "".join(
        f'<div class="cmt"><div class="cmt-head"><span class="cmt-name">{html.escape(n)}</span>'
        f'<span class="cmt-date">{html.escape(d)}</span></div><p>{html.escape(b)}</p></div>'
        for n, b, d in cmts) or '<p class="muted">Belum ada komentar. Jadi yang pertama.</p>'
    body = f"""<section class="block">
<a class="mono back" href="/">← arsip</a>
<p class="mono eyebrow"><span class="tick"></span><span>{html.escape(fmt_date(p.get('date','')))}</span></p>
<h1 style="max-width:20ch">{html.escape(p.get('title',''))}</h1>
{img}
<div class="body">{p.get('body_html','')}</div>
<div class="links-row"><span class="mono muted" style="align-self:center">tayang juga di:</span>{''.join(links)}</div>
{rating_block(slug, rav, rcount, mine)}
</section>
<section class="block">
<p class="mono eyebrow"><span class="tick"></span><span>komentar / {len(cmts)}</span></p>
{chtml}
<form class="cform" method="post" action="/api/comments">
<input type="hidden" name="slug" value="{html.escape(slug)}">
<input class="hp" type="text" name="website" tabindex="-1" autocomplete="off">
<input type="text" name="name" maxlength="40" placeholder="Nama" required>
<textarea name="body" maxlength="1000" placeholder="Tulis komentar..." required></textarea>
<button class="btn" type="submit">Kirim komentar</button>
</form></section>"""
    return shell(p.get("title", ""), body)

@app.route("/covers/<filename>")
def cover(filename):
    if not FILE_RE.match(filename):
        abort(404)
    return send_from_directory(IMG_DIR, filename)

STAR_SVG = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2.5l2.95 6.26 6.55.72-4.9 4.55 1.35 6.47L12 17.4l-5.95 3.1 1.35-6.47-4.9-4.55 6.55-.72z"/></svg>'

def rating_block(slug, avg, count, mine):
    info = f"{avg} dari 5 · {count} penilaian" if count else "belum ada penilaian"
    btns = "".join(
        f'<button type="button" data-stars="{i}" class="{"on" if i <= mine else ""}" aria-label="{i} bintang">{STAR_SVG}</button>'
        for i in range(1, 6))
    return f"""<div class="rate" data-slug="{html.escape(slug)}">
<div class="rate-top"><p class="mono">kasih rating tulisan ini</p><p class="mono muted rate-info" data-role="info">{info}</p></div>
<div class="stars" data-role="stars">{btns}</div></div>
<script>(function(){{var box=document.querySelector('.rate');if(!box)return;
var slug=box.dataset.slug,stars=box.querySelector('[data-role=stars]'),info=box.querySelector('[data-role=info]');
function paint(n){{stars.querySelectorAll('button').forEach(function(b){{b.classList.toggle('on',+b.dataset.stars<=n);}});}}
stars.addEventListener('click',function(e){{var b=e.target.closest('button');if(!b||b.disabled)return;
var v=+b.dataset.stars;stars.querySelectorAll('button').forEach(function(x){{x.disabled=true;}});
fetch('/api/rate',{{method:'POST',headers:{{'Content-Type':'application/x-www-form-urlencoded'}},body:'slug='+encodeURIComponent(slug)+'&stars='+v}})
.then(function(r){{return r.json();}}).then(function(d){{
if(d.ok){{paint(d.mine);info.textContent=d.avg+' dari 5 · '+d.count+' penilaian';}}
stars.querySelectorAll('button').forEach(function(x){{x.disabled=false;}});}})
.catch(function(){{stars.querySelectorAll('button').forEach(function(x){{x.disabled=false;}});}});}});}})();</script>"""

@app.route("/api/rate", methods=["POST"])
def rate():
    slug = request.form.get("slug", "")
    try:
        stars = int(request.form.get("stars", "0"))
    except ValueError:
        stars = 0
    if not SLUG_RE.match(slug) or not get_post(slug) or not 1 <= stars <= 5:
        abort(400)
    ip = client_ip()
    c = db()
    n = c.execute("SELECT COUNT(*) FROM ratings WHERE ip=? AND created_at > datetime('now','-1 hour')", (ip,)).fetchone()[0]
    if n >= 20:
        c.close()
        return Response(json.dumps({"ok": False}), 429, mimetype="application/json")
    c.execute("""INSERT INTO ratings(slug,ip,stars,created_at) VALUES(?,?,?,datetime('now','localtime'))
      ON CONFLICT(slug,ip) DO UPDATE SET stars=excluded.stars, created_at=excluded.created_at""",
      (slug, ip, stars))
    c.commit()
    avg, count, mine = rating_stats(c, slug, ip)
    c.close()
    return {"ok": True, "avg": avg, "count": count, "mine": mine}
def add_comment():
    slug = request.form.get("slug", "")
    name = request.form.get("name", "").strip()
    cbody = request.form.get("body", "").strip()
    if request.form.get("website"):
        return redirect(f"/p/{slug}", 303)
    if not SLUG_RE.match(slug) or not get_post(slug):
        abort(404)
    if not name or not cbody or len(name) > 40 or len(cbody) > 1000:
        abort(400)
    ip = client_ip()
    c = db()
    n = c.execute("SELECT COUNT(*) FROM comments WHERE ip=? AND created_at > datetime('now','-1 hour')", (ip,)).fetchone()[0]
    if n >= 5:
        c.close()
        return Response("Terlalu banyak komentar, coba lagi nanti.", 429)
    c.execute("INSERT INTO comments(slug,name,body,ip,created_at) VALUES(?,?,?,?,datetime('now','localtime'))",
              (slug, name, cbody, ip))
    c.commit()
    c.close()
    return redirect(f"/p/{slug}", 303)

@app.route("/robots.txt")
def robots():
    txt = "User-agent: *\nAllow: /\nSitemap: https://blog.peka.ai.id/sitemap.xml\n"
    return Response(txt, mimetype="text/plain")

@app.route("/sitemap.xml")
def sitemap():
    posts = load_posts()
    urls = ['<url><loc>https://blog.peka.ai.id/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>']
    for p in posts:
        slug = p["slug"]
        lastmod = (p.get("datetime") or p.get("date") or "")[:10]
        lm = f"<lastmod>{lastmod}</lastmod>" if lastmod else ""
        urls.append(f"<url><loc>https://blog.peka.ai.id/p/{slug}</loc>{lm}<changefreq>weekly</changefreq><priority>0.8</priority></url>")
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(urls) + "\n</urlset>"
    return Response(xml, mimetype="application/xml")

@app.route("/api/posts.json")
def posts_json():
    posts = load_posts()
    out = []
    for p in posts:
        img = p.get("image", "")
        out.append({
            "slug": p["slug"],
            "title": p.get("title", ""),
            "date": p.get("date", ""),
            "datetime": p.get("datetime", ""),
            "excerpt": p.get("excerpt", ""),
            "image": f"https://blog.peka.ai.id/covers/{img}" if FILE_RE.match(img) else None,
            "url": f"https://blog.peka.ai.id/p/{p['slug']}",
            "links": p.get("links") or {},
        })
    resp = Response(json.dumps(out, ensure_ascii=False), mimetype="application/json")
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp

@app.route("/healthz")
def healthz():
    return {"ok": True, "posts": len(load_posts())}

if __name__ == "__main__":
    os.makedirs(BLOG_DIR, exist_ok=True)
    db().close()
    app.run(host="127.0.0.1", port=18102)
