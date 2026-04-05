import requests, json, re, csv, io, base64, subprocess, os, shutil
from collections import Counter
from datetime import datetime

SHEET_ID     = os.environ["MCL_SHEET_ID"]
GITHUB_TOKEN = os.environ["MCL_GH_TOKEN"]
GITHUB_USER  = "davidmmclemore"
GITHUB_REPO  = "McLemore-Library"
GITHUB_BRANCH= "main"

# ── Download ──────────────────────────────────────────────────────────────────
url  = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Books"
resp = requests.get(url, timeout=60); resp.raise_for_status()
rows = list(csv.reader(io.StringIO(resp.text)))
data_rows = rows[1:]
print(f"Downloaded {len(data_rows)} rows")

def col(row,i,d=''):
    try: return row[i].strip() if i<len(row) else d
    except: return d
def clean_html(text,max_len=400):
    if not text: return ''
    text=re.sub(r'<[^>]+>',' ',text)
    for ent,rep in [('&nbsp;',' '),('&amp;','&'),('&lt;','<'),('&gt;','>'),
                    ('&mdash;','—'),('&ndash;','–'),('&ldquo;','"'),('&rdquo;','"'),
                    ('&lsquo;',"'"),('&rsquo;',"'"),('&#39;',"'"),('&quot;','"')]:
        text=text.replace(ent,rep)
    text=re.sub(r'&#x[0-9a-fA-F]+;','',text)
    text=re.sub(r'&[a-zA-Z0-9]+;',' ',text)
    return re.sub(r'\s+',' ',text).strip()[:max_len]
def parse_tags(s):
    return [t.strip() for t in s.split(',') if t.strip()][:12] if s else []
def extract_asin(u):
    m=re.search(r'/dp/([A-Z0-9]{10})',u,re.I); return m.group(1) if m else ''
def get_cover(cv,au,ac,pa):
    if cv and cv.startswith('http'): return cv
    asin=extract_asin(au)
    if not asin and re.match(r'^[A-Z0-9]{10}$',pa,re.I): asin=pa
    if not asin and re.match(r'^[A-Z0-9]{10}$',ac,re.I): asin=ac
    return f'https://images-na.ssl-images-amazon.com/images/P/{asin}.01.LZZZZZZZ.jpg' if asin else ''

SERIES_RE = re.compile(
    r'[\s,]+(?:#\s*\d+|no\.?\s*\d+|book\s+\d+|vol\.?\s*\d+|volume\s+\d+|part\s+\d+)\s*$',
    re.I)

def detect_series(title):
    """Return (series_name, volume_num) or ('', 0)"""
    m = re.search(
        r'^(.*?)[\s,]+(?:#\s*(\d+)|no\.?\s*(\d+)|book\s+(\d+)|vol\.?\s*(\d+)|volume\s+(\d+)|part\s+(\d+))\s*$',
        title, re.I)
    if m:
        series = m.group(1).strip().rstrip(',').strip()
        num = next(int(g) for g in m.groups()[1:] if g)
        return series, num
    return '', 0

books = []
for i, row in enumerate(data_rows):
    tag_list = parse_tags(col(row,7))
    cover    = get_cover(col(row,16), col(row,17), col(row,19), col(row,20))
    pages_raw= col(row,6)
    try: pages= int(float(pages_raw)) if pages_raw else 0
    except: pages=0
    book_id  = col(row,0) or f'BOOK-{i:04d}'
    title    = clean_html(col(row,1))
    series, svol = detect_series(title)
    books.append({
        'id': book_id,
        't':  title,
        'a':  clean_html(col(row,2)),
        'f':  clean_html(col(row,4)),
        'c':  clean_html(col(row,5)),
        'l':  clean_html(col(row,8)),
        'p':  pages,
        'tg': tag_list,
        's':  clean_html(col(row,9), max_len=2000),
        'img':cover,
        'url':col(row,17),
        'sr': series,   # series name
        'sv': svol,     # series volume
    })

authors    = [b['a'] for b in books if b['a']]
top_authors= [a for a,_ in Counter(authors).most_common(300)]
categories = sorted(set(b['c'] for b in books if b['c']))
formats    = sorted(set(b['f'] for b in books if b['f']))
locations  = sorted(set(b['l'] for b in books if b['l']))
all_tags   = sorted(set(t for b in books for t in b['tg'] if t))
all_series = sorted(set(b['sr'] for b in books if b['sr']))
tag_counts = Counter(t for b in books for t in b['tg'] if t)
meta = {
    'authors': top_authors, 'categories': categories,
    'formats': formats, 'locations': locations,
    'tags': all_tags, 'series': all_series,
    'tagCounts': dict(tag_counts.most_common(80)),
    'total': len(books), 'built': datetime.now().strftime('%B %d, %Y')
}

books_raw = json.dumps(books, separators=(',',':'))
meta_raw  = json.dumps(meta,  separators=(',',':'))
print(f'Books: {len(books)}, covers: {sum(1 for b in books if b["img"])}, series: {len(all_series)}')

def make_options(items):
    return '\n'.join(f'<option value="{v}">{v}</option>' for v in items)


