"use client";
import React, { useEffect, useState } from 'react';
import { Settings, Bell, Shield, User, Check, Mail, Phone, AlertCircle, Loader2, CheckCircle2, XCircle, Zap } from 'lucide-react';
import { apiClient } from '@/lib/api';

interface ChannelStatus {
  email_configured: boolean;
  sms_configured: boolean;
  email_provider: string;
  sms_provider: string;
}

export default function SettingsPage() {
  const [saved, setSaved] = useState(false);
  const [emailNotifs, setEmailNotifs] = useState(true);
  const [smsNotifs, setSmsNotifs] = useState(false);
  const [channelStatus, setChannelStatus] = useState<ChannelStatus | null>(null);
  const [smtpLoading, setSmtpLoading] = useState(false);
  const [smtpError, setSmtpError] = useState('');
  const [smtpSuccess, setSmtpSuccess] = useState('');
  const [twilioLoading, setTwilioLoading] = useState(false);
  const [twilioError, setTwilioError] = useState('');
  const [twilioSuccess, setTwilioSuccess] = useState('');

  const [smtp, setSmtp] = useState({
    smtp_host: '',
    smtp_port: 587,
    smtp_username: '',
    smtp_password: '',
    smtp_from_email: '',
    smtp_from_name: 'Nexus Portal',
    smtp_use_tls: true,
  });

  const [twilio, setTwilio] = useState({
    twilio_account_sid: '',
    twilio_auth_token: '',
    twilio_from_number: '',
  });

  useEffect(() => {
    apiClient.get('/settings/channels/status')
      .then(res => setChannelStatus(res.data))
      .catch(() => {});
  }, []);

  const handleSaveSmtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setSmtpLoading(true);
    setSmtpError('');
    setSmtpSuccess('');
    try {
      await apiClient.post('/settings/smtp', smtp);
      setSmtpSuccess('SMTP settings saved! Campaigns will now send real emails.');
      // Refresh status
      const statusRes = await apiClient.get('/settings/channels/status');
      setChannelStatus(statusRes.data);
    } catch (err: any) {
      setSmtpError(err?.response?.data?.detail || err?.response?.data?.error?.message || 'Failed to save SMTP settings');
    } finally {
      setSmtpLoading(false);
    }
  };

  const handleSaveTwilio = async (e: React.FormEvent) => {
    e.preventDefault();
    setTwilioLoading(true);
    setTwilioError('');
    setTwilioSuccess('');
    try {
      await apiClient.post('/settings/twilio', twilio);
      setTwilioSuccess('Twilio settings saved! Campaigns will now send real SMS messages.');
      const statusRes = await apiClient.get('/settings/channels/status');
      setChannelStatus(statusRes.data);
    } catch (err: any) {
      setTwilioError(err?.response?.data?.detail || err?.response?.data?.error?.message || 'Failed to save Twilio settings');
    } finally {
      setTwilioLoading(false);
    }
  };

  const handleSaveWorkspace = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  const ProviderBadge = ({ configured, provider }: { configured: boolean; provider: string }) => (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${
      configured
        ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
        : 'bg-amber-500/10 border-amber-500/20 text-amber-400'
    }`}>
      {configured ? <CheckCircle2 className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
      {configured ? `Live (${provider})` : 'Mock / Simulation'}
    </span>
  );

  return (
    <div className="space-y-8 max-w-3xl">

      {/* ── Channel Status Overview ──────────────────────────────────── */}
      {channelStatus && (
        <div className="glassmorphism rounded-2xl border border-white/10 p-6">
          <div className="flex items-center gap-3 mb-4 pb-4 border-b border-white/5">
            <Zap className="w-5 h-5 text-yellow-400" />
            <h3 className="font-semibold text-lg text-white">Channel Status</h3>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="flex items-center justify-between bg-white/5 rounded-xl px-4 py-3 border border-white/5">
              <div className="flex items-center gap-2">
                <Mail className="w-4 h-4 text-indigo-400" />
                <span className="text-sm font-medium">Email</span>
              </div>
              <ProviderBadge configured={channelStatus.email_configured} provider={channelStatus.email_provider} />
            </div>
            <div className="flex items-center justify-between bg-white/5 rounded-xl px-4 py-3 border border-white/5">
              <div className="flex items-center gap-2">
                <Phone className="w-4 h-4 text-emerald-400" />
                <span className="text-sm font-medium">SMS</span>
              </div>
              <ProviderBadge configured={channelStatus.sms_configured} provider={channelStatus.sms_provider} />
            </div>
          </div>
          {(!channelStatus.email_configured || !channelStatus.sms_configured) && (
            <p className="text-xs text-amber-400/80 mt-3 bg-amber-500/5 border border-amber-500/10 rounded-lg px-3 py-2">
              ⚡ Configure credentials below to send real messages. Without them, campaigns run in simulation mode.
            </p>
          )}
        </div>
      )}

      {/* ── Workspace ──────────────────────────────────── */}
      <div className="glassmorphism rounded-2xl border border-white/10 p-6">
        <div className="flex items-center gap-3 mb-6 pb-4 border-b border-white/5">
          <User className="w-5 h-5 text-indigo-400" />
          <h3 className="font-semibold text-lg text-white">Workspace</h3>
        </div>
        <div className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-white/70 mb-1.5">Workspace Name</label>
            <input
              type="text"
              defaultValue="Nexus Portal"
              className="w-full px-4 py-2.5 bg-black/40 border border-white/10 rounded-xl text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-white/70 mb-1.5">Admin Email</label>
            <input
              type="email"
              defaultValue="admin@campaignportal.io"
              className="w-full px-4 py-2.5 bg-black/40 border border-white/10 rounded-xl text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
            />
          </div>
          <div className="flex justify-end">
            <button
              onClick={handleSaveWorkspace}
              className="flex items-center gap-2 px-5 py-2 bg-indigo-500 hover:bg-indigo-400 text-white font-semibold rounded-xl transition-all text-sm"
            >
              {saved ? <><Check className="w-4 h-4" /> Saved!</> : <><Settings className="w-4 h-4" /> Save Workspace</>}
            </button>
          </div>
        </div>
      </div>

      {/* ── Notifications ──────────────────────────────── */}
      <div className="glassmorphism rounded-2xl border border-white/10 p-6">
        <div className="flex items-center gap-3 mb-6 pb-4 border-b border-white/5">
          <Bell className="w-5 h-5 text-purple-400" />
          <h3 className="font-semibold text-lg text-white">Notifications</h3>
        </div>
        <div className="space-y-4">
          {[
            { label: 'Email delivery reports', description: 'Receive a summary when a campaign finishes sending.', value: emailNotifs, toggle: () => setEmailNotifs(v => !v) },
            { label: 'SMS dispatch alerts', description: 'Get notified of SMS delivery status in real-time.', value: smsNotifs, toggle: () => setSmsNotifs(v => !v) },
          ].map((item) => (
            <div key={item.label} className="flex items-center justify-between py-3 px-4 bg-white/3 rounded-xl border border-white/5">
              <div>
                <div className="text-sm font-medium text-white">{item.label}</div>
                <div className="text-xs text-white/40 mt-0.5">{item.description}</div>
              </div>
              <button
                onClick={item.toggle}
                className={`relative w-10 h-6 rounded-full transition-colors duration-200 ${item.value ? 'bg-indigo-500' : 'bg-white/10'}`}
              >
                <span className={`absolute top-1 left-1 w-4 h-4 bg-white rounded-full shadow transition-transform duration-200 ${item.value ? 'translate-x-4' : ''}`} />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* ── SMTP Email Configuration ────────────────────── */}
      <form onSubmit={handleSaveSmtp} className="glassmorphism rounded-2xl border border-white/10 p-6">
        <div className="flex items-center justify-between mb-6 pb-4 border-b border-white/5">
          <div className="flex items-center gap-3">
            <Mail className="w-5 h-5 text-blue-400" />
            <div>
              <h3 className="font-semibold text-lg text-white">SMTP Email Configuration</h3>
              <p className="text-xs text-white/40 mt-0.5">Configure to send real emails via any SMTP provider</p>
            </div>
          </div>
          {channelStatus && (
            <ProviderBadge configured={channelStatus.email_configured} provider={channelStatus.email_provider} />
          )}
        </div>

        {smtpError && (
          <div className="mb-4 flex items-center gap-2 bg-red-500/10 border border-red-500/30 text-red-400 rounded-xl px-4 py-3 text-sm">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            {smtpError}
          </div>
        )}
        {smtpSuccess && (
          <div className="mb-4 flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 rounded-xl px-4 py-3 text-sm">
            <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
            {smtpSuccess}
          </div>
        )}

        <div className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <div className="col-span-2">
              <label className="block text-sm font-medium text-white/70 mb-1.5">SMTP Host</label>
              <input
                type="text"
                value={smtp.smtp_host}
                onChange={e => setSmtp(s => ({ ...s, smtp_host: e.target.value }))}
                placeholder="smtp.gmail.com"
                className="w-full px-4 py-2.5 bg-black/40 border border-white/10 rounded-xl text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-white/70 mb-1.5">Port</label>
              <input
                type="number"
                value={smtp.smtp_port}
                onChange={e => setSmtp(s => ({ ...s, smtp_port: parseInt(e.target.value) || 587 }))}
                className="w-full px-4 py-2.5 bg-black/40 border border-white/10 rounded-xl text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 text-sm"
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-white/70 mb-1.5">SMTP Username</label>
              <input
                type="text"
                value={smtp.smtp_username}
                onChange={e => setSmtp(s => ({ ...s, smtp_username: e.target.value }))}
                placeholder="your@gmail.com"
                className="w-full px-4 py-2.5 bg-black/40 border border-white/10 rounded-xl text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-white/70 mb-1.5">SMTP Password / App Password</label>
              <input
                type="password"
                value={smtp.smtp_password}
                onChange={e => setSmtp(s => ({ ...s, smtp_password: e.target.value }))}
                placeholder="••••••••••••••••"
                className="w-full px-4 py-2.5 bg-black/40 border border-white/10 rounded-xl text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 text-sm"
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-white/70 mb-1.5">From Email</label>
              <input
                type="email"
                value={smtp.smtp_from_email}
                onChange={e => setSmtp(s => ({ ...s, smtp_from_email: e.target.value }))}
                placeholder="campaigns@yourdomain.com"
                className="w-full px-4 py-2.5 bg-black/40 border border-white/10 rounded-xl text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-white/70 mb-1.5">From Name</label>
              <input
                type="text"
                value={smtp.smtp_from_name}
                onChange={e => setSmtp(s => ({ ...s, smtp_from_name: e.target.value }))}
                placeholder="Nexus Portal"
                className="w-full px-4 py-2.5 bg-black/40 border border-white/10 rounded-xl text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 text-sm"
              />
            </div>
          </div>
          <div className="flex items-center gap-3 py-2">
            <input
              id="use-tls"
              type="checkbox"
              checked={smtp.smtp_use_tls}
              onChange={e => setSmtp(s => ({ ...s, smtp_use_tls: e.target.checked }))}
              className="w-4 h-4 rounded border-white/20 bg-black/40 text-indigo-500"
            />
            <label htmlFor="use-tls" className="text-sm text-white/70">Use STARTTLS (recommended for port 587)</label>
          </div>
          <div className="bg-blue-500/5 border border-blue-500/15 rounded-xl px-4 py-3 text-xs text-blue-300/80 space-y-1">
            <p className="font-semibold text-blue-300">Quick Setup Guide:</p>
            <p>• <strong>Gmail:</strong> Enable 2FA → generate an App Password at myaccount.google.com/apppasswords</p>
            <p>• <strong>SendGrid:</strong> Host: smtp.sendgrid.net / User: apikey / Password: your SG API key</p>
            <p>• <strong>Mailtrap:</strong> sandbox.smtp.mailtrap.io:2525 — safe testing without real delivery</p>
          </div>
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={smtpLoading}
              className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-semibold rounded-xl transition-all text-sm shadow-[0_0_15px_rgba(37,99,235,0.3)]"
            >
              {smtpLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Mail className="w-4 h-4" />}
              {smtpLoading ? 'Saving…' : 'Save SMTP Settings'}
            </button>
          </div>
        </div>
      </form>

      {/* ── Twilio SMS Configuration ────────────────────── */}
      <form onSubmit={handleSaveTwilio} className="glassmorphism rounded-2xl border border-white/10 p-6">
        <div className="flex items-center justify-between mb-6 pb-4 border-b border-white/5">
          <div className="flex items-center gap-3">
            <Phone className="w-5 h-5 text-emerald-400" />
            <div>
              <h3 className="font-semibold text-lg text-white">Twilio SMS Configuration</h3>
              <p className="text-xs text-white/40 mt-0.5">Configure to send real SMS messages via Twilio</p>
            </div>
          </div>
          {channelStatus && (
            <ProviderBadge configured={channelStatus.sms_configured} provider={channelStatus.sms_provider} />
          )}
        </div>

        {twilioError && (
          <div className="mb-4 flex items-center gap-2 bg-red-500/10 border border-red-500/30 text-red-400 rounded-xl px-4 py-3 text-sm">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            {twilioError}
          </div>
        )}
        {twilioSuccess && (
          <div className="mb-4 flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 rounded-xl px-4 py-3 text-sm">
            <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
            {twilioSuccess}
          </div>
        )}

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-white/70 mb-1.5">Account SID</label>
            <input
              type="text"
              value={twilio.twilio_account_sid}
              onChange={e => setTwilio(t => ({ ...t, twilio_account_sid: e.target.value }))}
              placeholder="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
              className="w-full px-4 py-2.5 bg-black/40 border border-white/10 rounded-xl text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 font-mono text-sm"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-white/70 mb-1.5">Auth Token</label>
            <input
              type="password"
              value={twilio.twilio_auth_token}
              onChange={e => setTwilio(t => ({ ...t, twilio_auth_token: e.target.value }))}
              placeholder="••••••••••••••••••••••••••••••••"
              className="w-full px-4 py-2.5 bg-black/40 border border-white/10 rounded-xl text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 text-sm"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-white/70 mb-1.5">From Phone Number</label>
            <input
              type="text"
              value={twilio.twilio_from_number}
              onChange={e => setTwilio(t => ({ ...t, twilio_from_number: e.target.value }))}
              placeholder="+1xxxxxxxxxx (E.164 format)"
              className="w-full px-4 py-2.5 bg-black/40 border border-white/10 rounded-xl text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 font-mono text-sm"
            />
          </div>
          <div className="bg-emerald-500/5 border border-emerald-500/15 rounded-xl px-4 py-3 text-xs text-emerald-300/80">
            <p className="font-semibold text-emerald-300 mb-1">Setup: console.twilio.com</p>
            <p>Get your SID and Auth Token from the Twilio Console dashboard. Use a verified or purchased Twilio number as the from number.</p>
          </div>
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={twilioLoading}
              className="flex items-center gap-2 px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-semibold rounded-xl transition-all text-sm shadow-[0_0_15px_rgba(16,185,129,0.3)]"
            >
              {twilioLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Phone className="w-4 h-4" />}
              {twilioLoading ? 'Saving…' : 'Save Twilio Settings'}
            </button>
          </div>
        </div>
      </form>

    </div>
  );
}
