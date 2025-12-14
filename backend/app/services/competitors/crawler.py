"""
Production-Grade Competitor Price Scraping Engine
Uses Crawl4AI for headless browser scraping with provider-specific parsers
"""
import logging
import re
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from google.cloud import firestore

from app.core.firebase import db

logger = logging.getLogger(__name__)


# ==================== PROVIDER CONFIGURATION ====================
# Production URLs for Saudi Arabia car rental providers

PROVIDER_URLS = {
    "key": "https://www.key.sa/en/rent-a-car",
    "budget": "https://www.budgetsaudi.com",
    "yelo": "https://www.iyelo.com",
    "lumi": "https://www.lumi.com.sa"
}

# City name mappings for URL construction
CITY_SLUGS = {
    "riyadh": "riyadh",
    "jeddah": "jeddah",
    "dammam": "dammam",
    "mecca": "makkah",
    "medina": "madinah",
    "taif": "taif",
}

# Vehicle category mappings for normalization
CATEGORY_MAPPING = {
    "economy": ["economy", "compact", "small", "mini"],
    "sedan": ["sedan", "midsize", "standard", "medium"],
    "suv": ["suv", "4x4", "crossover", "jeep"],
    "luxury": ["luxury", "premium", "executive", "vip"],
}

# HTML cache to avoid rapid re-scraping (5 min TTL)
_html_cache: Dict[str, Dict[str, Any]] = {}


# ==================== CORE CRAWL4AI FUNCTIONS ====================

async def fetch_html(url: str, use_cache: bool = True) -> str:
    """
    Fetch rendered HTML using Crawl4AI headless browser.
    
    Args:
        url: Target URL to scrape
        use_cache: Whether to use 5-minute cache
        
    Returns:
        Rendered HTML content
        
    Raises:
        Exception: If crawling fails
    """
    # Check cache first
    if use_cache and url in _html_cache:
        cached = _html_cache[url]
        age = (datetime.utcnow() - cached['timestamp']).total_seconds()
        if age < 300:  # 5 minutes
            logger.info(f"Using cached HTML for {url} (age: {age:.0f}s)")
            return cached['html']
    
    try:
        logger.info(f"Fetching HTML from: {url}")
        
        # Configure browser for production scraping
        browser_config = BrowserConfig(
            headless=True,
            verbose=False,
            extra_args=["--disable-gpu", "--no-sandbox"]
        )
        
        # Configure crawler
        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            page_timeout=30000,  # 30 seconds
            wait_for="body",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
            }
        )
        
        # Fetch with Crawl4AI
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=url, config=crawler_config)
            
            if not result.success:
                raise Exception(f"Crawl failed: {result.error_message}")
            
            html = result.html
            
            # Cache the result
            if use_cache:
                _html_cache[url] = {
                    'html': html,
                    'timestamp': datetime.utcnow()
                }
            
            logger.info(f"Successfully fetched {len(html)} bytes from {url}")
            return html
            
    except Exception as e:
        logger.error(f"Error fetching {url}: {str(e)}")
        
        # Log failure to Firestore
        try:
            db.collection('scrape_failures').add({
                'url': url,
                'error': str(e),
                'timestamp': firestore.SERVER_TIMESTAMP
            })
        except:
            pass
        
        raise


def _extract_price(price_text: str) -> float:
    """
    Extract numeric price from text.
    
    Args:
        price_text: Text containing price (e.g., "SAR 150/day", "150 SR")
        
    Returns:
        Numeric price value
    """
    if not price_text:
        return 0.0
    
    # Remove common currency symbols and text
    cleaned = re.sub(r'[^\d.,]', '', price_text)
    cleaned = cleaned.replace(',', '')
    
    try:
        return float(cleaned)
    except:
        return 0.0


def _normalize_category(category_text: str) -> str:
    """
    Normalize category name to standard values.
    
    Args:
        category_text: Raw category text from website
        
    Returns:
        Normalized category: economy, sedan, suv, or luxury
    """
    if not category_text:
        return "sedan"
    
    text_lower = category_text.lower()
    
    for standard, variants in CATEGORY_MAPPING.items():
        if any(variant in text_lower for variant in variants):
            return standard
    
    return "sedan"  # Default