# ══════════════════════════════════════════════════════════════════════════════
CSS = r"""
:root {
  --bg:#f0f0ee; --surface:#fff; --surface2:#f3f4f6; --surface3:#e9eaec;
  --border:#e5e7eb; --text:#222; --text2:#6b7280; --text3:#9ca3af;
  --accent:#4f46e5; --accent2:#818cf8;
  --badge-fmt-bg:#dbeafe; --badge-fmt-txt:#1d4ed8;
  --badge-cat-bg:#ede9fe; --badge-cat-txt:#6d28d9;
  --badge-loc-bg:#d1fae5; --badge-loc-txt:#065f46;
  --badge-pg-bg:#fef3c7;  --badge-pg-txt:#92400e;
  --pill-bg:#f3f4f6; --pill-txt:#374151;
  --h-shadow:0 1px 3px rgba(0,0,0,.07);
  --card-shadow:0 4px 14px rgba(0,0,0,.1);
  --star:#f59e0b; --shelf-wood:#8b6914;
}
body.dark {
  --bg:#111827; --surface:#1f2937; --surface2:#374151; --surface3:#4b5563;
  --border:#374151; --text:#f9fafb; --text2:#9ca3af; --text3:#6b7280;
  --accent:#818cf8; --accent2:#a5b4fc;
  --badge-fmt-bg:#1e3a5f; --badge-fmt-txt:#93c5fd;
  --badge-cat-bg:#2e1b5e; --badge-cat-txt:#c4b5fd;
  --badge-loc-bg:#064e3b; --badge-loc-txt:#6ee7b7;
  --badge-pg-bg:#451a03;  --badge-pg-txt:#fcd34d;
  --pill-bg:#374151; --pill-txt:#d1d5db;
  --h-shadow:0 1px 4px rgba(0,0,0,.4);
  --card-shadow:0 4px 14px rgba(0,0,0,.5);
  --shelf-wood:#5c4209;
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;background:var(--bg);color:var(--text);transition:background .2s,color .2s}
a{color:inherit;text-decoration:none}

/* ── Header ── */
.header{background:var(--surface);border-bottom:1px solid var(--border);padding:10px 14px 0;position:sticky;top:0;z-index:100;box-shadow:var(--h-shadow)}
.header-top{display:flex;align-items:center;justify-content:space-between;margin-bottom:2px}
.header-top h1{font-size:1.2rem;font-weight:700;flex:1;text-align:center}
.tool-btn{background:none;border:1px solid var(--border);border-radius:8px;padding:5px 9px;cursor:pointer;font-size:.82rem;color:var(--text2);line-height:1;transition:background .15s}
.tool-btn:hover{background:var(--surface2)}
.tool-btn-group{display:flex;gap:4px}
.subtitle{text-align:center;color:var(--text2);font-size:.74rem;margin-bottom:6px}
.filters-toggle{display:none;width:100%;padding:7px;border:1px solid var(--border);border-radius:8px;background:var(--surface);font-size:.83rem;color:var(--text2);cursor:pointer;margin-bottom:6px;text-align:center}
.filters-body{display:contents}
.filter-row{display:flex;flex-wrap:wrap;gap:5px;align-items:center;padding-bottom:5px}
.filter-row input,.filter-row select{padding:5px 8px;border:1px solid var(--border);border-radius:8px;font-size:.78rem;background:var(--surface);color:var(--text);cursor:pointer}
.filter-row input{flex:1;min-width:140px;cursor:text}
.filter-row select{max-width:130px}
.filter-row input::placeholder{color:var(--text3)}
.count-row{display:flex;gap:5px;align-items:center;padding-bottom:7px;flex-wrap:wrap}
.count-lbl{font-size:.74rem;color:var(--text2);flex:1}
.btn-sm{padding:4px 9px;border:1px solid var(--border);border-radius:8px;background:var(--surface);cursor:pointer;font-size:.75rem;color:var(--text2)}
.btn-sm:hover{background:var(--surface2)}
.btn-accent{background:var(--accent);color:#fff;border-color:var(--accent)}
.btn-accent:hover{opacity:.88}

/* ── Book of the Day banner ── */
.botd-toggle{display:flex;align-items:center;gap:5px;font-size:.72rem;color:var(--text3);cursor:pointer;background:none;border:none;padding:2px 0 4px;width:100%}
.botd-toggle:hover{color:var(--text)}
.botd-toggle .toggle-arrow{font-size:.6rem;transition:transform .2s}
.botd-toggle.open .toggle-arrow{transform:rotate(90deg)}
.recent-toggle{display:flex;align-items:center;gap:5px;font-size:.72rem;color:var(--text3);cursor:pointer;background:none;border:none;padding:4px 8px 2px;width:100%}
.recent-toggle:hover{color:var(--text)}
.recent-toggle .toggle-arrow{font-size:.6rem;transition:transform .2s}
.recent-toggle.open .toggle-arrow{transform:rotate(90deg)}
.botd-bar{display:flex;align-items:center;gap:8px;padding:6px 10px;background:linear-gradient(90deg,#4f46e5,#7c3aed);color:#fff;font-size:.76rem;cursor:pointer;border-radius:8px;margin-bottom:6px}
.botd-bar img{width:28px;height:42px;object-fit:cover;border-radius:3px;flex-shrink:0}
.botd-bar .botd-lbl{font-weight:700;font-size:.7rem;opacity:.85;margin-bottom:1px}
.botd-bar .botd-title{font-weight:600;font-size:.8rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.botd-bar .botd-author{opacity:.8;font-size:.72rem}

/* ── Recently viewed strip ── */
.recent-strip{overflow-x:auto;display:flex;gap:7px;padding:8px 8px 4px;scrollbar-width:none}
.recent-strip::-webkit-scrollbar{display:none}
.recent-lbl{font-size:.68rem;color:var(--text3);white-space:nowrap;align-self:center;padding-left:2px;flex-shrink:0}
.recent-thumb{flex-shrink:0;width:44px;cursor:pointer;opacity:.85;transition:opacity .15s,transform .15s}
.recent-thumb:hover{opacity:1;transform:translateY(-2px)}
.recent-thumb img{width:44px;height:66px;object-fit:cover;border-radius:4px;display:block}
.recent-thumb .no-r{width:44px;height:66px;background:var(--surface2);border-radius:4px;display:flex;align-items:center;justify-content:center;font-size:1.1rem}

/* ── Grid ── */
.grid-wrap{padding:10px 8px}
.book-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(148px,1fr));gap:9px}

/* ── Card (grid) ── */
.card{background:var(--surface);border-radius:8px;border:1px solid var(--border);overflow:hidden;display:flex;flex-direction:column;transition:box-shadow .15s,transform .15s;cursor:pointer;outline:none;position:relative}
.card:hover,.card:focus{box-shadow:var(--card-shadow);transform:translateY(-2px)}
.card:focus{outline:2px solid var(--accent);outline-offset:1px}
.card-cover{width:100%;aspect-ratio:2/3;object-fit:cover;display:block;background:var(--surface2)}
.no-cover{width:100%;aspect-ratio:2/3;display:flex;align-items:center;justify-content:center;font-size:2rem;background:var(--surface2);color:var(--text3)}
.card-body{padding:7px;display:flex;flex-direction:column;gap:3px;flex:1}
.card-title{font-size:.73rem;font-weight:700;line-height:1.3;color:var(--text)}
.card-author{font-size:.66rem;color:var(--accent);cursor:pointer;font-weight:500}
.card-author:hover{text-decoration:underline}
.badges{display:flex;flex-wrap:wrap;gap:3px;margin-top:1px}
.badge{font-size:.59rem;font-weight:600;padding:2px 5px;border-radius:10px;cursor:pointer;white-space:nowrap}
.badge-format{background:var(--badge-fmt-bg);color:var(--badge-fmt-txt)}
.badge-category{background:var(--badge-cat-bg);color:var(--badge-cat-txt)}
.badge-location{background:var(--badge-loc-bg);color:var(--badge-loc-txt)}
.badge:hover{opacity:.75}
.card-pages{font-size:.6rem;color:var(--text3)}
.card-tags{display:flex;flex-wrap:wrap;gap:3px;margin-top:1px}
.tag-pill{font-size:.57rem;background:var(--pill-bg);color:var(--pill-txt);padding:2px 5px;border-radius:8px;cursor:pointer}
.tag-pill:hover{opacity:.75}
.card-summary{font-size:.66rem;color:var(--text2);line-height:1.5;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;margin-top:2px}
.card-summary.expanded{-webkit-line-clamp:unset;display:block}
.summary-toggle{font-size:.61rem;color:var(--accent);cursor:pointer;margin-top:2px;background:none;border:none;padding:0;text-align:left}
.amazon-btn{margin-top:auto;padding-top:5px}
.amazon-btn a{display:block;text-align:center;background:#ff9900;color:#111;font-size:.66rem;font-weight:700;padding:4px;border-radius:6px}
.amazon-btn a:hover{background:#e68900}

/* ── Stars (on card) ── */
.card-stars{display:flex;gap:1px;margin-top:2px}
.card-star{font-size:.65rem;color:var(--text3);cursor:pointer;line-height:1}
.card-star.filled{color:var(--star)}
.card-corner-badges{position:absolute;top:4px;right:4px;display:flex;flex-direction:column;gap:2px;align-items:flex-end}
.note-dot{width:8px;height:8px;background:#10b981;border-radius:50%;border:1px solid #fff}
.loan-dot{width:8px;height:8px;background:#ef4444;border-radius:50%;border:1px solid #fff}

/* ── List view ── */
.view-list .book-grid{display:flex;flex-direction:column;gap:4px}
.list-row{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:8px 10px;display:flex;align-items:center;gap:10px;cursor:pointer;transition:box-shadow .15s;outline:none}
.list-row:hover,.list-row:focus{box-shadow:var(--card-shadow)}
.list-row:focus{outline:2px solid var(--accent);outline-offset:1px}
.list-cover{width:40px;height:60px;object-fit:cover;border-radius:4px;flex-shrink:0;background:var(--surface2)}
.list-no-cover{width:40px;height:60px;display:flex;align-items:center;justify-content:center;font-size:1.3rem;background:var(--surface2);border-radius:4px;flex-shrink:0;color:var(--text3)}
.list-info{flex:1;min-width:0}
.list-title{font-size:.8rem;font-weight:700;color:var(--text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.list-author{font-size:.7rem;color:var(--accent);margin-bottom:2px;cursor:pointer}
.list-author:hover{text-decoration:underline}
.list-stars{display:flex;gap:1px}
.list-star{font-size:.65rem;color:var(--text3)}
.list-star.filled{color:var(--star)}
.list-right{display:flex;flex-direction:column;align-items:flex-end;gap:4px;flex-shrink:0;padding-left:8px}
.list-pages{font-size:.67rem;color:var(--text3);white-space:nowrap}

/* ── Spine / Bookshelf view ── */
.view-spine .book-grid{display:flex;flex-wrap:wrap;align-items:flex-end;gap:2px;padding:24px 8px 0;background:var(--bg);position:relative}
.view-spine .book-grid::after{content:'';display:block;width:100%;height:18px;background:linear-gradient(180deg,var(--shelf-wood) 0%,#6b4f10 60%,#4a3508 100%);border-radius:4px;margin-top:0;position:sticky;bottom:0;box-shadow:0 4px 12px rgba(0,0,0,.4)}
.spine{display:flex;align-items:center;justify-content:center;cursor:pointer;border-radius:3px 3px 0 0;transition:transform .15s,box-shadow .15s;position:relative;flex-shrink:0;overflow:hidden}
.spine:hover{transform:translateY(-8px);box-shadow:0 6px 16px rgba(0,0,0,.35);z-index:2}
.spine-title{writing-mode:vertical-rl;transform:rotate(180deg);font-size:.58rem;font-weight:700;color:#fff;text-shadow:0 1px 2px rgba(0,0,0,.6);padding:4px 2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-height:130px;line-height:1.15}
.spine-cover{width:100%;height:100%;object-fit:cover;border-radius:3px 3px 0 0}
.spine-no-cover{width:100%;height:100%;display:flex;align-items:flex-end;padding-bottom:6px;justify-content:center}

/* ── Search highlight ── */
mark{background:#fde68a;color:inherit;border-radius:2px;padding:0 1px}
body.dark mark{background:#78350f;color:#fde68a}

/* ── Modal ── */
.modal-overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:200;align-items:center;justify-content:center;padding:16px}
#modal-overlay{z-index:300}
.modal-overlay.open{display:flex}
.modal{background:var(--surface);border-radius:14px;max-width:740px;width:100%;max-height:90vh;overflow-y:auto;padding:24px;position:relative}
.modal-close{position:absolute;top:12px;right:14px;font-size:1.4rem;cursor:pointer;color:var(--text2);background:none;border:none;line-height:1}
.modal-top{display:flex;gap:20px;flex-wrap:wrap}
.modal-cover img{width:160px;border-radius:8px;flex-shrink:0}
.no-cover-lg{width:160px;height:240px;display:flex;align-items:center;justify-content:center;background:var(--surface2);border-radius:8px;font-size:3rem;color:var(--text3)}
.modal-info{flex:1;min-width:200px}
.modal-title{font-size:1.05rem;font-weight:700;line-height:1.3;margin-bottom:4px;color:var(--text)}
.modal-author{color:var(--accent);font-size:.88rem;margin-bottom:8px;cursor:pointer}
.modal-author:hover{text-decoration:underline}
.modal-meta{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:8px}
.modal-summary{font-size:.82rem;color:var(--text2);line-height:1.65;margin-top:8px}
.modal-amazon{margin-top:10px}
.modal-amazon a{display:inline-block;background:#ff9900;color:#111;font-size:.8rem;font-weight:700;padding:6px 16px;border-radius:8px}
.modal-section{margin-top:14px;padding-top:14px;border-top:1px solid var(--border)}
.modal-section-title{font-size:.75rem;font-weight:700;color:var(--text3);text-transform:uppercase;letter-spacing:.05em;margin-bottom:8px}

/* ── Stars in modal ── */
.star-row{display:flex;gap:4px;align-items:center;margin:8px 0}
.modal-star{font-size:1.4rem;cursor:pointer;color:var(--text3);transition:color .1s,transform .1s}
.modal-star:hover,.modal-star.hover{color:var(--star);transform:scale(1.2)}
.modal-star.filled{color:var(--star)}
.star-clear{font-size:.72rem;color:var(--text3);cursor:pointer;margin-left:4px}
.star-clear:hover{color:var(--accent)}

/* ── Notes in modal ── */
.notes-area{width:100%;padding:8px 10px;border:1px solid var(--border);border-radius:8px;font-size:.82rem;background:var(--surface2);color:var(--text);resize:vertical;min-height:70px;font-family:inherit}
.notes-area:focus{outline:2px solid var(--accent);outline-offset:-1px}
.notes-save{margin-top:5px;padding:5px 12px;background:var(--accent);color:#fff;border:none;border-radius:8px;cursor:pointer;font-size:.78rem}
.notes-save:hover{opacity:.88}
.notes-saved{font-size:.72rem;color:#10b981;margin-left:8px}

/* ── Reading dates ── */
.dates-row{display:flex;gap:8px;flex-wrap:wrap;margin-top:6px}
.date-field{display:flex;flex-direction:column;gap:3px}
.date-field label{font-size:.7rem;color:var(--text3)}
.date-field input[type=date]{padding:4px 7px;border:1px solid var(--border);border-radius:6px;background:var(--surface2);color:var(--text);font-size:.78rem}
.date-field input[type=date]:focus{outline:2px solid var(--accent);outline-offset:-1px}

/* ── Progress bar ── */
.progress-row{display:flex;align-items:center;gap:8px;margin-top:6px}
.progress-bar-wrap{flex:1;height:8px;background:var(--surface2);border-radius:4px;overflow:hidden}
.progress-bar-fill{height:100%;background:var(--accent);border-radius:4px;transition:width .3s}
.progress-input{width:55px;padding:3px 6px;border:1px solid var(--border);border-radius:6px;background:var(--surface2);color:var(--text);font-size:.78rem;text-align:center}

/* ── Loan tracker ── */
.loan-row{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-top:6px}
.loan-input{flex:1;min-width:120px;padding:4px 8px;border:1px solid var(--border);border-radius:6px;background:var(--surface2);color:var(--text);font-size:.78rem}
.loan-input:focus{outline:2px solid var(--accent);outline-offset:-1px}
.loan-active{font-size:.78rem;color:#ef4444;font-weight:600}

/* ── Discover / shelf / mini ── */
.discover-links{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px}
.discover-link{display:inline-flex;align-items:center;gap:4px;padding:5px 10px;border:1px solid var(--border);border-radius:20px;font-size:.74rem;color:var(--text2);background:var(--surface);transition:all .15s;white-space:nowrap}
.discover-link:hover{border-color:var(--accent);color:var(--accent)}
.wiki-blurb{font-size:.8rem;color:var(--text2);line-height:1.6;margin-bottom:5px}
.wiki-link{font-size:.74rem;color:var(--accent)}
.wiki-link:hover{text-decoration:underline}
.mini-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(88px,1fr));gap:7px;margin-top:6px}
.mini-card{background:var(--surface2);border-radius:6px;overflow:hidden;cursor:pointer;border:1px solid var(--border);transition:box-shadow .12s}
.mini-card:hover{box-shadow:var(--card-shadow)}
.mini-cover{width:100%;aspect-ratio:2/3;object-fit:cover;display:block}
.mini-no-cover{width:100%;aspect-ratio:2/3;display:flex;align-items:center;justify-content:center;font-size:1.3rem;background:var(--surface3);color:var(--text3)}
.mini-title{font-size:.6rem;font-weight:700;padding:4px 5px 2px;color:var(--text);line-height:1.3}
.mini-author{font-size:.56rem;color:var(--text2);padding:0 5px 4px}
.modal-shelf-row{display:flex;flex-wrap:wrap;gap:6px;padding:10px 0;border-top:1px solid var(--border);margin-top:10px}
.shelf-btn{padding:4px 10px;border:1px solid var(--border);border-radius:20px;background:var(--surface);color:var(--text2);cursor:pointer;font-size:.73rem;transition:all .15s;white-space:nowrap}
.shelf-btn:hover{border-color:var(--accent);color:var(--accent)}
.shelf-btn.active{background:var(--accent);color:#fff;border-color:var(--accent)}
.shelf-btn.active:hover{opacity:.85}
.shelves-modal,.stats-modal,.author-modal{max-width:580px}
.shelf-row-btn{display:flex;align-items:center;gap:12px;padding:11px;border:1px solid var(--border);border-radius:10px;cursor:pointer;background:var(--surface);transition:box-shadow .15s;width:100%;text-align:left;margin-bottom:6px}
.shelf-row-btn:hover{box-shadow:var(--card-shadow)}
.shelf-row-icon{font-size:1.3rem;width:30px;text-align:center;flex-shrink:0}
.shelf-row-label{font-weight:600;color:var(--text);font-size:.88rem}
.shelf-row-count{font-size:.72rem;color:var(--text2);margin-top:1px}
.shelf-chevron{margin-left:auto;color:var(--text3);font-size:1rem}
.shelf-mini-wrap{position:relative;display:flex;flex-direction:column}
.shelf-mini-remove{position:absolute;top:3px;right:3px;background:rgba(0,0,0,.55);color:#fff;border:none;border-radius:50%;width:17px;height:17px;font-size:.58rem;cursor:pointer;display:flex;align-items:center;justify-content:center;line-height:1;padding:0;z-index:2}
.share-row{display:flex;gap:7px;align-items:center;margin-top:10px;flex-wrap:wrap}
.share-input{flex:1;min-width:0;padding:5px 8px;border:1px solid var(--border);border-radius:8px;font-size:.73rem;background:var(--surface2);color:var(--text);font-family:monospace}
.import-banner{background:var(--surface2);border:1px solid var(--border);border-radius:10px;padding:10px;display:flex;align-items:center;gap:10px;margin-bottom:10px;flex-wrap:wrap}
.progress-mini-wrap{margin-top:4px}
.progress-mini-bar{height:4px;background:var(--surface2);border-radius:2px;overflow:hidden;margin-top:2px}
.progress-mini-fill{height:100%;background:var(--accent);border-radius:2px}
.progress-mini-lbl{font-size:.58rem;color:var(--text3)}

/* ── Stats ── */
.stat-grid{display:grid;grid-template-columns:1fr 1fr;gap:9px;margin-bottom:12px}
.stat-box{background:var(--surface2);border-radius:10px;padding:11px;text-align:center}
.stat-num{font-size:1.5rem;font-weight:700;color:var(--accent)}
.stat-lbl{font-size:.7rem;color:var(--text2);margin-top:2px}
.top-list{list-style:none}
.top-list li{display:flex;justify-content:space-between;align-items:center;padding:5px 0;border-bottom:1px solid var(--border);font-size:.78rem}
.top-list li:last-child{border-bottom:none}
.top-list .cnt{font-weight:700;color:var(--accent);margin-left:8px;flex-shrink:0}
.tag-cloud{display:flex;flex-wrap:wrap;gap:5px;padding:6px 0}
.tag-cloud-pill{cursor:pointer;border-radius:20px;padding:3px 9px;background:var(--pill-bg);color:var(--pill-txt);line-height:1;transition:background .12s}
.tag-cloud-pill:hover{background:var(--accent);color:#fff}
.year-bar-wrap{display:flex;align-items:center;gap:6px;margin-bottom:4px}
.year-bar-label{font-size:.72rem;color:var(--text2);width:36px;text-align:right;flex-shrink:0}
.year-bar-bg{flex:1;height:14px;background:var(--surface2);border-radius:4px;overflow:hidden}
.year-bar-fill{height:100%;background:var(--accent);border-radius:4px}
.year-bar-cnt{font-size:.68rem;color:var(--text3);width:24px;flex-shrink:0}

/* ── Custom shelf modal ── */
.new-shelf-row{display:flex;gap:6px;align-items:center;margin-top:10px;flex-wrap:wrap}
.new-shelf-input{flex:1;min-width:0;padding:6px 9px;border:1px solid var(--border);border-radius:8px;font-size:.8rem;background:var(--surface2);color:var(--text)}
.new-shelf-input:focus{outline:2px solid var(--accent);outline-offset:-1px}
.icon-options{display:flex;gap:5px;flex-wrap:wrap;margin-top:6px}
.icon-opt{cursor:pointer;padding:4px;border:1px solid transparent;border-radius:6px;font-size:1.1rem;transition:border-color .1s}
.icon-opt.sel{border-color:var(--accent);background:var(--surface2)}
.shelf-delete{background:none;border:none;cursor:pointer;color:var(--text3);font-size:.8rem;padding:2px 4px}
.shelf-delete:hover{color:#ef4444}

/* ── Author modal ── */
.author-header{display:flex;gap:14px;align-items:flex-start;margin-bottom:12px;flex-wrap:wrap}
.author-avatar{width:70px;height:70px;border-radius:50%;object-fit:cover;background:var(--surface2);flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:2rem}
.author-name{font-size:1rem;font-weight:700;color:var(--text)}
.author-count{font-size:.78rem;color:var(--text2)}
.author-bio{font-size:.8rem;color:var(--text2);line-height:1.6;margin-bottom:10px}

/* ── Print view ── */
@media print {
  .header,.recent-strip,.botd-bar,.count-row,.modal-overlay,.filters-toggle,.tool-btn,
  .amazon-btn,.summary-toggle,.card-stars,.card-corner-badges{display:none!important}
  body{background:#fff;color:#000;font-size:10pt}
  .grid-wrap{padding:0}
  .book-grid{grid-template-columns:repeat(4,1fr);gap:8px}
  .card{break-inside:avoid;border:1px solid #ccc;box-shadow:none}
  .card-cover{aspect-ratio:2/3}
}

/* ── Offline banner ── */
.offline-banner{display:none;position:fixed;bottom:12px;left:50%;transform:translateX(-50%);background:#1f2937;color:#f9fafb;padding:7px 16px;border-radius:20px;font-size:.78rem;z-index:300;gap:6px;align-items:center}
.offline-banner.show{display:flex}

/* ── Sync indicator ── */
.sync-dot{width:7px;height:7px;border-radius:50%;display:inline-block;margin-right:3px;vertical-align:middle;transition:background .3s}
.sync-dot.idle{background:var(--text3)}
.sync-dot.syncing{background:#f59e0b;animation:pulse .8s infinite}
.sync-dot.synced{background:#10b981}
.sync-dot.error{background:#ef4444}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.35}}
/* ── Sync / Settings modal ── */
.sync-modal{max-width:480px}
.sync-token-input{width:100%;padding:7px 10px;border:1px solid var(--border);border-radius:8px;font-size:.8rem;background:var(--surface2);color:var(--text);font-family:monospace;margin-top:6px}
.sync-token-input:focus{outline:2px solid var(--accent);outline-offset:-1px}
.sync-steps{font-size:.78rem;color:var(--text2);line-height:1.7;padding:8px 0}
.sync-steps a{color:var(--accent)}
.sync-status-bar{padding:8px 10px;border-radius:8px;font-size:.78rem;margin-top:8px;display:none}
.sync-status-bar.show{display:block}
.sync-status-bar.ok{background:#d1fae5;color:#065f46}
.sync-status-bar.err{background:#fee2e2;color:#991b1b}
body.dark .sync-status-bar.ok{background:#064e3b;color:#6ee7b7}
body.dark .sync-status-bar.err{background:#450a0a;color:#fca5a5}

/* ── Goal ring ── */
.goal-ring-wrap{display:flex;align-items:center;gap:5px;cursor:pointer}
.goal-ring{position:relative;width:28px;height:28px;flex-shrink:0}
.goal-ring svg{transform:rotate(-90deg)}
.goal-ring-bg{fill:none;stroke:var(--surface2);stroke-width:4}
.goal-ring-fill{fill:none;stroke:var(--accent);stroke-width:4;stroke-linecap:round;transition:stroke-dashoffset .5s}
.goal-ring-label{font-size:.62rem;color:var(--text2);white-space:nowrap}

/* ── Session timer ── */
.timer-btn{position:fixed;bottom:20px;right:20px;width:52px;height:52px;border-radius:50%;background:var(--accent);color:#fff;border:none;cursor:pointer;font-size:1.2rem;display:flex;align-items:center;justify-content:center;box-shadow:0 4px 12px rgba(79,70,229,.5);z-index:150;transition:transform .15s}
.timer-btn:hover{transform:scale(1.1)}
.timer-btn.running{background:#10b981;box-shadow:0 4px 12px rgba(16,185,129,.5)}
.timer-popup{position:fixed;bottom:82px;right:20px;background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:14px;width:240px;box-shadow:var(--card-shadow);z-index:150;display:none}
.timer-popup.open{display:block}
.timer-display{font-size:1.8rem;font-weight:700;text-align:center;font-variant-numeric:tabular-nums;color:var(--text);margin:6px 0}
.timer-book-select{width:100%;padding:5px 8px;border:1px solid var(--border);border-radius:7px;background:var(--surface2);color:var(--text);font-size:.75rem;margin-bottom:8px}
.timer-controls{display:flex;gap:6px}
.timer-controls button{flex:1;padding:5px;border:1px solid var(--border);border-radius:7px;background:var(--surface);cursor:pointer;font-size:.75rem;color:var(--text2)}
.timer-controls button:hover{background:var(--surface2)}
.timer-controls .btn-accent{background:var(--accent);color:#fff;border-color:var(--accent)}

/* ── Reading calendar ── */
.cal-wrap{overflow-x:auto;padding:4px 0}
.cal-grid{display:grid;grid-template-rows:repeat(7,12px);grid-auto-flow:column;gap:2px;width:max-content}
.cal-cell{width:12px;height:12px;border-radius:2px;background:var(--surface2)}
.cal-cell.l1{background:#bbf7d0}.cal-cell.l2{background:#4ade80}.cal-cell.l3{background:#16a34a}.cal-cell.l4{background:#14532d}
body.dark .cal-cell.l1{background:#14532d}body.dark .cal-cell.l2{background:#166534}body.dark .cal-cell.l3{background:#15803d}body.dark .cal-cell.l4{background:#4ade80}
.cal-months{display:flex;width:max-content;gap:0;margin-bottom:3px}
.cal-month-lbl{font-size:.6rem;color:var(--text3);width:max-content}
.cal-legend{display:flex;align-items:center;gap:4px;margin-top:4px;font-size:.62rem;color:var(--text3)}
.cal-legend-cell{width:10px;height:10px;border-radius:2px}

/* ── Genre pie chart ── */
.genre-chart{display:flex;gap:12px;flex-wrap:wrap;align-items:flex-start}
.genre-pie-wrap{flex-shrink:0}
.genre-legend{flex:1;min-width:120px}
.genre-legend-item{display:flex;align-items:center;gap:5px;font-size:.72rem;margin-bottom:3px;cursor:pointer}
.genre-legend-dot{width:10px;height:10px;border-radius:50%;flex-shrink:0}
.genre-legend-label{color:var(--text2);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:120px}
.genre-legend-pct{color:var(--text3);margin-left:auto;flex-shrink:0}

/* ── Achievements ── */
.achieve-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:8px;margin-top:6px}
.achieve-card{background:var(--surface2);border-radius:10px;padding:10px 8px;text-align:center;border:2px solid transparent;transition:border-color .2s}
.achieve-card.earned{border-color:var(--accent);background:var(--surface)}
.achieve-card.locked{opacity:.45}
.achieve-icon{font-size:1.6rem;line-height:1;margin-bottom:4px}
.achieve-name{font-size:.68rem;font-weight:700;color:var(--text);line-height:1.3}
.achieve-desc{font-size:.6rem;color:var(--text2);margin-top:2px;line-height:1.35}

/* ── Bulk selection ── */
.bulk-bar{display:none;position:sticky;top:0;z-index:99;background:var(--accent);color:#fff;padding:8px 14px;font-size:.8rem;align-items:center;gap:8px;flex-wrap:wrap}
.bulk-bar.show{display:flex}
.bulk-bar select{padding:4px 7px;border-radius:7px;border:none;font-size:.76rem;background:rgba(255,255,255,.2);color:#fff;cursor:pointer}
.bulk-bar select option{background:var(--surface);color:var(--text)}
.card.selected{outline:3px solid var(--accent);outline-offset:2px}
.list-row.selected{outline:3px solid var(--accent);outline-offset:-2px}
.card-checkbox{position:absolute;top:6px;left:6px;z-index:3;display:none;width:18px;height:18px;cursor:pointer;accent-color:var(--accent)}
.bulk-mode .card-checkbox{display:block}

/* ── Swipe gesture feedback ── */
.card{touch-action:pan-y}
.swipe-hint{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:2rem;border-radius:8px;pointer-events:none;opacity:0;transition:opacity .15s;z-index:4}
.swipe-hint-shelf{background:rgba(16,185,129,.3)}

/* ── Share card canvas ── */
.share-card-modal{max-width:440px}
.share-canvas-wrap{text-align:center;margin:10px 0}
.share-canvas-wrap canvas{border-radius:8px;max-width:100%;box-shadow:var(--card-shadow)}

/* ── Widget embed ── */
.widget-preview{border:1px solid var(--border);border-radius:10px;padding:10px;margin:8px 0;background:var(--surface2)}
.widget-code{width:100%;padding:7px;font-family:monospace;font-size:.72rem;background:var(--surface2);border:1px solid var(--border);border-radius:7px;color:var(--text);resize:vertical;min-height:60px}

/* ── Responsive ── */
@media(max-width:600px){
  .header{padding:8px 10px 0}
  .header-top h1{font-size:1rem}
  .filters-toggle{display:block}
  .filters-body{display:none;flex-direction:column;gap:5px;width:100%}
  .filters-body.open{display:flex}
  .filter-row{flex-direction:column;align-items:stretch;gap:5px;padding-bottom:0}
  .filter-row input{min-width:0;width:100%}
  .filter-row select{max-width:100%;width:100%}
  .grid-wrap{padding:7px 5px}
  .book-grid{grid-template-columns:repeat(auto-fill,minmax(108px,1fr));gap:6px}
  .card-body{padding:6px;gap:2px}
  .card-title{font-size:.69rem}
  .card-author{font-size:.61rem}
  .badge{font-size:.55rem;padding:1px 4px}
  .card-summary{-webkit-line-clamp:2}
  .modal{padding:14px;border-radius:10px}
  .modal-top{flex-direction:column}
  .modal-cover img,.no-cover-lg{width:100%;max-width:160px;margin:0 auto}
  .count-row{gap:4px}
  .btn-sm{font-size:.7rem;padding:3px 6px}
  .stat-grid{grid-template-columns:1fr 1fr}
}

/* ── Multi-filter dropdowns ── */
.mf-wrap{position:relative;display:inline-block}
.mf-btn{display:flex;align-items:center;gap:5px;padding:5px 9px;border:1px solid var(--border);border-radius:8px;font-size:.78rem;background:var(--surface);color:var(--text);cursor:pointer;white-space:nowrap;transition:border-color .15s}
.mf-btn:hover{border-color:var(--accent)}
.mf-btn.active{border-color:var(--accent);background:var(--surface2)}
.mf-badge{background:var(--accent);color:#fff;border-radius:10px;padding:1px 6px;font-size:.68rem;font-weight:700;line-height:1.4}
.mf-arrow{font-size:.6rem;color:var(--text3)}
.mf-panel{display:none;position:absolute;top:calc(100% + 4px);left:0;z-index:300;background:var(--surface);border:1px solid var(--border);border-radius:10px;box-shadow:0 6px 24px rgba(0,0,0,.15);min-width:200px;max-width:280px;padding:6px 0}
.mf-panel.open{display:flex;flex-direction:column}
.mf-search-wrap{padding:6px 8px;border-bottom:1px solid var(--border)}
.mf-search{width:100%!important;padding:4px 8px!important;border:1px solid var(--border)!important;border-radius:6px!important;font-size:.78rem!important;background:var(--surface2)!important;color:var(--text)!important;box-sizing:border-box!important;flex:none!important;min-width:0!important}
.mf-opts{max-height:220px;overflow-y:auto;padding:4px 0}
.mf-opt{display:flex;align-items:center;gap:8px;padding:5px 12px;font-size:.8rem;color:var(--text);cursor:pointer;transition:background .1s}
.mf-opt:hover{background:var(--surface2)}
.mf-opt input[type=checkbox]{accent-color:var(--accent);width:14px!important;height:14px!important;cursor:pointer!important;flex:none!important;min-width:0!important;padding:0!important;border:1px solid var(--border)!important;border-radius:3px!important;background:none!important}
.mf-opt span{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.mf-footer{display:flex;align-items:center;justify-content:space-between;padding:6px 10px;border-top:1px solid var(--border);margin-top:2px}
.mf-clear-btn{font-size:.72rem;color:var(--accent);cursor:pointer;background:none;border:none;padding:0}
.mf-clear-btn:hover{text-decoration:underline}
.mf-count-lbl{font-size:.7rem;color:var(--text3)}
@media(max-width:600px){.mf-panel{max-width:calc(100vw - 24px)}}

/* ── External book form ── */
.ext-lbl{font-size:.78rem;font-weight:600;display:block;margin-bottom:3px;color:var(--text)}
.ext-inp{width:100%;padding:7px 9px;border:1px solid var(--border);border-radius:6px;background:var(--surface2);color:var(--text);font-size:.82rem;box-sizing:border-box}
.ext-inp:focus{outline:2px solid var(--accent);outline-offset:-1px}
.ext-shelf-chip{padding:4px 10px;border:1px solid var(--border);border-radius:20px;background:var(--surface);color:var(--text2);cursor:pointer;font-size:.75rem;transition:all .12s;user-select:none}
.ext-shelf-chip.on{background:var(--accent);color:#fff;border-color:var(--accent)}
.ext-book-banner{background:#fef3c7;color:#92400e;border-radius:8px;padding:8px 12px;font-size:.78rem;display:flex;align-items:center;gap:8px;margin-bottom:12px}
.dark .ext-book-banner{background:#451a03;color:#fcd34d}
.ext-lookup-row{display:flex;gap:6px;margin-bottom:10px}
.ext-lookup-inp{flex:1;padding:7px 9px;border:1px solid var(--border);border-radius:6px;background:var(--surface2);color:var(--text);font-size:.82rem;box-sizing:border-box}
.ext-lookup-inp:focus{outline:2px solid var(--accent);outline-offset:-1px}
.ext-lookup-btn{padding:7px 11px;border:none;border-radius:6px;background:var(--accent);color:#fff;cursor:pointer;font-size:.8rem;white-space:nowrap;flex-shrink:0}
.ext-lookup-btn:disabled{opacity:.5;cursor:default}
.ext-results{display:flex;flex-direction:column;gap:5px;margin-bottom:10px;max-height:240px;overflow-y:auto}
.ext-result-card{display:flex;gap:8px;padding:7px 9px;border:1px solid var(--border);border-radius:8px;cursor:pointer;background:var(--surface);transition:background .12s;align-items:flex-start}
.ext-result-card:hover{background:var(--surface2);border-color:var(--accent)}
.ext-result-img{width:30px;height:45px;object-fit:cover;border-radius:3px;flex-shrink:0;background:var(--surface2)}
.ext-result-img-ph{width:30px;height:45px;border-radius:3px;flex-shrink:0;background:var(--surface2);display:flex;align-items:center;justify-content:center;font-size:1rem}
.ext-result-info{min-width:0;flex:1}
.ext-result-title{font-size:.78rem;font-weight:700;color:var(--text);overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical}
.ext-result-author{font-size:.72rem;color:var(--text2);margin-top:1px}
.ext-result-meta{font-size:.68rem;color:var(--text3);margin-top:2px}
.ext-divider{border:none;border-top:1px solid var(--border);margin:4px 0 10px}
"""
print("CSS done")

