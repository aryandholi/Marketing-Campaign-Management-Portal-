"use client";
import React, { useState, useEffect } from 'react';
import { Users, Search, Phone, Mail, User, CheckCircle2, XCircle, Plus, Loader2, AlertCircle } from 'lucide-react';
import { apiClient } from '@/lib/api';

interface Contact {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  username?: string;
}

export default function AudiencesPage() {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [resolveInput, setResolveInput] = useState('');
  const [resolveResult, setResolveResult] = useState<any>(null);
  const [resolving, setResolving] = useState(false);
  const [search, setSearch] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);
  const [addLoading, setAddLoading] = useState(false);
  const [addError, setAddError] = useState('');
  const [addSuccess, setAddSuccess] = useState('');

  const [newContact, setNewContact] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    username: '',
  });

  const fetchContacts = () => {
    apiClient.get('/contacts')
      .then(res => setContacts(res.data.contacts || []))
      .catch(() => {});
  };

  useEffect(() => {
    fetchContacts();
  }, []);

  const handleResolve = async () => {
    if (!resolveInput.trim()) return;
    setResolving(true);
    setResolveResult(null);
    try {
      const identifiers = resolveInput.split(',').map((s: string) => s.trim()).filter(Boolean);
      const res = await apiClient.post('/campaigns/audience/resolve', { identifiers });
      setResolveResult(res.data);
    } catch (err: any) {
      alert(err?.response?.data?.error?.message || 'Resolution failed');
    } finally {
      setResolving(false);
    }
  };

  const handleAddContact = async (e: React.FormEvent) => {
    e.preventDefault();
    setAddLoading(true);
    setAddError('');
    setAddSuccess('');
    try {
      await apiClient.post('/contacts', {
        first_name: newContact.first_name,
        last_name: newContact.last_name || '',
        email: newContact.email,
        phone: newContact.phone || null,
        username: newContact.username || null,
      });
      setAddSuccess(`Contact "${newContact.first_name}" added! You can now target ${newContact.email} in campaigns.`);
      setNewContact({ first_name: '', last_name: '', email: '', phone: '', username: '' });
      fetchContacts();
      setTimeout(() => setShowAddForm(false), 2000);
    } catch (err: any) {
      setAddError(err?.response?.data?.detail || err?.response?.data?.error?.message || 'Failed to add contact');
    } finally {
      setAddLoading(false);
    }
  };

  const filtered = contacts.filter(c =>
    `${c.first_name} ${c.last_name} ${c.email} ${c.username || ''}`.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-8">

      {/* ── Audience Resolver ─────────────────────── */}
      <div className="glassmorphism rounded-2xl border border-white/10 p-6">
        <div className="flex items-center gap-3 mb-5 pb-4 border-b border-white/5">
          <Search className="w-5 h-5 text-indigo-400" />
          <div>
            <h3 className="font-semibold text-lg">Audience Resolver</h3>
            <p className="text-sm text-white/50">Preview how identifiers resolve to contacts before sending a campaign.</p>
          </div>
        </div>
        <div className="flex gap-3">
          <input
            type="text"
            value={resolveInput}
            onChange={e => setResolveInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleResolve()}
            placeholder="your-real@email.com, +1-555-0102, charlie_choco..."
            className="flex-1 px-4 py-2.5 bg-black/40 border border-white/10 rounded-xl text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 text-sm"
          />
          <button
            onClick={handleResolve}
            disabled={resolving || !resolveInput.trim()}
            className="px-5 py-2.5 bg-indigo-500 hover:bg-indigo-400 disabled:opacity-50 text-white rounded-xl font-medium text-sm transition-all"
          >
            {resolving ? 'Resolving…' : 'Resolve'}
          </button>
        </div>

        {resolveResult && (
          <div className="mt-5 space-y-3">
            <div className="flex items-center gap-4 text-sm">
              <span className="flex items-center gap-1.5 text-emerald-400"><CheckCircle2 className="w-4 h-4" /> {resolveResult.total_resolved} resolved</span>
              <span className="flex items-center gap-1.5 text-red-400"><XCircle className="w-4 h-4" /> {resolveResult.total_unresolved} unresolved</span>
            </div>
            {resolveResult.resolved.map((c: any) => (
              <div key={c.id} className="flex items-center gap-4 bg-emerald-500/5 border border-emerald-500/20 rounded-xl px-4 py-3">
                <div className="w-9 h-9 rounded-full bg-emerald-500/20 flex items-center justify-center text-emerald-400 font-bold text-sm flex-shrink-0">
                  {c.first_name?.[0] ?? '?'}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-medium">{c.first_name} {c.last_name}</div>
                  <div className="text-xs text-white/40">via: <span className="text-indigo-300">{c.identifier}</span></div>
                </div>
                <div className="text-right text-xs text-white/50">
                  <div>{c.email}</div>
                  <div>{c.phone}</div>
                </div>
              </div>
            ))}
            {resolveResult.unresolved.map((id: string, i: number) => (
              <div key={i} className="flex items-center gap-3 bg-red-500/5 border border-red-500/20 rounded-xl px-4 py-3">
                <XCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
                <div className="flex-1">
                  <span className="font-mono text-sm text-white/60">{id}</span>
                </div>
                <span className="text-xs text-red-400">Not found — add this contact below</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ── Add Real Contact ───────────────────────── */}
      <div className="glassmorphism rounded-2xl border border-white/10 p-6">
        <div className="flex items-center justify-between mb-5 pb-4 border-b border-white/5">
          <div className="flex items-center gap-3">
            <Plus className="w-5 h-5 text-emerald-400" />
            <div>
              <h3 className="font-semibold text-lg">Add Real Contact</h3>
              <p className="text-sm text-white/50">Register a real email address to receive actual campaign emails.</p>
            </div>
          </div>
          <button
            onClick={() => { setShowAddForm(v => !v); setAddError(''); setAddSuccess(''); }}
            className={`px-4 py-2 rounded-xl text-sm font-medium transition-all border ${
              showAddForm
                ? 'bg-white/5 border-white/10 text-white/70'
                : 'bg-emerald-500 border-emerald-500 text-white hover:bg-emerald-400 shadow-[0_0_15px_rgba(16,185,129,0.3)]'
            }`}
          >
            {showAddForm ? 'Cancel' : '+ Add Contact'}
          </button>
        </div>

        {showAddForm && (
          <form onSubmit={handleAddContact} className="space-y-4 mb-2">
            {addError && (
              <div className="flex items-center gap-2 bg-red-500/10 border border-red-500/30 text-red-400 rounded-xl px-4 py-3 text-sm">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                {addError}
              </div>
            )}
            {addSuccess && (
              <div className="flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 rounded-xl px-4 py-3 text-sm">
                <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
                {addSuccess}
              </div>
            )}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-white/60 mb-1.5 uppercase tracking-wider">First Name *</label>
                <input
                  type="text"
                  required
                  value={newContact.first_name}
                  onChange={e => setNewContact(c => ({ ...c, first_name: e.target.value }))}
                  placeholder="John"
                  className="w-full px-3 py-2.5 bg-black/40 border border-white/10 rounded-xl text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-white/60 mb-1.5 uppercase tracking-wider">Last Name</label>
                <input
                  type="text"
                  value={newContact.last_name}
                  onChange={e => setNewContact(c => ({ ...c, last_name: e.target.value }))}
                  placeholder="Doe"
                  className="w-full px-3 py-2.5 bg-black/40 border border-white/10 rounded-xl text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 text-sm"
                />
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium text-white/60 mb-1.5 uppercase tracking-wider">Real Email Address *</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
                <input
                  type="email"
                  required
                  value={newContact.email}
                  onChange={e => setNewContact(c => ({ ...c, email: e.target.value }))}
                  placeholder="yourname@gmail.com"
                  className="w-full pl-10 pr-4 py-2.5 bg-black/40 border border-white/10 rounded-xl text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 text-sm"
                />
              </div>
              <p className="text-xs text-indigo-300/70 mt-1">
                ⚡ This person will receive real emails when SMTP is configured in Settings.
              </p>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-white/60 mb-1.5 uppercase tracking-wider">Phone (for SMS)</label>
                <div className="relative">
                  <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
                  <input
                    type="tel"
                    value={newContact.phone}
                    onChange={e => setNewContact(c => ({ ...c, phone: e.target.value }))}
                    placeholder="+1234567890"
                    className="w-full pl-10 pr-4 py-2.5 bg-black/40 border border-white/10 rounded-xl text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 text-sm"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-white/60 mb-1.5 uppercase tracking-wider">Username (optional)</label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
                  <input
                    type="text"
                    value={newContact.username}
                    onChange={e => setNewContact(c => ({ ...c, username: e.target.value }))}
                    placeholder="john_doe"
                    className="w-full pl-10 pr-4 py-2.5 bg-black/40 border border-white/10 rounded-xl text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 text-sm"
                  />
                </div>
              </div>
            </div>
            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setShowAddForm(false)}
                className="px-4 py-2.5 rounded-xl border border-white/10 hover:bg-white/5 text-white/70 text-sm font-medium transition-all"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={addLoading}
                className="flex items-center gap-2 px-5 py-2.5 bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-white rounded-xl font-semibold text-sm transition-all shadow-[0_0_15px_rgba(16,185,129,0.3)]"
              >
                {addLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                {addLoading ? 'Adding…' : 'Add Contact'}
              </button>
            </div>
          </form>
        )}

        {!showAddForm && (
          <p className="text-sm text-white/40">
            Add a real email address to enable actual email delivery when SMTP is configured in Settings.
            Use the contact's email in campaign Target Audience to send them real messages.
          </p>
        )}
      </div>

      {/* ── Contact Directory ─────────────────────── */}
      <div className="glassmorphism rounded-2xl border border-white/10 p-6">
        <div className="flex items-center justify-between mb-5 pb-4 border-b border-white/5">
          <div className="flex items-center gap-3">
            <Users className="w-5 h-5 text-purple-400" />
            <div>
              <h3 className="font-semibold text-lg">Contact Directory</h3>
              <p className="text-sm text-white/50">{contacts.length} contacts available for campaigns.</p>
            </div>
          </div>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
            <input
              type="text"
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search contacts..."
              className="pl-9 pr-4 py-2 bg-black/40 border border-white/10 rounded-xl text-sm text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-white/40 text-xs uppercase tracking-wider border-b border-white/5">
                <th className="text-left pb-3 font-medium">Contact</th>
                <th className="text-left pb-3 font-medium"><Mail className="w-3 h-3 inline mr-1" />Email</th>
                <th className="text-left pb-3 font-medium"><Phone className="w-3 h-3 inline mr-1" />Phone</th>
                <th className="text-left pb-3 font-medium"><User className="w-3 h-3 inline mr-1" />Username</th>
                <th className="text-left pb-3 font-medium">Channels</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-10 text-center text-white/40 text-sm">
                    <Users className="w-8 h-8 mx-auto mb-2 text-white/15" />
                    {search ? 'No contacts match your search.' : 'No contacts yet. Add one above.'}
                  </td>
                </tr>
              ) : filtered.map(c => (
                <tr key={c.id} className="hover:bg-white/3 transition-colors">
                  <td className="py-4 pr-4">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500/30 to-purple-500/30 flex items-center justify-center text-white font-bold text-sm border border-white/10 flex-shrink-0">
                        {c.first_name[0]}
                      </div>
                      <div>
                        <div className="font-medium">{c.first_name} {c.last_name}</div>
                        <div className="text-xs text-white/40">ID: {c.id.slice(-8)}</div>
                      </div>
                    </div>
                  </td>
                  <td className="py-4 pr-4 text-white/70 font-mono text-xs">{c.email}</td>
                  <td className="py-4 pr-4 text-white/70 font-mono text-xs">{c.phone || <span className="text-white/25 italic">—</span>}</td>
                  <td className="py-4 pr-4 text-white/70 font-mono text-xs">{c.username ? `@${c.username}` : <span className="text-white/25 italic">—</span>}</td>
                  <td className="py-4">
                    <div className="flex gap-1.5 flex-wrap">
                      {c.email && (
                        <span className="px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider rounded border bg-blue-500/10 border-blue-500/20 text-blue-400">Email</span>
                      )}
                      {c.phone && (
                        <span className="px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider rounded border bg-emerald-500/10 border-emerald-500/20 text-emerald-400">SMS</span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
