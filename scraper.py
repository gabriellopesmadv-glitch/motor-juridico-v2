import cloudscraper
from bs4 import BeautifulSoup
import feedparser
from urllib.parse import urlparse, urljoin
from datetime import datetime
import requests

# ==========================================
# INSIRA AQUI O NOVO URL DO GOOGLE APPS SCRIPT
URL_WEB_APP = "COLE_AQUI_O_SEU_URL_DO_WEB_APP"
# ==========================================

URLS_RSS = [
    "https://www.migalhas.com.br/arquivo/rss/migalhas.xml/rss",
    "https://www.conjur.com.br/feed/",
    "https://www.stj.jus.br/sites/portalp/Paginas/RSS.aspx",
    "https://www.tst.jus.br/rss",
    "https://www.senado.gov.br/rss/agenciasenado.xml",
    "https://www.camara.leg.br/noticias/rss",
    "https://agenciabrasil.ebc.com.br/feed/"
]

URLS_HTML = [
    "https://www.migalhas.com.br/",
    "https://www.conjur.com.br/",
    "https://www.jota.info/",
    "https://portal.jota.info/newsletter-jota",
    "https://noticias.stf.jus.br/",
    "https://www.cnj.jus.br/category/noticias/cnj/",
    "https://www.cnj.jus.br/agencia-cnj/cnj-noticias/",
    "https://www.gov.br/receitafederal/pt-br/assuntos/noticias",
    "https://www.gov.br/pgfn/pt-br",
    "https://www.gov.br/carf/pt-br/assuntos/noticias",
    "https://www2.camara.leg.br/agencia/assinarRSS.html",
    "https://www.direitonews.com.br/"
]

GATILHOS = [
    'tributário', 'tributario', 'icms', 'iss', 'ipi', 'irpj', 'csll', 'pis', 'cofins', 
    'itcmd', 'ipva', 'iptu', 'transação', 'pgfn', 'dívida ativa', 'compensação', 
    'restituição', 'ressarcimento', 'carf', 'reforma tributária', 'cbs', 'ibs', 'imposto',
    'execução fiscal', 'cumprimento de sentença', 'penhora', 'bloqueio', 'sisbajud', 'renajud', 
    'arresto', 'expropriação', 'prescrição', 'garantia', 'fiança', 'embargos',
    'repercussão geral', 'repetitivo', 'tese vinculante', 'súmula', 'modulação'
]

scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})

def normalizar_link(dominio_base, href):
    if href.startswith('http'): return href
    if not href.startswith('/'): href = '/' + href
    return dominio_base + href

def extrair():
    noticias = []
    vistos = set()
    print("Iniciando varredura...")
    
    for url in URLS_RSS:
        try:
            feed = feedparser.parse(scraper.get(url, timeout=15).text)
            cota = 0
            for entry in feed.entries:
                if cota >= 3: break
                tit = getattr(entry, 'title', '')
                lnk = getattr(entry, 'link', '')
                if tit and lnk and lnk not in vistos and any(g in tit.lower() for g in GATILHOS):
                    noticias.append({"titulo": tit.strip(), "link": lnk.strip(), "fonte": urlparse(url).netloc})
                    vistos.add(lnk)
                    cota += 1
        except Exception as e: print(f"Erro RSS {url}: {e}")

    for url in URLS_HTML:
        try:
            res = scraper.get(url, timeout=15)
            soup = BeautifulSoup(res.text, 'html.parser')
            dom = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
            cota = 0
            for a in soup.find_all('a', href=True):
                if cota >= 3: break
                tit = a.get_text().strip()
                lnk = normalizar_link(dom, a['href'])
                if len(tit) > 20 and lnk not in vistos and any(g in tit.lower() for g in GATILHOS):
                    noticias.append({"titulo": tit, "link": lnk, "fonte": urlparse(url).netloc})
                    vistos.add(lnk)
                    cota += 1
        except Exception as e: print(f"Erro HTML {url}: {e}")
    return noticias

if __name__ == "__main__":
    resultado = extrair()
    print(f"Extraídas {len(resultado)} notícias do núcleo duro.")
    if resultado:
        res = requests.post(URL_WEB_APP, json={"noticias": resultado})
        print("Enviado para o Google:", res.status_code)
