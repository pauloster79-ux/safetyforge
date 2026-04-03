import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { EmailVerificationBanner } from '@/components/auth/EmailVerificationBanner';
import { JurisdictionProvider } from '@/contexts/JurisdictionContext';

export function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <JurisdictionProvider>
      <div className="flex h-screen bg-[#f4f5f3]">
        <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />

        <div className="flex flex-1 flex-col overflow-hidden">
          <Header onMenuClick={() => setSidebarOpen(true)} />
          <EmailVerificationBanner />

          <main className="flex-1 overflow-y-auto p-6">
            <Outlet />
          </main>

          {/* Footer bar — clipboard aesthetic */}
          <footer className="flex items-center justify-between border-t border-[#e6e8e3] bg-white px-6 py-2.5 font-mono text-[11px] text-[#71766b]">
            <span>SafetyForge v2.1</span>
            <span>Last sync: 2 min ago</span>
          </footer>
        </div>
      </div>
    </JurisdictionProvider>
  );
}
