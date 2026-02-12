# Contributing Guidelines

Development guidelines and code standards for TTE contributors.

## Table of Contents

1. [Code Style Guidelines](#code-style-guidelines)
2. [Logging Requirements](#logging-requirements)
3. [Git Workflow](#git-workflow)
4. [Pull Request Process](#pull-request-process)
5. [Testing Requirements](#testing-requirements)
6. [Documentation Updates](#documentation-updates)

---

## Code Style Guidelines

### General Principles

1. **Follow existing patterns** - Match the style of surrounding code
2. **Keep functions focused** - Single responsibility principle
3. **Prefer clarity over cleverness** - Readable code is maintainable code
4. **Avoid over-engineering** - Solve the current problem, not hypothetical future ones

### Python Conventions

```python
# Use snake_case for functions and variables
def get_next_symbol_batch(size: int = 20):
    batch_response = api.fetch_batch(size)
    return batch_response

# Use PascalCase for classes
class TieredOrchestrator:
    pass

# Use UPPER_SNAKE_CASE for constants
NWE_BATCH_SIZE = 20
CHART_TIMEFRAME = "5 minutes"
```

### Naming Guidelines

| Type | Convention | Example |
|------|------------|---------|
| Variables | snake_case | `symbol_list`, `batch_count` |
| Functions | snake_case, verb prefix | `get_symbols()`, `create_alert()` |
| Classes | PascalCase | `Browser`, `TieredOrchestrator` |
| Constants | UPPER_SNAKE_CASE | `MAX_RETRIES`, `API_TIMEOUT` |
| Files | snake_case | `api_client.py`, `handle_alerts.py` |

### Function Guidelines

```python
# GOOD: Clear name, focused purpose, proper typing
def create_webhook_alert(indicator_shorttitle: str, webhook_url: str) -> bool:
    """Creates a TradingView alert with webhook notification.

    Args:
        indicator_shorttitle: The short title of the indicator
        webhook_url: The URL that TradingView will POST to

    Returns:
        True if alert created successfully, False otherwise
    """
    # Implementation
    pass

# BAD: Vague name, no typing, unclear purpose
def process(data):
    # Does validation, calculation, and side effects
    pass
```

### Error Handling

```python
# GOOD: Specific exception handling with logging
try:
    indicator = self.get_indicator(shorttitle)
    indicator.click()
except StaleElementReferenceException:
    logger.warning(f"Stale element for {shorttitle}, retrying...")
    indicator = self._get_fresh_indicator(shorttitle)
except TimeoutException:
    logger.error(f"Timeout waiting for {shorttitle}")
    return False

# BAD: Silent failure
try:
    indicator = self.get_indicator(shorttitle)
except:
    pass  # Silent failure - hard to debug
```

---

## Logging Requirements

**CRITICAL**: Every new function or significant code block MUST include debug logging.

### Why Logging is Essential

- Browser automation issues are difficult to debug without logs
- Logs help identify where operations fail
- Timing issues require visibility into execution flow
- Production debugging relies entirely on log output

### Logging Methods

Use both immediate print output and file logging:

```python
# Immediate console output (for real-time debugging)
print(f"[DEBUG] Starting {operation_name}...", flush=True)
print(f"[DEBUG] {variable} = {value}", flush=True)

# File logging (for persistent records)
logger.info(f"Successfully completed {operation}")
logger.warning(f"Non-critical issue: {issue}")
logger.error(f"Operation failed: {error}")
logger.exception(f"Exception in {function}:")  # Includes stack trace
```

### Logging Patterns

```python
def process_batch(self, symbols: List[str]) -> bool:
    """Example function with proper logging."""
    print(f"[DEBUG] process_batch called with {len(symbols)} symbols", flush=True)
    logger.info(f"Processing batch of {len(symbols)} symbols")

    try:
        # Log before critical operations
        print("[DEBUG] Calling API to fetch data...", flush=True)
        data = self.api.fetch_data(symbols)
        print(f"[DEBUG] API returned {len(data)} items", flush=True)

        # Log state changes
        for item in data:
            print(f"[DEBUG] Processing item: {item['id']}", flush=True)
            self._process_item(item)

        logger.info(f"Successfully processed batch of {len(symbols)} symbols")
        print("[DEBUG] process_batch complete", flush=True)
        return True

    except Exception as e:
        print(f"[DEBUG] process_batch failed: {e}", flush=True)
        logger.exception(f"Error processing batch: {e}")
        return False
```

### Log Level Guidelines

| Level | Usage | Example |
|-------|-------|---------|
| DEBUG (print) | Detailed execution flow | `[DEBUG] Entering function X` |
| INFO | Normal operations | `Successfully created alert` |
| WARNING | Non-critical issues | `Could not save layout` |
| ERROR | Operation failures | `Failed to sign in` |
| EXCEPTION | Errors with traces | `Error in processing:` |

---

## Git Workflow

### Branch Naming

```
feature/description    # New features
fix/description        # Bug fixes
refactor/description   # Code improvements
docs/description       # Documentation changes
```

Examples:
- `feature/add-obdiv-screener`
- `fix/stale-element-retry`
- `refactor/api-client-cleanup`
- `docs/add-api-reference`

### Commit Messages

```
# Format
<type>: <short description>

<longer description if needed>

# Examples
feat: Add webhook alert creation for tiered mode

Implement create_webhook_alert() method in Browser class.
This enables TradingView to POST to Stock Buddy API when
screener conditions are met.

fix: Handle stale element in indicator access

Add retry logic with fresh element lookup when
StaleElementReferenceException occurs.

docs: Add API reference documentation
```

### Commit Types

| Type | Usage |
|------|-------|
| `feat` | New feature |
| `fix` | Bug fix |
| `refactor` | Code restructuring (no behavior change) |
| `docs` | Documentation only |
| `style` | Formatting, no code change |
| `test` | Adding tests |
| `chore` | Maintenance tasks |

---

## Pull Request Process

### Before Creating PR

1. Run validation:
   ```bash
   python tiered_main.py --validate
   ```

2. Test API connection:
   ```bash
   python tiered_main.py --test-api
   ```

3. Run a single cycle (if code changes affect execution):
   ```bash
   python tiered_main.py --single-cycle
   ```

4. Update relevant documentation

### PR Requirements

- Clear title describing the change
- Description of what changed and why
- Reference any related issues
- Update documentation if needed
- Add appropriate logging to new code
- Follow code style guidelines

### PR Template

```markdown
## Summary
Brief description of changes

## Changes
- Change 1
- Change 2

## Testing
How was this tested?

## Documentation
- [ ] Updated relevant docs
- [ ] Added logging to new code
- [ ] Updated CLAUDE.md if architecture changed
```

---

## Testing Requirements

### Manual Testing

Before submitting changes:

1. **Configuration validation**:
   ```bash
   python tiered_main.py --validate   # Tiered mode
   python combo_main.py --validate    # Combo mode
   ```

2. **API connectivity**:
   ```bash
   python tiered_main.py --test-api
   ```

3. **Browser automation** (if changed browser code):
   ```bash
   python tiered_main.py --test-browser
   ```

4. **Single cycle / setup** (for workflow changes):
   ```bash
   python tiered_main.py --single-cycle    # Tiered mode
   python combo_main.py --setup-only       # Combo mode
   ```

5. **Phase 2 testing** (if OBDIV-related):
   ```bash
   python tiered_main.py --test-phase2
   ```

6. **Combo maintenance** (if changed maintenance code):
   ```bash
   python combo_main.py --maintain-only
   ```

### What to Verify

- [ ] No Python syntax errors
- [ ] Configuration validates successfully
- [ ] API connection works
- [ ] Browser launches correctly
- [ ] TradingView login succeeds
- [ ] Layout switching works
- [ ] Indicator detection works
- [ ] Alert creation/deletion works
- [ ] No new warnings or errors in logs

---

## Documentation Updates

### When to Update Docs

Update documentation when:

| Change Type | Files to Update |
|-------------|-----------------|
| Features or usage changes | `README.md` |
| Setup/configuration changes | `docs/SETUP.md` |
| API endpoint changes | `docs/API.md` |
| Database schema changes | `docs/DATABASE.md` |
| Tiered architecture/module changes | `docs/legacy/ARCHITECTURE.md` |
| Combo architecture/module changes | `docs/combo/ARCHITECTURE.md` |
| New issues/solutions discovered | `docs/TROUBLESHOOTING.md` |
| Tiered implementation progress | `docs/legacy/PRD.md` |
| Combo implementation progress | `docs/combo/PRD.md` |

### Documentation Style

- Use clear, concise language
- Include code examples where helpful
- Keep formatting consistent
- Update table of contents if adding sections
- Test all code examples

### Record Learnings

When you make a mistake or discover something important:

1. Add the learning to `AGENTS.md`:
   ```markdown
   ## Lesson Learned: [Date]

   **Issue**: Description of what went wrong
   **Solution**: How it was fixed
   **Prevention**: How to avoid in future
   ```

2. Update `TROUBLESHOOTING.md` if it's a common issue

---

## Code Review Checklist

For reviewers:

- [ ] Code follows project style guidelines
- [ ] Appropriate logging is included
- [ ] Error handling is present
- [ ] No hardcoded credentials or secrets
- [ ] Documentation is updated
- [ ] Changes are tested
- [ ] Commit messages are clear
- [ ] No unnecessary changes included

---

## Quick Reference

### Setup Development Environment

```bash
# Clone and setup
git clone <repository-url>
cd tradingview-to-everywhere
pipenv install
pipenv shell

# Create branch
git checkout -b feature/my-feature

# Make changes...

# Test
python tiered_main.py --validate      # Tiered mode
python combo_main.py --validate       # Combo mode

# Commit
git add .
git commit -m "feat: description of change"

# Push
git push origin feature/my-feature
```

### Key Files for Reference

- `CLAUDE.md` - Project overview and instructions
- `docs/legacy/PRD.md` - Tiered mode specification
- `docs/legacy/ARCHITECTURE.md` - Tiered mode system design
- `docs/combo/PRD.md` - Combo mode specification
- `docs/combo/ARCHITECTURE.md` - Combo mode system design
- `AGENTS.md` - Lessons learned

---

## See Also

- [Architecture](legacy/ARCHITECTURE.md) - System design reference
- [Setup Guide](SETUP.md) - Development environment setup
- [CLAUDE.md](../CLAUDE.md) - Project overview
