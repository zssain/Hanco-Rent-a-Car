import { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { doc, getDoc, collection, addDoc } from 'firebase/firestore';
import { db } from '@/lib/firebase';
import { useAuth } from '../contexts/AuthContext';
import { pricingService } from '../services/pricingService';
import { Calendar, CreditCard, MapPin, Car, CheckCircle } from 'lucide-react';

export function Booking() {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();
  const [vehicle, setVehicle] = useState<any>(null);
  const [formData, setFormData] = useState({
    startDate: location.state?.startDate || '',
    endDate: location.state?.endDate || '',
    city: location.state?.city || 'Riyadh',
    pickup: location.state?.pickup || 'Riyadh Airport',
    dropoff: location.state?.dropoff || 'Riyadh Airport',
    cardNumber: '',
    expiryDate: '',
    cvv: '',
    cardName: '',
    guestName: '',
    guestEmail: '',
    guestPhone: ''
  });
  const [pricingResult, setPricingResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [bookingId, setBookingId] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

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
      }
    };

    fetchVehicle();
  }, [id]);

  useEffect(() => {
    if (formData.startDate && formData.endDate && vehicle) {
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
    }
  }, [formData.startDate, formData.endDate, formData.city, formData.pickup, formData.dropoff, vehicle]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // Guest bookings are allowed - no authentication required

      if (!pricingResult) {
        throw new Error('Price calculation failed');
      }

      // Create booking in Firebase
      const bookingData = {
        user_id: user?.uid || 'guest',
        vehicle_id: id,
        vehicle_name: vehicle.name,
        start_date: formData.startDate,
        end_date: formData.endDate,
        pickup_location: formData.pickup,
        dropoff_location: formData.dropoff,
        total_price: pricingResult.totalPrice,
        daily_price: pricingResult.dailyPrice,
        status: 'confirmed',
        payment_status: 'completed',
        payment_method: 'card',
        guest_name: !user ? formData.guestName : undefined,
        guest_email: !user ? formData.guestEmail : undefined,
        guest_phone: !user ? formData.guestPhone : undefined,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };

      const bookingsRef = collection(db, 'bookings');
      const bookingDoc = await addDoc(bookingsRef, bookingData);
      
      setBookingId(bookingDoc.id);
      setSuccess(true);
    } catch (err: any) {
      setError(err.message || 'Booking failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="container-custom py-12">
        <div className="max-w-2xl mx-auto text-center">
          <div className="bg-white rounded-lg p-8 shadow-sm border border-gray-200">
            <CheckCircle className="h-16 w-16 text-green-600 mx-auto mb-4" />
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Booking Confirmed!</h1>
            <p className="text-gray-600 mb-6">Your vehicle has been successfully booked.</p>
            
            <div className="bg-gray-50 rounded-lg p-6 mb-6 text-left">
              <h2 className="font-semibold text-lg mb-4">Booking Details</h2>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Booking ID:</span>
                  <span className="font-mono font-semibold">{bookingId}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Vehicle:</span>
                  <span className="font-semibold">{vehicle?.name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Duration:</span>
                  <span>{formData.startDate} to {formData.endDate}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Total Paid:</span>
                  <span className="font-bold text-red-700">{pricingResult?.totalPrice} SAR</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Daily Rate:</span>
                  <span className="font-semibold">{pricingResult?.dailyPrice} SAR/day</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Status:</span>
                  <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs font-medium">
                    Confirmed
                  </span>
                </div>
              </div>
            </div>

            <div className="flex space-x-3">
              <button
                onClick={() => navigate('/my-bookings')}
                className="flex-1 bg-red-700 text-white py-3 rounded-lg font-semibold hover:bg-red-800 transition-colors"
              >
                View My Bookings
              </button>
              <button
                onClick={() => navigate('/vehicles')}
                className="flex-1 bg-gray-100 text-gray-900 py-3 rounded-lg font-semibold hover:bg-gray-200 transition-colors"
              >
                Browse Vehicles
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!vehicle) {
    return <div className="container-custom py-12 text-center">Loading...</div>;
  }

  return (
    <div className="container-custom py-12">
      <h1 className="text-3xl font-bold mb-8">Complete Your Booking</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2">
          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                {error}
              </div>
            )}

            {/* Guest Information - only shown if not logged in */}
            {!user && (
              <div className="card">
                <h2 className="text-xl font-semibold mb-4">Your Information</h2>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Full Name</label>
                    <input
                      type="text"
                      className="input"
                      placeholder="John Doe"
                      required
                      value={formData.guestName}
                      onChange={(e) => setFormData({ ...formData, guestName: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Email</label>
                    <input
                      type="email"
                      className="input"
                      placeholder="john@example.com"
                      required
                      value={formData.guestEmail}
                      onChange={(e) => setFormData({ ...formData, guestEmail: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Phone Number</label>
                    <input
                      type="tel"
                      className="input"
                      placeholder="+966 50 123 4567"
                      required
                      value={formData.guestPhone}
                      onChange={(e) => setFormData({ ...formData, guestPhone: e.target.value })}
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Rental Period */}
            <div className="card">
              <h2 className="text-xl font-semibold mb-4 flex items-center">
                <Calendar className="h-5 w-5 mr-2 text-red-700" />
                Rental Period
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Start Date</label>
                  <input
                    type="date"
                    className="input"
                    required
                    min={new Date().toISOString().split('T')[0]}
                    value={formData.startDate}
                    onChange={(e) => setFormData({ ...formData, startDate: e.target.value })}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">End Date</label>
                  <input
                    type="date"
                    className="input"
                    required
                    min={formData.startDate}
                    value={formData.endDate}
                    onChange={(e) => setFormData({ ...formData, endDate: e.target.value })}
                  />
                </div>
              </div>

              <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2 flex items-center">
                    <MapPin className="h-4 w-4 mr-1" />
                    City
                  </label>
                  <select
                    className="input"
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

                <div>
                  <label className="block text-sm font-medium mb-2">Pickup Location</label>
                  <select
                    className="input"
                    value={formData.pickup}
                    onChange={(e) => setFormData({ ...formData, pickup: e.target.value })}
                  >
                    <option value="Riyadh Airport">Riyadh Airport</option>
                    <option value="Riyadh Downtown">Riyadh Downtown</option>
                    <option value="Jeddah Airport">Jeddah Airport</option>
                    <option value="Jeddah Corniche">Jeddah Corniche</option>
                    <option value="Dammam Airport">Dammam Airport</option>
                    <option value="Dammam City">Dammam City</option>
                    <option value="Mecca Central">Mecca Central</option>
                    <option value="Medina Airport">Medina Airport</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Dropoff Location</label>
                  <select
                    className="input"
                    value={formData.dropoff}
                    onChange={(e) => setFormData({ ...formData, dropoff: e.target.value })}
                  >
                    <option value="Riyadh Airport">Riyadh Airport</option>
                    <option value="Riyadh Downtown">Riyadh Downtown</option>
                    <option value="Jeddah Airport">Jeddah Airport</option>
                    <option value="Jeddah Corniche">Jeddah Corniche</option>
                    <option value="Dammam Airport">Dammam Airport</option>
                    <option value="Dammam City">Dammam City</option>
                    <option value="Mecca Central">Mecca Central</option>
                    <option value="Medina Airport">Medina Airport</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Payment */}
            <div className="card">
              <h2 className="text-xl font-semibold mb-4 flex items-center">
                <CreditCard className="h-5 w-5 mr-2 text-red-700" />
                Payment Information
              </h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Cardholder Name</label>
                  <input
                    type="text"
                    className="input"
                    placeholder="John Doe"
                    required
                    value={formData.cardName}
                    onChange={(e) => setFormData({ ...formData, cardName: e.target.value })}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Card Number</label>
                  <input
                    type="text"
                    className="input"
                    placeholder="1234 5678 9012 3456"
                    required
                    maxLength={19}
                    value={formData.cardNumber}
                    onChange={(e) => setFormData({ ...formData, cardNumber: e.target.value })}
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Expiry Date</label>
                    <input
                      type="text"
                      className="input"
                      placeholder="MM/YY"
                      required
                      maxLength={5}
                      value={formData.expiryDate}
                      onChange={(e) => setFormData({ ...formData, expiryDate: e.target.value })}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">CVV</label>
                    <input
                      type="text"
                      className="input"
                      placeholder="123"
                      required
                      maxLength={4}
                      value={formData.cvv}
                      onChange={(e) => setFormData({ ...formData, cvv: e.target.value })}
                    />
                  </div>
                </div>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading || !pricingResult}
              className="w-full bg-red-700 text-white py-3 rounded-lg font-semibold hover:bg-red-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Processing...' : `Confirm Booking & Pay ${pricingResult?.totalPrice || 0} SAR`}
            </button>
          </form>
        </div>

        {/* Summary Sidebar */}
        <div className="lg:col-span-1">
          <div className="card sticky top-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center">
              <Car className="h-5 w-5 mr-2 text-red-700" />
              Booking Summary
            </h2>

            <div className="mb-4">
              <img
                src={vehicle.image || 'https://via.placeholder.com/400x200'}
                alt={vehicle.name}
                className="w-full rounded-lg mb-3"
              />
              <h3 className="font-semibold text-lg">{vehicle.name}</h3>
              <p className="text-sm text-gray-600">{vehicle.make} {vehicle.model}</p>
            </div>

            <div className="border-t pt-4 space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Start Date:</span>
                <span className="font-medium">{formData.startDate || '-'}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">End Date:</span>
                <span className="font-medium">{formData.endDate || '-'}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Pickup:</span>
                <span className="font-medium">{formData.pickup}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Dropoff:</span>
                <span className="font-medium">{formData.dropoff}</span>
              </div>
            </div>

            {pricingResult && (
              <div className="border-t mt-4 pt-4">
                <div className="space-y-2 mb-3">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Daily Rate:</span>
                    <span className="font-medium">{pricingResult.dailyPrice} SAR/day</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Duration:</span>
                    <span className="font-medium">{pricingResult.days} days</span>
                  </div>
                  {pricingResult.savings > 0 && (
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">You Save:</span>
                      <span className="font-medium text-green-600">-{pricingResult.savings} SAR</span>
                    </div>
                  )}
                </div>
                <div className="flex justify-between items-center border-t pt-3">
                  <span className="text-lg font-semibold">Total Amount:</span>
                  <span className="text-2xl font-bold text-red-700">{pricingResult.totalPrice} SAR</span>
                </div>
                <p className="text-xs text-gray-500 mt-1">Includes dynamic pricing & taxes</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
