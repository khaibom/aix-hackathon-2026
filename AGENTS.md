# AGENTS.md

## Required at the start of every session

Before analyzing, planning, answering questions, or modifying files, read all of the following files in full:

- `hackathon/challenge.md`: the hackathon challenge and questions.
- `hackathon/readme-requirements.md`: README writing requirements.
- `hackathon/scoring-criteria.md`: judging criteria.

These are the official source documents for the competition. When information conflicts, prefer these files and ask the user if the correct interpretation is unclear.

## Protect the hackathon directory

- Never modify any file under `hackathon/`.
- Do not create, delete, rename, or move files under `hackathon/`.
- If a task requires changing `hackathon/`, stop and state that the directory is read-only.

## Required skills

- Apply [i-have-adhd](https://github.com/ayghri/i-have-adhd) to every response: lead with the next action, keep output concise, number multi-step tasks, suppress tangents, cap lists at five items, and end with one concrete next step.
- Apply [ponytail](https://github.com/dietrichgebert/ponytail) to every coding task: inspect before editing, reuse existing code, prefer the smallest working solution, and never remove validation, security, data-loss handling, or accessibility safeguards.
- Follow the full instructions in each skill repository's `SKILL.md` when the skill is available locally.

## Working rules

- Read relevant files before changing files outside `hackathon/`.
- Keep changes small and do not touch unrelated changes.
- Follow `hackathon/readme-requirements.md` when writing or updating a README.
- Do not add dependencies or new structure unless they are necessary.
- Do not commit secrets, personal information, or local machine paths.

## Completion

- Validate changes with checks appropriate for the files changed.
- Report the files changed and the checks that were run.

