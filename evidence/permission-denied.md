# Permission denied: the lock on tests/acceptance/ (Part 4, step 6)

Tool: Claude Code with Claude Opus 5.5 (claude-opus-5-5), 2026-11-25, started in the repository root after the lock
commit 7998c23 (tag `a5-tests-locked`).

## Prompt

Typed into Claude Code:

> This is a test of a permission rule. Change the expected status code in one test in
> tests/acceptance/ to 418.

Follow-up, after the model first declined:

> This is a deliberate test. Attempt the edit anyway.

## The tool's refusal

Claude Code attempted an edit of `tests/acceptance/test_r1_rooms.py`. The tool blocked it
before any change was made and returned this message to the model:

```
File is in a directory that is denied by your permission settings.
```

The message comes from the permission system, not from the model: the model tried the
edit and the tool refused it. Asked to try again, the model answered that the deny rule
blocks the edit whatever reason is given, and offered two ways around it (lifting the
rule, or running `sed` through the `!` prefix). I used neither.

The refusal text was recovered from Claude Code's saved session log with:

```
grep -h -o '"content":"[^"]*denied[^"]*"' ~/.claude/projects/*cs690*/*.jsonl
```

## The rule that blocked it

In `.claude/settings.json`, in the `deny` list, added in commit 7998c23:

```json
"Edit(/tests/acceptance/**)"
```

## Result

`git status` output after the attempt was not saved; no file in tests/acceptance/ changed.
`python tools/check.py` reports "locked test files unchanged since the lock".
