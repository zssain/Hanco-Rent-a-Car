import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const DEMO_CREDENTIALS = [
  { role: 'Consumer', email: 'consumer@hanco.com', password: 'Consumer123!' },
  { role: 'Admin', email: 'admin@hanco.com', password: 'Admin123!' },
  { role: 'Business', email: 'business@hanco.com', password: 'Business123!' },
  { role: 'Support', email: 'support@hanco.com', password: 'Support123!' },
];

export function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleQuickLogin = async (demoEmail: string, demoPassword: string) => {
    setLoading(true);
    setError('');
    try {
      await login(demoEmail, demoPassword);
      navigate('/vehicles');
    } catch (err: any) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(email, password);
      navigate('/vehicles');
    } catch (err: any) {
      setError(err.message || 'Failed to login');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-lg p-10 w-full max-w-md">
        <div className="text-center mb-8">
          <img 
            src="/hanco-logo.jpg" 
            alt="Hanco Logo" 
            className="h-14 mx-auto mb-4"
            onError={(e) => {
              e.currentTarget.style.display = 'none';
              const fallback = e.currentTarget.nextElementSibling as HTMLElement;
              if (fallback) fallback.style.display = 'block';
            }}
          />
          <div style={{ display: 'none' }} className="mb-4">
            <div className="inline-block">
              <svg width="120" height="50" viewBox="0 0 120 50" className="mx-auto">
                <rect x="10" y="10" width="30" height="30" fill="#B91C1C" rx="4"/>
                <text x="50" y="28" fontFamily="Arial, sans-serif" fontSize="24" fontWeight="bold" fill="#B91C1C">HANCO</text>
                <text x="50" y="38" fontFamily="Arial, sans-serif" fontSize="10" fill="#6B7280">Rent a Car</text>
              </svg>
            </div>
          </div>
          <h1 className="text-2xl font-bold text-gray-800 mb-1">HANCO</h1>
          <p className="text-sm text-gray-500">Rent a Car</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 mb-6">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded text-sm">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-2.5 border border-gray-300 rounded focus:ring-2 focus:ring-red-500 focus:border-transparent text-gray-900"
              placeholder="Enter your email"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2.5 border border-gray-300 rounded focus:ring-2 focus:ring-red-500 focus:border-transparent text-gray-900"
              placeholder="Enter your password"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-red-700 text-white py-3 rounded font-semibold hover:bg-red-800 transition-colors disabled:opacity-50"
          >
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>

        <div className="mb-6">
          <p className="text-xs text-gray-500 mb-3 text-center">Quick Login:</p>
          <div className="grid grid-cols-2 gap-2">
            {DEMO_CREDENTIALS.map((cred) => (
              <button
                key={cred.role}
                onClick={() => handleQuickLogin(cred.email, cred.password)}
                disabled={loading}
                className="px-3 py-2 bg-gray-100 text-gray-700 rounded text-sm font-medium hover:bg-gray-200 transition-colors disabled:opacity-50 border border-gray-300"
              >
                {cred.role}
              </button>
            ))}
          </div>
        </div>

        <div className="pt-4 border-t border-gray-200 text-center text-xs text-gray-500">
          <p>Demo Environment - Click any role above to auto-fill credentials</p>
        </div>
      </div>
    </div>
  );
}
