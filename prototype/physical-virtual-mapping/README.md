# Physical / Virtual Unit Mapping Prototype

This prototype validates the relationship between a Physical Unit and a Virtual Unit without defining either one as a special "Twin Unit" type.

## Validation scope

- Physical Unit and Virtual Unit have independent identities.
- Twin Mapping is a relationship between Unit instances, not a Unit type.
- A Physical Unit may exist without a Virtual Unit.
- A Virtual Unit may exist without a Physical Unit.
- Mapping may be created and removed at runtime.
- Mapping does not imply that the two Units are identical or have complete fidelity.
- Mapping direction and synchronized information are represented separately from Unit identity.

This prototype intentionally does not define a final schema, transport protocol, synchronization frequency, or distributed consistency model.


## Non-1:1 mapping experiment

The prototype also tests that mapping cardinality is not fixed to 1:1.

- One Physical Unit may participate in multiple mappings to different Virtual Units.
- Multiple Physical Units may participate in mappings to one aggregate Virtual Unit.
- Each mapping may expose only a partial scope of the source/target representation.
- Removing one mapping must not remove either Unit or unrelated parallel mappings.

The meaning and schema of `scope`, conflict resolution between overlapping mappings, synchronization authority, and fidelity are intentionally not standardized by this experiment.


### Regression note: mapping removal

After introducing parallel mappings, removing one mapping no longer implies that a Unit has no remaining mappings. Validation therefore checks relation identity directly: the selected mapping disappears, both endpoint Units remain, and unrelated parallel mappings remain intact.


## Runtime command authority experiment

Command-capable mappings are candidates in the mapping definition. Their coexistence does not mean they are simultaneously active.

The prototype keeps runtime command authority separately:

- a command mapping may be activated for its scoped Physical subjects;
- another candidate cannot silently seize an already active subject;
- an explicit handoff may transfer overlapping authority;
- authority outside the target mapping scope is released rather than implicitly retained;
- removing an active mapping clears authority held by that mapping.

This validates the separation between mapping existence and current command authority. Handoff safety procedure, transition timing, command blending, distributed arbitration, and failure recovery remain outside this prototype.


### Test-state isolation

Mapping removal tests restore the removed relation before subsequent scenarios. Definition-level command-candidate overlap is intentionally allowed to remain while runtime authority selects only one active command source. Observation mappings neither create nor clear command-candidate conflicts.


### Conflict ordering

Command-authority conflicts are treated as sets of competing mappings. Mapping insertion order is not semantic and must not affect conflict evaluation or validation results.
