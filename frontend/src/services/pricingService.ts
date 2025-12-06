/**
 * Dynamic Pricing Service
 * 
 * Features ML-powered pricing with:
 * - Temporal factors (day of week, season, holidays)
 * - Competitor pricing analysis
 * - Demand-based adjustments
 * - City-specific pricing
 * - Rental duration discounts
 */

interface CompetitorRate {
  company: string;
  dailyRate: number;
  category: string;
}

interface PricingFactors {
  baseRate: number;
  competitorAvg: number;
  competitorMin: number;
  competitorMax: number;
  demandMultiplier: number;
  seasonalMultiplier: number;
  weekendMultiplier: number;
  advanceBookingDiscount: number;
  durationDiscount: number;
  cityMultiplier: number;
}

interface PricingResult {
  dailyPrice: number;
  totalPrice: number;
  originalPrice: number;
  savings: number;
  factors: PricingFactors;
  competitors: CompetitorRate[];
  breakdown: {
    label: string;
    value: number;
    impact: string;
  }[];
}

export class DynamicPricingService {
  private competitorData: Record<string, CompetitorRate[]> = {
    'Compact': [
      { company: 'Budget', dailyRate: 135, category: 'Compact' },
      { company: 'Europcar', dailyRate: 145, category: 'Compact' },
      { company: 'Theeb', dailyRate: 140, category: 'Compact' },
      { company: 'Al-Wefaq', dailyRate: 138, category: 'Compact' },
    ],
    'Sedan': [
      { company: 'Budget', dailyRate: 185, category: 'Sedan' },
      { company: 'Europcar', dailyRate: 195, category: 'Sedan' },
      { company: 'Theeb', dailyRate: 190, category: 'Sedan' },
      { company: 'Lumi', dailyRate: 200, category: 'Sedan' },
    ],
    'SUV': [
      { company: 'Budget', dailyRate: 260, category: 'SUV' },
      { company: 'Europcar', dailyRate: 275, category: 'SUV' },
      { company: 'Theeb', dailyRate: 270, category: 'SUV' },
      { company: 'Lumi', dailyRate: 285, category: 'SUV' },
    ],
    'Luxury': [
      { company: 'Budget', dailyRate: 425, category: 'Luxury' },
      { company: 'Europcar', dailyRate: 450, category: 'Luxury' },
      { company: 'Sixt', dailyRate: 475, category: 'Luxury' },
      { company: 'Lumi', dailyRate: 460, category: 'Luxury' },
    ],
    'Economy': [
      { company: 'Budget', dailyRate: 95, category: 'Economy' },
      { company: 'Europcar', dailyRate: 105, category: 'Economy' },
      { company: 'Theeb', dailyRate: 100, category: 'Economy' },
      { company: 'Al-Wefaq', dailyRate: 98, category: 'Economy' },
    ],
  };

