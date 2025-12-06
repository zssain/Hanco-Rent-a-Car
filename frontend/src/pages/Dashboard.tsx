import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { collection, query, where, getDocs } from 'firebase/firestore';
import { db } from '../lib/firebase';

export function Dashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [dashboardData, setDashboardData] = useState({
    total_bookings: 0,
    loyalty_points: 0,
    saved_amount: 'SAR 0',
    ai_bookings: 0,
    recent_activity: []
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchDashboard = async () => {
      if (!user) return;
      
      try {
        setLoading(true);
        
        // Fetch bookings from Firebase
        const bookingsRef = collection(db, 'bookings');
        const q = query(bookingsRef, where('user_id', '==', user.uid));
        const snapshot = await getDocs(q);
        
        const bookingsData = snapshot.docs.map(doc => ({
          id: doc.id,
          ...doc.data()
        }));
        
        const totalBookings = bookingsData.length;
        const totalSpent = bookingsData.reduce((sum: number, b: any) => sum + (b.total_price || 0), 0);
        const savedAmount = totalSpent * 0.1; // Assume 10% savings from dynamic pricing
        
        setDashboardData({
          total_bookings: totalBookings,
          loyalty_points: totalBookings * 10,
          saved_amount: `SAR ${savedAmount.toFixed(0)}`,
          ai_bookings: 0, // TODO: Track chatbot bookings
          recent_activity: bookingsData.slice(0, 5)
        });
      } catch (error) {
        console.error('Error fetching dashboard:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboard();
  }, [user]);

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      <div className="mb-8">
        <h2 className="text-3xl font-bold mb-2 text-gray-900">
          Welcome back, {user?.displayName || user?.email}!
        </h2>
        <p className="text-gray-600">Consumer Dashboard</p>
      </div>

      <div className="space-y-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
            <h3 className="text-gray-600 text-sm font-medium mb-2">Total Bookings</h3>
            <div className="text-3xl font-bold mb-1 text-red-700">
              {loading ? '...' : dashboardData.total_bookings}
            </div>
            <p className="text-gray-500 text-sm">Since joining</p>
          </div>

          <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
            <h3 className="text-gray-600 text-sm font-medium mb-2">Loyalty Points</h3>
            <div className="text-3xl font-bold mb-1 text-red-700">
              {loading ? '...' : dashboardData.loyalty_points.toLocaleString()}
            </div>
            <p className="text-gray-500 text-sm">Redeem for discounts</p>
          </div>

          <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
            <h3 className="text-gray-600 text-sm font-medium mb-2">Saved Amount</h3>
            <div className="text-3xl font-bold mb-1 text-green-600">
              {loading ? '...' : dashboardData.saved_amount}
            </div>
            <p className="text-gray-500 text-sm">Through dynamic pricing</p>
          </div>

          <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
            <h3 className="text-gray-600 text-sm font-medium mb-2">AI Bookings</h3>
            <div className="text-3xl font-bold mb-1 text-red-700">
              {loading ? '...' : dashboardData.ai_bookings}
            </div>
            <p className="text-gray-500 text-sm">Via chatbot</p>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-6 pb-0">
            <h3 className="text-xl font-semibold text-gray-900 mb-6">Quick Actions</h3>
          </div>
          <div className="grid grid-cols-2">
            <button
              onClick={() => navigate('/vehicles')}
              className="bg-red-700 text-white p-8 hover:bg-red-800 transition-colors text-left border-r border-red-600"
            >
              <div className="flex items-center space-x-4">
                <div className="bg-red-600 p-3 rounded-lg">
                  <span className="text-3xl">🚗</span>
                </div>
                <div>
                  <h4 className="font-semibold text-white text-lg">Browse Vehicles</h4>
                  <p className="text-red-100 text-sm">Find your perfect ride</p>
                </div>
              </div>
            </button>

            <button
              onClick={() => {
                // Trigger click on chatbot button
                const chatButton = document.querySelector('button[aria-label="Open chat"]') as HTMLButtonElement;
                if (chatButton) {
                  chatButton.click();
                }
              }}
              className="bg-red-700 text-white p-8 hover:bg-red-800 transition-colors text-left"
            >
              <div className="flex items-center space-x-4">
                <div className="bg-red-600 p-3 rounded-lg">
                  <span className="text-3xl">💬</span>
                </div>
                <div>
                  <h4 className="font-semibold text-white text-lg">AI Assistant</h4>
                  <p className="text-red-100 text-sm">Chat with our AI bot</p>
                </div>
              </div>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
