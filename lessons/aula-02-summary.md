# Aula 02 - Spec-Driven Development & AI-Native Workflows

> **Lecture Date:** Class 02 | **Duration:** ~2+ hours | **Instructor:** Hugo
> **Confidence:** 0.92 (HIGH)
> **Format:** Live coding demonstration with interactive Q&A

---

## Executive Summary

This lecture introduced the transition from **Vibe Coding** (ad-hoc AI-assisted development) to **structured AI-native workflows** using Spec-Driven Development (SDD) and the Dev Loop methodology. The instructor demonstrated how to build production-grade invoice processing pipelines using specialized AI agents, knowledge bases, and systematic development processes. Key concepts included: standardization through agents, the importance of reading and patience in the AI era, and three distinct development maturity levels (Vibe Coding → Agent Check/Dev Loop → Spec-Driven Development).

---

## Table of Contents

1. [Key Concepts & Topics Covered](#1-key-concepts--topics-covered)
2. [Learning Objectives](#2-learning-objectives)
3. [Important Definitions & Explanations](#3-important-definitions--explanations)
4. [Examples & Demonstrations](#4-examples--demonstrations)
5. [Exercises & Action Items](#5-exercises--action-items)
6. [Questions Raised by Students](#6-questions-raised-by-students)
7. [Technical Details & Architecture](#7-technical-details--architecture)
8. [Next Steps & Future Topics](#8-next-steps--future-topics)
9. [Teaching Methods & Pedagogical Approach](#9-teaching-methods--pedagogical-approach)
10. [Resources & References](#10-resources--references)

---

## 1. Key Concepts & Topics Covered

### 1.1 Three Maturity Levels of AI-Native Development

| Level | Approach | Characteristics | Use Cases |
|-------|----------|-----------------|-----------|
| **Vibe Coding** | Ad-hoc prompting | Intelligence in developer's head, context-dependent, minimal structure | Quick fixes, experiments, solo prototypes |
| **Agent Check / Dev Loop** | Structured iteration with agents | Uses specialized agents, knowledge bases, PROMPT.md files, iterative refinement | Knowledge base building, utilities, single features |
| **Spec-Driven Development (SDD)** | Full traceability pipeline | 5-phase workflow (/brainstorm → /define → /design → /build → /ship), complete documentation, team collaboration | Production features, enterprise projects, regulated environments |

### 1.2 Core Philosophy Shifts

**From Traditional → AI-Native:**

- Waterfall → Iterative with agents
- Separate documentation → Living specs
- Code review → Dual AI review (human + agents)
- Knowledge in heads → Knowledge bases
- Manual standardization → Agent-enforced patterns

**Critical Mindset Change:**
> "Not writing code is harder than writing code" - Hugo

**Reasoning:** Working alone requires one mental model. Working in teams requires integration, standardization, and patience - areas where AI agents excel at enforcement but humans struggle with consistency.

### 1.3 Skills for 2026 and Beyond

1. **Reading comprehension** - Ability to digest agent outputs, specifications, and documentation
2. **Patience** - Resisting social media-conditioned instant gratification
3. **Attention** - "Attention is all you need" (reference to transformer architecture paper, applied to human workflow)
4. **Slow thinking** - Taking time to understand context rather than rushing to code

**Key Quote:**
> "Social media took our patience away. We scroll for quick dopamine hits. Now we need to slow down our minds again. Reading is the critical skill for 2026."

---

## 2. Learning Objectives

By the end of this lecture, students should be able to:

### Primary Objectives

- [ ] **Distinguish** between Vibe Coding, Agent Check/Dev Loop, and Spec-Driven Development workflows
- [ ] **Understand** why AI can write better code than humans (with proper instructions)
- [ ] **Recognize** when to use each development maturity level based on task complexity
- [ ] **Create** structured prompts using context engineering techniques
- [ ] **Utilize** specialized agents (meeting-analyst, the-planner, prompt-crafter) for different tasks
- [ ] **Appreciate** the importance of standardization and knowledge bases in team environments

### Secondary Objectives

- [ ] Recognize the friction caused by "vibe coding" perception differences between engineers and non-engineers
- [ ] Understand the Ralph Wingham loop concept for iterative agent refinement
- [ ] See the value of extracting meeting notes into structured requirements
- [ ] Grasp the prototype-first approach for validating business requirements

---

## 3. Important Definitions & Explanations

### 3.1 Vibe Coding

**Definition:** Ad-hoc AI-assisted development where the developer provides informal prompts without structured process or documentation.

**Characteristics:**

- Intelligence lives in the developer's head
- Context-dependent on the developer's mood, productivity, and vision
- Minimal structure or repeatability
- Fast for simple tasks, risky for complex work

**When to Use:**

- Quick fixes (e.g., "Fix this field validation")
- Small changes (e.g., "Add logging to this function")
- Prototyping and experimentation
- Solo developer scenarios

**Trade-off:**
> "When you write code just for yourself, it's one thing. When you write code for a team, things start entering a negative loop."

### 3.2 Agent Check / Dev Loop (Level 2)

**Definition:** A structured iterative development approach using specialized agents, knowledge bases, and PROMPT.md files with session recovery capabilities.

**Architecture:**

```text
User Input → Prompt Crafter → PROMPT.md → Dev Loop Executor
                                              ↓
                                         Agent Loop
                                         (Ralph Wingham)
                                              ↓
                                         Validation
                                              ↓
                                         Output + Progress Tracking
```

**Components:**

1. **Prompt Crafter Agent** - Transforms informal requests into structured prompts using context engineering
2. **PROMPT.md Files** - Persistent prompt documents that can be version-controlled
3. **Ralph Wingham Loop** - Iterative refinement pattern where agent continuously improves output until exit criteria met
4. **Session Recovery** - Ability to resume interrupted work (`/dev tasks/PROMPT_X.md --resume`)

**When to Use:**

- Knowledge base creation
- Utility and parser development
- Single feature implementation
- Prototyping with more structure than vibe coding

**Key Innovation:**
> "The Dev Loop sits between vibe coding and spec-driven development. It brings structure without the overhead of full traceability."

### 3.3 Spec-Driven Development (SDD)

**Definition:** A comprehensive 5-phase development methodology with complete traceability, designed for production features requiring team collaboration and documentation.

**Five Phases:**

| Phase | Command | Model | Purpose | Output |
|-------|---------|-------|---------|--------|
| 0 | `/brainstorm` | Opus | Explore ideas through dialogue (optional) | Brainstorming notes |
| 1 | `/define` | Opus | Capture and validate requirements | DEFINE.md |
| 2 | `/design` | Opus | Create architecture and specification | DESIGN.md |
| 3 | `/build` | Sonnet | Execute implementation with verification | Code + BUILD_REPORT.md |
| 4 | `/ship` | Haiku | Archive with lessons learned | Archive + SHIPPED.md |
| - | `/iterate` | Any | Update documents when changes needed | Updated specs |

**Directory Structure:**

```text
.claude/sdd/
├── features/           # Active development
│   ├── FEATURE_X_DEFINE.md
│   ├── FEATURE_X_DESIGN.md
│   └── FEATURE_X_BUILD_REPORT.md
├── archive/            # Shipped features
│   └── FEATURE_X_SHIPPED/
├── architecture/       # System-wide decisions
└── examples/           # Reference implementations
```

**When to Use:**

- New production features
- Multi-version implementations (v1 → v2 migration)
- Features requiring architectural decisions
- Team collaboration scenarios
- Regulatory/compliance requirements

**Benefits:**

- Complete traceability from requirements to code
- Team visibility into decisions
- Clear scope boundaries (in-scope vs. out-of-scope)
- Documentation that stays current
- Onboarding new team members

### 3.4 Key Technical Concepts

#### Structured Outputs

**Definition:** Forcing LLMs to return predictable, schema-compliant data using validation frameworks like Pydantic.

**Example:**

```python
# Instead of free-form text, enforce structure:
class Restaurant(BaseModel):
    name: str
    description: str
    address: str
    type: str
    certificate: str

class OrderItem(BaseModel):
    items: List[Item]  # Force list structure
```

**Why Important:**
> "How do you make AI outputs predictable? You force structured output. When you work with data pipelines, this is essential."

#### Knowledge Bases (KB)

**Definition:** Domain-specific documentation organized in a standardized structure that agents can query for context.

**Structure:**

```text
.claude/kb/{domain}/
├── index.md           # Domain overview
├── quick-reference.md # Cheat sheet
├── concepts/          # Core concepts
├── patterns/          # Implementation patterns
└── specs/             # YAML specifications
```

**Purpose:**

- Extract knowledge from individual developers' heads
- Provide consistent context to all agents
- Enable new team members to onboard faster
- Create "single source of truth" for development patterns

#### Ralph Wingham Loop

**Definition:** An iterative refinement pattern where an agent runs in a continuous loop, improving its output until exit criteria are met.

**Mechanism:**

```text
1. Agent generates output
2. Validate against criteria
3. If criteria not met → continue loop (go to step 1)
4. If criteria met → exit loop
5. Return final output
```

**Origin:** Named after a pattern developed by the Claude Code community for autonomous agent iteration.

**Application:** Used in Dev Loop to continuously refine code until quality thresholds are satisfied.

---

## 4. Examples & Demonstrations

### 4.1 Live Demonstration: Invoice Extraction Prototype

**Context:** Building a prototype to extract structured data from delivery platform invoices (UberEats, DoorDash, Grubhub, iFood, Rappi).

#### Challenge

- Multiple vendor formats (5 different invoice types)
- TIFF files (not natively supported by Gemini)
- Multi-page documents with page breaks
- Need for validation (e.g., line item totals must match invoice total)

#### Vibe Coding Approach (Demonstrated First)

**Student Prompt Example:**

```text
I have invoice samples in examples/invoices/.
I need to build an extraction prototype.

Requirements:
- Invoices land in data/input
- Processing needs to use Gemini Flash 2.5 via OpenRouter
- Output needs to be structured
- Adding validation using Pydantic model
- Output in parquet and JSON
- Logs for observability
- Code should go in src/invoice_extractor/
```

**Observations:**

- This is vibe coding - intelligence is in the developer's head
- Depends on how detailed the developer is feeling that day
- No structured process
- Fast but not repeatable

#### Agent Check Approach (Demonstrated Second)

**Step 1: Use Meeting Analyst Agent**

```bash
# Prompt given to Claude
Use @meeting-analyst to analyze notes/summary-requirements.md
Extract requirements for creating an invoice local processor
Parse requirements, identify Pydantic schemas
List technologies, define acceptance criteria
Output: clean, technical, max 100 lines
Write to design/invoice-extractor-requirements.md
```

**What Happened:**

- Agent read 6 meeting transcripts consolidated in summary file
- Extracted core requirements automatically
- Identified that TIFF → PNG conversion needed
- Recognized structured output requirement
- Determined in-scope vs. out-of-scope (no cloud deployment in prototype)

**Step 2: Use The Planner Agent**

```bash
# Refine requirements into design
@the-planner: Create design document with these 6 implementation sections:
1. Architecture overview
2. Component breakdown
3. Pydantic schemas
4. Technology stack
5. Acceptance criteria
6. Out-of-scope items

Write to design/invoice-extractor-design.md
```

**Result:**

- Planner refined requirements into structured design
- Automatically included Pydantic schema definitions
- Listed technologies (Gemini 2.0 Flash, OpenRouter, Pillow for TIFF conversion)
- Defined clear acceptance criteria
- Documented out-of-scope: BigQuery, Terraform, deployment, monitoring

**Key Teaching Point:**
> "See how fast that was? The Meeting Analyst understood the context because we documented everything in the meetings. This is why requirements gathering is critical - the more insights you capture, the better your agents perform."

#### Comparison Table

| Aspect | Vibe Coding | Agent Check | Spec-Driven |
|--------|-------------|-------------|-------------|
| **Time to Setup** | 0 min | 2 min | 10-15 min |
| **Prompt Complexity** | Medium | Low (agents handle it) | Very Low (phases guide) |
| **Repeatability** | Low | Medium | High |
| **Team Visibility** | None | Some | Complete |
| **Documentation** | None | Design docs | Full traceability |
| **Best For** | Solo, quick tasks | Prototypes, utilities | Production features |

### 4.2 Repository Anti-Patterns (Discussed)

**Real-world problems the instructor has encountered:**

1. **Outdated README** - "How many times have you entered a repository where the README wasn't updated?"
2. **No CHANGELOG** - Changes not documented
3. **Direct main commits** - No PR workflow
4. **Hardcoded values** - "Theoretically working code but tons of hardcoded stuff"
5. **TODO overload** - "You open the code and there are 300 TODOs"
6. **Comment pollution** - "Code is all commented with what will be done"

**Solution with Agents:**
> "Today we can automatically improve this process in ways we couldn't before. The process hasn't changed - our enforcement capability has."

### 4.3 Technology Stack Example

**For Invoice Processing Prototype:**

| Component | Technology | Reason |
|-----------|------------|--------|
| LLM | Gemini Flash 2.5 (upgraded to 3.0) | Multimodal document understanding |
| LLM Gateway | OpenRouter | Abstraction layer, fallback capability |
| Validation | Pydantic v2 | Structured output enforcement |
| Image Processing | Pillow | TIFF → PNG conversion |
| Output Formats | JSON + Parquet | Debugging + production pipeline |
| Observability | Logging (structured) | Prototype-level monitoring |

**Explicitly Out of Scope:**

- Cloud deployment (GCP Cloud Functions)
- BigQuery integration
- Terraform infrastructure
- Langfuse observability
- Production monitoring

**Reasoning:**
> "What's the purpose of a prototype? Validate if we can actually meet the business requirement. Can we read these invoices and process them? That's what we need to prove."

---

## 5. Exercises & Action Items

### 5.1 Mentioned During Lecture

**Immediate Actions for Students:**

1. **Install SDD in Your Repositories**
   - Take the SDD structure shown
   - Add to your current projects
   - Start using the 5-phase workflow

2. **Practice Patience and Reading**
   - Consciously slow down when reviewing agent outputs
   - Read entire specifications before coding
   - Practice "slow thinking" on complex problems

3. **Create Knowledge Bases**
   - Document your team's coding patterns
   - Extract tribal knowledge into KB structure
   - Make it accessible to agents

4. **Experiment with Development Levels**
   - Use Vibe Coding for quick fixes
   - Use Dev Loop for utilities
   - Use SDD for your next production feature

### 5.2 Implicit Practice Opportunities

**Based on Demonstrations:**

- [ ] Build an invoice extractor prototype using the approaches shown
- [ ] Convert existing meeting notes into structured requirements using meeting-analyst
- [ ] Create a PROMPT.md file for a utility you need to build
- [ ] Set up the Ralph Wingham loop pattern in your workflow
- [ ] Compare code quality between vibe coding and agent check approaches

### 5.3 Reflection Questions

1. Where in your current workflow are you doing vibe coding when you should use structure?
2. What knowledge is trapped in your head that should be in a knowledge base?
3. Which repositories would benefit most from SDD implementation?
4. How can you improve your reading and patience practices?

---

## 6. Questions Raised by Students

### 6.1 Student Questions (from chat)

**Q1: "Do you believe we can code better than AI in general?"**

- **Instructor's Answer:** "Not anymore. Looking at Opus 4.5, I really don't believe that - with correct instructions. The key is instructing correctly."
- **Follow-up Discussion:** There's lots of "slop" (bad AI-generated code), but that's about who's writing it and how, not the AI's capability.

**Q2: "Is this vibe coding?"** _(referring to the structured prompt example)_

- **Instructor's Answer:** "Yes, this is still vibe coding. The intelligence is in our heads. This depends on our mood, productivity level, current vision. Do you understand?"

**Q3: "Who here is using spec-driven development in production?"**

- **Response:** Very few hands (poll showed minimal adoption)
- **Instructor's Reaction:** "I think what you'll see here will be very surprising. We'll have several 'aha moments', okay?"

**Q4: "Shouldn't we add alerting systems to the prototype?"**

- **Instructor's Answer:** "I like alerting systems, but it doesn't fit in the prototype. This is what I want to know. As a data engineer, what should you keep in mind? We need to pay attention to what we're going to do and what we're going to solve. What's the intention of the prototype? Validate if it's really possible to meet the business requirement."

**Q5: "Should we add simple component tests?"**

- **Instructor's Answer:** "I like that too. Good thinking."

**Q6: "Add code style guides?"**

- **Instructor's Answer:** "Code style guides are great - if it's important to the project and company culture, I do include coding guides. Good point."

### 6.2 Instructor Polling Questions

**Q: "Do you all agree with me?"** _(about vibe coding being unstructured)_

- **Context:** Validating understanding that ad-hoc prompting lacks structure
- **Student Response:** General agreement in chat

**Q: "What would you do first?"** _(when building the prototype)_

- **Context:** Soliciting student input on prototype requirements
- **Responses included:**
  - Output in JSON
  - Logs and observability
  - Using Gemini 3.0
  - Alerting systems
  - Simple tests
  - Code examples

**Q: "Who has felt this?"** _(about working in teams with different code standards)_

- **Context:** Discussing the challenge of standardization
- **Student Response:** Many acknowledged the pain

---

## 7. Technical Details & Architecture

### 7.1 Agent Architecture Components

**Standard Agent Structure:**

```text
┌─────────────────────────────────────────┐
│            AGENT                         │
├─────────────────────────────────────────┤
│ 1. System Prompt                         │
│    └─ Role, capabilities, constraints    │
│                                          │
│ 2. Tool Access                           │
│    └─ File ops, search, execution       │
│                                          │
│ 3. Knowledge Base                        │
│    └─ Domain-specific context           │
│                                          │
│ 4. Observability                         │
│    └─ Logging, tracing, metrics         │
└─────────────────────────────────────────┘
```

**Why This Works:**

1. **Context Control** - Each agent has focused expertise
2. **Ultra-Specialization** - Agents can be hyper-specialized for specific tasks
3. **Composability** - Agents can call other agents (meeting-analyst → the-planner)

### 7.2 Dev Loop Architecture (Level 2)

```text
User Request
     ↓
┌─────────────────────┐
│  Prompt Crafter     │ ← Uses context engineering
│  Agent              │    and prompt techniques
└─────────────────────┘
     ↓
  PROMPT.md File
  (Versioned)
     ↓
┌─────────────────────┐
│  Dry Run            │ ← Validate before execution
│  (Optional)         │
└─────────────────────┘
     ↓
┌─────────────────────────────────────┐
│  Ralph Wingham Loop                 │
│  ┌───────────────────────┐         │
│  │ 1. Generate Output    │         │
│  │ 2. Validate           │         │
│  │ 3. Check Exit Criteria│         │
│  │ 4. If not met, retry  │ ←──┐   │
│  └───────────────────────┘    │   │
│            │                   │   │
│            └───────────────────┘   │
└─────────────────────────────────────┘
     ↓
  Validated Output
     ↓
  Progress Tracking
  (Session Recovery)
```

**Exit Criteria Examples:**

- Code passes all tests
- Documentation complete
- Linting passes
- Schema validation successful

### 7.3 SDD Workflow Architecture

```text
Phase 0: /brainstorm (Optional)
    └─> Exploratory dialogue
         └─> Ideas captured in notes

Phase 1: /define
    ├─> Analyze requirements
    ├─> Extract from meetings/stakeholders
    ├─> Validate completeness
    └─> Output: DEFINE.md
         ├─ Functional requirements
         ├─ Non-functional requirements
         ├─ Success criteria
         └─ Constraints

Phase 2: /design
    ├─> Read DEFINE.md
    ├─> Create architecture
    ├─> Define components
    ├─> Choose technologies
    └─> Output: DESIGN.md
         ├─ System architecture
         ├─ Component specs
         ├─ Data models
         ├─ Tech stack
         └─ Out-of-scope items

Phase 3: /build
    ├─> Read DESIGN.md
    ├─> Implement code
    ├─> Write tests
    ├─> Verify against specs
    └─> Output: Code + BUILD_REPORT.md
         ├─ Implementation notes
         ├─ Deviations from design
         ├─ Test results
         └─ Known issues

Phase 4: /ship
    ├─> Validate completeness
    ├─> Archive feature
    ├─> Document lessons learned
    └─> Output: SHIPPED.md + Archive
         ├─ Final metrics
         ├─ Lessons learned
         ├─ Future improvements
         └─ Complete audit trail

/iterate (Any Phase)
    └─> Update documents when requirements change
        └─> Maintains traceability
```

### 7.4 Invoice Processing Example Architecture

**Prototype Design (from demonstration):**

```text
INPUT (data/input/)
    ↓
┌──────────────────────┐
│ TIFF/PDF Detection   │
└──────────────────────┘
    ↓
┌──────────────────────┐
│ TIFF → PNG           │ ← Pillow library
│ Conversion           │   (Gemini doesn't support TIFF)
└──────────────────────┘
    ↓
┌──────────────────────┐
│ Multi-page Handler   │ ← Handle page breaks
└──────────────────────┘
    ↓
┌──────────────────────────────────┐
│ Gemini Flash 2.5/3.0             │
│ via OpenRouter                   │
│                                  │
│ Structured Output Prompting:     │
│  ├─ Restaurant info              │
│  ├─ Order items                  │
│  ├─ Payment summary              │
│  └─ Vendor-specific fields       │
└──────────────────────────────────┘
    ↓
┌──────────────────────┐
│ Pydantic Validation  │
│                      │
│ - Schema compliance  │
│ - Total validation   │
│ - Required fields    │
└──────────────────────┘
    ↓
OUTPUT
    ├─ JSON (debugging)
    └─ Parquet (production)
```

**Key Design Decisions:**

1. **Why TIFF → PNG?** Gemini doesn't natively process TIFF files
2. **Why OpenRouter?** Gateway abstraction, multi-provider fallback
3. **Why Pydantic?** Enforce structured outputs for predictable data pipelines
4. **Why both JSON and Parquet?** JSON for debugging, Parquet for production
5. **Why logging only?** Prototype phase - don't over-engineer monitoring

### 7.5 Knowledge Base Structure (Mentioned)

**Example: OpenRouter KB**

```text
.claude/kb/openrouter/
├── index.md
│   └─ Overview of OpenRouter as LLM gateway
├── quick-reference.md
│   └─ API endpoints, authentication
├── concepts/
│   ├─ multi-provider-fallback.md
│   ├─ model-routing.md
│   └─ cost-optimization.md
└── patterns/
    ├─ structured-output-pattern.md
    └─ retry-strategy-pattern.md
```

**How Agents Use It:**

- Agent receives task: "Use OpenRouter for LLM calls"
- Agent queries KB for OpenRouter patterns
- Agent applies validated patterns automatically
- Result: Consistent implementation across team

---

## 8. Next Steps & Future Topics

### 8.1 Immediate Next Steps (Mentioned in Lecture)

1. **Build Google Cloud Functions**
   - Instructor will demonstrate building Cloud Run Functions
   - Everything can be done via CLI without touching GCP Console
   - "This is very outside the curve" - unique to GCP

2. **Continue SDD Demonstration**
   - Walk through complete /define → /design → /build flow
   - Show PROMPT.md structure in detail
   - Demonstrate Ralph Wingham loop in practice

3. **Deploy to Production**
   - Move from prototype to production implementation
   - Add infrastructure components (BigQuery, Terraform)
   - Integrate observability (Langfuse)

### 8.2 Topics for Future Classes

**Implied but not explicitly scheduled:**

- Full SDD workflow walkthrough (all 5 phases)
- Google Cloud Platform deployment via CLI
- Infrastructure as Code with agents
- Knowledge base creation and maintenance
- Agent composition patterns
- Team adoption of SDD methodology
- Transitioning legacy projects to SDD

### 8.3 Homework/Practice Expectations

**Implicit expectations for students:**

- Implement SDD in personal projects
- Practice using the three maturity levels appropriately
- Build knowledge bases for frequently used technologies
- Experiment with agent composition
- Document findings and share with class

---

## 9. Teaching Methods & Pedagogical Approach

### 9.1 Teaching Style Characteristics

**1. Live Coding & Real-Time Demonstration**

- Instructor demonstrates in real repository
- Shows actual tool usage (Claude Code, agents)
- Makes mistakes and troubleshoots live
- "Let's see what happens" exploratory approach

**2. Socratic Method & Polling**

- Frequently asks "What would you do?"
- Polls students for opinions and experiences
- Validates understanding through questions
- Builds on student responses

**3. Contrast & Comparison**

- Shows vibe coding THEN agent check
- Explicitly compares approaches side-by-side
- Demonstrates why one approach is better
- Uses tables and visual comparisons

**4. Real-World Grounding**

- Shares personal experiences ("In my projects...")
- References actual repository anti-patterns
- Discusses team dynamics and friction
- Acknowledges social media's impact on attention

**5. Philosophical Framing**

- Starts with mindset and cultural context
- Discusses broader trends (AI replacing code writing)
- Questions fundamental assumptions
- "Why is not writing code harder?"

### 9.2 Pedagogical Techniques Used

**Progressive Disclosure:**

```text
Simple concept → Complex example → Deep dive
     ↓              ↓                  ↓
Vibe Coding → Agent Check → Spec-Driven Development
```

**Scaffolding:**

- Builds on Day 1 concepts
- References previous setup (meeting notes, agents)
- Layers complexity gradually
- "Remember yesterday we..."

**Think-Aloud Protocol:**

- Narrates reasoning while coding
- Explains decision-making process
- Verbalizes doubts and corrections
- "What I'm thinking here is..."

**Community Building:**

- Asks for collective experiences
- Validates shared frustrations
- Creates "us vs. the old way" mentality
- "Who here has felt this pain?"

### 9.3 Engagement Strategies

**Interactive Elements:**

1. **Chat Participation** - Students contribute ideas for prototype requirements
2. **Polling** - "Who's using SDD in production?" (shows novelty of approach)
3. **Validation Loops** - "Do you all agree?" (checks understanding)
4. **Prediction** - "What will happen here?" (before running code)

**Attention Management:**

- Uses strong language occasionally ("foda", "tesão") to maintain energy
- Creates suspense ("You'll have several aha moments")
- Varies pace between explanation and demonstration
- Uses repetition for key concepts

**Cognitive Load Management:**

- Introduces one concept at a time
- Provides visual structure (tables, diagrams in explanations)
- Repeats key phrases ("Beleza?" as checkpoints)
- Offers multiple examples of same concept

### 9.4 Assessment Approach

**No Formal Assessment, But Implicit Success Criteria:**

- Can student articulate when to use each maturity level?
- Does student understand agent architecture?
- Can student explain why standardization matters?
- Has student internalized "reading is the skill for 2026"?

**Formative Assessment Through:**

- Chat responses to questions
- Quality of student suggestions during demo
- Level of engagement with concepts
- Understanding shown in follow-up questions

---

## 10. Resources & References

### 10.1 Tools & Technologies Mentioned

| Tool/Tech | Purpose | Context |
|-----------|---------|---------|
| **Claude Code** | AI-native development environment | Primary platform for demonstration |
| **Cursor** | AI code editor | Shown on screen during demo |
| **Gemini Flash 2.5/3.0** | Multimodal LLM | Invoice document processing |
| **OpenRouter** | LLM gateway | Multi-provider abstraction |
| **Pydantic v2** | Schema validation | Structured output enforcement |
| **Pillow** | Image processing | TIFF → PNG conversion |
| **GCP Cloud Functions** | Serverless compute | Future deployment target |
| **BigQuery** | Data warehouse | Production data storage (out of prototype scope) |
| **Terraform** | Infrastructure as Code | Production deployment (out of prototype scope) |
| **Langfuse** | LLM observability | Production monitoring (out of prototype scope) |

### 10.2 Agents Referenced

| Agent Name | Purpose | Used For |
|------------|---------|----------|
| **meeting-analyst** | Extract structured info from meetings | Requirements gathering from notes |
| **the-planner** | Planning, scoping, understanding | Refining requirements into design |
| **prompt-crafter** | Transform informal requests to structured prompts | Dev Loop input processing |
| **code-reviewer** | Code quality analysis | Implied for future use |
| **dual-reviewer** | Human + AI code review | Mentioned as modern practice |

### 10.3 Methodologies & Frameworks

**Spec-Driven Development (SDD)**

- Proprietary methodology developed by instructor
- 5-phase workflow with complete traceability
- Positioned as "next stage" beyond vibe coding

**Dev Loop (Level 2)**

- Structured iteration framework
- Uses Ralph Wingham loop pattern
- PROMPT.md-based workflow

**Ralph Wingham Loop**

- Named pattern from Claude Code community
- Continuous iteration until exit criteria met
- Core mechanism of Dev Loop

**Agent Check**

- Term used interchangeably with Dev Loop
- Structured agent usage with knowledge bases

### 10.4 Repository Structure References

**Paths Mentioned:**

```text
notes/summary-requirements.md    # Consolidated meeting notes
design/                          # Design documents
.claude/sdd/features/           # Active SDD features
.claude/sdd/archive/            # Shipped features
.claude/kb/                     # Knowledge bases
examples/invoices/              # Sample invoice files
data/input/                     # Prototype input directory
src/invoice_extractor/          # Prototype code location
```

### 10.5 External References

**"Attention Is All You Need"**

- Famous transformer architecture paper (Vaswani et al., 2017)
- Repurposed by instructor to mean "human attention is the critical resource"
- Used to emphasize importance of reading and patience

**Social Media Critique**

- Discussed impact of scrolling on patience
- Reference to dopamine-driven quick gratification
- Argument for "slowing down our minds"

### 10.6 Concepts for Further Study

**Recommended Exploration:**

1. **Context Engineering** - Techniques for providing optimal context to LLMs
2. **Prompt Engineering** - Structured prompt design beyond ad-hoc
3. **Knowledge Base Architecture** - How to organize domain knowledge for agents
4. **Agent Composition** - Chaining specialized agents
5. **Structured Output Techniques** - Pydantic, JSON Schema, function calling
6. **Iterative Refinement Patterns** - Ralph Wingham and similar loops
7. **Documentation as Code** - Living specs that evolve with implementation

---

## Appendix: Key Quotes & Teaching Moments

### Most Impactful Quotes

> "Not writing code is harder than writing code. Why? When you work alone, you have one mental model. When you work in a team, you need to integrate things. And that's annoying."

> "Social media took our patience away. Scrolling for quick videos made our minds addicted to fast pleasure and fast results. Now we need to unlearn that mental process."

> "The skill for 2026? Reading, thinking, and going slow. Attention is all you need."

> "How many times have you entered a repository where the README wasn't updated? With agents, I see this becoming solvable. You know why? Because honestly, how many times have you entered a repo with direct commits to main? With 300 TODOs? With everything hardcoded?"

> "When you're building a prototype with vibe coding, you're trying to bring your experience into the project. When we move to a more strict process, we're trying to standardize."

> "The Meeting Analyst did a great job here. See how fast that was? Because we documented everything in the meetings. This is why requirements gathering is critical."

### Teaching Moments

**Moment 1: The Repository Rant**

- Instructor lists 7+ common repository anti-patterns
- Students recognize every single one
- Creates shared frustration, then offers solution (agents)
- Impact: Establishes credibility and relevance

**Moment 2: The Vibe Coding Reveal**

- Shows a reasonably structured prompt
- Asks "Is this vibe coding?"
- Students hesitate
- Reveals: "Yes, this is STILL vibe coding"
- Impact: Reframes understanding of what "structured" means

**Moment 3: The Speed Demonstration**

- Uses meeting-analyst to extract requirements in seconds
- Students see real-time extraction from 6 meetings
- Requirements appear automatically
- Impact: "Aha moment" about agent capabilities

**Moment 4: The Patience Plea**

- Pauses coding to discuss social media's impact
- "This might seem stupid, but no, it's not"
- Emphasizes reading as critical skill
- Impact: Mindset shift about what success requires

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| **Core Concepts Introduced** | 12+ |
| **Agents Demonstrated** | 3 (meeting-analyst, the-planner, prompt-crafter) |
| **Maturity Levels Defined** | 3 (Vibe Coding, Agent Check/Dev Loop, SDD) |
| **Live Demonstrations** | 2 major (Vibe Coding vs. Agent Check) |
| **Student Interactions** | 10+ questions/polls |
| **Repository Anti-Patterns** | 7 mentioned |
| **Technologies Mentioned** | 15+ |
| **Phases in SDD** | 5 (/brainstorm, /define, /design, /build, /ship) |

---

## Instructor Observations

### What Worked Well

1. **Contrast Teaching** - Showing vibe coding THEN agent check made the difference clear
2. **Live Demonstration** - Real-time agent usage more impactful than slides
3. **Student Polling** - Engaged students, validated shared experiences
4. **Philosophical Framing** - Starting with mindset before diving into tools

### Areas for Expansion

1. **Ralph Wingham Loop** - Mentioned but not fully demonstrated
2. **Full SDD Workflow** - Introduced but not completed
3. **Knowledge Base Creation** - Referenced but not built live
4. **Team Dynamics** - Discussed friction but not solutions in depth

### Student Readiness Indicators

- **High Recognition** - Students identified with repository anti-patterns
- **Low Current Adoption** - Almost no one using SDD in production yet
- **Engagement Level** - Active chat participation throughout
- **Conceptual Understanding** - Successfully distinguished vibe coding from structure

---

## Glossary

| Term | Definition |
|------|------------|
| **Vibe Coding** | Ad-hoc AI-assisted development without structured process |
| **Agent Check** | Structured development using specialized agents and KBs |
| **Dev Loop** | Level 2 workflow with PROMPT.md files and iterative refinement |
| **SDD** | Spec-Driven Development - 5-phase methodology with full traceability |
| **Ralph Wingham Loop** | Iterative agent refinement pattern until exit criteria met |
| **PROMPT.md** | Version-controlled prompt document used in Dev Loop |
| **Knowledge Base (KB)** | Structured domain documentation for agent context |
| **Structured Output** | LLM response constrained to schema (e.g., Pydantic) |
| **The Planner** | Specialized agent for planning and scoping |
| **Meeting Analyst** | Agent for extracting structured info from meeting notes |
| **Prompt Crafter** | Agent that transforms informal requests to structured prompts |
| **Slop** | Low-quality AI-generated code (pejorative) |

---

**Document Version:** 1.0
**Generated:** 2026-01-31
**Confidence Score:** 0.92 (HIGH)
**Source:** /Users/hugogiacomini/GitHub/btc-zero-prd-claude-code/transcriptions/aula-02-transcriptions.txt
**Analysis Framework:** Meeting Analyst 10-Section Framework (adapted for lecture format)

---

## Notes on Analysis Methodology

**Adaptations Made for Lecture Context:**

1. **Decisions → Key Concepts** - Educational content focuses on concepts rather than business decisions
2. **Action Items → Exercises** - Student practice rather than team assignments
3. **Requirements → Learning Objectives** - Educational outcomes instead of project requirements
4. **Stakeholders → Students/Instructor** - Educational roles vs. business roles
5. **Timeline → Course Progression** - Class sequence rather than project milestones

**Confidence Modifiers Applied:**

- Clear speaker attribution (instructor identified): +0.10
- Explicit teaching points documented: +0.05
- Timestamps available for flow tracking: +0.05
- Multiple demonstrations corroborate concepts: +0.05
- Incomplete coverage of some topics (Ralph Wingham, full SDD): -0.05
- Portuguese transcription with occasional ambiguity: -0.03

**Final Confidence:** 0.92 (HIGH - Reliable for comprehensive analysis)

**Limitations:**

- Transcript is in Portuguese; some nuance may be lost in interpretation
- Full SDD demonstration promised but not completed in this lecture
- Ralph Wingham loop mentioned extensively but not shown in detail
- Some student chat responses may not be captured in transcript
- Lecture continues beyond analyzed sections (file truncated for analysis)

**Recommendations for Follow-Up:**

1. Create dedicated SDD workflow tutorial based on promised demonstration
2. Document Ralph Wingham loop implementation with code examples
3. Build sample PROMPT.md templates for common tasks
4. Create knowledge base creation guide
5. Develop SDD adoption checklist for teams
