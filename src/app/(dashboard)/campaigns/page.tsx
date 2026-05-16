"use client";
import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { Plus, Search, Megaphone, Trash2 } from 'lucide-react';
import { apiClient } from '@/lib/api';

const statusColors: any = {
  'draft': 'bg-gray-500/20 text-gray-400 border-gray-500/30',
  'scheduled': 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  'active': 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  'paused': 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  'completed': 'bg-purple-500/20 text-purple-400 border-purple-500/30',
  'stopped': 'bg-red-500/20 text-red-400 border-red-500/30',
};

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  const fetchCampaigns = () => {
    setLoading(true);
    apiClient.get('/campaigns')
      .then(res => {
        setCampaigns(res.data.campaigns || []);
      })
      .catch(err => {
        console.error("Error fetching", err);
        setCampaigns([]);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchCampaigns();
  }, []);

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Delete campaign "${name}"? This cannot be undone.`)) return;
    try {
      await apiClient.delete(`/campaigns/${id}`);
      fetchCampaigns();
    } catch (err) {
      console.error(err);
      alert("Failed to delete campaign");
    }
  };

  const filtered = campaigns.filter(c =>
    c.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div className="relative w-full max-w-sm">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="h-4 w-4 text-white/40" />
          </div>
          <input
            type="text"
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-white/5 border border-white/10 rounded-xl text-white placeholder-white/40 focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/50 transition-all text-sm"
            placeholder="Search campaigns..."
          />
        </div>
        <Link 
          href="/campaigns/new"
          className="flex items-center gap-2 bg-white text-black px-4 py-2 rounded-xl font-medium text-sm hover:bg-white/90 transition-all shadow-[0_0_15px_rgba(255,255,255,0.2)]"
        >
          <Plus className="w-4 h-4" />
          New Campaign
        </Link>
      </div>

      <div className="glassmorphism rounded-2xl border border-white/10 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-white/5 border-b border-white/10 text-white/50">
              <tr>
                <th className="px-6 py-4 font-medium">Campaign</th>
                <th className="px-6 py-4 font-medium">Status</th>
                <th className="px-6 py-4 font-medium">Channel</th>
                <th className="px-6 py-4 font-medium">Created Date</th>
                <th className="px-6 py-4 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {loading ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-white/50">
                    <div className="flex justify-center mb-2">
                       <div className="w-6 h-6 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                    </div>
                    Loading campaigns...
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-10 text-center text-white/50">
                    <div className="flex justify-center mb-3">
                      <Megaphone className="w-8 h-8 text-white/20" />
                    </div>
                    {searchTerm ? 'No campaigns match your search.' : 'No campaigns found. Create your first one to get started.'}
                  </td>
                </tr>
              ) : (
                filtered.map((camp) => (
                  <tr key={camp.id} className="hover:bg-white/5 transition-colors group">
                    <td className="px-6 py-4 font-medium w-[40%]">
                      <Link href={`/campaigns/${camp.id}`} className="hover:text-indigo-300 transition-colors">
                        {camp.name}
                      </Link>
                      <div className="text-xs text-white/40 mt-1 font-normal line-clamp-1">{camp.description}</div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2.5 py-1 text-[10px] font-bold tracking-wider uppercase rounded-md border ${statusColors[camp.status] || 'bg-white/10 text-white/70'}`}>
                        {camp.status}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-white/80 uppercase">{camp.channel}</span>
                    </td>
                    <td className="px-6 py-4 text-white/50">
                      {new Date(camp.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={() => handleDelete(camp.id, camp.name)}
                        className="text-white/40 hover:text-red-400 transition-colors p-1 rounded hover:bg-white/10"
                        title="Delete campaign"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
