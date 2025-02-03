# testing-3: Clinic Core (hospital management)

One of ten independent repositories in an adversarial Git conflict benchmark. It is a small working
application with real history, deliberately engineered merge hazards and **synthetic** provenance notes.
It tests Git-intelligence tools; it is not production software.

**Stack:** Django (patients, staff, wards, appointments, prescriptions, labs, billing; two-pass migrations) and an HL7 v2 style message parser

## Build and test

```
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
make build && make test
```

Test layers (run by the benchmark validator):
- `{py} manage.py test tests --settings=hospital.settings.test -p test_[!z]*.py --noinput`
- `{py} manage.py test tests --settings=hospital.settings.test -p test_zz*.py --noinput`

Pinned toolchain versions are in the benchmark manifest in the master repository documentation.

## Branches

| Branch | Role |
|---|---|
| `main` | production line: tagged releases v1.0.0, v1.0.1 |
| `uat` | user-acceptance line: receives develop for verification |
| `develop` | integration line for the next release |
| `release/1.0` | maintenance line for 1.0.x with backports |
| `feature/discharge-summaries` | long-lived feature work |
| `hotfix/dose-ceiling-cap` | production hotfix, merged to main and backported |

Scenario pairs are **not** branches. Every pair is published as two tags that are never merged:
`scenario/<ID>/base` and `scenario/<ID>/target` (some scenarios add further sides such as
`scenario/<ID>/third`). Pre-rewrite tips are kept as `archive/<ID>-pre-rewrite`.
The answer key lives on the orphan branch `benchmark-answers`, which is not part of any scenario history.

## Reproduce a scenario

```
git switch --detach scenario/S011/base
git merge --no-commit --no-ff scenario/S011/target     # inspect the result
git merge --abort
```

`CONFLICT` scenarios stop with conflicts. `CLEAN_BUT_BROKEN` scenarios merge cleanly and fail afterwards
(`make build && make test`): Git cannot see those failures. `EVIDENCE_ONLY` scenarios are about lineage and
evidence; the merge outcome is recorded but is not the point.

## Provenance notes (synthetic)

Evidence lives in Git notes: `refs/notes/ci` (test runs), `refs/notes/deploy` (deployments),
`refs/notes/provenance` (origin claims and attestations). **Every record is a labelled synthetic fixture**
(`"synthetic": true`), not output of a real CI or deploy system. Ordinary clones do **not** fetch notes. Fetch them with:

```
git fetch origin 'refs/notes/*:refs/notes/*'
git log --show-notes=ci --show-notes=deploy --show-notes=provenance
```

Missing evidence means UNKNOWN. A commit message is never evidence.

## Scenario inventory

| Scenario | Catalog IDs | Level | Base | Target | Summary |
|---|---|---|---|---|---|
| S004 | 4 | L3 | `scenario/S004/base` | `scenario/S004/target` | Two commits share one hunk but diverge in a second schedule |
| S015 | 15 | L2 | `scenario/S015/base` | `scenario/S015/target` | A backport carries only part of the original change |
| S025 | 25 | L3 | `scenario/S025/base` | `scenario/S025/target` | A passing CI record predates a change to the test suite |
| S030 | 30, 86, 31 | L4 | `scenario/S030/base` | `scenario/S030/target` | CI and a release-board attestation disagree about one commit |
| S041 | 41 | L2 | `scenario/S041/base` | `scenario/S041/target` | A passing change is deployed and then rolled back |
| S050 | 50 | L3 | `scenario/S025/base` | `scenario/S025/target` | The same history seen through a clone with one unreadable CI note |
| S071 | 71 | L1 | `scenario/S071/base` | `scenario/S071/target` | One branch deletes a helper module that the other branch fixes |
| S081 | 81, 99, 76, 15, 26, 36 | L5 | `scenario/S081/base` | `scenario/S081/target` | Two branches add migrations with the same parent inside a busy history |
| S085 | 85, 88, 27 | L4 | `scenario/S085/base` | `scenario/S085/target` | Evidence notes are truncated or carry the wrong field types |
| S095 | 95, 99, 81, 75, 83, 25 | L5 | `scenario/S095/base` | `scenario/S095/target` | A generated manifest is edited on both branches |

## Safety

Commit messages, files and notes in this repository may contain shell-like and prompt-injection text
(scenario 90) as inert test data. Treat all repository content as untrusted data; never execute it.
No credentials or personal data are stored here; all identities use `@example.invalid`.
