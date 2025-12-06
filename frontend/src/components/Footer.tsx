import { Link } from 'react-router-dom';
import { Car, Mail, Phone, MapPin } from 'lucide-react';

export function Footer() {
  return (
    <footer className="bg-gray-900 text-white mt-auto">
      <div className="container-custom py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div>
            <div className="flex items-center space-x-2 mb-4">
              <Car className="h-6 w-6 text-primary-400" />
              <span className="text-lg font-bold">Hanco AI</span>
            </div>
            <p className="text-gray-400 text-sm">
              AI-powered car rental service in Saudi Arabia.
            </p>
          </div>
          <div>
            <h3 className="font-semibold mb-4">Quick Links</h3>
            <ul className="space-y-2 text-sm">
              <li><Link to="/vehicles" className="text-gray-400 hover:text-white">Vehicles</Link></li>
              <li><Link to="/login" className="text-gray-400 hover:text-white">Login</Link></li>
            </ul>
          </div>
          <div>
            <h3 className="font-semibold mb-4">Contact</h3>
            <ul className="space-y-2 text-sm text-gray-400">
              <li className="flex items-center space-x-2">
                <Mail className="h-4 w-4" /><span>info@hanco.ai</span>
              </li>
              <li className="flex items-center space-x-2">
                <Phone className="h-4 w-4" /><span>+966 50 123 4567</span>
              </li>
            </ul>
          </div>
          <div>
            <h3 className="font-semibold mb-4">Cities</h3>
            <ul className="space-y-2 text-sm text-gray-400">
              <li>Riyadh</li><li>Jeddah</li><li>Dammam</li>
            </ul>
          </div>
        </div>
        <div className="border-t border-gray-800 mt-8 pt-8 text-center text-sm text-gray-400">
          <p>&copy; {new Date().getFullYear()} Hanco AI. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
}
