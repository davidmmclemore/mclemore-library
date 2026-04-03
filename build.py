import requests, json, re, csv, io
from collections import Counter
from datetime import datetime

SHEET_ID = "1I2r2ITzDtvC-RiJZauCeLi3vd26S_jAVz15KajTZwwc"

# --- Download CSV from Google Sheets ---
url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&sheet=Books"
resp = requests.get(url, timeout=60)
resp.raise_for_status()
reader = csv.reader(io.StringIO(resp.text))
rows = list(reader)
headers = rows[0]
data_rows = rows[1:]
print(f"Downloaded {len(data_rows)} rows")

def col(row, i, default=''):
    try: return row[i].strip() if i < len(row) else default
    except: return default

def clean_html(text):
    if not text: return ''
    text = re.sub(r'<[^>]+>', ' ', text)
    for ent,rep in [('&nbsp;',' '),('&amp;','&'),('&lt;','<'),('&gt;','>'),
                    ('&mdash;','—'),('&ndash;','–'),('&ldquo;','"'),('&rdquo;','"'),
                    ('&lsquo;',"'"),('&rsquo;',"'"),('&#39;',"'"),('&quot;','"')]:
        text = text.replace(ent, rep)
    text = re.sub(r'&#x[0-9a-fA-F]+;', '', text)
    text = re.sub(r'&[a-zA-Z0-9]+;', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:400]

def parse_tags(s):
    if not s: return []
    return [t.strip() for t in s.split(',') if t.strip()][:12]

def extract_asin(url):
    if not url: return ''
    m = re.search(r'/dp/([A-Z0-9]{10})', url, re.IGNORECASE)
    return m.group(1) if m else ''

def get_cover(cover_url, amz_url, asin_col, prime_asin):
    if cover_url and cover_url.startswith('http'):
        return cover_url
    asin = extract_asin(amz_url)
    if not asin and re.match(r'^[A-Z0-9]{10}$', prime_asin, re.I):
        asin = prime_asin
    if not asin and re.match(r'^[A-Z0-9]{10}$', asin_col, re.I):
        asin = asin_col
    if asin:
        return f'https://images-na.ssl-images-amazon.com/images/P/{asin}.01.LZZZZZZZ.jpg'
    return ''

books = []
for i, row in enumerate(data_rows):
    tag_list = parse_tags(col(row, 7))
    cover = get_cover(col(row, 16), col(row, 17), col(row, 19), col(row, 20))
    pages_raw = col(row, 6)
    try: pages = int(float(pages_raw)) if pages_raw else 0
    except: pages = 0
    book_id = col(row, 0) or f'BOOK-{i:04d}'
    b = {
        'id': book_id, 't': clean_html(col(row,1)), 'a': clean_html(col(row,2)),
        'f': clean_html(col(row,4)), 'c': clean_html(col(row,5)),
        'l': clean_html(col(row,8)), 'p': pages,
        'tg': tag_list, 's': clean_html(col(row,9)),
        'img': cover, 'url': col(row,17),
    }
    books.append(b)

authors = [b['a'] for b in books if b['a']]
top_authors = [a for a, _ in Counter(authors).most_common(300)]
categories = sorted(set(b['c'] for b in books if b['c']))
formats = sorted(set(b['f'] for b in books if b['f']))
locations = sorted(set(b['l'] for b in books if b['l']))
all_tags = sorted(set(t for b in books for t in b['tg'] if t))

meta = {
    'authors': top_authors, 'categories': categories,
    'formats': formats, 'locations': locations,
    'tags': all_tags, 'total': len(books),
    'built': datetime.now().strftime('%B %d, %Y')
}

books_raw = json.dumps(books, separators=(',', ':'))
meta_raw = json.dumps(meta, separators=(',', ':'))

def make_options(items):
    return '\n'.join(f'<option value="{v}">{v}</option>' for v in items)

cover_count = sum(1 for b in books if b['img'])
print(f'Books: {len(books)}, covers: {cover_count} ({cover_count/len(books)*100:.1f}%)')
print(f'Categories: {len(categories)}, Authors: {len(top_authors)}, Tags: {len(all_tags)}')

