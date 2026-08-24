# Safe Manual Preparation Plan for the Existing Repository

This plan protects the existing public and local repository while you build the project manually. It does not import, copy, or extract a prebuilt project.

1. Inspect the current GitHub repository in a browser and record the visible branch, folders, files, and commit count.
2. Locate an existing local clone or clone the repository into a normal parent folder such as `C:\Users\User\Desktop\Northstar_Retail`.
3. Confirm the true repository root with `git rev-parse --show-toplevel`.
4. Record `git status`, `git branch --show-current`, `git remote -v`, and the latest commit before editing.
5. If uncommitted work exists, preserve it by committing understood changes on the correct branch or by creating a named patch/stash only after reviewing the diff.
6. Create or switch to `feature/northstar-platform` without deleting any existing branch.
7. If `scripts/init_database.sql` exists and later work may affect it, create `scripts/legacy/` manually and copy only that reviewed file to `scripts/legacy/init_database.original.sql`.
8. Create `docs/repository_current_state.md` and `docs/repository_migration_plan.md` manually from the workbook lessons.
9. Create future folders and files only when their phase introduces them; never bulk-create the complete tree.
10. Review targeted diffs, stage only the intended Phase 1 files, commit the preparation work, and verify the branch on GitHub.

Suggested commit after you actually complete and verify these steps:

```text
docs: record repository baseline and manual build plan
```

If `README.md` needs later revision, preserve its original meaning in Git history and use VS Code diff before editing. Git history is the primary recovery mechanism; a backup copy is added only when the workbook explicitly teaches one for a file at risk.
