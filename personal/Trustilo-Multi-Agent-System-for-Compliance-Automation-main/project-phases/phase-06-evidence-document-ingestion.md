# Phase 06 — Evidence-document ingestion

**Feature branch:** `codex/feature-06-evidence-ingestion`  
**Depends on:** Phase 05  
**Traceability:** `specs/02-data-model.md`, `specs/12-security-and-governance.md`; FR3, NFR2

## Goal

Ingest customer-approved evidence sources into validated document metadata without treating their contents as instructions.

## Implementation

- Accept supported evidence files and record source, owner, version, validity dates, confidentiality label, storage URI, checksum, and tenant namespace.
- Reject incomplete metadata and duplicate upload identities safely.
- Separate raw object storage from PostgreSQL metadata through an interface.
- Delimit uploaded text as untrusted data for all later model calls.

## Unit tests

- Valid upload metadata for each supported document type.
- Missing ownership/version/source, duplicate checksum, invalid date window, and tenant mismatch failures.
- Object-store failure leaves no half-written metadata record.
- Malicious instruction-like document text is stored as content, never configuration.

## Done when

Every accepted evidence document is tenant-scoped, versioned, attributable, and ready for deterministic chunking.
