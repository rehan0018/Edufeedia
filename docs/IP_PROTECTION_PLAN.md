# Edufeedia Intellectual Property Protection & Governance Plan (India)

**Document Version:** 1.0.0  
**Jurisdiction:** India (Governed by Copyright Act 1957, Trade Marks Act 1999, Patents Act 1970, Indian Contract Act 1872, and DPDP Act 2023)  
**Classification:** STRICTLY CONFIDENTIAL & PROPRIETARY  
**Target Platform:** Edufeedia (K-12 Safe Educational Platform & Socratic Tutoring)

---

## 1. Executive Summary & Legal Framework

Edufeedia is a controlled educational software platform designed for students under 18, featuring curriculum alignment, short-form educational content curation, active-recall quiz generation, and Socratic AI tutoring.

This document establishes a practical, legally grounded intellectual property (IP) and confidentiality governance system tailored to the Indian legal landscape.

### Governing Statutes & Standards
* **The Copyright Act, 1957 (as amended in 2012)**: Governs source code, UI designs, educational scripts, database structures, graphics, and video content.
* **The Trade Marks Act, 1999 & Trade Marks Rules, 2017**: Governs the brand name "Edufeedia", logos, slogans, and trade dress.
* **The Patents Act, 1970 (as amended)** & **CRI Guidelines (Computer Related Inventions)**: Governs statutory patentability exclusions under Section 3(k).
* **The Indian Contract Act, 1872**: Governs Non-Disclosure Agreements (NDAs), trade secret protection under common law equity, and Section 27 non-disclosure enforcement.
* **The Digital Personal Data Protection Act, 2023 (DPDP Act)**: Governs Section 9 statutory mandates on children's data and verifiable parental consent (distinguished from IP).
* **Bharatiya Sakshya Adhiniyam, 2023 (BSA §63) / Indian Evidence Act §65B**: Governs the admissibility of electronic records (Git commit logs, timestamps, hash proofs).

---

## 2. IP Asset Categorization & Protection Analysis

### A. Copyrightable Material (Copyright Act, 1957)
Under Section 2(o) of the Indian Copyright Act, software programs (both source code and object code) are protected as **literary works**.

