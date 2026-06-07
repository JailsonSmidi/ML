"""
Scraper do Mercado Livre — coleta anúncios via Playwright com proxy rotativo.

Estratégia:
- Playwright em modo headless (chromium) — renderiza JS como um browser real
- Proxy rotativo configurável via PROXY_URL no .env
- Coleta as primeiras 3 páginas de resultados por busca
- Extrai: título, preço, foto, tipo (catálogo/orgânico), logística (Full/ME),
  tipo de anúncio (classic/premium), tag de vendas, posição, data do anúncio
- Delays aleatórios entre requisições para parecer comportamento humano
- Rejeita anúncios sem preço ou sem título

Limitações conhecidas:
- O ML atualiza o layout periodicamente — os seletores podem precisar de ajuste
- O scraping vai contra os ToS do ML — use com responsabilidade e proxy rotativo
"""

import logging
import random
import asyncio
import re
from datetime import datetime, timezone
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from app.config import settings

logger = logging.getLogger(__name__)

# Seletores do ML (atualizados para o layout de 2025)
# Estes são os seletores mais estáveis — preferem atributos data-* a classes CSS
SELECTORS = {
    "results_container": "[data-testid='gallery-result'], .ui-search-results",
    "item": ".ui-search-result__wrapper, [data-testid='result']",
    "title": ".poly-component__title, .ui-search-item__title",
    "price": ".andes-money-amount__fraction",
    "price_cents": ".andes-money-amount__cents",
    "thumbnail": ".poly-card__portada img, .ui-search-result-image__element",
    "sales_tag": ".poly-component__sold, .ui-search-item__group--label",
    "listing_date": "[class*='date'], [class*='ago']",
    "full_badge": "[class*='full'], [aria-label*='Full'], [title*='Full']",
    "catalog_indicator": "[class*='catalog'], [data-testid*='catalog']",
    "total_results": ".ui-search-search-result__quantity-results",
    "ad_type_premium": "[class*='gold_pro'], [class*='gold-pro'], [class*='premium']",
}

ML_BASE_URL = "https://www.mercadolivre.com.br"
PAGES_TO_SCRAPE = 3
MIN_DELAY_MS = 1500
MAX_DELAY_MS = 3500


async def scrape_listings(
    search_term: str,
    proxy_url: str | None = None,
) -> list[dict]:
    """
    Coleta anúncios do ML para o termo de busca informado.
    Retorna lista de dicts com os dados brutos de cada anúncio.
    """
    proxy_url = proxy_url or settings.proxy_url
    logger.info(f"Scraping: '{search_term}' | proxy: {'sim' if proxy_url else 'não'}")

    async with async_playwright() as pw:
        browser = await _launch_browser(pw, proxy_url)
        context = await _create_context(browser)

        try:
            all_listings = []
            for page_num in range(1, PAGES_TO_SCRAPE + 1):
                url = _build_search_url(search_term, page_num)
                listings = await _scrape_page(context, url, page_num)
                all_listings.extend(listings)

                if not listings:
                    logger.info(f"Página {page_num} vazia — parando")
                    break

                # Delay entre páginas para simular comportamento humano
                if page_num < PAGES_TO_SCRAPE:
                    delay = random.randint(MIN_DELAY_MS, MAX_DELAY_MS)
                    await asyncio.sleep(delay / 1000)

            logger.info(f"Scraping concluído: {len(all_listings)} anúncios coletados")
            return all_listings

        finally:
            await browser.close()


