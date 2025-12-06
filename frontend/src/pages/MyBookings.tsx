import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { collection, query, where, getDocs, deleteDoc, doc } from 'firebase/firestore';
import { db } from '../lib/firebase';
import { useAuth } from '../contexts/AuthContext';
import { Calendar, MapPin, Car, Trash2, AlertCircle } from 'lucide-react';

interface Booking {
  id: string;
  vehicle_id: string;
  vehicle_name?: string;
  start_date: string;
  end_date: string;
  pickup_location: string;
  dropoff_location: string;
  total_price: number;
  status: string;
  created_at: string;
}

export function MyBookings() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchBookings();
  }, [user]);

  const fetchBookings = async () => {
    try {
      if (!user) {
        setBookings([]);
        setLoading(false);
        return;
      }

      const bookingsRef = collection(db, 'bookings');
      const q = query(bookingsRef, where('user_id', '==', user.uid));
      const snapshot = await getDocs(q);
      
      const bookingsData = snapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data()
      })) as Booking[];
      
      setBookings(bookingsData);
    } catch (err: any) {
      console.error('Error fetching bookings:', err);
      setError('Failed to load bookings');
    } finally {
      setLoading(false);
    }
  };

  const handleCancelBooking = async (bookingId: string) => {
    if (!window.confirm('Are you sure you want to cancel this booking?')) {
      return;
    }

    try {
      await deleteDoc(doc(db, 'bookings', bookingId));
      setBookings(bookings.filter(b => b.id !== bookingId));
    } catch (err: any) {
      alert('Failed to cancel booking');
    }
  };

  const getStatusBadge = (status: string) => {
    const statusColors: Record<string, string> = {
      pending: 'bg-yellow-100 text-yellow-800',
      confirmed: 'bg-green-100 text-green-800',
      active: 'bg-blue-100 text-blue-800',
      completed: 'bg-gray-100 text-gray-800',
      cancelled: 'bg-red-100 text-red-800',
    };

    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[status] || 'bg-gray-100 text-gray-800'}`}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="container-custom py-12 text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-700 mx-auto"></div>
      </div>
    );
  }

  return (
    <div className="container-custom py-12">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">My Bookings</h1>
        <p className="text-gray-600">Manage your vehicle reservations</p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6 flex items-center">
          <AlertCircle className="h-5 w-5 mr-2" />
          {error}
        </div>
      )}

      {bookings.length === 0 ? (
        <div className="card text-center py-12">
          <Car className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">No Bookings Yet</h2>
          <p className="text-gray-600 mb-6">Start exploring our vehicles and make your first booking!</p>
          <button
            onClick={() => navigate('/vehicles')}
            className="btn btn-primary"
          >
            Browse Vehicles
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6">
          {bookings.map((booking) => (
            <div key={booking.id} className="card hover:shadow-md transition-shadow">
              <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
                <div className="flex-1">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3 className="font-semibold text-lg text-gray-900 flex items-center">
                        <Car className="h-5 w-5 mr-2 text-red-700" />
                        {booking.vehicle_name || `Vehicle #${booking.vehicle_id}`}
                      </h3>
                      <p className="text-sm text-gray-500 mt-1">Booking ID: {booking.id}</p>
                    </div>
                    {getStatusBadge(booking.status)}
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
                    <div className="flex items-center text-gray-600">
                      <Calendar className="h-4 w-4 mr-2 text-gray-400" />
                      <div>
                        <p className="text-xs text-gray-500">Start</p>
                        <p className="font-medium text-gray-900">{booking.start_date}</p>
                      </div>
                    </div>

                    <div className="flex items-center text-gray-600">
                      <Calendar className="h-4 w-4 mr-2 text-gray-400" />
                      <div>
                        <p className="text-xs text-gray-500">End</p>
                        <p className="font-medium text-gray-900">{booking.end_date}</p>
                      </div>
                    </div>

                    <div className="flex items-center text-gray-600">
                      <MapPin className="h-4 w-4 mr-2 text-gray-400" />
                      <div>
                        <p className="text-xs text-gray-500">Pickup</p>
                        <p className="font-medium text-gray-900">{booking.pickup_location}</p>
                      </div>
                    </div>

                    <div className="flex items-center text-gray-600">
                      <MapPin className="h-4 w-4 mr-2 text-gray-400" />
                      <div>
                        <p className="text-xs text-gray-500">Dropoff</p>
                        <p className="font-medium text-gray-900">{booking.dropoff_location}</p>
                      </div>
                    </div>
                  </div>

                  <div className="mt-4 flex items-center justify-between border-t pt-3">
                    <div>
                      <span className="text-sm text-gray-500">Total Amount:</span>
                      <span className="ml-2 text-xl font-bold text-red-700">{booking.total_price || 'N/A'} SAR</span>
                    </div>
                  </div>
                </div>

                <div className="mt-4 lg:mt-0 lg:ml-6 flex lg:flex-col gap-2">
                  {(booking.status === 'pending' || booking.status === 'confirmed') && (
                    <button
                      onClick={() => handleCancelBooking(booking.id)}
                      className="btn btn-outline text-red-600 hover:bg-red-50 border-red-300"
                    >
                      <Trash2 className="h-4 w-4 mr-1" />
                      Cancel
                    </button>
                  )}
                  <button
                    onClick={() => navigate(`/vehicles/${booking.vehicle_id}`)}
                    className="btn btn-secondary"
                  >
                    View Vehicle
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
