# Phase 07 — Chunking, versioning, and supersession

**Feature branch:** `codex/feature-07-evidence-chunking`  
**Depends on:** Phase 06  
**Traceability:** `specs/02-data-model.md`, `specs/05-retrieval.md`; FR3, NFR2

## Goal

Turn evidence documents into stable, citable chunks while preserving historical versions.

## Implementation

- Add deterministic chunking with stable ordering and configurable overlap.
- Denormalize document/source/version/validity metadata onto each chunk.
- Mark earlier versions superseded instead of deleting them.
- Generate opaque stable IDs and store embedding references separately from source text.
- Make active/superseded selection tenant-scoped.

## Unit tests

- Deterministic chunk boundaries and IDs for repeated input.
- Required metadata on every chunk.
- New-version upload supersedes prior chunks while old citation targets still resolve.
- Empty, oversized, and malformed documents fail predictably.
- Cross-tenant version updates cannot supersede another tenant's chunks.

## Done when

All indexed chunks satisfy FR3, active retrieval can exclude superseded versions, and historical citations remain reconstructable.
