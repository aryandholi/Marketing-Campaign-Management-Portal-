"use client";
import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Save, Play, Clock, Loader2, Mail, Phone, Info } from 'lucide-react';
import Link from 'next/link';
import { apiClient } from '@/lib/api';

export default function NewCampaignPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [contacts, setContacts] = useState<any[]>([]);

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    channel: 'email',
    message_template: '',
    target_audience: '',
    schedule_time: '',
  });

  useEffect(() => {
    // Load contacts to show available audience options
    apiClient.get('/contacts')
      .then(res => setContacts(res.data.contacts || []))
      .catch(() => {});
  }, []);

  const set = (field: string, val: string) => setFormData(f => ({ ...f, [field]: val }));

  const handleSubmit = async (e: React.FormEvent, startAfter = false) => {
    e.preventDefault();
    if (!formData.name.trim()) { setError('Campaign name is required'); return; }
    if (!formData.message_template.trim()) { setError('Message template is required'); return; }
    setLoading(true);
    setError('');
    try {
      const payload: any = {
        name: formData.name,
        description: formData.description || null,
        channel: formData.channel,
        message_template: formData.message_template,
        target_audience: formData.target_audience || null,
        schedule_time: formData.schedule_time
          ? new Date(formData.schedule_time).toISOString()
          : null,
      };
      const res = await apiClient.post('/campaigns', payload);
      const campaignId = res.data.id;

      if (startAfter) {
        await apiClient.post(`/campaigns/${campaignId}/start`);
      }
      router.push(`/campaigns/${campaignId}`);
    } catch (err: any) {
      const msg = err?.response?.data?.error?.message || 'Failed to create campaign';
      setError(msg);
      setLoading(false);
    }
  };

  // Quick-fill audience with all contacts of the selected channel type
  const fillAudience = () => {
    const field = formData.channel === 'email' ? 'email' : 'phone';
    const addresses = contacts
      .filter(c => c[field])
      .map(c => c[field])
      .join(', ');
    if (addresses) set('target_audience', addresses);
  };

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center gap-4 mb-6">
        <Link href="/campaigns" className="p-2 hover:bg-white/10 rounded-lg transition-colors text-white/70 hover:text-white">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div>
          <h2 className="text-2xl font-semibold">Create Campaign</h2>
          <p className="text-sm text-white/50">Set up a new marketing outreach effort.</p>
        </div>
      </div>

      {error && (
        <div className="mb-4 bg-red-500/10 border border-red-500/30 text-red-400 rounded-xl px-5 py-3 text-sm">{error}</div>
      )}

      <form className="glassmorphism rounded-2xl border border-white/10 p-8 space-y-6">

        {/* Row 1: Name + Channel */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-white/70 mb-1.5">Campaign Name *</label>
            <input
              type="text" required
              value={formData.name}
              onChange={e => set('name', e.target.value)}
              placeholder="e.g. Summer Sale 2024"
              className="w-full px-4 py-2.5 bg-black/40 border border-white/10 rounded-xl text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-white/70 mb-1.5">Channel *</label>
            <select
              value={formData.channel}
              onChange={e => set('channel', e.target.value)}
              className="w-full px-4 py-2.5 bg-black/40 border border-white/10 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/50 appearance-none"
            >
              <option value="email">📧 Email</option>
              <option value="sms">📱 SMS</option>
            </select>
          </div>
        </div>

        {/* Description */}
        <div>
          <label className="block text-sm font-medium text-white/70 mb-1.5">Description</label>
          <textarea
            rows={2}
            value={formData.description}
            onChange={e => set('description', e.target.value)}
            placeholder="Internal notes about campaign objectives..."
            className="w-full px-4 py-2.5 bg-black/40 border border-white/10 rounded-xl text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
          />
        </div>

        {/* Target Audience */}
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label className="block text-sm font-medium text-white/70">Target Audience</label>
            {contacts.length > 0 && (
              <button
                type="button"
                onClick={fillAudience}
                className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors flex items-center gap-1"
              >
                {formData.channel === 'email' ? <Mail className="w-3 h-3" /> : <Phone className="w-3 h-3" />}
                Fill all {formData.channel} contacts ({contacts.filter(c => c[formData.channel === 'email' ? 'email' : 'phone']).length})
              </button>
            )}
          </div>
          <textarea
            rows={3}
            value={formData.target_audience}
            onChange={e => set('target_audience', e.target.value)}
            placeholder={formData.channel === 'email'
              ? "yourname@gmail.com, friend@example.com, alice@example.com..."
              : "+1-555-0101, +1-555-0102..."
            }
            className="w-full px-4 py-2.5 bg-black/40 border border-white/10 rounded-xl text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
          />
          <div className="mt-2 bg-indigo-500/5 border border-indigo-500/15 rounded-xl px-4 py-3">
            <div className="flex items-start gap-2">
              <Info className="w-3.5 h-3.5 text-indigo-400 mt-0.5 flex-shrink-0" />
              <div className="text-xs text-indigo-300/80 space-y-1">
                <p>Comma-separated emails, phone numbers, or usernames.</p>
                {formData.channel === 'email' && (
                  <p>
                    <strong>Real email:</strong> Enter any real email address (e.g. <span className="font-mono">yourname@gmail.com</span>).
                    If not already a contact, <Link href="/audiences" className="underline hover:text-indigo-200">add them in Audiences</Link> first.
                    Requires SMTP configured in <Link href="/settings" className="underline hover:text-indigo-200">Settings</Link>.
                  </p>
                )}
                {contacts.length > 0 && (
                  <p>
                    <strong>Pre-seeded contacts:</strong>{' '}
                    {contacts.slice(0, 5).map(c => (
                      <span
                        key={c.id}
                        onClick={() => set('target_audience', formData.target_audience ? `${formData.target_audience}, ${formData.channel === 'email' ? c.email : c.phone || c.email}` : (formData.channel === 'email' ? c.email : c.phone || c.email))}
                        className="text-indigo-400 cursor-pointer hover:text-indigo-300 mr-2 underline-offset-2 hover:underline"
                      >
                        {formData.channel === 'email' ? c.email : (c.phone || c.email)}
                      </span>
                    ))}
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Message Template */}
        <div>
          <label className="block text-sm font-medium text-white/70 mb-1.5">Message Template *</label>
          <div className="bg-black/20 rounded-xl border border-white/10 overflow-hidden">
            <div className="flex items-center gap-2 px-3 py-2 border-b border-white/5 bg-white/2">
              <span className="text-[10px] uppercase font-bold text-white/40 tracking-wider">Template Editor</span>
              <span className="ml-auto text-[10px] text-white/25">tokens: {'{{first_name}}'} {'{{last_name}}'} {'{{email}}'} {'{{phone}}'}</span>
            </div>
            <textarea
              rows={6}
              required
              value={formData.message_template}
              onChange={e => set('message_template', e.target.value)}
              placeholder={formData.channel === 'email'
                ? "Hello {{first_name}},\n\nWe have a special offer just for you...\n\nBest regards,\nThe Nexus Team"
                : "Hi {{first_name}}! Flash sale ends in 2h. Use code SAVE20. Reply STOP to opt out."}
              className="w-full bg-transparent p-4 text-white placeholder-white/30 focus:outline-none font-mono text-sm resize-y"
            />
          </div>
        </div>

        {/* Schedule Time */}
        <div>
          <label className="block text-sm font-medium text-white/70 mb-1.5 flex items-center gap-1.5">
            <Clock className="w-4 h-4 text-blue-400" /> Schedule Time (optional)
          </label>
          <input
            type="datetime-local"
            value={formData.schedule_time}
            onChange={e => set('schedule_time', e.target.value)}
            className="w-full px-4 py-2.5 bg-black/40 border border-white/10 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/50 [color-scheme:dark]"
          />
          <p className="text-xs text-white/40 mt-1">Leave blank to trigger manually via the Dispatch button after starting.</p>
        </div>

        {/* Actions */}
        <div className="pt-4 border-t border-white/10 flex items-center justify-end gap-3">
          <button
            type="button" disabled={loading}
            onClick={(e) => handleSubmit(e, false)}
            className="px-5 py-2.5 rounded-xl border border-white/10 hover:bg-white/5 font-medium transition-colors flex items-center gap-2 disabled:opacity-50"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4 text-white/70" />}
            Save as Draft
          </button>
          <button
            type="button" disabled={loading}
            onClick={(e) => handleSubmit(e, true)}
            className="px-5 py-2.5 rounded-xl bg-indigo-500 hover:bg-indigo-400 font-semibold text-white transition-colors flex items-center gap-2 shadow-[0_0_15px_rgba(99,102,241,0.4)] disabled:opacity-50"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            Create & Start
          </button>
        </div>
      </form>
    </div>
  );
}
