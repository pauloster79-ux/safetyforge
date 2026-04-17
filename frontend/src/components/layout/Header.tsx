import { Menu, LogOut, User, Settings, Clock } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useAuth } from '@/hooks/useAuth';
import { useCompany, useSubscription } from '@/hooks/useCompany';
import { useProjects } from '@/hooks/useProjects';
import { ROUTES } from '@/lib/constants';
import { LocaleToggle } from './LocaleToggle';

interface HeaderProps {
  onMenuClick: () => void;
}

export function Header({ onMenuClick }: HeaderProps) {
  const { user, signOut } = useAuth();
  const { data: company } = useCompany();
  const { data: subscription } = useSubscription();
  const { data: projects } = useProjects();
  const navigate = useNavigate();

  const displayName = user?.fullName || user?.primaryEmailAddress?.emailAddress?.split('@')[0] || 'User';
  const initials = displayName
    .split(' ')
    .map((n: string) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);

  const activeProjects = projects?.filter((p) => p.status === 'active') ?? [];
  const currentProject = activeProjects[0];

  const handleSignOut = async () => {
    await signOut();
    navigate(ROUTES.LOGIN);
  };

  return (
    <header className="flex items-center justify-between gap-3 border-b border-[#e6e8e3] bg-white px-4 py-3 lg:px-6">
      {/* Left: hamburger + project context */}
      <div className="flex items-center gap-3 min-w-0">
        <Button
          variant="ghost"
          size="icon"
          className="flex-shrink-0 lg:hidden"
          onClick={onMenuClick}
        >
          <Menu className="h-5 w-5" />
        </Button>
        <div className="min-w-0">
          <h1 className="text-sm font-bold text-foreground truncate lg:text-base">
            {currentProject?.name || company?.name || 'Kerf'}
          </h1>
          <p className="font-mono text-[11px] text-muted-foreground truncate hidden sm:block">
            {activeProjects.length > 0 ? `${activeProjects.length} active project${activeProjects.length !== 1 ? 's' : ''}` : 'No projects yet'}
          </p>
        </div>
      </div>

      {/* Right: actions + avatar */}
      <div className="flex items-center gap-2 flex-shrink-0">
        {subscription?.is_trial && subscription.trial_days_remaining != null && subscription.trial_days_remaining > 0 && (
          <Badge
            className="cursor-pointer bg-primary/10 text-primary hover:bg-primary/20 text-[11px] gap-1 hidden sm:flex"
            onClick={() => navigate(ROUTES.BILLING)}
          >
            <Clock className="h-3 w-3" />
            {subscription.trial_days_remaining}d trial
          </Badge>
        )}

        <LocaleToggle />

        <Button
          variant="outline"
          size="sm"
          className="text-[12px] hidden md:flex"
        >
          Export
        </Button>

        <Button
          size="sm"
          className="text-[12px] hidden sm:flex"
          onClick={() => {
            if (activeProjects.length > 0) {
              navigate(ROUTES.INSPECTION_NEW(activeProjects[0].id));
            } else {
              navigate(ROUTES.PROJECT_NEW);
            }
          }}
        >
          + New Inspection
        </Button>

        <DropdownMenu>
          <DropdownMenuTrigger
            className="flex items-center gap-2 rounded-[3px] px-1.5 py-1.5 hover:bg-muted"
          >
            <Avatar className="h-8 w-8">
              <AvatarImage src={user?.imageUrl || undefined} />
              <AvatarFallback className="bg-[var(--concrete-100)] text-[var(--concrete-500)] font-mono text-[10px] font-semibold">
                {initials}
              </AvatarFallback>
            </Avatar>
            <span className="hidden text-[13px] font-medium text-[#545951] lg:inline-block">
              {displayName}
            </span>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <div className="px-2 py-1.5">
              <p className="text-sm font-medium">{displayName}</p>
              <p className="text-xs text-muted-foreground">{user?.primaryEmailAddress?.emailAddress}</p>
            </div>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => navigate(ROUTES.SETTINGS)}>
              <User className="mr-2 h-4 w-4" />
              Profile & Company
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => navigate(ROUTES.SETTINGS)}>
              <Settings className="mr-2 h-4 w-4" />
              Settings
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleSignOut} className="text-[#c53030]">
              <LogOut className="mr-2 h-4 w-4" />
              Sign Out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
