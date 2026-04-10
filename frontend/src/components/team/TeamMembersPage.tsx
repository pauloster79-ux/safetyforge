import { useState } from 'react';
import {
  Users,
  Mail,
  Loader2,
  UserPlus,
  Shield,
  Trash2,
  Clock,
  XCircle,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  useMembers,
  useInvitations,
  useInviteMember,
  useUpdateMemberRole,
  useRemoveMember,
  useRevokeInvitation,
  type MemberRole,
} from '@/hooks/useMembers';

const ROLE_CONFIG: Record<MemberRole, { label: string; className: string; description: string }> = {
  owner: {
    label: 'Owner',
    className: 'bg-[var(--concrete-800)] text-white hover:bg-[var(--concrete-800)]',
    description: 'Full access, can transfer ownership',
  },
  admin: {
    label: 'Admin',
    className: 'bg-primary/10 text-primary hover:bg-primary/10',
    description: 'Can manage team and settings',
  },
  editor: {
    label: 'Editor',
    className: 'bg-[var(--pass-bg)] text-[var(--pass)] hover:bg-[var(--pass-bg)]',
    description: 'Can create and edit content',
  },
  viewer: {
    label: 'Viewer',
    className: 'bg-muted text-muted-foreground hover:bg-muted',
    description: 'Read-only access',
  },
};

function RoleBadge({ role }: { role: MemberRole }) {
  const config = ROLE_CONFIG[role];
  return <Badge className={config.className}>{config.label}</Badge>;
}

