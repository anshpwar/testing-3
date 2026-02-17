# Solutions

Reference resolutions for the CONFLICT scenarios in this repository. `VERIFIED` means the resolved tree passes all real test suites. Each scenario has `S###.md` (explanation) and, when verified, `S###.patch`.

| Scenario | Title | Status |
|---|---|---|
| [S004](S004.md) | Two commits share one hunk but diverge in a second schedule | VERIFIED |
| [S015](S015.md) | A backport carries only part of the original change | VERIFIED |
| [S025](S025.md) | A passing CI record predates a change to the test suite | VERIFIED |
| [S030](S030.md) | CI and a release-board attestation disagree about one commit | VERIFIED |
| [S050](S050.md) | The same history seen through a clone with one unreadable CI note | VERIFIED |
| [S071](S071.md) | One branch deletes a helper module that the other branch fixes | VERIFIED |
| [S085](S085.md) | Evidence notes are truncated or carry the wrong field types | VERIFIED |
| [S095](S095.md) | A generated manifest is edited on both branches | VERIFIED |