# ==================== PROVIDER-SPECIFIC PARSERS ====================

def _parse_key_sa(html: str, city: str) -> List[Dict]:
    """
    Parse KEY.SA rental car listings.
    
    HTML Structure:
        - Vehicle cards: .car-box
        - Name: .car-name
        - Category: inferred from labels/description
        - Price: .car-price
    """
    offers = []
    
    try:
        soup = BeautifulSoup(html, 'lxml')
        
        # Find all car boxes
        car_boxes = soup.find_all(class_='car-box')
        if not car_boxes:
            # Try alternative selectors
            car_boxes = soup.find_all('div', {'class': re.compile(r'vehicle|car|product')})
        
        logger.info(f"KEY.SA: Found {len(car_boxes)} vehicle cards")
        
        for box in car_boxes:
            try:
                # Extract vehicle name
                name_elem = box.find(class_='car-name') or box.find(class_='vehicle-name')
                vehicle_name = name_elem.get_text(strip=True) if name_elem else "Unknown"
                
                # Extract category
                category_elem = box.find(class_='car-type') or box.find(class_='category')
                category_text = category_elem.get_text(strip=True) if category_elem else vehicle_name
                category = _normalize_category(category_text)
                
                # Extract price
                price_elem = box.find(class_='car-price') or box.find(class_='price')
                price_text = price_elem.get_text(strip=True) if price_elem else "0"
                price = _extract_price(price_text)
                
                if price > 0:
                    offers.append({
                        "provider": "key",
                        "city": city,
                        "category": category,
                        "vehicle_name": vehicle_name,
                        "price": price,
                        "currency": "SAR",
                        "scraped_at": datetime.utcnow(),
                        "url": PROVIDER_URLS["key"]
                    })
                    
            except Exception as e:
                logger.warning(f"KEY.SA: Error parsing car box: {e}")
                continue
        
    except Exception as e:
        logger.error(f"KEY.SA: Parser error: {e}")
    
    return offers


def _parse_budget_saudi(html: str, city: str) -> List[Dict]:
    """
    Parse BudgetSaudi.com rental car listings.
    
    HTML Structure:
        - Vehicle cards: .vehicle-item
        - Name: .vehicle-name
        - Category: .vehicle-type
        - Price: .rate
    """
    offers = []
    
    try:
        soup = BeautifulSoup(html, 'lxml')
        
        # Find all vehicle items
        vehicle_items = soup.find_all(class_='vehicle-item')
        if not vehicle_items:
            vehicle_items = soup.find_all('div', {'class': re.compile(r'vehicle|car-card')})
        
        logger.info(f"BudgetSaudi: Found {len(vehicle_items)} vehicle cards")
        
        for item in vehicle_items:
            try:
                # Extract vehicle name
                name_elem = item.find(class_='vehicle-name') or item.find('h3') or item.find('h4')
                vehicle_name = name_elem.get_text(strip=True) if name_elem else "Unknown"
                
                # Extract category
                type_elem = item.find(class_='vehicle-type') or item.find(class_='category')
                category_text = type_elem.get_text(strip=True) if type_elem else vehicle_name
                category = _normalize_category(category_text)
                
                # Extract price
                rate_elem = item.find(class_='rate') or item.find(class_='price')
                price_text = rate_elem.get_text(strip=True) if rate_elem else "0"
                price = _extract_price(price_text)
                
                if price > 0:
                    offers.append({
                        "provider": "budget",
                        "city": city,
                        "category": category,
                        "vehicle_name": vehicle_name,
                        "price": price,
                        "currency": "SAR",
                        "scraped_at": datetime.utcnow(),
                        "url": PROVIDER_URLS["budget"]
                    })
                    
            except Exception as e:
                logger.warning(f"BudgetSaudi: Error parsing vehicle item: {e}")
                continue
        
    except Exception as e:
        logger.error(f"BudgetSaudi: Parser error: {e}")
    
    return offers


