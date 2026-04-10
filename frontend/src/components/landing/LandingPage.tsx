import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { ROUTES } from '@/lib/constants';
import {
  ShieldCheck,
  AlertTriangle,
  MessageSquare,
  FileWarning,
  Siren,
  FileText,
  ClipboardList,
  Zap,
  DollarSign,
  Clock,
  Ban,
  ChevronDown,
  ChevronUp,
  Check,
  ArrowRight,
  HardHat,
  Lock,
  Star,
  Menu,
  X,
  Mic,
  Timer,
  Users,
  Wrench,
  CalendarCheck,
  Smartphone,
  Globe,
  TrendingDown,
} from 'lucide-react';

/* ------------------------------------------------------------------ */
/*  Logo                                                                */
/* ------------------------------------------------------------------ */

function LogoMark({ size = 28 }: { size?: number }) {
  const iconSize = Math.round(size * 0.53);
  return (
    <div
      className="flex items-center justify-center bg-primary"
      style={{ width: size, height: size, borderRadius: 6 }}
    >
      <svg width={iconSize} height={iconSize} viewBox="0 0 18 18" fill="none">
        <path d="M4 9.5L7.5 13L14 5.5" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Form Section wrapper (reusable)                                     */
/* ------------------------------------------------------------------ */

function FormSection({
  title,
  action,
  children,
  className = '',
}: {
  title: string;
  action?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`bg-white border border-[var(--border)] ${className}`}>
      <div className="flex items-center justify-between px-3 py-2.5 border-b border-[var(--border)] bg-[var(--concrete-50)] lg:px-[18px]">
        <span className="text-[12px] font-bold uppercase tracking-[0.5px] text-[var(--concrete-700)]">
          {title}
        </span>
        {action}
      </div>
      {children}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Navbar                                                              */
/* ------------------------------------------------------------------ */

function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <nav className="sticky top-0 z-50 bg-white border-b border-[var(--border)]">
      <div className="mx-auto flex items-center justify-between px-4 py-3 lg:px-8">
        <Link to="/" className="flex items-center gap-2">
          <LogoMark size={28} />
          <span className="text-[15px] font-bold">
            <span className="text-foreground">Kerf</span>
          </span>
        </Link>

        <div className="hidden items-center gap-5 md:flex">
          <a href="#platform" className="text-[13px] font-medium text-muted-foreground hover:text-foreground">
            Platform
          </a>
          <a href="#documents" className="text-[13px] font-medium text-muted-foreground hover:text-foreground">
            Documents
          </a>
          <a href="#pricing" className="text-[13px] font-medium text-muted-foreground hover:text-foreground">
            Pricing
          </a>
          <a href="#faq" className="text-[13px] font-medium text-muted-foreground hover:text-foreground">
            FAQ
          </a>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" render={<Link to={ROUTES.LOGIN} />}>
            Log In
          </Button>
          <Button
            size="sm"
            className="bg-primary hover:bg-[var(--machine-dark)] text-primary-foreground"
            render={<Link to={ROUTES.SIGNUP} />}
          >
            Get Started Free
          </Button>
          <button
            className="ml-1 p-2 md:hidden"
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label="Toggle menu"
          >
            {mobileOpen ? <X className="size-5" /> : <Menu className="size-5" />}
          </button>
        </div>
      </div>

      {/* Mobile nav */}
      {mobileOpen && (
        <div className="border-t border-[var(--border)] bg-white px-4 py-3 md:hidden">
          <div className="flex flex-col gap-3">
            <a href="#platform" onClick={() => setMobileOpen(false)} className="text-[13px] font-medium text-muted-foreground">Platform</a>
            <a href="#documents" onClick={() => setMobileOpen(false)} className="text-[13px] font-medium text-muted-foreground">Documents</a>
            <a href="#pricing" onClick={() => setMobileOpen(false)} className="text-[13px] font-medium text-muted-foreground">Pricing</a>
            <a href="#faq" onClick={() => setMobileOpen(false)} className="text-[13px] font-medium text-muted-foreground">FAQ</a>
          </div>
        </div>
      )}
    </nav>
  );
}

/* ------------------------------------------------------------------ */
/*  Hero                                                                */
/* ------------------------------------------------------------------ */

function HeroSection() {
  return (
    <section className="bg-white border-b border-[var(--border)]">
      <div className="mx-auto max-w-4xl px-4 py-12 lg:py-16 lg:px-8">
        <div className="max-w-2xl">
          <p className="font-mono text-[11px] font-medium uppercase tracking-[1px] text-[var(--machine-dark)] mb-3">
            Safety &middot; Daily logs &middot; Time tracking &middot; Quality &middot; One app
          </p>
          <h1 className="text-3xl font-bold text-foreground lg:text-4xl leading-tight">
            One site walk.{' '}
            <span className="text-primary">Everything documented.</span>
          </h1>
          <p className="mt-4 text-[15px] text-muted-foreground leading-relaxed">
            Walk your site while Kerf interviews you — it asks what you see, follows up on hazards,
            and prompts for details you&apos;d miss. The conversation becomes your safety inspection,
            daily log, and quality report. Your crew clocks in with a tap. Your certifications
            track themselves. Your Sundays are yours again.
          </p>
          <div className="mt-6 flex flex-col gap-3 sm:flex-row">
            <Button
              size="lg"
              className="bg-primary px-8 text-[13px] font-semibold text-primary-foreground hover:bg-[var(--machine-dark)]"
              render={<Link to={ROUTES.SIGNUP} />}
            >
              Try it free — no credit card
              <ArrowRight className="ml-2 size-4" />
            </Button>
            <Button
              variant="outline"
              size="lg"
              className="px-8 text-[13px] border-[var(--concrete-200)] text-[var(--concrete-600)] hover:border-[var(--concrete-400)]"
              render={<a href="#demo" />}
            >
              See a 2-minute demo
            </Button>
          </div>
        </div>

        {/* What you get strip */}
        <div className="mt-8 flex flex-wrap bg-[var(--concrete-50)] border border-[var(--border)]">
          {[
            { label: 'Safety', detail: 'Inspections & docs' },
            { label: 'Daily Logs', detail: 'Auto-populated' },
            { label: 'Time Tracking', detail: 'GPS clock-in' },
            { label: 'Quality', detail: 'Same walk, extra report' },
            { label: 'Sub Compliance', detail: 'COI & cert tracking' },
            { label: 'Mock OSHA', detail: 'Find gaps first' },
            { label: 'Voice Interview', detail: 'AI asks, you talk' },
          ].map((item, i) => (
            <div
              key={item.label}
              className={`flex-1 min-w-[100px] px-3 py-2.5 ${i < 6 ? 'border-r border-[var(--border)]' : ''}`}
            >
              <div className="font-mono text-[10px] font-medium uppercase tracking-[1px] text-muted-foreground">{item.label}</div>
              <div className="text-[12px] text-foreground mt-0.5 hidden sm:block">{item.detail}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/*  Problem Section                                                     */
/* ------------------------------------------------------------------ */

function ProblemSection() {
  const scenarios = [
    {
      icon: AlertTriangle,
      situation: 'A GC asks for your safety program before awarding the sub',
      reality: 'You scramble to update a 3-year-old Word doc the night before. It looks amateur and you know it.',
      color: 'bg-[var(--warn-bg)]',
      iconColor: 'text-[var(--warn)]',
    },
    {
      icon: Ban,
      situation: "A worker's crane cert expired 2 weeks ago — nobody noticed",
      reality: "If OSHA had walked on site, that's a $16,550 serious violation. And you're operating uninsured for that scope.",
      color: 'bg-[var(--fail-bg)]',
      iconColor: 'text-[var(--fail)]',
    },
    {
      icon: FileText,
      situation: 'Your daily logs are fiction written from memory on Sunday night',
      reality: "You know the logs should match what actually happened. But by Sunday you can't remember if the rebar delivery was Tuesday or Wednesday. Neither can your foreman.",
      color: 'bg-[var(--machine-wash)]',
      iconColor: 'text-[var(--machine-dark)]',
    },
    {
      icon: Timer,
      situation: 'Paper timesheets are costing you $52K a year',
      reality: "Buddy punching, rounding, lost sheets — a 50-person crew loses an average of $52,000 annually to bad time tracking. And you can't allocate costs to the right job.",
      color: 'bg-[var(--fail-bg)]',
      iconColor: 'text-[var(--fail)]',
    },
    {
      icon: DollarSign,
      situation: "You're paying for 4 apps that don't talk to each other",
      reality: "Safety in one app, daily logs in another, time tracking in a third, paper for the rest. Your data lives in silos. Nothing connects.",
      color: 'bg-[var(--warn-bg)]',
      iconColor: 'text-[var(--warn)]',
    },
    {
      icon: Globe,
      situation: "A third of your crew can't read the safety plan",
      reality: "34% of the construction workforce is Hispanic/Latino. Your safety documents are in English. Your toolbox talks are in English. The workers most at risk get the least information.",
      color: 'bg-[var(--machine-wash)]',
      iconColor: 'text-[var(--machine-dark)]',
    },
  ];

  return (
    <section className="bg-[var(--concrete-50)] py-6 lg:py-8">
      <div className="mx-auto max-w-4xl px-4 lg:px-8">
        <FormSection
          title="If any of this is you"
          action={
            <span className="font-mono text-[11px] text-muted-foreground">You&apos;re not alone</span>
          }
        >
          {scenarios.map((s, i) => (
            <div
              key={i}
              className={`flex items-start gap-3 px-3 py-3 lg:px-[18px] ${
                i < scenarios.length - 1 ? 'border-b border-[var(--concrete-50)]' : ''
              }`}
            >
              <div className={`flex size-8 items-center justify-center flex-shrink-0 ${s.color}`}>
                <s.icon className={`size-4 ${s.iconColor}`} />
              </div>
              <div className="min-w-0">
                <div className="text-[13px] font-semibold text-foreground">{s.situation}</div>
                <div className="mt-0.5 text-[12px] text-muted-foreground">{s.reality}</div>
              </div>
            </div>
          ))}
        </FormSection>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/*  Demo Moment — The Marco Story                                       */
/* ------------------------------------------------------------------ */

function DemoSection() {
  return (
    <section id="demo" className="scroll-mt-16 bg-[var(--concrete-50)] pb-6 lg:pb-8">
      <div className="mx-auto max-w-4xl px-4 lg:px-8">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {/* Before */}
          <FormSection title="Before Kerf — Marco's morning">
            <div className="px-3 py-3 lg:px-[18px]">
              <ul className="space-y-2">
                {[
                  'Check weather on phone',
                  'Open App 1 for safety checklist',
                  'Open App 2 for daily log',
                  'Open App 3 for time tracking',
                  'Check email for RFI responses',
                  'Open spreadsheet for schedule',
                  'Sunday night: reconcile all of it',
                ].map((step, i) => (
                  <li key={i} className="flex items-start gap-2 text-[12px] text-[var(--concrete-600)]">
                    <X className="mt-0.5 size-3.5 shrink-0 text-[var(--fail)]" />
                    {step}
                  </li>
                ))}
              </ul>
              <div className="mt-3 px-2 py-1.5 bg-[var(--fail-bg)] text-[12px] font-semibold text-[var(--fail)]">
                6 apps. Paper timesheets. Fiction written from memory.
              </div>
            </div>
          </FormSection>

          {/* After */}
          <FormSection
            title="With Kerf — Marco's morning"
            action={
              <span className="font-mono text-[10px] font-semibold uppercase text-[var(--pass)]">
                One tool
              </span>
            }
          >
            <div className="px-3 py-3 lg:px-[18px]">
              <ul className="space-y-2">
                {[
                  { time: '5:30 AM', text: 'Morning brief is waiting — risk score, weather, expiring certs, today\'s talk' },
                  { time: '6:00 AM', text: 'Deliver toolbox talk in English and Spanish. Crew signs on their phones.' },
                  { time: '6:15 AM', text: 'Walk the site. Kerf interviews you — asks what you see, follows up on hazards.' },
                  { time: '6:23 AM', text: 'Safety inspection, daily log, and quality report are done. Review. Two taps.' },
                  { time: 'Always', text: 'Crew clocked in with GPS. Certs tracked. No paper anywhere.' },
                ].map((step, i) => (
                  <li key={i} className="flex items-start gap-2 text-[12px] text-[var(--concrete-600)]">
                    <Check className="mt-0.5 size-3.5 shrink-0 text-[var(--pass)]" />
                    <div>
                      <span className="font-mono text-[10px] font-semibold text-muted-foreground mr-1.5">{step.time}</span>
                      {step.text}
                    </div>
                  </li>
                ))}
              </ul>
              <div className="mt-3 px-2 py-1.5 bg-[var(--pass-bg)] text-[12px] font-semibold text-[var(--pass)]">
                One walk. Three reports. No forms.
              </div>
            </div>
          </FormSection>
        </div>

        {/* Voice interview callout */}
        <div className="mt-4 bg-white border border-[var(--border)]">
          <div className="flex items-center gap-3 px-3 py-3 lg:px-[18px]">
            <div className="flex size-8 items-center justify-center flex-shrink-0 bg-[var(--machine-wash)]">
              <Mic className="size-4 text-[var(--machine-dark)]" />
            </div>
            <div className="min-w-0">
              <div className="text-[13px] font-semibold text-foreground">
                Not a recording. A conversation.
              </div>
              <div className="mt-0.5 text-[12px] text-muted-foreground leading-relaxed">
                Kerf doesn&apos;t just listen — it interviews you. It asks what you see, follows up on hazards, prompts for
                details a checklist would miss. Like walking the site with a safety director who never forgets a question.
                In English or Spanish.
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/*  How It Works — Platform                                             */
/* ------------------------------------------------------------------ */

function HowItWorksSection() {
  const items = [
    {
      label: '5:30 AM',
      title: 'Morning brief and toolbox talk — ready and waiting',
      description: "Risk score, weather, expiring certs, yesterday's open items, and today's toolbox talk in English and Spanish. Your foreman delivers it, crew signs on their phones. Four minutes, everything covered.",
      tag: 'DAILY',
      tagColor: 'text-[var(--pass)] bg-[var(--pass-bg)]',
    },
    {
      label: '6:15 AM',
      title: 'AI voice interview turns your site walk into three reports',
      description: "Walk the site with Kerf on your phone. It interviews you as you go — asks what you see, follows up on hazards, prompts for quality observations and crew counts. Takes photos when you point. Eight minutes later: safety inspection, daily log, and quality report. Done.",
      tag: 'VOICE AI',
      tagColor: 'text-[var(--machine-dark)] bg-[var(--machine-wash)]',
    },
    {
      label: 'Always on',
      title: 'GPS time tracking and certification management',
      description: "Crew clocks in with one tap — GPS-verified, cost codes auto-assigned. Certifications track themselves with 30-day expiry alerts. Fall protection, NCCCO, OSHA-10, confined space — all in one place. Kerf flags conflicts before they become violations.",
      tag: 'AUTOMATED',
      tagColor: 'text-[var(--warn)] bg-[var(--warn-bg)]',
    },
    {
      label: 'Weekly',
      title: 'Mock OSHA inspection and GC sub compliance',
      description: "Run a full Mock OSHA Inspection — Kerf audits your docs, certs, and inspection history against 1,300 checkpoints and returns findings in citation format with penalty estimates. GC portal gives real-time sub compliance visibility. Seven out of ten COIs are non-compliant — Kerf catches them.",
      tag: 'PROACTIVE',
      tagColor: 'text-[var(--fail)] bg-[var(--fail-bg)]',
    },
  ];

  return (
    <section id="platform" className="scroll-mt-16 bg-[var(--concrete-50)] pb-6 lg:pb-8">
      <div className="mx-auto max-w-4xl px-4 lg:px-8">
        <FormSection
          title="How contractors use Kerf"
          action={
            <span className="text-[11px] font-semibold text-[var(--machine-dark)]">
              One tool, not six
            </span>
          }
        >
          {items.map((item, i) => (
            <div
              key={i}
              className={`flex items-start gap-3 px-3 py-3 lg:px-[18px] ${
                i < items.length - 1 ? 'border-b border-[var(--concrete-50)]' : ''
              }`}
            >
              <div className="w-[80px] flex-shrink-0 hidden sm:block">
                <span className="font-mono text-[10px] font-medium uppercase tracking-[0.5px] text-muted-foreground">
                  {item.label}
                </span>
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-[13px] font-semibold text-foreground">{item.title}</span>
                  <span className={`font-mono text-[10px] font-semibold uppercase px-1.5 py-0.5 flex-shrink-0 hidden md:inline ${item.tagColor}`}>
                    {item.tag}
                  </span>
                </div>
                <div className="mt-0.5 text-[12px] text-muted-foreground leading-relaxed">{item.description}</div>
              </div>
            </div>
          ))}
        </FormSection>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/*  What You Can Cancel — Consolidation                                 */
/* ------------------------------------------------------------------ */

function ConsolidationSection() {
  const tools = [
    { label: 'Safety app', cost: '$300–600/mo', icon: ShieldCheck },
    { label: 'Daily log app', cost: '$150–400/mo', icon: ClipboardList },
    { label: 'Time tracker', cost: '$100–375/mo', icon: Timer },
    { label: 'Paper forms & fines', cost: 'Priceless', icon: FileWarning },
  ];

  return (
    <section className="bg-[var(--concrete-50)] pb-6 lg:pb-8">
      <div className="mx-auto max-w-4xl px-4 lg:px-8">
        <FormSection
          title="What you can cancel"
          action={
            <span className="font-mono text-[11px] text-muted-foreground">For a 25-person crew</span>
          }
        >
          {tools.map((tool, i) => (
            <div
              key={tool.label}
              className={`flex items-center justify-between px-3 py-2.5 lg:px-[18px] ${
                i < tools.length - 1 ? 'border-b border-[var(--concrete-50)]' : ''
              }`}
            >
              <div className="flex items-center gap-3">
                <tool.icon className="size-4 text-muted-foreground" />
                <span className="text-[13px] text-[var(--concrete-600)]">{tool.label}</span>
              </div>
              <span className="font-mono text-[12px] text-[var(--fail)] font-medium">{tool.cost}</span>
            </div>
          ))}

          {/* Total row */}
          <div className="flex items-center justify-between px-3 py-2.5 border-t border-[var(--border)] bg-[var(--concrete-50)] lg:px-[18px]">
            <span className="text-[13px] font-semibold text-[var(--concrete-600)]">
              Typical combined cost
            </span>
            <span className="font-mono text-[13px] text-[var(--fail)] font-bold line-through">
              $1,275/mo
            </span>
          </div>
          <div className="flex items-center justify-between px-3 py-3 border-t border-[var(--border)] bg-[var(--machine-wash)] lg:px-[18px]">
            <div className="flex items-center gap-3">
              <LogoMark size={20} />
              <span className="text-[13px] font-bold text-foreground">
                Kerf Professional — everything above, plus quality inspections and sub compliance
              </span>
            </div>
            <span className="font-mono text-[16px] text-foreground font-bold">
              $299/mo
            </span>
          </div>
        </FormSection>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/*  Document Types                                                      */
/* ------------------------------------------------------------------ */

function DocumentTypesSection() {
  const docTypes = [
    {
      icon: ShieldCheck,
      name: 'Site-Specific Safety Plan (SSSP)',
      description:
        'Complete, site-specific safety plans generated from your voice interview data and project details. Not a template with blanks — a professional document with the correct regulatory citations.',
      oshaLine: 'Required by OSHA for multi-employer construction sites.',
    },
    {
      icon: AlertTriangle,
      name: 'Job Hazard Analysis (JHA)',
      description:
        'Task-specific JHAs with hazard identification and controls mapped to OSHA standards. Generated from your project scope and the hazards surfaced during site walk interviews.',
      oshaLine: 'Required by OSHA 29 CFR 1926 for hazardous job tasks.',
    },
    {
      icon: MessageSquare,
      name: 'Toolbox Talk Record',
      description:
        'Daily safety briefings in English and Spanish with digital crew sign-off. Topics generated from your project risks, weather, and recent incidents.',
      oshaLine: 'Required by OSHA for ongoing safety training documentation.',
    },
    {
      icon: FileWarning,
      name: 'Incident Report',
      description:
        'Kerf interviews your foreman about what happened, asks clarifying questions, classifies recordability, and generates the complete report with root cause analysis.',
      oshaLine: 'Required by OSHA 29 CFR 1904 for recordable incidents.',
    },
    {
      icon: Siren,
      name: 'Emergency Action Plan',
      description:
        'Site-specific emergency procedures covering evacuation routes, contacts, and response protocols — generated from your project location and scope.',
      oshaLine: 'Required by OSHA 29 CFR 1926.35 for all construction sites.',
    },
  ];

  return (
    <section id="documents" className="scroll-mt-16 bg-[var(--concrete-50)] pb-6 lg:pb-8">
      <div className="mx-auto max-w-4xl px-4 lg:px-8">
        <FormSection title="AI-generated safety documents">
          {/* Table header */}
          <div className="hidden sm:grid grid-cols-[1fr_200px] px-3 py-1.5 border-b border-[var(--border)] bg-[var(--concrete-50)] lg:px-[18px]">
            <span className="font-mono text-[10px] font-semibold uppercase tracking-[0.5px] text-muted-foreground">
              Document Type
            </span>
            <span className="font-mono text-[10px] font-semibold uppercase tracking-[0.5px] text-muted-foreground">
              OSHA Requirement
            </span>
          </div>
          {docTypes.map((doc, i) => (
            <div
              key={doc.name}
              className={`px-3 py-3 lg:px-[18px] ${
                i < docTypes.length - 1 ? 'border-b border-[var(--concrete-50)]' : ''
              }`}
            >
              <div className="sm:grid sm:grid-cols-[1fr_200px] sm:items-start sm:gap-4">
                <div className="flex items-start gap-3">
                  <doc.icon className="size-4 text-primary flex-shrink-0 mt-0.5" />
                  <div className="min-w-0">
                    <div className="text-[13px] font-semibold text-foreground">{doc.name}</div>
                    <div className="mt-0.5 text-[12px] text-muted-foreground">{doc.description}</div>
                  </div>
                </div>
                <div className="mt-2 sm:mt-0 flex items-start gap-1.5 pl-7 sm:pl-0">
                  <Lock className="size-3 text-muted-foreground flex-shrink-0 mt-0.5" />
                  <span className="font-mono text-[11px] text-muted-foreground">{doc.oshaLine}</span>
                </div>
              </div>
            </div>
          ))}
          <div className="px-3 py-3 border-t border-[var(--border)] bg-[var(--concrete-50)] lg:px-[18px]">
            <span className="text-[12px] text-muted-foreground">
              Every document is generated from your voice interview data and project context — not a template with blanks.
            </span>
          </div>
        </FormSection>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/*  Pricing                                                             */
/* ------------------------------------------------------------------ */

function PricingSection() {
  const plans = [
    {
      name: 'Starter',
      price: '$99',
      period: '/month',
      description: 'For small contractors getting started.',
      safetyFeatures: [
        '2 projects',
        'All document generation',
        'Inspections & toolbox talks',
        'Mock OSHA Inspection',
        'Morning Brief',
        'Bilingual (EN/ES)',
      ],
      opsFeatures: [
        'GPS time tracking',
      ],
      cta: 'Start Free Trial',
      highlighted: false,
    },
    {
      name: 'Professional',
      price: '$299',
      period: '/month',
      description: 'For active contractors with multiple projects.',
      safetyFeatures: [
        '8 projects',
        'Everything in Starter',
        'AI voice interview',
        'Photo hazard assessment',
        'Certification tracking',
        'Prequalification automation',
      ],
      opsFeatures: [
        'Daily logs (auto-populated)',
        'Quality inspections',
      ],
      cta: 'Start Free Trial',
      highlighted: true,
    },
    {
      name: 'Business',
      price: '$499',
      period: '/month',
      description: 'For companies managing multiple crews.',
      safetyFeatures: [
        '20 projects',
        'Everything in Professional',
        'EMR modeling',
        'Predictive risk scoring',
        'GC portal',
      ],
      opsFeatures: [
        'Equipment management',
        'Expanded sub compliance',
      ],
      cta: 'Start Free Trial',
      highlighted: false,
    },
    {
      name: 'Enterprise',
      price: 'Custom',
      period: '',
      description: 'For large organizations.',
      safetyFeatures: [
        'Unlimited projects',
        'Everything in Business',
        'State-specific compliance',
        'Custom templates',
        'White-label branding',
      ],
      opsFeatures: [
        'API access',
        'SSO integration',
        'Dedicated CSM',
      ],
      cta: 'Contact Sales',
      highlighted: false,
    },
  ];

  return (
    <section id="pricing" className="scroll-mt-16 bg-[var(--concrete-50)] pb-6 lg:pb-8">
      <div className="mx-auto max-w-5xl px-4 lg:px-8">
        <div className="mb-4">
          <h2 className="text-[16px] font-bold text-foreground">Simple, Transparent Pricing</h2>
          <p className="mt-1 text-[13px] text-muted-foreground">
            Per-project pricing with unlimited users. Every tier. No per-seat fees, ever.
          </p>
        </div>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`bg-white border flex flex-col ${
                plan.highlighted
                  ? 'border-primary'
                  : 'border-[var(--border)]'
              }`}
            >
              {/* Header */}
              <div className={`flex items-center justify-between px-3 py-2.5 border-b bg-[var(--concrete-50)] lg:px-[18px] ${
                plan.highlighted ? 'border-primary' : 'border-[var(--border)]'
              }`}>
                <span className="text-[12px] font-bold uppercase tracking-[0.5px] text-[var(--concrete-700)]">
                  {plan.name}
                </span>
                {plan.highlighted && (
                  <span className="bg-primary text-primary-foreground font-mono text-[10px] font-semibold uppercase tracking-[0.5px] px-1.5 py-0.5">
                    Most Popular
                  </span>
                )}
              </div>

              {/* Price */}
              <div className="px-3 py-3 border-b border-[var(--concrete-50)] lg:px-[18px]">
                <div className="flex items-baseline gap-1">
                  <span className="text-[26px] font-bold text-foreground tracking-tight">{plan.price}</span>
                  <span className="font-mono text-[11px] text-muted-foreground">{plan.period}</span>
                </div>
                <p className="mt-1 text-[12px] text-muted-foreground">{plan.description}</p>
              </div>

              {/* Safety features */}
              <div className="flex-1 px-3 py-3 lg:px-[18px]">
                <div className="font-mono text-[10px] font-semibold uppercase tracking-[0.5px] text-muted-foreground mb-2">
                  Safety
                </div>
                <ul className="space-y-2">
                  {plan.safetyFeatures.map((feature) => (
                    <li key={feature} className="flex items-start gap-2 text-[12px] text-[var(--concrete-600)]">
                      <Check className="mt-0.5 size-3.5 shrink-0 text-[var(--pass)]" />
                      {feature}
                    </li>
                  ))}
                </ul>

                {/* Ops features */}
                <div className="font-mono text-[10px] font-semibold uppercase tracking-[0.5px] text-[var(--machine-dark)] mt-3 mb-2">
                  Operations
                </div>
                <ul className="space-y-2">
                  {plan.opsFeatures.map((feature) => (
                    <li key={feature} className="flex items-start gap-2 text-[12px] text-[var(--concrete-600)]">
                      <Check className="mt-0.5 size-3.5 shrink-0 text-primary" />
                      {feature}
                    </li>
                  ))}
                </ul>
              </div>

              {/* CTA */}
              <div className="px-3 py-3 border-t border-[var(--concrete-50)] lg:px-[18px]">
                <Button
                  className={`w-full text-[13px] ${
                    plan.highlighted
                      ? 'bg-primary text-primary-foreground hover:bg-[var(--machine-dark)]'
                      : 'bg-[var(--concrete-900)] text-white hover:bg-[var(--concrete-800)]'
                  }`}
                  render={<Link to={ROUTES.SIGNUP} />}
                >
                  {plan.cta}
                </Button>
              </div>
            </div>
          ))}
        </div>
        <p className="mt-3 text-center font-mono text-[11px] text-muted-foreground">
          25% off with annual billing. 14-day free trial of Professional. No credit card required.
        </p>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/*  Trust / Social Proof                                                */
/* ------------------------------------------------------------------ */

function TrustSection() {
  return (
    <section className="bg-[var(--concrete-50)] pb-6 lg:pb-8">
      <div className="mx-auto max-w-4xl px-4 lg:px-8">
        <FormSection title="Built for how construction actually works">
          <div className="grid grid-cols-1 sm:grid-cols-3 divide-y sm:divide-y-0 sm:divide-x divide-[var(--border)]">
            <div className="px-3 py-3 lg:px-[18px]">
              <div className="flex items-center gap-0.5 mb-2">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Star key={i} className="size-3.5 fill-primary text-primary" />
                ))}
              </div>
              <p className="text-[13px] text-[var(--concrete-600)] leading-relaxed">
                &ldquo;We were paying a consultant $1,200 per safety plan. Kerf does it in
                10 minutes and the output is better — it actually references the right CFR sections
                for our scope.&rdquo;
              </p>
              <div className="mt-2">
                <span className="text-[13px] font-semibold text-foreground">Mike R.</span>
                <span className="text-[12px] text-muted-foreground"> — GC, 14 employees, Austin TX</span>
              </div>
            </div>
            <div className="px-3 py-3 lg:px-[18px]">
              <div className="flex items-center gap-0.5 mb-2">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Star key={i} className="size-3.5 fill-primary text-primary" />
                ))}
              </div>
              <p className="text-[13px] text-[var(--concrete-600)] leading-relaxed">
                &ldquo;The cert tracking alone is worth it. We had a guy running a boom lift with
                an expired NCCCO — Kerf flagged it a month before expiry. That would have
                been a $16k fine.&rdquo;
              </p>
              <div className="mt-2">
                <span className="text-[13px] font-semibold text-foreground">Sarah K.</span>
                <span className="text-[12px] text-muted-foreground"> — Safety Manager, 40 employees, Denver CO</span>
              </div>
            </div>
            <div className="px-3 py-3 lg:px-[18px]">
              <div className="flex items-center gap-0.5 mb-2">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Star key={i} className="size-3.5 fill-primary text-primary" />
                ))}
              </div>
              <p className="text-[13px] text-[var(--concrete-600)] leading-relaxed">
                &ldquo;I did my site walk, talked to the app, and the safety report, daily log,
                and quality check all wrote themselves. I cancelled two other subscriptions
                the same week.&rdquo;
              </p>
              <div className="mt-2">
                <span className="text-[13px] font-semibold text-foreground">Dave M.</span>
                <span className="text-[12px] text-muted-foreground"> — Superintendent, 38 employees, Houston TX</span>
              </div>
            </div>
          </div>
        </FormSection>

        {/* What it replaces */}
        <div className="mt-4 flex flex-wrap bg-white border border-[var(--border)]">
          {[
            { label: 'Replaces', value: 'Safety binder, daily log app, time tracker, paper forms' },
            { label: 'Cost', value: 'From $99/mo vs $1,275/mo in separate tools' },
            { label: 'Standards', value: 'OSHA 29 CFR 1926, ISO 45001, ANSI Z10' },
          ].map((item, i) => (
            <div
              key={item.label}
              className={`flex-1 min-w-[180px] px-3 py-2.5 lg:px-[18px] ${i < 2 ? 'border-r border-[var(--border)]' : ''}`}
            >
              <div className="font-mono text-[10px] font-medium uppercase tracking-[1px] text-muted-foreground">{item.label}</div>
              <div className="text-[12px] text-foreground mt-0.5">{item.value}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/*  FAQ                                                                 */
/* ------------------------------------------------------------------ */

function FAQItem({
  question,
  answer,
}: {
  question: string;
  answer: string;
}) {
  const [open, setOpen] = useState(false);
  return (
    <button
      onClick={() => setOpen(!open)}
      className="flex flex-col w-full text-left px-3 py-2.5 border-b border-[var(--concrete-50)] last:border-b-0 lg:px-[18px]"
    >
      <div className="flex items-center justify-between w-full">
        <span className="text-[13px] font-medium text-foreground pr-4">{question}</span>
        {open ? (
          <ChevronUp className="size-4 shrink-0 text-muted-foreground" />
        ) : (
          <ChevronDown className="size-4 shrink-0 text-muted-foreground" />
        )}
      </div>
      {open && (
        <div className="mt-2 text-[12px] leading-relaxed text-muted-foreground">{answer}</div>
      )}
    </button>
  );
}

function FAQSection() {
  const faqs = [
    {
      question: 'How does the AI voice interview work?',
      answer:
        'When you start a site walk, Kerf opens a conversation — it asks what you see, follows up on hazards, prompts for details about crew count, equipment, and weather. It\'s like walking the site with a safety director who never forgets a question. The conversation is transcribed, structured, and turned into your inspection report, daily log, and quality observations. In English or Spanish.',
    },
    {
      question: 'Will my crew actually use it?',
      answer:
        'Kerf is built for the foreman, not the office. Every field task takes three taps or less. Voice interview means no typing — talk and take photos. Spanish-speaking workers use it in their language natively, not through a translation layer. Clock-in is one tap with GPS. If a foreman can\'t finish a task in two minutes, it doesn\'t ship.',
    },
    {
      question: 'Are the documents actually OSHA-compliant?',
      answer:
        'Yes. Every generated document references current OSHA 29 CFR 1926 standards with the correct regulatory citations. Documents are reviewed against applicable standards for your trade, project type, and jurisdiction. We update whenever OSHA revises standards.',
    },
    {
      question: 'Can I replace my daily log app with Kerf?',
      answer:
        'Yes. On Professional plans and above, Kerf auto-populates your daily log from data captured during your morning site walk interview — weather, crew count, equipment on site, safety observations, quality notes. You add the work-completed narrative and tap submit. What used to take 30 minutes of writing after a long day now takes a 5-minute review.',
    },
    {
      question: 'What about time tracking?',
      answer:
        'GPS-verified clock-in and clock-out on every tier starting at Starter. One tap for the worker. Cost codes auto-assigned from project. No paper timesheets. Bad time tracking costs a 50-person crew roughly $52,000 a year — Kerf eliminates buddy punching, rounding, and lost sheets.',
    },
    {
      question: 'Does it work in Spanish?',
      answer:
        'Yes — and not as a translation. Spanish is a first-class language in Kerf. The voice interview works in Spanish. Toolbox talks are generated in both English and Spanish. Hazard reports can be submitted in Spanish with a voice note and photo. 34% of the US construction workforce is Hispanic/Latino. They deserve safety information in their language.',
    },
    {
      question: 'Does it work offline?',
      answer:
        'Every field function works fully offline with automatic sync when connectivity returns. Construction sites have dead zones in basements, tunnels, and rural areas. Your voice interview records locally and processes through cloud AI when you\'re back online.',
    },
    {
      question: 'Do you offer refunds?',
      answer:
        'Yes. If you\'re not satisfied within the first 30 days of a paid plan, we\'ll issue a full refund — no questions asked. After 30 days, you can cancel anytime and your plan stays active through the end of the billing period.',
    },
  ];

  return (
    <section id="faq" className="scroll-mt-16 bg-[var(--concrete-50)] pb-6 lg:pb-8">
      <div className="mx-auto max-w-4xl px-4 lg:px-8">
        <FormSection title="Frequently Asked Questions">
          {faqs.map((faq) => (
            <FAQItem key={faq.question} question={faq.question} answer={faq.answer} />
          ))}
        </FormSection>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/*  CTA Footer                                                          */
/* ------------------------------------------------------------------ */

function FooterCTA() {
  return (
    <section className="bg-[var(--concrete-50)] pb-6 lg:pb-8">
      <div className="mx-auto max-w-4xl px-4 lg:px-8">
        <FormSection title="Your foreman opens one app tomorrow morning">
          <div className="px-3 py-4 lg:px-[18px]">
            <p className="text-[15px] font-semibold text-foreground">
              Everything else takes care of itself.
            </p>
            <p className="mt-2 max-w-xl text-[13px] text-muted-foreground leading-relaxed">
              The morning brief is waiting. The toolbox talk is ready in English and Spanish.
              The site walk becomes three reports. The crew clocks in with a tap.
              And Sunday night? That&apos;s yours again.
            </p>
            <div className="mt-4 flex flex-col gap-3 sm:flex-row">
              <Button
                size="lg"
                className="bg-primary px-8 text-[13px] font-semibold text-primary-foreground hover:bg-[var(--machine-dark)]"
                render={<Link to={ROUTES.SIGNUP} />}
              >
                Start free — takes 2 minutes
                <ArrowRight className="ml-2 size-4" />
              </Button>
              <Button
                variant="outline"
                size="lg"
                className="px-8 text-[13px] border-[var(--concrete-200)] text-[var(--concrete-600)] hover:border-[var(--concrete-400)]"
                render={<Link to={ROUTES.SIGNUP} />}
              >
                Run your free Mock Inspection
              </Button>
            </div>
            <p className="mt-3 font-mono text-[11px] text-muted-foreground">
              No credit card. 14-day Professional trial. Unlimited users on every plan.
            </p>
          </div>
        </FormSection>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/*  Footer                                                              */
/* ------------------------------------------------------------------ */

function Footer() {
  return (
    <footer className="bg-white border-t border-[var(--border)]">
      <div className="mx-auto flex flex-col items-center justify-between gap-4 px-4 py-4 md:flex-row lg:px-8">
        <div className="flex items-center gap-2">
          <LogoMark size={22} />
          <span className="text-[13px] font-bold">
            <span className="text-foreground">Kerf</span>
          </span>
        </div>
        <div className="flex items-center gap-5">
          <a href="/privacy" className="font-mono text-[11px] text-muted-foreground hover:text-[var(--concrete-600)]">
            Privacy Policy
          </a>
          <a href="/terms" className="font-mono text-[11px] text-muted-foreground hover:text-[var(--concrete-600)]">
            Terms of Service
          </a>
          <a href="mailto:support@kerf.build" className="font-mono text-[11px] text-muted-foreground hover:text-[var(--concrete-600)]">
            Contact
          </a>
        </div>
        <p className="font-mono text-[10px] text-muted-foreground">
          &copy; {new Date().getFullYear()} Kerf. All rights reserved.
        </p>
      </div>
    </footer>
  );
}

/* ------------------------------------------------------------------ */
/*  Main Landing Page                                                   */
/* ------------------------------------------------------------------ */

export function LandingPage() {
  return (
    <div className="min-h-screen scroll-smooth bg-[var(--concrete-50)]">
      <Navbar />
      <HeroSection />
      <ProblemSection />
      <DemoSection />
      <HowItWorksSection />
      <ConsolidationSection />
      <DocumentTypesSection />
      <PricingSection />
      <TrustSection />
      <FAQSection />
      <FooterCTA />
      <Footer />
    </div>
  );
}
