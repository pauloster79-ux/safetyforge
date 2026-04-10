import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';

export type MemberRole = 'owner' | 'admin' | 'editor' | 'viewer';
export type InvitationStatus = 'pending' | 'accepted' | 'expired' | 'revoked';

export interface Member {
  id: string;
  company_id: string;
  uid: string;
  email: string;
  display_name: string;
  role: MemberRole;
  invited_by: string | null;
  joined_at: string;
  created_at: string;
  updated_at: string;
}

export interface Invitation {
  id: string;
  company_id: string;
  company_name: string;
  email: string;
  role: MemberRole;
  status: InvitationStatus;
  invited_by: string;
  invited_by_email: string;
  token: string;
  expires_at: string;
  created_at: string;
  accepted_at: string | null;
}

export function useMembers() {
  return useQuery<Member[]>({
    queryKey: ['members'],
    queryFn: () => api.get<Member[]>('/me/members'),
  });
}

export function useInvitations() {
  return useQuery<Invitation[]>({
    queryKey: ['invitations'],
    queryFn: () => api.get<Invitation[]>('/me/members/invitations'),
  });
}

export function useInviteMember() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { email: string; role: MemberRole }) =>
      api.post<Invitation>('/me/members/invite', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invitations'] });
    },
  });
}

export function useUpdateMemberRole() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ memberId, role }: { memberId: string; role: MemberRole }) =>
      api.patch<Member>(`/me/members/${memberId}`, { role }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['members'] });
    },
  });
}

export function useRemoveMember() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (memberId: string) =>
      api.delete(`/me/members/${memberId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['members'] });
    },
  });
}

export function useRevokeInvitation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (invitationId: string) =>
      api.delete(`/me/members/invitations/${invitationId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invitations'] });
    },
  });
}
