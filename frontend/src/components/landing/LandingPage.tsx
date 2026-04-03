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
            <span className="text-foreground">Safety</span>
            <span className="text-primary">Forge</span>
          </span>
        </Link>

        <div className="hidden items-center gap-5 md:flex">
          <a href="#how-it-works" className="text-[13px] font-medium text-muted-foreground hover:text-foreground">
            How It Works
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
            <a href="#how-it-works" onClick={() => setMobileOpen(false)} className="text-[13px] font-medium text-muted-foreground">How It Works</a>
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
            For construction contractors who run their own safety
          </p>
          <h1 className="text-3xl font-bold text-foreground lg:text-4xl leading-tight">
            Know exactly where you stand{' '}
            <span className="text-primary">before OSHA walks on site.</span>
          </h1>
          <p className="mt-4 text-[15px] text-muted-foreground leading-relaxed">
            Most contractors find out they have a compliance gap when they get the citation.
            SafetyForge gives you the inspections, documentation, and worker tracking to
            stay ahead of it — without hiring a full-time safety director.
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
              render={<a href="#how-it-works" />}
            >
              See what OSHA would find
            </Button>
          </div>
        </div>

        {/* What you get strip */}
        <div className="mt-8 flex bg-[var(--concrete-50)] border border-[var(--border)]">
          {[
            { label: 'Inspections', detail: 'Digital checklists' },
            { label: 'Documents', detail: 'SSSPs, JHAs, toolbox talks' },
            { label: 'Workers', detail: 'Certs & training tracking' },
            { label: 'OSHA Log', detail: '300, 300A, 301 auto-filled' },
            { label: 'Mock Inspection', detail: 'Find gaps before OSHA does' },
          ].map((item, i) => (
            <div
              key={item.label}
              className={`flex-1 px-3 py-2.5 ${i < 4 ? 'border-r border-[var(--border)]' : ''}`}
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
      reality: "If OSHA had walked on site, that's a $16,131 serious violation. And you're operating uninsured for that scope.",
      color: 'bg-[var(--fail-bg)]',
      iconColor: 'text-[var(--fail)]',
    },
    {
      icon: DollarSign,
      situation: 'Your safety consultant charges $1,500 per SSSP',
      reality: "It's the same template every time with your project name swapped in. You're paying for formatting, not expertise.",
      color: 'bg-[var(--machine-wash)]',
      iconColor: 'text-[var(--machine-dark)]',
    },
    {
      icon: Clock,
      situation: "You need to run toolbox talks but don't have time to prep them",
      reality: "So they don't happen. Or they happen without documentation. Either way, you're exposed.",
      color: 'bg-[var(--info-bg)]',
      iconColor: 'text-[var(--info)]',
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
/*  How It Works                                                        */
/* ------------------------------------------------------------------ */

function HowItWorksSection() {
  const items = [
    {
      label: 'Monday morning',
      title: 'Run your Mock OSHA Inspection',
      description: 'SafetyForge walks your project data and flags exactly what an inspector would find. Missing docs, expired certs, overdue inspections — all surfaced before it becomes a citation.',
      tag: 'PROACTIVE',
      tagColor: 'text-[var(--pass)] bg-[var(--pass-bg)]',
    },
    {
      label: 'Every day',
      title: 'Digital inspections replace the clipboard',
      description: 'Your foreman runs the daily checklist on their phone. Photos, GPS, timestamps. Deficiencies auto-create corrective actions with deadlines. No paper to lose.',
      tag: 'ON SITE',
      tagColor: 'text-[var(--machine-dark)] bg-[var(--machine-wash)]',
    },
    {
      label: 'When you need docs',
      title: 'Generate SSSPs, JHAs, and toolbox talks in minutes',
      description: 'Enter your project details, select hazards from a construction-specific list, and get a professional PDF. Every document references current OSHA 29 CFR 1926 standards.',
      tag: 'COMPLIANT',
      tagColor: 'text-[var(--info)] bg-[var(--info-bg)]',
    },
    {
      label: 'Always running',
      title: 'Worker certs and training tracked automatically',
      description: "NCCCO, OSHA-10, confined space, fall protection — all tracked with expiry alerts. You'll know 30 days before a cert lapses, not 2 weeks after.",
      tag: 'AUTOMATED',
      tagColor: 'text-[var(--warn)] bg-[var(--warn-bg)]',
    },
  ];

  return (
    <section id="how-it-works" className="scroll-mt-16 bg-[var(--concrete-50)] pb-6 lg:pb-8">
      <div className="mx-auto max-w-4xl px-4 lg:px-8">
        <FormSection
          title="How contractors use SafetyForge"
          action={
            <span className="text-[11px] font-semibold text-[var(--machine-dark)]">
              Not just documents
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
/*  Document Types                                                      */
/* ------------------------------------------------------------------ */

function DocumentTypesSection() {
  const docTypes = [
    {
      icon: ShieldCheck,
      name: 'Site-Specific Safety Plan (SSSP)',
      description:
        'Comprehensive safety plan covering hazard identification, emergency procedures, and worker responsibilities.',
      oshaLine: 'Required by OSHA for multi-employer construction sites.',
    },
    {
      icon: AlertTriangle,
      name: 'Job Hazard Analysis (JHA)',
      description:
        'Step-by-step analysis identifying hazards for specific tasks with preventive measures for each.',
      oshaLine: 'Required by OSHA 29 CFR 1926 for hazardous job tasks.',
    },
    {
      icon: MessageSquare,
      name: 'Toolbox Talk Record',
      description:
        'Structured safety briefing with attendance tracking, designed for daily or weekly crew meetings.',
      oshaLine: 'Required by OSHA for ongoing safety training documentation.',
    },
    {
      icon: FileWarning,
      name: 'Incident Report',
      description:
        'Formal documentation including root cause analysis, corrective actions, and witness statements.',
      oshaLine: 'Required by OSHA 29 CFR 1904 for recordable incidents.',
    },
    {
      icon: Siren,
      name: 'Emergency Action Plan',
      description:
        'Site-specific emergency procedures covering evacuation routes, contacts, and response protocols.',
      oshaLine: 'Required by OSHA 29 CFR 1926.35 for all construction sites.',
    },
  ];

  return (
    <section id="documents" className="scroll-mt-16 bg-[var(--concrete-50)] pb-6 lg:pb-8">
      <div className="mx-auto max-w-4xl px-4 lg:px-8">
        <FormSection title="5 Essential Document Types">
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
          {/* Custom doc row */}
          <div className="px-3 py-3 border-t border-[var(--border)] bg-[var(--concrete-50)] lg:px-[18px]">
            <span className="text-[12px] text-muted-foreground">
              Need a custom document type? Enterprise plans include custom templates.
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
      description: 'For small contractors getting started with safety compliance.',
      features: [
        '2 projects',
        'All document generation',
        'Inspections',
        'Toolbox talks',
        'Bilingual support',
        'PDF export',
        'Email support',
      ],
      cta: 'Start Free Trial',
      highlighted: false,
    },
    {
      name: 'Professional',
      price: '$299',
      period: '/month',
      description: 'For active contractors who need advanced safety tools.',
      features: [
        '8 projects',
        'Everything in Starter',
        'Mock OSHA Inspection',
        'Morning Brief',
        'Photo assessment',
        'Certification tracking',
        'Voice input',
        'Priority support',
      ],
      cta: 'Start Free Trial',
      highlighted: true,
    },
    {
      name: 'Business',
      price: '$599',
      period: '/month',
      description: 'For companies managing multiple crews and sites.',
      features: [
        '20 projects',
        'Everything in Professional',
        'Prequalification automation',
        'EMR modeling',
        'Predictive scoring',
        'GC portal',
        'Dedicated account manager',
      ],
      cta: 'Start Free Trial',
      highlighted: false,
    },
    {
      name: 'Enterprise',
      price: 'Custom',
      period: '',
      description: 'For large organizations with unlimited needs.',
      features: [
        'Unlimited projects',
        'Everything in Business',
        'Custom templates',
        'White-label branding',
        'API access',
        'SSO integration',
        'Custom integrations',
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
            Start free. Upgrade when you need more.
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

              {/* Features */}
              <div className="flex-1 px-3 py-3 lg:px-[18px]">
                <ul className="space-y-2">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-start gap-2 text-[12px] text-[var(--concrete-600)]">
                      <Check className="mt-0.5 size-3.5 shrink-0 text-[var(--pass)]" />
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
          <div className="grid grid-cols-1 sm:grid-cols-2 divide-y sm:divide-y-0 sm:divide-x divide-[var(--border)]">
            <div className="px-3 py-3 lg:px-[18px]">
              <div className="flex items-center gap-0.5 mb-2">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Star key={i} className="size-3.5 fill-primary text-primary" />
                ))}
              </div>
              <p className="text-[13px] text-[var(--concrete-600)] leading-relaxed">
                &ldquo;We were paying a consultant $1,200 per safety plan. SafetyForge does it in
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
                an expired NCCCO — SafetyForge flagged it a month before expiry. That would have
                been a $16k fine.&rdquo;
              </p>
              <div className="mt-2">
                <span className="text-[13px] font-semibold text-foreground">Sarah K.</span>
                <span className="text-[12px] text-muted-foreground"> — Safety Manager, 40 employees, Denver CO</span>
              </div>
            </div>
          </div>
        </FormSection>

        {/* What it replaces */}
        <div className="mt-4 flex bg-white border border-[var(--border)]">
          {[
            { label: 'Replaces', value: 'Safety consultants, paper forms, Excel trackers' },
            { label: 'Cost', value: 'From $99/mo vs $500+ per document' },
            { label: 'Standards', value: 'OSHA 29 CFR 1926, ISO 45001, ANSI Z10' },
          ].map((item, i) => (
            <div
              key={item.label}
              className={`flex-1 px-3 py-2.5 lg:px-[18px] ${i < 2 ? 'border-r border-[var(--border)]' : ''}`}
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
      question: 'Are these documents actually OSHA-compliant?',
      answer:
        'Yes. Our templates are developed by certified safety professionals and reviewed against current OSHA 29 CFR 1926 standards. Each document includes all required sections, references the correct regulatory citations, and follows accepted industry formatting. We update templates whenever OSHA revises its standards.',
    },
    {
      question: 'Can I edit the generated documents?',
      answer:
        'Absolutely. Every generated document is fully editable within SafetyForge before you export it. You can add, remove, or modify any section. We also export to Word format on Professional and Enterprise plans so you can make changes in your preferred editor.',
    },
    {
      question: 'What if I need a document type you don\'t offer?',
      answer:
        'We currently support the 5 most commonly required construction safety documents. Enterprise plan customers can request custom templates, and we\'re constantly adding new document types based on customer feedback. Contact us if you need something specific.',
    },
    {
      question: 'How does the free tier work?',
      answer:
        'The free tier gives you 3 documents per month at no cost, forever. No credit card required to sign up. You get access to all 5 document templates and PDF export. Your document count resets on the first of each month.',
    },
    {
      question: 'Do you offer refunds?',
      answer:
        'Yes. If you\'re not satisfied within the first 30 days of a paid plan, we\'ll issue a full refund -- no questions asked. After 30 days, you can cancel anytime and your plan will remain active through the end of the billing period.',
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
        <FormSection title="Your next OSHA inspection could be tomorrow">
          <div className="px-3 py-4 lg:px-[18px]">
            <p className="text-[15px] font-semibold text-foreground">
              Would you pass?
            </p>
            <p className="mt-2 max-w-xl text-[13px] text-muted-foreground leading-relaxed">
              Run a Mock OSHA Inspection on your current projects — free. SafetyForge will
              tell you exactly what an inspector would flag, what it would cost you, and how
              to fix it before they show up.
            </p>
            <div className="mt-4 flex flex-col gap-3 sm:flex-row">
              <Button
                size="lg"
                className="bg-primary px-8 text-[13px] font-semibold text-primary-foreground hover:bg-[var(--machine-dark)]"
                render={<Link to={ROUTES.SIGNUP} />}
              >
                Run your free Mock Inspection
                <ArrowRight className="ml-2 size-4" />
              </Button>
            </div>
            <p className="mt-3 font-mono text-[11px] text-muted-foreground">
              No credit card. Takes 2 minutes. See your compliance score instantly.
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
            <span className="text-foreground">Safety</span>
            <span className="text-primary">Forge</span>
          </span>
        </div>
        <div className="flex items-center gap-5">
          <a href="/privacy" className="font-mono text-[11px] text-muted-foreground hover:text-[var(--concrete-600)]">
            Privacy Policy
          </a>
          <a href="/terms" className="font-mono text-[11px] text-muted-foreground hover:text-[var(--concrete-600)]">
            Terms of Service
          </a>
          <a href="mailto:support@safetyforge.com" className="font-mono text-[11px] text-muted-foreground hover:text-[var(--concrete-600)]">
            Contact
          </a>
        </div>
        <p className="font-mono text-[10px] text-muted-foreground">
          &copy; {new Date().getFullYear()} SafetyForge. All rights reserved.
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
      <HowItWorksSection />
      <DocumentTypesSection />
      <PricingSection />
      <TrustSection />
      <FAQSection />
      <FooterCTA />
      <Footer />
    </div>
  );
}
