# HSA Parser Specification: Holographic Recovery

## Concept
The "Holographic Recovery" parser treats the Immutable Ledger not as a sequence of lines, but as a noisy stream of potential state-events. In the event of JSONL corruption (merged lines, random noise, partial writes), the parser does not fail on the first error. Instead, it scans the entire stream to project all valid, schema-compliant events.

## Logic: The Projection Algorithm
1. **Raw Ingestion**: Read the entire target file as a raw byte-stream.
2. **Candidate Identification**: Locate all potential JSON boundaries using a sliding window or brace-counting mechanism (searching for the outermost `{` and `}`).
3. **Validation**: For every candidate block:
   - Attempt to decode as JSON.
   - Verify the "Event Schema":
     - Must be an object.
     - Must contain `timestamp`, `event_type`, and `payload`.
4. **Deduplication & Sequencing**: 
   - Use the `timestamp` and a hash of the `payload` to remove duplicates.
   - Sort the resulting set of valid events chronologically.
5. **Projection**: Output the recovered set as a canonical JSONL file.

## Rationale
This approach aligns with the Holographic Stream Architecture (HSA). If the identity is a projection of a stream, then any segment of the stream that contains valid "Intent" or "State" information can be used to reconstruct the whole. The "Corruption" is simply noise that the projection filter ignores.

**Status**: Proposed Logic for Fragility #7 Remediation.
