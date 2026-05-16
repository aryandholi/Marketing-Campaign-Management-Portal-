"use client";
import React, { useEffect, useState } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Users, Send, CheckCircle2, BarChart3, AlertTriangle, Eye, MousePointerClick } from 'lucide-react';
import { apiClient } from '@/lib/api';

export default function DashboardOverview() {
  const [metrics, setMetrics] = useState<any>(null);
  const [campaigns, setCampaigns] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      apiClient.get('/reports/campaigns/summary').catch(() => ({ data: {} })),
      apiClient.get('/campaigns?limit=5').catch(() => ({ data: { campaigns: [] } })),
    ])
      .then(([summaryRes, campRes]) => {
        setMetrics(summaryRes.data);
        setCampaigns(campRes.data?.campaigns || []);
      })
      .finally(() => setLoading(false));
  }, []);

  const statCards = [
    { title: 'Total Campaigns', value: metrics?.total_campaigns || 0, icon: BarChart3, color: 'text-blue-400' },
    { title: 'Total Sent', value: (metrics?.total_sent || 0).toLocaleString(), icon: Send, color: 'text-indigo-400' },
    { title: 'Delivered', value: (metrics?.total_delivered || 0).toLocaleString(), icon: CheckCircle2, color: 'text-emerald-400' },
    { title: 'Opened', value: (metrics?.total_opened || 0).toLocaleString(), icon: Eye, color: 'text-purple-400' },
    { title: 'Clicked', value: (metrics?.total_clicked || 0).toLocaleString(), icon: MousePointerClick, color: 'text-cyan-400' },
    { title: 'Failed', value: (metrics?.total_failed || 0).toLocaleString(), icon: AlertTriangle, color: 'text-red-400' },
  ];

  const totalSent = metrics?.total_sent || 0;
  const totalDelivered = metrics?.total_delivered || 0;
  const totalOpened = metrics?.total_opened || 0;
  const totalClicked = metrics?.total_clicked || 0;
  const deliveryRate = totalSent > 0 ? ((totalDelivered / totalSent) * 100) : 0;
  const openRate = totalDelivered > 0 ? ((totalOpened / totalDelivered) * 100) : 0;
  const clickRate = totalOpened > 0 ? ((totalClicked / totalOpened) * 100) : 0;

  const statusColors: any = {
    'draft': 'bg-gray-500/20 text-gray-400 border-gray-500/30',
    'active': 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    'paused': 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    'completed': 'bg-purple-500/20 text-purple-400 border-purple-500/30',
    'stopped': 'bg-red-500/20 text-red-400 border-red-500/30',
  };

  return (
    <div className="space-y-6">
      
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {statCards.map((stat, idx) => (
          <div key={idx} className="glassmorphism rounded-2xl p-6 border border-white/10 relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
              <stat.icon className={`w-16 h-16 ${stat.color}`} />
            </div>
            <div className={`w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center mb-4 border border-white/5`}>
              <stat.icon className={`w-5 h-5 ${stat.color}`} />
            </div>
            <p className="text-white/50 text-sm font-medium">{stat.title}</p>
            {loading ? (
              <div className="h-8 w-24 bg-white/10 animate-pulse rounded mt-1" />
            ) : (
              <h3 className="text-3xl font-bold text-white mt-1 tracking-tight">{stat.value}</h3>
            )}
          </div>
        ))}
      </div>

      {/* Conversion Rates + Recent Campaigns */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="glassmorphism rounded-2xl p-6 border border-white/10 flex flex-col">
           <h3 className="text-lg font-semibold mb-1">Conversion Funnel</h3>
           <p className="text-sm text-white/50 mb-6">Aggregate pipeline rates</p>
           
           <div className="flex-1 flex flex-col justify-center space-y-6">
              {[
                { label: 'Delivery Rate', value: `${deliveryRate.toFixed(1)}%`, progress: deliveryRate },
                { label: 'Open Rate', value: `${openRate.toFixed(1)}%`, progress: openRate },
                { label: 'Click Rate', value: `${clickRate.toFixed(1)}%`, progress: clickRate },
              ].map((item, idx) => (
                <div key={idx}>
                  <div className="flex justify-between items-end mb-2">
                    <span className="text-sm font-medium text-white/80">{item.label}</span>
                    <span className="text-xl font-bold">{item.value}</span>
                  </div>
                  <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden">
                    <div 
                      className={`h-full rounded-full bg-gradient-to-r ${idx === 0 ? 'from-emerald-600 to-emerald-400' : idx === 1 ? 'from-purple-600 to-purple-400' : 'from-indigo-600 to-indigo-400'}`} 
                      style={{ width: `${Math.min(item.progress, 100)}%` }} 
                    />
                  </div>
                </div>
              ))}
           </div>
        </div>

        <div className="lg:col-span-2 glassmorphism rounded-2xl p-6 border border-white/10">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-lg font-semibold">Recent Campaigns</h3>
              <p className="text-sm text-white/50">Latest campaigns at a glance</p>
            </div>
          </div>
          {loading ? (
            <div className="flex justify-center py-10">
              <div className="w-6 h-6 border-2 border-white/20 border-t-white rounded-full animate-spin" />
            </div>
          ) : campaigns.length === 0 ? (
            <div className="text-center py-10 text-white/40">
              <BarChart3 className="w-10 h-10 mx-auto mb-3 text-white/15" />
              <p>No campaigns yet. Create one to see data here.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {campaigns.map((camp: any) => (
                <a key={camp.id} href={`/campaigns/${camp.id}`} className="flex items-center justify-between bg-white/5 rounded-xl px-5 py-4 border border-white/5 hover:bg-white/10 transition-colors group">
                  <div className="flex-1 min-w-0">
                    <div className="font-medium group-hover:text-indigo-300 transition-colors">{camp.name}</div>
                    <div className="text-xs text-white/40 mt-0.5 uppercase">{camp.channel} · {new Date(camp.created_at).toLocaleDateString()}</div>
                  </div>
                  <span className={`px-2.5 py-1 text-[10px] font-bold tracking-wider uppercase rounded-md border ml-4 ${statusColors[camp.status] || 'bg-white/10 text-white/70'}`}>
                    {camp.status}
                  </span>
                </a>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