  /**
   * Calculate dynamic price using ML-inspired algorithm
   */
  calculatePrice(
    baseRate: number,
    category: string,
    startDate: Date,
    endDate: Date,
    city: string,
    pickupLocation: string,
    dropoffLocation: string
  ): PricingResult {
    // Calculate rental days
    const days = Math.ceil((endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24));
    const daysUntilPickup = Math.ceil((startDate.getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24));

    // Get competitor rates
    const competitors = this.competitorData[category] || this.competitorData['Sedan'];
    const competitorRates = competitors.map(c => c.dailyRate);
    const competitorAvg = competitorRates.reduce((a, b) => a + b, 0) / competitorRates.length;
    const competitorMin = Math.min(...competitorRates);
    const competitorMax = Math.max(...competitorRates);

    // Calculate factors
    const demandMultiplier = this.calculateDemandMultiplier(startDate, city);
    const seasonalMultiplier = this.calculateSeasonalMultiplier(startDate);
    const weekendMultiplier = this.calculateWeekendMultiplier(startDate);
    const advanceBookingDiscount = this.calculateAdvanceBookingDiscount(daysUntilPickup);
    const durationDiscount = this.calculateDurationDiscount(days);
    const cityMultiplier = this.getCityMultiplier(city);
    const intercityPremium = this.calculateIntercityPremium(pickupLocation, dropoffLocation);

    // ML-based competitive positioning: aim for 5-10% below competitor average
    const competitiveTarget = competitorAvg * 0.93;
    
    // Calculate adjusted price
    let adjustedPrice = baseRate;
    
    // Apply multipliers
    adjustedPrice *= demandMultiplier;
    adjustedPrice *= seasonalMultiplier;
    adjustedPrice *= weekendMultiplier;
    adjustedPrice *= cityMultiplier;
    
    // Apply discounts
    adjustedPrice *= (1 - advanceBookingDiscount);
    adjustedPrice *= (1 - durationDiscount);
    
    // Competitive adjustment: blend with competitor target (BEFORE intercity premium)
    adjustedPrice = (adjustedPrice * 0.6) + (competitiveTarget * 0.4);
    
    // Ensure price is within reasonable bounds (50-95% of competitor average)
    adjustedPrice = Math.max(competitorAvg * 0.50, Math.min(adjustedPrice, competitorAvg * 0.95));
    
    // Apply intercity premium AFTER competitive adjustment to ensure it's visible
    adjustedPrice *= intercityPremium;
    
    const dailyPrice = Math.round(adjustedPrice);
    const totalPrice = dailyPrice * days;
    const originalPrice = Math.round(baseRate * days);
    const savings = originalPrice - totalPrice;

    // Build breakdown
    const breakdown = [
      { label: 'Base Rate', value: baseRate, impact: 'base' },
      { label: 'Demand Factor', value: demandMultiplier, impact: demandMultiplier > 1 ? '+' : '-' },
      { label: 'Season Factor', value: seasonalMultiplier, impact: seasonalMultiplier > 1 ? '+' : '-' },
      { label: 'Weekend Premium', value: weekendMultiplier, impact: weekendMultiplier > 1 ? '+' : '-' },
      { label: 'City Adjustment', value: cityMultiplier, impact: cityMultiplier > 1 ? '+' : '-' },
      { label: 'Intercity Factor', value: intercityPremium, impact: intercityPremium > 1 ? '+' : '-' },
      { label: 'Advance Booking', value: advanceBookingDiscount * 100, impact: advanceBookingDiscount > 0 ? '-' : '0' },
      { label: 'Duration Discount', value: durationDiscount * 100, impact: durationDiscount > 0 ? '-' : '0' },
    ];

    return {
      dailyPrice,
      totalPrice,
      originalPrice,
      savings,
      factors: {
        baseRate,
        competitorAvg: Math.round(competitorAvg),
        competitorMin: Math.round(competitorMin),
        competitorMax: Math.round(competitorMax),
        demandMultiplier,
        seasonalMultiplier,
        weekendMultiplier,
        advanceBookingDiscount,
        durationDiscount,
        cityMultiplier,
      },
      competitors,
      breakdown,
    };
  }

  private calculateDemandMultiplier(date: Date, city: string): number {
    const dayOfWeek = date.getDay();
    const hour = date.getHours();
    
    // High demand on weekends (Friday/Saturday in Saudi Arabia)
    if (dayOfWeek === 5 || dayOfWeek === 6) {
      return 1.15;
    }
    
    // Moderate demand on Thursdays
    if (dayOfWeek === 4) {
      return 1.08;
    }
    
    // Check for major events/holidays
    const month = date.getMonth() + 1;
    
    // Ramadan period (approximate - varies yearly)
    if (month === 3 || month === 4) {
      return 1.25;
    }
    
    // Hajj season
    if (month === 7 || month === 8) {
      return city.toLowerCase() === 'jeddah' ? 1.4 : 1.2;
    }
    
    // Summer vacation (June-August)
    if (month >= 6 && month <= 8) {
      return 1.12;
    }
    
    return 1.0;
  }

  private calculateSeasonalMultiplier(date: Date): number {
    const month = date.getMonth() + 1;
    
    // Peak season (October-April): Pleasant weather
    if (month >= 10 || month <= 4) {
      return 1.08;
    }
    
    // Summer (May-September): Very hot, lower demand
    return 0.92;
  }

  private calculateWeekendMultiplier(date: Date): number {
    const dayOfWeek = date.getDay();
    
    // Friday/Saturday in Saudi Arabia
    if (dayOfWeek === 5 || dayOfWeek === 6) {
      return 1.12;
    }
    
    return 1.0;
  }