html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>McLemore Library</title>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;background:#f0f0ee;color:#222}}
a{{color:inherit;text-decoration:none}}
.header{{background:#fff;border-bottom:1px solid #e5e7eb;padding:12px 16px 0;position:sticky;top:0;z-index:100;box-shadow:0 1px 3px rgba(0,0,0,.07)}}
.header h1{{font-size:1.3rem;font-weight:700;margin-bottom:2px;text-align:center}}
.header .subtitle{{text-align:center;color:#6b7280;font-size:.78rem;margin-bottom:10px}}
.filter-bar{{display:flex;flex-wrap:wrap;gap:6px;align-items:center;padding-bottom:8px}}
.filter-bar input{{flex:1;min-width:160px;padding:7px 11px;border:1px solid #d1d5db;border-radius:8px;font-size:.85rem}}
.filter-bar select{{padding:7px 8px;border:1px solid #d1d5db;border-radius:8px;font-size:.8rem;background:#fff;cursor:pointer;max-width:140px}}
.tag-row{{display:flex;gap:6px;align-items:center;padding-bottom:8px;flex-wrap:wrap}}
.tag-row select{{flex:1;padding:7px 8px;border:1px solid #d1d5db;border-radius:8px;font-size:.8rem;background:#fff;cursor:pointer}}
.count-label{{font-size:.78rem;color:#6b7280;white-space:nowrap}}
.btn-clear{{padding:6px 10px;border:1px solid #d1d5db;border-radius:8px;background:#fff;cursor:pointer;font-size:.8rem;color:#374151}}
.btn-clear:hover{{background:#f3f4f6}}
.filters-toggle{{display:none;width:100%;padding:7px;border:1px solid #d1d5db;border-radius:8px;background:#fff;font-size:.83rem;color:#374151;cursor:pointer;margin-bottom:6px;text-align:center}}
.filters-body{{display:contents}}
.grid-wrap{{padding:12px 8px}}
.book-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px}}
.card{{background:#fff;border-radius:8px;border:1px solid #e5e7eb;overflow:hidden;display:flex;flex-direction:column;transition:box-shadow .15s,transform .15s;cursor:pointer}}
.card:hover{{box-shadow:0 4px 14px rgba(0,0,0,.1);transform:translateY(-2px)}}
.card-cover{{width:100%;aspect-ratio:2/3;object-fit:cover;display:block;background:#f3f4f6}}
.no-cover{{width:100%;aspect-ratio:2/3;display:flex;align-items:center;justify-content:center;font-size:2rem;background:#f3f4f6;color:#9ca3af}}
.card-body{{padding:8px;display:flex;flex-direction:column;gap:4px;flex:1}}
.card-title{{font-size:.75rem;font-weight:700;line-height:1.3;color:#111}}
.card-author{{font-size:.68rem;color:#4f46e5;cursor:pointer;font-weight:500}}
.card-author:hover{{text-decoration:underline}}
.badges{{display:flex;flex-wrap:wrap;gap:3px;margin-top:2px}}
.badge{{font-size:.6rem;font-weight:600;padding:2px 6px;border-radius:10px;cursor:pointer;white-space:nowrap}}
.badge-format{{background:#dbeafe;color:#1d4ed8}}
.badge-category{{background:#ede9fe;color:#6d28d9}}
.badge-location{{background:#d1fae5;color:#065f46}}
.badge:hover{{opacity:.75}}
.card-pages{{font-size:.62rem;color:#9ca3af}}
.card-tags{{display:flex;flex-wrap:wrap;gap:3px;margin-top:2px}}
.tag-pill{{font-size:.58rem;background:#f3f4f6;color:#374151;padding:2px 5px;border-radius:8px;cursor:pointer}}
.tag-pill:hover{{background:#e5e7eb}}
.card-summary{{font-size:.68rem;color:#6b7280;line-height:1.5;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;margin-top:2px}}
.card-summary.expanded{{-webkit-line-clamp:unset;display:block}}
.summary-toggle{{font-size:.63rem;color:#4f46e5;cursor:pointer;margin-top:2px;background:none;border:none;padding:0;text-align:left}}
.amazon-btn{{margin-top:auto;padding-top:6px}}
.amazon-btn a{{display:block;text-align:center;background:#ff9900;color:#111;font-size:.68rem;font-weight:700;padding:5px;border-radius:6px;text-decoration:none}}
.amazon-btn a:hover{{background:#e68900}}
.modal-overlay{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:200;align-items:center;justify-content:center;padding:16px}}
.modal-overlay.open{{display:flex}}
.modal{{background:#fff;border-radius:14px;max-width:680px;width:100%;max-height:90vh;overflow-y:auto;padding:24px;position:relative}}
.modal-close{{position:absolute;top:14px;right:16px;font-size:1.4rem;cursor:pointer;color:#6b7280;background:none;border:none;line-height:1}}
.modal-inner{{display:flex;gap:20px;flex-wrap:wrap}}
.modal-cover img,.modal-cover .no-cover{{width:160px;border-radius:8px;flex-shrink:0}}
.modal-cover .no-cover{{height:240px;font-size:3rem}}
.modal-info{{flex:1;min-width:200px}}
.modal-title{{font-size:1.1rem;font-weight:700;line-height:1.3;margin-bottom:6px}}
.modal-author{{color:#4f46e5;font-size:.9rem;margin-bottom:10px}}
.modal-meta{{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px}}
.modal-summary{{font-size:.84rem;color:#374151;line-height:1.65;margin-top:10px}}
.modal-amazon{{margin-top:14px}}
.modal-amazon a{{display:inline-block;background:#ff9900;color:#111;font-size:.82rem;font-weight:700;padding:8px 18px;border-radius:8px}}
.hidden{{display:none!important}}
.count-row{{display:flex;gap:6px;justify-content:space-between;align-items:center;padding-bottom:8px}}
@media (max-width:600px){{
  .header{{padding:10px 10px 0}}
  .header h1{{font-size:1.1rem}}
  .filters-toggle{{display:block}}
  .filters-body{{display:none;flex-direction:column;gap:6px;width:100%}}
  .filters-body.open{{display:flex}}
  .filter-bar{{flex-direction:column;align-items:stretch;gap:6px;padding-bottom:0}}
  .filter-bar input{{min-width:0;width:100%}}
  .filter-bar select{{max-width:100%;width:100%}}
  .tag-row{{flex-direction:column;align-items:stretch}}
  .tag-row select{{width:100%}}
  .grid-wrap{{padding:8px 6px}}
  .book-grid{{grid-template-columns:repeat(auto-fill,minmax(110px,1fr));gap:7px}}
  .card-body{{padding:6px;gap:3px}}
  .card-title{{font-size:.7rem}}
  .card-author{{font-size:.63rem}}
  .badge{{font-size:.56rem;padding:1px 5px}}
  .card-summary{{-webkit-line-clamp:2}}
  .modal{{padding:16px;border-radius:10px}}
  .modal-inner{{flex-direction:column}}
  .modal-cover img,.modal-cover .no-cover{{width:100%;max-width:180px;margin:0 auto}}
}}
</style>
</head>
<body>
<div class="header">
  <h1>📚 McLemore Library</h1>
  <div class="subtitle" id="subtitle">· {meta["total"]} titles · Built {meta["built"]} ·</div>
  <button class="filters-toggle" onclick="toggleFilters()">⚙ Filters</button>
  <div class="filters-body" id="filters-body">
  <div class="filter-bar">
    <input type="text" id="q" placeholder="Search title or author…" oninput="applyF()">
    <select id="fAuthor" onchange="applyF()"><option value="">All Authors</option>{make_options(meta["authors"])}</select>
    <select id="fCat" onchange="applyF()"><option value="">All Categories</option>{make_options(meta["categories"])}</select>
    <select id="fFmt" onchange="applyF()"><option value="">All Formats</option>{make_options(meta["formats"])}</select>
    <select id="fLoc" onchange="applyF()"><option value="">All Locations</option>{make_options(meta["locations"])}</select>
  </div>
  <div class="tag-row" id="tag-row">
    <select id="fTag" onchange="applyF()"><option value="">All Tags</option>{make_options(meta["tags"])}</select>
  </div>
  </div>
  <div class="count-row">
    <span class="count-label" id="countLbl">Showing 0 of 0</span>
    <button class="btn-clear" onclick="clearF()">✕ Clear</button>
  </div>
</div>
<div class="grid-wrap">
  <div class="book-grid" id="book-grid"></div>
  <div id="sentinel" style="height:1px"></div>
</div>
<div class="modal-overlay" id="modal-overlay" onclick="closeModal(event)">
  <div class="modal" id="modal">
    <button class="modal-close" onclick="closeModal()">✕</button>
    <div class="modal-inner" id="modal-inner"></div>
  </div>
</div>
<script type="application/json" id="bdata">{books_raw}</script>
<script type="application/json" id="mdata">{meta_raw}</script>
<script>
const ALL=JSON.parse(document.getElementById("bdata").textContent);
const META=JSON.parse(document.getElementById("mdata").textContent);
let filtered=[],rendered=0;
const PAGE=60;
function esc(s){{return String(s||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;")}}
function imgErr(el){{el.parentNode.innerHTML="<div class=\\"no-cover\\">📚</div>"}}
function imgEl(src,title){{if(!src)return"<div class=\\"no-cover\\">📚</div>";return`<img class="card-cover" src="${{esc(src)}}" alt="${{esc(title)}}" loading="lazy" onerror="imgErr(this)">`}}
function setFilter(key,val){{const map={{author:"fAuthor",category:"fCat",format:"fFmt",location:"fLoc",tag:"fTag"}};const el=document.getElementById(map[key]);if(el){{el.value=val;applyF()}}}}
function toggleFilters(){{const body=document.getElementById("filters-body");const btn=document.querySelector(".filters-toggle");const open=body.classList.toggle("open");btn.textContent=open?"✕ Hide filters":"⚙ Filters"}}
function cardHTML(b){{
  const tags=(b.tg||[]).map(t=>`<span class="tag-pill" onclick="event.stopPropagation();setFilter('tag','${{esc(t)}}')">${{esc(t)}}</span>`).join("");
  const sumId="sum-"+esc(b.id),togId="tog-"+esc(b.id);
  const sumHTML=b.s?`<div class="card-summary" id="${{sumId}}">${{esc(b.s)}}</div><button class="summary-toggle" id="${{togId}}" onclick="event.stopPropagation();toggleSum('${{esc(b.id)}}')">Read more ↓</button>`:"";
  const amazonBtn=b.url?`<div class="amazon-btn"><a href="${{esc(b.url)}}" target="_blank" onclick="event.stopPropagation()">View on Amazon →</a></div>`:"";
  return`<div class="card" onclick="openModal('${{esc(b.id)}}')">
    ${{imgEl(b.img,b.t)}}
    <div class="card-body">
      <div class="card-title">${{esc(b.t)}}</div>
      <div class="card-author" onclick="event.stopPropagation();setFilter('author','${{esc(b.a)}}')">${{esc(b.a)}}</div>
      <div class="badges">
        ${{b.f?`<span class="badge badge-format" onclick="event.stopPropagation();setFilter('format','${{esc(b.f)}}')">${{esc(b.f)}}</span>`:""}}
        ${{b.c?`<span class="badge badge-category" onclick="event.stopPropagation();setFilter('category','${{esc(b.c)}}')">${{esc(b.c)}}</span>`:""}}
        ${{b.l?`<span class="badge badge-location" onclick="event.stopPropagation();setFilter('location','${{esc(b.l)}}')">${{esc(b.l)}}</span>`:""}}
      </div>
      ${{b.p?`<div class="card-pages">${{b.p}} pages</div>`:""}}
      <div class="card-tags">${{tags}}</div>
      ${{sumHTML}}
      ${{amazonBtn}}
    </div>
  </div>`}}
function toggleSum(id){{const el=document.getElementById("sum-"+id);const btn=document.getElementById("tog-"+id);if(!el||!btn)return;const expanded=el.classList.toggle("expanded");btn.textContent=expanded?"Show less ↑":"Read more ↓"}}
function renderMore(){{const grid=document.getElementById("book-grid");const chunk=filtered.slice(rendered,rendered+PAGE);grid.insertAdjacentHTML("beforeend",chunk.map(cardHTML).join(""));rendered+=chunk.length}}
function applyF(){{
  const q=document.getElementById("q").value.toLowerCase().trim();
  const au=document.getElementById("fAuthor").value;
  const cat=document.getElementById("fCat").value;
  const fmt=document.getElementById("fFmt").value;
  const loc=document.getElementById("fLoc").value;
  const tag=document.getElementById("fTag").value;
  filtered=ALL.filter(b=>{{
    if(q&&!b.t.toLowerCase().includes(q)&&!b.a.toLowerCase().includes(q))return false;
    if(au&&b.a!==au)return false;
    if(cat&&b.c!==cat)return false;
    if(fmt&&b.f!==fmt)return false;
    if(loc&&b.l!==loc)return false;
    if(tag&&!(b.tg||[]).includes(tag))return false;
    return true;
  }});
  document.getElementById("countLbl").textContent=`Showing ${{filtered.length}} of ${{ALL.length}}`;
  const grid=document.getElementById("book-grid");
  grid.innerHTML="";rendered=0;renderMore();
}}
function clearF(){{document.getElementById("q").value="";["fAuthor","fCat","fFmt","fLoc","fTag"].forEach(id=>document.getElementById(id).value="");applyF()}}
const bookMap={{}};ALL.forEach(b=>bookMap[b.id]=b);
function openModal(id){{
  const b=bookMap[id];if(!b)return;
  const badges=[
    b.f&&`<span class="badge badge-format">${{esc(b.f)}}</span>`,
    b.c&&`<span class="badge badge-category">${{esc(b.c)}}</span>`,
    b.l&&`<span class="badge badge-location">${{esc(b.l)}}</span>`,
    b.p&&`<span class="badge" style="background:#fef3c7;color:#92400e">${{b.p}} pages</span>`,
  ].filter(Boolean).join("");
  const tags=(b.tg||[]).map(t=>`<span class="tag-pill">${{esc(t)}}</span>`).join("");
  const coverImg=b.img?`<img src="${{esc(b.img)}}" alt="${{esc(b.t)}}" style="width:160px;border-radius:8px" onerror="imgErr(this)">`:"<div class=\\"no-cover\\" style=\\"width:160px;height:240px;border-radius:8px\\">📚</div>";
  document.getElementById("modal-inner").innerHTML=`
    <div class="modal-cover">${{coverImg}}</div>
    <div class="modal-info">
      <div class="modal-title">${{esc(b.t)}}</div>
      <div class="modal-author">${{esc(b.a)}}</div>
      <div class="modal-meta">${{badges}}</div>
      ${{tags?`<div class="card-tags" style="margin-bottom:8px">${{tags}}</div>`:""}}
      ${{b.s?`<div class="modal-summary">${{esc(b.s)}}</div>`:""}}
      ${{b.url?`<div class="modal-amazon"><a href="${{esc(b.url)}}" target="_blank">View on Amazon →</a></div>`:""}}
    </div>`;
  document.getElementById("modal-overlay").classList.add("open");
  document.body.style.overflow="hidden";
}}
function closeModal(e){{if(e&&e.target!==document.getElementById("modal-overlay")&&!e.target.classList.contains("modal-close"))return;document.getElementById("modal-overlay").classList.remove("open");document.body.style.overflow=""}}
document.addEventListener("keydown",e=>{{if(e.key==="Escape")closeModal({{target:document.getElementById("modal-overlay")}});}});
const observer=new IntersectionObserver(entries=>{{if(entries[0].isIntersecting&&rendered<filtered.length)renderMore();}},{{rootMargin:"200px"}});
observer.observe(document.getElementById("sentinel"));
applyF();
</script>
</body>
</html>'''

with open('index.html', 'w') as f:
    f.write(html)
print(f"index.html written: {len(html.encode())//1024} KB")