# ── JavaScript ────────────────────────────────────────────────────────────────
JS = r"""
const ALL  = JSON.parse(document.getElementById('bdata').textContent);
const META = JSON.parse(document.getElementById('mdata').textContent);
let filtered=[], rendered=0;
const PAGE=60;

/* ── Utils ── */
function esc(s){ return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;') }
function imgErr(el){ el.parentNode.innerHTML='<div class="no-cover">📚</div>' }
function imgEl(src,t){ if(!src)return'<div class="no-cover">📚</div>';return`<img class="card-cover" src="${esc(src)}" alt="${esc(t)}" loading="lazy" onerror="imgErr(this)">` }
function miniImgErr(el){ el.parentNode.innerHTML='<div class="mini-no-cover">📚</div>' }
function miniImgEl(src,t){ if(!src)return'<div class="mini-no-cover">📚</div>';return`<img class="mini-cover" src="${esc(src)}" alt="${esc(t)}" loading="lazy" onerror="miniImgErr(this)">` }

/* ── LocalStorage helpers ── */
function lsGet(k,def={}){ try{const v=localStorage.getItem(k); return v?JSON.parse(v):def}catch{return def} }
function lsSet(k,v){ try{localStorage.setItem(k,JSON.stringify(v))}catch{} }
function lsGetRatings(){ return lsGet('mcl_ratings') }
function lsGetNotes(){ return lsGet('mcl_notes') }
function lsGetRecent(){ return lsGet('mcl_recent',[]) }
function lsGetProgress(){ return lsGet('mcl_progress') }
function lsGetDates(){ return lsGet('mcl_dates') }
function lsGetLoans(){ return lsGet('mcl_loans') }

/* ── Dark mode ── */
let darkMode = lsGet('mcl_dark','0')==='1';
function initDark(){ document.body.classList.toggle('dark',darkMode); document.getElementById('darkBtn').textContent=darkMode?'☀️':'🌙'; }
function toggleDark(){ darkMode=!darkMode; lsSet('mcl_dark',darkMode?'1':'0'); initDark(); }

/* ── View (grid/list/spine) ── */
const VIEWS = ['grid','list','spine'];
let viewIdx = Math.max(0, VIEWS.indexOf(lsGet('mcl_view','grid')));
function curView(){ return VIEWS[viewIdx] }
function initView(){
  document.getElementById('grid-wrap').className = 'grid-wrap view-'+curView();
  document.getElementById('viewBtn').textContent = curView()==='grid'?'≡':curView()==='list'?'⊟':'📚';
}
function toggleView(){ viewIdx=(viewIdx+1)%VIEWS.length; lsSet('mcl_view',curView()); initView(); renderPage(); }
function renderPage(){ const g=document.getElementById('book-grid'); g.innerHTML=''; rendered=0; renderMore(); }

/* ── Book map ── */
const bookMap={};ALL.forEach(b=>bookMap[b.id]=b);

/* ── Ratings ── */
function getRating(id){ return lsGetRatings()[id]||0 }
function setRating(id,r){
  const d=lsGetRatings(); d[id]=r; lsSet('mcl_ratings',d); triggerSync();
  document.querySelectorAll(`[data-stars-id="${id}"]`).forEach(el=>renderStarRow(el,id));
}
function starsHTML(id, interactive=false, cls='card-star'){
  const r=getRating(id);
  const stars=[1,2,3,4,5].map(n=>`<span class="${cls}${n<=r?' filled':''}" data-n="${n}">★</span>`).join('');
  return stars;
}
function renderStarRow(container,id){
  const r=getRating(id);
  container.innerHTML=[1,2,3,4,5].map(n=>`<span class="card-star${n<=r?' filled':''}" data-n="${n}">★</span>`).join('');
}

/* ── Recently viewed ── */
function pushRecent(id){
  let r=lsGetRecent().filter(x=>x!==id);
  r.unshift(id); r=r.slice(0,10);
  lsSet('mcl_recent',r); triggerSync();
  renderRecentStrip();
}
function renderRecentStrip(){
  const rec=lsGetRecent().map(id=>bookMap[id]).filter(Boolean);
  const strip=document.getElementById('recent-strip');
  const toggleBtn=document.getElementById('recent-toggle');
  if(!strip)return;
  if(!rec.length){
    if(toggleBtn)toggleBtn.style.display='none';
    return;
  }
  if(toggleBtn)toggleBtn.style.display='flex';
  _applyRecentState();
  strip.style.display='flex';
  strip.innerHTML=`<span class="recent-lbl">Recently viewed</span>`+rec.map(b=>`
    <div class="recent-thumb" onclick="openModal('${esc(b.id)}')" title="${esc(b.t)}">
      ${b.img?`<img src="${esc(b.img)}" alt="${esc(b.t)}" loading="lazy" onerror="this.parentNode.innerHTML='<div class=\'no-r\'>📚</div>'">`:`<div class="no-r">📚</div>`}
    </div>`).join('');
}

/* ── Book of the Day (weighted) ── */
function getBookOfDay(){
  const d=new Date(); const seed=d.getFullYear()*10000+(d.getMonth()+1)*100+d.getDate();
  const shelves=loadShelves();
  const reading=new Set(shelves.reading||[]);
  const recent=lsGetRecent();
  const dates=lsGetDates();
  const weighted=[];
  for(let i=0;i<ALL.length;i++){
    const b=ALL[i];
    let w=1; // base weight
    if(reading.has(b.id))w=5; // on reading shelf
    else if(!recent.includes(b.id))w=3; // never viewed
    else {
      // in series check — if prev book finished
      if(b.sr){
        const allInSeries=ALL.filter(x=>x.sr===b.sr);
        const idx=allInSeries.findIndex(x=>x.id===b.id);
        if(idx>0){
          const prevBook=allInSeries[idx-1];
          const prevFinished=dates[prevBook.id]?.finished;
          if(prevFinished)w=4;
        }
      }
      // old unread: weight by position
      const recIdx=recent.indexOf(b.id);
      if(recIdx<0)w=2;
      else w=2-(i/ALL.length);
    }
    for(let j=0;j<w;j++)weighted.push(b);
  }
  if(!weighted.length)return ALL[0];
  let hash=seed;
  for(let i=0;i<7;i++){hash=(hash*1664525+1013904223)>>>0}
  return weighted[hash%weighted.length];
}
function toggleBotdPanel(){
  const show=lsGet('mcl_show_botd','0')==='1';
  lsSet('mcl_show_botd',show?'0':'1');
  _applyBotdState();
}
function _applyBotdState(){
  const show=lsGet('mcl_show_botd','0')==='1';
  const wrap=document.getElementById('botd-wrap');
  const btn=document.getElementById('botd-toggle');
  if(wrap)wrap.style.display=show?'':'none';
  if(btn)btn.classList.toggle('open',show);
  if(show)renderBotd();
}
function toggleRecentPanel(){
  const show=lsGet('mcl_show_recent','0')==='1';
  lsSet('mcl_show_recent',show?'0':'1');
  _applyRecentState();
}
function _applyRecentState(){
  const show=lsGet('mcl_show_recent','0')==='1';
  const wrap=document.getElementById('recent-wrap');
  const btn=document.getElementById('recent-toggle');
  if(wrap)wrap.style.display=show?'':'none';
  if(btn)btn.classList.toggle('open',show);
}
function renderBotd(){
  const b=getBookOfDay();
  const el=document.getElementById('botd-bar');
  if(!el||!b)return;
  el.innerHTML=`${b.img?`<img src="${esc(b.img)}" alt="${esc(b.t)}" onerror="this.style.display='none'">`:'📖'}
    <div style="min-width:0;flex:1">
      <div class="botd-lbl">📅 Book of the Day</div>
      <div class="botd-title">${esc(b.t)}</div>
      <div class="botd-author">${esc(b.a)}</div>
    </div>`;
  el.onclick=()=>openModal(b.id);
}

/* ── Fuzzy search ── */
function searchScore(b, q){
  if(!q) return 1;
  const title  = (b.t  ||'').toLowerCase();
  const author = (b.a  ||'').toLowerCase();
  const cat    = (b.c  ||'').toLowerCase();
  const series = (b.sr ||'').toLowerCase();
  const loc    = (b.l  ||'').toLowerCase();
  const fmt    = (b.f  ||'').toLowerCase();
  const desc   = (b.s  ||'').toLowerCase();
  const tags   = (b.tg ||[]).join(' ').toLowerCase().replace(/-/g,' ');
  const meta   = [cat,series,loc,fmt].join(' ');
  if(title.includes(q))  return 1000+(title.indexOf(q)===0?200:0);
  if(author.includes(q)) return 900;
  if(meta.includes(q))   return 700;
  if(tags.includes(q))   return 600;
  if(desc.includes(q))   return 500;
  const tokens=q.split(/\s+/).filter(Boolean);
  if(!tokens.length) return 1;
  let score=0, matched=0;
  for(const tok of tokens){
    let best=0;
    if(title.includes(tok))  best=Math.max(best,20);
    if(author.includes(tok)) best=Math.max(best,16);
    if(cat.includes(tok)||series.includes(tok)||fmt.includes(tok)||loc.includes(tok)) best=Math.max(best,10);
    if(tags.includes(tok))   best=Math.max(best,8);
    if(desc.includes(tok))   best=Math.max(best,4);
    if(best===0&&tok.length>=3){
      const re=new RegExp('(?:^|\\s|-)'+tok.replace(/[.*+?^${}()|[\]\\]/g,'\\$&'));
      if(re.test([title,author,meta,tags,desc].join(' '))) best=2;
    }
    if(best>0){matched++;score+=best;}
  }
  if(matched<Math.max(1,Math.ceil(tokens.length*0.6))) return 0;
  return score;
}

/* ── Search highlighting ── */
let _q='';
function highlight(text){
  if(!_q||!text) return esc(text);
  // highlight individual tokens
  let highlighted=esc(text);
  const tokens=_q.split(/\s+/).filter(Boolean);
  for(const tok of tokens){
    const regex=new RegExp(`(${tok.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')})`, 'gi');
    highlighted=highlighted.replace(regex,'<mark>$1</mark>');
  }
  return highlighted;
}

/* ── Filter & sort ── */
function setFilter(key,val){
  const map={author:'author',category:'cat',format:'fmt',location:'loc',tag:'tag',series:'series',shelf:'shelf'};
  const mfKey=map[key];
  if(mfKey){mfSetValue(mfKey,val);applyF();}
}
function toggleFilters(){
  const body=document.getElementById('filters-body');
  const btn=document.querySelector('.filters-toggle');
  const open=body.classList.toggle('open');
  btn.textContent=open?'✕ Hide filters':'⚙ Filters';
}
/* ════════════════════════════════════════════════════════════════
   MULTI-FILTER ENGINE
   ════════════════════════════════════════════════════════════════ */
const _mf={author:new Set(),cat:new Set(),fmt:new Set(),loc:new Set(),tag:new Set(),series:new Set(),shelf:new Set()};
const _mfOpts={};
const _mfLabels={author:'Author',cat:'Category',fmt:'Format',loc:'Location',tag:'Tag',series:'Series',shelf:'Shelf'};
let _mfOpenKey=null;

function mfInit(key,selectId){
  const sel=document.getElementById(selectId);
  if(!sel)return;
  if(document.getElementById('mf-wrap-'+key))return;
  const toLabel=key==='tag'?(v=>v.replace(/-/g,' ').replace(/\b\w/g,c=>c.toUpperCase())):((v,t)=>t);
  const opts=[...sel.options].filter(o=>o.value).map(o=>({v:o.value,l:toLabel(o.value,o.text)}));
  _mfOpts[key]=opts;
  const wrap=document.createElement('div');
  wrap.className='mf-wrap'; wrap.id='mf-wrap-'+key;
  wrap.innerHTML=`<button class="mf-btn" id="mf-btn-${key}" onclick="mfToggle('${key}')"><span id="mf-label-${key}">${_mfLabels[key]}</span><span class="mf-badge" id="mf-badge-${key}" style="display:none"></span><span class="mf-arrow">&#9662;</span></button>`;
  sel.parentNode.insertBefore(wrap,sel);
  sel.style.display='none';
}

// Shared portal panel attached to <body>
let _mfPortal=null;
function _getMfPortal(){
  if(!_mfPortal){
    _mfPortal=document.createElement('div');
    _mfPortal.id='mf-portal';
    _mfPortal.style.cssText='position:fixed;z-index:9999;background:var(--surface);border:1px solid var(--border);border-radius:10px;box-shadow:0 6px 24px rgba(0,0,0,.18);min-width:220px;max-width:300px;display:none;flex-direction:column;font-size:.82rem;color:var(--text);font-family:inherit';
    document.body.appendChild(_mfPortal);
  }
  return _mfPortal;
}

function mfToggle(key){
  const btn=document.getElementById('mf-btn-'+key);
  if(!btn)return;
  const portal=_getMfPortal();
  const isOpen=_mfOpenKey===key&&portal.style.display!=='none';
  portal.style.display='none'; _mfOpenKey=null;
  if(isOpen)return;
  const opts=_mfOpts[key]||[];
  const selected=_mf[key]||new Set();
  portal.innerHTML=`
    <div style="padding:7px 8px;border-bottom:1px solid var(--border)">
      <input id="mf-portal-search" type="text" placeholder="Search ${_mfLabels[key]}\u2026"
        style="width:100%;padding:5px 8px;border:1px solid var(--border);border-radius:6px;font-size:.8rem;background:var(--surface2);color:var(--text);box-sizing:border-box;outline:none;display:block"
        oninput="mfSearch('${key}',this.value)">
    </div>
    <div id="mf-opts-${key}" style="max-height:240px;overflow-y:auto;padding:4px 0">
      ${opts.map(o=>`<label style="display:flex;align-items:center;gap:8px;padding:6px 12px;cursor:pointer" onmouseover="this.style.background='var(--surface2)'" onmouseout="this.style.background=''">
        <input type="checkbox" value="${esc(o.v)}" ${selected.has(o.v)?'checked':''} onchange="mfChange('${key}',this)" style="width:14px;height:14px;flex-shrink:0;cursor:pointer;accent-color:var(--accent);margin:0">
        <span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${esc(o.l)}">${esc(o.l)}</span>
      </label>`).join('')}
    </div>
    <div style="display:flex;align-items:center;justify-content:space-between;padding:6px 10px;border-top:1px solid var(--border)">
      <span style="font-size:.7rem;color:var(--text3)" id="mf-cnt-${key}">${selected.size?selected.size+' selected':''}</span>
      <button onclick="mfClearKey('${key}')" style="font-size:.72rem;color:var(--accent);background:none;border:none;cursor:pointer;padding:0">Clear</button>
    </div>`;
  const rect=btn.getBoundingClientRect();
  portal.style.display='flex';
  const pw=Math.min(300,window.innerWidth-16);
  portal.style.minWidth=pw+'px';
  let left=rect.left;
  if(left+pw>window.innerWidth-8) left=window.innerWidth-8-pw;
  if(left<8) left=8;
  portal.style.left=left+'px';
  portal.style.top=(rect.bottom+4)+'px';
  const ph=portal.getBoundingClientRect().height;
  if(rect.bottom+4+ph>window.innerHeight-8) portal.style.top=(rect.top-4-ph)+'px';
  _mfOpenKey=key;
  const si=document.getElementById('mf-portal-search');
  if(si)si.focus();
}

document.addEventListener('click',function(e){
  if(!_mfOpenKey)return;
  const portal=document.getElementById('mf-portal');
  if(portal&&!portal.contains(e.target)&&!e.target.closest('.mf-wrap')){
    portal.style.display='none'; _mfOpenKey=null;
  }
});

function mfChange(key,cb){
  if(cb.checked) _mf[key].add(cb.value);
  else _mf[key].delete(cb.value);
  mfUpdateLabel(key);
  applyF();
}

function mfClearKey(key){
  _mf[key].clear();
  const container=document.getElementById('mf-opts-'+key);
  if(container)container.querySelectorAll('input[type=checkbox]').forEach(cb=>cb.checked=false);
  mfUpdateLabel(key); applyF();
}

function mfUpdateLabel(key){
  const n=_mf[key].size;
  const badge=document.getElementById('mf-badge-'+key);
  const btn=document.getElementById('mf-btn-'+key);
  if(badge){badge.textContent=n;badge.style.display=n?'':'none';}
  if(btn){btn.classList.toggle('active',n>0);}
  const cnt=document.getElementById('mf-cnt-'+key);
  if(cnt)cnt.textContent=n?n+' selected':'';
}

function mfSearch(key,q){
  const container=document.getElementById('mf-opts-'+key);
  if(!container)return;
  const labels=container.querySelectorAll('label');
  const lq=q.toLowerCase();
  labels.forEach(el=>{
    const cb=el.querySelector('input[type=checkbox]');
    const val=(cb?cb.value:'').toLowerCase().replace(/-/g,' ');
    const lbl=(el.querySelector('span')||el).textContent.toLowerCase();
    el.style.display=(!lq||val.includes(lq)||lbl.includes(lq))?'':'none';
  });
}

function mfSetValue(key,val){
  mfClearKey(key);
  if(!val)return;
  _mf[key].add(val);
  const cb=document.querySelector(\`#mf-opts-\${key} input[value="\${CSS.escape(val)}"]\`);
  if(cb)cb.checked=true;
  mfUpdateLabel(key);
}

let _mfInitted=false;
function mfInitAll(){
  if(_mfInitted)return; _mfInitted=true;
  mfInit('author','fAuthor');
  mfInit('cat','fCat');
  mfInit('fmt','fFmt');
  mfInit('loc','fLoc');
  mfInit('tag','fTag');
  mfInit('series','fSeries');
  mfInit('shelf','fShelf');
  const cat2=document.getElementById('fCat2'); if(cat2)cat2.remove();
}

function applyF(){
  _q=document.getElementById('q').value.toLowerCase().trim();
  const sort=document.getElementById('fSort').value;
  const minP=parseInt(document.getElementById('fMinP').value)||0;
  const maxP=parseInt(document.getElementById('fMaxP').value)||Infinity;
  const minR=parseInt(document.getElementById('fMinR').value)||0;
  const ratings=lsGetRatings();
  const shelves=loadShelves();
  const scoreMap=new Map();
  if(_q) ALL.forEach(b=>{const s=searchScore(b,_q);if(s>0)scoreMap.set(b.id,s);});
  filtered=ALL.filter(b=>{
    if(_q&&!scoreMap.has(b.id))return false;
    if(_mf.author.size&&!_mf.author.has(b.a))return false;
    if(_mf.cat.size&&!_mf.cat.has(b.c))return false;
    if(_mf.fmt.size&&!_mf.fmt.has(b.f))return false;
    if(_mf.loc.size&&!_mf.loc.has(b.l))return false;
    if(_mf.tag.size&&![..._mf.tag].some(t=>(b.tg||[]).includes(t)))return false;
    if(_mf.series.size&&!_mf.series.has(b.sr))return false;
    if(_mf.shelf.size&&![..._mf.shelf].some(sid=>(shelves[sid]||[]).includes(b.id)))return false;
    if(minP&&(b.p||0)<minP)return false;
    if(maxP<Infinity&&(b.p||0)>maxP)return false;
    if(minR&&(ratings[b.id]||0)<minR)return false;
    return true;
  });
  if(_q) filtered.sort((a,b)=>(scoreMap.get(b.id)||0)-(scoreMap.get(a.id)||0));
  if(sort==='title_az')filtered.sort((a,b)=>a.t.localeCompare(b.t));
  else if(sort==='title_za')filtered.sort((a,b)=>b.t.localeCompare(a.t));
  else if(sort==='author_az')filtered.sort((a,b)=>a.a.localeCompare(b.a));
  else if(sort==='pages_asc')filtered.sort((a,b)=>(a.p||0)-(b.p||0));
  else if(sort==='pages_desc')filtered.sort((a,b)=>(b.p||0)-(a.p||0));
  else if(sort==='rating_desc'){const r=lsGetRatings();filtered.sort((a,b)=>(r[b.id]||0)-(r[a.id]||0));}
  document.getElementById('countLbl').textContent=`Showing ${filtered.length.toLocaleString()} of ${ALL.length.toLocaleString()}`;
  renderPage(); syncURL();
}
function clearF(){
  document.getElementById('q').value='';
  Object.keys(_mf).forEach(k=>mfClearKey(k));
  ['fSort','fMinR'].forEach(id=>{const el=document.getElementById(id);if(el)el.value='';});
  ['fMinP','fMaxP'].forEach(id=>{const el=document.getElementById(id);if(el)el.value='';});
  applyF();
}
function surpriseMe(){ if(!filtered.length)return; openModal(filtered[Math.floor(Math.random()*filtered.length)].id); }

/* ── Card rendering ── */
function cardHTML(b){
  const tags=(b.tg||[]).map(t=>`<span class="tag-pill" onclick="event.stopPropagation();setFilter('tag','${esc(t)}')">${highlight(t)}</span>`).join('');
  const notes=lsGetNotes(); const loans=lsGetLoans();
  const corners=[notes[b.id]?'<div class="note-dot" title="Has notes"></div>':'',loans[b.id]?'<div class="loan-dot" title="Lent out"></div>':''].join('');
  const r=getRating(b.id);
  const starHtml=`<div class="card-stars" data-stars-id="${esc(b.id)}" onclick="event.stopPropagation()">${[1,2,3,4,5].map(n=>`<span class="card-star${n<=r?' filled':''}" data-n="${n}" onclick="event.stopPropagation();cardStarClick(event,'${esc(b.id)}')">★</span>`).join('')}</div>`;
  const pctStr=lsGetProgress()[b.id];
  const progBar=b.tg&&false||true?'':(pctStr?`<div class="progress-mini-wrap"><div class="progress-mini-lbl">${pctStr}%</div><div class="progress-mini-bar"><div class="progress-mini-fill" style="width:${pctStr}%"></div></div></div>`:'');
  const sumId='sum-'+esc(b.id),togId='tog-'+esc(b.id);
  const sumHTML=b.s?`<div class="card-summary" id="${sumId}">${highlight(b.s)}</div><button class="summary-toggle" id="${togId}" onclick="event.stopPropagation();toggleSum('${esc(b.id)}')">Read more ↓</button>`:'';
  const amazonBtn=b.url?`<div class="amazon-btn"><a href="${esc(b.url)}" target="_blank" onclick="event.stopPropagation()">View on Amazon →</a></div>`:'';
  const cardEl=`<div class="card" tabindex="0" id="card-${esc(b.id)}" onclick="if(_bulkMode){toggleBulkSelect('${esc(b.id)}',this)}else{openModal('${esc(b.id)}')}" onkeydown="if(event.key==='Enter'&&!_bulkMode)openModal('${esc(b.id)}')" data-book-id="${esc(b.id)}">
    <input type="checkbox" class="card-checkbox" onclick="event.stopPropagation();toggleBulkSelect('${esc(b.id)}',this.closest('.card'))">
    <div class="swipe-hint swipe-hint-shelf">\uD83D\uDCDA Added!</div>
    ${corners?`<div class="card-corner-badges">${corners}</div>`:''}
    ${imgEl(b.img,b.t)}
    <div class="card-body">
      <div class="card-title">${highlight(b.t)}</div>
      <div class="card-author" onclick="event.stopPropagation();openAuthorModal('${esc(b.a)}')">${highlight(b.a)}</div>
      <div class="badges">
        ${b.ext?`<span class="badge" style="background:#fef3c7;color:#92400e;font-size:.55rem" title="External book (not in library)">📝</span>`:''}
        ${b.f?`<span class="badge badge-format" onclick="event.stopPropagation();setFilter('format','${esc(b.f)}')">${esc(b.f)}</span>`:''}
        ${b.c?`<span class="badge badge-category" onclick="event.stopPropagation();setFilter('category','${esc(b.c)}')">${esc(b.c)}</span>`:''}
        ${b.l?`<span class="badge badge-location" onclick="event.stopPropagation();setFilter('location','${esc(b.l)}')">${esc(b.l)}</span>`:''}
      </div>
      ${b.p?`<div class="card-pages">${b.p} pages</div>`:''}
      ${starHtml}
      <div class="card-tags">${tags}</div>
      ${sumHTML}${amazonBtn}
    </div>
  </div>`;
  // Register swipe after DOM insertion (next tick)
  requestAnimationFrame(function(){const el=document.getElementById('card-'+esc(b.id));if(el)addSwipeToCard(el,b.id);});
  return cardEl;
}
function cardStarClick(e,id){
  e.stopPropagation();
  const n=parseInt(e.target.dataset.n||0);
  const cur=getRating(id);
  setRating(id, n===cur?0:n);
}
function toggleSum(id){ const el=document.getElementById('sum-'+id),btn=document.getElementById('tog-'+id); if(!el||!btn)return; const ex=el.classList.toggle('expanded'); btn.textContent=ex?'Show less ↑':'Read more ↓'; }

/* ── List row rendering ── */
function listRowHTML(b){
  const r=getRating(b.id);
  const starHtml=[1,2,3,4,5].map(n=>`<span class="list-star${n<=r?' filled':''}">★</span>`).join('');
  const coverEl=b.img?`<img class="list-cover" src="${esc(b.img)}" alt="${esc(b.t)}" loading="lazy" onerror="this.parentNode.innerHTML='<div class=\'list-no-cover\'>📚</div>'">`:`<div class="list-no-cover">📚</div>`;
  return`<div class="list-row" tabindex="0" onclick="openModal('${esc(b.id)}')" onkeydown="if(event.key==='Enter')openModal('${esc(b.id)}')">
    ${coverEl}
    <div class="list-info">
      <div class="list-title">${highlight(b.t)}</div>
      <div class="list-author" onclick="event.stopPropagation();openAuthorModal('${esc(b.a)}')">${highlight(b.a)}</div>
      <div class="badges" style="margin-top:3px">
        ${b.f?`<span class="badge badge-format">${esc(b.f)}</span>`:''}
        ${b.c?`<span class="badge badge-category">${esc(b.c)}</span>`:''}
      </div>
    </div>
    <div class="list-right">
      <div class="list-stars">${starHtml}</div>
      ${b.p?`<div class="list-pages">${b.p}p</div>`:''}
    </div>
  </div>`;
}

/* ── Spine rendering ── */
const SPINE_COLORS=['#4f46e5','#7c3aed','#0891b2','#065f46','#92400e','#991b1b','#1d4ed8','#5b21b6','#047857','#b45309'];
const catColorMap={};
function spineColor(b){
  if(!catColorMap[b.c]){ catColorMap[b.c]=SPINE_COLORS[Object.keys(catColorMap).length%SPINE_COLORS.length]; }
  return catColorMap[b.c]||'#4f46e5';
}
function spineHTML(b){
  const h=Math.min(180,Math.max(100, b.p?Math.round(b.p/4)+70:130));
  const w=28;
  const col=spineColor(b);
  const titleCapped=b.t.length>40?b.t.slice(0,38)+'…':b.t;
  return`<div class="spine" style="width:${w}px;height:${h}px;background:${col}" tabindex="0"
      onclick="openModal('${esc(b.id)}')" onkeydown="if(event.key==='Enter')openModal('${esc(b.id)}')"
      title="${esc(b.t)} — ${esc(b.a)}">
    ${b.img
      ?`<img class="spine-cover" src="${esc(b.img)}" alt="${esc(b.t)}" loading="lazy" onerror="this.style.display='none'">`
      :`<div class="spine-no-cover"><span class="spine-title">${esc(titleCapped)}</span></div>`}
  </div>`;
}

/* ── renderMore ── */
function renderMore(){
  const grid=document.getElementById('book-grid');
  const chunk=filtered.slice(rendered,rendered+PAGE);
  const fn=curView()==='list'?listRowHTML:curView()==='spine'?spineHTML:cardHTML;
  grid.insertAdjacentHTML('beforeend',chunk.map(fn).join(''));
  rendered+=chunk.length;
}

/* ── Excel Export ── */
function exportXLSX(){
  if(typeof XLSX==='undefined'){exportCSVFallback();return;}
  const ratings=lsGetRatings(), notes=lsGetNotes();
  const headers=['Title','Author','Format','Category','Location','Pages','Series','Tags','Rating','Notes','Summary','Amazon URL'];
  const wsData=[headers,...filtered.map(b=>[
    b.t,b.a,b.f,b.c,b.l,b.p||'',b.sr||'',(b.tg||[]).join('; '),ratings[b.id]||'',notes[b.id]||'',b.s,b.url
  ])];
  const ws=XLSX.utils.aoa_to_sheet(wsData);
  ws['!cols']=[{wch:38},{wch:23},{wch:10},{wch:16},{wch:12},{wch:6},{wch:20},{wch:28},{wch:7},{wch:30},{wch:55},{wch:38}];
  const wb=XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb,ws,'Library');
  XLSX.writeFile(wb,`McLemore-Library-${new Date().toISOString().slice(0,10)}.xlsx`);
}
function exportCSVFallback(){
  const ratings=lsGetRatings(),notes=lsGetNotes();
  const headers=['Title','Author','Format','Category','Location','Pages','Tags','Rating','Notes','Summary','Amazon URL'];
  const escCSV=v=>'"'+String(v||'').replace(/"/g,'""')+'"';
  const rows=filtered.map(b=>[b.t,b.a,b.f,b.c,b.l,b.p||'',(b.tg||[]).join('; '),ratings[b.id]||'',notes[b.id]||'',b.s,b.url].map(escCSV).join(','));
  const csv=[headers.join(','),...rows].join('\r\n');
  const blob=new Blob(['\uFEFF'+csv],{type:'text/csv;charset=utf-8'});
  const a=document.createElement('a'); a.href=URL.createObjectURL(blob);
  a.download=`McLemore-Library-${new Date().toISOString().slice(0,10)}.csv`;
  document.body.appendChild(a);a.click();document.body.removeChild(a);
}

/* ── Print view ── */
function printList(){
  // If in shelf view, print that shelf; otherwise print filtered list
  if(_shelfView){
    const shelves=loadShelves();
    const ids=(shelves[_shelfView]||[]);
    const bks=ids.map(id=>bookMap[id]).filter(Boolean);
    const allShelves=getAllShelves();
    const def=allShelves.find(d=>d.id===_shelfView);
    printShelf(_shelfView, def, bks);
  } else {
    window.print();
  }
}
function printShelf(shelfId, shelfDef, books){
  const ratings=lsGetRatings();
  const notes=lsGetNotes();
  const rows=books.map((b,idx)=>`
    <tr>
      <td style="padding:8px;border-bottom:1px solid #ddd;text-align:center;width:40px">${idx+1}</td>
      <td style="padding:8px;border-bottom:1px solid #ddd;text-align:center;width:60px">
        ${b.img?`<img src="${esc(b.img)}" style="width:50px;height:auto;border-radius:3px" onerror="this.style.display='none'">`:''}
      </td>
      <td style="padding:8px;border-bottom:1px solid #ddd"><strong>${esc(b.t)}</strong></td>
      <td style="padding:8px;border-bottom:1px solid #ddd">${esc(b.a)}</td>
      <td style="padding:8px;border-bottom:1px solid #ddd">${esc(b.c||'')}</td>
      <td style="padding:8px;border-bottom:1px solid #ddd;text-align:center">${[1,2,3,4,5].map(n=>`<span style="color:#f59e0b">${n<=(ratings[b.id]||0)?'★':'☆'}</span>`).join('')}</td>
      <td style="padding:8px;border-bottom:1px solid #ddd;font-size:.9em;color:#666">${esc((notes[b.id]||'').slice(0,100))}</td>
    </tr>
  `).join('');
  const html=`<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>${shelfDef.label} - Print List</title>
<style>
  body{font-family:Georgia,serif;background:#fff;color:#222;margin:20px;line-height:1.5}
  h1{font-size:2em;margin-bottom:10px;border-bottom:2px solid #333;padding-bottom:10px}
  .subtitle{color:#666;font-size:.95em;margin-bottom:20px}
  table{width:100%;border-collapse:collapse;margin-top:20px}
  th{background:#f5f5f5;padding:10px;text-align:left;font-weight:600;border-bottom:2px solid #ccc}
  td{padding:8px;border-bottom:1px solid #ddd;vertical-align:top}
  @media print{body{margin:0;font-size:11pt}h1{font-size:1.5em;margin-bottom:8px}table{font-size:10pt}td{padding:6px}}
</style>
</head>
<body>
<h1>${shelfDef.icon} ${shelfDef.label}</h1>
<div class="subtitle">Printed ${new Date().toLocaleDateString()} • ${books.length} book${books.length!==1?'s':''}</div>
<table>
  <thead>
    <tr>
      <th style="width:40px">#</th>
      <th style="width:60px">Cover</th>
      <th>Title</th>
      <th>Author</th>
      <th>Category</th>
      <th style="text-align:center">Rating</th>
      <th>Notes</th>
    </tr>
  </thead>
  <tbody>${rows}</tbody>
</table>
</body>
</html>`;
  const win=window.open('','','width=900,height=700');
  win.document.write(html);
  win.document.close();
  setTimeout(()=>win.print(),500);
}

/* ── URL sync ── */
function syncURL(){
  const params=new URLSearchParams();
  const map={q:'q',author:'fAuthor',cat:'fCat',cat2:'fCat2',fmt:'fFmt',loc:'fLoc',tag:'fTag',sort:'fSort',ser:'fSeries',minp:'fMinP',maxp:'fMaxP',minr:'fMinR',shelf:'fShelf'};
  Object.entries(map).forEach(([k,id])=>{const el=document.getElementById(id);if(el&&el.value)params.set(k,el.value);});
  const imp=new URLSearchParams(location.search).get('import');
  if(imp)params.set('import',imp);
  const str=params.toString();
  history.replaceState(null,'',str?'?'+str:location.pathname);
}
function loadFromURL(){
  const p=new URLSearchParams(location.search);
  const map={q:'q',author:'fAuthor',cat:'fCat',cat2:'fCat2',fmt:'fFmt',loc:'fLoc',tag:'fTag',sort:'fSort',ser:'fSeries',minp:'fMinP',maxp:'fMaxP',minr:'fMinR',shelf:'fShelf'};
  Object.entries(map).forEach(([k,id])=>{const el=document.getElementById(id);if(el&&p.get(k))el.value=p.get(k);});
}

/* ════════════════════════════════════════════════════════════════
   MODAL – book detail
   ═══════════════════════════════════════════════════════════════ */
function _closeModal(){ document.getElementById('modal-overlay').classList.remove('open'); document.body.style.overflow=''; }
function closeModal(e){ if(e&&e.target!==document.getElementById('modal-overlay')&&!e.target.classList.contains('modal-close'))return; _closeModal(); }

function miniCardHTML(b){
  return`<div class="mini-card" onclick="_closeModal();setTimeout(()=>openModal('${esc(b.id)}'),40)">
    ${miniImgEl(b.img,b.t)}<div class="mini-title">${esc(b.t)}</div><div class="mini-author">${esc(b.a)}</div>
  </div>`;
}

/* Related */
function getRelated(b,n){
  const scores=[];
  for(const r of ALL){
    if(r.id===b.id)continue; let s=0;
    if(r.a===b.a)s+=6;
    if(r.c===b.c&&b.c)s+=3;
    if(r.sr&&r.sr===b.sr)s+=8;
    s+=(r.tg||[]).filter(t=>(b.tg||[]).includes(t)).length*2;
    if(s>0)scores.push({b:r,s});
  }
  return scores.sort((a,b)=>b.s-a.s).slice(0,n).map(x=>x.b);
}

function openModal(id){
  const b=bookMap[id]; if(!b)return;
  pushRecent(id);
  const wcatQ=encodeURIComponent((b.t+' '+b.a).slice(0,80));
  const wcatUrl='https://www.worldcat.org/search?q='+wcatQ;
  const badges=[
    b.f&&`<span class="badge badge-format">${esc(b.f)}</span>`,
    b.c&&`<span class="badge badge-category">${esc(b.c)}</span>`,
    b.l&&`<span class="badge badge-location">${esc(b.l)}</span>`,
    b.p&&`<span class="badge" style="background:var(--badge-pg-bg);color:var(--badge-pg-txt)">${b.p} pages</span>`,
    b.sr&&`<span class="badge" style="background:var(--surface2);color:var(--text2)">📚 ${esc(b.sr)} #${b.sv}</span>`,
  ].filter(Boolean).join('');
  const tags=(b.tg||[]).map(t=>`<span class="tag-pill" onclick="_closeModal();setFilter('tag','${esc(t)}')">${esc(t)}</span>`).join('');
  const coverImg=b.img?`<img src="${esc(b.img)}" alt="${esc(b.t)}" style="width:160px;border-radius:8px" onerror="this.parentNode.innerHTML='<div class=\'no-cover-lg\'>📚</div>'">`:`<div class="no-cover-lg">📚</div>`;

  // Shelf buttons (preset + custom)
  const allShelves=[...SHELF_DEFS,...getCustomShelves()];
  const shelfBtns=allShelves.map(def=>{
    const on=isOnShelf(def.id,b.id);
    return`<button class="shelf-btn${on?' active':''}" id="shelfbtn-${def.id}" onclick="toggleShelf('${def.id}','${esc(b.id)}')">${def.icon} ${def.label}</button>`;
  }).join('');

  // Stars
  const r=getRating(id);
  const starBtns=[1,2,3,4,5].map(n=>`<span class="modal-star${n<=r?' filled':''}" data-n="${n}" onmouseenter="hoverStar(this,${n},'${esc(id)}')" onmouseleave="unhoverStar('${esc(id)}')" onclick="setRating('${esc(id)}',${n}===${r}?0:${n});rerenderModalStars('${esc(id)}')" >★</span>`).join('');

  // Loan
  const loans=lsGetLoans(); const loan=loans[id];
  const loanHTML=loan
    ?`<div class="loan-active">📤 Lent to ${esc(loan.name)} on ${esc(loan.date)}</div>
      <button class="btn-sm" onclick="returnLoan('${esc(id)}')">Mark returned</button>`
    :`<div class="loan-row">
        <input class="loan-input" id="loan-input-${esc(id)}" placeholder="Lent to…" type="text">
        <button class="btn-sm" onclick="saveLoan('${esc(id)}')">📤 Record loan</button>
      </div>`;

  // Reading dates
  const dates=lsGetDates(); const bd=dates[id]||{};
  const datesHTML=`<div class="dates-row">
    <div class="date-field"><label>Started</label><input type="date" id="dstart-${esc(id)}" value="${esc(bd.started||'')}" onchange="saveDate('${esc(id)}','started',this.value)"></div>
    <div class="date-field"><label>Finished</label><input type="date" id="dfinish-${esc(id)}" value="${esc(bd.finished||'')}" onchange="saveDate('${esc(id)}','finished',this.value)"></div>
  </div>`;

  // Reading progress (if on "reading" shelf)
  const pct=lsGetProgress()[id]||0;
  const progressHTML=isOnShelf('reading',id)?`
    <div class="progress-row">
      <div class="progress-bar-wrap"><div class="progress-bar-fill" id="prog-bar-${esc(id)}" style="width:${pct}%"></div></div>
      <input class="progress-input" id="prog-input-${esc(id)}" type="number" min="0" max="100" value="${pct}" placeholder="%"
        oninput="saveProgress('${esc(id)}',this.value)"> %
    </div>`:'';

  // Notes
  const notes=lsGetNotes();
  const notesHTML=`<textarea class="notes-area" id="note-${esc(id)}" placeholder="Your notes…" rows="3">${esc(notes[id]||'')}</textarea>
    <button class="notes-save" onclick="saveNote('${esc(id)}')">Save note</button>
    <span class="notes-saved" id="notesaved-${esc(id)}" style="display:none">✓ Saved</span>`;

  // Related
  const related=getRelated(b,4);
  const relHTML=related.length?`<div class="modal-section"><div class="modal-section-title">More Like This</div><div class="mini-grid">${related.map(miniCardHTML).join('')}</div></div>`:'';

  document.getElementById('modal-inner').innerHTML=`
    <div class="modal-top">
      <div class="modal-cover">${coverImg}</div>
      <div class="modal-info">
        <div class="modal-title">${esc(b.t)}</div>
        <div class="modal-author" onclick="_closeModal();openAuthorModal('${esc(b.a)}')">${esc(b.a)}</div>
        <div class="modal-meta">${badges}</div>
        ${tags?`<div class="card-tags" style="margin-bottom:8px">${tags}</div>`:''}
        ${b.s?`<div class="modal-summary">${esc(b.s)}</div>`:''}
        ${b.url?`<div class="modal-amazon"><a href="${esc(b.url)}" target="_blank">View on Amazon \u2192</a></div>`:''}
        <div class="modal-amazon" style="margin-top:3px;display:flex;flex-wrap:wrap;gap:6px;align-items:center">
          <a href="${wcatUrl}" target="_blank" style="font-size:.74rem;color:var(--accent)">\uD83C\uDFDB Find at library (WorldCat) \u2192</a>
          <button class="btn-sm" style="font-size:.72rem" onclick="_closeModal();openShareCard('${esc(b.id)}')">\uD83D\uDCE4 Share</button>
        </div>
        <div id="ol-data-${esc(b.id)}"></div>
      </div>
    </div>

    ${b.ext?`<div class="ext-book-banner">📝 <span><strong>Not in your library</strong> — tracked externally &nbsp;·&nbsp; <a href="#" onclick="event.preventDefault();_closeModal();setTimeout(()=>openExternalModal('${esc(id)}'),60)" style="color:#92400e;text-decoration:underline">Edit</a> &nbsp;·&nbsp; <a href="#" onclick="event.preventDefault();deleteExternalBook('${esc(id)}')" style="color:#ef4444;text-decoration:underline">Delete</a></span></div>`:''}
    <div class="modal-shelf-row">${shelfBtns}</div>
    ${progressHTML}

    <div class="modal-section">
      <div class="modal-section-title">⭐ Your Rating</div>
      <div class="star-row" id="modal-stars-${esc(id)}">${starBtns}</div>
      <span class="star-clear" onclick="setRating('${esc(id)}',0);rerenderModalStars('${esc(id)}')">clear</span>
    </div>

    <div class="modal-section">
      <div class="modal-section-title">📅 Reading Dates</div>
      ${datesHTML}
    </div>

    <div class="modal-section">
      <div class="modal-section-title">📤 Loan Tracker</div>
      ${loanHTML}
    </div>

    <div class="modal-section">
      <div class="modal-section-title">📝 Your Notes</div>
      ${notesHTML}
    </div>

    ${relHTML}
    <div id="modal-discover" class="modal-section"></div>`;

  document.getElementById('modal-overlay').classList.add('open');
  document.body.style.overflow='hidden';
  loadDiscover(b);
  fetchOpenLibrary(b.t,b.a,'ol-data-'+id);
}

function hoverStar(el,n,id){
  const row=document.getElementById('modal-stars-'+id); if(!row)return;
  row.querySelectorAll('.modal-star').forEach((s,i)=>s.classList.toggle('hover',i<n));
}
function unhoverStar(id){
  const row=document.getElementById('modal-stars-'+id); if(!row)return;
  row.querySelectorAll('.modal-star').forEach(s=>s.classList.remove('hover'));
}
function rerenderModalStars(id){
  const row=document.getElementById('modal-stars-'+id); if(!row)return;
  const r=getRating(id);
  row.querySelectorAll('.modal-star').forEach((s,i)=>s.classList.toggle('filled',i<r));
  // Also update any card stars
  document.querySelectorAll(`[data-stars-id="${id}"]`).forEach(el=>renderStarRow(el,id));
}

/* ── Notes ── */
function saveNote(id){
  const el=document.getElementById('note-'+id); if(!el)return;
  const d=lsGetNotes(); d[id]=el.value; lsSet('mcl_notes',d); triggerSync();
  const sv=document.getElementById('notesaved-'+id);
  if(sv){sv.style.display='';setTimeout(()=>sv.style.display='none',2000);}
}

/* ── Reading dates ── */
function saveDate(id,field,val){
  const d=lsGetDates(); if(!d[id])d[id]={};
  d[id][field]=val; lsSet('mcl_dates',d); triggerSync();
}

/* ── Loan tracker ── */
function saveLoan(id){
  const inp=document.getElementById('loan-input-'+id); if(!inp||!inp.value.trim())return;
  const d=lsGetLoans();
  d[id]={name:inp.value.trim(), date:new Date().toLocaleDateString()};
  lsSet('mcl_loans',d); triggerSync();
  openModal(id);
}
function returnLoan(id){
  const d=lsGetLoans(); delete d[id]; lsSet('mcl_loans',d); triggerSync();
  openModal(id);
}

/* ── Reading progress ── */
function saveProgress(id,val){
  const pct=Math.min(100,Math.max(0,parseInt(val)||0));
  const d=lsGetProgress(); d[id]=pct; lsSet('mcl_progress',d); triggerSync();
  const bar=document.getElementById('prog-bar-'+id); if(bar)bar.style.width=pct+'%';
}

/* ════════════════════════════════════════════════════════════════
   DISCOVER  (Wikipedia + platform links)
   ═══════════════════════════════════════════════════════════════ */
async function loadDiscover(b){
  const el=document.getElementById('modal-discover'); if(!el)return;
  const q=encodeURIComponent(b.t+' '+b.a);
  const links=[
    {icon:'▶️',label:'YouTube',href:`https://www.youtube.com/results?search_query=${q}+book`},
    {icon:'🎙️',label:'Podcasts',href:`https://open.spotify.com/search/${encodeURIComponent(b.t)}/podcasts`},
    {icon:'📖',label:'Goodreads',href:`https://www.goodreads.com/search?q=${q}`},
    {icon:'🔍',label:'Google',href:`https://www.google.com/search?q=${q}+book+review`},
  ];
  el.innerHTML=`<div class="modal-section-title">Discover More</div>
    <div class="discover-links">${links.map(l=>`<a href="${l.href}" target="_blank" class="discover-link">${l.icon} ${l.label}</a>`).join('')}</div>
    <div id="wiki-area"><span style="font-size:.75rem;color:var(--text3)">Loading Wikipedia…</span></div>`;
  try{
    const wr=await fetch(`https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(b.t)}?redirect=true`);
    const wa=document.getElementById('wiki-area'); if(!wa)return;
    if(!wr.ok)throw new Error();
    const sd=await wr.json();
    if(sd.extract){
      wa.innerHTML=`<div class="modal-section-title" style="margin-top:10px">Wikipedia</div>
        <div class="wiki-blurb">${esc(sd.extract.slice(0,450)+(sd.extract.length>450?'…':''))}</div>
        <a class="wiki-link" href="${esc(sd.content_urls?.desktop?.page||'#')}" target="_blank">Read full article →</a>`;
    } else { wa.innerHTML=''; }
  }catch{ const wa=document.getElementById('wiki-area'); if(wa)wa.innerHTML=''; }
}

/* ════════════════════════════════════════════════════════════════
   AUTHOR MODAL
   ═══════════════════════════════════════════════════════════════ */
function openAuthorModal(author){
  const booksBy=ALL.filter(b=>b.a===author).sort((a,b)=>a.t.localeCompare(b.t));
  document.getElementById('author-inner').innerHTML=`
    <div class="author-header">
      <div class="author-avatar">✍️</div>
      <div>
        <div class="author-name">${esc(author)}</div>
        <div class="author-count">${booksBy.length} book${booksBy.length!==1?'s':''} in your library</div>
        <a href="https://en.wikipedia.org/wiki/${encodeURIComponent(author)}" target="_blank" style="font-size:.76rem;color:var(--accent)">Wikipedia →</a>
        &nbsp;
        <a href="https://www.goodreads.com/search?q=${encodeURIComponent(author)}" target="_blank" style="font-size:.76rem;color:var(--accent)">Goodreads →</a>
      </div>
    </div>
    <div id="author-wiki-area"><span style="font-size:.75rem;color:var(--text3)">Loading bio…</span></div>
    <div class="modal-section-title" style="margin-top:12px">All Books (${booksBy.length})</div>
    <div class="mini-grid">${booksBy.map(b=>`<div class="mini-card" onclick="closeAuthorModal();setTimeout(()=>openModal('${esc(b.id)}'),40)">${miniImgEl(b.img,b.t)}<div class="mini-title">${esc(b.t)}</div></div>`).join('')}</div>`;
  document.getElementById('author-overlay').classList.add('open');
  document.body.style.overflow='hidden';
  // Load Wikipedia bio for author
  fetch(`https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(author)}?redirect=true`)
    .then(r=>r.ok?r.json():null)
    .then(d=>{
      const el=document.getElementById('author-wiki-area'); if(!el)return;
      if(d&&d.extract){
        el.innerHTML=`<div class="author-bio">${esc(d.extract.slice(0,500)+(d.extract.length>500?'…':''))}</div>`;
      } else { el.innerHTML=''; }
    }).catch(()=>{const el=document.getElementById('author-wiki-area');if(el)el.innerHTML='';});
}
function closeAuthorModal(e){
  if(e&&e.target!==document.getElementById('author-overlay')&&!e.target.classList.contains('modal-close'))return;
  document.getElementById('author-overlay').classList.remove('open');
  document.body.style.overflow='';
}

/* ════════════════════════════════════════════════════════════════
   SHELF SYSTEM (preset + custom shelves)
   ═══════════════════════════════════════════════════════════════ */
const SHELF_DEFS=[
  {id:'want',   icon:'🔖', label:'Want to Read'},
  {id:'reading',icon:'📖', label:'Reading Now'},
  {id:'upnext', icon:'📋', label:'Up Next'},
  {id:'done',   icon:'✅', label:'Finished'},
  {id:'fave',   icon:'⭐', label:'Favorites'},
];
const CUSTOM_ICONS=['📌','🏷️','💡','🎯','🔥','💎','🌟','📝','🧠','🎓','🚀','❤️'];

function getCustomShelves(){ return lsGet('mcl_custom_shelves',[]) }
function saveCustomShelves(s){ lsSet('mcl_custom_shelves',s); triggerSync(); }
function getAllShelves(){ return [...SHELF_DEFS,...getCustomShelves()] }

function loadShelves(){ return lsGet('mcl_shelves') }
function saveShelves(s){ lsSet('mcl_shelves',s); triggerSync(); }
function isOnShelf(shelfId,bookId){ return(loadShelves()[shelfId]||[]).includes(bookId) }
function toggleShelf(shelfId,bookId){
  const s=loadShelves(); if(!s[shelfId])s[shelfId]=[];
  const idx=s[shelfId].indexOf(bookId);
  if(idx>=0)s[shelfId].splice(idx,1); else s[shelfId].push(bookId);
  saveShelves(s);
  getAllShelves().forEach(def=>{
    const btn=document.getElementById('shelfbtn-'+def.id);
    if(btn){const on=isOnShelf(def.id,bookId);btn.classList.toggle('active',on);}
  });
}

let _shelfView=null, _newShelfIcon=CUSTOM_ICONS[0];
function openShelves(){ _shelfView=null; renderShelvesModal(); document.getElementById('shelves-overlay').classList.add('open'); document.body.style.overflow='hidden'; }
function closeShelves(e){ if(e&&e.target!==document.getElementById('shelves-overlay')&&!e.target.classList.contains('modal-close'))return; document.getElementById('shelves-overlay').classList.remove('open'); document.body.style.overflow=''; }

function renderShelvesModal(){
  const s=loadShelves(); const importData=getImportData(); const allShelves=getAllShelves();
  let importBanner='';
  if(importData) importBanner=`<div class="import-banner"><span>📥 ${importData.books.length} book${importData.books.length!==1?'s':''} shared</span><button class="btn-sm btn-accent" onclick="importShelf('${importData.shelfId}',importData.books)">Import</button></div>`;
  const inner=document.getElementById('shelves-inner');
  if(_shelfView){
    const def=allShelves.find(d=>d.id===_shelfView);
    const ids=(s[_shelfView]||[]);
    let bks=ids.map(id=>bookMap[id]).filter(Boolean);
    // For Up Next shelf, reorder by mcl_upnext_order
    if(_shelfView==='upnext'){
      const order=getUpNextOrder();
      const ordered=order.map(id=>bookMap[id]).filter(Boolean);
      const unordered=bks.filter(b=>!order.includes(b.id));
      bks=[...ordered,...unordered];
    }
    // Reading progress list for "reading" shelf
    const extra=_shelfView==='reading'?bks.map(b=>{
      const pct=lsGetProgress()[b.id]||0;
      return`<div style="margin-bottom:6px"><div style="font-size:.76rem;font-weight:600">${esc(b.t)}</div>
        <div class="progress-row" style="gap:6px">
          <div class="progress-bar-wrap"><div class="progress-bar-fill" style="width:${pct}%"></div></div>
          <input class="progress-input" type="number" min="0" max="100" value="${pct}" placeholder="%" style="width:48px"
            oninput="saveProgress('${esc(b.id)}',this.value)">%
        </div></div>`;
    }).join(''):'';
    const cardClassName=_shelfView==='upnext'?' upnext-card':'';
    inner.innerHTML=`<h2 style="font-size:.96rem;font-weight:700;margin-bottom:10px">${def.icon} ${def.label} (${ids.length})</h2>
      ${importBanner}
      <button class="btn-sm" onclick="_shelfView=null;renderShelvesModal()" style="margin-bottom:10px">← Back</button>
      ${_shelfView==='upnext'?`<p style="color:var(--text2);font-size:.8rem;margin-bottom:8px">Drag to reorder →</p>`:''}
      ${extra?`<div class="modal-section" style="padding-top:0">${extra}</div>`:''}
      ${bks.length?`${generateShareRow(_shelfView,ids)}<div class="mini-grid">${bks.map(b=>`<div class="shelf-mini-wrap${cardClassName}" data-book-id="${b.id}" onclick="openModal('${esc(b.id)}')" style="cursor:pointer">${miniImgEl(b.img,b.t)}<div class="mini-title">${esc(b.t)}</div><div class="mini-author">${esc(b.a)}</div><button class="shelf-mini-remove" onclick="event.stopPropagation();toggleShelf('${def.id}','${esc(b.id)}');renderShelvesModal()" title="Remove">✕</button></div>`).join('')}</div>`:'<p style="color:var(--text2);font-size:.86rem;padding:8px 0">No books on this shelf yet.</p>'}`;
    if(_shelfView==='upnext')setTimeout(setupUpNextDrag,50);
  } else {
    // Overview
    const rows=allShelves.map(def=>{
      const count=(s[def.id]||[]).length;
      const isCustom=!SHELF_DEFS.find(d=>d.id===def.id);
      return`<button class="shelf-row-btn" onclick="_shelfView='${def.id}';renderShelvesModal()">
        <span class="shelf-row-icon">${def.icon}</span>
        <span><div class="shelf-row-label">${esc(def.label)}</div><div class="shelf-row-count">${count} book${count!==1?'s':''}</div></span>
        ${isCustom?`<button class="shelf-delete" onclick="event.stopPropagation();deleteCustomShelf('${def.id}')" title="Delete shelf">🗑</button>`:''}
        <span class="shelf-chevron">›</span>
      </button>`;
    }).join('');
    const iconOpts=CUSTOM_ICONS.map(ic=>`<span class="icon-opt${ic===_newShelfIcon?' sel':''}" onclick="selectNewShelfIcon('${ic}')">${ic}</span>`).join('');
    inner.innerHTML=`<h2 style="font-size:.96rem;font-weight:700;margin-bottom:10px">📚 My Shelves</h2>
      ${importBanner}${rows}
      <div class="modal-section">
        <button class="btn-sm" onclick="openExternalModal()" style="margin-bottom:12px;width:100%">➕ Track a Book</button>
        <div class="modal-section-title">+ New Shelf</div>
        <div class="icon-options">${iconOpts}</div>
        <div class="new-shelf-row">
          <input class="new-shelf-input" id="new-shelf-name" placeholder="Shelf name…">
          <button class="btn-sm btn-accent" onclick="addCustomShelf()">Add</button>
        </div>
      </div>`;
  }
}
function selectNewShelfIcon(ic){
  _newShelfIcon=ic;
  document.querySelectorAll('.icon-opt').forEach(el=>el.classList.toggle('sel',el.textContent===ic));
}
function addCustomShelf(){
  const inp=document.getElementById('new-shelf-name'); if(!inp||!inp.value.trim())return;
  const cs=getCustomShelves();
  const id='custom-'+Date.now();
  cs.push({id, icon:_newShelfIcon, label:inp.value.trim()});
  saveCustomShelves(cs); inp.value=''; renderShelvesModal();
}
function deleteCustomShelf(id){
  const cs=getCustomShelves().filter(d=>d.id!==id); saveCustomShelves(cs);
  const s=loadShelves(); delete s[id]; saveShelves(s);
  renderShelvesModal();
}
function shelfMiniCard(b,shelfId){
  return`<div class="shelf-mini-wrap">${miniImgEl(b.img,b.t)}
    <div class="mini-title">${esc(b.t)}</div>
    <div class="mini-author">${esc(b.a)}</div>
    <button class="shelf-mini-remove" onclick="toggleShelf('${shelfId}','${esc(b.id)}');renderShelvesModal()" title="Remove">✕</button>
  </div>`;
}
function generateShareRow(shelfId,bookIds){
  const data=btoa(unescape(encodeURIComponent(JSON.stringify({shelfId,books:bookIds}))));
  const url=location.origin+location.pathname+'?import='+data;
  return`<div class="share-row"><input class="share-input" type="text" readonly value="${esc(url)}" onclick="this.select()">
    <button class="btn-sm" onclick="navigator.clipboard.writeText('${esc(url)}').then(()=>this.textContent='Copied!').catch(()=>this.select())">Copy link</button>
  </div>`;
}
function getImportData(){
  const raw=new URLSearchParams(location.search).get('import'); if(!raw)return null;
  try{return JSON.parse(decodeURIComponent(escape(atob(raw))));}catch{return null;}
}
function importShelf(shelfId,bookIds){
  const s=loadShelves(); if(!s[shelfId])s[shelfId]=[];
  bookIds.forEach(id=>{if(!s[shelfId].includes(id))s[shelfId].push(id);});
  saveShelves(s); _shelfView=shelfId; renderShelvesModal();
}

/* ════════════════════════════════════════════════════════════════
   UP NEXT SHELF – Drag-to-reorder
   ═══════════════════════════════════════════════════════════════ */
function getUpNextOrder(){ return lsGet('mcl_upnext_order',[]) }
function saveUpNextOrder(ord){ lsSet('mcl_upnext_order',ord); triggerSync(); }
let _draggedId=null;
function setupUpNextDrag(){
  document.querySelectorAll('.upnext-card').forEach(card=>{
    card.draggable=true;
    card.ondragstart=(e)=>{_draggedId=card.dataset.bookId;e.dataTransfer.effectAllowed='move';};
    card.ondragover=(e)=>{e.preventDefault();e.dataTransfer.dropEffect='move';};
    card.ondrop=(e)=>{
      e.preventDefault();
      if(!_draggedId||_draggedId===card.dataset.bookId)return;
      const order=getUpNextOrder();
      const dragIdx=order.indexOf(_draggedId);
      const dropIdx=order.indexOf(card.dataset.bookId);
      if(dragIdx>=0&&dropIdx>=0){
        order.splice(dragIdx,1);
        order.splice(dropIdx,0,_draggedId);
        saveUpNextOrder(order);
        renderShelvesModal();
      }
      _draggedId=null;
    };
    card.ondragend=()=>{_draggedId=null;};
  });
}

/* ════════════════════════════════════════════════════════════════
   EXTERNAL BOOKS (tracker for books not in library)
   ═══════════════════════════════════════════════════════════════ */
function lsGetExternalBooks(){ return lsGet('mcl_external_books',[]) }
function lsSetExternalBooks(books){ lsSet('mcl_external_books',books); triggerSync(); }
function mergeExternalBooks(){
  const ext=lsGetExternalBooks();
  ext.forEach(b=>{
    if(!bookMap[b.id]){ALL.push(b);bookMap[b.id]=b;}
    else{Object.assign(bookMap[b.id],b);}  // update existing entry with latest edits
  });
}

function _extShelfChips(){
  const allShelves=[...SHELF_DEFS,...getCustomShelves()];
  const wrap=document.getElementById('ext-shelf-picks'); if(!wrap)return;
  const editId=document.getElementById('ext-editing-id').value;
  const shelves=loadShelves();
  wrap.innerHTML=allShelves.map(def=>{
    const on=editId&&(shelves[def.id]||[]).includes(editId);
    return`<span class="ext-shelf-chip${on?' on':''}" data-shelf-id="${def.id}" onclick="this.classList.toggle('on')">${def.icon} ${def.label}</span>`;
  }).join('');
}

function openExternalModal(editId){
  const modal=document.getElementById('ext-overlay');
  const idField=document.getElementById('ext-editing-id');
  document.getElementById('ext-modal-title').textContent=editId?'\u270f\ufe0f Edit Tracked Book':'\u2795 Track a Book';
  document.getElementById('ext-save-btn').textContent=editId?'Save Changes':'Save & Track';
  idField.value=editId||'';
  // Clear lookup state
  const lq=document.getElementById('ext-lookup-q'); if(lq)lq.value='';
  const lr=document.getElementById('ext-lookup-results'); if(lr)lr.innerHTML='';
  // Hide lookup section when editing (already have data), show for new
  const ls=document.getElementById('ext-lookup-section'); if(ls)ls.style.display=editId?'none':'';
  if(editId){
    const b=bookMap[editId]||{};
    const dates=lsGetDates()[editId]||{};
    document.getElementById('ext-title').value=b.t||'';
    document.getElementById('ext-author').value=b.a||'';
    document.getElementById('ext-pages').value=b.p||'';
    document.getElementById('ext-cat').value=b.c||'';
    document.getElementById('ext-img').value=b.img||'';
    document.getElementById('ext-started').value=dates.started||'';
    document.getElementById('ext-finished').value=dates.finished||'';
  } else {
    ['ext-title','ext-author','ext-pages','ext-cat','ext-img','ext-started','ext-finished'].forEach(id=>{ const el=document.getElementById(id); if(el)el.value=''; });
  }
  modal.classList.add('open'); document.body.style.overflow='hidden';
  _extShelfChips();
}

function closeExternalModal(e){
  if(e&&e.type==='click'&&e.target!==document.getElementById('ext-overlay')&&!e.target.classList.contains('modal-close'))return;
  document.getElementById('ext-overlay').classList.remove('open'); document.body.style.overflow='';
}

/* ── Google Books lookup ── */
let _extBooks=[];
async function lookupBookOnline(){
  const q=document.getElementById('ext-lookup-q').value.trim();
  if(!q)return;
  const btn=document.getElementById('ext-lookup-btn');
  const res=document.getElementById('ext-lookup-results');
  btn.disabled=true; btn.textContent='Searching\u2026';
  res.innerHTML='<div style="padding:8px 2px;color:var(--text2);font-size:.78rem">\uD83D\uDD0D Looking up books\u2026</div>';
  try{
    const url='https://www.googleapis.com/books/v1/volumes?q='+encodeURIComponent(q)+'&maxResults=6&printType=books';
    const data=await fetch(url).then(r=>r.json());
    if(!data.items||!data.items.length){
      res.innerHTML='<div style="padding:8px 2px;color:var(--text2);font-size:.78rem">No results found \u2014 try a different title or author.</div>';
    } else {
      _extBooks=data.items.map(item=>{
        const v=item.volumeInfo||{};
        return{
          title:v.title||'',
          author:(v.authors||[]).join(', '),
          pages:v.pageCount||0,
          cat:(v.categories||[])[0]||'',
          img:v.imageLinks?(v.imageLinks.thumbnail||v.imageLinks.smallThumbnail||'').replace('http://','https://'):''
        };
      });
      res.innerHTML=_extBooks.map((r,i)=>`
        <div class="ext-result-card" onclick="fillExtBook(${i})">
          ${r.img?`<img class="ext-result-img" src="${esc(r.img)}" onerror="this.style.display='none'">`
                 :`<div class="ext-result-img-ph">\uD83D\uDCD6</div>`}
          <div class="ext-result-info">
            <div class="ext-result-title">${esc(r.title)}</div>
            <div class="ext-result-author">${esc(r.author)}</div>
            <div class="ext-result-meta">${[r.pages?r.pages+' pages':'',r.cat].filter(Boolean).join(' \u00b7 ')}</div>
          </div>
        </div>`).join('');
    }
  }catch(err){
    res.innerHTML='<div style="padding:8px 2px;color:var(--text2);font-size:.78rem">Search unavailable \u2014 fill in manually.</div>';
  }
  btn.disabled=false; btn.textContent='\uD83D\uDD0D Look up';
}
function fillExtBook(i){
  const r=_extBooks[i]; if(!r)return;
  document.getElementById('ext-title').value=r.title;
  document.getElementById('ext-author').value=r.author;
  if(r.pages)document.getElementById('ext-pages').value=r.pages;
  document.getElementById('ext-cat').value=r.cat;
  document.getElementById('ext-img').value=r.img;
  document.getElementById('ext-lookup-results').innerHTML='';
  document.getElementById('ext-lookup-q').value='';
  document.getElementById('ext-title').focus();
}

function saveExternalBook(){
  const t=document.getElementById('ext-title').value.trim();
  if(!t){document.getElementById('ext-title').focus();return;}
  const editId=document.getElementById('ext-editing-id').value;
  const id=editId||('ext-'+Date.now());
  const b={id,t,a:document.getElementById('ext-author').value.trim()||'Unknown',
    p:parseInt(document.getElementById('ext-pages').value)||0,
    c:document.getElementById('ext-cat').value.trim()||'',
    img:document.getElementById('ext-img').value.trim()||'',ext:true};
  const ext=lsGetExternalBooks().filter(x=>x.id!==id);
  ext.push(b); lsSetExternalBooks(ext);
  if(!bookMap[id]){ALL.push(b);} else {Object.assign(bookMap[id],b);}
  bookMap[id]=b;
  const started=document.getElementById('ext-started').value;
  const finished=document.getElementById('ext-finished').value;
  if(started||finished){
    const dates=lsGetDates(); if(!dates[id])dates[id]={};
    if(started)dates[id].started=started; if(finished)dates[id].finished=finished;
    lsSet('mcl_dates',dates); triggerSync();
  }
  const chips=document.querySelectorAll('#ext-shelf-picks .ext-shelf-chip');
  const shelves=loadShelves();
  chips.forEach(chip=>{
    const sid=chip.dataset.shelfId; if(!shelves[sid])shelves[sid]=[];
    const idx=shelves[sid].indexOf(id);
    if(chip.classList.contains('on')&&idx<0) shelves[sid].push(id);
    else if(!chip.classList.contains('on')&&idx>=0) shelves[sid].splice(idx,1);
  });
  saveShelves(shelves);
  document.getElementById('ext-overlay').classList.remove('open'); document.body.style.overflow='';
  applyF();
}

function deleteExternalBook(id){
  if(!confirm('Remove this tracked book? This will also delete its ratings, notes, and reading dates.'))return;
  lsSetExternalBooks(lsGetExternalBooks().filter(b=>b.id!==id));
  const idx=ALL.findIndex(b=>b.id===id); if(idx>=0)ALL.splice(idx,1);
  delete bookMap[id];
  const shelves=loadShelves();
  Object.keys(shelves).forEach(k=>{ shelves[k]=(shelves[k]||[]).filter(x=>x!==id); });
  saveShelves(shelves);
  const ratings=lsGetRatings(); delete ratings[id]; lsSet('mcl_ratings',ratings);
  const notes=lsGetNotes(); delete notes[id]; lsSet('mcl_notes',notes);
  const dates=lsGetDates(); delete dates[id]; lsSet('mcl_dates',dates);
  triggerSync();
  _closeModal(); applyF();
}

/* ════════════════════════════════════════════════════════════════
   STATS MODAL
   ═══════════════════════════════════════════════════════════════ */
function openStats(){ renderStatsModal(); document.getElementById('stats-overlay').classList.add('open'); document.body.style.overflow='hidden'; }
function closeStats(e){ if(e&&e.target!==document.getElementById('stats-overlay')&&!e.target.classList.contains('modal-close'))return; document.getElementById('stats-overlay').classList.remove('open'); document.body.style.overflow=''; }
function renderStatsModal(){
  const totalPages=ALL.reduce((s,b)=>s+(b.p||0),0);
  const withPages=ALL.filter(b=>b.p>0);
  const avgPages=withPages.length?Math.round(totalPages/withPages.length):0;
  const authCount=new Map(); ALL.forEach(b=>{if(b.a)authCount.set(b.a,(authCount.get(b.a)||0)+1);});
  const catCount=new Map();  ALL.forEach(b=>{if(b.c)catCount.set(b.c,(catCount.get(b.c)||0)+1);});
  const topAuthors=[...authCount.entries()].sort((a,b)=>b[1]-a[1]).slice(0,8);
  const topCats=[...catCount.entries()].sort((a,b)=>b[1]-a[1]).slice(0,8);
  const ratings=lsGetRatings(); const ratedBooks=Object.values(ratings).filter(Boolean);
  const avgRating=ratedBooks.length?(ratedBooks.reduce((s,r)=>s+r,0)/ratedBooks.length).toFixed(1):'-';
  // Yearly reading summary
  const dates=lsGetDates();
  const yearMap=new Map();
  Object.values(dates).forEach(d=>{ if(d.finished){const y=d.finished.slice(0,4);yearMap.set(y,(yearMap.get(y)||0)+1);} });
  const years=[...yearMap.entries()].sort((a,b)=>b[0]-a[0]);
  const maxYear=Math.max(...yearMap.values(),1);
  const yearBars=years.map(([y,n])=>`<div class="year-bar-wrap">
    <div class="year-bar-label">${y}</div>
    <div class="year-bar-bg"><div class="year-bar-fill" style="width:${Math.round(n/maxYear*100)}%"></div></div>
    <div class="year-bar-cnt">${n}</div>
  </div>`).join('');
  // Tag cloud
  const tagCounts=META.tagCounts||{};
  const maxTag=Math.max(...Object.values(tagCounts),1);
  const tagCloud=Object.entries(tagCounts).map(([t,n])=>{
    const sz=0.65+0.55*(n/maxTag);
    return`<span class="tag-cloud-pill" style="font-size:${sz.toFixed(2)}rem" onclick="closeStats({target:document.getElementById('stats-overlay')});setFilter('tag','${esc(t)}')">${esc(t)} <span style="opacity:.6">${n}</span></span>`;
  }).join('');
  // V6: streak, pace, completion
  const streak=getReadingStreak();
  const pace=calcReadingPace();
  const comp=calcCompletionRate();
  const y=new Date().getFullYear();
  const goal=getYearGoal(y); const done=getBooksFinishedYear(y);
  document.getElementById('stats-inner').innerHTML=`
    <h2 style="font-size:.95rem;font-weight:700;margin-bottom:12px">\uD83D\uDCCA Library Stats</h2>
    <div class="stat-grid">
      <div class="stat-box"><div class="stat-num">${ALL.length.toLocaleString()}</div><div class="stat-lbl">Total Titles</div></div>
      <div class="stat-box"><div class="stat-num">${totalPages.toLocaleString()}</div><div class="stat-lbl">Total Pages</div></div>
      <div class="stat-box"><div class="stat-num">${avgPages.toLocaleString()}</div><div class="stat-lbl">Avg Pages</div></div>
      <div class="stat-box"><div class="stat-num">${authCount.size.toLocaleString()}</div><div class="stat-lbl">Authors</div></div>
      <div class="stat-box"><div class="stat-num">${ratedBooks.length}</div><div class="stat-lbl">Books Rated</div></div>
      <div class="stat-box"><div class="stat-num">${avgRating}</div><div class="stat-lbl">Avg Rating</div></div>
      ${streak?`<div class="stat-box"><div class="stat-num">${streak}\uD83D\uDD25</div><div class="stat-lbl">Day Streak</div></div>`:''}
      ${goal?`<div class="stat-box"><div class="stat-num">${done}/${goal}</div><div class="stat-lbl">${y} Goal</div></div>`:''}
      ${pace?`<div class="stat-box"><div class="stat-num">${pace.perMonth}</div><div class="stat-lbl">Books/Month</div></div>`:''}
      ${comp&&comp.finished?`<div class="stat-box"><div class="stat-num">${comp.pct}%</div><div class="stat-lbl">Finished Rate</div></div>`:''}
    </div>
    ${years.length?`<div class="modal-section-title">\uD83D\uDCC5 Read by Year</div>${yearBars}`:''}
    <div class="modal-section-title" style="margin-top:12px">\uD83D\uDCC5 Reading Calendar</div>
    <div id="stats-cal"></div>
    <div class="modal-section-title" style="margin-top:12px">\uD83C\uDF67 Genre Breakdown</div>
    <div id="stats-pie"></div>
    <div class="modal-section-title" style="margin-top:12px">Top Authors</div>
    <ul class="top-list">${topAuthors.map(([a,n])=>`<li><span style="cursor:pointer;color:var(--accent)" onclick="closeStats({target:document.getElementById('stats-overlay')});openAuthorModal('${esc(a)}')">${esc(a)}</span><span class="cnt">${n}</span></li>`).join('')}</ul>
    <div class="modal-section-title" style="margin-top:12px">Top Categories</div>
    <ul class="top-list">${topCats.map(([c,n])=>`<li><span>${esc(c)}</span><span class="cnt">${n}</span></li>`).join('')}</ul>
    ${tagCloud?`<div class="modal-section-title" style="margin-top:12px">\uD83C\uDFF7\uFE0F Tag Cloud</div><div class="tag-cloud">${tagCloud}</div>`:''}
    <div style="margin-top:14px;display:flex;gap:8px;flex-wrap:wrap">
      <button class="btn-sm btn-accent" onclick="openAchievements()">\uD83C\uDF96\uFE0F Achievements</button>
      <button class="btn-sm" onclick="openPublicProfile()">\uD83D\uDD17 Public Profile</button>
      <button class="btn-sm" onclick="openWidgetModal()">\uD83D\uDCE1 Reading Widget</button>
    </div>`;
  renderCalendar('stats-cal');
  renderGenrePie('stats-pie');
}

/* ════════════════════════════════════════════════════════════════
   GITHUB GIST SYNC  — cross-browser / cross-device personal data
   ═══════════════════════════════════════════════════════════════ */
const GIST_FILE  = 'mclemore-library-data.json';
const DATA_KEYS  = ['mcl_ratings','mcl_notes','mcl_shelves','mcl_custom_shelves',
                    'mcl_progress','mcl_dates','mcl_loans','mcl_recent','mcl_sessions','mcl_external_books','mcl_upnext_order'];
const ARRAY_KEYS = new Set(['mcl_custom_shelves','mcl_recent','mcl_sessions','mcl_external_books','mcl_upnext_order']);

let _ghToken  = localStorage.getItem('mcl_gh_token')||'';
let _gistId   = localStorage.getItem('mcl_gist_id')||'';
let _syncTimer = null;
let _syncState = 'idle'; // idle | syncing | synced | error

function setSyncState(s){
  _syncState=s;
  const dot=document.getElementById('sync-dot');
  if(dot){dot.className='sync-dot '+s; dot.title={idle:'Not connected',syncing:'Syncing…',synced:'Synced ✓',error:'Sync error'}[s]||'';}
}

function ghHeaders(){
  return {'Authorization':'token '+_ghToken,'Accept':'application/vnd.github.v3+json','Content-Type':'application/json'};
}

async function gistLoad(){
  if(!_ghToken)return;
  setSyncState('syncing');
  try{
    // Discover gist ID if not cached
    if(!_gistId){
      const resp=await fetch('https://api.github.com/gists?per_page=100',{headers:ghHeaders()});
      if(!resp.ok)throw new Error('auth');
      const list=await resp.json();
      const found=list.find(g=>g.files&&g.files[GIST_FILE]);
      if(found){_gistId=found.id;localStorage.setItem('mcl_gist_id',_gistId);}
    }
    if(!_gistId){setSyncState('synced');return;} // no gist yet, nothing to load
    const resp=await fetch(`https://api.github.com/gists/${_gistId}`,{headers:ghHeaders()});
    if(!resp.ok)throw new Error('load');
    const gist=await resp.json();
    const raw=gist.files?.[GIST_FILE]?.content;
    if(raw){
      const remote=JSON.parse(raw);
      DATA_KEYS.forEach(k=>{
        if(remote[k]!==undefined){
          try{
            if(k==='mcl_custom_shelves'){
              // Merge: keep any local custom shelves not present in remote (by id)
              const local=lsGet('mcl_custom_shelves',[]);
              const remoteIds=new Set((remote[k]||[]).map(function(s){return s.id;}));
              const merged=[...(remote[k]||[]),...local.filter(function(s){return!remoteIds.has(s.id);})];
              localStorage.setItem(k,JSON.stringify(merged));
            } else if(k==='mcl_external_books'){
              // Merge: remote wins for any shared IDs (edits propagate); keep local-only additions
              const local=lsGet('mcl_external_books',[]);
              const remoteIds=new Set((remote[k]||[]).map(function(b){return b.id;}));
              const merged=[...(remote[k]||[]),...local.filter(function(b){return!remoteIds.has(b.id);})];
              localStorage.setItem(k,JSON.stringify(merged));
            } else if(k==='mcl_shelves'){
              // Merge: for any shelf key present locally but missing from remote, keep local data
              const local=lsGet('mcl_shelves',{});
              const merged=Object.assign({},local,remote[k]);
              localStorage.setItem(k,JSON.stringify(merged));
            } else {
              localStorage.setItem(k,JSON.stringify(remote[k]));
            }
          }catch{}
        }
      });
      console.log('[Gist] Personal data loaded from Gist');
    }
    setSyncState('synced');
  }catch(e){
    console.warn('[Gist] Load failed',e);
    setSyncState(e.message==='auth'?'error':'synced'); // don't mark error if just no gist
  }
}

async function gistSave(){
  if(!_ghToken){setSyncState('idle');return;}
  setSyncState('syncing');
  const data={};
  DATA_KEYS.forEach(k=>{
    try{const v=localStorage.getItem(k);data[k]=v?JSON.parse(v):(ARRAY_KEYS.has(k)?[]:{})}catch{data[k]=ARRAY_KEYS.has(k)?[]:{};}
  });
  const content=JSON.stringify(data,null,2);
  try{
    const body=JSON.stringify({files:{[GIST_FILE]:{content}},description:'McLemore Library — personal data',public:false});
    let resp;
    if(_gistId){
      resp=await fetch(`https://api.github.com/gists/${_gistId}`,{method:'PATCH',headers:ghHeaders(),body});
    }else{
      resp=await fetch('https://api.github.com/gists',{method:'POST',headers:ghHeaders(),body});
      if(resp.ok){const g=await resp.json();_gistId=g.id;localStorage.setItem('mcl_gist_id',_gistId);}
    }
    setSyncState(resp.ok?'synced':'error');
  }catch(e){setSyncState('error');}
}

/* Call this after every personal-data write */
function triggerSync(){
  clearTimeout(_syncTimer);
  _syncTimer=setTimeout(gistSave,1500);
}

/* ── Sync settings modal ── */
function openSync(){
  const connected=!!_ghToken;
  document.getElementById('sync-inner').innerHTML=`
    <h2 style="font-size:.95rem;font-weight:700;margin-bottom:10px">☁️ Cloud Sync (GitHub Gist)</h2>
    <p class="sync-steps">
      Your ratings, notes, shelves, reading dates, and loans sync to a <strong>private GitHub Gist</strong>.<br>
      To enable, create a token at
      <a href="https://github.com/settings/tokens/new?scopes=gist&description=McLemore+Library" target="_blank">github.com/settings/tokens</a>
      with only the <strong>gist</strong> scope checked, then paste it below.
    </p>
    <input class="sync-token-input" id="sync-token-inp" type="password"
      placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
      value="${esc(_ghToken)}"
      autocomplete="off">
    <div style="display:flex;gap:8px;margin-top:10px;flex-wrap:wrap">
      <button class="btn-sm btn-accent" onclick="saveGhToken()">
        ${connected?'Update token':'Connect'}
      </button>
      ${connected?`<button class="btn-sm" onclick="syncNow()">↺ Sync now</button>`:''}
      ${connected?`<button class="btn-sm" style="color:#ef4444;border-color:#ef4444" onclick="disconnectGist()">Disconnect</button>`:''}
    </div>
    ${connected?`<div class="sync-status-bar show ok" id="sync-msg">✓ Connected — Gist ID: ${esc(_gistId||'(will create on first save)')}</div>`:''}`;
  document.getElementById('sync-overlay').classList.add('open');
  document.body.style.overflow='hidden';
}
function closeSync(e){
  if(e&&e.target!==document.getElementById('sync-overlay')&&!e.target.classList.contains('modal-close'))return;
  document.getElementById('sync-overlay').classList.remove('open');
  document.body.style.overflow='';
}
async function saveGhToken(){
  const inp=document.getElementById('sync-token-inp');
  if(!inp)return;
  const tok=inp.value.trim();
  if(!tok)return;
  _ghToken=tok; localStorage.setItem('mcl_gh_token',tok);
  _gistId=''; localStorage.removeItem('mcl_gist_id'); // reset so we re-discover
  const msg=document.getElementById('sync-msg')||document.createElement('div');
  msg.id='sync-msg'; msg.className='sync-status-bar show';
  msg.textContent='Testing connection…';
  inp.parentNode.appendChild(msg);
  // Test by loading
  try{
    const resp=await fetch('https://api.github.com/gists?per_page=1',{headers:ghHeaders()});
    if(!resp.ok)throw new Error();
    msg.className='sync-status-bar show ok';
    msg.textContent='✓ Connected! Loading your data…';
    await gistLoad();
    openSync(); // refresh modal
    applyF(); // re-render with loaded data
  }catch{
    msg.className='sync-status-bar show err';
    msg.textContent='✗ Could not connect. Check that your token has the "gist" scope.';
  }
}
function disconnectGist(){
  if(!confirm('Remove your sync token? Your local data stays, but syncing stops.'))return;
  _ghToken=''; _gistId='';
  localStorage.removeItem('mcl_gh_token'); localStorage.removeItem('mcl_gist_id');
  setSyncState('idle'); closeSync({target:document.getElementById('sync-overlay')});
}
async function syncNow(){ await gistLoad(); applyF(); renderRecentStrip(); openSync(); }

/* ── Keyboard shortcuts ── */
document.addEventListener('keydown',e=>{
  if(e.key==='Escape'){
    ['modal-overlay','stats-overlay','shelves-overlay','author-overlay','sync-overlay'].forEach(id=>{
      document.getElementById(id)?.classList.remove('open');
    });
    document.body.style.overflow='';
  }
  if(e.key==='/' && !['INPUT','TEXTAREA'].includes(document.activeElement.tagName)){
    e.preventDefault(); document.getElementById('q')?.focus();
  }
});

/* ── Infinite scroll ── */
const observer=new IntersectionObserver(
  entries=>{if(entries[0].isIntersecting&&rendered<filtered.length)renderMore();},{rootMargin:'200px'});
observer.observe(document.getElementById('sentinel'));

/* ── Service worker (offline support) ── */
if('serviceWorker' in navigator){
  const swCode=`const CACHE='mcl-v1';
self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.add('/'))));
self.addEventListener('fetch',e=>e.respondWith(caches.match(e.request).then(r=>r||fetch(e.request).then(resp=>{
  if(resp.ok&&e.request.method==='GET'){const clone=resp.clone();caches.open(CACHE).then(c=>c.put(e.request,clone));}
  return resp;
}).catch(()=>caches.match('/')))));`;
  const blob=new Blob([swCode],{type:'application/javascript'});
  navigator.serviceWorker.register(URL.createObjectURL(blob)).catch(()=>{});
  window.addEventListener('offline',()=>document.getElementById('offline-banner')?.classList.add('show'));
  window.addEventListener('online',()=>document.getElementById('offline-banner')?.classList.remove('show'));
}

/* ── URL sync ── */
function syncURL(){
  const params=new URLSearchParams();
  const map={q:'q',author:'fAuthor',cat:'fCat',fmt:'fFmt',loc:'fLoc',tag:'fTag',sort:'fSort',ser:'fSeries',minp:'fMinP',maxp:'fMaxP',minr:'fMinR'};
  Object.entries(map).forEach(([k,id])=>{const el=document.getElementById(id);if(el&&el.value)params.set(k,el.value);});
  const imp=new URLSearchParams(location.search).get('import');
  if(imp)params.set('import',imp);
  const str=params.toString();
  history.replaceState(null,'',str?'?'+str:location.pathname);
}

/* ════════════════════════════════════════════════════════════════
   V6 FEATURES
   ════════════════════════════════════════════════════════════════ */

/* ── Goal ring & yearly challenge ── */
function getYearGoal(y){ y=y||new Date().getFullYear(); return parseInt(lsGet('mcl_goal_'+y,0))||0; }
function setYearGoal(y,n){ lsSet('mcl_goal_'+y,n); triggerSync(); }
function getBooksFinishedYear(y){ y=y||new Date().getFullYear(); const dates=lsGetDates(); return Object.values(dates).filter(d=>d.finished&&d.finished.startsWith(y+'')).length; }
function initGoalRing(){
  const y=new Date().getFullYear();
  const goal=getYearGoal(y);
  const done=getBooksFinishedYear(y);
  const wrap=document.getElementById('goal-ring-container');
  if(!wrap)return;
  if(!goal){
    wrap.innerHTML='<span class="goal-ring-label" style="cursor:pointer;font-size:.72rem;color:var(--text2)" onclick="promptGoal()" title="Set '+y+' reading goal">\uD83C\uDFAF Set goal</span>';
    return;
  }
  const pct=Math.min(1,done/goal);
  const r=11; const circ=2*Math.PI*r;
  const offset=circ*(1-pct);
  wrap.innerHTML='<div class="goal-ring-wrap" onclick="promptGoal()" title="'+done+'/'+goal+' books finished in '+y+'"><div class="goal-ring"><svg width="28" height="28" viewBox="0 0 28 28"><circle class="goal-ring-bg" cx="14" cy="14" r="'+r+'"/><circle class="goal-ring-fill" cx="14" cy="14" r="'+r+'" stroke-dasharray="'+circ.toFixed(1)+'" stroke-dashoffset="'+offset.toFixed(1)+'"/></svg></div><span class="goal-ring-label">'+done+'/'+goal+'</span></div>';
}
function promptGoal(){
  const y=new Date().getFullYear();
  const cur=getYearGoal(y)||'';
  const n=prompt('Set your '+y+' reading goal (books to finish this year):',cur);
  if(n===null)return;
  const num=parseInt(n);
  if(num>0){setYearGoal(y,num);initGoalRing();}
}

/* ── Reading streak ── */
function getReadingStreak(){
  const dates=lsGetDates();
  const days=new Set();
  Object.values(dates).forEach(function(d){ if(d.finished)days.add(d.finished.slice(0,10)); });
  let streak=0;
  const today=new Date();
  for(let i=0;i<365;i++){
    const d=new Date(today);
    d.setDate(today.getDate()-i);
    const key=d.toISOString().slice(0,10);
    if(days.has(key))streak++;
    else if(i>0)break;
  }
  return streak;
}

/* ── Achievements ── */
const ACHIEVEMENTS=[
  {id:'first',  icon:'\uD83C\uDF31',name:'First Book',   desc:'Rate your first book',       test:function(r){return Object.keys(r).length>=1;}},
  {id:'fivestr',icon:'\u2B50',      name:'Five Stars',   desc:'Give a 5-star rating',       test:function(r){return Object.values(r).includes(5);}},
  {id:'ten',    icon:'\uD83D\uDD1F',name:'Ten Books',    desc:'Rate 10 books',              test:function(r){return Object.keys(r).length>=10;}},
  {id:'fifty',  icon:'\uD83C\uDFC6',name:'50 Books',     desc:'Rate 50 books',              test:function(r){return Object.keys(r).length>=50;}},
  {id:'hundred',icon:'\uD83D\uDCAF',name:'Century',      desc:'Rate 100 books',             test:function(r){return Object.keys(r).length>=100;}},
  {id:'str3',   icon:'\uD83D\uDD25',name:'On a Roll',    desc:'3-day reading streak',       test:function(){return getReadingStreak()>=3;}},
  {id:'str7',   icon:'\uD83C\uDF1F',name:'Week Streak',  desc:'7-day reading streak',       test:function(){return getReadingStreak()>=7;}},
  {id:'shelf',  icon:'\uD83D\uDCDA',name:'Shelf Builder',desc:'Create a custom shelf',      test:function(r,cs){return cs.length>0;}},
  {id:'notes5', icon:'\uD83D\uDCDD',name:'Annotator',    desc:'Write 5 notes',              test:function(r,cs,n){return Object.keys(n).length>=5;}},
  {id:'loan',   icon:'\uD83E\uDD1D',name:'Generous',     desc:'Loan out a book',            test:function(r,cs,n,l){return Object.keys(l).length>=1;}},
  {id:'goal',   icon:'\uD83C\uDFAF',name:'Goal Setter',  desc:'Set a yearly reading goal',  test:function(){return getYearGoal()>0;}},
  {id:'finish', icon:'\u2705',      name:'Finisher',     desc:'Mark a book as finished',    test:function(){return Object.values(lsGetDates()).some(function(d){return d.finished;});}},
  {id:'timer',  icon:'\u23F1',      name:'Timer',        desc:'Log a reading session',      test:function(){return lsGet('mcl_sessions',[]).length>0;}},
];
function computeAchievements(){
  const r=lsGetRatings(); const cs=getCustomShelves(); const n=lsGetNotes(); const l=lsGetLoans();
  return ACHIEVEMENTS.map(function(a){return Object.assign({},a,{earned:a.test(r,cs,n,l)});});
}
function openAchievements(){
  const list=computeAchievements();
  const earned=list.filter(function(a){return a.earned;}).length;
  document.getElementById('achieve-inner').innerHTML='<h2 style="font-size:1.1rem;font-weight:700;margin-bottom:12px">\uD83C\uDF96\uFE0F Achievements <span style="font-size:.8rem;color:var(--text2);font-weight:400">'+earned+'/'+list.length+'</span></h2><div class="achieve-grid">'+list.map(function(a){return'<div class="achieve-card '+(a.earned?'earned':'locked')+'"><div class="achieve-icon">'+a.icon+'</div><div class="achieve-name">'+a.name+'</div><div class="achieve-desc">'+a.desc+'</div></div>';}).join('')+'</div>';
  document.getElementById('achieve-overlay').classList.add('open');
  document.body.style.overflow='hidden';
}
function closeAchievements(e){
  if(!e||e.target===document.getElementById('achieve-overlay')||e.target.classList.contains('modal-close')){
    document.getElementById('achieve-overlay').classList.remove('open');
    document.body.style.overflow='';
  }
}

/* ── Reading calendar heatmap ── */
function renderCalendar(containerId){
  const container=document.getElementById(containerId);
  if(!container)return;
  const dates=lsGetDates();
  const dayMap={};
  Object.values(dates).forEach(function(d){ if(d.finished){const k=d.finished.slice(0,10);dayMap[k]=(dayMap[k]||0)+1;} });
  const today=new Date();
  const cells=[];
  const monthLabel=[];
  let lastM=-1;
  for(let i=363;i>=0;i--){
    const d=new Date(today);d.setDate(today.getDate()-i);
    const k=d.toISOString().slice(0,10);
    const cnt=dayMap[k]||0;
    const lvl=cnt===0?0:cnt===1?1:cnt===2?2:cnt<=4?3:4;
    cells.push({k:k,cnt:cnt,lvl:lvl});
    const m=d.getMonth();
    if(m!==lastM){monthLabel.push({col:Math.floor((363-i)/7),label:d.toLocaleString('default',{month:'short'})});lastM=m;}
  }
  const totalCols=Math.ceil(cells.length/7);
  let html='<div style="font-size:.72rem;font-weight:600;margin-bottom:5px;color:var(--text2)">\uD83D\uDCC5 Reading Calendar (past year)</div>';
  html+='<div class="cal-wrap"><div class="cal-months">';
  for(let c=0;c<totalCols;c++){
    const ml=monthLabel.find(function(m){return m.col===c;});
    html+='<div style="width:14px;font-size:.58rem;color:var(--text3);overflow:visible;white-space:nowrap">'+(ml?ml.label:'')+'</div>';
  }
  html+='</div><div class="cal-grid">';
  cells.forEach(function(cell){
    const tip=cell.cnt?cell.cnt+' book'+(cell.cnt>1?'s':'')+' finished on '+cell.k:cell.k;
    html+='<div class="cal-cell l'+cell.lvl+'" title="'+tip+'"></div>';
  });
  html+='</div><div class="cal-legend"><div class="cal-legend-cell" style="background:var(--surface2)"></div><span>Less</span>';
  [1,2,3,4].forEach(function(l){html+='<div class="cal-legend-cell cal-cell l'+l+'"></div>';});
  html+='<span>More</span></div></div>';
  container.innerHTML=html;
}

/* ── Genre pie chart ── */
function renderGenrePie(containerId){
  const container=document.getElementById(containerId);
  if(!container)return;
  const catMap={};
  ALL.forEach(function(b){if(b.c)catMap[b.c]=(catMap[b.c]||0)+1;});
  const entries=Object.entries(catMap).sort(function(a,b){return b[1]-a[1];}).slice(0,8);
  const total=entries.reduce(function(s,e){return s+e[1];},0);
  if(!total){container.innerHTML='<div style="color:var(--text3);font-size:.8rem">No category data</div>';return;}
  const COLORS=['#4f46e5','#7c3aed','#db2777','#ea580c','#d97706','#16a34a','#0891b2','#6b7280'];
  const R=60,CX=70,CY=70;
  let angle=0;
  const slices=entries.map(function(entry,i){
    const cat=entry[0],cnt=entry[1];
    const pct=cnt/total;
    const a1=angle;angle+=pct*2*Math.PI;
    const x1=CX+R*Math.cos(a1-Math.PI/2),y1=CY+R*Math.sin(a1-Math.PI/2);
    const x2=CX+R*Math.cos(angle-Math.PI/2),y2=CY+R*Math.sin(angle-Math.PI/2);
    const large=pct>0.5?1:0;
    return{cat:cat,cnt:cnt,pct:pct,path:'M'+CX+','+CY+'L'+x1.toFixed(1)+','+y1.toFixed(1)+'A'+R+','+R+',0,'+large+',1,'+x2.toFixed(1)+','+y2.toFixed(1)+'Z',color:COLORS[i]};
  });
  const svg='<svg width="140" height="140" viewBox="0 0 140 140">'+slices.map(function(s){return'<path d="'+s.path+'" fill="'+s.color+'" stroke="var(--bg)" stroke-width="1.5"><title>'+esc(s.cat)+': '+s.cnt+'</title></path>';}).join('')+'</svg>';
  const legend=slices.map(function(s){return'<div class="genre-legend-item" onclick="closeStats({target:document.getElementById(\'stats-overlay\')});setFilter(\'category\',\''+esc(s.cat)+'\')"><div class="genre-legend-dot" style="background:'+s.color+'"></div><span class="genre-legend-label">'+esc(s.cat)+'</span><span class="genre-legend-pct">'+Math.round(s.pct*100)+'%</span></div>';}).join('');
  container.innerHTML='<div class="genre-chart"><div class="genre-pie-wrap">'+svg+'</div><div class="genre-legend">'+legend+'</div></div>';
}

/* ── Reading pace & completion ── */
function calcReadingPace(){
  const dates=lsGetDates();
  const finished=Object.values(dates).filter(function(d){return d.finished;}).sort(function(a,b){return a.finished.localeCompare(b.finished);});
  if(finished.length<2)return null;
  const first=new Date(finished[0].finished);
  const last=new Date(finished[finished.length-1].finished);
  const days=Math.max(1,Math.round((last-first)/86400000));
  return{total:finished.length,days:days,perMonth:(finished.length/days*30).toFixed(1),daysPer:(days/finished.length).toFixed(0)};
}
function calcCompletionRate(){
  const dates=lsGetDates();
  const finished=Object.values(dates).filter(function(d){return d.finished;}).length;
  const rated=Object.keys(lsGetRatings()).length;
  if(!rated&&!finished)return null;
  const started=Math.max(rated,finished);
  return{started:started,finished:finished,pct:started?Math.round(finished/started*100):0};
}

/* ── Session timer ── */
var _timerInterval=null,_timerTotal=0,_timerRunning=false,_timerBookId=null;
function initTimerFAB(){
  const fab=document.getElementById('timer-fab');
  if(fab)fab.addEventListener('click',toggleTimerPopup);
}
function toggleTimerPopup(){
  const p=document.getElementById('timer-popup');
  if(!p)return;
  p.classList.toggle('open');
  if(p.classList.contains('open'))populateTimerBooks();
}
function populateTimerBooks(){
  const sel=document.getElementById('timer-book-sel');
  if(!sel)return;
  const prog=lsGetProgress();
  const inProg=ALL.filter(function(b){return prog[b.id]&&prog[b.id]<100;}).slice(0,40);
  sel.innerHTML='<option value="">— select a book —</option>'+inProg.map(function(b){return'<option value="'+esc(b.id)+'">'+esc(b.t.slice(0,45))+'</option>';}).join('');
  if(_timerBookId)sel.value=_timerBookId;
}
function timerTick(){
  _timerTotal++;
  const h=String(Math.floor(_timerTotal/3600)).padStart(2,'0');
  const m=String(Math.floor((_timerTotal%3600)/60)).padStart(2,'0');
  const s=String(_timerTotal%60).padStart(2,'0');
  const el=document.getElementById('timer-display');
  if(el)el.textContent=h+':'+m+':'+s;
}
function startTimer(){
  if(_timerRunning)return;
  _timerRunning=true;
  const sel=document.getElementById('timer-book-sel');
  _timerBookId=sel?sel.value||null:null;
  _timerInterval=setInterval(timerTick,1000);
  const fab=document.getElementById('timer-fab');
  if(fab)fab.classList.add('running');
  const btn=document.getElementById('timer-start-btn');
  if(btn)btn.textContent='Pause';
}
function pauseTimer(){
  if(!_timerRunning)return;
  _timerRunning=false;
  clearInterval(_timerInterval);
  const fab=document.getElementById('timer-fab');
  if(fab)fab.classList.remove('running');
  const btn=document.getElementById('timer-start-btn');
  if(btn)btn.textContent='Resume';
}
function resetTimer(){
  pauseTimer();_timerTotal=0;
  const el=document.getElementById('timer-display');
  if(el)el.textContent='00:00:00';
  const btn=document.getElementById('timer-start-btn');
  if(btn)btn.textContent='Start';
}
function toggleTimer(){if(_timerRunning)pauseTimer();else startTimer();}
function logSession(){
  const mins=Math.round(_timerTotal/60);
  if(mins<1){alert('Session too short to log (need at least 1 minute).');return;}
  const sessions=lsGet('mcl_sessions',[]);
  sessions.push({date:new Date().toISOString().slice(0,10),bookId:_timerBookId,mins:mins});
  lsSet('mcl_sessions',sessions);
  triggerSync();
  resetTimer();
  toggleTimerPopup();
  alert('\u2705 Logged '+mins+'-minute reading session!');
}

/* ── Open Library API ── */
async function fetchOpenLibrary(title,author,targetId){
  const container=document.getElementById(targetId);
  if(container)container.innerHTML='<span style="color:var(--text3);font-size:.72rem">Loading Open Library data\u2026</span>';
  try{
    const q=encodeURIComponent((title+' '+author).slice(0,80));
    const resp=await fetch('https://openlibrary.org/search.json?q='+q+'&limit=1&fields=title,author_name,first_publish_year,isbn,number_of_pages_median,subject');
    if(!resp.ok)throw new Error('fetch');
    const data=await resp.json();
    const doc=data.docs&&data.docs[0];
    if(!doc){if(container)container.innerHTML='';return;}
    const parts=[];
    if(doc.first_publish_year)parts.push('<span><b>First published:</b> '+doc.first_publish_year+'</span>');
    if(doc.isbn&&doc.isbn[0])parts.push('<span><b>ISBN:</b> '+doc.isbn[0]+'</span>');
    if(doc.subject&&doc.subject.length)parts.push('<span><b>Subjects:</b> '+doc.subject.slice(0,4).join(', ')+'</span>');
    if(container)container.innerHTML=parts.length
      ?'<div style="font-size:.72rem;color:var(--text2);display:flex;flex-direction:column;gap:2px;margin-top:4px">'+parts.join('')+'</div>'
      :'';
  }catch(e){if(container)container.innerHTML='';}
}

/* ── Share / recommendation card ── */
function openShareCard(bookId){
  const b=bookMap[bookId];if(!b)return;
  const overlay=document.getElementById('share-overlay');if(!overlay)return;
  document.getElementById('share-inner').innerHTML='<h2 style="font-size:1.05rem;font-weight:700;margin-bottom:10px">\uD83D\uDCE4 Share "'+esc(b.t.slice(0,40))+'"</h2><div class="share-canvas-wrap"><canvas id="share-canvas" width="400" height="220"></canvas></div><div style="display:flex;gap:6px;margin-top:10px;flex-wrap:wrap"><button class="btn-sm btn-accent" onclick="downloadShareCard()">\u2B07\uFE0F Download Image</button><button class="btn-sm" onclick="copyShareURL(\''+esc(bookId)+'\')">\uD83D\uDD17 Copy Link</button></div>';
  overlay.classList.add('open');
  document.body.style.overflow='hidden';
  requestAnimationFrame(function(){drawShareCard(b);});
}
function closeShareOverlay(e){
  if(!e||e.target===document.getElementById('share-overlay')||e.target.classList.contains('modal-close')){
    document.getElementById('share-overlay').classList.remove('open');
    document.body.style.overflow='';
  }
}
function drawShareCard(b){
  const canvas=document.getElementById('share-canvas');if(!canvas)return;
  const ctx=canvas.getContext('2d');const W=400,H=220;
  const grad=ctx.createLinearGradient(0,0,W,H);
  grad.addColorStop(0,'#4f46e5');grad.addColorStop(1,'#7c3aed');
  ctx.fillStyle=grad;ctx.fillRect(0,0,W,H);
  const rating=lsGetRatings()[b.id]||0;
  function drawOverlay(){
    ctx.fillStyle='rgba(0,0,0,.32)';ctx.fillRect(100,0,W-100,H);
    ctx.fillStyle='#fff';
    ctx.font='bold 15px system-ui,sans-serif';
    const title=b.t.length>36?b.t.slice(0,34)+'\u2026':b.t;
    ctx.fillText(title,112,36);
    ctx.font='12px system-ui,sans-serif';ctx.fillStyle='rgba(255,255,255,.82)';
    ctx.fillText(b.a||'',112,56);
    if(b.c){ctx.font='11px system-ui,sans-serif';ctx.fillStyle='rgba(255,255,255,.6)';ctx.fillText(b.c,112,74);}
    if(rating){ctx.font='16px system-ui,sans-serif';ctx.fillStyle='#fbbf24';ctx.fillText('\u2605'.repeat(rating)+'\u2606'.repeat(5-rating),112,100);}
    ctx.font='bold 10px system-ui,sans-serif';ctx.fillStyle='rgba(255,255,255,.45)';ctx.fillText('\uD83D\uDCDA McLemore Library',112,H-14);
  }
  if(b.img){
    const img=new Image();img.crossOrigin='anonymous';
    img.onload=function(){ctx.drawImage(img,0,0,98,H);drawOverlay();};
    img.onerror=drawOverlay;
    img.src=b.img;
  }else{
    ctx.fillStyle='rgba(255,255,255,.15)';ctx.fillRect(0,0,98,H);
    ctx.font='38px sans-serif';ctx.fillText('\uD83D\uDCDA',20,H/2+14);
    drawOverlay();
  }
}
function downloadShareCard(){
  const canvas=document.getElementById('share-canvas');if(!canvas)return;
  const a=document.createElement('a');a.download='book-recommendation.png';a.href=canvas.toDataURL('image/png');a.click();
}
function copyShareURL(bookId){
  const url=location.origin+location.pathname+'?book='+encodeURIComponent(bookId);
  navigator.clipboard.writeText(url).then(function(){alert('Link copied!');}).catch(function(){prompt('Copy this link:',url);});
}

/* ── Currently reading widget ── */
function openWidgetModal(){
  const overlay=document.getElementById('widget-overlay');if(!overlay)return;
  const prog=lsGetProgress();
  const reading=ALL.filter(function(b){return prog[b.id]&&prog[b.id]<100;}).slice(0,3);
  let preview='';
  reading.forEach(function(b){
    const p=prog[b.id]||0;
    preview+='<div style="display:flex;gap:8px;align-items:center;margin-bottom:6px">'
      +(b.img?'<img src="'+esc(b.img)+'" style="width:32px;height:48px;object-fit:cover;border-radius:3px" loading="lazy">':'<div style="width:32px;height:48px;background:var(--surface3);border-radius:3px;display:flex;align-items:center;justify-content:center">\uD83D\uDCDA</div>')
      +'<div style="flex:1;min-width:0">'
      +'<div style="font-size:.76rem;font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'+esc(b.t.slice(0,30))+'</div>'
      +'<div style="font-size:.66rem;color:var(--text2)">'+esc(b.a||'')+'</div>'
      +'<div style="height:4px;background:var(--surface3);border-radius:2px;margin-top:3px"><div style="height:4px;background:var(--accent);border-radius:2px;width:'+p+'%"></div></div>'
      +'</div></div>';
  });
  if(!reading.length)preview='<div style="color:var(--text3);font-size:.8rem">No books currently in progress.</div>';
  const widgetCode='<iframe src="'+location.origin+location.pathname+'?widget=1" width="320" height="200" frameborder="0" style="border-radius:12px;border:1px solid #e5e7eb"></iframe>';
  document.getElementById('widget-inner').innerHTML='<h2 style="font-size:1.05rem;font-weight:700;margin-bottom:10px">\uD83D\uDCE1 Currently Reading Widget</h2><div class="widget-preview">'+preview+'</div><p style="font-size:.75rem;color:var(--text2);margin:10px 0 4px">Embed code:</p><textarea class="widget-code" id="widget-code-txt" readonly>'+esc(widgetCode)+'</textarea><button class="btn-sm btn-accent" style="margin-top:6px" onclick="navigator.clipboard.writeText(document.getElementById(\'widget-code-txt\').value).then(function(){alert(\'Copied!\');})">Copy embed code</button>';
  overlay.classList.add('open');document.body.style.overflow='hidden';
}
function closeWidgetOverlay(e){
  if(!e||e.target===document.getElementById('widget-overlay')||e.target.classList.contains('modal-close')){
    document.getElementById('widget-overlay').classList.remove('open');document.body.style.overflow='';
  }
}

/* ── Public reading profile ── */
function openPublicProfile(){
  const ratings=lsGetRatings(); const dates=lsGetDates();
  const fiveStars=ALL.filter(function(b){return ratings[b.id]===5;}).slice(0,10).map(function(b){return{t:b.t,a:b.a};});
  const recent=Object.entries(dates)
    .filter(function(e){return e[1].finished;})
    .sort(function(a,b){return b[1].finished.localeCompare(a[1].finished);})
    .slice(0,5)
    .map(function(e){const b=bookMap[e[0]];return b?{t:b.t,a:b.a,d:e[1].finished.slice(0,10)}:null;})
    .filter(Boolean);
  const streak=getReadingStreak();
  const pub={v:1,total:Object.keys(ratings).length,streak:streak,fiveStars:fiveStars,recent:recent};
  const encoded=btoa(encodeURIComponent(JSON.stringify(pub)));
  const url=location.origin+location.pathname+'?profile='+encoded;
  prompt('Your public reading profile URL (safe to share):',url);
}

/* ── Swipe gestures ── */
function addSwipeToCard(el,bookId){
  var startX=0,startY=0;
  var THRESHOLD=60;
  el.addEventListener('touchstart',function(e){startX=e.touches[0].clientX;startY=e.touches[0].clientY;},{passive:true});
  el.addEventListener('touchend',function(e){
    var dx=e.changedTouches[0].clientX-startX;
    var dy=Math.abs(e.changedTouches[0].clientY-startY);
    if(dx<THRESHOLD||dy>Math.abs(dx)*0.8)return;
    var shelves=getAllShelves();
    if(shelves.length>0){addToShelf(bookId,shelves[0].id);flashSwipeHint(el,'shelf');}
  },{passive:true});
}
function flashSwipeHint(el,type){
  var hint=el.querySelector('.swipe-hint-'+type);
  if(!hint)return;
  hint.style.opacity='1';
  setTimeout(function(){hint.style.opacity='0';},700);
}

/* ── PWA manifest ── */
function installPWA(){
  try{
    var manifest={name:'McLemore Library',short_name:'McL Library',start_url:location.href,
      display:'standalone',background_color:'#f0f0ee',theme_color:'#4f46e5',
      icons:[{src:"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ctext y='.9em' font-size='90'%3E%F0%9F%93%9A%3C/text%3E%3C/svg%3E",sizes:'any',type:'image/svg+xml'}]};
    var blob=new Blob([JSON.stringify(manifest)],{type:'application/manifest+json'});
    var url=URL.createObjectURL(blob);
    var link=document.getElementById('pwa-manifest');
    if(!link){link=document.createElement('link');link.id='pwa-manifest';link.rel='manifest';document.head.appendChild(link);}
    link.href=url;
    window.addEventListener('beforeinstallprompt',function(e){
      e.preventDefault();window._pwaPrompt=e;
      var btn=document.getElementById('pwa-install-btn');
      if(btn)btn.style.display='inline-flex';
    });
  }catch(e){console.warn('PWA manifest error',e);}
}
function promptInstallPWA(){
  if(window._pwaPrompt){
    window._pwaPrompt.prompt();
    window._pwaPrompt.userChoice.then(function(){
      window._pwaPrompt=null;
      var btn=document.getElementById('pwa-install-btn');if(btn)btn.style.display='none';
    });
  }else{alert('App install not available in this browser. Try Chrome on Android or Edge on desktop.');}
}

/* ── Bulk selection ── */
var _bulkMode=false;
var _bulkSelected=new Set();
function toggleBulkMode(){
  _bulkMode=!_bulkMode;
  _bulkSelected.clear();
  var bar=document.getElementById('bulk-bar');
  if(bar)bar.classList.toggle('show',_bulkMode);
  var gw=document.getElementById('grid-wrap');
  if(gw)gw.classList.toggle('bulk-mode',_bulkMode);
  if(!_bulkMode)document.querySelectorAll('.card.selected,.list-row.selected').forEach(function(el){el.classList.remove('selected');});
  updateBulkCount();
}
function toggleBulkSelect(bookId,el){
  if(!_bulkMode)return;
  if(_bulkSelected.has(bookId)){_bulkSelected.delete(bookId);el.classList.remove('selected');}
  else{_bulkSelected.add(bookId);el.classList.add('selected');}
  updateBulkCount();
}
function updateBulkCount(){
  var el=document.getElementById('bulk-count');
  if(el)el.textContent=_bulkSelected.size+' selected';
}
function bulkAddToShelf(){
  var sel=document.getElementById('bulk-shelf-sel');
  if(!sel||!sel.value){alert('Choose a shelf first.');return;}
  var shelfId=sel.value;
  var s=loadShelves(); if(!s[shelfId])s[shelfId]=[];
  var added=0;
  _bulkSelected.forEach(function(id){
    if(!s[shelfId].includes(id)){s[shelfId].push(id);added++;}
  });
  saveShelves(s);
  alert('Added '+added+' book'+(added!==1?'s':'')+' to shelf!');
  toggleBulkMode(); renderPage();
}
function bulkRate(){
  var sel=document.getElementById('bulk-rate-sel');
  if(!sel||!sel.value){alert('Choose a rating first.');return;}
  var rating=parseInt(sel.value);
  _bulkSelected.forEach(function(id){setRating(id,rating);});
  alert('Rated '+_bulkSelected.size+' book'+(_bulkSelected.size!==1?'s':'')+' '+rating+' \u2605');
  toggleBulkMode(); renderPage();
}
function initBulkBar(){
  var shelfSel=document.getElementById('bulk-shelf-sel');
  if(shelfSel){
    var all=getAllShelves();
    shelfSel.innerHTML='<option value="">Shelf\u2026</option>'+all.map(function(s){return'<option value="'+esc(s.id)+'">'+(s.icon||'')+' '+esc(s.label||s.name||s.id)+'</option>';}).join('');
  }
}

/* ── Populate shelf filter ── */
function populateShelfFilter(){
  const sel=document.getElementById('fShelf');
  if(!sel)return;
  const shelves=getAllShelves();
  sel.innerHTML='<option value="">All Shelves</option>'+shelves.map(d=>`<option value="${d.id}">${d.icon} ${d.label}</option>`).join('');
  const existing=document.getElementById('mf-wrap-shelf');
  if(existing)existing.remove();
  mfInit('shelf','fShelf');
  mfUpdateLabel('shelf');
}

/* ── Init ── */
function checkOnLoad(){
  const data=getImportData(); if(data)window.importData=data;
}
initDark(); initView(); loadFromURL(); checkOnLoad();
mergeExternalBooks();
populateShelfFilter();
mfInitAll();
_applyBotdState(); renderRecentStrip();
initGoalRing(); initTimerFAB(); initBulkBar(); installPWA();
// Load Gist data first, then render (async — will re-render if data changes)
if(_ghToken){ gistLoad().then(function(){ mergeExternalBooks(); applyF(); renderRecentStrip(); initGoalRing(); }); } else { applyF(); }
"""
print("JS done")

