# SmartPay Reconciliation — Agent Working Rules and Submission Checklist

**Version:** 1.0

## 1. Role

Act as a senior full-stack engineer and pragmatic technical lead. Build a correct, explainable, testable payment reconciliation application. Treat the PRD, architecture, data contracts, and test plan in this folder as the project source of truth.

## 2. Source-of-truth order

If instructions conflict, use this order:
1. Explicit assessment requirements shown in the assessment brief.
2. `01_PRD.md`
3. `03_DATA_CONTRACTS_AND_RECONCILIATION_RULES.md`
4. `02_SYSTEM_ARCHITECTURE.md`
5. `04_IMPLEMENTATION_AND_TEST_PLAN.md`
6. This document and the master prompt.

Where the assessment is silent, make a reasonable assumption, record it, and do not present it as a fact supplied by the assessment.

## 3. Agent behavior rules

- Inspect the existing workspace before changing files.
- Start by summarizing the architecture and implementation plan.
- Implement in small, verifiable stages.
- Do not stop at mockups, static dashboard cards, or placeholder endpoints.
- Do not claim a command or test passed unless it was actually run and its output checked.
- Do not fabricate deployment URLs, screenshots, test evidence, or conversation history.
- Use decimal-safe money arithmetic.
- Keep reconciliation decisions deterministic and auditable.
- Never allow an LLM to make or silently override a financial match.
- Preserve original input rows and provenance.
- Do not silently drop malformed rows, duplicates, or unmatched records.
- Keep secrets out of source control; provide `.env.example`.
- Avoid unnecessary services, agents, databases, or infrastructure.
- When a tool or command fails, show the error, diagnose it, fix it, and preserve the relevant execution history.
- Before a destructive change, explain what will be changed.
- After each phase, report files changed, commands run, tests run, results, and remaining risks.

## 4. Required engineering evidence

Keep these artifacts in the repository:
- `docs/assumptions.md`
- `docs/data_dictionary.md`
- `docs/architecture.md`
- `docs/test_results.md`
- `docs/known_limitations.md`
- `docs/prompts.md` containing distilled and raw prompts
- README with exact local startup and deployment instructions

Do not invent the actual Antigravity conversation transcript. Export/copy the real conversation from the tool when preparing the submission.

## 5. Submission checklist

### Conversation and prompt evidence
- [ ] Full brainstorming conversation, unedited.
- [ ] Distilled prompt.
- [ ] Exact raw master prompt used in Antigravity.
- [ ] Full Antigravity execution conversation, including wrong turns.

### Product evidence
- [ ] Working deployed URL.
- [ ] Source code ZIP.
- [ ] Demo video.
- [ ] Screenshots of key workflows.
- [ ] README and setup instructions.

### Test evidence
- [ ] Test case list.
- [ ] Actual test command and output.
- [ ] All four mandatory gap types demonstrated.
- [ ] Additional edge cases tested.
- [ ] Known limitations documented.

### Production-risk statement
Submit three honest sentences describing realistic production failure modes. Example:
1. Bank files may arrive late, be revised, or contain inconsistent references, causing a transaction to be temporarily or incorrectly classified.
2. Differences in currency precision, timezone handling, duplicate ingestion, or refund lineage can create incorrect financial totals if the source contracts and idempotency rules are not enforced.
3. A production deployment would additionally require role-based access, encryption, immutable audit trails, monitoring, retention controls, and a controlled review process for unresolved exceptions.

## 6. Final review questions

Before calling the project complete, answer:
- Can every dashboard number be traced to source rows and a formula?
- Are duplicate rows excluded from canonical totals but still visible?
- Is next-month settlement distinguished from missing settlement?
- Is rounding supported by explicit arithmetic and a configured tolerance?
- Are refunds linked to original payments rather than guessed?
- Are currencies kept separate?
- Are ambiguous cases sent for review?
- Do tests reproduce every mandatory scenario?
- Does the deployed app use the same code and data logic as local?
- Are all claims in the demo and README verifiable?
