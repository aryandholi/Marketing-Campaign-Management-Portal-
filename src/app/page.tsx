import Link from "next/link";
import { ArrowRight, BarChart3, Megaphone, Zap } from "lucide-react";

export default function Home() {
  return (
    <div className="flex flex-col min-h-screen bg-black text-white selection:bg-indigo-500/30 overflow-hidden relative">
      {/* Background Glow */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-indigo-600/20 blur-[120px] rounded-full pointer-events-none" />
      <div className="absolute bottom-0 right-0 w-[600px] h-[600px] bg-purple-600/10 blur-[150px] rounded-full pointer-events-none" />

      {/* Navigation */}
      <nav className="w-full max-w-7xl mx-auto px-6 py-6 flex items-center justify-between relative z-10">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <Megaphone className="w-4 h-4 text-white" />
          </div>
          <span className="font-semibold text-lg tracking-tight">Nexus Campaigns</span>
        </div>
        <div className="flex items-center gap-4">
          <Link href="/login" className="text-sm font-medium text-white/70 hover:text-white transition-colors">
            Sign In
          </Link>
          <Link href="/login" className="px-4 py-2 bg-white text-black text-sm font-medium rounded-full hover:bg-white/90 transition-all shadow-lg shadow-white/10">
            Get Started
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="flex-1 flex flex-col items-center justify-center w-full max-w-5xl mx-auto px-6 pt-20 pb-32 text-center relative z-10">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-sm font-medium text-indigo-300 mb-8 backdrop-blur-sm">
          <span className="flex h-2 w-2 rounded-full bg-indigo-500 animate-pulse"></span>
          Nexus Portal 1.0 is live
        </div>
        
        <h1 className="text-5xl sm:text-7xl font-bold tracking-tighter mb-8 leading-[1.1] bg-clip-text text-transparent bg-gradient-to-b from-white to-white/60">
          Orchestrate Campaigns <br className="hidden sm:block" />
          with Unmatched Clarity.
        </h1>
        
        <p className="text-lg sm:text-xl text-white/50 max-w-2xl mb-12 leading-relaxed">
          The ultimate platform for modern marketing teams. Seamlessly resolve audiences, dispatch across channels, and track engagement down to the millisecond.
        </p>
        
        <div className="flex flex-col sm:flex-row items-center gap-4">
          <Link 
            href="/login" 
            className="flex items-center gap-2 px-8 py-4 bg-white text-black font-semibold rounded-full hover:scale-105 transition-transform shadow-[0_0_40px_rgba(255,255,255,0.2)]"
          >
            Go to Dashboard <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </main>

      {/* Features Showcase */}
      <section className="w-full max-w-6xl mx-auto px-6 pb-32 relative z-10 grid grid-cols-1 md:grid-cols-3 gap-6">
        {[
          {
            icon: Zap,
            title: "Lightning Fast Dispatch",
            description: "Extensible adapters for Email, SMS, and WhatsApp. Designed for scale.",
          },
          {
            icon: BarChart3,
            title: "Real-time Analytics",
            description: "Track deliveries, opens, and clicks as they happen with robust webhook ingestion.",
          },
          {
            icon: Megaphone,
            title: "Campaign Orchestration",
            description: "Manage campaign lifecycles. Draft, schedule, pause, and stop with precision.",
          }
        ].map((feature, idx) => (
          <div key={idx} className="glassmorphism p-8 rounded-3xl border border-white/10 relative overflow-hidden group">
            <div className="w-12 h-12 rounded-xl bg-white/5 flex items-center justify-center mb-6 border border-white/5 group-hover:scale-110 transition-transform">
              <feature.icon className="w-6 h-6 text-indigo-400" />
            </div>
            <h3 className="text-xl font-semibold mb-3">{feature.title}</h3>
            <p className="text-white/50 leading-relaxed">
              {feature.description}
            </p>
          </div>
        ))}
      </section>
    </div>
  );
}
