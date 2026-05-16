"use client";
import React, { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Sidebar } from "@/components/Sidebar";

const pageTitles: Record<string, { title: string; subtitle: string }> = {
  '/dashboard': { title: 'Overview', subtitle: 'Here is what is happening with your campaigns today.' },
  '/campaigns': { title: 'Campaigns', subtitle: 'Manage and monitor your marketing campaigns.' },
  '/campaigns/new': { title: 'Create Campaign', subtitle: 'Set up a new marketing outreach effort.' },
  '/audiences': { title: 'Audiences', subtitle: 'Manage and segment your contact lists.' },
  '/reports': { title: 'Performance', subtitle: 'Track campaign analytics and engagement metrics.' },
  '/settings': { title: 'Settings', subtitle: 'Configure your workspace and preferences.' },
};

export default function DashboardLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const pathname = usePathname();
  const router = useRouter();
  const [isAuthed, setIsAuthed] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/login');
    } else {
      setIsAuthed(true);
    }
  }, [router]);

  if (!isAuthed) {
    return (
      <div className="min-h-screen bg-[#050505] flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin" />
      </div>
    );
  }

  const pageInfo = pageTitles[pathname] || { title: 'Campaign Portal', subtitle: '' };
  // Handle dynamic routes like /campaigns/[id]
  const isCampaignDetail = pathname.startsWith('/campaigns/') && pathname !== '/campaigns/new';

  return (
    <div className="flex min-h-screen bg-[#050505] relative overflow-hidden">
      {/* Decorative ambient background lights */}
      <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-indigo-900/20 blur-[120px] rounded-full pointer-events-none" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-purple-900/10 blur-[120px] rounded-full pointer-events-none" />
      
      <Sidebar />
      <main className="flex-1 ml-64 p-8 relative z-10">
        <header className="flex justify-between items-center mb-8">
          <div>
            <h2 className="text-2xl font-semibold tracking-tight">
              {isCampaignDetail ? 'Campaign Details' : pageInfo.title}
            </h2>
            <p className="text-sm text-white/50 mt-1">
              {isCampaignDetail ? 'View and manage campaign lifecycle and metrics.' : pageInfo.subtitle}
            </p>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 bg-white/5 border border-white/10 px-3 py-1.5 rounded-full text-sm">
              <div className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)] animate-pulse" />
              <span className="text-white/80">API Connected</span>
            </div>
          </div>
        </header>
        {children}
      </main>
    </div>
  );
}
