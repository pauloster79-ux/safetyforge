/**
 * CardRenderer — selects the right card component based on tool name.
 *
 * Maps tool_result event tool names to specialized card components.
 * Falls back to GenericEntityCard for unrecognized tools.
 */

import { AssumptionCard } from './AssumptionCard';
import { ApplyInsightCard } from './ApplyInsightCard';
import { ExclusionCard } from './ExclusionCard';
import { InsightCard } from './InsightCard';
import { InsightConfirmationCard } from './InsightConfirmationCard';
import { ProjectSummaryCard } from './ProjectSummaryCard';
import { ComplianceStatusCard } from './ComplianceStatusCard';
import { DailyLogCard } from './DailyLogCard';
import { MorningBriefCard } from './MorningBriefCard';
import { InspectionCard } from './InspectionCard';
import { WorkItemCard } from './WorkItemCard';
import { LeadCard } from './LeadCard';
import { CapacityCard } from './CapacityCard';
import { ScheduleCard } from './ScheduleCard';
import { ConflictAlertCard } from './ConflictAlertCard';
import { SubComplianceCard } from './SubComplianceCard';
import { SubPerformanceCard } from './SubPerformanceCard';
import { EstimateSummaryCard } from './EstimateSummaryCard';
import { ProposalCard } from './ProposalCard';
import { InvoiceCard } from './InvoiceCard';
import { PaymentStatusCard } from './PaymentStatusCard';
import { TimeEntryCard } from './TimeEntryCard';
import { QualityCard } from './QualityCard';
import { JobCostCard } from './JobCostCard';
import { VariationCard } from './VariationCard';
import { FinancialOverviewCard } from './FinancialOverviewCard';
import { GenericEntityCard } from './GenericEntityCard';

interface CardRendererProps {
  toolName: string;
  result: Record<string, unknown>;
}

/** Map tool names (or prefixes) to card components */
const TOOL_CARD_MAP: Record<string, React.ComponentType<{ result: Record<string, unknown> }>> = {
  get_project_summary: ProjectSummaryCard,
  get_project_details: ProjectSummaryCard,
  check_worker_compliance: ComplianceStatusCard,
  check_project_compliance: ComplianceStatusCard,
  check_compliance: ComplianceStatusCard,
  get_compliance_status: ComplianceStatusCard,
  get_daily_log_status: DailyLogCard,
  get_daily_logs: DailyLogCard,
  generate_morning_brief: MorningBriefCard,
  get_morning_brief: MorningBriefCard,
  get_inspection: InspectionCard,
  get_inspection_details: InspectionCard,
  create_inspection: InspectionCard,
  get_work_item: WorkItemCard,
  create_work_item: WorkItemCard,
  // Execute & Document
  create_daily_log: DailyLogCard,
  auto_populate_daily_log: DailyLogCard,
  record_time: TimeEntryCard,
  report_quality_observation: QualityCard,
  // Manage Money
  get_job_cost_summary: JobCostCard,
  detect_variation: VariationCard,
  create_variation: VariationCard,
  get_financial_overview: FinancialOverviewCard,
  // Find & Qualify Work
  capture_lead: LeadCard,
  qualify_project: LeadCard,
  check_capacity: CapacityCard,
  // Plan & Mobilise
  get_schedule: ScheduleCard,
  assign_workers: WorkItemCard,
  detect_conflicts: ConflictAlertCard,
  // Sub Management
  check_sub_compliance: SubComplianceCard,
  list_subs: SubComplianceCard,
  get_sub_performance: SubPerformanceCard,
  // Assumptions & Exclusions
  add_assumption: AssumptionCard,
  update_assumption: AssumptionCard,
  // remove_assumption falls through to GenericEntityCard via the default fallback
  add_exclusion: ExclusionCard,
  update_exclusion: ExclusionCard,
  // Layer 4: Knowledge accumulation
  create_insight: InsightCard,
  apply_insight: ApplyInsightCard,
  // Proposal-before-save flow — shown when the agent surfaces a candidate
  // pattern for user confirmation rather than committing directly.
  offer_insight_capture: InsightConfirmationCard,
  propose_insight: InsightConfirmationCard,
  // remove_exclusion falls through to GenericEntityCard via the default fallback
  // Estimate & Price
  update_work_item: WorkItemCard,
  get_estimate_summary: EstimateSummaryCard,
  // search_historical_rates has a different shape — use GenericEntityCard via fallback
  add_item_to_work_item: WorkItemCard,
  // Propose & Win
  generate_proposal: ProposalCard,
  update_project_status: ProjectSummaryCard,
  // Get Paid
  generate_invoice: InvoiceCard,
  track_payment_status: PaymentStatusCard,
  record_payment: InvoiceCard,
};

export function CardRenderer({ toolName, result }: CardRendererProps) {
  // Direct match
  const Card = TOOL_CARD_MAP[toolName];
  if (Card) return <Card result={result} />;

  // Prefix matching for namespaced tools (e.g., "compliance_check_worker")
  for (const [key, Component] of Object.entries(TOOL_CARD_MAP)) {
    if (toolName.includes(key) || key.includes(toolName)) {
      return <Component result={result} />;
    }
  }

  // Fallback
  return <GenericEntityCard toolName={toolName} result={result} />;
}
