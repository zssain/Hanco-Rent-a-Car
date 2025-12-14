import { useState, useEffect } from 'react';
import api from '@/lib/api';

interface Booking {
  id: string;
  vehicle_id: string;
  vehicle_name?: string;
  start_date: string;
  end_date: string;
  status: string;
  total_amount: number;
  created_at: string;
}

export function Admin() {
  const [stats, setStats] = useState({
    totalBookings: 0,
    totalRevenue: 0,
    totalVehicles: 0,
    totalUsers: 0
  });
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [bookingsRes, vehiclesRes] = await Promise.all([
          api.get('/api/v1/bookings'),
          api.get('/api/v1/vehicles')
        ]);

        const bookingsData = Array.isArray(bookingsRes.data) ? bookingsRes.data : [];
        setBookings(bookingsData);
        
        const totalRevenue = bookingsData.reduce((sum: number, b: any) => sum + (b.total_amount || 0), 0);
        
        setStats({
          totalBookings: bookingsData.length,
          totalRevenue: totalRevenue,
          totalVehicles: vehiclesRes.data.length,
          totalUsers: 0
        });
      } catch (error) {
        console.error('Error fetching admin data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const getStatusBadge = (status: string) => {
    const statusClasses = {
      confirmed: 'bg-green-100 text-green-800',
      pending: 'bg-yellow-100 text-yellow-800',
      active: 'bg-blue-100 text-blue-800',
      completed: 'bg-gray-100 text-gray-800',
      cancelled: 'bg-red-100 text-red-800'
    };

    return statusClasses[status as keyof typeof statusClasses] || 'bg-gray-100 text-gray-800';
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-6 py-12 text-center">
        <div className="text-gray-600">Loading admin dashboard...</div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2 text-gray-900">Admin Dashboard</h1>
        <p className="text-gray-600">Manage bookings, vehicles, and platform analytics</p>
      </div>

      <div className="space-y-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">Total Bookings</p>
                <p className="text-3xl font-bold text-red-700">{stats.totalBookings}</p>
              </div>
              <div className="bg-red-100 p-3 rounded-lg">
                <span className="text-3xl">📊</span>
              </div>
            </div>
            <p className="text-gray-500 text-sm mt-2">All time bookings</p>
          </div>

          <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">Total Revenue</p>
                <p className="text-3xl font-bold text-green-600">{stats.totalRevenue.toFixed(0)} SAR</p>
              </div>
              <div className="bg-green-100 p-3 rounded-lg">
                <span className="text-3xl">💰</span>
              </div>
            </div>
            <p className="text-gray-500 text-sm mt-2">Total earnings</p>
          </div>

          <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">Total Vehicles</p>
                <p className="text-3xl font-bold text-red-700">{stats.totalVehicles}</p>
              </div>
              <div className="bg-red-100 p-3 rounded-lg">
                <span className="text-3xl">🚗</span>
              </div>
            </div>
            <p className="text-gray-500 text-sm mt-2">Fleet size</p>
          </div>

          <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">Active Users</p>
                <p className="text-3xl font-bold text-red-700">{stats.totalUsers}</p>
              </div>
              <div className="bg-red-100 p-3 rounded-lg">
                <span className="text-3xl">👥</span>
              </div>
            </div>
            <p className="text-gray-500 text-sm mt-2">Registered users</p>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">Recent Bookings</h2>
            <p className="text-gray-600 text-sm mt-1">Latest booking transactions</p>
          </div>
          
          <div className="p-6">
            {bookings.length === 0 ? (
              <div className="text-center py-12">
                <div className="bg-gray-100 p-4 rounded-full w-16 h-16 mx-auto mb-4 flex items-center justify-center">
                  <span className="text-3xl">📋</span>
                </div>
                <p className="text-gray-600">No bookings yet</p>
                <p className="text-gray-500 text-sm mt-1">Bookings will appear here once customers start renting</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-3 px-4 text-gray-700 font-semibold">ID</th>
                      <th className="text-left py-3 px-4 text-gray-700 font-semibold">Vehicle</th>
                      <th className="text-left py-3 px-4 text-gray-700 font-semibold">Start Date</th>
                      <th className="text-left py-3 px-4 text-gray-700 font-semibold">End Date</th>
                      <th className="text-left py-3 px-4 text-gray-700 font-semibold">Status</th>
                      <th className="text-left py-3 px-4 text-gray-700 font-semibold">Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {bookings.slice(0, 10).map((booking) => (
                      <tr key={booking.id} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                        <td className="py-3 px-4 text-gray-900 font-mono text-sm">{booking.id.slice(0, 8)}</td>
                        <td className="py-3 px-4 text-gray-900">{booking.vehicle_name || booking.vehicle_id}</td>
                        <td className="py-3 px-4 text-gray-600">{new Date(booking.start_date).toLocaleDateString()}</td>
                        <td className="py-3 px-4 text-gray-600">{new Date(booking.end_date).toLocaleDateString()}</td>
                        <td className="py-3 px-4">
                          <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusBadge(booking.status)}`}>
                            {booking.status}
                          </span>
                        </td>
                        <td className="py-3 px-4 font-semibold text-gray-900">{booking.total_amount.toFixed(2)} SAR</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
