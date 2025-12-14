import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { User, LogOut, LayoutDashboard, Calendar } from 'lucide-react';

export function Navbar() {
  const { user, logout } = useAuth();

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
            {user && (
              <>
                <Link to="/my-bookings" className="text-gray-700 hover:text-red-700 font-medium transition-colors flex items-center">
                  <Calendar className="inline h-4 w-4 mr-1" />
                  My Bookings
                </Link>
                <Link to="/dashboard" className="text-gray-700 hover:text-red-700 font-medium transition-colors flex items-center">
                  <LayoutDashboard className="inline h-4 w-4 mr-1" />
                  Dashboard
                </Link>
              </>
            )}
          </div>

          {/* Auth Section */}
          <div className="flex items-center space-x-4">
            {user ? (
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <User className="h-5 w-5 text-gray-500" />
                  <span className="text-sm text-gray-700">{user.email}</span>
                </div>
                <button
                  onClick={() => logout()}
                  className="bg-gray-100 text-gray-900 px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors flex items-center"
                >
                  <LogOut className="h-4 w-4 mr-1" />
                  Logout
                </button>
              </div>
            ) : (
              <div className="flex items-center space-x-3">
                <Link to="/login" className="text-gray-700 hover:text-red-700 font-medium transition-colors">
                  Login
                </Link>
                <Link to="/register" className="bg-red-700 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-red-800 transition-colors">
                  Sign Up
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