# ── HTML template ────────────────────────────────────────────────────────────
author_opts  = make_options(meta['authors'])
cat_opts     = make_options(meta['categories'])
fmt_opts     = make_options(meta['formats'])
loc_opts     = make_options(meta['locations'])
tag_opts     = make_options(meta['tags'])
series_opts  = make_options(meta['series'])
total        = meta['total']
built        = meta['built']

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>McLemore Library</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js"></script>
<style>{CSS}</style>
</head>
<body>

<div class="header">
  <div class="header-top">
    <div class="tool-btn-group">
      <button class="tool-btn" onclick="openStats()"    title="Stats">📊</button>
      <button class="tool-btn" onclick="openShelves()"  title="Shelves">📚</button>
      <button class="tool-btn" onclick="openAchievements()" title="Achievements">🏅</button>
      <button class="tool-btn" onclick="toggleBulkMode()" title="Bulk select">☑</button>
    </div>
    <h1>📚 McLemore Library</h1>
    <div class="tool-btn-group">
      <div id="goal-ring-container" style="display:flex;align-items:center;padding:0 4px"></div>
      <button class="tool-btn" onclick="openSync()" title="Cloud sync"><span class="sync-dot idle" id="sync-dot"></span>☁️</button>
      <button id="darkBtn" class="tool-btn" onclick="toggleDark()" title="Dark mode">🌙</button>
      <button id="viewBtn" class="tool-btn" onclick="toggleView()" title="Toggle view">≡</button>
      <button id="pwa-install-btn" class="tool-btn btn-accent" onclick="promptInstallPWA()" title="Install app" style="display:none">⬇ Install</button>
    </div>
  </div>
  <div class="subtitle">· {total:,} titles · Built {built} ·</div>

  <!-- Book of the Day -->
  <button class="botd-toggle" id="botd-toggle" onclick="toggleBotdPanel()">
    <span class="toggle-arrow">›</span><span>📅 Book of the Day</span>
  </button>
  <div id="botd-wrap" style="display:none"><div class="botd-bar" id="botd-bar"></div></div>

  <button class="filters-toggle" onclick="toggleFilters()">⚙ Filters</button>
  <div class="filters-body" id="filters-body">
    <div class="filter-row">
      <input type="text" id="q" placeholder="Search title, author, summary, tags…" oninput="applyF()">
      <select id="fAuthor" onchange="applyF()"><option value="">All Authors</option>{author_opts}</select>
      <select id="fCat"    onchange="applyF()"><option value="">All Categories</option>{cat_opts}</select>
      <select id="fCat2"   onchange="applyF()"><option value="">+ Category 2</option>{cat_opts}</select>
      <select id="fFmt"    onchange="applyF()"><option value="">All Formats</option>{fmt_opts}</select>
      <select id="fLoc"    onchange="applyF()"><option value="">All Locations</option>{loc_opts}</select>
      <select id="fShelf"  onchange="applyF()"><option value="">All Shelves</option></select>
    </div>
    <div class="filter-row">
      <select id="fTag"    onchange="applyF()"><option value="">All Tags</option>{tag_opts}</select>
      <select id="fSeries" onchange="applyF()"><option value="">All Series</option>{series_opts}</select>
      <select id="fSort"   onchange="applyF()" style="max-width:155px">
        <option value="">Default order</option>
        <option value="title_az">Title A → Z</option>
        <option value="title_za">Title Z → A</option>
        <option value="author_az">Author A → Z</option>
        <option value="pages_asc">Pages: fewest first</option>
        <option value="pages_desc">Pages: most first</option>
        <option value="rating_desc">Highest rated first</option>
      </select>
      <select id="fMinR" onchange="applyF()" style="max-width:120px">
        <option value="">Any rating</option>
        <option value="1">★ 1+</option>
        <option value="2">★★ 2+</option>
        <option value="3">★★★ 3+</option>
        <option value="4">★★★★ 4+</option>
        <option value="5">★★★★★ 5 only</option>
      </select>
      <input type="number" id="fMinP" placeholder="Min pages" min="0" style="width:95px" oninput="applyF()">
      <input type="number" id="fMaxP" placeholder="Max pages" min="0" style="width:95px" oninput="applyF()">
    </div>
  </div>

  <div class="count-row">
    <span class="count-lbl" id="countLbl">Showing 0 of 0</span>
    <button class="btn-sm btn-accent" onclick="surpriseMe()">🎲 Surprise Me</button>
    <button class="btn-sm" onclick="exportXLSX()" title="Export to Excel">⬇ Excel</button>
    <button class="btn-sm" onclick="printList()" title="Print / Reading list">🖨 Print</button>
    <button class="btn-sm" onclick="clearF()">✕ Clear</button>
  </div>
