import { useParams, useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { doc, getDoc } from 'firebase/firestore';
import { db } from '../lib/firebase';
import { pricingService } from '../services/pricingService';
import { Calendar, MapPin, TrendingDown, Info } from 'lucide-react';

export function VehicleDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [vehicle, setVehicle] = useState<any>(null);
  const [pricingResult, setPricingResult] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [formData, setFormData] = useState({
    startDate: new Date().toISOString().split('T')[0],
    endDate: new Date(Date.now() + 86400000 * 3).toISOString().split('T')[0], // 3 days default
    city: 'Riyadh',
    pickup: 'Riyadh Airport',
    dropoff: 'Riyadh Airport'
  });

  useEffect(() => {
    const fetchVehicle = async () => {
      try {
        if (!id) return;
        const vehicleRef = doc(db, 'vehicles', id);
        const vehicleSnap = await getDoc(vehicleRef);
        
        if (vehicleSnap.exists()) {
          setVehicle({ id: vehicleSnap.id, ...vehicleSnap.data() });
        }
      } catch (error) {
        console.error('Error fetching vehicle:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchVehicle();
  }, [id]);

  useEffect(() => {
    const calculatePrice = () => {
      if (!vehicle || !formData.startDate || !formData.endDate) return;
      
      const start = new Date(formData.startDate);
      const end = new Date(formData.endDate);
      const baseRate = vehicle.current_price || vehicle.base_daily_rate || 150;
      
      const result = pricingService.calculatePrice(
        baseRate,
        vehicle.category || 'Sedan',
        start,
        end,
        formData.city,
        formData.pickup,
        formData.dropoff
      );
      
      setPricingResult(result);
    };

    calculatePrice();
  }, [vehicle, formData.startDate, formData.endDate, formData.city, formData.pickup, formData.dropoff]);

  if (loading) {
    return <div className="max-w-7xl mx-auto px-6 py-12 text-center">Loading...</div>;
  }

  if (!vehicle) {
    return <div className="max-w-7xl mx-auto px-6 py-12 text-center">Vehicle not found</div>;
  }

  return (
    <div className="max-w-7xl mx-auto px-6 py-12">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div>
          <img
            src={vehicle.image || 'https://via.placeholder.com/600x400'}
            alt={vehicle.name}
            className="w-full rounded-lg shadow-lg object-cover h-96"
          />
        </div>

        <div className="bg-white rounded-lg p-8 shadow-sm border border-gray-200">
          <h1 className="text-3xl font-bold mb-4 text-gray-900">{vehicle.name}</h1>
          <p className="text-gray-600 mb-2">{vehicle.make} {vehicle.model} {vehicle.year}</p>
          
          <div className="flex items-center space-x-4 mb-6">
            <span className="px-3 py-1 bg-red-100 text-red-800 rounded-full text-sm font-medium">
              {vehicle.category}
            </span>
          </div>

          <div className="space-y-3 mb-6 text-gray-700">
            <div className="flex items-center">
              <span className="mr-3">👥</span>
              <span>{vehicle.seats} Seats</span>
            </div>
            <div className="flex items-center">
              <span className="mr-3">⚙️</span>
              <span>{vehicle.transmission}</span>
            </div>
            <div className="flex items-center">
              <span className="mr-3">⛽</span>
              <span>{vehicle.fuel_type}</span>
            </div>
            <div className="flex items-center">
              <span className="mr-3">📍</span>
              <span>{vehicle.location}</span>
            </div>
          </div>

          {/* Rental Details Form */}
          <div className="border-t pt-6 space-y-4">
            <h3 className="font-semibold text-lg flex items-center">
              <Calendar className="h-5 w-5 mr-2 text-red-700" />
              Select Dates
            </h3>
            
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
                <input
                  type="date"
                  className="input w-full text-sm"
                  value={formData.startDate}
                  min={new Date().toISOString().split('T')[0]}
                  onChange={(e) => setFormData({ ...formData, startDate: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">End Date</label>
                <input
                  type="date"
                  className="input w-full text-sm"
                  value={formData.endDate}
                  min={formData.startDate}
                  onChange={(e) => setFormData({ ...formData, endDate: e.target.value })}
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center">
                <MapPin className="h-4 w-4 mr-1" />
                City
              </label>
              <select
                className="input w-full"
                value={formData.city}
                onChange={(e) => setFormData({ ...formData, city: e.target.value })}
              >
                <option value="Riyadh">Riyadh</option>
                <option value="Jeddah">Jeddah</option>
                <option value="Dammam">Dammam</option>
                <option value="Mecca">Mecca</option>
                <option value="Medina">Medina</option>
              </select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Pickup</label>
                <select
                  className="input w-full text-sm"
                  value={formData.pickup}
                  onChange={(e) => setFormData({ ...formData, pickup: e.target.value })}
                >
                  <option value="Riyadh Airport">Riyadh Airport</option>
                  <option value="Riyadh City">Riyadh City Center</option>
                  <option value="Jeddah Airport">Jeddah Airport</option>
                  <option value="Jeddah City">Jeddah City Center</option>
                  <option value="Dammam Airport">Dammam Airport</option>
                  <option value="Dammam City">Dammam City Center</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Dropoff</label>
                <select
                  className="input w-full text-sm"
                  value={formData.dropoff}
                  onChange={(e) => setFormData({ ...formData, dropoff: e.target.value })}
                >
                  <option value="Riyadh Airport">Riyadh Airport</option>
                  <option value="Riyadh City">Riyadh City Center</option>
                  <option value="Jeddah Airport">Jeddah Airport</option>
                  <option value="Jeddah City">Jeddah City Center</option>
                  <option value="Dammam Airport">Dammam Airport</option>
                  <option value="Dammam City">Dammam City Center</option>
                </select>
              </div>
            </div>

            {pricingResult && (
              <>
                {/* Dynamic Price Display */}
                <div className="bg-gradient-to-r from-red-50 to-orange-50 p-6 rounded-lg border border-red-200">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <p className="text-sm text-gray-600 mb-1">AI-Powered Dynamic Price</p>
                      <div className="flex items-baseline gap-3">
                        <span className="text-4xl font-bold text-red-700">{pricingResult.dailyPrice} SAR</span>
                        <span className="text-sm text-gray-600">/day</span>
                      </div>
                      {pricingResult.savings > 0 && (
                        <div className="flex items-center gap-2 mt-2">
                          <span className="text-sm line-through text-gray-500">{Math.round(vehicle.base_daily_rate)} SAR</span>
                          <span className="text-sm font-medium text-green-600 flex items-center">
                            <TrendingDown className="h-4 w-4 mr-1" />
                            Save {pricingResult.savings} SAR
                          </span>
                        </div>
                      )}
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-gray-600">Total</p>
                      <p className="text-2xl font-bold text-gray-900">{pricingResult.totalPrice} SAR</p>
                      <p className="text-xs text-gray-500 mt-1">
                        {Math.ceil((new Date(formData.endDate).getTime() - new Date(formData.startDate).getTime()) / (1000 * 60 * 60 * 24))} days
                      </p>
                    </div>
                  </div>
                  
                  {/* Pricing Factors */}
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    {pricingResult.factors.advanceBookingDiscount > 0 && (
                      <div className="flex items-center text-green-700">
                        <span className="mr-1">✓</span>
                        <span>Early booking: -{Math.round(pricingResult.factors.advanceBookingDiscount * 100)}%</span>
                      </div>
                    )}
                    {pricingResult.factors.durationDiscount > 0 && (
                      <div className="flex items-center text-green-700">
                        <span className="mr-1">✓</span>
                        <span>Duration discount: -{Math.round(pricingResult.factors.durationDiscount * 100)}%</span>
                      </div>
                    )}
                    {formData.pickup !== formData.dropoff && (
                      <div className="flex items-center text-orange-600">
                        <span className="mr-1">!</span>
                        <span>One-way rental: +15%</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Competitor Comparison */}
                <div className="bg-white p-4 rounded-lg border border-gray-200">
                  <h4 className="font-semibold text-sm mb-3 flex items-center text-gray-900">
                    <Info className="h-4 w-4 mr-2 text-blue-600" />
                    Competitor Price Comparison
                  </h4>
                  <div className="space-y-2">
                    {pricingResult.competitors.map((comp: any, idx: number) => (
                      <div key={idx} className="flex justify-between items-center text-sm py-1">
                        <span className="text-gray-600">{comp.company}</span>
                        <span className="font-medium text-gray-900">{comp.dailyRate} SAR/day</span>
                      </div>
                    ))}
                    <div className="border-t pt-2 mt-2">
                      <div className="flex justify-between items-center font-semibold">
                        <span className="text-red-700">HANCO (You save!)</span>
                        <span className="text-red-700">{pricingResult.dailyPrice} SAR/day</span>
                      </div>
                      <p className="text-xs text-green-600 mt-1">
                        ⭐ {Math.round(((pricingResult.factors.competitorAvg - pricingResult.dailyPrice) / pricingResult.factors.competitorAvg) * 100)}% cheaper than competitors!
                      </p>
                    </div>
                  </div>
                </div>
              </>
            )}

            <button
              onClick={() => navigate(`/booking/${id}`, { state: { ...formData, price: pricingResult?.totalPrice } })}
              disabled={!pricingResult}
              className="w-full bg-red-700 text-white py-3 rounded-lg font-semibold hover:bg-red-800 transition-colors"
            >
              Proceed to Booking
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
