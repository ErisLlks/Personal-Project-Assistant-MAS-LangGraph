# MAS-ARPS Requirements Specification
## Multi-Agent System for Academic Research & Presentation Synthesis

---

# 1. Introduction

This document defines the functional and non-functional requirements for MAS-ARPS, a multi-agent system designed to perform structured academic research and generate university-level presentation slides.

The system enables users (e.g., professors or presenters) to input academic topics, retrieve relevant sources, generate structured summaries, iterate on research results, and produce citation-compliant presentation slides.

---

# 2. Functional Requirements

## FR-1: Topic Input

- The system must accept between 1 and 5 academic topics per session.
- Each topic must be processed independently.
- The system must generate a unique session ID per research session.
- Topics must be stored for traceability and logging.

---

## FR-2: Source Selection

The user must be able to select one or more research sources:

- Local folder (uploaded or predefined directory)
- Google Drive storage
- Web research
- Combination of the above

The system must:
- Clearly log which sources were selected.
- Process each source through a standardized ingestion pipeline.
- Prevent duplicate ingestion of the same document within a session.

---

## FR-3: Summary Output

The system must generate a structured academic summary containing:

- An overview section (150–250 words).
- Between 5 and 10 key points.
- Supporting citations for each key point.
- A confidence score indicating reliability of retrieved evidence.

Each key point must:
- Be supported by at least one retrieved source.
- Include source metadata (author, year, document name, page number if available).

---

## FR-4: Iterative Research Loop

The system must allow the user to:

- Expand a specific key point.
- Request additional research on the same topic.
- Finalize the summary and proceed to presentation generation.

If "Research More" is selected:
- The system must prioritize previously unused sources where possible.
- The system must log iteration number and action type.
- The system must prevent infinite iteration (configurable maximum attempts).

---

## FR-5: Presentation Output

Upon user approval, the system must generate a presentation containing:

- Between 10 and 20 slides.
- Speaker notes for every slide.
- At least one citation per conceptual slide.
- An automatically generated reference slide.
- Academic citation style selectable (default: APA 7th Edition).

The presentation must:
- Follow defined editorial guidelines.
- Respect slide bullet limits.
- Ensure citations match the reference list.

---

# 3. Non-Functional Requirements

## NFR-1: Accuracy

- No unsupported claims are permitted.
- Each major claim must cite at least one retrievable source.
- Generated citations must correspond to real, retrievable documents.
- Contradictory evidence should be acknowledged when present.

---

## NFR-2: Traceability

- Every key point must include source metadata.
- Each slide bullet must be traceable to retrieved document chunks.
- The system must maintain session logs including:
  - Selected sources
  - Retrieved documents
  - Iteration history
  - Generated outputs

---

## NFR-3: Performance

- Research summary generation must complete within 120 seconds under normal operating conditions.
- For MVP phase, up to 180 seconds is acceptable.
- Slide generation must complete within 60 seconds after summary approval.
- Retrieval queries must return results within 10 seconds.
- Iterative re-search actions must complete within 120 seconds.

Performance testing must be conducted using a corpus of at least 50 academic documents.

The system must remain responsive during long-running tasks by:
- Providing status updates (e.g., “Retrieving sources…”, “Generating summary…”).
- Preventing UI freezing during background processing.

---

## NFR-4: Security

- No API keys or credentials may be stored in source code.
- Secrets must be stored in environment variables or secure vault.
- Local files must be accessed in read-only mode.
- The system must validate external URLs before scraping.
- User-uploaded files must be sanitized before processing.

---

# 4. Constraints

- The system depends on availability of selected LLM provider.
- Web scraping must comply with applicable terms of service.
- Academic paywalled content must not be accessed without proper authorization.

---

# 5. Assumptions

- Input topics are academically meaningful.
- Source documents are machine-readable.
- Internet connection is available when web research is selected.
- Selected citation style is recognized and well-defined (e.g., APA 7th Edition).

---

# 6. Acceptance Criteria

The system will be considered successful when:

- A research summary is generated containing:
  - 5–10 supported key points.
  - Valid citations.
  - Traceable source metadata.
- A presentation of 10–20 slides is generated.
- Each slide follows editorial rules.
- All citations appear correctly in the reference slide.
- No unsupported claims are present.
- System logs provide full traceability of session actions.

---

# End of Requirements Specification