def _parse_iyelo(html: str, city: str) -> List[Dict]:
    """
    Parse iYelo.com rental car listings.
    
    HTML Structure:
        - Product cards: .product-card
        - Name: .product-card-title
        - Category: text inside "Category:" field
        - Price: .product-card-price
    """
    offers = []
    
    try:
        soup = BeautifulSoup(html, 'lxml')
        
        # Find all product cards
        product_cards = soup.find_all(class_='product-card')
        if not product_cards:
            product_cards = soup.find_all('div', {'class': re.compile(r'product|vehicle|car')})
        
        logger.info(f"iYelo: Found {len(product_cards)} product cards")
        
        for card in product_cards:
            try:
                # Extract vehicle name
                title_elem = card.find(class_='product-card-title') or card.find('h3')
                vehicle_name = title_elem.get_text(strip=True) if title_elem else "Unknown"
                
                # Extract category (look for "Category:" label)
                category_text = vehicle_name
                category_label = card.find(string=re.compile(r'Category:', re.I))
                if category_label and category_label.parent:
                    category_text = category_label.parent.get_text(strip=True)
                
                category = _normalize_category(category_text)
                
                # Extract price
                price_elem = card.find(class_='product-card-price') or card.find(class_='price')
                price_text = price_elem.get_text(strip=True) if price_elem else "0"
                price = _extract_price(price_text)
                
                if price > 0:
                    offers.append({
                        "provider": "yelo",
                        "city": city,
                        "category": category,
                        "vehicle_name": vehicle_name,
                        "price": price,
                        "currency": "SAR",
                        "scraped_at": datetime.utcnow(),
                        "url": PROVIDER_URLS["yelo"]
                    })
                    
            except Exception as e:
                logger.warning(f"iYelo: Error parsing product card: {e}")
                continue
        
    except Exception as e:
        logger.error(f"iYelo: Parser error: {e}")
    
    return offers


def _parse_lumi(html: str, city: str) -> List[Dict]:
    """
    Parse Lumi.com.sa rental car listings.
    
    HTML Structure:
        - Vehicle cards: .v-card
        - Name: .v-title
        - Category: .v-category
        - Price: .v-rate
    """
    offers = []
    
    try:
        soup = BeautifulSoup(html, 'lxml')
        
        # Find all v-cards
        v_cards = soup.find_all(class_='v-card')
        if not v_cards:
            v_cards = soup.find_all('div', {'class': re.compile(r'card|vehicle|car')})
        
        logger.info(f"Lumi: Found {len(v_cards)} vehicle cards")
        
        for card in v_cards:
            try:
                # Extract vehicle name
                title_elem = card.find(class_='v-title') or card.find('h3') or card.find('h4')
                vehicle_name = title_elem.get_text(strip=True) if title_elem else "Unknown"
                
                # Extract category
                category_elem = card.find(class_='v-category') or card.find(class_='category')
                category_text = category_elem.get_text(strip=True) if category_elem else vehicle_name
                category = _normalize_category(category_text)
                
                # Extract price
                rate_elem = card.find(class_='v-rate') or card.find(class_='price')
                price_text = rate_elem.get_text(strip=True) if rate_elem else "0"
                price = _extract_price(price_text)
                
                if price > 0:
                    offers.append({
                        "provider": "lumi",
                        "city": city,
                        "category": category,
                        "vehicle_name": vehicle_name,
                        "price": price,
                        "currency": "SAR",
                        "scraped_at": datetime.utcnow(),
                        "url": PROVIDER_URLS["lumi"]
                    })
                    
            except Exception as e:
                logger.warning(f"Lumi: Error parsing v-card: {e}")
                continue
        
    except Exception as e:
        logger.error(f"Lumi: Parser error: {e}")
    
    return offers


