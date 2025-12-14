import { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { auth } from '@/lib/firebase';

interface BookingDetails {
  booking_id: string;
  vehicle_name: string;
  start_date: string;
  end_date: string;
  pickup_location: string;
  total_price: number;
  status: string;
}

export function Payment() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const bookingId = searchParams.get('booking_id');

  const [booking, setBooking] = useState<BookingDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState('');

  // Card form state
  const [cardNumber, setCardNumber] = useState('');
  const [cardName, setCardName] = useState('');
  const [expiryDate, setExpiryDate] = useState('');
  const [cvv, setCvv] = useState('');

  useEffect(() => {
    if (!bookingId) {
      setError('No booking ID provided');
      setLoading(false);
      return;
    }

    // Fetch booking details
    const fetchBooking = async () => {
      try {
        // SECURITY: Get fresh token from Firebase auth (not localStorage)
        if (!auth.currentUser) {
          setError('You must be logged in to view this page');
          setLoading(false);
          navigate('/login');
          return;
        }
        const token = await auth.currentUser.getIdToken();
        const response = await axios.get(
          `http://localhost:8000/api/v1/bookings/${bookingId}`,
          {
            headers: { Authorization: `Bearer ${token}` },
          }
        );

        const data = response.data;
        setBooking({
          booking_id: data.booking_id,
          vehicle_name: data.selected_vehicle?.name || 'Vehicle',
          start_date: data.start_date,
          end_date: data.end_date,
          pickup_location: data.pickup_location,
          total_price: data.pricing_info?.recommended_price?.total_price || 0,
          status: data.status,
        });
      } catch (err: any) {
        console.error('Error fetching booking:', err);
        setError(err.response?.data?.detail || 'Failed to load booking details');
      } finally {
        setLoading(false);
      }
    };

    fetchBooking();
  }, [bookingId]);

  const handlePayment = async (e: React.FormEvent) => {
    e.preventDefault();
    setProcessing(true);
    setError('');

    try {
      // SECURITY: Get fresh token from Firebase auth (not localStorage)
      if (!auth.currentUser) {
        setError('You must be logged in to make payments');
        setProcessing(false);
        navigate('/login');
        return;
      }
      const token = await auth.currentUser.getIdToken();
      const response = await axios.post(
        'http://localhost:8000/api/v1/payments/pay',
        {
          booking_id: bookingId,
          card_number: cardNumber.replace(/\s/g, ''),
          card_holder: cardName,
          expiry_date: expiryDate,
          cvv: cvv,
          amount: booking?.total_price || 0,
        },
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      if (response.data.status === 'success') {
        // Payment successful - redirect to bookings
        alert('✅ Payment successful! Your booking is confirmed.');
        navigate('/my-bookings');
      } else {
        setError(response.data.message || 'Payment failed');
      }
    } catch (err: any) {
      console.error('Payment error:', err);
      setError(err.response?.data?.detail || 'Payment processing failed');
    } finally {
      setProcessing(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading booking details...</p>
        </div>
      </div>
    );
  }

  if (error && !booking) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 text-xl mb-4">❌ {error}</p>
          <button
            onClick={() => navigate('/my-bookings')}
            className="bg-red-600 text-white px-6 py-2 rounded-lg hover:bg-red-700"
          >
            Go to My Bookings
          </button>
        </div>
      </div>
    );
  }

  if (!booking) {
    return null;
  }

  // Format card number with spaces
  const formatCardNumber = (value: string) => {
    const cleaned = value.replace(/\s/g, '');
    const groups = cleaned.match(/.{1,4}/g);
    return groups ? groups.join(' ') : cleaned;
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-lg shadow-lg overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-red-600 to-red-800 px-6 py-8">
            <h1 className="text-3xl font-bold text-white">Complete Payment</h1>
            <p className="text-red-100 mt-2">Secure payment for your booking</p>
          </div>

          <div className="grid md:grid-cols-2 gap-8 p-6">
            {/* Booking Summary */}
            <div className="space-y-4">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Booking Summary</h2>
              
              <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">Booking ID:</span>
                  <span className="font-mono text-sm">{booking.booking_id.slice(0, 12)}...</span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-gray-600">Vehicle:</span>
                  <span className="font-semibold">{booking.vehicle_name}</span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-gray-600">Dates:</span>
                  <span>{booking.start_date} to {booking.end_date}</span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-gray-600">Pickup:</span>
                  <span>{booking.pickup_location}</span>
                </div>
                
                <div className="border-t pt-3 mt-3">
                  <div className="flex justify-between items-center">
                    <span className="text-lg font-semibold text-gray-900">Total Amount:</span>
                    <span className="text-2xl font-bold text-red-600">{booking.total_price} SAR</span>
                  </div>
                </div>
              </div>

              <div className="flex items-start space-x-2 text-sm text-gray-600 bg-blue-50 p-3 rounded">
                <span>🔒</span>
                <p>Your payment is secured with industry-standard encryption</p>
              </div>
            </div>

            {/* Payment Form */}
            <div className="space-y-4">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Payment Details</h2>
              
              <form onSubmit={handlePayment} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Card Number
                  </label>
                  <input
                    type="text"
                    value={cardNumber}
                    onChange={(e) => {
                      const formatted = formatCardNumber(e.target.value);
                      if (formatted.replace(/\s/g, '').length <= 16) {
                        setCardNumber(formatted);
                      }
                    }}
                    placeholder="1234 5678 9012 3456"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Cardholder Name
                  </label>
                  <input
                    type="text"
                    value={cardName}
                    onChange={(e) => setCardName(e.target.value)}
                    placeholder="John Doe"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                    required
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Expiry Date
                    </label>
                    <input
                      type="text"
                      value={expiryDate}
                      onChange={(e) => {
                        let value = e.target.value.replace(/\D/g, '');
                        if (value.length >= 2) {
                          value = value.slice(0, 2) + '/' + value.slice(2, 4);
                        }
                        setExpiryDate(value);
                      }}
                      placeholder="MM/YY"
                      maxLength={5}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      CVV
                    </label>
                    <input
                      type="text"
                      value={cvv}
                      onChange={(e) => {
                        const value = e.target.value.replace(/\D/g, '');
                        if (value.length <= 3) {
                          setCvv(value);
                        }
                      }}
                      placeholder="123"
                      maxLength={3}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                      required
                    />
                  </div>
                </div>

                {error && (
                  <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                    {error}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={processing}
                  className="w-full bg-red-600 text-white py-3 rounded-lg font-semibold hover:bg-red-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                >
                  {processing ? (
                    <span className="flex items-center justify-center">
                      <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Processing...
                    </span>
                  ) : (
                    `Pay ${booking.total_price} SAR`
                  )}
                </button>
              </form>

              <div className="text-xs text-gray-500 text-center">
                <p>💳 Test Card: 4242 4242 4242 4242</p>
                <p>Any future expiry date and 3-digit CVV</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
