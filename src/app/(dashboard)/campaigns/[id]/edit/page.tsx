"use client";
import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Save, Loader2 } from 'lucide-react';
import { apiClient } from '@/lib/api';

export default function EditCampaignPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = React.use(params);
  const { id } = resolvedParams;
  const router = useRouter();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    message_template: '',
    target_audience: '',
    schedule_time: '',
  });

  useEffect(() => {
    apiClient.get(`/campaigns/${id}`)
      .then(res => {
        const c = res.data;
        setFormData({
          name: c.name || '',
          description: c.description || '',
          message_template: c.message_template || '',
          target_audience: c.target_audience || '',
          schedule_time: c.schedule_time ? new Date(c.schedule_time).toISOString().slice(0, 16) : '',
        });
      })
      .catch(() => setError('Failed to load campaign'))
      .finally(() => setLoading(false));
  }, [id]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      const payload: any = {
        name: formData.name,
        description: formData.description || null,
        message_template: formData.message_template,
        target_audience: formData.target_audience || null,
        schedule_time: formData.schedule_time ? new Date(formData.schedule_time).toISOString() : null,
      };
      await apiClient.put(`/campaigns/${id}`, payload);
      router.push(`/campaigns/${id}`);
    } catch (err: any) {
      const msg = err?.response?.data?.error?.message || 'Failed to update campaign';
      setError(msg);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="text-white/50 text-center py-20 animate-pulse">Loading...</div>;

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center gap-4 mb-2">
        <Link href={`/campaigns/${id}`} className="p-2 hover:bg-white/10 rounded-lg transition-colors text-white/70 hover:text-white">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Edit Campaign</h1>
          <p className="text-white/50 text-sm mt-0.5">Only draft campaigns can be edited.</p>
        </div>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 text-red-400 rounded-xl px-5 py-4 text-sm">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="glassmorphism rounded-2xl border border-white/10 p-8 space-y-6">
        <div>
          <label className="block text-sm font-medium text-white/70 mb-1.5">Campaign Name *</label>
          <input
            required
            type="text"
            value={formData.name}
            onChange={e => setFormData({ ...formData, name: e.target.value })}
            className="w-full px-4 py-2.5 bg-black/40 border border-white/10 rounded-xl text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
            placeholder="e.g. Summer Sale Promo"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-white/70 mb-1.5">Description</label>
          <textarea
            rows={2}
            value={formData.description}
            onChange={e => setFormData({ ...formData, description: e.target.value })}
            className="w-full px-4 py-2.5 bg-black/40 border border-white/10 rounded-xl text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
            placeholder="Internal notes about campaign objectives..."
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-white/70 mb-1.5">Target Audience</label>
          <textarea
            rows={3}
            value={formData.target_audience}
            onChange={e => setFormData({ ...formData, target_audience: e.target.value })}
            className="w-full px-4 py-2.5 bg-black/40 border border-white/10 rounded-xl text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
            placeholder="Comma-separated: alice@example.com, +1-555-0101, bob_builder..."
          />
          <p className="text-xs text-white/40 mt-1">Emails, phone numbers, or usernames — comma separated.</p>
        </div>

        <div>
          <label className="block text-sm font-medium text-white/70 mb-1.5">Message Template *</label>
          <textarea
            required
            rows={5}
            value={formData.message_template}
            onChange={e => setFormData({ ...formData, message_template: e.target.value })}
            className="w-full px-4 py-2.5 bg-black/40 border border-white/10 rounded-xl text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 font-mono text-sm"
            placeholder="Hello {{first_name}}, your message here..."
          />
          <p className="text-xs text-white/40 mt-1">Available tokens: {'{{first_name}}'}, {'{{last_name}}'}, {'{{email}}'}, {'{{phone}}'}, {'{{username}}'}</p>
        </div>

        <div>
          <label className="block text-sm font-medium text-white/70 mb-1.5">Schedule Time (UTC)</label>
          <input
            type="datetime-local"
            value={formData.schedule_time}
            onChange={e => setFormData({ ...formData, schedule_time: e.target.value })}
            className="w-full px-4 py-2.5 bg-black/40 border border-white/10 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/50 [color-scheme:dark]"
          />
          <p className="text-xs text-white/40 mt-1">Optional — leave blank to trigger manually via Dispatch.</p>
        </div>

        <div className="flex justify-end gap-3 pt-2 border-t border-white/5">
          <Link
            href={`/campaigns/${id}`}
            className="px-5 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-white/70 transition-all text-sm font-medium"
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={saving}
            className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium transition-all shadow-[0_0_15px_rgba(99,102,241,0.4)]"
          >
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </form>
    </div>
  );
}
