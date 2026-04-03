import { useState } from 'react';
import {
  MapPin,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Loader2,
  Search,
  Info,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { ComplianceRing } from '@/components/projects/ComplianceRing';
import type { StateRequirement, StateComplianceResult } from '@/lib/constants';

const AVAILABLE_STATES = [
  'California',
  'New York',
  'Washington',
  'Oregon',
  'Michigan',
] as const;

function useStateRequirements(state: string) {
  return useQuery<StateRequirement[]>({
    queryKey: ['state-compliance', 'requirements', state],
    queryFn: () => api.get<StateRequirement[]>(`/me/state-compliance/requirements?state=${encodeURIComponent(state)}`),
    enabled: !!state,
  });
}

function useStateComplianceCheck(state: string) {
  return useQuery<StateComplianceResult>({
    queryKey: ['state-compliance', 'check', state],
    queryFn: () => api.get<StateComplianceResult>(`/me/state-compliance/check?state=${encodeURIComponent(state)}`),
    enabled: !!state,
  });
}

function RequirementRow({ requirement, isGap }: { requirement: StateRequirement; isGap: boolean }) {
  return (
    <div className="flex items-start gap-3 rounded-lg border p-3">
      {isGap ? (
        <XCircle className="mt-0.5 h-5 w-5 shrink-0 text-[var(--fail)]" />
      ) : (
        <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-[var(--pass)]" />
      )}
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <p className="text-sm font-medium text-[var(--concrete-600)]">{requirement.requirement_name}</p>
          <Badge className={
            requirement.severity === 'mandatory'
              ? 'bg-[var(--fail-bg)] text-[var(--fail)] text-[10px] hover:bg-[var(--fail-bg)]'
              : 'bg-[var(--info-bg)] text-[var(--info)] text-[10px] hover:bg-[var(--info-bg)]'
          }>
            {requirement.severity}
          </Badge>
        </div>
        <p className="mt-1 text-xs text-muted-foreground">{requirement.description}</p>
        <p className="mt-1 text-xs text-muted-foreground">
          Standard: <span className="font-medium">{requirement.state_standard}</span>
        </p>
      </div>
    </div>
  );
}

function GapDetail({ gap }: { gap: { requirement: string; status: string; action_needed: string } }) {
  return (
    <div className="flex items-start gap-3 rounded-lg border border-[var(--fail)] bg-[var(--fail-bg)] p-3">
      <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-[var(--fail)]" />
      <div>
        <p className="text-sm font-medium text-[var(--fail)]">{gap.requirement}</p>
        <p className="mt-1 text-xs text-[var(--fail)]">{gap.action_needed}</p>
      </div>
    </div>
  );
}

export function StateCompliancePage() {
  const [selectedState, setSelectedState] = useState<string>('');

  const { data: requirements, isLoading: reqLoading } = useStateRequirements(selectedState);
  const { data: compliance, isLoading: compLoading } = useStateComplianceCheck(selectedState);

  const isLoading = reqLoading || compLoading;

  // Determine which requirements are gaps
  const gapNames = new Set(compliance?.gaps.map(g => g.requirement) ?? []);

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">State Compliance</h1>
        <p className="text-sm text-muted-foreground">
          Check your compliance against state-specific safety requirements beyond federal OSHA
        </p>
      </div>

      {/* State selector */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-end gap-4">
            <div className="flex-1 space-y-2">
              <label className="text-sm font-medium text-[var(--concrete-600)]">Select State</label>
              <Select value={selectedState} onValueChange={(v) => { if (v) setSelectedState(v); }}>
                <SelectTrigger>
                  <SelectValue placeholder="Choose a state to check compliance" />
                </SelectTrigger>
                <SelectContent>
                  {AVAILABLE_STATES.map(state => (
                    <SelectItem key={state} value={state}>
                      <div className="flex items-center gap-2">
                        <MapPin className="h-3.5 w-3.5 text-muted-foreground" />
                        {state}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {selectedState && (
              <Button
                variant="outline"
                className="border-primary text-[var(--machine-dark)] hover:bg-[var(--machine-wash)]"
                onClick={() => setSelectedState(selectedState)}
              >
                <Search className="mr-2 h-4 w-4" />
                Re-check
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Loading state */}
      {isLoading && selectedState && (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      )}

      {/* Results */}
      {!isLoading && selectedState && compliance && requirements && (
        <>
          {/* State header + score */}
          <div className="grid gap-4 sm:grid-cols-3">
            <Card>
              <CardContent className="flex flex-col items-center pt-6">
                <ComplianceRing score={compliance.compliance_percentage} size="lg" />
                <p className="mt-2 text-sm font-semibold text-[var(--concrete-600)]">{selectedState}</p>
                <p className="text-xs text-muted-foreground">
                  {compliance.met_requirements} of {compliance.total_requirements} requirements met
                </p>
              </CardContent>
            </Card>
            <Card className="sm:col-span-2">
              <CardContent className="pt-6">
                <div className="flex items-start gap-3">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[var(--info-bg)]">
                    <Info className="h-5 w-5 text-[var(--info)]" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-foreground">
                      {selectedState} requires {compliance.total_requirements} standard{compliance.total_requirements !== 1 ? 's' : ''} beyond federal OSHA
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {compliance.gaps.length > 0
                        ? `You have ${compliance.gaps.length} gap${compliance.gaps.length !== 1 ? 's' : ''} to address before working in ${selectedState}.`
                        : `You are fully compliant with ${selectedState} state-specific requirements.`}
                    </p>
                    {compliance.gaps.length > 0 && (
                      <div className="mt-3 flex items-center gap-4">
                        <div className="flex items-center gap-1">
                          <CheckCircle2 className="h-4 w-4 text-[var(--pass)]" />
                          <span className="text-xs text-muted-foreground">{compliance.met_requirements} met</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <XCircle className="h-4 w-4 text-[var(--fail)]" />
                          <span className="text-xs text-muted-foreground">{compliance.gaps.length} gaps</span>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Gaps section */}
          {compliance.gaps.length > 0 && (
            <Card className="border-[var(--fail)]">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg text-[var(--fail)]">
                  <AlertTriangle className="h-5 w-5 text-[var(--fail)]" />
                  Compliance Gaps ({compliance.gaps.length})
                </CardTitle>
                <CardDescription>
                  Actions needed to meet {selectedState} state requirements
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {compliance.gaps.map((gap, i) => (
                  <GapDetail key={i} gap={gap} />
                ))}
              </CardContent>
            </Card>
          )}

          {/* Full requirements list */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">All {selectedState} Requirements</CardTitle>
              <CardDescription>
                State-specific safety requirements beyond federal OSHA standards
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {requirements.map(req => (
                <RequirementRow
                  key={req.id}
                  requirement={req}
                  isGap={gapNames.has(req.requirement_name)}
                />
              ))}
            </CardContent>
          </Card>
        </>
      )}

      {/* No state selected */}
      {!selectedState && (
        <Card>
          <CardContent className="flex flex-col items-center py-12 text-center">
            <MapPin className="h-12 w-12 text-muted-foreground" />
            <p className="mt-3 text-sm font-medium text-muted-foreground">Select a state to check compliance</p>
            <p className="mt-1 max-w-sm text-xs text-muted-foreground">
              Each state has unique safety requirements beyond federal OSHA. Select a state above to see what additional standards apply and check your current compliance status.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
