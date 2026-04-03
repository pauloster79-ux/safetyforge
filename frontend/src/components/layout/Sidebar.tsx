import { Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  FolderKanban,
  FileText,
  Settings,
  CreditCard,
  X,
  Users,
  ClipboardList,
  Shield,
  BarChart3,
  FileCheck,
  Building2,
  MapPin,
  AlertTriangle,
  MessageSquare,
  Search,
  Leaf,
  Wrench,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { ROUTES } from '@/lib/constants';
import { Button } from '@/components/ui/button';
import { useJurisdiction } from '@/contexts/JurisdictionContext';

interface SidebarProps {
  open: boolean;
  onClose: () => void;
}

interface NavItem {
  label: string;
  icon: typeof LayoutDashboard;
  path: string;
  badge?: string;
}

interface NavSection {
  label: string;
  items: NavItem[];
}

function useNavSections(): NavSection[] {
  const j = useJurisdiction();

  return [
    {
      label: 'Main',
      items: [
        { label: 'Dashboard', icon: LayoutDashboard, path: ROUTES.DASHBOARD },
        { label: 'Projects', icon: FolderKanban, path: ROUTES.PROJECTS },
      ],
    },
    {
      label: 'Safety',
      items: [
        { label: 'Inspections', icon: Search, path: ROUTES.PROJECTS, badge: '3' },
        { label: 'Documents', icon: FileText, path: ROUTES.DOCUMENTS },
        { label: 'Incidents', icon: AlertTriangle, path: ROUTES.PROJECTS, badge: '1' },
        { label: 'Workers', icon: Users, path: ROUTES.WORKERS },
        { label: 'Toolbox Talks', icon: MessageSquare, path: ROUTES.PROJECTS },
        { label: j.complianceAudit.name, icon: Shield, path: ROUTES.MOCK_INSPECTION },
        { label: 'Equipment', icon: Wrench, path: ROUTES.EQUIPMENT },
      ],
    },
    {
      label: 'Compliance',
      items: [
        { label: j.recordKeeping.name, icon: ClipboardList, path: ROUTES.OSHA_LOG },
        { label: 'Regional Compliance', icon: MapPin, path: ROUTES.STATE_COMPLIANCE },
        { label: 'Prequalification', icon: FileCheck, path: ROUTES.PREQUALIFICATION },
        { label: 'GC Portal', icon: Building2, path: ROUTES.GC_PORTAL },
        { label: 'Environmental', icon: Leaf, path: ROUTES.ENVIRONMENTAL },
      ],
    },
    {
      label: 'Reports',
      items: [
        { label: 'Analytics', icon: BarChart3, path: ROUTES.ANALYTICS },
      ],
    },
    {
      label: 'Settings',
      items: [
        { label: 'Settings', icon: Settings, path: ROUTES.SETTINGS },
        { label: 'Billing', icon: CreditCard, path: ROUTES.BILLING },
      ],
    },
  ];
}

export function Sidebar({ open, onClose }: SidebarProps) {
  const location = useLocation();
  const NAV_SECTIONS = useNavSections();

  return (
    <>
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/30 lg:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 flex w-[210px] flex-col bg-white border-r border-[var(--border)] transition-transform duration-200 lg:static lg:translate-x-0',
          open ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        {/* Logo */}
        <div className="flex h-14 items-center justify-between px-4 border-b border-[var(--border)]">
          <Link to={ROUTES.DASHBOARD} className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-md bg-[#F5B800]">
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="white"
                strokeWidth="3"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="h-4.5 w-4.5"
              >
                <polyline points="20 6 9 17 4 12" />
              </svg>
            </div>
            <div className="flex items-baseline gap-0">
              <span className="text-base font-bold text-foreground">Safety</span>
              <span className="text-base font-bold text-[#F5B800]">Forge</span>
            </div>
          </Link>
          <Button
            variant="ghost"
            size="icon"
            className="text-muted-foreground hover:text-foreground lg:hidden"
            onClick={onClose}
          >
            <X className="h-5 w-5" />
          </Button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto px-3 pt-2 pb-4">
          {NAV_SECTIONS.map((section) => (
            <div key={section.label} className="mt-4 first:mt-0">
              <p className="mb-1.5 px-2 font-mono text-[10px] font-medium uppercase tracking-[1.5px] text-[var(--concrete-400)]">
                {section.label}
              </p>
              <div className="space-y-0.5">
                {section.items.map((item) => {
                  const isActive =
                    item.path === ROUTES.DASHBOARD
                      ? location.pathname === '/dashboard' || location.pathname === '/'
                      : location.pathname.startsWith(item.path);

                  return (
                    <Link
                      key={item.label}
                      to={item.path}
                      onClick={onClose}
                      className={cn(
                        'flex items-center gap-2.5 px-2 py-1.5 text-[13px] font-medium transition-colors',
                        isActive
                          ? 'bg-[var(--machine-wash)] text-foreground font-semibold border-l-2 border-[#F5B800] -ml-[2px] pl-[10px]'
                          : 'text-[var(--concrete-500)] hover:text-foreground hover:bg-[var(--concrete-50)]'
                      )}
                    >
                      <item.icon
                        className={cn(
                          'w-4 h-4',
                          isActive ? 'text-[var(--machine-dark)]' : 'opacity-50'
                        )}
                      />
                      {item.label}
                      {item.badge && (
                        <span className="ml-auto font-mono text-[10px] bg-[#c53030] text-white px-[5px] rounded-[3px] font-semibold">
                          {item.badge}
                        </span>
                      )}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>
      </aside>
    </>
  );
}
