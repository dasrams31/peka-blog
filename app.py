#!/usr/bin/env python3
"""Peka AI blog — blog.peka.ai.id. Spec-sheet aesthetic mirroring peka.ai.id."""
import html
import json
import os
import re
import sqlite3
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

from flask import Flask, Response, abort, redirect, request, send_from_directory

SITE = "https://blog.peka.ai.id"

WIB = timezone(timedelta(hours=7))

def wib_now():
    return datetime.now(WIB).strftime("%Y-%m-%d %H:%M:%S")

def wib_hour_ago():
    return (datetime.now(WIB) - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")

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
.block{padding:56px var(--gutter);border-bottom:1px solid var(--line);position:relative}
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
.cover{width:100%;height:auto;display:block;border:1px solid var(--line);border-radius:var(--radius);margin:28px 0;background:#fff}
.slider{position:relative;border:1px solid var(--line);border-radius:var(--radius);margin:28px 0;background:#fff;overflow:hidden}
.strack{display:flex;transition:transform .38s ease}
.strack img{flex:0 0 100%;width:100%;height:auto;display:block}
.sbtn{position:absolute;top:50%;transform:translateY(-50%);background:none;border:0;color:#fff;font-size:2.6rem;line-height:1;cursor:pointer;padding:10px 14px;text-shadow:0 1px 6px rgba(0,0,0,.55);z-index:2}
.sbtn.prev{left:2px}
.sbtn.next{right:2px}
.sbtn:hover{opacity:.75}
.scounter{position:absolute;top:12px;right:12px;background:var(--fg);color:#fff;font-family:var(--mono);font-size:.72rem;padding:5px 10px;border-radius:var(--radius);z-index:2}
.sdots{position:absolute;left:0;right:0;bottom:12px;display:flex;gap:7px;justify-content:center;z-index:2}
.sdots button{width:11px;height:11px;border-radius:50%;border:1px solid var(--fg);background:#fff;padding:0;cursor:pointer}
.sdots button.on{background:var(--accent)}
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
.byline{display:flex;align-items:center;gap:10px;margin:16px 0 0;color:var(--muted);font-size:.82rem;flex-wrap:wrap}
.byline img{width:26px;height:26px;border-radius:50%;border:1px solid var(--line)}
.tagrow{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 18px}
.share-row{display:flex;flex-wrap:wrap;gap:10px;margin-top:26px;align-items:center}
.share-row button{font:inherit;cursor:pointer}
.pnnav{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:26px}
.pnnav a{border:1px solid var(--line);border-radius:var(--radius);background:#fff;padding:14px 16px;text-decoration:none;display:block;color:inherit}
.pnnav a:hover{border-color:var(--fg)}
.pnnav .pn-k{font-size:.68rem}
.pnnav .pn-t{display:block;font-weight:600;margin-top:4px;line-height:1.35;font-size:.95rem}
.pnnav .next{text-align:right}
.featured{display:grid;grid-template-columns:1.1fr 1fr;gap:26px;align-items:center;padding:6px 0 30px;text-decoration:none;color:inherit}
.featured:hover .ptitle{text-decoration:underline;text-underline-offset:4px}
.featured .ptitle{font-size:2rem}
.featured img{width:100%;aspect-ratio:16/10;object-fit:cover;border:1px solid var(--line);border-radius:var(--radius);background:#fff}
.tagfilter{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:6px}
@media(max-width:680px){
  .featured{grid-template-columns:1fr;gap:14px}
  .featured .ptitle{font-size:1.6rem}
  .pnnav{grid-template-columns:1fr}
}
@media(max-width:680px){
  .postrow{grid-template-columns:44px 1fr}
  .pthumb{display:none}
  section.block{padding:36px var(--gutter)}
  .nav-links a.hide-m{display:none}
  .nav-links{gap:14px}
  .brand{font-size:.95rem}
}
#progress{position:fixed;top:0;left:0;height:3px;width:0;background:var(--accent);z-index:200}
.toc{border:1px solid var(--line);border-radius:var(--radius);background:#fff;padding:18px 22px;margin:26px 0;max-width:68ch}
.toc p{margin:0 0 10px}
.toc ol{margin:0;padding-left:20px}
.toc li{margin:5px 0}
.toc a{text-decoration:none;color:var(--muted)}
.toc a:hover{color:var(--fg);text-decoration:underline;text-underline-offset:3px}
.toc a.on{color:var(--fg);font-weight:600}
.body h2,.body h3{scroll-margin-top:84px}
.body code{font-family:var(--mono);font-size:.86em;background:#e7e7e1;border:1px solid var(--line);border-radius:var(--radius);padding:.08em .35em}
.term{background:#111;border:1px solid #111;border-radius:6px;margin:22px 0;overflow:hidden;max-width:68ch}
.term-bar{display:flex;align-items:center;gap:10px;background:#1c1c1c;padding:9px 12px;border-bottom:1px solid #2c2c2c}
.tdots{display:inline-flex;gap:7px}
.tdots i{width:11px;height:11px;border-radius:50%;display:block}
.tdots i:nth-child(1){background:#ff5f57}
.tdots i:nth-child(2){background:#febc2e}
.tdots i:nth-child(3){background:#28c840}
.tlabel{font-family:var(--mono);font-size:.72rem;color:#9a9a94;text-transform:uppercase;letter-spacing:.05em}
.tcopy{margin-left:auto;font-family:var(--mono);font-size:.72rem;text-transform:uppercase;letter-spacing:.05em;background:var(--accent);color:#111;border:1px solid var(--accent);border-radius:var(--radius);padding:5px 12px;cursor:pointer}
.tcopy:hover{background:transparent;color:var(--accent)}
.term pre{margin:0;padding:18px 20px;overflow-x:auto;background:#111}
.term pre code{font-family:var(--mono);font-size:.9rem;line-height:1.6;color:#e8e8e8;background:none;border:0;padding:0;white-space:pre}
.search{display:flex;gap:10px;margin:0 0 18px;max-width:560px}
.search input{flex:1}
.search button{white-space:nowrap}
#toTop{position:fixed;right:18px;bottom:18px;width:44px;height:44px;display:none;align-items:center;justify-content:center;background:var(--accent);color:#111;border:1px solid #111;border-radius:var(--radius);font-size:1.15rem;cursor:pointer;z-index:150}
#toTop.show{display:flex}
.lightbox{position:fixed;inset:0;background:rgba(10,10,10,.92);display:none;align-items:center;justify-content:center;z-index:300;cursor:zoom-out;padding:24px}
.lightbox.open{display:flex}
.lightbox img{max-width:100%;max-height:100%;border:1px solid #333}
.body img{cursor:zoom-in}
#themebtn{background:none;border:1px solid var(--line);border-radius:var(--radius);color:var(--muted);font-family:var(--mono);font-size:.72rem;text-transform:uppercase;letter-spacing:.04em;padding:8px 12px;cursor:pointer}
#themebtn:hover{color:var(--fg);border-color:var(--fg)}
:root[data-theme="dark"]{--bg:#131311;--fg:#f0f0ec;--muted:#a3a3a0;--line:#2e2e2c}
:root[data-theme="dark"] .cmt,:root[data-theme="dark"] .rate,:root[data-theme="dark"] .toc,:root[data-theme="dark"] .pnnav a{background:#1b1b19}
:root[data-theme="dark"] input,:root[data-theme="dark"] textarea{background:#1b1b19;color:var(--fg);border-color:var(--muted)}
:root[data-theme="dark"] .body code{background:#26261f}
:root[data-theme="dark"] .pthumb,:root[data-theme="dark"] .cover,:root[data-theme="dark"] .slider,:root[data-theme="dark"] .featured img{background:#1b1b19}
:root[data-theme="dark"] .brand .logo{background:#f3f3f0}
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

TAG_RE = re.compile(r"^[a-zA-Z0-9 ]{1,24}$")

def post_tags(p):
    tags = []
    for t in (p.get("tags") or []):
        t = str(t).strip()
        if t and TAG_RE.match(t) and t not in tags:
            tags.append(t)
    return tags

def all_tags(posts):
    seen = []
    for p in posts:
        for t in post_tags(p):
            if t not in seen:
                seen.append(t)
    return seen

def reading_time(p):
    text = re.sub(r"<[^>]+>", " ", p.get("body_html", ""))
    words = len(re.findall(r"\S+", text))
    return max(1, round(words / 200))

def cover_img(p, cls):
    img = p.get("image", "")
    if FILE_RE.match(img):
        return f'<img class="{cls}" src="/covers/{img}" alt="{html.escape(p.get("title", ""))}" loading="lazy">'
    return ""

def gallery(p):
    """Post header media: slider when the post JSON carries images[], else the
    single cover. Images render full-width at natural aspect (never cropped)."""
    imgs = p.get("images")
    if not isinstance(imgs, list):
        imgs = []
    imgs = [i for i in imgs if isinstance(i, str) and FILE_RE.match(i)]
    main = p.get("image", "")
    if main and FILE_RE.match(main) and main not in imgs:
        imgs.insert(0, main)
    if len(imgs) <= 1:
        return cover_img(p, "cover")
    title = html.escape(p.get("title", ""))
    slides = "".join(f'<img src="/covers/{i}" alt="{title}" loading="lazy">' for i in imgs)
    dots = "".join(
        f'<button type="button" aria-label="Gambar {k + 1}" class="{"on" if k == 0 else ""}"></button>'
        for k in range(len(imgs)))
    return f"""<div class="slider"><div class="strack">{slides}</div>
<button type="button" class="sbtn prev" aria-label="Gambar sebelumnya">&#8249;</button>
<button type="button" class="sbtn next" aria-label="Gambar berikutnya">&#8250;</button>
<span class="scounter">1 / {len(imgs)}</span>
<div class="sdots">{dots}</div></div>
<script>(function(){{var s=document.querySelector('.slider');if(!s)return;
var track=s.querySelector('.strack'),n=track.children.length,i=0;
var cnt=s.querySelector('.scounter'),dots=s.querySelectorAll('.sdots button');
function go(j){{i=(j+n)%n;track.style.transform='translateX(-'+(i*100)+'%)';cnt.textContent=(i+1)+' / '+n;dots.forEach(function(d,k){{d.classList.toggle('on',k===i);}});}}
s.querySelector('.prev').addEventListener('click',function(){{go(i-1);}});
s.querySelector('.next').addEventListener('click',function(){{go(i+1);}});
dots.forEach(function(d,k){{d.addEventListener('click',function(){{go(k);}});}});
var sx=null;s.addEventListener('touchstart',function(e){{sx=e.touches[0].clientX;}},{{passive:true}});
s.addEventListener('touchend',function(e){{if(sx===null)return;var dx=e.changedTouches[0].clientX-sx;if(Math.abs(dx)>42)go(i+(dx<0?1:-1));sx=null;}},{{passive:true}});
document.addEventListener('keydown',function(e){{if(e.key==='ArrowLeft')go(i-1);if(e.key==='ArrowRight')go(i+1);}});
}})();</script>"""

PRE_RE = re.compile(r"<pre([^>]*)>(.*?)</pre>", re.S | re.I)
CODE_RE = re.compile(r"^<code([^>]*)>(.*)</code>$", re.S | re.I)
HEAD_RE = re.compile(r"<h([23])(\s[^>]*)?>(.*?)</h\1>", re.S | re.I)


def _term(m):
    """Wrap one <pre> block in terminal chrome: window bar, language label,
    copy button (wired up in /static/blog.js)."""
    attrs, inner = m.group(1) or "", m.group(2).strip()
    lang = ""
    lm = re.search(r'data-lang="([\w-]+)"', attrs) or re.search(r"language-([\w-]+)", attrs)
    if lm:
        lang = lm.group(1)
    cm = CODE_RE.match(inner)
    if cm:
        lm2 = re.search(r"language-([\w-]+)", cm.group(1))
        if lm2:
            lang = lm2.group(1)
        code = cm.group(2)
    else:
        code = inner
    label = html.escape(lang) if lang else "terminal"
    cls = f' class="language-{html.escape(lang)}"' if lang else ""
    return (f'<div class="term"><div class="term-bar"><span class="tdots"><i></i><i></i><i></i></span>'
            f'<span class="tlabel">{label}</span>'
            f'<button type="button" class="tcopy">salin</button></div>'
            f"<pre><code{cls}>{code}</code></pre></div>")


def enhance_body(raw):
    """Server-side article enhancements: heading ids + table of contents,
    terminal-style code blocks. Returns (html, toc_html)."""
    toc = []
    seen = {}

    def _head(m):
        lvl, attrs, inner = m.group(1), m.group(2) or "", m.group(3)
        text = re.sub(r"<[^>]+>", "", inner).strip()
        if not text:
            return m.group(0)
        im = re.search(r'id="([^"]+)"', attrs)
        if im:
            hid = im.group(1)
        else:
            base = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:48] or "bagian"
            seen[base] = seen.get(base, 0) + 1
            hid = base if seen[base] == 1 else f"{base}-{seen[base]}"
            attrs = attrs + f' id="{hid}"'
        toc.append((int(lvl), hid, text))
        return f"<h{lvl}{attrs}>{inner}</h{lvl}>"

    out = HEAD_RE.sub(_head, raw)
    out = PRE_RE.sub(_term, out)
    toc_html = ""
    if len(toc) >= 3:
        items = "".join(
            f'<li style="margin-left:{(lvl - 2) * 16}px"><a href="#{hid}" data-toc="{hid}">{html.escape(text)}</a></li>'
            for lvl, hid, text in toc)
        toc_html = (f'<nav class="toc"><p class="mono muted">daftar isi</p>'
                    f"<ol>{items}</ol></nav>")
    return out, toc_html


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

def seo_head(p=None):
    """Per-page SEO: description, canonical, Open Graph, Twitter card, JSON-LD."""
    if p:
        title = p.get("title", "")
        desc = p.get("excerpt", "")
        url = f"{SITE}/p/{p['slug']}"
        img = p.get("image", "")
        img_url = f"{SITE}/covers/{img}" if FILE_RE.match(img) else f"{SITE}/static/logo.png"
        iso = (p.get("datetime") or p.get("date") or "")[:10]
        ld = {
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": title,
            "description": desc,
            "image": img_url,
            "url": url,
            "datePublished": iso,
            "inLanguage": "id",
            "author": {"@type": "Organization", "name": "Peka AI", "url": "https://peka.ai.id"},
            "publisher": {"@type": "Organization", "name": "Peka AI", "url": "https://peka.ai.id",
                          "logo": {"@type": "ImageObject", "url": f"{SITE}/static/logo.png"}},
        }
        return "\n".join([
            f'<meta name="description" content="{html.escape(desc)}">',
            f'<link rel="canonical" href="{url}">',
            '<meta property="og:type" content="article">',
            '<meta property="og:site_name" content="Peka AI Blog">',
            f'<meta property="og:title" content="{html.escape(title)}">',
            f'<meta property="og:description" content="{html.escape(desc)}">',
            f'<meta property="og:url" content="{url}">',
            f'<meta property="og:image" content="{img_url}">',
            f'<meta property="article:published_time" content="{iso}">',
            '<meta name="twitter:card" content="summary_large_image">',
            f'<meta name="twitter:title" content="{html.escape(title)}">',
            f'<meta name="twitter:description" content="{html.escape(desc)}">',
            f'<meta name="twitter:image" content="{img_url}">',
            f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>',
        ])
    desc = "Arsip tulisan Peka AI: info AI terbaru, tools, project, dan info bansos."
    return "\n".join([
        f'<meta name="description" content="{desc}">',
        f'<link rel="canonical" href="{SITE}/">',
        '<meta property="og:type" content="website">',
        '<meta property="og:site_name" content="Peka AI Blog">',
        '<meta property="og:title" content="Peka AI Blog">',
        f'<meta property="og:description" content="{desc}">',
        f'<meta property="og:url" content="{SITE}/">',
        f'<meta property="og:image" content="{SITE}/static/logo.png">',
    ])

def shell(title, body_html, head_extra=""):
    t = f"{html.escape(title)} · Peka AI Blog" if title != "Arsip" else "Peka AI Blog · info AI & bansos harian"
    return f"""<!doctype html><html lang="id"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#f3f3f0">
<script>try{{var t=localStorage.getItem("peka-theme");if(t)document.documentElement.setAttribute("data-theme",t);}}catch(e){{}}</script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css">
<link rel="icon" href="/static/favicon.ico" sizes="48x48">
<link rel="icon" type="image/png" sizes="32x32" href="/static/favicon-32.png">
<link rel="icon" type="image/png" sizes="96x96" href="/static/favicon-96.png">
<link rel="apple-touch-icon" href="/static/apple-touch-icon.png">
<title>{t}</title>
{head_extra}
<style>{CSS}</style></head><body>
<div id="progress"></div>
<nav class="nav"><div class="frame"><div class="nav-inner">
<a class="brand" href="/"><img class="logo" src="/static/logo.png" alt="Logo Peka AI">peka.ai.id <span class="muted mono">/ blog</span></a>
<div class="nav-links"><a class="hide-m" href="https://www.instagram.com/peka.ai.id">Instagram</a><a class="hide-m" href="https://www.threads.com/@peka.ai.id">Threads</a><button id="themebtn" type="button">gelap</button><a class="btn-site" href="https://peka.ai.id">Website resmi</a></div>
</div></div></nav>
<div class="frame">{body_html}
<footer class="footer"><span class="mono">peka.ai.id / blog</span><span class="mono"><a href="https://url.peka.ai.id" target="_blank" rel="noopener">semua link resmi: url.peka.ai.id</a></span><span class="mono muted">info ai &amp; bansos, dikurasi tiap hari</span></footer>
</div>
<div class="lightbox" id="lightbox"><img alt="Gambar diperbesar"></div>
<button id="toTop" type="button" aria-label="Kembali ke atas">&#8593;</button>
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js" defer></script>
<script src="/static/blog.js" defer></script>
</body></html>"""

@app.route("/")
def index():
    posts = load_posts()
    rmap = rating_map()
    tags = all_tags(posts)
    active = request.args.get("tag", "")
    if active not in tags:
        active = ""
    shown = [p for p in posts if active in post_tags(p)] if active else posts
    q = request.args.get("q", "").strip()
    if q:
        ql = q.lower()

        def _hit(p):
            text = re.sub(r"<[^>]+>", " ", p.get("body_html", ""))
            blob = " ".join([p.get("title", ""), p.get("excerpt", ""),
                             " ".join(post_tags(p)), text]).lower()
            return ql in blob

        shown = [p for p in shown if _hit(p)]

    frow = '<div class="tagfilter"><span class="mono muted" style="align-self:center">topik:</span>'
    frow += f'<a class="tag{" ghost" if active else ""}" href="/">Semua</a>'
    for t in tags:
        frow += f'<a class="tag{" ghost" if t != active else ""}" href="/?tag={quote(t)}">{html.escape(t)}</a>'
    frow += "</div>"

    feat = ""
    rest = shown
    if not active and not q and shown:
        f = shown[0]
        rest = shown[1:]
        feat = f"""<a class="featured" href="/p/{f['slug']}">{cover_img(f, "pimg")}
<span><span class="mono muted" style="display:block;margin-bottom:8px">sorotan · {html.escape(fmt_date(f.get('date', '')))}</span>
<span class="ptitle">{html.escape(f.get('title', ''))}</span>
<span class="pexcerpt" style="display:block;margin-top:10px">{html.escape(f.get('excerpt', ''))}</span></span></a>"""

    rows = []
    start = 2 if feat else 1
    for i, p in enumerate(rest, start):
        meta = fmt_date(p.get("date", ""))
        if p["slug"] in rmap:
            avg, n = rmap[p["slug"]]
            meta += f" · {avg}/5 ({n} penilaian)"
        trow = "".join(f'<span class="tag ghost" style="font-size:.62rem;padding:4px 8px">{html.escape(t)}</span>'
                       for t in post_tags(p))
        rows.append(f"""<a class="postrow" href="/p/{p['slug']}">
<span class="pnum">{i:02d}</span>
<span><span class="mono muted" style="display:block;margin-bottom:6px">{html.escape(meta)}</span>
<span class="ptitle">{html.escape(p.get('title',''))}</span>
<span class="pexcerpt">{html.escape(p.get('excerpt',''))}</span>
<span style="display:flex;gap:6px;margin-top:8px;flex-wrap:wrap">{trow}</span></span>
{cover_img(p, "pthumb")}</a>""")
    nline = f"arsip / {len(shown)} tulisan"
    if active:
        nline += f" · topik {active}"
    if q:
        nline += f" · cari: {q}"
    search = (f'<form class="search" method="get" action="/">'
              f'<input type="search" name="q" value="{html.escape(q)}" '
              f'placeholder="Cari tulisan, topik, atau kata kunci..." aria-label="Cari tulisan">'
              f'<button class="btn" type="submit">Cari</button></form>')
    body = f"""<section class="block">
<p class="mono eyebrow"><span class="tick"></span><span>peka.ai.id / blog</span></p>
<h1>Sinyal AI,<br>dikutip <span style="background:var(--accent);padding:0 .1em">peka</span>.</h1>
<p class="lead">Arsip setiap postingan Peka AI: info AI terbaru, tools, project, dan info bansos. Sama dengan yang tayang di Instagram dan Threads. Di sini versi lengkapnya, plus kolom komentar.</p>
</section>
<section class="block">{search}{frow}
<p class="mono muted" style="margin:10px 0 8px">{html.escape(nline)}</p>
{feat}
{''.join(rows) if rows else '<p class="muted">Belum ada tulisan di topik ini.</p>'}</section>"""
    return shell("Arsip", body, seo_head())

@app.route("/p/<slug>")
def post(slug):
    if not SLUG_RE.match(slug):
        abort(404)
    allp = load_posts()
    p = next((x for x in allp if x["slug"] == slug), None)
    if not p:
        abort(404)
    title = p.get("title", "")
    page_url = f"{SITE}/p/{slug}"
    iso = (p.get("datetime") or p.get("date") or "")[:10]

    links = []
    for label, url in (p.get("links") or {}).items():
        if url and url.startswith("http"):
            links.append(f'<a class="tag ghost" href="{html.escape(url)}">{html.escape(label)}</a>')

    trow = "".join(
        f'<a class="tag" href="/?tag={quote(t)}">{html.escape(t)}</a>' for t in post_tags(p))
    trow = f'<div class="tagrow">{trow}</div>' if trow else ""

    share = [("WhatsApp", f"https://wa.me/?text={quote(title + ' ' + page_url)}"),
             ("X", f"https://twitter.com/intent/tweet?text={quote(title)}&url={quote(page_url)}"),
             ("Telegram", f"https://t.me/share/url?url={quote(page_url)}&text={quote(title)}")]
    sh = '<div class="share-row"><span class="mono muted">bagikan:</span>' + "".join(
        f'<a class="tag ghost" target="_blank" rel="noopener" href="{u}">{n}</a>' for n, u in share)
    sh += (f'<button class="tag ghost" type="button" data-copy="{page_url}">salin tautan</button></div>'
           '<script>(function(){var b=document.querySelector("[data-copy]");if(!b)return;'
           'b.addEventListener("click",function(){navigator.clipboard.writeText(b.dataset.copy);'
           'b.textContent="disalin!";});})();</script>')

    idx = next(i for i, x in enumerate(allp) if x["slug"] == slug)
    older = allp[idx + 1] if idx + 1 < len(allp) else None
    newer = allp[idx - 1] if idx - 1 >= 0 else None
    pn = '<nav class="pnnav" aria-label="Navigasi tulisan">'
    pn += (f'<a href="/p/{older["slug"]}"><span class="mono muted pn-k">← lebih lama</span>'
           f'<span class="pn-t">{html.escape(older.get("title", ""))}</span></a>' if older else '<span></span>')
    pn += (f'<a class="next" href="/p/{newer["slug"]}"><span class="mono muted pn-k">lebih baru →</span>'
           f'<span class="pn-t">{html.escape(newer.get("title", ""))}</span></a>' if newer else '<span></span>')
    pn += "</nav>"

    others = [x for x in allp if x["slug"] != slug][:3]
    rel = ""
    if others:
        rel = ('<div style="margin-top:30px"><p class="mono eyebrow"><span class="tick"></span>'
               '<span>baca juga</span></p>' + "".join(
            f"""<a class="postrow" href="/p/{x['slug']}">
<span class="pnum">→</span>
<span><span class="mono muted" style="display:block;margin-bottom:6px">{html.escape(fmt_date(x.get('date', '')))}</span>
<span class="ptitle" style="font-size:1.2rem">{html.escape(x.get('title', ''))}</span></span>
{cover_img(x, "pthumb")}</a>""" for x in others) + "</div>")

    ip = client_ip()
    c = db()
    rav, rcount, mine = rating_stats(c, slug, ip)
    cmts = c.execute("SELECT name, body, created_at FROM comments WHERE slug=? ORDER BY id ASC", (slug,)).fetchall()
    c.close()
    chtml = "".join(
        f'<div class="cmt"><div class="cmt-head"><span class="cmt-name">{html.escape(n)}</span>'
        f'<span class="cmt-date">{html.escape(d)}</span></div><p>{html.escape(b)}</p></div>'
        for n, b, d in cmts) or '<p class="muted">Belum ada komentar. Jadi yang pertama.</p>'
    enhanced, toc_html = enhance_body(p.get("body_html", ""))
    body = f"""<article class="block">
<a class="mono back" href="/">← arsip</a>
{trow}
<h1 style="max-width:20ch">{html.escape(title)}</h1>
<p class="byline"><img src="/static/logo.png" alt="Peka AI"><span class="mono">Peka AI · <time datetime="{iso}">{html.escape(fmt_date(p.get('date', '')))}</time> · {reading_time(p)} menit baca</span></p>
{gallery(p)}
{toc_html}
<div class="body">{enhanced}</div>
<div class="links-row"><span class="mono muted" style="align-self:center">tayang juga di:</span>{''.join(links)}</div>
{sh}
{rating_block(slug, rav, rcount, mine)}
{rel}
{pn}
</article>
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
    return shell(title, body, seo_head(p))

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
    n = c.execute("SELECT COUNT(*) FROM ratings WHERE ip=? AND created_at > ?", (ip, wib_hour_ago())).fetchone()[0]
    if n >= 20:
        c.close()
        return Response(json.dumps({"ok": False}), 429, mimetype="application/json")
    c.execute("""INSERT INTO ratings(slug,ip,stars,created_at) VALUES(?,?,?,?)
      ON CONFLICT(slug,ip) DO UPDATE SET stars=excluded.stars, created_at=excluded.created_at""",
      (slug, ip, stars, wib_now()))
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
    n = c.execute("SELECT COUNT(*) FROM comments WHERE ip=? AND created_at > ?", (ip, wib_hour_ago())).fetchone()[0]
    if n >= 5:
        c.close()
        return Response("Terlalu banyak komentar, coba lagi nanti.", 429)
    c.execute("INSERT INTO comments(slug,name,body,ip,created_at) VALUES(?,?,?,?,?)",
              (slug, name, cbody, ip, wib_now()))
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
