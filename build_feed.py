#!/usr/bin/env python3
# Gera RSS de 56 artigos com URLs absolutas e datas originais.
from pathlib import Path
import os, csv, sys
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from email.utils import format_datetime
from xml.sax.saxutils import escape
from urllib.parse import urlparse

root=Path(__file__).resolve().parent
site=root/'site'
rows=list(csv.DictReader(open(root/'indice_resenhas.csv',encoding='utf-8-sig',newline='')))
base=(sys.argv[1] if len(sys.argv)>1 else os.environ.get('SITE_URL','')).strip().rstrip('/')+'/'
if base == '/' or not base.startswith('https://'):
    raise SystemExit('Informe URL pública https://.../ ou defina SITE_URL.')
def cdata(x): return '<![CDATA['+str(x).replace(']]>',']]]]><![CDATA[>')+']]>'
items=[]
for r in rows:
    filename=Path(r['arquivo_html']).name
  source=Path('posts', filename).read_text(encoding='utf-8')
    soup=BeautifulSoup(source,'html.parser')
    article=soup.find('article')
    figures=soup.find_all('figure')
    if article is None: raise ValueError('Artigo sem corpo: '+filename)
    content='\n'.join(str(f) for f in figures)+'\n'+str(article)
    content=content.replace('../imagens/',base+'imagens/')
    # ensure every photo in each item points to a public URL
    if '../imagens/' in content: raise ValueError('Imagem sem URL pública: '+filename)
    link=base+'posts/'+filename
    date=datetime.strptime(r['horario_original_brasilia'],'%d/%m/%Y %H:%M').replace(tzinfo=ZoneInfo('America/Sao_Paulo'))
    items.append(f'''<item>
<title>{escape(r['titulo'])}</title>
<link>{escape(link)}</link>
<guid isPermaLink="true">{escape(link)}</guid>
<pubDate>{format_datetime(date)}</pubDate>
<dc:creator>{cdata('Guilherme Reis')}</dc:creator>
<category>Resenhas</category>
<description>{cdata(article.get_text(' ',strip=True)[:350])}</description>
<content:encoded>{cdata(content)}</content:encoded>
</item>''')
items.reverse() # latest-first, with all 56 articles
rss=f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:dc="http://purl.org/dc/elements/1.1/">
<channel>
<title>Vida de Guilherme — Arquivo de Resenhas</title>
<link>{escape(base)}</link>
<description>Arquivo de resenhas originalmente publicadas no Instagram @gui_ta_lendo, de 2021 a 2026.</description>
<language>pt-BR</language>
<lastBuildDate>{format_datetime(datetime.now(timezone.utc))}</lastBuildDate>
<atom:link xmlns:atom="http://www.w3.org/2005/Atom" href="{escape(base+'feed.xml')}" rel="self" type="application/rss+xml" />
{''.join(items)}
</channel>
</rss>'''
(site/'feed.xml').write_text(rss,encoding='utf-8')
assert rss.count('<item>') == 56
print('OK: 56 artigos gerados em',site/'feed.xml','para',base)