export function TeamMembersPage() {
  const { data: members, isLoading: membersLoading } = useMembers();
  const { data: invitations, isLoading: invitationsLoading } = useInvitations();
  const inviteMember = useInviteMember();
  const updateRole = useUpdateMemberRole();
  const removeMember = useRemoveMember();
  const revokeInvitation = useRevokeInvitation();

  const [inviteOpen, setInviteOpen] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState<MemberRole>('editor');

  const isLoading = membersLoading || invitationsLoading;
  const pendingInvitations = invitations?.filter((inv) => inv.status === 'pending') ?? [];

  const handleInvite = () => {
    if (!inviteEmail.trim()) return;
    inviteMember.mutate(
      { email: inviteEmail.trim(), role: inviteRole },
      {
        onSuccess: () => {
          setInviteEmail('');
          setInviteRole('editor');
          setInviteOpen(false);
        },
      }
    );
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Team Members</h1>
          <p className="text-sm text-muted-foreground">
            Manage who has access to your company account
          </p>
        </div>

        <Button size="sm" onClick={() => setInviteOpen(true)}>
          <UserPlus className="mr-2 h-4 w-4" />
          Invite Member
        </Button>

        <Dialog open={inviteOpen} onOpenChange={setInviteOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Invite Team Member</DialogTitle>
              <DialogDescription>
                Send an invitation to join your company account
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 pt-2">
              <div className="space-y-2">
                <Label htmlFor="invite-email">Email address</Label>
                <Input
                  id="invite-email"
                  type="email"
                  placeholder="colleague@company.com"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleInvite()}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="invite-role">Role</Label>
                <Select value={inviteRole} onValueChange={(v) => setInviteRole(v as MemberRole)}>
                  <SelectTrigger id="invite-role">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="admin">Admin — {ROLE_CONFIG.admin.description}</SelectItem>
                    <SelectItem value="editor">Editor — {ROLE_CONFIG.editor.description}</SelectItem>
                    <SelectItem value="viewer">Viewer — {ROLE_CONFIG.viewer.description}</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <Button variant="outline" onClick={() => setInviteOpen(false)}>
                  Cancel
                </Button>
                <Button
                  onClick={handleInvite}
                  disabled={!inviteEmail.trim() || inviteMember.isPending}
                >
                  {inviteMember.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Send Invitation
                </Button>
              </div>
              {inviteMember.isError && (
                <p className="text-sm text-[var(--fail)]">
                  Failed to send invitation. Please try again.
                </p>
              )}
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Active Members */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Users className="h-5 w-5 text-muted-foreground" />
            <div>
              <CardTitle className="text-lg">
                Active Members ({members?.length ?? 0})
              </CardTitle>
              <CardDescription>People with access to your account</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {members && members.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Member</TableHead>
                  <TableHead className="hidden sm:table-cell">Role</TableHead>
                  <TableHead className="hidden md:table-cell">Joined</TableHead>
                  <TableHead className="w-[100px]">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {members.map((member) => (
                  <TableRow key={member.id}>
                    <TableCell>
                      <div>
                        <p className="text-sm font-medium text-foreground">
                          {member.display_name}
                        </p>
                        <p className="text-xs text-muted-foreground">{member.email}</p>
                        <div className="mt-1 sm:hidden">
                          <RoleBadge role={member.role} />
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="hidden sm:table-cell">
                      {member.role === 'owner' ? (
                        <RoleBadge role={member.role} />
                      ) : (
                        <Select
                          value={member.role}
                          onValueChange={(v) =>
                            updateRole.mutate({ memberId: member.id, role: v as MemberRole })
                          }
                        >
                          <SelectTrigger className="h-8 w-[110px]">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="admin">Admin</SelectItem>
                            <SelectItem value="editor">Editor</SelectItem>
                            <SelectItem value="viewer">Viewer</SelectItem>
                          </SelectContent>
                        </Select>
                      )}
                    </TableCell>
                    <TableCell className="hidden md:table-cell">
                      <span className="text-sm text-muted-foreground">
                        {new Date(member.joined_at).toLocaleDateString('en-US', {
                          month: 'short',
                          day: 'numeric',
                          year: 'numeric',
                        })}
                      </span>
                    </TableCell>
                    <TableCell>
                      {member.role !== 'owner' && (
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-muted-foreground hover:text-[var(--fail)]"
                          onClick={() => removeMember.mutate(member.id)}
                          disabled={removeMember.isPending}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <Users className="mb-3 h-10 w-10 text-muted-foreground/50" />
              <p className="text-sm text-muted-foreground">No team members yet</p>
              <p className="text-xs text-muted-foreground">Invite your first team member to get started</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Pending Invitations */}
      {pendingInvitations.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Mail className="h-5 w-5 text-muted-foreground" />
              <div>
                <CardTitle className="text-lg">
                  Pending Invitations ({pendingInvitations.length})
                </CardTitle>
                <CardDescription>Invitations awaiting acceptance</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Email</TableHead>
                  <TableHead className="hidden sm:table-cell">Role</TableHead>
                  <TableHead className="hidden md:table-cell">Sent</TableHead>
                  <TableHead className="w-[100px]">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {pendingInvitations.map((invitation) => (
                  <TableRow key={invitation.id}>
                    <TableCell>
                      <div>
                        <p className="text-sm font-medium text-foreground">
                          {invitation.email}
                        </p>
                        <div className="mt-1 flex items-center gap-1.5 sm:hidden">
                          <RoleBadge role={invitation.role} />
                          <Badge variant="outline" className="text-[10px] gap-1">
                            <Clock className="h-2.5 w-2.5" />
                            Pending
                          </Badge>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="hidden sm:table-cell">
                      <RoleBadge role={invitation.role} />
                    </TableCell>
                    <TableCell className="hidden md:table-cell">
                      <span className="text-sm text-muted-foreground">
                        {new Date(invitation.created_at).toLocaleDateString('en-US', {
                          month: 'short',
                          day: 'numeric',
                          year: 'numeric',
                        })}
                      </span>
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-muted-foreground hover:text-[var(--fail)]"
                        onClick={() => revokeInvitation.mutate(invitation.id)}
                        disabled={revokeInvitation.isPending}
                        title="Revoke invitation"
                      >
                        <XCircle className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* Role Descriptions */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-muted-foreground" />
            <CardTitle className="text-lg">Role Permissions</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 sm:grid-cols-2">
            {(Object.entries(ROLE_CONFIG) as [MemberRole, typeof ROLE_CONFIG[MemberRole]][]).map(
              ([role, config]) => (
                <div key={role} className="flex items-start gap-3 rounded-lg border border-border p-3">
                  <RoleBadge role={role} />
                  <p className="text-xs text-muted-foreground">{config.description}</p>
                </div>
              )
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