def _extract_offers_from_html(provider: str, city: str, html: str) -> List[Dict]:
    """
    Extract offers from HTML using provider-specific parsers.
    
    Args:
        provider: Provider key (key, budget, yelo, lumi)
        city: City name
        html: Rendered HTML content
        
    Returns:
        List of normalized offer dictionaries
    """
    if provider == "key":
        return _parse_key_sa(html, city)
    elif provider == "budget":
        return _parse_budget_saudi(html, city)
    elif provider == "yelo":
        return _parse_iyelo(html, city)
    elif provider == "lumi":
        return _parse_lumi(html, city)
    else:
        logger.error(f"Unknown provider: {provider}")
        return []


# ==================== MAIN SCRAPING FUNCTIONS ====================

async def scrape_provider(provider: str, city: str, category: Optional[str] = None) -> List[Dict]:
    """
    Scrape a single provider for a specific city and optional category.
    
    Args:
        provider: Provider key (key, budget, yelo, lumi)
        city: City name
        category: Optional category filter (not used in URL but for filtering results)
        
    Returns:
        List of offer dictionaries
    """
    if provider not in PROVIDER_URLS:
        logger.error(f"Unknown provider: {provider}")
        return []
    
    try:
        # Fetch HTML
        url = PROVIDER_URLS[provider]
        html = await fetch_html(url)
        
        # Extract offers
        offers = _extract_offers_from_html(provider, city, html)
        
        # Filter by category if specified
        if category:
            offers = [o for o in offers if o['category'] == category]
        
        # Save to Firestore
        if offers:
            competitor_ref = db.collection('competitor_prices')
            batch = db.batch()
            
            for offer in offers:
                offer['created_at'] = firestore.SERVER_TIMESTAMP
                offer['updated_at'] = firestore.SERVER_TIMESTAMP
                doc_ref = competitor_ref.document()
                batch.set(doc_ref, offer)
            
            batch.commit()
            logger.info(f"Saved {len(offers)} offers from {provider} to Firestore")
        
        return offers
        
    except Exception as e:
        logger.error(f"Error scraping {provider}: {str(e)}")
        return []


async def scrape_all_providers(city: str, category: Optional[str] = None) -> Dict[str, List[Dict]]:
    """
    Scrape all providers in parallel for a specific city.
    
    This is the main entry point for competitor price scraping.
    Used by the pricing engine to get real-time competitor data.
    
    Args:
        city: City name (riyadh, jeddah, etc.)
        category: Optional category filter (economy, sedan, suv, luxury)
        
    Returns:
        Dictionary mapping provider names to lists of offers:
        {
            "key": [...],
            "budget": [...],
            "yelo": [...],
            "lumi": [...]
        }
    """
    logger.info(f"Scraping all providers for city={city}, category={category}")
    
    # Create tasks for parallel scraping
    tasks = {
        provider: scrape_provider(provider, city, category)
        for provider in PROVIDER_URLS.keys()
    }
    
    # Execute all tasks in parallel
    results = await asyncio.gather(*tasks.values(), return_exceptions=True)
    
    # Map results back to providers
    scraped_data = {}
    for provider, result in zip(tasks.keys(), results):
        if isinstance(result, Exception):
            logger.error(f"Failed to scrape {provider}: {result}")
            scraped_data[provider] = []
        else:
            scraped_data[provider] = result
    
    total_offers = sum(len(offers) for offers in scraped_data.values())
    logger.info(f"Scraped {total_offers} total offers from {len(scraped_data)} providers")
    
    return scraped_data


# ==================== LEGACY SUPPORT FUNCTIONS ====================
# These maintain backward compatibility with existing API

async def fetch_offers_for_provider(provider: str, city: str, crawler_config: Optional[CrawlerRunConfig] = None) -> List[Dict]:
    """
    Legacy function for backward compatibility.
    Use scrape_provider() instead.
    """
    return await scrape_provider(provider, city)