</div>

<!-- Bulk action bar -->
<div class="bulk-bar" id="bulk-bar">
  <span id="bulk-count">0 selected</span>
  <select id="bulk-shelf-sel"></select>
  <button class="btn-sm btn-accent" onclick="bulkAddToShelf()">Add to shelf</button>
  <select id="bulk-rate-sel">
    <option value="">Rate…</option>
    <option value="1">★ 1</option>
    <option value="2">★★ 2</option>
    <option value="3">★★★ 3</option>
    <option value="4">★★★★ 4</option>
    <option value="5">★★★★★ 5</option>
  </select>
  <button class="btn-sm" onclick="bulkRate()">Rate</button>
  <button class="btn-sm" onclick="toggleBulkMode()" style="margin-left:auto">✕ Cancel</button>
</div>

<!-- Recently viewed strip -->
<button class="recent-toggle" id="recent-toggle" onclick="toggleRecentPanel()" style="display:none">
  <span class="toggle-arrow">›</span><span>🕐 Recently Viewed</span>
</button>
<div id="recent-wrap" style="display:none">
  <div class="recent-strip" id="recent-strip"></div>
</div>

<div class="grid-wrap" id="grid-wrap">
  <div class="book-grid" id="book-grid"></div>
  <div id="sentinel" style="height:1px"></div>