async def fetch_search_results_count(search_term: str) -> dict:
    """
    Busca preliminar para validação de termos.
    Retorna total de resultados e amostra de títulos.
    Mais leve que o scraping completo — só carrega a primeira página.
    """
    proxy_url = settings.proxy_url
    async with async_playwright() as pw:
        browser = await _launch_browser(pw, proxy_url)
        context = await _create_context(browser)
        try:
            page = await context.new_page()
            url = _build_search_url(search_term, 1)

            await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            await _random_delay(page)

            # Total de resultados
            total = 0
            try:
                qty_el = await page.query_selector(SELECTORS["total_results"])
                if qty_el:
                    qty_text = await qty_el.inner_text()
                    numbers = re.findall(r"[\d.]+", qty_text.replace(".", ""))
                    if numbers:
                        total = int(numbers[0])
            except Exception:
                pass

            # Amostra de títulos (primeiros 15)
            titles = []
            try:
                title_els = await page.query_selector_all(SELECTORS["title"])
                for el in title_els[:15]:
                    text = await el.inner_text()
                    if text.strip():
                        titles.append(text.strip())
            except Exception:
                pass

            await page.close()
            return {"total_results": total, "sample_titles": titles}

        finally:
            await browser.close()


async def _launch_browser(pw, proxy_url: str | None) -> Browser:
    launch_args = {
        "headless": True,
        "args": [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-blink-features=AutomationControlled",
        ],
    }
    if proxy_url:
        # Formato: http://user:pass@host:port
        launch_args["proxy"] = {"server": proxy_url}

    return await pw.chromium.launch(**launch_args)


async def _create_context(browser: Browser) -> BrowserContext:
    return await browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1366, "height": 768},
        locale="pt-BR",
        timezone_id="America/Sao_Paulo",
        extra_http_headers={
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )


def _build_search_url(term: str, page: int) -> str:
    from urllib.parse import quote_plus
    encoded = quote_plus(term)
    if page == 1:
        return f"{ML_BASE_URL}/search?q={encoded}&item_id=MLB#D[A:{encoded}]"
    offset = (page - 1) * 50
    return f"{ML_BASE_URL}/search?q={encoded}&item_id=MLB_Desde_{offset + 1}#D[A:{encoded}]"


async def _scrape_page(context: BrowserContext, url: str, page_num: int) -> list[dict]:
    page = await context.new_page()
    listings = []

    try:
        logger.debug(f"Carregando página {page_num}: {url}")
        await page.goto(url, wait_until="networkidle", timeout=45_000)
        await _random_delay(page)

        # Scroll para carregar lazy-loaded items
        await _scroll_page(page)

        items = await page.query_selector_all(SELECTORS["item"])
        logger.debug(f"Página {page_num}: {len(items)} items encontrados")

        for position, item in enumerate(items, start=(page_num - 1) * 50 + 1):
            try:
                listing = await _extract_listing(item, position)
                if listing:
                    listings.append(listing)
            except Exception as exc:
                logger.debug(f"Erro ao extrair item na posição {position}: {exc}")
                continue

    except Exception as exc:
        logger.error(f"Erro ao carregar página {page_num}: {exc}")

    finally:
        await page.close()

    return listings


