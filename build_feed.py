#!/usr/bin/env python3
from pathlib import Path
import csv
import os
import shutil
import sys
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from email.utils import format_datetime
from xml.sax.saxutils import escape

root = Path(__file__).resolve().parent
site = root / 'site'
base = (sys.argv[1] if len(sys.argv) > 1 else os.environ.get('SITE_URL', '')).strip().rstrip('/') + '/'
if base == '/' or not base.startswith('https://'):
    raise SystemExit('Informe uma URL publica HTTPS.')

site.mkdir(exist_ok=True)
for folder in ('posts', 'imagens'):
    origin = root / folder
    if not origin.is_dir():
        raise SystemExit(f'Pasta nao encontrada: {origin}')
    shutil.copytree(origin, site / folder, dirs_exist_ok=True)
if (root / 'index.html').exists():
    shutil.copy2(root / 'index.html', site / 'index.html')
(site / '.nojekyll').touch()

def cdata(value):
    return '<![CDATA[' + str(value).replace(']]>', ']]]]><![CDATA[>') + ']]>'

with (root / 'indice_resenhas.csv').open(encoding='utf-8-sig', newline='') as file:
    rows = list(csv.DictReader(file))
items = []
for row in rows:
    filename = Path(row['arquivo_html']).name
    source = (site / 'posts' / filename).read_text(encoding='utf-8')
    soup = BeautifulSoup(source, 'html.parser')
    article = soup.find('article')
    if article is None:
        raise ValueError(f'Artigo sem corpo: {filename}')
    figures = soup.find_all('figure')
capa = str(figures[0]) if figures else ''
content = capa + '\n' + str(article)
    content = content.replace('../imagens/', base + 'imagens/')
    if '../imagens/' in content:
        raise ValueError(f'Imagem sem URL publica: {filename}')
    link = base + 'posts/' + filename
    date = datetime.strptime(row['horario_original_brasilia'], '%d/%m/%Y %H:%M').replace(tzinfo=ZoneInfo('America/Sao_Paulo'))
    items.append(f'''<item>
<title>{escape(row['titulo'])}</title>
<link>{escape(link)}</link>
<guid isPermaLink="true">{escape(link)}</guid>
<pubDate>{format_datetime(date)}</pubDate>
<dc:creator>{cdata('Guilherme Reis')}</dc:creator>
<category>Resenhas</category>
<description>{cdata(article.get_text(' ', strip=True)[:350])}</description>
<content:encoded>{cdata(content)}</content:encoded>
</item>''')
items.reverse()
rss = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
<title>Vida de Guilherme — Arquivo de Resenhas</title>
<link>{escape(base)}</link>
<description>Arquivo de resenhas originalmente publicadas no Instagram @gui_ta_lendo, de 2021 a 2026.</description>
<language>pt-BR</language>
<lastBuildDate>{format_datetime(datetime.now(timezone.utc))}</lastBuildDate>
<atom:link href="{escape(base + 'feed.xml')}" rel="self" type="application/rss+xml" />
{''.join(items)}
</channel>
</rss>'''
if len(items) != 56:
    raise ValueError(f'Esperados 56 artigos; encontrados {len(items)}')
(site / 'feed.xml').write_text(rss, encoding='utf-8')
print(f'OK: {len(items)} artigos gerados em {site / "feed.xml"} para {base}')