</div>

<!-- Book detail modal -->
<div id="modal-overlay" class="modal-overlay" onclick="closeModal(event)">
  <div class="modal">
    <button class="modal-close" onclick="_closeModal()">✕</button>
    <div id="modal-inner"></div>
  </div>
</div>

<!-- Shelves modal -->
<div id="shelves-overlay" class="modal-overlay" onclick="closeShelves(event)">
  <div class="modal shelves-modal">
    <button class="modal-close" onclick="closeShelves({{target:this}})">✕</button>
    <div id="shelves-inner"></div>
  </div>
</div>

<!-- Stats modal -->
<div id="stats-overlay" class="modal-overlay" onclick="closeStats(event)">
  <div class="modal stats-modal">
    <button class="modal-close" onclick="closeStats({{target:this}})">✕</button>
    <div id="stats-inner"></div>
  </div>
</div>

<!-- Author modal -->
<div id="author-overlay" class="modal-overlay" onclick="closeAuthorModal(event)">
  <div class="modal author-modal">
    <button class="modal-close" onclick="closeAuthorModal({{target:this}})">✕</button>
    <div id="author-inner"></div>
  </div>
</div>

<!-- Sync / Settings modal -->
<div id="sync-overlay" class="modal-overlay" onclick="closeSync(event)">
  <div class="modal sync-modal">
    <button class="modal-close" onclick="closeSync({{target:this}})">✕</button>
    <div id="sync-inner"></div>
  </div>