async def _extract_listing(item, position: int) -> dict | None:
    """Extrai dados de um item da página de resultados."""
    try:
        # Título
        title_el = await item.query_selector(SELECTORS["title"])
        if not title_el:
            return None
        title = (await title_el.inner_text()).strip()
        if not title:
            return None

        # Preço
        price_el = await item.query_selector(SELECTORS["price"])
        if not price_el:
            return None
        price_text = (await price_el.inner_text()).strip().replace(".", "").replace(",", ".")
        try:
            price = float(re.sub(r"[^\d.]", "", price_text))
        except ValueError:
            return None

        # Centavos (opcional)
        cents_el = await item.query_selector(SELECTORS["price_cents"])
        if cents_el:
            cents_text = (await cents_el.inner_text()).strip()
            try:
                price += float(cents_text) / 100
            except ValueError:
                pass

        # ML Item ID (da URL do anúncio)
        ml_item_id = ""
        try:
            link_el = await item.query_selector("a[href*='MLB']")
            if link_el:
                href = await link_el.get_attribute("href")
                match = re.search(r"MLB-?(\d+)", href or "")
                if match:
                    ml_item_id = f"MLB{match.group(1)}"
        except Exception:
            pass

        if not ml_item_id:
            return None  # Sem ID não tem como referenciar o anúncio

        # Thumbnail
        thumbnail_url = None
        try:
            img_el = await item.query_selector(SELECTORS["thumbnail"])
            if img_el:
                thumbnail_url = (
                    await img_el.get_attribute("data-src")
                    or await img_el.get_attribute("src")
                )
        except Exception:
            pass

        # Logística (Full ou Mercado Envios)
        logistics = "mercado_envios"
        try:
            full_badge = await item.query_selector(SELECTORS["full_badge"])
            if full_badge:
                logistics = "full"
        except Exception:
            pass

        # Tipo de anúncio (Premium = gold_pro, Classic = demais)
        ad_type = "classic"
        try:
            premium_el = await item.query_selector(SELECTORS["ad_type_premium"])
            if premium_el:
                ad_type = "premium"
        except Exception:
            pass

        # Catálogo vs orgânico
        listing_type = "organic"
        try:
            catalog_el = await item.query_selector(SELECTORS["catalog_indicator"])
            if catalog_el:
                listing_type = "catalog"
            # ML também sinaliza catálogo pela estrutura da URL
            if "p/MLB" in ml_item_id or "/p/" in (await item.inner_html()):
                listing_type = "catalog"
        except Exception:
            pass

        # Tag de vendas ("+500 vendidos", "+1000 vendidos", etc.)
        sales_tag = None
        try:
            sales_el = await item.query_selector(SELECTORS["sales_tag"])
            if sales_el:
                sales_text = await sales_el.inner_text()
                match = re.search(r"\+?([\d.]+)\s*mil", sales_text, re.IGNORECASE)
                if match:
                    sales_tag = int(float(match.group(1).replace(".", "")) * 1000)
                else:
                    match = re.search(r"\+?([\d.]+)", sales_text)
                    if match:
                        sales_tag = int(match.group(1).replace(".", ""))
        except Exception:
            pass

        # Dias no ar — estimativa via texto relativo ("há 2 meses", "há 1 ano")
        listing_age_days = None
        try:
            date_el = await item.query_selector(SELECTORS["listing_date"])
            if date_el:
                date_text = await date_el.inner_text()
                listing_age_days = _parse_relative_date(date_text)
        except Exception:
            pass

        return {
            "ml_item_id": ml_item_id,
            "title": title,
            "price": round(price, 2),
            "thumbnail_url": thumbnail_url,
            "listing_type": listing_type,
            "logistics": logistics,
            "ad_type": ad_type,
            "sales_tag": sales_tag,
            "listing_age_days": listing_age_days,
            "search_position": position,
        }

    except Exception as exc:
        logger.debug(f"Erro ao extrair listing: {exc}")
        return None


def _parse_relative_date(text: str) -> int | None:
    """
    Converte texto de data relativa do ML para dias.
    Exemplos: "há 2 meses", "há 1 ano", "há 3 semanas"
    """
    text = text.lower()
    try:
        if "ano" in text:
            match = re.search(r"(\d+)\s*ano", text)
            return int(match.group(1)) * 365 if match else None
        if "mes" in text or "mês" in text:
            match = re.search(r"(\d+)\s*m", text)
            return int(match.group(1)) * 30 if match else None
        if "semana" in text:
            match = re.search(r"(\d+)\s*semana", text)
            return int(match.group(1)) * 7 if match else None
        if "dia" in text:
            match = re.search(r"(\d+)\s*dia", text)
            return int(match.group(1)) if match else None
    except Exception:
        pass
    return None


async def _scroll_page(page: Page):
    """Scroll gradual para forçar carregamento de itens lazy."""
    try:
        for step in range(3):
            await page.evaluate(f"window.scrollTo(0, {(step + 1) * 800})")
            await asyncio.sleep(0.4)
        await page.evaluate("window.scrollTo(0, 0)")
    except Exception:
        pass


async def _random_delay(page: Page):
    """Delay humano entre ações."""
    delay = random.randint(MIN_DELAY_MS, MAX_DELAY_MS)
    await asyncio.sleep(delay / 1000)
