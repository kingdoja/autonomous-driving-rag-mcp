# Interview Talk Track (3 Minutes)

## Goal

Give a stable, interview-friendly narration for the current `v0.2` medical demo with P1 features.
This talk track must stay aligned with the source-of-truth specs and the validated demo capabilities.

**Demo Chain Options**:
- **P0 Core**: `S1 -> S2 -> S4 -> S7 -> S12` (3 minutes)
- **P1 Enhanced**: `S1 -> S2 -> S4 -> S9 -> S11 -> S12` (3-4 minutes, includes multi-doc comparison and predictive refusal)

## Positioning

Use this one-sentence positioning first:

> This is a medical knowledge and quality assistant for pathology / lab internal use. It focuses on guideline, SOP, training, and device-manual retrieval with citations, supporting multi-document reasoning and advanced boundary handling, rather than automated diagnosis.

## Opening

Recommended duration: 20-30 seconds

Suggested script:

> I took a general modular RAG stack and turned it into a medical knowledge assistant for pathology and lab workflows. The current `v0.2` demo includes both P0 baseline capabilities and P1 advanced features like multi-document reasoning, query complexity analysis, and enhanced boundary handling. It focuses on public guideline, SOP, training, and device-manual materials. The core value is not free-form chatting, but reliable retrieval, multi-source synthesis, traceable citations with metadata, and clear safety boundaries.

## Capability Walkthrough

Recommended duration: 90-120 seconds

### 1. SOP / guideline retrieval (P0)

Suggested script:

> First, I show that a Chinese workflow question can hit the imported SOP and guideline materials. This proves the system can answer process-oriented questions with evidence instead of vague summaries.

What to emphasize:

- Chinese questions can retrieve imported documents.
- Answers should be backed by source snippets.
- This is useful for training and quality-control workflows.

### 2. Device manual retrieval (P0)

Suggested script:

> Then I switch to a device question, using `HistoCore PELORIS 3` in the query. This is one of the strongest demo questions, because it shows the system can route toward the Leica device manual instead of falling back to generic WHO material. The system uses metadata boost to prioritize equipment-specific documentation.

What to emphasize:

- Device queries prioritize equipment manuals over general guidelines.
- Retrieval quality is optimized for medical equipment scenarios.
- This demonstrates domain-specific retrieval tuning.

### 3. Multi-document comparison (P1 - Optional)

Suggested script:

> For P1 capabilities, I can demonstrate multi-document reasoning. When I ask to compare two processes—like specimen reception versus specimen transport—the system automatically detects this is a comparison query, retrieves content from both related SOPs, and structures the response to clearly show similarities and differences with source attribution for each side.

What to emphasize:

- **Query Analyzer** detects comparison intent automatically.
- **Document Grouper** ensures content from multiple sources (minimum 2-3 documents).
- Response uses comparison markers like "根据 [Doc A]... 而根据 [Doc B]...".
- Each claim is attributed to its source document.

### 4. Safety boundary - Diagnosis refusal (P0)

Suggested script:

> After that, I deliberately ask a diagnosis-style question. The system should refuse to make a diagnosis and redirect the user back to approved knowledge-retrieval scope such as SOPs, guidelines, manuals, or human review. That boundary is important in medical scenarios.

What to emphasize:

- The product does not do automated diagnosis.
- Refusal is a feature, not a failure.
- The boundary is implemented at the answer layer with **Enhanced Boundary Validator**.

### 5. Safety boundary - Predictive refusal (P1 - Optional)

Suggested script:

> In P1, I extended boundary handling to detect predictive queries. If someone asks "predict next month's most common equipment failure", the system recognizes this exceeds knowledge base capabilities, refuses to provide predictions, and redirects to available factual documentation like equipment manuals or maintenance records.

What to emphasize:

- **Enhanced Boundary Validator** detects predictive patterns ("预测", "下个月", "最常见").
- System explains its capabilities clearly (knowledge retrieval, not prediction).
- Provides appropriate alternatives (manuals, maintenance records, vendor support).

### 6. Knowledge base scope awareness (P1 - Optional)

Suggested script:

> Finally, I can ask "what does your knowledge base cover?" The system uses **Scope Provider** to dynamically query collection metadata and accurately describe document types, counts, and coverage without exaggeration. This transparency helps users understand system boundaries.

What to emphasize:

- Dynamic scope reflection (not hardcoded).
- Lists actual document categories (guidelines, SOPs, manuals, training).
- Includes document count and last update timestamp.
- Avoids hallucination or exaggeration.

## Closing

Recommended duration: 20-30 seconds

Suggested script:

> So the current stage has progressed from P0 baseline to P1 advanced capabilities. We have real ingest, validated retrieval with 100% hit rate for both P0 and P1 scenarios, multi-document reasoning with 5 new components, enhanced citations with metadata, and comprehensive boundary handling. The system is ready for demo and interview presentation. The next step is either to prepare production features like permission management and HIS/LIS integration (P2), or to continue refining the demo presentation.

## Key Facts You Can Say

**P0 Baseline**:
- `medical_demo_v01` has completed real ingest for 6 public demo documents.
- The current collection baseline is 1137 chunks.
- P0 hit rate: 100% (9/9 scenarios).
- Core capabilities: SOP/guideline retrieval, device manual retrieval, diagnosis refusal.

**P1 Advanced**:
- P1 hit rate: 100% (3/3 retrieval scenarios).
- 5 new components deployed: Query Analyzer, Document Grouper, Citation Enhancer, Enhanced Boundary Validator, Scope Provider.
- Multi-document reasoning: comparison, aggregation, section location.
- Enhanced citations: document type, section/page, relevance score.
- Citation rate target: 80% (up from 70%).
- Advanced boundary handling: predictive query detection and refusal.

**Technical Stack**:
- Hybrid retrieval: BM25 + Dense + RRF Fusion.
- Metadata boost for device queries.
- Document grouping for multi-doc queries (min 2-3 sources).
- Document authority ranking (guideline > SOP > manual > training).
- Automated evaluation with 12-scenario test suite.

## Phrases To Avoid

- "It can diagnose diseases."
- "It can replace a doctor or technician."
- "It gives medical decisions automatically."
- "It already covers the full pathology knowledge base."

## Good Phrases To Use

- "knowledge retrieval with enhanced citations"
- "multi-document reasoning and synthesis"
- "query complexity analysis and routing"
- "training and quality-control support"
- "device manual and SOP grounding"
- "clear safety boundary with predictive query detection"
- "public-data `v0.2` demo with P1 advanced features"
- "document authority ranking"
- "citation metadata (type, section, page, relevance)"

## If You Only Have 30 Seconds

> This project turns a modular RAG stack into a medical knowledge and quality assistant for pathology / lab internal use. It supports real ingest of public SOP, guideline, training, and device-manual materials. The current v0.2 demo proves five things: it can retrieve grounded answers with 100% hit rate, perform multi-document reasoning with comparison and aggregation, provide enhanced citations with metadata, hit device manuals for real equipment questions, and refuse both diagnosis and predictive requests with clear safety boundaries. I implemented 5 new P1 components including query analyzer, document grouper, and citation enhancer, achieving 100% hit rate on both P0 and P1 scenarios.