</div>

<!-- Achievements modal -->
<div id="achieve-overlay" class="modal-overlay" onclick="closeAchievements(event)">
  <div class="modal" style="max-width:520px">
    <button class="modal-close" onclick="closeAchievements({{target:this}})">✕</button>
    <div id="achieve-inner"></div>
  </div>
</div>

<!-- Share card modal -->
<div id="share-overlay" class="modal-overlay" onclick="closeShareOverlay(event)">
  <div class="modal share-card-modal">
    <button class="modal-close" onclick="closeShareOverlay({{target:this}})">✕</button>
    <div id="share-inner"></div>
  </div>
</div>

<!-- Widget modal -->
<div id="widget-overlay" class="modal-overlay" onclick="closeWidgetOverlay(event)">
  <div class="modal" style="max-width:480px">
    <button class="modal-close" onclick="closeWidgetOverlay({{target:this}})">✕</button>
    <div id="widget-inner"></div>
  </div>
</div>

<!-- External book tracker modal -->
<div id="ext-overlay" class="modal-overlay" onclick="closeExternalModal(event)">
  <div class="modal" style="max-width:440px;max-height:90vh;overflow-y:auto">
    <button class="modal-close" onclick="closeExternalModal()">✕</button>
    <h2 id="ext-modal-title" style="font-size:.95rem;font-weight:700;margin-bottom:4px">➕ Track a Book</h2>
    <p style="font-size:.75rem;color:var(--text2);margin-bottom:12px">Books tracked here won't appear in your Google Sheet library — they're stored locally and synced to your Gist.</p>
    <input type="hidden" id="ext-editing-id">
    <div id="ext-lookup-section">
      <div class="ext-lookup-row">
        <input type="text" id="ext-lookup-q" class="ext-lookup-inp" placeholder="Search by title or author to auto-fill…" onkeydown="if(event.key==='Enter'){{event.preventDefault();lookupBookOnline();}}">
        <button class="ext-lookup-btn" id="ext-lookup-btn" onclick="lookupBookOnline()">🔍 Look up</button>
      </div>
      <div id="ext-lookup-results"></div>
      <hr class="ext-divider" id="ext-divider">
    </div>
    <div style="display:flex;flex-direction:column;gap:11px">
      <div>
        <label class="ext-lbl">Title *</label>
        <input type="text" id="ext-title" placeholder="Book title…" class="ext-inp">
      </div>
      <div>
        <label class="ext-lbl">Author</label>
        <input type="text" id="ext-author" placeholder="Author name…" class="ext-inp">
      </div>
      <div style="display:flex;gap:8px">
        <div style="flex:1">
          <label class="ext-lbl">Pages</label>
          <input type="number" id="ext-pages" placeholder="Pages…" class="ext-inp">
        </div>
        <div style="flex:1">
          <label class="ext-lbl">Category</label>
          <input type="text" id="ext-cat" placeholder="e.g. Fiction…" class="ext-inp">
        </div>
      </div>
      <div>
        <label class="ext-lbl">Cover URL (optional)</label>
        <input type="text" id="ext-img" placeholder="https://…" class="ext-inp">
      </div>
      <div style="display:flex;gap:8px">
        <div style="flex:1">
          <label class="ext-lbl">Date Started</label>
          <input type="date" id="ext-started" class="ext-inp">
        </div>
        <div style="flex:1">
          <label class="ext-lbl">Date Finished</label>
          <input type="date" id="ext-finished" class="ext-inp">
        </div>
      </div>
      <div>
        <label class="ext-lbl">Add to Shelf</label>
        <div id="ext-shelf-picks" style="display:flex;flex-wrap:wrap;gap:6px;margin-top:4px"></div>
      </div>
      <button class="btn-accent" id="ext-save-btn" onclick="saveExternalBook()" style="padding:10px;margin-top:4px">Save & Track</button>
    </div>
  </div>
