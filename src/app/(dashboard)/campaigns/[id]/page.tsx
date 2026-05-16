"use client";
import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { ArrowLeft, Play, Pause, Square, BarChart3, Users, Mail, Settings, RefreshCw, Send, Eye, MousePointerClick, MessageSquare, Pencil, Clock, Reply } from 'lucide-react';
import { apiClient } from '@/lib/api';

const statusColors: any = {
  'draft':     'bg-gray-500/20 text-gray-400 border-gray-500/30',
  'scheduled': 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  'active':    'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  'paused':    'bg-amber-500/20 text-amber-400 border-amber-500/30',
  'completed': 'bg-purple-500/20 text-purple-400 border-purple-500/30',
  'stopped':   'bg-red-500/20 text-red-400 border-red-500/30',
};

export default function CampaignDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = React.use(params);
  const { id } = resolvedParams;

  const [campaign, setCampaign]     = useState<any>(null);
  const [metrics, setMetrics]       = useState<any>(null);
  const [events, setEvents]         = useState<any[]>([]);
  const [loading, setLoading]       = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  const fetchData = async () => {
    try {
      const [campRes, metRes, evtRes] = await Promise.all([
        apiClient.get(`/campaigns/${id}`),
        apiClient.get(`/reports/campaigns/${id}`).catch(() => ({ data: {} })),
        apiClient.get(`/reports/campaigns/${id}/events`).catch(() => ({ data: { events: [] } })),
      ]);
      setCampaign(campRes.data);
      setMetrics(metRes.data);
      setEvents(evtRes.data?.events || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [id]);

  const handleAction = async (action: string) => {
    setActionLoading(true);
    try {
      if      (action === 'start')  await apiClient.post(`/campaigns/${id}/start`);
      else if (action === 'pause')  await apiClient.post(`/campaigns/${id}/pause`);
      else if (action === 'resume') await apiClient.post(`/campaigns/${id}/resume`);
      else if (action === 'stop')   await apiClient.post(`/campaigns/${id}/stop`);
      else if (action === 'send') {
        await apiClient.post(`/campaigns/${id}/send`, { recipient_identifiers: null });
        alert('Messages dispatched successfully!');
      }
      await fetchData();
    } catch (err: any) {
      const msg = err?.response?.data?.error?.message || `Failed to execute ${action}`;
      alert(msg);
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) return <div className="text-white/50 text-center py-20 animate-pulse">Loading Campaign...</div>;
  if (!campaign) return <div className="text-white/50 text-center py-20">Campaign not found.</div>;

  const status = campaign.status;
  const isDraft = status === 'draft';

  return (
    <div className="space-y-6">
      {/* ── Header ─────────────────────────────────── */}
      <div className="flex items-start justify-between mb-8">
        <div className="flex items-center gap-4">
          <Link href="/campaigns" className="p-2 hover:bg-white/10 rounded-lg transition-colors text-white/70 hover:text-white">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-3xl font-bold tracking-tight">{campaign.name}</h1>
              <span className={`px-2.5 py-1 text-xs font-bold tracking-wider uppercase rounded-md border ${statusColors[status]}`}>
                {status}
              </span>
            </div>
            <p className="text-white/50">{campaign.description || 'No description provided.'}</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Edit — only in draft */}
          {isDraft && (
            <Link
              href={`/campaigns/${id}/edit`}
              className="flex items-center gap-2 bg-white/5 hover:bg-white/10 border border-white/10 text-white/70 px-4 py-2 rounded-xl transition-all font-medium text-sm"
            >
              <Pencil className="w-4 h-4" /> Edit
            </Link>
          )}
          {/* Start draft */}
          {isDraft && (
            <button onClick={() => handleAction('start')} disabled={actionLoading}
              className="flex items-center gap-2 bg-emerald-500 hover:bg-emerald-400 text-white px-4 py-2 rounded-xl transition-all font-medium shadow-[0_0_15px_rgba(16,185,129,0.3)]">
              <Play className="w-4 h-4" /> Start Campaign
            </button>
          )}
          {/* Active → send + pause */}
          {status === 'active' && (<>
            <button onClick={() => handleAction('send')} disabled={actionLoading}
              className="flex items-center gap-2 bg-indigo-500 hover:bg-indigo-400 text-white px-4 py-2 rounded-xl transition-all font-medium shadow-[0_0_15px_rgba(99,102,241,0.3)]">
              <Send className="w-4 h-4" /> Dispatch Messages
            </button>
            <button onClick={() => handleAction('pause')} disabled={actionLoading}
              className="flex items-center gap-2 bg-amber-500/20 hover:bg-amber-500/30 border border-amber-500/50 text-amber-400 px-4 py-2 rounded-xl transition-all font-medium">
              <Pause className="w-4 h-4" /> Pause
            </button>
          </>)}
          {/* Paused → resume */}
          {status === 'paused' && (
            <button onClick={() => handleAction('resume')} disabled={actionLoading}
              className="flex items-center gap-2 bg-emerald-500 hover:bg-emerald-400 text-white px-4 py-2 rounded-xl transition-all font-medium shadow-[0_0_15px_rgba(16,185,129,0.3)]">
              <Play className="w-4 h-4" /> Resume
            </button>
          )}
          {/* Active or Paused → stop */}
          {(status === 'active' || status === 'paused') && (
            <button onClick={() => handleAction('stop')} disabled={actionLoading}
              className="flex items-center gap-2 bg-red-500/20 hover:bg-red-500/30 border border-red-500/50 text-red-400 px-4 py-2 rounded-xl transition-all font-medium">
              <Square className="w-4 h-4" /> Stop
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* ── Config Panel ──────────────────────────── */}
        <div className="space-y-6">
          <div className="glassmorphism rounded-2xl border border-white/10 p-6">
            <div className="flex items-center gap-3 mb-6 pb-4 border-b border-white/5">
              <Settings className="w-5 h-5 text-indigo-400" />
              <h3 className="font-semibold text-lg">Configuration</h3>
            </div>
            <div className="space-y-5 text-sm">
              <div>
                <label className="text-white/40 block mb-1">Channel</label>
                <span className="font-medium bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 px-3 py-1 rounded-lg uppercase text-xs font-bold tracking-wider">{campaign.channel}</span>
              </div>
              <div>
                <label className="text-white/40 block mb-1">Created</label>
                <p className="font-medium text-white/80">{new Date(campaign.created_at).toLocaleString()}</p>
              </div>
              {campaign.schedule_time && (
                <div>
                  <label className="text-white/40 block mb-1 flex items-center gap-1"><Clock className="w-3 h-3" /> Scheduled Send</label>
                  <p className="font-medium text-blue-300">{new Date(campaign.schedule_time).toLocaleString()}</p>
                </div>
              )}
              <div>
                <label className="text-white/40 block mb-1.5">Target Audience</label>
                <div className="bg-black/30 rounded-lg border border-white/5 p-3 text-xs font-mono text-white/70 break-all leading-relaxed">
                  {campaign.target_audience || <span className="italic text-white/30">No audience specified</span>}
                </div>
              </div>
              <div>
                <label className="text-white/40 block mb-1.5">Message Template</label>
                <div className="bg-black/50 border border-white/10 rounded-lg p-3 font-mono text-xs text-white/70 whitespace-pre-wrap leading-relaxed">
                  {campaign.message_template}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* ── Metrics + Feed ────────────────────────── */}
        <div className="lg:col-span-2 space-y-6">
          {/* Delivery metrics */}
          <div className="glassmorphism rounded-2xl border border-white/10 p-6">
            <div className="flex items-center justify-between mb-6 pb-4 border-b border-white/5">
              <div className="flex items-center gap-3">
                <BarChart3 className="w-5 h-5 text-emerald-400" />
                <h3 className="font-semibold text-lg">Delivery Analytics</h3>
              </div>
              <button onClick={fetchData} className="text-white/50 hover:text-white transition-colors p-1 rounded hover:bg-white/10">
                <RefreshCw className="w-4 h-4" />
              </button>
            </div>

            {/* Row 1: Volume counts */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-4">
              {[
                { label: 'Recipients', value: metrics?.total_recipients ?? 0, icon: Users, color: 'text-white/70' },
                { label: 'Sent',       value: metrics?.total_sent ?? 0,       icon: Mail,  color: 'text-indigo-400' },
                { label: 'Delivered',  value: metrics?.total_delivered ?? 0,  icon: Play,  color: 'text-emerald-400' },
                { label: 'Failed',     value: metrics?.total_failed ?? 0,     icon: Square, color: 'text-red-400' },
              ].map(s => (
                <div key={s.label} className="bg-white/5 rounded-xl p-4 border border-white/5">
                  <span className={`text-xs font-semibold uppercase tracking-wider mb-2 flex items-center gap-1.5 ${s.color}`}>
                    <s.icon className="w-3 h-3" /> {s.label}
                  </span>
                  <span className="text-3xl font-bold text-white">{s.value}</span>
                </div>
              ))}
            </div>

            {/* Row 2: Engagement counts */}
            <div className="grid grid-cols-3 gap-4 mb-4">
              {[
                { label: 'Opened / Read', value: metrics?.total_opened   ?? 0, icon: Eye,            color: 'text-purple-400' },
                { label: 'Replied',       value: metrics?.total_replied  ?? 0, icon: Reply,          color: 'text-amber-400' },
                { label: 'Clicked',       value: metrics?.total_clicked  ?? 0, icon: MousePointerClick, color: 'text-blue-400' },
              ].map(s => (
                <div key={s.label} className="bg-white/5 rounded-xl p-4 border border-white/5">
                  <span className={`text-xs font-semibold uppercase tracking-wider mb-2 flex items-center gap-1.5 ${s.color}`}>
                    <s.icon className="w-3 h-3" /> {s.label}
                  </span>
                  <span className="text-3xl font-bold text-white">{s.value}</span>
                </div>
              ))}
            </div>

            {/* Row 3: Rates */}
            <div className="grid grid-cols-3 gap-4">
              {[
                { label: 'Delivery Rate', value: metrics?.delivery_rate ?? 0, color: 'text-emerald-400' },
                { label: 'Open Rate',     value: metrics?.open_rate     ?? 0, color: 'text-purple-400'  },
                { label: 'Click Rate',    value: metrics?.click_rate    ?? 0, color: 'text-blue-400'    },
              ].map(s => (
                <div key={s.label} className="bg-white/5 rounded-xl p-4 border border-white/5 text-center">
                  <div className="text-xs text-white/50 uppercase tracking-wider mb-1">{s.label}</div>
                  <div className={`text-2xl font-semibold ${s.color}`}>{s.value.toFixed(1)}%</div>
                  <div className="h-1.5 w-full bg-white/5 rounded-full mt-2 overflow-hidden">
                    <div className={`h-full rounded-full bg-current opacity-60`} style={{ width: `${Math.min(s.value, 100)}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Engagement Feed */}
          <div className="glassmorphism rounded-2xl border border-white/10 p-6">
            <div className="flex items-center gap-3 mb-4 pb-4 border-b border-white/5">
              <Eye className="w-5 h-5 text-purple-400" />
              <h3 className="font-semibold text-lg">Engagement Feed</h3>
              <span className="text-xs bg-purple-500/10 border border-purple-500/20 text-purple-400 px-2 py-0.5 rounded-full ml-auto">{events.length} events</span>
            </div>
            {events.length === 0 ? (
              <div className="bg-black/40 rounded-xl p-8 border border-white/5 text-center">
                <Eye className="w-10 h-10 mx-auto mb-3 text-white/10" />
                <p className="text-white/40 text-sm">No engagement events yet.</p>
                <p className="text-white/25 text-xs mt-1">Start & dispatch the campaign, then events will appear here.</p>
              </div>
            ) : (
              <div className="space-y-2 max-h-[320px] overflow-y-auto pr-1">
                {events.map((evt: any, idx: number) => {
                  const iconMap: any = {
                    opened:        { icon: Eye,              bg: 'bg-purple-500/20 text-purple-400' },
                    read:          { icon: Eye,              bg: 'bg-purple-500/20 text-purple-400' },
                    link_clicked:  { icon: MousePointerClick, bg: 'bg-blue-500/20 text-blue-400'   },
                    button_clicked:{ icon: MousePointerClick, bg: 'bg-blue-500/20 text-blue-400'   },
                    delivered:     { icon: Mail,             bg: 'bg-emerald-500/20 text-emerald-400' },
                    replied:       { icon: Reply,            bg: 'bg-amber-500/20 text-amber-400'  },
                    page_navigated:{ icon: MessageSquare,    bg: 'bg-cyan-500/20 text-cyan-400'    },
                  };
                  const meta = iconMap[evt.event_type] || { icon: MessageSquare, bg: 'bg-white/10 text-white/50' };
                  const IconComp = meta.icon;
                  return (
                    <div key={idx} className="flex items-center gap-3 bg-white/5 rounded-lg px-4 py-3 border border-white/5 text-sm hover:bg-white/8 transition-colors">
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${meta.bg}`}>
                        <IconComp className="w-4 h-4" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <span className="font-semibold uppercase text-xs tracking-wider">{evt.event_type.replace(/_/g, ' ')}</span>
                        <div className="text-xs text-white/40 truncate">msg: {evt.message_id?.slice(0, 12)}…</div>
                      </div>
                      <div className="text-xs text-white/30 flex-shrink-0">{evt.created_at ? new Date(evt.created_at).toLocaleTimeString() : ''}</div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
