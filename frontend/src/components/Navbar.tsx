import { Link } from 'react-router-dom';
import { LayoutDashboard, Calendar, MessageSquare } from 'lucide-react';

export function Navbar() {
  return (
    <nav className="bg-white border-b border-gray-200 sticky top-0 z-50 shadow-sm">
      <div className="container-custom">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-3">
            <img 
              src="/hanco-logo.jpg" 
              alt="Hanco" 
              className="h-12"
              onError={(e) => {
                e.currentTarget.style.display = 'none';
                const fallback = e.currentTarget.nextElementSibling as HTMLElement;
                if (fallback) fallback.style.display = 'flex';
              }}
            />
            <div style={{ display: 'none' }} className="items-center space-x-2">
              <div className="bg-red-700 p-1.5 rounded">
                <span className="text-white text-lg font-bold">H</span>
              </div>
              <span className="text-xl font-bold text-gray-900">HANCO</span>
            </div>
          </Link>

          {/* Navigation Links */}
          <div className="hidden md:flex items-center space-x-6">
            <Link to="/vehicles" className="text-gray-700 hover:text-red-700 font-medium transition-colors">
              Vehicles
            </Link>
            <Link to="/my-bookings" className="text-gray-700 hover:text-red-700 font-medium transition-colors flex items-center">
              <Calendar className="inline h-4 w-4 mr-1" />
              My Bookings
            </Link>
            <Link to="/dashboard" className="text-gray-700 hover:text-red-700 font-medium transition-colors flex items-center">
              <LayoutDashboard className="inline h-4 w-4 mr-1" />
              Dashboard
            </Link>
          </div>

          {/* Right Section */}
          <div className="flex items-center space-x-4">
            <Link 
              to="/dashboard" 
              className="bg-red-700 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-red-800 transition-colors flex items-center"
            >
              <MessageSquare className="h-4 w-4 mr-1" />
              AI Chatbot
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}
