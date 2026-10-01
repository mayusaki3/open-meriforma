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
