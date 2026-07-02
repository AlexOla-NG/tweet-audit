# Tweet-Audit Project Rules

## Git Workflow

**Always follow this workflow for every feature:**

1. **Before starting any feature**, create a new branch from `main`:
   ```
   git checkout main
   git pull origin main
   git checkout -b feat/<feature-name>
   ```

2. **Commit changes** on the feature branch as work progresses with clear, descriptive commit messages.

3. **After completing a feature**, push the branch to GitHub:
   ```
   git push origin feat/<feature-name>
   ```

4. **Open a Pull Request** to `main` on GitHub and provide the PR link to the user.

5. **After the PR is merged** (user confirms), clean up:
   ```
   git checkout main
   git pull origin main
   git branch -d feat/<feature-name>
   git push origin --delete feat/<feature-name>
   ```

6. **Always update `README.md`, `TRADEOFFS.md` and `GEMINI.md`** to reflect any codebase changes made as part of a feature.
