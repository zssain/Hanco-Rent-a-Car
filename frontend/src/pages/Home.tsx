import { Link } from 'react-router-dom';

export function Home() {
  return (
    <div className="bg-gray-50">
      <section className="bg-white py-20 border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 text-center">
          <img 
            src="/hanco-logo.jpg" 
            alt="Hanco Logo" 
            className="h-20 mx-auto mb-6"
            onError={(e) => {
              e.currentTarget.style.display = 'none';
              e.currentTarget.nextElementSibling?.classList.remove('hidden');
            }}
          />
          <div className="hidden mb-6">
            <svg width="120" height="50" viewBox="0 0 120 50" className="mx-auto">
              <rect width="50" height="50" fill="#b91c1c" rx="4"/>
              <text x="55" y="35" fontFamily="Arial" fontSize="28" fontWeight="bold" fill="#1f2937">HANCO</text>
            </svg>
          </div>
          <h1 className="text-5xl md:text-6xl font-bold mb-4 text-gray-900">Welcome to HANCO</h1>
          <p className="text-xl mb-8 text-gray-600">Premium Car Rental Services in Saudi Arabia</p>
          
          <div className="bg-white rounded-lg p-8 shadow-lg max-w-4xl mx-auto border border-gray-200">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Find Your Perfect Vehicle</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="text-left">
                <label className="block text-gray-700 text-sm font-medium mb-2">City</label>
                <select className="w-full px-4 py-2.5 border border-gray-300 rounded focus:ring-2 focus:ring-red-500 focus:border-transparent">
                  <option>Riyadh</option><option>Jeddah</option><option>Dammam</option>
                </select>
              </div>
              <div className="text-left">
                <label className="block text-gray-700 text-sm font-medium mb-2">Start Date</label>
                <input type="date" className="w-full px-4 py-2.5 border border-gray-300 rounded focus:ring-2 focus:ring-red-500 focus:border-transparent" />
              </div>
              <div className="text-left">
                <label className="block text-gray-700 text-sm font-medium mb-2">End Date</label>
                <input type="date" className="w-full px-4 py-2.5 border border-gray-300 rounded focus:ring-2 focus:ring-red-500 focus:border-transparent" />
              </div>
            </div>
            <Link to="/vehicles" className="w-full bg-red-700 text-white py-3.5 rounded font-semibold hover:bg-red-800 transition-colors text-lg block text-center">
              Search Vehicles
            </Link>
          </div>
        </div>
      </section>
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-center mb-12 text-gray-900">Why Choose HANCO?</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="bg-white rounded-lg p-8 shadow-md border border-gray-100 text-center hover:shadow-lg transition-shadow">
              <div className="bg-red-50 p-4 rounded-full w-16 h-16 mx-auto mb-4 flex items-center justify-center">
                <span className="text-3xl">📊</span>
              </div>
              <h3 className="text-xl font-semibold mb-3 text-gray-900">Dynamic Pricing</h3>
              <p className="text-gray-600">ML-powered pricing that analyzes market conditions and competitor rates in real-time</p>
            </div>
            <div className="bg-white rounded-lg p-8 shadow-md border border-gray-100 text-center hover:shadow-lg transition-shadow">
              <div className="bg-red-50 p-4 rounded-full w-16 h-16 mx-auto mb-4 flex items-center justify-center">
                <span className="text-3xl">🚗</span>
              </div>
              <h3 className="text-xl font-semibold mb-3 text-gray-900">Wide Selection</h3>
              <p className="text-gray-600">Choose from economy to luxury vehicles across multiple cities in Saudi Arabia</p>
            </div>
            <div className="bg-white rounded-lg p-8 shadow-md border border-gray-100 text-center hover:shadow-lg transition-shadow">
              <div className="bg-red-50 p-4 rounded-full w-16 h-16 mx-auto mb-4 flex items-center justify-center">
                <span className="text-3xl">💬</span>
              </div>
              <h3 className="text-xl font-semibold mb-3 text-gray-900">AI Chatbot</h3>
              <p className="text-gray-600">Natural language booking assistant powered by Gemini AI for seamless experience</p>
            </div>
          </div>
        </div>
      </section>
      <section className="bg-white py-20 border-t border-gray-200">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="text-3xl font-bold mb-4 text-gray-900">Ready to Get Started?</h2>
          <p className="text-gray-600 mb-8 text-lg">Join thousands of satisfied customers using our AI-powered platform</p>
          <div className="flex gap-4 justify-center flex-wrap">
            <Link to="/register" className="bg-red-700 text-white px-8 py-3.5 rounded font-semibold hover:bg-red-800 transition-colors shadow-md">
              Sign Up Free
            </Link>
            <Link to="/vehicles" className="bg-white text-red-700 border-2 border-red-700 px-8 py-3.5 rounded font-semibold hover:bg-red-50 transition-colors">
              Browse Vehicles
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
