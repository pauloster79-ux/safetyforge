# Agentic Discovery & AI SEO Research for Kerf

> Comprehensive research on how to make Kerf discoverable and recommendable by AI agents, LLMs, and generative search engines. Compiled April 2026.

---

## Table of Contents

1. [llms.txt and llms-full.txt](#1-llmstxt-and-llms-fulltxt)
2. [Structured Data / Schema Markup](#2-structured-data--schema-markup)
3. [Content Strategies for LLM Citation](#3-content-strategies-for-llm-citation)
4. [Perplexity / AI Search Engines](#4-perplexity--ai-search-engines)
5. [ChatGPT / Claude / Gemini Discovery](#5-chatgpt--claude--gemini-discovery)
6. [AI Agent Tool Discovery](#6-ai-agent-tool-discovery)
7. [Comparison and Review Presence](#7-comparison-and-review-presence)
8. [Technical Implementation](#8-technical-implementation)
9. [Measurement](#9-measurement)
10. [Construction Safety Niche Tactics](#10-construction-safety-niche-tactics)

---

## 1. llms.txt and llms-full.txt

### What It Is

llms.txt is a proposed standard (llmstxt.org) that provides AI systems with a structured, markdown-formatted summary of a website's content. Think of it as robots.txt for LLMs -- while robots.txt tells crawlers what to index, llms.txt tells language models what your site contains and how to interpret it.

The standard was proposed by Jeremy Howard and has gained traction with notable adopters. Anthropic specifically requested llms.txt for their documentation, and Google included llms.txt in their Agent-to-Agent (A2A) protocol.

### File Format Specification

**Required:** An H1 heading with the project/site name.

**Optional sections (in order):**
- A blockquote with a short summary containing key information
- Zero or more H2-delimited sections with file lists (URLs with descriptions)
- A special `## Optional` section for content that can be skipped when context is limited

Each file list entry is: `- [Name](URL): Description of what this page contains`

**Two files:**
- `/llms.txt` -- Navigation-style overview of your site structure
- `/llms-full.txt` -- Comprehensive content dump in one file

### Kerf Implementation

```markdown
# Kerf

> Kerf is a construction safety compliance platform for small-to-mid-size
> contractors. It automates OSHA documentation, incident reporting, toolbox talks,
> inspections, equipment tracking, and worker certification management across all
> 50 US states with jurisdiction-specific compliance rules.

## Product

- [Features Overview](https://kerf.build/features): Complete feature list
  including AI-powered compliance monitoring, incident reporting, toolbox talk
  generation, inspection management, and OSHA 300 log automation
- [Pricing](https://kerf.build/pricing): Plans for contractors from 5 to
  500+ workers, starting at $X/month
- [Use Cases](https://kerf.build/use-cases): How general contractors,
  subcontractors, and safety managers use Kerf

## Compliance Coverage

- [OSHA Compliance](https://kerf.build/compliance/osha): How Kerf
  handles OSHA 29 CFR 1926 construction standards
- [State Compliance](https://kerf.build/compliance/states): Coverage across
  all 50 states including OSHA State Plan states (CA-OSHA, WA L&I, etc.)
- [Multi-Jurisdiction](https://kerf.build/compliance/multi-jurisdiction):
  How contractors working across state lines stay compliant

## Documentation

- [Getting Started](https://kerf.build/docs/getting-started): Quick setup
  guide for new contractors
- [API Reference](https://kerf.build/docs/api): REST API for integrations
  with project management and ERP systems
- [Integrations](https://kerf.build/integrations): Connections with Procore,
  PlanGrid, and other construction platforms

## Resources

- [Safety Compliance Guide](https://kerf.build/guides/osha-compliance):
  Complete guide to OSHA compliance for small contractors
- [Toolbox Talk Library](https://kerf.build/resources/toolbox-talks):
  Pre-built safety meeting topics for construction crews
- [Blog](https://kerf.build/blog): Construction safety news, regulatory
  updates, and best practices

## Optional

- [Changelog](https://kerf.build/changelog): Product updates and new features
- [About](https://kerf.build/about): Company mission and team
```

### Key Implementation Notes

- Place at the root: `kerf.build/llms.txt`
- Also create `kerf.build/llms-full.txt` with full page content
- Use plain, factual language -- no marketing fluff
- Update quarterly or when product changes significantly
- As of July 2025, only ~951 domains had published llms.txt -- early mover advantage is real
- Implementation takes 1-4 hours with no demonstrated downside

---

## 2. Structured Data / Schema Markup

### Why It Matters for AI Discovery

Google confirmed in April 2025 that structured data provides an advantage in search results. Microsoft's Fabrice Canel confirmed in March 2025 that schema markup helps Bing's LLMs understand content. One company added SoftwareApplication schema and saw AI traffic increase 100% from a zero baseline within 90 days.

### Priority Schema Types for Kerf

#### SoftwareApplication (Highest Priority)

```json
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "Kerf",
  "applicationCategory": "BusinessApplication",
  "applicationSubCategory": "Construction Safety Compliance Software",
  "operatingSystem": "Web Browser",
  "offers": {
    "@type": "Offer",
    "price": "XX.XX",
    "priceCurrency": "USD",
    "priceValidUntil": "2026-12-31"
  },
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.X",
    "reviewCount": "XX"
  },
  "featureList": [
    "OSHA compliance automation",
    "Incident reporting and tracking",
    "Digital toolbox talks",
    "Inspection management",
    "Worker certification tracking",
    "Equipment management",
    "Multi-state compliance",
    "OSHA 300 log generation"
  ],
  "screenshot": "https://kerf.build/images/dashboard-screenshot.png",
  "softwareHelp": {
    "@type": "CreativeWork",
    "url": "https://kerf.build/docs"
  }
}
```

#### Organization

```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "Kerf",
  "description": "Construction safety compliance platform for small-to-mid-size contractors",
  "url": "https://kerf.build",
  "foundingDate": "2024",
  "sameAs": [
    "https://www.g2.com/products/kerf",
    "https://www.capterra.com/p/XXXXX/Kerf/",
    "https://www.linkedin.com/company/kerf",
    "https://twitter.com/kerf"
  ]
}
```

#### FAQPage (High Citation Value)

LLMs cite FAQs heavily. Implement FAQ schema on every page that has Q&A content.

```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "What OSHA records does Kerf automate?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Kerf automates OSHA 300 logs, 300A summaries, and 301 incident reports. It tracks recordability criteria per 29 CFR 1904 and handles multi-state reporting requirements for contractors working across jurisdictions."
      }
    },
    {
      "@type": "Question",
      "name": "Does Kerf work for small contractors with under 20 workers?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Yes. Kerf is designed specifically for small-to-mid-size contractors starting at 5 workers. The platform scales from single-site subcontractors to multi-project general contractors with 500+ workers."
      }
    }
  ]
}
```

#### HowTo (For Guide Content)

Use on setup guides, compliance walkthroughs, and instructional content.

#### Product (For Pricing Pages)

Pair with SoftwareApplication for pricing tier pages.

### Implementation Priority

1. SoftwareApplication on the homepage and product page
2. Organization on the homepage
3. FAQPage on every page with questions (pricing FAQ, feature FAQ, compliance FAQ)
4. HowTo on guide and tutorial pages
5. Article + Author on blog posts (author credibility matters for AI citation)
6. BreadcrumbList on all pages (helps AI understand site structure)

---

## 3. Content Strategies for LLM Citation

### What Gets Cited: The Data

Research from 2025 reveals specific content characteristics that drive LLM citations:

- Adding statistics increases AI visibility by **22%**
- Using quotations boosts visibility by **37%**
- Models extract **44% of citations from the first 30% of a page**
- Comparative listicles, how-to guides, and FAQs are the most cited formats
- **40-60 word modular paragraphs** improve extraction likelihood
- Pages not updated quarterly are **3x more likely to lose citations**
- Average domain age of ChatGPT-cited sources is **17 years** (authority matters)

### The Answer-First Format

AI retrieval systems extract the first 1-2 sentences of a section to determine if it answers a query. Every page and section should open with a clear, direct answer.

**Pattern:** `[Entity] is a [category] that [differentiator].`

**Bad opening:**
> "In today's fast-paced construction industry, safety has never been more important. That's why we built Kerf..."

**Good opening:**
> "Kerf is a construction safety compliance platform that automates OSHA documentation, incident reporting, and worker certification tracking for contractors with 5 to 500+ workers across all 50 US states."

### Content Types That Drive Citations

#### 1. Definitive Guide Pages (Highest Citation Value)
- "Complete Guide to OSHA Compliance for Small Contractors"
- "Construction Safety Software Comparison: Features, Pricing, and Compliance Coverage"
- "State-by-State Construction Safety Requirements"
- Format: Answer-first, statistics-rich, updated quarterly

#### 2. FAQ Pages (High Citation Value)
- Dedicated FAQ page with 30-50 questions contractors actually ask
- FAQ sections on every product/feature page
- Use schema markup on all FAQ content

#### 3. Comparison Pages
- "Kerf vs. Procore Safety" (feature-by-feature)
- "Best Construction Safety Software for Small Contractors [2026]"
- Include pricing, feature matrices, and honest assessments

#### 4. Data-Rich Content
- "Construction Safety Statistics 2026"
- "OSHA Citation Trends by State"
- "Average Cost of OSHA Non-Compliance for Small Contractors"
- Original data and statistics get cited more than any other content type

#### 5. Glossary / Knowledge Base
- Define every construction safety term
- Each definition is a potential citation target
- Use `DefinedTerm` schema markup

### Writing Rules for LLM Citation

1. **First 200 words must directly answer the primary query** the page targets
2. **Front-load the answer in under 30 words**, then expand with context
3. **Use named, credentialed authors** -- anonymous bylines are a GEO penalty
4. **Include statistics with sources** in every major piece of content
5. **Write in 40-60 word modular paragraphs** that are easy to extract
6. **Use clear H2/H3 headers phrased as questions** people actually ask
7. **Update content quarterly** -- freshness is a direct citation signal
8. **Include expert quotes** -- quotations boost visibility by 37%

---

## 4. Perplexity / AI Search Engines

### Current State (2026)

Perplexity surpassed 15 million daily active users in early 2026. The platform abandoned all advertising in February 2026 over trust concerns -- meaning there is no paid placement option. All visibility must be earned organically.

### How Perplexity Discovers Sources

Perplexity uses real-time web retrieval (not just training data) to answer queries. It crawls and indexes the web with PerplexityBot. When a user asks a question, it retrieves relevant pages, synthesizes an answer, and provides source citations.

### How to Appear in Perplexity Answers

1. **Allow PerplexityBot in robots.txt** (it uses `PerplexityBot` user-agent)
2. **Allow Perplexity-User** for live retrieval (note: Perplexity-User does not always respect robots.txt)
3. **Create definitive, authoritative content** on your target topics
4. **Use structured data** so Perplexity can quickly parse your pages
5. **Build citations from authoritative third-party sources** (G2, Capterra, industry publications)
6. **Ensure fast page loads** -- retrieval systems have timeout limits
7. **Maintain content freshness** -- Perplexity favors recent, updated content

### Key Insight: Cross-Platform Divergence

Only 11% of domains are cited by both ChatGPT and Perplexity, meaning you must optimize for each platform separately. 35-40% of queries produce completely disjoint source sets across different AI systems.

---

## 5. ChatGPT / Claude / Gemini Discovery

### How New Products Enter LLM Knowledge

There are two pathways into an LLM's recommendations:

#### Path 1: Training Data (Slow, Persistent)
- Content published before the model's knowledge cutoff gets baked into the model
- Current cutoff dates (as of early 2026):
  - ChatGPT-5.4: August 31, 2025
  - Claude 4.6 Sonnet: ~August 2025 (training data through January 2026)
  - Gemini 3.1 Flash: January 2025
- Content must exist on crawlable, authoritative sources to be included
- This is why G2, Capterra, Wikipedia, and Reddit matter -- they are in every model's training data

#### Path 2: Real-Time Retrieval (Fast, Ephemeral)
- All major LLMs now have web search capabilities
- When a user asks about a topic, the model can search the web in real time
- Your site must be crawlable, fast, and well-structured for retrieval
- This is where llms.txt, schema markup, and content structure pay off immediately

### Platform-Specific Strategies

#### ChatGPT
- Processes 100M+ search-like queries per day
- Allow `OAI-SearchBot` and `ChatGPT-User` in robots.txt
- Can block `GPTBot` (training) while allowing search
- Heavily weights G2, Capterra, and Reddit in software recommendations

#### Claude
- Allow `Claude-SearchBot` and `Claude-User` in robots.txt
- Can block `ClaudeBot` (training) while allowing search
- Values structured, factual content with clear definitions
- llms.txt was specifically requested by Anthropic

#### Gemini
- Google signed a $60M/year deal with Reddit for training data
- Allow `Google-Extended` for AI features (or block to prevent training)
- AI Overviews appear in 47%+ of Google searches
- Google AI Mode has reached 75M daily active users

### The Critical Insight

94% of B2B buyers now use generative AI in their purchasing process, with AI becoming the most cited information source -- ranking above vendor websites and sales reps. If Kerf does not appear when a contractor asks "what safety software should I use?", it effectively does not exist for that buyer.

---

## 6. AI Agent Tool Discovery

### The Emerging Landscape

As AI agents become more autonomous (researching, comparing, and recommending tools on behalf of users), website structure for agent crawlability becomes critical.

### MCP (Model Context Protocol) Server

MCP has exploded from 100K downloads in November 2024 to 97M+ monthly SDK downloads in 2026. It was donated to the Linux Foundation's Agentic AI Foundation in December 2025.

**For Kerf, consider building an MCP server that:**
- Exposes safety data and compliance information through a standardized interface
- Allows AI agents to query Kerf capabilities programmatically
- Provides tool descriptions that agents can discover and use
- Supports dynamic discovery (agents can ask "what can you do?")

### API Documentation for Agents

Structure API docs so AI agents can understand and use them:
- OpenAPI/Swagger specification at a well-known URL
- Clear, descriptive endpoint names and descriptions
- Example requests and responses for every endpoint
- Machine-readable capability descriptions

### Website Structure for Agent Crawlability

1. **Clean HTML semantics** -- agents parse HTML structure, not visual layout
2. **Consistent URL patterns** -- predictable routing helps agents navigate
3. **Machine-readable product descriptions** -- JSON-LD, llms.txt, API specs
4. **Clear capability statements** -- "Kerf does X, Y, Z" not "Transform your safety culture"
5. **Comparison data** -- structured feature/pricing comparisons agents can extract

### Future-Proofing

Google's A2A (Agent-to-Agent) protocol, Anthropic's MCP, and emerging standards like ACP (Agent Communication Protocol) are converging toward a world where AI agents discover and interact with SaaS tools programmatically. Having machine-readable product information, API documentation, and potentially an MCP server positions Kerf for this future.

---

## 7. Comparison and Review Presence

### Platform Priority (By LLM Citation Weight)

Research shows that 100% of tools mentioned in ChatGPT answers had a Capterra presence and 99% had a G2 presence. Domains with review platform profiles have 3x higher chances of being cited.

#### Tier 1: Must-Have (Direct Citation Sources)

| Platform | Why | Citation Impact |
|----------|-----|-----------------|
| **G2** | Top 20 most-cited domain across all LLMs; 22-23% share of voice for software categories; 100K+ citations and growing | Companies with 50+ G2 reviews cross a citation threshold that makes them disproportionately influential |
| **Capterra** | 100% of ChatGPT software recommendations had Capterra presence; ~20% share of voice | Essential for basic inclusion in AI recommendations |
| **Reddit** | Most-cited domain in LLM responses at 40.1%; organic community discussions are viewed as impartial | Real user discussions and recommendations drive AI trust signals |

#### Tier 2: High Value

| Platform | Why |
|----------|-----|
| **Wikipedia** | 26.3% of LLM citations; extremely high authority signal. Requires notability criteria -- may need PR/media coverage first |
| **Gartner Peer Insights** | Top 5 most-cited source for software; carries enterprise credibility |
| **TrustRadius** | B2B-focused; cited by AI models for detailed technical reviews |
| **Quora** | Feeds into LLM training data; answers to construction safety questions are citation targets |

#### Tier 3: Supporting Presence

| Platform | Why |
|----------|-----|
| **Product Hunt** | Helps with initial visibility; tech-savvy audience; gets indexed |
| **Hacker News** | High authority domain; technical credibility. Hard to game -- must offer genuine value |
| **Stack Overflow / Stack Exchange** | Technical Q&A gets cited; relevant for API/integration questions |
| **Industry-Specific** | Construction industry publications, safety associations (OSHA.gov, NSC, AGC) |

### Reddit Strategy

Reddit is the #1 cited domain by LLMs. Strategy for Kerf:

1. **Participate authentically** in r/construction, r/OSHA, r/ConstructionManagement, r/SafetyProfessionals
2. **Answer real questions** about safety compliance, not self-promotion
3. **Write posts that anticipate follow-up questions** -- this is the citation trigger for AI models
4. **Use short paragraphs, headings, and bullets** -- help both humans and AI parse content
5. **Personal accounts, not brand accounts** -- Reddit users prefer real conversations with individuals
6. **Share genuinely useful insights** about construction safety compliance that demonstrate expertise

### G2 Strategy

Being in the top 3 on G2 for your category is described as the single most reliable AI visibility signal for SaaS companies.

1. Create a complete G2 profile with all features, screenshots, and pricing
2. Actively collect reviews -- target 50+ reviews (the citation threshold)
3. Encourage detailed reviews that mention specific features (OSHA compliance, multi-state, small contractors)
4. Respond to every review
5. Keep the profile updated with new features

---

## 8. Technical Implementation

### robots.txt Configuration

The recommended approach: block training crawlers but allow search/retrieval crawlers.

```
# Kerf robots.txt
# Strategy: Allow AI search crawlers, block training-only crawlers

# === AI Search Crawlers (ALLOW) ===
# These crawlers help your site appear in AI-generated answers

User-agent: OAI-SearchBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: Claude-SearchBot
Allow: /

User-agent: Claude-User
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Perplexity-User
Allow: /

User-agent: Bingbot
Allow: /

# === Training Crawlers (BLOCK for content protection) ===
# These crawlers collect content for model training
# Block if you want to protect content; allow if you want to be in training data

# OPTION A: Block training (protects content, still appears in search)
User-agent: GPTBot
Disallow: /

User-agent: ClaudeBot
Disallow: /

User-agent: Google-Extended
Disallow: /

User-agent: CCBot
Disallow: /

# OPTION B: Allow training (maximizes long-term AI visibility)
# Comment out the blocks above and use:
# User-agent: GPTBot
# Allow: /
# User-agent: ClaudeBot
# Allow: /

# === Standard Search Engines ===
User-agent: Googlebot
Allow: /

User-agent: *
Allow: /

Sitemap: https://kerf.build/sitemap.xml
```

**Recommendation for Kerf:** Use OPTION B (allow training). As a newer product trying to build AI visibility, being included in training data is more valuable than protecting content. 69% of sites block ClaudeBot and 62% block GPTBot -- allowing them is a competitive advantage.

### Sitemap Structure

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <!-- Priority pages for AI discovery -->
  <url>
    <loc>https://kerf.build/</loc>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://kerf.build/features</loc>
    <changefreq>monthly</changefreq>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>https://kerf.build/pricing</loc>
    <changefreq>monthly</changefreq>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>https://kerf.build/compliance/osha</loc>
    <changefreq>monthly</changefreq>
    <priority>0.9</priority>
  </url>
  <!-- Comparison and guide pages -->
  <url>
    <loc>https://kerf.build/compare/construction-safety-software</loc>
    <changefreq>quarterly</changefreq>
    <priority>0.8</priority>
  </url>
  <!-- FAQ pages -->
  <url>
    <loc>https://kerf.build/faq</loc>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
</urlset>
```

### Meta Tags for AI Discovery

```html
<head>
  <!-- Standard meta -->
  <title>Kerf - Construction Safety Compliance Software for Contractors</title>
  <meta name="description" content="Kerf automates OSHA compliance,
    incident reporting, toolbox talks, inspections, and worker certifications
    for construction contractors with 5-500+ workers across all 50 US states." />

  <!-- Open Graph (used by AI systems for page understanding) -->
  <meta property="og:title" content="Kerf - Construction Safety Compliance Software" />
  <meta property="og:description" content="Automated OSHA compliance, incident
    reporting, and safety management for small-to-mid-size contractors." />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="https://kerf.build" />
  <meta property="og:image" content="https://kerf.build/images/og-image.png" />

  <!-- Additional signals -->
  <meta name="robots" content="index, follow" />
  <link rel="canonical" href="https://kerf.build" />

  <!-- JSON-LD structured data (see Section 2) -->
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    "name": "Kerf",
    ...
  }
  </script>
</head>
```

### Content Freshness Signals

- Add `datePublished` and `dateModified` to Article schema
- Show "Last updated: [date]" visibly on guide pages
- Update key pages quarterly at minimum
- Maintain a blog with regular posts (at least monthly)
- Include structured data timestamps

### Page Speed

AI retrieval systems have timeout limits. Ensure:
- Core Web Vitals passing
- Server response under 200ms
- Total page load under 2 seconds
- Clean HTML that parses easily (minimal JavaScript rendering)
- Server-side rendering (SSR) preferred over client-side rendering for crawlability

---

## 9. Measurement

### Dedicated LLM Monitoring Tools

A new category of tools has emerged specifically for tracking AI visibility:

| Tool | What It Does | Pricing Tier |
|------|-------------|-------------|
| **Peec AI** | Monitors brand visibility and sentiment across AI search engines. Backed by EUR21M Series A (2025) | Enterprise |
| **Profound** | Connects AI visibility to behavioral analytics and conversion tracking -- shows what happens after a mention | Mid-market |
| **Otterly.ai** | AI Visibility Tracker used by 20K+ professionals. Tracks ChatGPT, Perplexity, Google AI Overviews | SMB-friendly |
| **Semrush AI Visibility Toolkit** | Bundled with full SEO toolkit; keyword data + AI visibility in one platform | Part of Semrush subscription |

### Key Metrics to Track

1. **Mention Rate** -- percentage of AI-generated answers that mention "Kerf" for target queries
2. **Citation Rate** -- percentage that include a clickable URL to kerf.build
3. **Position** -- where Kerf appears in the answer (first mentioned, middle, end)
4. **Sentiment** -- whether the AI recommendation is positive, neutral, or negative
5. **Competitor Share of Voice** -- how often competitors are mentioned vs. Kerf

### DIY Monitoring Approach

Before investing in paid tools:

1. **Manual prompt testing** -- Ask target questions weekly across ChatGPT, Claude, Perplexity, and Gemini:
   - "What is the best safety compliance software for small contractors?"
   - "How do small construction companies handle OSHA compliance?"
   - "What software automates OSHA 300 logs?"
   - "Compare construction safety management platforms"
   - Record whether Kerf appears, in what position, and what is said

2. **Server log analysis** -- Monitor for AI crawler user-agents:
   - `OAI-SearchBot`, `ChatGPT-User` (OpenAI)
   - `Claude-SearchBot`, `Claude-User` (Anthropic)
   - `PerplexityBot`, `Perplexity-User` (Perplexity)
   - Track which pages they access most frequently

3. **Referral traffic analysis** -- Track visits from:
   - `chat.openai.com`
   - `perplexity.ai`
   - Google AI Overview clicks (identifiable in GA4)

4. **Review platform monitoring** -- Track G2 and Capterra review counts, ratings, and ranking

### Critical Statistic

Google AI Mode has reached 75 million daily active users, and approximately 93% of those sessions end without a single click to any website. If your brand is not mentioned in the AI response itself, you may not exist for that user.

---

## 10. Construction Safety Niche Tactics

### Target Queries

These are the questions contractors and safety managers ask AI systems. Kerf must appear in answers to these:

#### Software Selection Queries
- "What is the best construction safety software for small contractors?"
- "Best OSHA compliance software for construction 2026"
- "Construction safety management app for subcontractors"
- "Safety software that handles multi-state compliance"
- "Cheapest safety management software for small construction companies"
- "Construction safety software comparison"
- "Alternative to [competitor name] for construction safety"

#### Problem-Solution Queries
- "How to automate OSHA 300 logs for construction"
- "How to manage worker certifications on a construction site"
- "How to run digital toolbox talks"
- "How to track safety inspections for multiple job sites"
- "How to prepare for an OSHA inspection as a small contractor"
- "How to report construction site incidents"
- "What safety documentation do small contractors need?"

#### Compliance Queries
- "OSHA requirements for contractors with fewer than 20 employees"
- "What OSHA forms do construction companies need to keep?"
- "State-specific construction safety requirements"
- "OSHA 1926 compliance checklist for small contractors"
- "Construction safety training requirements by state"

#### Cost/ROI Queries
- "How much does construction safety software cost?"
- "ROI of safety management software for contractors"
- "Cost of OSHA non-compliance for small construction companies"
- "Is safety software worth it for a 10-person crew?"

### Content Strategy for the Niche

#### Create Definitive Resources

1. **"Complete Guide to OSHA Compliance for Small Contractors"** -- 5,000+ word guide covering every requirement. This becomes the page AI cites. Update quarterly.

2. **"State-by-State Construction Safety Requirements"** -- Individual pages for each state (or at minimum, OSHA State Plan states). Kerf's multi-jurisdiction architecture is a differentiator -- turn it into content.

3. **"Construction Safety Software Buyer's Guide 2026"** -- Honest comparison including Kerf and competitors. AI models cite comparison content heavily.

4. **"OSHA Inspection Preparation Checklist"** -- Practical, downloadable resource. Include statistics on citation rates and fines.

5. **"Construction Safety Statistics 2026"** -- Original data compilation. Statistics increase AI visibility by 22%.

#### Leverage Kerf Differentiators

Kerf has specific features that matter for AI recommendations:
- **Multi-state compliance** -- Few competitors handle jurisdiction-specific rules across 50 states
- **Small contractor focus** -- Most platforms target enterprise; small contractors are underserved
- **AI-powered compliance monitoring** -- Proactive alerts vs. passive record-keeping
- **Toolbox talk generation** -- AI-generated safety meeting content
- **Affordable pricing** -- Price point matters for small contractors

Every piece of content should reinforce these differentiators because they answer the follow-up questions AI models anticipate.

#### Industry Authority Building

1. **Publish original research** -- Survey contractors about safety practices, publish results
2. **Comment on OSHA regulatory changes** -- Be a go-to source for analysis of new rules
3. **Create state-specific compliance guides** -- Become THE authority on construction safety compliance in specific states
4. **Contribute to industry publications** -- Guest posts in ENR, Construction Dive, Safety+Health Magazine
5. **Partner with industry associations** -- AGC, ABC, NAHB, ASA references carry weight with AI models

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1-2)

- [ ] Create and deploy `/llms.txt` and `/llms-full.txt`
- [ ] Implement SoftwareApplication, Organization, and FAQPage JSON-LD schema
- [ ] Configure robots.txt to allow AI search crawlers (and consider allowing training crawlers)
- [ ] Ensure sitemap.xml is complete and submitted
- [ ] Add Open Graph meta tags to all pages

### Phase 2: Content (Week 3-6)

- [ ] Rewrite homepage and product pages in answer-first format
- [ ] Create dedicated FAQ page with 30+ questions and FAQPage schema
- [ ] Write "Complete Guide to OSHA Compliance for Small Contractors" (definitive guide)
- [ ] Write "Construction Safety Software Comparison 2026" (comparison page)
- [ ] Create state-by-state compliance pages (start with top 10 states by contractor volume)
- [ ] Add author bios with credentials to all content

### Phase 3: Review Platforms (Week 4-8)

- [ ] Create complete G2 profile with screenshots, features, and pricing
- [ ] Create Capterra profile
- [ ] Create TrustRadius profile
- [ ] Begin systematic review collection (target: 50+ G2 reviews)
- [ ] Create Gartner Peer Insights profile
- [ ] Consider Product Hunt launch

### Phase 4: Community Presence (Week 6-12)

- [ ] Begin authentic participation in r/construction, r/OSHA, r/ConstructionManagement
- [ ] Answer construction safety questions on Quora
- [ ] Contribute to relevant Stack Exchange discussions
- [ ] Seek industry publication guest posts (Construction Dive, Safety+Health)
- [ ] Build PR presence for potential Wikipedia notability

### Phase 5: Measurement & Iteration (Ongoing)

- [ ] Set up manual prompt testing protocol (weekly across ChatGPT, Claude, Perplexity, Gemini)
- [ ] Monitor AI crawler access in server logs
- [ ] Evaluate Otterly.ai or similar LLM monitoring tool
- [ ] Track referral traffic from AI platforms
- [ ] Quarterly content refresh cycle
- [ ] Monthly new content targeting identified query gaps

### Phase 6: Agent Readiness (Month 3-6)

- [ ] Publish OpenAPI specification for Kerf API
- [ ] Evaluate building an MCP server for Kerf
- [ ] Create machine-readable capability descriptions
- [ ] Ensure API documentation is AI-agent-friendly

---

## Key Takeaways

1. **llms.txt is low-hanging fruit** -- implement it today. Under 1,000 sites have done it. Early mover advantage is significant.

2. **G2 and Capterra are non-negotiable** -- 100% of ChatGPT software recommendations have Capterra presence. Target 50+ reviews on G2.

3. **Content must be answer-first** -- AI models extract from the first 30% of a page. Lead with the answer, not the preamble.

4. **Allow AI crawlers** -- Most sites block them. Allowing them is a competitive advantage for discovery.

5. **Reddit is the #1 cited source** -- Authentic participation in construction safety subreddits has outsized impact.

6. **Structured data is confirmed to help** -- Google and Microsoft have both confirmed schema markup aids AI understanding.

7. **Freshness matters** -- Content not updated quarterly loses citation probability by 3x. Build a quarterly refresh cycle.

8. **Multi-platform presence is essential** -- Only 11% of domains are cited by both ChatGPT and Perplexity. Optimize for each.

9. **Measurement is now possible** -- Tools like Otterly.ai, Peec AI, and Profound allow tracking AI mentions.

10. **The construction safety niche is winnable** -- Most competitors are not optimizing for AI discovery. Moving first on llms.txt, schema, and answer-first content creates a durable advantage.

---

## Sources

- [llmstxt.org - The /llms.txt file specification](https://llmstxt.org/)
- [Semrush - What Is LLMs.txt & Should You Use It?](https://www.semrush.com/blog/llms-txt/)
- [Rankability - LLMS.txt Best Practices & Implementation Guide](https://www.rankability.com/guides/llms-txt-best-practices/)
- [GenieOptimize - llms.txt for SaaS: A Complete Playbook](https://genieoptimize.com/blog/llms-txt-playbook/)
- [First Page Sage - Generative Engine Optimization Best Practices in 2026](https://firstpagesage.com/seo-blog/generative-engine-optimization-best-practices/)
- [Search Engine Land - Generative engine optimization (GEO): How to win AI mentions](https://searchengineland.com/what-is-generative-engine-optimization-geo-444418)
- [Search Engine Land - Mastering generative engine optimization in 2026](https://searchengineland.com/mastering-generative-engine-optimization-in-2026-full-guide-469142)
- [Quoleady - Do G2 and Capterra Reviews Influence ChatGPT Rankings?](https://www.quoleady.com/llmo-research/)
- [G2 - Does G2 Get Ranked in AI LLM Search?](https://learn.g2.com/tech-signals-does-g2-get-ranked-in-ai-llm-search)
- [SE Ranking - Despite 90% Traffic Loss, Review Platforms Top AI Overview Citations](https://seranking.com/blog/review-platforms-in-ai-overviews/)
- [Quoleady - Schema & Structured Data for LLM Visibility](https://www.quoleady.com/schema-structured-data-for-llm-visibility/)
- [Search Engine Land - How schema markup fits into AI search](https://searchengineland.com/schema-markup-ai-search-no-hype-472339)
- [The Digital Bloom - 2025 AI Visibility Report: How LLMs Choose What Sources to Mention](https://thedigitalbloom.com/learn/2025-ai-citation-llm-visibility-report/)
- [ALM Corp - Perplexity AI Abandons Advertising](https://almcorp.com/blog/perplexity-ai-abandons-advertising-2026-analysis/)
- [ALM Corp - ClaudeBot, Claude-User & Claude-SearchBot robots.txt Strategy](https://almcorp.com/blog/anthropic-claude-bots-robots-txt-strategy/)
- [TheGeoCommunity - robots.txt for AI Bots: What to Allow, What to Block](https://thegeocommunity.com/blogs/generative-engine-optimization/robots-txt-ai-bots/)
- [Backlinko - 5 AI Visibility Tools to Track Your Brand Across LLMs](https://backlinko.com/llm-tracking-tools/)
- [Semrush - The 9 Best LLM Monitoring Tools for Brand Visibility in 2026](https://www.semrush.com/blog/llm-monitoring-tools/)
- [Otterly.ai - AI Search Monitoring Tool](https://otterly.ai)
- [Conductor - What is Answer Engine Optimization?](https://www.conductor.com/academy/answer-engine-optimization/)
- [Brainz Digital - Why Reddit Matters For LLM Visibility In 2026](https://www.brainz.digital/blog/reddit-seo-llm-aeo/)
- [Perrill - Why Reddit is Frequently Cited by Large Language Models](https://www.perrill.com/why-is-reddit-cited-in-llms/)
- [Otterly.ai - LLM Knowledge Cutoff Dates (2026)](https://otterly.ai/blog/knowledge-cutoff/)
- [Frase.io - What is Generative Engine Optimization (GEO)?](https://www.frase.io/blog/what-is-generative-engine-optimization-geo)
- [Medium - AI Visibility for SaaS Companies](https://medium.com/@seoforgpt/ai-visibility-for-saas-companies-how-to-get-recommended-by-chatgpt-claude-perplexity-d4e19e572bf2)
- [Discovered Labs - How to get cited by ChatGPT, Claude & Perplexity](https://discoveredlabs.com/blog/how-to-get-cited-by-chatgpt-claude-perplexity-managed-aeo-vs-diy-for-b2b-saas-companies)
