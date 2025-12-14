import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { collection, getDocs } from 'firebase/firestore';
import { db } from '@/lib/firebase';

export function Vehicles() {
  const navigate = useNavigate();
  const [vehicles, setVehicles] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchVehicles = async () => {
      try {
        const vehiclesRef = collection(db, 'vehicles');
        const snapshot = await getDocs(vehiclesRef);
        const vehiclesList = snapshot.docs.map(doc => ({
          id: doc.id,
          ...doc.data()
        }));
        setVehicles(vehiclesList);
      } catch (error) {
        console.error('Error fetching vehicles:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchVehicles();
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      <div className="mb-8">
        <h2 className="text-3xl font-bold mb-2 text-gray-900">Available Vehicles</h2>
        <p className="text-gray-600">Browse and select from our fleet</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {loading ? (
          <div className="col-span-full text-center py-8 text-gray-500">Loading vehicles...</div>
        ) : vehicles.length > 0 ? (
          vehicles.map((vehicle) => (
            <div
              key={vehicle.id}
              onClick={() => navigate(`/vehicles/${vehicle.id}`)}
              className="bg-white rounded-lg overflow-hidden hover:shadow-lg transition-shadow border border-gray-200 cursor-pointer"
            >
              {vehicle.image && (
                <img 
                  src={vehicle.image} 
                  alt={vehicle.name}
                  className="w-full h-48 object-cover"
                />
              )}
              <div className="p-6">
                <div className="flex justify-between items-start mb-2">
                  <h3 className="text-xl font-semibold text-gray-900">{vehicle.name}</h3>
                  <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">{vehicle.category}</span>
                </div>
                <p className="text-gray-600 mb-2 text-sm">
                  {vehicle.make} {vehicle.model} {vehicle.year}
                </p>
                <p className="text-2xl font-bold text-red-700 mb-2">
                  {vehicle.current_price || vehicle.base_daily_rate} SAR<span className="text-sm font-normal text-gray-500">/day</span>
                </p>
                <p className="text-sm text-gray-500 mb-3">📍 {vehicle.location}</p>
                <div className="flex items-center justify-between text-xs text-gray-600 mb-4">
                  <span>👥 {vehicle.seats} seats</span>
                  <span>⚙️ {vehicle.transmission}</span>
                  <span>⭐ {vehicle.rating}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span
                    className={`px-3 py-1 rounded-full text-sm ${
                      vehicle.availability_status === 'available'
                        ? 'bg-green-100 text-green-700'
                        : 'bg-gray-100 text-gray-700'
                    }`}
                  >
                    {vehicle.availability_status || 'Available'}
                  </span>
                  <button className="bg-red-700 hover:bg-red-800 text-white px-4 py-2 rounded text-sm font-medium transition-colors">
                    Book Now
                  </button>
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="col-span-full text-center py-8 text-gray-500">
            No vehicles available. Please check if Firebase is connected.
          </div>
        )}
      </div>
    </div>
  );
}
