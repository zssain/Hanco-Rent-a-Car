"""
Feature engineering for pricing model
Builds feature vectors for ONNX model input
"""
from datetime import date
from typing import Dict
import logging
from google.cloud.firestore_v1 import FieldFilter

from app.services.weather.open_meteo import get_weather_features
# from app.services.competitors.crawler import scrape_all_providers  # Disabled due to dependency conflicts

logger = logging.getLogger(__name__)


async def build_pricing_features(
    vehicle_doc: Dict,
    start_date: date,
    end_date: date,
    city: str,
    firestore_client
) -> Dict[str, float]:
    """
    Build all features required for pricing prediction
    
    Args:
        vehicle_doc: Vehicle document from Firestore
        start_date: Rental start date
        end_date: Rental end date
        city: City name
        firestore_client: Firestore database client
        
    Returns:
        Dictionary of numeric features for ONNX model
    """
    try:
        # 1. Temporal features
        rental_length_days = (end_date - start_date).days
        day_of_week = start_date.weekday()  # 0=Monday, 6=Sunday
        month = start_date.month  # 1-12
        
        # 2. Vehicle features
        base_daily_rate = vehicle_doc.get('base_daily_rate', 100.0)
        category = vehicle_doc.get('category', 'sedan')
        
        # 3. Weather features
        weather = await get_weather_features(city, start_date)
        avg_temp = weather.get('avg_temp', 25.0)
        rain = weather.get('rain', 0.0)
        wind = weather.get('wind', 10.0)
        
        # 4. Competitor pricing features
        avg_competitor_price = await get_avg_competitor_price(
            firestore_client,
            city,
            category
        )
        
        # 5. Demand features
        demand_index = await calculate_demand_index(
            firestore_client,
            city,
            start_date,
            end_date
        )
        
        # 6. Bias term
        bias = 1.0
        
        features = {
            'rental_length_days': float(rental_length_days),
            'day_of_week': float(day_of_week),
            'month': float(month),
            'base_daily_rate': float(base_daily_rate),
            'avg_temp': float(avg_temp),
            'rain': float(rain),
            'wind': float(wind),
            'avg_competitor_price': float(avg_competitor_price),
            'demand_index': float(demand_index),
            'bias': float(bias)
        }
        
        logger.info(f"Built pricing features: {features}")
        
        return features
        
    except Exception as e:
        logger.error(f"Error building features: {str(e)}")
        raise


async def get_avg_competitor_price(
    firestore_client,
    city: str,
    category: str,
    use_realtime: bool = False
) -> float:
    """
    Get average competitor price for same city and category
    
    Args:
        firestore_client: Firestore database
        city: City name
        category: Vehicle category
        use_realtime: If True, scrape live prices instead of using cached data
        
    Returns:
        Average competitor price (or base fallback)
    """
    try:
        prices = []
        
        # Option 1: Real-time scraping (fresh data)
        if use_realtime:
            logger.warning(f"Real-time competitor scraping requested but crawl4ai is disabled")
            # Scraping disabled - fall back to historical data
            # scraped_data = await scrape_all_providers(city, category)
            # [Scraping code removed]
        
        # Option 2: Historical data from Firestore (cached)
        else:
            logger.info(f"Fetching cached competitor prices for {city}/{category}")
            
            # Query competitor_prices collection
            competitor_ref = firestore_client.collection('competitor_prices')
            
            # Filter by city and category
            query = competitor_ref\
                .where(filter=FieldFilter('city', '==', city))\
                .where(filter=FieldFilter('category', '==', category))\
                .limit(20)
            
            docs = query.stream()
            
            # Extract prices
            for doc in docs:
                doc_data = doc.to_dict()
                price = doc_data.get('price', 0)
                if price > 0:
                    prices.append(price)
        
        # Calculate average
        if prices:
            avg_price = sum(prices) / len(prices)
            logger.info(f"Found {len(prices)} competitor prices, avg: {avg_price:.2f} SAR")
            return avg_price
        else:
            # No competitor data, return a reasonable default
            logger.warning(f"No competitor prices for {city}/{category}, using default")
            return 100.0
            
    except Exception as e:
        logger.error(f"Error fetching competitor prices: {str(e)}")
        return 100.0


async def calculate_demand_index(
    firestore_client,
    city: str,
    start_date: date,
    end_date: date
) -> float:
    """
    Calculate demand index based on existing bookings
    
    Args:
        firestore_client: Firestore database
        city: City name
        start_date: Rental start date
        end_date: Rental end date
        
    Returns:
        Demand index (0.0 - 2.0, where 1.0 is normal)
    """
    try:
        # Query bookings in the same city and date range
        bookings_ref = firestore_client.collection('bookings')
        
        # Get all active bookings
        query = bookings_ref.where(
            filter=FieldFilter('status', 'in', ['pending', 'confirmed', 'active'])
        )
        
        docs = query.stream()
        
        # Count overlapping bookings
        overlap_count = 0
        for doc in docs:
            doc_data = doc.to_dict()
            
            # Check if booking overlaps with requested dates
            booking_start = doc_data.get('start_date')
            booking_end = doc_data.get('end_date')
            
            # Convert to date if string
            if isinstance(booking_start, str):
                from datetime import datetime
                booking_start = datetime.fromisoformat(booking_start).date()
            if isinstance(booking_end, str):
                from datetime import datetime
                booking_end = datetime.fromisoformat(booking_end).date()
            
            # Check overlap
            if hasattr(booking_start, 'date'):
                booking_start = booking_start.date()
            if hasattr(booking_end, 'date'):
                booking_end = booking_end.date()
                
            if start_date <= booking_end and end_date >= booking_start:
                overlap_count += 1
        
        # Normalize to 0-2 range (0=no demand, 1=normal, 2=high demand)
        # Assume 5 overlapping bookings = normal demand
        demand_index = min(overlap_count / 5.0, 2.0)
        
        logger.info(f"Demand index for {city}: {demand_index:.2f} ({overlap_count} overlapping bookings)")
        
        return demand_index
        
    except Exception as e:
        logger.error(f"Error calculating demand: {str(e)}")
        return 0.5  # Default to low demand on error
