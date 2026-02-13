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
class Browser:
    pass

# Use UPPER_SNAKE_CASE for constants
BATCH_SIZE = 3
CHART_TIMEFRAME = "1 minute"
```

### Naming Guidelines

| Type | Convention | Example |
|------|------------|---------|
| Variables | snake_case | `symbol_list`, `batch_count` |
| Functions | snake_case, verb prefix | `get_symbols()`, `create_alert()` |
| Classes | PascalCase | `Browser`, `ComboConfig` |
| Constants | UPPER_SNAKE_CASE | `MAX_RETRIES`, `LAYOUT_NAME` |
| Files | snake_case | `tte/main.py`, `tte/browser/tradingview.py` |

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

**CRITICAL**: Every new function or significant code block MUST include logging.

### Why Logging is Essential

- Browser automation issues are difficult to debug without logs
- Logs help identify where operations fail
- Timing issues require visibility into execution flow
- Production debugging relies entirely on log output

### Logging Methods

Use the project's logger setup:

```python
from tte import log

logger = log.setup_logger(__name__, log.DEBUG)

# File logging (for persistent records)
logger.info(f"Successfully completed {operation}")
logger.debug(f"Detailed step: {variable} = {value}")
logger.warning(f"Non-critical issue: {issue}")
logger.error(f"Operation failed: {error}")
logger.exception(f"Exception in {function}:")  # Includes stack trace
```

### Log Level Guidelines

| Level | Usage | Example |
|-------|-------|---------|
| DEBUG | Detailed execution flow | `Entering function X` |
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
- `feature/add-maintenance-retry`
- `fix/stale-element-retry`
- `refactor/alert-creation-cleanup`
- `docs/update-api-reference`

### Commit Messages

```
# Format
<type>: <short description>

<longer description if needed>

# Examples
feat: Add webhook alert creation for combo mode

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
   python combo_main.py --validate
   ```

2. Verify all Python files compile:
   ```bash
   python -m py_compile tte/main.py
   python -m py_compile tte/browser/tradingview.py
   ```

3. Update relevant documentation

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
   python combo_main.py --validate
   ```

2. **Browser automation** (if changed browser code):
   Run with `headless: false` to visually verify behavior

3. **Setup test** (for alert creation changes):
   ```bash
   python combo_main.py --setup-only
   ```

4. **Maintenance test** (if changed maintenance code):
   ```bash
   python combo_main.py --maintain-only
   ```

### What to Verify

- [ ] No Python syntax errors
- [ ] Configuration validates successfully
- [ ] Browser launches correctly
- [ ] TradingView login succeeds
- [ ] Layout switching works
- [ ] Indicator detection works
- [ ] Alert creation works
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
| Combo architecture/module changes | `docs/combo/ARCHITECTURE.md` |
| New issues/solutions discovered | `docs/TROUBLESHOOTING.md` |
| Combo implementation progress | `docs/combo/PRD.md` |

### Documentation Style

- Use clear, concise language
- Include code examples where helpful
- Keep formatting consistent
- Update table of contents if adding sections
- Test all code examples

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
python combo_main.py --validate

# Commit
git add .
git commit -m "feat: description of change"

# Push
git push origin feature/my-feature
```

### Key Files for Reference

- `CLAUDE.md` - Project overview and instructions
- `docs/combo/PRD.md` - Combo mode specification
- `docs/combo/ARCHITECTURE.md` - Combo mode system design

---

## See Also

- [Combo Architecture](combo/ARCHITECTURE.md) - System design reference
- [Setup Guide](SETUP.md) - Development environment setup
- [CLAUDE.md](../CLAUDE.md) - Project overview
