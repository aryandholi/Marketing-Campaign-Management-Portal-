"use client";
import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { BarChart3, Send, CheckCircle2, XCircle, Eye, Reply, MousePointerClick, Users, TrendingUp, RefreshCw } from 'lucide-react';
import { apiClient } from '@/lib/api';

const statusColors: any = {
  draft: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
  active: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  paused: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  completed: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
  stopped: 'bg-red-500/20 text-red-400 border-red-500/30',
};

export default function PerformancePage() {
  const [summary, setSummary] = useState<any>(null);
  const [campaigns, setCampaigns] = useState<any[]>([]);
  const [metrics, setMetrics] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(true);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [sumRes, campRes] = await Promise.all([
        apiClient.get('/reports/campaigns/summary'),
        apiClient.get('/campaigns?limit=50'),
      ]);
      setSummary(sumRes.data);
      const camps: any[] = campRes.data?.campaigns || [];
      setCampaigns(camps);

      // Fetch per-campaign metrics in parallel
      const metricsEntries = await Promise.all(
        camps.map(async (c: any) => {
          const res = await apiClient.get(`/reports/campaigns/${c.id}`).catch(() => ({ data: {} }));
          return [c.id, res.data];
        })
      );
      setMetrics(Object.fromEntries(metricsEntries));
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAll(); }, []);

  const summaryCards = [
    { label: 'Total Campaigns', value: summary?.total_campaigns ?? 0, icon: BarChart3,        color: 'text-blue-400',    bg: 'bg-blue-500/10 border-blue-500/20' },
    { label: 'Total Sent',      value: summary?.total_sent ?? 0,      icon: Send,             color: 'text-indigo-400',  bg: 'bg-indigo-500/10 border-indigo-500/20' },
    { label: 'Delivered',       value: summary?.total_delivered ?? 0, icon: CheckCircle2,     color: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/20' },
    { label: 'Failed',          value: summary?.total_failed ?? 0,    icon: XCircle,          color: 'text-red-400',     bg: 'bg-red-500/10 border-red-500/20' },
    { label: 'Opened / Read',   value: summary?.total_opened ?? 0,    icon: Eye,              color: 'text-purple-400',  bg: 'bg-purple-500/10 border-purple-500/20' },
    { label: 'Clicked',         value: summary?.total_clicked ?? 0,   icon: MousePointerClick, color: 'text-cyan-400',   bg: 'bg-cyan-500/10 border-cyan-500/20' },
  ];

  return (
    <div className="space-y-8">

      {/* ── Aggregate Summary ─────────────────────── */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold">Aggregate Metrics</h3>
            <p className="text-sm text-white/50">Across all campaigns you own.</p>
          </div>
          <button onClick={fetchAll} className="flex items-center gap-2 text-white/50 hover:text-white text-sm px-3 py-1.5 rounded-lg hover:bg-white/10 transition-colors">
            <RefreshCw className="w-4 h-4" /> Refresh
          </button>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {summaryCards.map((s, i) => (
            <div key={i} className="glassmorphism rounded-2xl border border-white/10 p-5 flex flex-col gap-3">
              <div className={`w-9 h-9 rounded-xl border flex items-center justify-center ${s.bg}`}>
                <s.icon className={`w-4 h-4 ${s.color}`} />
              </div>
              <div>
                {loading ? (
                  <div className="h-7 w-12 bg-white/10 animate-pulse rounded" />
                ) : (
                  <div className="text-2xl font-bold text-white">{s.value.toLocaleString()}</div>
                )}
                <div className="text-xs text-white/40 mt-0.5">{s.label}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Per-Campaign Breakdown ────────────────── */}
      <div className="glassmorphism rounded-2xl border border-white/10 overflow-hidden">
        <div className="flex items-center gap-3 px-6 py-5 border-b border-white/5">
          <TrendingUp className="w-5 h-5 text-emerald-400" />
          <h3 className="font-semibold text-lg">Per-Campaign Breakdown</h3>
        </div>

        {loading ? (
          <div className="flex justify-center py-16">
            <div className="w-6 h-6 border-2 border-white/20 border-t-white rounded-full animate-spin" />
          </div>
        ) : campaigns.length === 0 ? (
          <div className="text-center py-16 text-white/40">
            <BarChart3 className="w-10 h-10 mx-auto mb-3 text-white/15" />
            <p>No campaigns yet. Create and run one to see metrics here.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-white/3 text-white/40 text-xs uppercase tracking-wider">
                <tr>
                  <th className="text-left px-6 py-3 font-medium">Campaign</th>
                  <th className="text-left px-4 py-3 font-medium">Status</th>
                  <th className="text-right px-4 py-3 font-medium">
                    <span className="flex items-center justify-end gap-1"><Users className="w-3 h-3" /> Recipients</span>
                  </th>
                  <th className="text-right px-4 py-3 font-medium">
                    <span className="flex items-center justify-end gap-1"><Send className="w-3 h-3" /> Sent</span>
                  </th>
                  <th className="text-right px-4 py-3 font-medium">
                    <span className="flex items-center justify-end gap-1"><CheckCircle2 className="w-3 h-3" /> Delivered</span>
                  </th>
                  <th className="text-right px-4 py-3 font-medium">
                    <span className="flex items-center justify-end gap-1"><XCircle className="w-3 h-3" /> Failed</span>
                  </th>
                  <th className="text-right px-4 py-3 font-medium">
                    <span className="flex items-center justify-end gap-1"><Eye className="w-3 h-3" /> Opened</span>
                  </th>
                  <th className="text-right px-4 py-3 font-medium">
                    <span className="flex items-center justify-end gap-1"><Reply className="w-3 h-3" /> Replied</span>
                  </th>
                  <th className="text-right px-4 py-3 font-medium">
                    <span className="flex items-center justify-end gap-1"><MousePointerClick className="w-3 h-3" /> Clicked</span>
                  </th>
                  <th className="text-right px-6 py-3 font-medium">Delivery %</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {campaigns.map((camp: any) => {
                  const m = metrics[camp.id] || {};
                  return (
                    <tr key={camp.id} className="hover:bg-white/3 transition-colors">
                      <td className="px-6 py-4">
                        <Link href={`/campaigns/${camp.id}`} className="font-medium hover:text-indigo-300 transition-colors block">
                          {camp.name}
                        </Link>
                        <div className="text-xs text-white/40 mt-0.5 uppercase">{camp.channel}</div>
                      </td>
                      <td className="px-4 py-4">
                        <span className={`px-2 py-0.5 text-[10px] font-bold tracking-wider uppercase rounded border ${statusColors[camp.status] || 'bg-white/10 text-white/50'}`}>
                          {camp.status}
                        </span>
                      </td>
                      <td className="px-4 py-4 text-right font-mono text-white/80">{m.total_recipients ?? 0}</td>
                      <td className="px-4 py-4 text-right font-mono text-white/80">{m.total_sent ?? 0}</td>
                      <td className="px-4 py-4 text-right font-mono text-emerald-400">{m.total_delivered ?? 0}</td>
                      <td className="px-4 py-4 text-right font-mono text-red-400">{m.total_failed ?? 0}</td>
                      <td className="px-4 py-4 text-right font-mono text-purple-400">{m.total_opened ?? 0}</td>
                      <td className="px-4 py-4 text-right font-mono text-amber-400">{m.total_replied ?? 0}</td>
                      <td className="px-4 py-4 text-right font-mono text-blue-400">{m.total_clicked ?? 0}</td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <div className="w-16 h-1.5 bg-white/10 rounded-full overflow-hidden">
                            <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${Math.min(m.delivery_rate ?? 0, 100)}%` }} />
                          </div>
                          <span className="text-emerald-400 font-mono text-xs w-10 text-right">{(m.delivery_rate ?? 0).toFixed(0)}%</span>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
