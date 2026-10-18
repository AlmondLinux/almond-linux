# Sources and coverage

## Import boundary
The requested source is [Build Almond Linux](chatgpt-conversation://6acf427f-f6c4-83ed-9c5d-fc4d5288d163). The reader returned only five recent turns even with a ten-turn limit; it supplied no cursor for older turns and no attachments. A second read with a 20,000-character per-item limit recovered text cut off in the initial preview. The final returned messages have no truncation flags. This does not establish that the original chat contained only five turns.

The [raw reader response](sources/conversation-reader.json) and [readable archive](sources/accessible-conversation.md) preserve exactly the accessible subset. The cached preview overlaps these turns; it is not additional historical coverage. We did not read the Obsidian vault, local Downloads, original Claude session, omitted ChatGPT messages, or final design images.

## Repository snapshot
Inspected repository: [AlmondLinux/almond-linux](https://github.com/AlmondLinux/almond-linux).
Import baseline: PR #1 branch `ai-bridge/phase-1`, commit `d668bc8e27b88196e703162cfa894525fc842a76`.
PR #1 was OPEN against main on 2026-10-18. This import is a separate, stacked PR against that branch; it does not merge or modify PR #1.

| Source | What it supports | Limits |
|---|---|---|
| Accessible conversation | Later status debate, proposed handoff, request to transfer chat | Five turns only; assistant assertions are not direct owner approval |
| [D-0002](../../ai-bridge/decisions/D-0002-edition-names.md) | Final edition names, owner acceptance recorded 2026-10-18 | Original Claude exchange not inspected |
| [D-0003](../../ai-bridge/decisions/D-0003-aalldm-visual-design-approved.md) | AALLDM visual acceptance recorded 2026-10-18 | Final mockups absent |
| [Test report](../../tests/results/2026-10-17-vm/RESULTS.md) | Build, boot matrix, bugs, hardware, limitations | Report inspected; execution not repeated |
| [1 GB raw memory](../../tests/results/2026-10-17-vm/memory-1gb.txt), [2 GB raw memory](../../tests/results/2026-10-17-vm/memory-2gb.txt) | Single-run memory evidence | No five-boot series |
| [AALDM plan](../AALDM-PLAN.md), [architecture](../ARCHITECTURE.md), [roadmap](../ROADMAP.md) | Technical design and milestones | Older blanket “not built” statements can be stale |
| [Design rules](../DESIGN_RULES.md), [status](../PROJECT_STATUS.md) | Current documented constraints and conceptual definitions | Broad summaries can overstate test coverage |
| [Tasks](../../ai-bridge/tasks/) and [decisions](../../ai-bridge/decisions/) | Open work and recorded decisions | A ready task is not implementation |
| Source tree at baseline | Existing build, launcher and theme files | No independent runtime validation in this import |

## Completing the archive
User-provided full transcript export is required for a verbatim whole-chat archive. Include original message order, timestamps/IDs if available, and exported attachments or original downloadable images. The request was made in the importing Codex chat. No export was supplied during initial import.

When provided: preserve the original file, record its SHA256 and provenance, reconcile overlapping messages by ID/text, retain corrections in chronological order, and flag any remaining gaps. Add images with original names and message associations; distinguish alternatives from final approved versions. Do not silently replace the partial source or reconstruct missing dialogue. Review the supplied export for unrelated private content before committing it.
