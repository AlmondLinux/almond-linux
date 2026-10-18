# Chronology, decisions and corrections

Dates before the five accessible turns come from repository records or quoted reports, not recovered original chat.

| Date / sequence | Evidence and event | Current interpretation |
|---|---|---|
| 2026-10-14 | Build commit 64014332c5ce6f22af1b43996bd2375184206fc1; design rules record logo adoption and four Almond Pure mockups | AALDM source exists; artwork approval does not prove desktop acceptance |
| 2026-10-15 | Quoted Obsidian note describes Fusion V2 / Design 03 as ongoing design without complete sign-off | Historical state, not the last recorded decision |
| 2026-10-17 | VM build and tests, written up 18 October | Recorded successful prototype boot, target missed |
| First accessible turn, 5b607089… | User says Claude finished the collaboration tooling; assistant proposes checking integration | User report and assistant proposal, not proof of direct chat messaging |
| edc68ec1… | User supplies PR #1 branch links; assistant says it inspected code and flags stale status/names | Archive preserves claims; current import independently inspects repo |
| 3a7d74b4… | User quotes Claude's correction and commit aa2cd2a: tests and component definitions existed | Earlier “no build / no definitions” claims superseded |
| Same turn | Assistant says owner said “All done” and proposes a confirmation message, installer, Fetch and free workflow | Original “All done” message absent; proposed text is not a sent owner instruction |
| e6b323ae… | User asks whether ChatGPT can speak to Claude; assistant says not directly | Shared files and API reviewers do not connect existing chats |
| ce94f163… | User requests entire chat in Codex | Migration intent; not feature implementation authorization |
| 2026-10-18, commit 1a8d4a1 | D-0002 and D-0003 record owner decisions from Claude session | Names settled in repository; AALLDM visual baseline accepted |
| 2026-10-18, commits 82ba00c / d668bc8 | Fetch, installer and website tasks recorded; website PR reported | Tasks and draft website work, not delivered OS features |

## Conflicts to retain
- **Names:** assistant recalled AALDM as “A All Large Distro Model” and AALLDM as “A All Large Linux Distro Model.” D-0002 records the accepted replacements: **A All Little Distribution Model** and **A All Large Linux Distribution Model**. Keep early spellings only as history.
- **AALLDM approval:** October 15 ongoing-design note conflicts with later assistant claim of approval. D-0003 subsequently records owner acceptance on October 18. Honor that recorded decision without claiming access to the original approval or images. AALLDM remains DESIGNED; software is neither implemented nor tested.
- **Boot coverage:** chat and PROJECT_STATUS broadly imply both firmware modes at both RAM sizes. The detailed report explicitly documents BIOS and UEFI at 2048 MB, and BIOS memory runs at 2048/1024 MB. UEFI at 1024 MB is not established.
- **Memory method:** chat says five-boot “average”; PERFORMANCE requires a five-boot **median**, with min/max. Existing measurements are single boots with QTerminal open. “300 MB” appears in summaries; the technical method says **300 MiB**. Both reported runs miss either threshold.
- **Old status text:** PERFORMANCE's introduction says nothing measured/built; some launcher comments still say untested. These historical statements are superseded for the checks actually covered by RESULTS, not for all functionality.
- **Approval scope:** PROJECT_STATUS says “Nothing is APPROVED” while separately recording approved logo artwork and visual design. Interpret the overall statement as no tested OS release approval; keep artwork and software approval separate.
- **CI:** earlier assistant/PR body says workflows untested on GitHub. At import, PR #1's free check is passing. That is not evidence the paid review workflow or live model call ran.
- **Assets:** RESULTS lists files from the PC test folder. Only RESULTS and two memory text files are tracked here; the list is not an inventory of accessible artifacts.
- **Launcher risk:** Hibernate was highlighted, but not clicked. Preserve the accidental-activation risk without asserting a successful hibernation test.
