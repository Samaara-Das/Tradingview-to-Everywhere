# Ship It — Commit, PR, Review, Merge

Automated pipeline to ship the current branch to main. Runs sequentially:

## Step 1: Commit & Push
Use the `/commit-push` skill to:
1. Git add the unstaged changes
2. Remove unnecessary debug logs and temporary files
3. Understand the changes and make a commit with a clear message
4. Push changes to the remote branch

## Step 2: Create a Pull Request
1. Determine the current branch name with `git branch --show-current`
2. If the branch is `main` or `master`, STOP and report an error — never PR from main to main
3. Create a PR targeting `main` using `gh pr create`:
   - Title: Short, descriptive (under 70 chars)
   - Body: Use this format:
     ```
     ## Summary
     <1-3 bullet points describing what changed and why>

     ## Test plan
     - [ ] Pre-commit hooks pass (ruff lint + format, pyright)
     - [ ] Config validation passes (`python combo_main.py --validate`)
     - [ ] TTE.exe rebuilt if GUI changed

     Generated with [Claude Code](https://claude.com/claude-code)
     ```
4. Capture the PR URL and number from the output

## Step 3: Code Review
1. Use the `/code-review:code-review` skill to review the PR
2. The review will analyze the diff, check for issues, and post findings
3. If the review finds **critical issues** (security vulnerabilities, broken functionality, type errors):
   - Report the issues to the user
   - STOP — do not merge
4. If the review finds only **minor suggestions** or no issues, proceed to merge

## Step 4: Merge to Main
1. Squash merge the PR: `gh pr merge <PR_NUMBER> --squash --delete-branch`
2. Confirm the merge succeeded with `gh pr view <PR_NUMBER> --json state`
3. Report the final status: merged PR URL, commit hash on main

## Step 5: Report
Provide a final summary:
- Commit message
- PR URL and number
- Review result (clean / minor suggestions noted)
- Merge status (merged / blocked)

## Error Handling
- If any step fails, report the error clearly and stop
- Never force-push or use destructive git operations
- If the PR has merge conflicts, report them and stop — do not auto-resolve