async def refresh_competitor_prices(
    cities: List[str],
    firestore_client,
    providers: Optional[List[str]] = None
) -> Dict[str, any]:
    """
    Refresh competitor prices for multiple cities and providers.
    
    Args:
        cities: List of city names to scrape
        firestore_client: Firestore database client (ignored, uses global db)
        providers: Optional list of providers (defaults to all)
        
    Returns:
        Summary dictionary with:
            - total_offers: int
            - offers_by_provider: dict
            - cities_scraped: list
            - errors: list
    """
    if providers is None:
        providers = list(PROVIDER_URLS.keys())
    
    summary = {
        "total_offers": 0,
        "offers_by_provider": {},
        "cities_scraped": cities,
        "errors": [],
        "started_at": datetime.utcnow(),
    }
    
    try:
        # Scrape each provider x city combination
        tasks = []
        for provider in providers:
            for city in cities:
                tasks.append(scrape_provider(provider, city))
        
        # Run with rate limiting (batch of 3)
        batch_size = 3
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i+batch_size]
            results = await asyncio.gather(*batch, return_exceptions=True)
            
            for j, result in enumerate(results):
                if isinstance(result, Exception):
                    summary["errors"].append(str(result))
                else:
                    provider = providers[(i + j) // len(cities)]
                    summary["total_offers"] += len(result)
                    summary["offers_by_provider"][provider] = summary["offers_by_provider"].get(provider, 0) + len(result)
            
            # Delay between batches
            if i + batch_size < len(tasks):
                await asyncio.sleep(2)
        
        summary["completed_at"] = datetime.utcnow()
        summary["duration_seconds"] = (summary["completed_at"] - summary["started_at"]).total_seconds()
        
        logger.info(f"Competitor refresh complete: {summary['total_offers']} offers in {summary['duration_seconds']:.1f}s")
        
    except Exception as e:
        logger.error(f"Error in refresh_competitor_prices: {str(e)}")
        summary["errors"].append(str(e))
    
    return summary


def get_supported_cities() -> List[str]:
    """Get list of supported cities for scraping."""
    return list(CITY_SLUGS.keys())


def get_supported_providers() -> List[str]:
    """Get list of supported providers."""
    return list(PROVIDER_URLS.keys())


async def cleanup_old_prices(firestore_client, days_old: int = 7) -> int:
    """
    Delete competitor prices older than specified days.
    
    Args:
        firestore_client: Firestore database client (ignored, uses global db)
        days_old: Delete prices older than this many days
        
    Returns:
        Number of documents deleted
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        competitor_ref = db.collection('competitor_prices')
        old_docs = competitor_ref.where('scraped_at', '<', cutoff_date).stream()
        
        batch = db.batch()
        count = 0
        
        for doc in old_docs:
            batch.delete(doc.reference)
            count += 1
            
            if count % 500 == 0:
                batch.commit()
                batch = db.batch()
        
        if count % 500 != 0:
            batch.commit()
        
        logger.info(f"Deleted {count} old competitor prices (>{days_old} days)")
        return count
        
    except Exception as e:
        logger.error(f"Error cleaning up old prices: {str(e)}")
        return 0


# ==================== ML TRAINING INTEGRATION ====================

def export_competitor_data_for_training(target_csv_path: str) -> int:
    """
    Export all competitor_prices from Firestore to CSV for ML training.
    
    This allows retraining the pricing model with historical competitor data.
    
    Args:
        target_csv_path: Path to save CSV file
        
    Returns:
        Number of records exported
    """
    import csv
    
    try:
        logger.info(f"Exporting competitor data to {target_csv_path}")
        
        # Query all competitor prices
        competitor_ref = db.collection('competitor_prices')
        docs = competitor_ref.stream()
        
        # Prepare CSV
        fieldnames = ['provider', 'city', 'category', 'vehicle_name', 'price', 'currency', 'scraped_at']
        
        with open(target_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            count = 0
            for doc in docs:
                data = doc.to_dict()
                
                # Write row
                writer.writerow({
                    'provider': data.get('provider', ''),
                    'city': data.get('city', ''),
                    'category': data.get('category', ''),
                    'vehicle_name': data.get('vehicle_name', ''),
                    'price': data.get('price', 0.0),
                    'currency': data.get('currency', 'SAR'),
                    'scraped_at': data.get('scraped_at', '')
                })
                count += 1
        
        logger.info(f"Exported {count} competitor price records to {target_csv_path}")
        return count
        
    except Exception as e:
        logger.error(f"Error exporting competitor data: {str(e)}")
        return 0