</div>

<!-- Reading session timer FAB -->
<button class="timer-btn" id="timer-fab" title="Reading session timer">⏱</button>
<div class="timer-popup" id="timer-popup">
  <div style="font-size:.8rem;font-weight:700;margin-bottom:6px">⏱ Reading Session Timer</div>
  <select class="timer-book-select" id="timer-book-sel"></select>
  <div class="timer-display" id="timer-display">00:00:00</div>
  <div class="timer-controls">
    <button id="timer-start-btn" class="btn-accent" onclick="toggleTimer()">Start</button>
    <button onclick="resetTimer()">Reset</button>
    <button onclick="logSession()">Log</button>
  </div>
</div>

<!-- Offline banner -->
<div class="offline-banner" id="offline-banner">📵 You're offline — showing cached library</div>

<script type="application/json" id="bdata">{books_raw}</script>
<script type="application/json" id="mdata">{meta_raw}</script>
<script>{JS}</script>
</body>
</html>"""

# ── Write & push ──────────────────────────────────────────────────────────────
out = '/sessions/lucid-dreamy-meitner/mnt/outputs/McLemore-Library.html'
with open(out, 'w') as f:
    f.write(html)
print(f"HTML written: {len(html.encode())//1024} KB")

repo = '/sessions/lucid-dreamy-meitner/McLemore-Library-work'
shutil.copy(out, os.path.join(repo, 'index.html'))
subprocess.run(['git','config','http.postBuffer','524288000'], cwd=repo, capture_output=True)
subprocess.run(['git','add','index.html'], cwd=repo, capture_output=True)
commit = subprocess.run(
    ['git','commit','-m','v6: analytics heatmap, goal ring, achievements, OL API, share cards, swipe, timer, PWA, bulk select'],
    cwd=repo, capture_output=True, text=True)
print("Commit:", commit.stdout.strip() or commit.stderr.strip())
env = os.environ.copy(); env['GIT_SSH_COMMAND']=''
push = subprocess.run(
    ['git','push',f'https://davidmmclemore:{GITHUB_TOKEN}@github.com/davidmmclemore/McLemore-Library.git','main'],
    cwd=repo, capture_output=True, text=True, env=env)
print("Push:", push.stderr.strip())
print("✅ Done!" if push.returncode==0 else f"❌ Push failed ({push.returncode})")
