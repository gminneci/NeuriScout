'use client';

import { signIn } from 'next-auth/react';
import { useSearchParams } from 'next/navigation';
import { useState, Suspense } from 'react';
import { ALLOWED_DOMAINS } from '@/config/allowedDomains';

function SignInForm() {
  const searchParams = useSearchParams();
  const callbackUrl = searchParams.get('callbackUrl') || '/';
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    
    setIsLoading(true);
    setError('');
    
    const result = await signIn('credentials', { 
      email, 
      callbackUrl,
      redirect: false 
    });
    
    if (result?.error) {
      setError('Access denied. Only authorized email domains are allowed.');
      setIsLoading(false);
    } else if (result?.ok) {
      window.location.href = callbackUrl;
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#22367a]">
      <div className="bg-white p-8 rounded-lg shadow-2xl max-w-md w-full">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            NeuriScout
          </h1>
          <p className="text-gray-600">
            Navigate NeurIPS 2025 Papers
          </p>
          <p className="text-xs text-gray-400 mt-2">
            Powered by <span className="font-semibold text-gray-700">Fractile</span>
          </p>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <p className="text-sm text-gray-600 text-center mb-6">
            Enter your email to continue
          </p>
          
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
              {error}
            </div>
          )}
          
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
              Email Address
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="your@email.com"
              required
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          
          <button
            type="submit"
            disabled={isLoading || !email}
            className="w-full bg-[#f26954] text-white rounded-lg px-6 py-3 font-medium hover:bg-[#ff7a63] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Signing in...' : 'Continue'}
          </button>
        </form>
        
        <p className="text-xs text-gray-500 text-center mt-6">
          Allowed domains: {ALLOWED_DOMAINS.join(', ')}
        </p>
      </div>
    </div>
  );
}

export default function SignIn() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-[#22367a]">
        <div className="text-white">Loading...</div>
      </div>
    }>
      <SignInForm />
    </Suspense>
  );
}