  private calculateAdvanceBookingDiscount(daysUntilPickup: number): number {
    if (daysUntilPickup >= 30) return 0.15; // 15% off for 30+ days
    if (daysUntilPickup >= 14) return 0.10; // 10% off for 14+ days
    if (daysUntilPickup >= 7) return 0.05;  // 5% off for 7+ days
    return 0;
  }

  private calculateDurationDiscount(days: number): number {
    if (days >= 30) return 0.20; // 20% off monthly rentals
    if (days >= 14) return 0.15; // 15% off bi-weekly
    if (days >= 7) return 0.10;  // 10% off weekly
    if (days >= 3) return 0.05;  // 5% off 3+ days
    return 0;
  }

  private getCityMultiplier(city: string): number {
    const cityFactors: Record<string, number> = {
      'riyadh': 1.0,    // Base city
      'jeddah': 1.05,   // Higher demand (tourism)
      'dammam': 0.95,   // Lower demand
      'mecca': 1.15,    // High demand (religious tourism)
      'medina': 1.12,   // High demand (religious tourism)
      'taif': 1.08,     // Summer tourism
    };
    
    return cityFactors[city.toLowerCase()] || 1.0;
  }

  private calculateIntercityPremium(pickup: string, dropoff: string): number {
    // Extract city names from location strings (e.g., "Riyadh Airport" -> "Riyadh")
    const pickupCity = pickup.split(' ')[0].toLowerCase();
    const dropoffCity = dropoff.split(' ')[0].toLowerCase();
    
    // Same city, different locations (e.g., Airport to City Center)
    if (pickupCity === dropoffCity) {
      return 1.0; // No premium for same city
    }
    
    // Distance-based intercity premiums (one-way rentals)
    // Based on actual distances in Saudi Arabia
    const distancePremiums: Record<string, Record<string, number>> = {
      'riyadh': {
        'jeddah': 1.25,   // ~950 km - Major route
        'dammam': 1.18,   // ~400 km
        'mecca': 1.28,    // ~870 km
        'medina': 1.30,   // ~850 km
        'taif': 1.22,     // ~750 km
      },
      'jeddah': {
        'riyadh': 1.25,   // ~950 km
        'dammam': 1.35,   // ~1,300 km - Longest route
        'mecca': 1.08,    // ~80 km - Short distance
        'medina': 1.15,   // ~420 km
        'taif': 1.10,     // ~170 km
      },
      'dammam': {
        'riyadh': 1.18,   // ~400 km
        'jeddah': 1.35,   // ~1,300 km
        'mecca': 1.32,    // ~1,250 km
        'medina': 1.30,   // ~1,150 km
        'taif': 1.28,     // ~1,100 km
      },
      'mecca': {
        'riyadh': 1.28,   // ~870 km
        'jeddah': 1.08,   // ~80 km
        'dammam': 1.32,   // ~1,250 km
        'medina': 1.12,   // ~340 km
        'taif': 1.12,     // ~90 km
      },
      'medina': {
        'riyadh': 1.30,   // ~850 km
        'jeddah': 1.15,   // ~420 km
        'dammam': 1.30,   // ~1,150 km
        'mecca': 1.12,    // ~340 km
        'taif': 1.18,     // ~280 km
      },
    };
    
    // Get premium based on route, default to 1.20 if route not defined
    const premium = distancePremiums[pickupCity]?.[dropoffCity] || 1.20;
    
    return premium;
  }

  /**
   * Get competitor comparison for display
   */
  getCompetitorComparison(category: string, ourPrice: number): {
    competitors: CompetitorRate[];
    ourPosition: string;
    savings: number;
    percentLower: number;
  } {
    const competitors = this.competitorData[category] || this.competitorData['Sedan'];
    const competitorAvg = competitors.reduce((sum, c) => sum + c.dailyRate, 0) / competitors.length;
    const savings = Math.round(competitorAvg - ourPrice);
    const percentLower = Math.round(((competitorAvg - ourPrice) / competitorAvg) * 100);
    
    let position = 'competitive';
    if (ourPrice < Math.min(...competitors.map(c => c.dailyRate))) {
      position = 'best';
    } else if (ourPrice <= competitorAvg) {
      position = 'better';
    }
    
    return {
      competitors,
      ourPosition: position,
      savings,
      percentLower,
    };
  }
}

export const pricingService = new DynamicPricingService();
