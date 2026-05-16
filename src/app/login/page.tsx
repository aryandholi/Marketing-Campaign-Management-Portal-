"use client";
import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Megaphone, Mail, Lock, Loader2, AlertCircle } from 'lucide-react';
import { GoogleLogin } from '@react-oauth/google';
import { apiClient } from '@/lib/api';

export default function LoginPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Email / password form state
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  React.useEffect(() => {
    if (localStorage.getItem('token')) {
      router.push('/dashboard');
    }
  }, [router]);

  // ── Google OAuth ────────────────────────────────────────────────────────
  const handleGoogleSuccess = async (credentialResponse: any) => {
    setLoading(true);
    setError('');
    try {
      const res = await apiClient.post('/auth/google', {
        credential: credentialResponse.credential,
      });
      localStorage.setItem('token', res.data.access_token);
      router.push('/dashboard');
    } catch {
      setError('Google authentication failed. Is the backend running?');
    } finally {
      setLoading(false);
    }
  };

  // ── Email / Password ────────────────────────────────────────────────────
  const handleEmailLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const res = await apiClient.post('/auth/login', { email, password });
      localStorage.setItem('token', res.data.access_token);
      router.push('/dashboard');
    } catch (err: any) {
      const msg = err?.response?.data?.detail || 'Invalid credentials. Please try again.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#050505] flex items-center justify-center relative overflow-hidden">
      {/* Ambient background */}
      <div className="absolute top-[10%] left-[20%] w-[60%] h-[60%] bg-indigo-900/20 blur-[150px] rounded-full pointer-events-none" />
      <div className="absolute bottom-[10%] right-[20%] w-[50%] h-[50%] bg-purple-900/20 blur-[150px] rounded-full pointer-events-none" />

      <div className="w-full max-w-md relative z-10 px-4">
        {/* Logo / Title */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 mx-auto rounded-2xl bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center shadow-[0_0_40px_rgba(99,102,241,0.4)] mb-6">
            <Megaphone className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Welcome to Nexus</h1>
          <p className="text-white/50">Sign in to your campaign portal</p>
        </div>

        <div className="glassmorphism p-8 rounded-2xl border border-white/10 shadow-2xl space-y-6">

          {/* Error Banner */}
          {error && (
            <div className="flex items-center gap-2 bg-red-500/10 border border-red-500/30 text-red-400 rounded-xl px-4 py-3 text-sm">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              {error}
            </div>
          )}

          {loading ? (
            <div className="flex flex-col items-center py-8">
              <div className="w-8 h-8 border-4 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin mb-4" />
              <p className="text-white/50 text-sm">Authenticating...</p>
            </div>
          ) : (
            <>
              {/* Email / Password Form */}
              <form onSubmit={handleEmailLogin} className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-white/60 mb-1.5 uppercase tracking-wider">
                    Email
                  </label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
                    <input
                      id="email"
                      type="email"
                      required
                      value={email}
                      onChange={e => setEmail(e.target.value)}
                      placeholder="admin@campaignportal.io"
                      className="w-full pl-10 pr-4 py-2.5 bg-black/40 border border-white/10 rounded-xl text-white placeholder-white/25 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all text-sm"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-medium text-white/60 mb-1.5 uppercase tracking-wider">
                    Password
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
                    <input
                      id="password"
                      type="password"
                      required
                      value={password}
                      onChange={e => setPassword(e.target.value)}
                      placeholder="Any non-empty password"
                      className="w-full pl-10 pr-4 py-2.5 bg-black/40 border border-white/10 rounded-xl text-white placeholder-white/25 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all text-sm"
                    />
                  </div>
                </div>
                <button
                  type="submit"
                  className="w-full py-2.5 bg-indigo-500 hover:bg-indigo-400 text-white font-semibold rounded-xl transition-all shadow-[0_0_15px_rgba(99,102,241,0.4)] flex items-center justify-center gap-2"
                >
                  <Loader2 className="w-4 h-4 hidden" />
                  Sign In
                </button>
              </form>

              {/* Divider */}
              <div className="relative flex items-center gap-3">
                <div className="flex-1 h-px bg-white/10" />
                <span className="text-xs text-white/30 font-medium uppercase tracking-wider">or continue with</span>
                <div className="flex-1 h-px bg-white/10" />
              </div>

              {/* Google Login */}
              <div className="flex justify-center">
                <GoogleLogin
                  onSuccess={handleGoogleSuccess}
                  onError={() => setError('Google Login Failed. Check that Google OAuth is configured.')}
                  theme="filled_black"
                  shape="rectangular"
                  text="signin_with"
                  size="large"
                />
              </div>

              {/* Demo Hint */}
              <div className="bg-indigo-500/5 border border-indigo-500/20 rounded-xl px-4 py-3">
                <p className="text-xs text-indigo-300/80 font-medium mb-1">Demo Credentials</p>
                <p className="text-xs text-white/40">
                  Email: <span className="text-white/70 font-mono">admin@campaignportal.io</span><br />
                  Password: <span className="text-white/70 font-mono">any non-empty value</span>
                </p>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
