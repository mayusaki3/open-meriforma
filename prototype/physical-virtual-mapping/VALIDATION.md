# Physical / Virtual Unit Mapping Validation

This document records prototype findings. It does not freeze the final standard schema or terminology.

## Validated architecture candidates

- Physical Unit and Virtual Unit have independent identities and lifecycles.
- Twin Mapping is a relationship, not a special Unit type.
- A Physical Unit or Virtual Unit may exist without a Twin Mapping.
- Mapping cardinality is not restricted to 1:1; 1:N and N:1 relationships are representable.
- A Mapping may cover only a partial scope of either endpoint.
- Mapping existence, endpoint availability, Mapping usability, command candidacy, and active command authority are separate concepts.
- Physical-to-Virtual observation may be shared by multiple mappings without creating command-authority conflict.
- Multiple Virtual-to-Physical command candidates may be declared, but overlapping active command authority must be exclusive per Physical subject.
- Command authority can be handed off for only the overlapping scope while source-only authority remains with the source mapping.
- Mapping insertion order has no semantic meaning for authority conflict.
- Endpoint loss makes a configured Mapping unusable without deleting it.
- Unknown endpoint state is not silently treated as usable.
- If an endpoint is lost while command authority is active, the authority record is retained and reported as invalid rather than silently released.
- Endpoint recovery clears the Mapping usability failure but does not itself transfer, recreate, or release command authority.
- Runtime/Safety policy decides STOP, release, transition, or explicit resume behavior.

## Relationship to Body Graph validation

The Mapping prototype follows the same separation already validated by the Body Graph prototype:

- topology/reachability state is separate from ownership;
- loss of reachability is detected without silently mutating ownership;
- recovery of reachability does not imply automatic execution restart;
- runtime policy is kept above the graph/relation representation.

## Prototype-only mechanisms

The following are implementation devices for validation and are not standardized:

- JSON field names such as `scope`, `channels`, `authority`, and `direction`;
- string reason formats;
- boolean/None endpoint availability state;
- `command` and `observe` authority labels;
- Python dictionary storage;
- current Runtime API names;
- the Foot/Leg example topology and channel names.

## Not yet validated

- synchronization timestamps, freshness, latency, and ordering;
- state divergence and reconciliation between Physical and Virtual endpoints;
- fidelity metadata and model accuracy;
- distributed authority arbitration;
- safe command transition/blending during handoff;
- restart/resume policy after communication recovery;
- interaction between Twin Mapping and Safety constraints;
- mapping Definition/Instance persistence and version compatibility.

## Current conclusion

A Twin should be modeled as a relationship between independently existing Physical and Virtual Units rather than as a Unit category. The relationship may be partial and non-1:1. Runtime synchronization usability and command authority are dynamic states layered on top of the configured Mapping.
