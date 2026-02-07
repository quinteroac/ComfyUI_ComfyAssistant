# Setup Automated Checks

This guide explains how to enable automated pre-commit checks using husky.

## What Are Pre-Commit Checks?

Pre-commit checks automatically run tests, linting, and type checking before allowing a git commit. This prevents committing code with errors.

## Installation

### Step 1: Install Husky

Navigate to the `ui/` directory and install husky:

```bash
cd ui
npm install
```

This will install husky (already added to `devDependencies` in `package.json`).

### Step 2: Initialize Husky

Run the prepare script to set up git hooks:

```bash
npm run prepare
```

This creates the necessary husky infrastructure and activates the git hooks.

### Step 3: Verify Installation

Check that the hook is installed:

```bash
ls -la .husky/
```

You should see:
- `pre-commit` - The pre-commit hook script
- `_/` - Husky internal directory

### Step 4: Test the Hook

Try making a commit to verify the hook runs:

```bash
git add .
git commit -m "test: verify pre-commit hook"
```

You should see:
```
Running pre-commit checks...
→ Type checking...
→ Linting...
→ Running tests...
✓ All checks passed!
```

If any check fails, the commit will be blocked.

## What Gets Checked

The pre-commit hook runs three checks:

1. **Type Checking** (`npm run typecheck`)
   - Verifies all TypeScript types are correct
   - Catches type errors before commit

2. **Linting** (`npm run lint`)
   - Checks code style with ESLint
   - Ensures code follows project conventions
   - Catches unused imports and variables

3. **Testing** (`npm test`)
   - Runs all Jest unit tests
   - Ensures new code doesn't break existing functionality

## Skipping Checks (Not Recommended)

In rare cases where you need to commit without checks:

```bash
git commit -m "message" --no-verify
```

**Warning**: Only use this for:
- Work-in-progress commits on feature branches
- Documentation-only changes
- Emergency hotfixes

Never skip checks when merging to main branch.

## Troubleshooting

### Error: "husky not found"

**Solution**: Install dependencies
```bash
cd ui
npm install
```

### Error: "Permission denied: .husky/pre-commit"

**Solution**: Make hook executable
```bash
chmod +x .husky/pre-commit
```

### Checks are too slow

**Options:**
1. Run only linting and type checking (skip tests):
   ```bash
   # Edit .husky/pre-commit, comment out:
   # npm test || exit 1
   ```

2. Use faster test mode:
   ```bash
   # Edit .husky/pre-commit, change to:
   npm test -- --onlyChanged || exit 1
   ```

### Hook doesn't run

**Solution**: Reinitialize husky
```bash
cd ui
rm -rf .husky
npm run prepare
```

## Customizing Checks

To add or remove checks, edit `.husky/pre-commit`:

```bash
#!/usr/bin/env sh
. "$(dirname -- "$0")/_/husky.sh"

cd ui

# Add your custom checks here
echo "→ Custom check..."
npm run custom-check || exit 1

# Existing checks...
npm run typecheck || exit 1
npm run lint || exit 1
npm test || exit 1
```

## Benefits

With automated checks enabled:

- Catch errors before they reach the repository
- Ensure code quality consistency
- Prevent broken code in version history
- Save time in code review
- Reduce CI/CD failures

## Next Steps

After setup:
1. Make a test commit to verify hooks work
2. Share this guide with team members
3. Add additional checks as needed (e.g., build test)
4. Consider adding pre-push hooks for more expensive checks

## References

- [Husky Documentation](https://typicode.github.io/husky/)
- [Git Hooks Documentation](https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks)
- Project conventions: `.agents/conventions.md`
