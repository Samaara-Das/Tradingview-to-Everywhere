# Contributing Guide
# TTE Tiered Screener Architecture

Thank you for your interest in contributing to the TTE project. This guide explains how to contribute effectively.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Setup](#development-setup)
3. [Code Guidelines](#code-guidelines)
4. [Pull Request Process](#pull-request-process)
5. [Testing Requirements](#testing-requirements)
6. [Documentation](#documentation)

---

## Getting Started

### Prerequisites

- **Python 3.9+** - For orchestrator development
- **Node.js 18+** - For Stock Buddy development
- **Chrome Browser** - For Selenium automation
- **TradingView Account** - For Pine Script testing
- **Git** - For version control

### Repository Structure

```
tradingview-to-everywhere/
├── Pine Script Code/          # TradingView indicators and screeners
│   ├── TTE NWE Screener.txt
│   ├── TTE OBDIV Screener.txt
│   └── ...
├── docs/                      # Project documentation
│   ├── GLOSSARY.md
│   ├── API_DOCUMENTATION.md
│   └── ...
├── database/                  # Database utilities
├── send_to_socials/           # Social media integration
├── main.py                    # Python entry point
├── tiered_orchestrator.py     # Tiered system orchestrator
└── CLAUDE.md                  # AI assistant instructions
```

---

## Development Setup

### Python Environment

```bash
# Clone repository
git clone <repository-url>
cd tradingview-to-everywhere

# Create virtual environment
pipenv install --dev

# Activate environment
pipenv shell

# Verify installation
python -c "import selenium; print('OK')"
```

### Stock Buddy (Next.js)

```bash
# Navigate to Stock Buddy directory
cd stock-buddy

# Install dependencies
npm install

# Set up environment
cp .env.example .env.local
# Edit .env.local with your values

# Start development server
npm run dev
```

### Environment Configuration

See `docs/ENVIRONMENT_CONFIG.md` for complete environment variable documentation.

---

## Code Guidelines

### Python Code Style

Follow PEP 8 with these additions:

```python
# Use type hints
def process_signal(symbol: str, direction: str) -> dict:
    """Process a trading signal.

    Args:
        symbol: Trading symbol (e.g., "GBPAUD")
        direction: Signal direction ("bullish" or "bearish")

    Returns:
        Dictionary containing processed signal data

    Raises:
        ValueError: If direction is invalid
    """
    if direction not in ("bullish", "bearish"):
        raise ValueError(f"Invalid direction: {direction}")

    return {
        "symbol": symbol,
        "direction": direction,
        "processed_at": datetime.utcnow()
    }
```

**Formatting:**
- Use Black for auto-formatting
- Line length: 88 characters
- Import sorting with isort

```bash
# Format code
black .
isort .
```

### TypeScript Code Style

Follow ESLint + Prettier configuration:

```typescript
// Use interfaces for object shapes
interface Signal {
  id: string;
  symbol: string;
  direction: 'bullish' | 'bearish';
  level: 1 | 2 | 3;
  createdAt: Date;
}

// Use async/await over promises
async function fetchSignals(limit: number): Promise<Signal[]> {
  const response = await fetch(`/api/signals?limit=${limit}`);
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }
  return response.json();
}
```

**Formatting:**
```bash
# In stock-buddy directory
npm run lint
npm run format
```

### Pine Script Code Style

```pinescript
// Use consistent indentation (4 spaces)
// Group related logic with comments
// Name variables descriptively

//@version=5
indicator("TTE Example", overlay=true)

// ═══════════════════════════════════════════════════════════════════
// INPUTS
// ═══════════════════════════════════════════════════════════════════

i_symbol = input.symbol("GBPAUD", "Symbol")
i_period = input.int(14, "Period", minval=1)

// ═══════════════════════════════════════════════════════════════════
// CALCULATIONS
// ═══════════════════════════════════════════════════════════════════

float sma_value = ta.sma(close, i_period)
bool is_above = close > sma_value

// ═══════════════════════════════════════════════════════════════════
// PLOTTING
// ═══════════════════════════════════════════════════════════════════

plot(sma_value, "SMA", color=color.blue)
bgcolor(is_above ? color.new(color.green, 90) : na)
```

### Commit Messages

Follow conventional commits:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation only
- `style` - Formatting (no code change)
- `refactor` - Code restructuring
- `test` - Adding tests
- `chore` - Maintenance tasks

**Examples:**
```
feat(screener): add weekly timeframe support for OB detection

fix(api): handle missing timestamp in NWE webhook

docs(readme): update installation instructions

refactor(orchestrator): extract screenshot logic to separate module
```

---

## Pull Request Process

### Before Submitting

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Follow code guidelines
   - Add tests for new functionality
   - Update documentation

3. **Run Tests**
   ```bash
   # Python tests
   pytest

   # TypeScript tests (in stock-buddy)
   npm test
   ```

4. **Format Code**
   ```bash
   # Python
   black . && isort .

   # TypeScript
   npm run lint:fix
   ```

5. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat(scope): description"
   ```

### Submitting PR

1. **Push Branch**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create Pull Request**
   - Use PR template
   - Fill in all sections
   - Link related issues

3. **PR Description Template**
   ```markdown
   ## Summary
   Brief description of changes

   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Breaking change
   - [ ] Documentation update

   ## Testing
   Describe how you tested the changes

   ## Checklist
   - [ ] Code follows project style guidelines
   - [ ] Tests added/updated
   - [ ] Documentation updated
   - [ ] No new warnings
   ```

### Review Process

1. **Automated Checks**
   - Linting passes
   - Tests pass
   - Build succeeds

2. **Code Review**
   - At least 1 approval required
   - All comments addressed

3. **Merge**
   - Squash and merge preferred
   - Delete feature branch after merge

---

## Testing Requirements

### Python Tests

```python
# tests/test_orchestrator.py
import pytest
from tiered_orchestrator import process_hot_symbol

def test_process_hot_symbol_valid():
    """Test processing valid hot symbol."""
    result = process_hot_symbol({
        "symbol": "GBPAUD",
        "direction": "bullish",
        "nwe_timeframes": ["H4", "D1"]
    })
    assert result["success"] is True
    assert result["symbol"] == "GBPAUD"

def test_process_hot_symbol_invalid_direction():
    """Test processing with invalid direction."""
    with pytest.raises(ValueError):
        process_hot_symbol({
            "symbol": "GBPAUD",
            "direction": "invalid"
        })
```

**Running Tests:**
```bash
# All tests
pytest

# With coverage
pytest --cov=. --cov-report=html

# Specific test file
pytest tests/test_orchestrator.py

# Specific test
pytest tests/test_orchestrator.py::test_process_hot_symbol_valid
```

### TypeScript Tests

```typescript
// __tests__/api/nwe.test.ts
import { createMocks } from 'node-mocks-http';
import handler from '@/pages/api/nwe';

describe('/api/nwe', () => {
  it('accepts valid NWE webhook', async () => {
    const { req, res } = createMocks({
      method: 'POST',
      body: {
        tier: 'nwe',
        symbol: 'GBPAUD',
        direction: 'bullish',
        timeframes: ['H4', 'D1']
      }
    });

    await handler(req, res);

    expect(res._getStatusCode()).toBe(200);
    expect(JSON.parse(res._getData())).toMatchObject({
      success: true
    });
  });

  it('rejects invalid direction', async () => {
    const { req, res } = createMocks({
      method: 'POST',
      body: {
        tier: 'nwe',
        symbol: 'GBPAUD',
        direction: 'invalid'
      }
    });

    await handler(req, res);

    expect(res._getStatusCode()).toBe(400);
  });
});
```

**Running Tests:**
```bash
# In stock-buddy directory
npm test

# Watch mode
npm test -- --watch

# Coverage
npm test -- --coverage
```

### Pine Script Testing

Pine Script doesn't have automated tests. Manual testing process:

1. **Load in TradingView**
   - Add indicator to chart
   - Verify no compilation errors

2. **Visual Verification**
   - Check signals match expected behavior
   - Compare with reference indicators

3. **Alert Testing**
   - Set up test alert
   - Trigger condition manually
   - Verify webhook payload

---

## Documentation

### When to Update Docs

- **New Feature**: Update relevant guides
- **API Change**: Update API documentation
- **Configuration Change**: Update environment config
- **Bug Fix**: Update troubleshooting if relevant

### Documentation Files

| File | Update When |
|------|-------------|
| `README.md` | Major features, setup changes |
| `docs/API_DOCUMENTATION.md` | API endpoints change |
| `docs/ENVIRONMENT_CONFIG.md` | Environment variables change |
| `docs/GLOSSARY.md` | New terms introduced |
| `CHANGELOG.md` | Every release |

### Documentation Style

- Use clear, concise language
- Include code examples
- Keep formatting consistent
- Test all code snippets

---

## Getting Help

### Resources

- **Project Docs**: `docs/` folder
- **Glossary**: `docs/GLOSSARY.md`
- **API Reference**: `docs/API_DOCUMENTATION.md`

### Questions

- Create GitHub Issue with "question" label
- Check existing issues first
- Provide context and code examples

### Reporting Bugs

Use the bug report template:

```markdown
## Bug Description
Clear description of the bug

## Steps to Reproduce
1. Step 1
2. Step 2
3. Step 3

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: [e.g., Windows 11]
- Python: [e.g., 3.11]
- Browser: [e.g., Chrome 120]

## Additional Context
Any other relevant information
```

---

*Thank you for contributing to TTE!*
