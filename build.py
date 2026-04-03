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