| Asset Type | Specific Edufeedia Components | Indian Copyright Scope | What It DOES NOT Protect |
| :--- | :--- | :--- | :--- |
| **Source Code** | FastAPI backend, React frontend components, database migration scripts, orchestration logic | Protects literal code, structure, sequence, and organization against direct copying or unauthorized adaptation. | Does **NOT** protect the underlying logic, programming language, functional idea, algorithms, or mathematical formulas (*Idea-Expression Dichotomy*). |
| **UI/UX Designs** | Figma layouts, design tokens, color palettes, custom component hierarchies | Protects original visual presentation, graphic layouts, and UI iconography as artistic works. | Does **NOT** protect functional workflows (e.g., standard login flow, quiz card layout pattern, standard tabbed navigation). |
| **Graphics & Mascots** | Custom character mascots (e.g., Leo the Lion, Ollie the Owl, Cosmo Astronaut), vector badges, visual rewards | Protects original artistic character designs and graphic artwork. | Does **NOT** protect generic animal/character concepts or public domain folklore motifs. |
| **Audio/Video Media** | Educational video explainers, animated shorts, Socratic voiceovers, interactive audio | Protects original audiovisual recordings, audio tracks, and storyboard illustrations. | Does **NOT** protect generic educational topics or factual historical/scientific information. |
| **Educational Scripts & Text** | Socratic prompts, pedagogy rules, system prompt engineering, original quiz questions, lesson outlines | Protects original written explanatory text, question phrasing, and curated pedagogical narratives. | Does **NOT** protect academic facts (e.g., Pythagoras theorem, Newton's laws, NCERT textbook formulas). |
| **Database Schemas & Data** | PostgreSQL schemas, table relational structures, taxonomy indices, curated lesson metadata | Protects original selection, arrangement, and creative compilation of database records (*sweat of the brow / modicum of creativity*). | Does **NOT** protect raw public domain facts or single data points extracted in isolation. |

#### The Idea-Expression Dichotomy (*R.G. Anand v. Delux Films, AIR 1978 SC 1613*)
Copyright protects **only the original expression of an idea**, never the idea itself. A competitor may independently build a "safe educational platform for K-12 students" with their own code, brand, and design without infringing Edufeedia's copyright, provided they do not copy Edufeedia's literal code, UI artwork, pedagogical scripts, or proprietary compilations.

---

### B. Trademark Protection (Trade Marks Act, 1999)

#### Strategic Protection Objectives
Trademark protection provides exclusive statutory rights to the brand name, prevents consumer confusion, stops copycats from trading on Edufeedia's reputation, and secures brand assets for school licensing and parent trust.

#### Relevant Indian Trademark Classes (Nice Classification)
1. **Class 9 (Primary — Core Software)**:
   - *Downloadable computer software, mobile application software for educational purposes, software for Socratic AI tutoring, recorded computer programs.*
2. **Class 41 (Primary — Educational Services)**:
   - *Education services, interactive learning services, conducting online quizzes and assessments, publication of educational short-form multimedia, pedagogical guidance.*
3. **Class 42 (Primary — SaaS & Cloud Technology)**:
   - *Software as a service (SaaS) featuring platforms for K-12 learning management, cloud-hosted educational portals, algorithmic recommendation services, non-downloadable web application hosting.*
4. **Class 38 (Secondary / Defensive — Telecommunications & Streaming)**:
   - *Digital media streaming, secure peer-to-peer transmission of educational feeds.*

#### Trademark Search Protocol (MANDATORY BEFORE BRAND COMMITMENT)
* **Official Registry Search**: Conduct a comprehensive phonetically and visually similar mark search on the **IP India Public Search Portal** (`ipindiaonline.gov.in`) across classes 9, 41, and 42.
* **Identify Conflicting Names**: Search prefixes/variants: `Edufeed`, `Edfeedia`, `Edufeedia`, `Feedia`, `EduMedia`.
* **Examine Common Law Conflicts**: Search MCA corporate registrations, Indian startup directories, Google Play Store, Apple App Store, and social media handles.
* **Assessment**: Confirm absence of registered prior marks in similar education/software classes that could lead to Section 11 relative grounds objections or trademark infringement actions.

---

### C. Trade Secrets & Confidential Information (Common Law & Contract Act, 1872)

Because India lacks a codified Trade Secrets Act, trade secret protection rests upon:
1. **Section 27 of the Indian Contract Act, 1872** (enforceability of non-disclosure covenants during and after association).
2. **Common Law Principles of Equity & Breach of Confidence** (*John Richard Brady v. Chemical Process Equipments, AIR 1987 Del 372*; *Burlington Home Shopping v. Rajnish Chibber, 1995*).

```
   ┌────────────────────────────────────────────────────────┐
   │        TRADE SECRET TRIAD REQUIRED UNDER INDIAN LAW    │
   ├────────────────────────────────────────────────────────┤
   │ 1. Information has commercial value from secrecy       │
   │ 2. Information is NOT generally known to the public     │
   │ 3. Owner takes ACTIVE, REASONABLE MEASURES of secrecy   │
   └────────────────────────────────────────────────────────┘
```

#### Edufeedia Confidential Information Inventory:
1. **Recommendation & Ranking Logic**: Hybrid scoring math, cold-start fallback weights, curriculum-drift detection rules, cognitive load pacing.
2. **Socratic AI Gateway & Prompt Engineering**: Multi-turn system prompts, fail-closed safety triggers, moderation taxonomies, student intent classifiers.
3. **Curriculum Mapping & Internal Embeddings**: Chunking methodologies, vector dimensions, specialized topic-mastery graphs.
4. **Business Strategy & Product Roadmap**: School pricing models, pilot partnership lists, DPDP compliance audit architecture, unreleased parent controls.

---

## 3. Patentability Analysis under Indian Law

### Statutory Reality: Section 3(k) of The Patents Act, 1970
Section 3(k) explicitly excludes from patentability:
> *"a mathematical or business method or a computer programme per se or algorithms."*

### Guidelines for Examination of Computer Related Inventions (CRI Guidelines, 2017)
The Indian Patent Office and Delhi High Court jurisprudence (*Ferid Allani v. Union of India, 2019*; *Microsoft Technology Licensing v. Assistant Controller, 2023*) establish that software is patentable **ONLY IF**:
1. It produces a **technical effect** or makes a **technical contribution** outside of generic software execution.
2. It solves a specific **technical problem** using a novel technical architecture (e.g., enhanced cryptographic security, novel data transmission compression, hardware-tied sensor verification).

### Application to Edufeedia
* **NON-PATENTABLE (Section 3(k) Exclusions)**:
  - The business concept of a "safe educational feed for students under 18".
  - Curating educational videos based on academic syllabus.
  - Generating quizzes automatically from video transcripts.
  - Spaced repetition schedules and gamification reward algorithms.
  - Scoring models and dashboard analytics.
* **POTENTIALLY PATENTABLE (Requires Deep Technical Examination)**:
  - If Edufeedia engineers a novel, hardware-tied, client-side zero-knowledge audit chain that cryptographically proves parental consent on low-resource mobile devices without exposing personal data.
  - If a novel, hardware-optimized local embedding compression algorithm enables real-time vector search on edge devices without server round-trips.

> [!WARNING]
> **Strict First-to-File Rule**: India does not have a broad one-year public disclosure grace period. If a genuinely novel technical invention is developed, **no public disclosure, demo, investor presentation, or open-source release may occur before filing a Provisional Patent Application**.

---

## 4. IP Ownership: Founders, Employees & Contractors

### The Critical Trap of Section 17 & 19 of the Copyright Act, 1957

```
                     ┌─────────────────────────────┐
                     │   WHO CREATED THE WORK?     │
                     └──────────────┬──────────────┘
                                    │
            ┌───────────────────────┴───────────────────────┐
            ▼                                               ▼
┌───────────────────────────────┐       ┌───────────────────────────────┐
│     FULL-TIME EMPLOYEE        │       │  FREELANCER / CONTRACTOR /    │
│    (Contract of Service)      │       │     CO-FOUNDER / AGENCY       │
└──────────────┬────────────────┘       └──────────────┬────────────────┘
               │                                        │
    Section 17(c) applies:                   Section 17 does NOT apply:
Employer owns copyright automatically    Creator owns copyright by default,
  (Subject to employment terms)           even if you paid 100% of invoice!
                                                        │
                                                        ▼
                                             MANDATORY REQUIREMENT:
                                         Signed written IP Assignment 
                                          Agreement under Section 19!
```

### Mandatory Requirements for Indian IP Assignment Clauses (§19):
Every assignment agreement with any developer, freelancer, designer, agency, or co-founder MUST include:
1. **Specific Identification**: Identify the exact works (code, designs, documentation, assets).
2. **Perpetual Duration**: Expressly state the assignment is **in perpetuity** (otherwise, under Section 19(5), it lapses back to the creator after **5 years**).
3. **Worldwide Territory**: Expressly state the territory is **worldwide** (otherwise, under Section 19(6), it is limited strictly to India).
4. **Royalty-Free & Consideration**: State that the fee paid represents full, adequate consideration, with no recurring royalty obligations.
5. **Waiver of Section 19(4)**: Expressly exclude Section 19(4) (which causes assignment to lapse if not exercised within 1 year).
6. **Moral Rights Waiver**: Include a waiver of moral rights under Section 57 to the maximum extent permitted by Indian law.

---

## 5. Non-Disclosure & Confidentiality Strategy

### What an NDA Can and Cannot Do
* **What an NDA Can Do**:
  - Establishes a formal legal obligation of confidence under the Indian Contract Act.
  - Serves as prima facie proof in court that information was disclosed confidentially.
  - Creates deterrence against casual disclosure by contractors, advisors, and vendors.
* **What an NDA Cannot Do**:
  - It does **not** transfer ownership of IP (an NDA is never a substitute for an IP Assignment).
  - It cannot protect public information, common knowledge, or concepts developed independently.
  - Most venture capital (VC) investors will refuse to sign NDAs during initial pitch meetings.

### When to Require an NDA:
* **MANDATORY**: Before sharing codebase access, proprietary algorithms, database schemas, internal prompts, or product roadmaps with contractors, freelancers, software agencies, or prospective technical hires.
* **RECOMMENDED**: In bilateral discussions with pilot schools, content licensing partners, or distribution partners where sensitive business terms or unreleased features are disclosed.
* **NOT PRACTICAL**: Cold investor outreach. Instead, rely on a **two-tier disclosure model**: share non-confidential pitch deck publicly, and share confidential architecture only in due diligence under NDA.

---

## 6. Open-Source Software (OSS) Governance

Open-source libraries significantly accelerate development, but incompatible licenses create existential IP contamination risks.

```
┌─────────────────────────────────┬─────────────────────────────────┬─────────────────────────────────┐
│     PERMISSIVE (SAFE TO USE)    │      WEAK COPYLEFT (CAUTION)    │    STRONG COPYLEFT (FORBIDDEN)  │
├─────────────────────────────────┼─────────────────────────────────┼─────────────────────────────────┤
│ MIT, Apache 2.0, BSD-2/3, ISC   │ LGPL v2.1/v3, MPL 2.0           │ GPL v2/v3, AGPL v3              │
│                                 │                                 │                                 │
│ Safe for proprietary backend    │ Can be used as dynamically      │ MUST NEVER be linked or included│
│ and frontend platforms.         │ linked libraries without        │ in Edufeedia proprietary core.  │
│ Retain copyright notices.       │ contaminating core code.        │ Compels opening proprietary code│
└─────────────────────────────────┴─────────────────────────────────┴─────────────────────────────────┘
```

### Action Requirement:
Maintain [`docs/THIRD_PARTY_LICENSES.md`](file:///c:/Users/Rehan%20Shaikh/Downloads/web%20dev/projects/edufeedia/docs/THIRD_PARTY_LICENSES.md) listing every OSS library, its license, and repository URL. Scan dependencies using automated license-audit tools in CI.

---

## 7. AI-Generated Content & IP Protection

Edufeedia leverages AI models for Socratic dialog, automated quiz synthesis, and educational animations.

### Legal Reality: Human Authorship Required
* Under Section 2(d)(vi) of the Copyright Act, 1957, copyright requires a human creator who "causes the work to be created".
* **Raw, unedited AI outputs** (e.g., text generated by an LLM with a generic prompt, or images generated without human modification) may lack copyright protectability in India.
* **Protectable Elements**:
  - Proprietary prompt engineering sequences, multi-step orchestration workflows, and prompt templates (protected as confidential trade secrets).
  - Substantial human curation, editing, pedagogical validation, and artistic arrangement of generated materials.
* **Terms of Service Compliance**:
  - Review the commercial licensing terms of model providers (OpenAI, Anthropic, Google Gemini, Midjourney). Ensure terms grant full commercial ownership and do not train public models on confidential Edufeedia inputs.
* **Infringement Safeguards**:
  - Never include copyrighted third-party textbook text or proprietary question banks directly in AI prompts without authorization.

---

## 8. Student & Child Data Protection (DPDP Act, 2023 §9)

### IP Protection vs. Privacy Compliance: Crucial Distinction
* **IP Protection** establishes Edufeedia's exclusive ownership over its proprietary technology, codebase, brand, and creative works.
* **Data Privacy Compliance** represents non-negotiable statutory obligations governing the processing of personal data belonging to children under 18.

### Mandatory DPDP Act §9 Principles:
1. **Verifiable Parental Consent (VPC)**: Mandatory guardian consent before processing any minor's data or enabling AI Socratic tutoring.
2. **Prohibition of Behavioral Tracking**: Zero behavioral monitoring, profiling, or targeted advertisements directed at minors.
3. **No Detrimental Processing**: Prohibit any processing that negatively affects child psychological or physical well-being.
4. **Data Minimization & Ephemeral Storage**: Collect only essential learning telemetry, hash identifiers, and implement automatic session data pruning.

---

## 9. Comprehensive IP Risk Matrix

| Risk Scenario | Edufeedia Vulnerability Point | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :---: | :---: | :--- |
| **Contractor IP Claim** | Freelancer builds React UI or AI module and later claims copyright ownership. | High | Critical | Execute written IP Assignment Agreement (§19) **prior** to granting repo access or paying first invoice. |
| **Brand Copycat / Squatting** | Competitor registers "Edufeedia" or confusingly similar domain/trademark in Class 41/42. | High | High | Conduct official TM search now; file Form TM-A in Classes 9, 41, and 42 before public announcement. |
| **Trade Secret Leakage** | Socratic prompts or hybrid recommendation weights exposed publicly or taken by departing team member. | Medium | High | Enforce least-privilege repository permissions, private repos, secrets auditing in CI, and clear NDA obligations. |
| **OSS Copyleft Contamination** | Developer inadvertently imports an AGPL-3.0 library into backend API core. | Medium | Critical | Add automated license scanning in CI; enforce strict prohibition against GPL/AGPL in dependency policy. |
| **Premature Public Disclosure** | Founder demos proprietary technical mechanism at a hackathon before filing provisional patent. | Medium | Critical | Implement 3-tier disclosure system. Keep novel technical mechanisms under strict confidentiality until patent counsel review. |
| **Third-Party Content Infringement** | Ingesting NCERT or YouTube content beyond fair dealing or valid license boundaries. | Medium | High | Maintain strict provenance metadata, verify OER open licenses, use official embedding protocols (e.g., YouTube oEmbed). |
| **DPDP Act §9 Non-Compliance** | Profiling student screen-time or collecting student data without verifiable parental consent. | Low (Mitigated) | Critical | Authoritative `ConsentService` architecture, verified email OTP parental consent, fail-closed AI access. |

---

## 10. Master Folder & Documentation System

Structure all IP, governance, and development history records in the repository as follows:

```
edufeedia/
├── docs/
│   ├── ip_governance/
│   │   ├── 01_MASTER_IDEA_RECORD.md
│   │   ├── 02_PRODUCT_SPECIFICATION.md
│   │   ├── 03_TECHNICAL_SPECIFICATION.md
│   │   ├── 04_INNOVATION_RECORDS/
│   │   │   └── IR-2026-001_socratic_fail_closed_gateway.md
│   │   ├── 05_IP_ASSET_REGISTER.md
│   │   └── templates/
│   │       ├── MUTUAL_NDA_TEMPLATE.md
│   │       ├── CONTRACTOR_IP_ASSIGNMENT_CHECKLIST.md
│   │       └── FOUNDER_IP_ASSIGNMENT_TEMPLATE.md
│   ├── CONSENT.md
│   ├── DEPLOYMENT.md
│   ├── DATABASE.md
│   └── THIRD_PARTY_LICENSES.md
├── backend/
│   └── scripts/
│       └── audit_git_secrets.py
├── CLA.md
├── CONTRIBUTING.md
├── LICENSE
├── NOTICE
├── SECURITY.md
└── TRADEMARKS.md
```

---

## 11. Prioritized 5-Stage IP Implementation Plan

### Stage 1: DO THIS NOW (Immediate Baseline)
* [x] Maintain private Git repository with strict branch protection on `main`.
* [ ] Initialize Document 01 (`01_MASTER_IDEA_RECORD.md`) with timestamped founder signatures.
* [ ] Execute Founder IP Assignment into the holding corporate vehicle (or execute explicit founder-ownership declaration).
* [ ] Conduct professional trademark search for "Edufeedia" on `ipindiaonline.gov.in` across classes 9, 41, and 42.
* [ ] Ensure all API keys and production credentials pass automated git secret audit (`audit_git_secrets.py`).

### Stage 2: DO THIS DURING DEVELOPMENT (Continuous Hygiene)
* [ ] Require signed Contractor IP Assignment (with §19 perpetual, worldwide clauses) before any freelancer writes a single line of code.
* [ ] Maintain [`docs/THIRD_PARTY_LICENSES.md`](file:///c:/Users/Rehan%20Shaikh/Downloads/web%20dev/projects/edufeedia/docs/THIRD_PARTY_LICENSES.md) for every `npm` and `pip` package; ban AGPL/GPL dependencies.
* [ ] Use GPG-signed Git commits (`git commit -S`) to establish cryptographic non-repudiation of code creation dates.
* [ ] File an Innovation Record (`IR-YYYY-NNN`) whenever a potentially patentable technical architecture or mechanism is engineered.

### Stage 3: DO THIS BEFORE SHARING (Pre-Disclosure & Partnerships)
* [ ] Apply 3-Tier Disclosure: Share public pitch deck freely; share architecture only under signed NDA.
* [ ] File Form TM-A with Indian Trade Marks Registry for "Edufeedia" in Classes 9, 41, and 42 to establish priority date.
* [ ] If any Innovation Record demonstrates genuine technical contribution beyond CRI exclusions, consult an Indian Patent Agent and file a **Provisional Patent Application** *before* sharing technical details.

### Stage 4: DO THIS BEFORE COMMERCIAL LAUNCH (Public Rollout)
* [ ] Publish comprehensive public **Terms of Service** and **Privacy Policy** fully aligned with the DPDP Act 2023.
* [ ] Ensure verifiable parental consent (`ConsentService`) is active on all under-18 student accounts.
* [ ] Audit all multimedia assets: verify licenses for all mascot illustrations, audio tracks, and stock assets.
* [ ] Perform final secret scanner audit and license compliance scan on production release bundle.

### Stage 5: DO THIS WHEN SCALING (Growth & Enterprise)
* [ ] Expand trademark registrations internationally (via Madrid Protocol) across target expansion jurisdictions.
* [ ] Formalize full-time employee contracts with robust post-termination confidentiality and invention-assignment terms.
* [ ] Conduct annual third-party IP audits and SOC2/ISO27001 data governance certifications for enterprise school procurement.

---

*Disclaimer: This document establishes an operational intellectual property governance system and technical workflow based on Indian intellectual property and data protection statutes. It does not constitute formal individualized legal advice. For formal trademark filing, patent drafting, or dispute representation, engage an advocate enrolled with the Bar Council of India or a registered Patent/Trademark Agent.*
