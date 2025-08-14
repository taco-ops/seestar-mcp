# Pre-commit Setup for SeestarS50 MCP

This project uses [pre-commit](https://pre-commit.com/) to automatically run code quality checks before each commit, ensuring consistent code style and catching issues early.

## What is Pre-commit?

Pre-commit is a framework for managing and maintaining multi-language pre-commit hooks. It automatically runs tools like Black, flake8, and mypy on your code before you commit, helping maintain code quality and consistency across the project.

## Installed Tools

The following tools are configured to run automatically:

### Code Quality Tools
- **Black**: Code formatter that ensures consistent Python code style
- **isort**: Import statement sorter that organizes imports consistently
- **flake8**: Linter that catches syntax errors, undefined variables, and style issues
- **mypy**: Static type checker for Python

### Security and Documentation
- **bandit**: Security vulnerability scanner for Python code
- **blacken-docs**: Formats Python code in documentation files

### Basic Checks
- Trailing whitespace removal
- End-of-file fixing
- YAML/JSON/TOML validation
- Large file detection
- Merge conflict detection

## Setup

Pre-commit is automatically installed when you install the development dependencies:

```bash
# With uv (recommended)
uv pip install -e ".[dev]"
pre-commit install

# With pip
pip install -e ".[dev]"
pre-commit install
```

## Usage

### Automatic Execution

Once installed, pre-commit hooks run automatically on each `git commit`. If any hook fails or makes changes, the commit is stopped and you'll need to review and re-add the changes.

```bash
git add .
git commit -m "Your commit message"
# Pre-commit hooks run automatically here
```

### Manual Code Quality Commands

If you prefer to run code quality tools manually instead of through pre-commit hooks:

### 🔧 Setup (One-time)
```bash
# Install pre-commit hooks (if not already done)
uv run pre-commit install
```

### 📝 Code Formatting
```bash
# Format all Python code with Black
uv run black src tests

# Sort imports with isort
uv run isort src tests

# Format both at once
uv run black src tests && uv run isort src tests
```

### 🔍 Linting and Type Checking
```bash
# Run flake8 linting
uv run flake8 src tests

# Run mypy type checking
uv run mypy src

# Run bandit security checks
uv run bandit -r src
```

### 🧪 Testing
```bash
# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=seestar_mcp --cov-report=term-missing

# Run tests with HTML coverage report
uv run pytest --cov=seestar_mcp --cov-report=html
```

### ⚡ Quick Commands
```bash
# Check everything (no fixes)
uv run black --check src tests && \
uv run isort --check-only src tests && \
uv run flake8 src tests && \
uv run mypy src

# Fix formatting and check linting
uv run black src tests && \
uv run isort src tests && \
uv run flake8 src tests && \
uv run mypy src

# Complete quality check with tests
uv run black src tests && \
uv run isort src tests && \
uv run flake8 src tests && \
uv run mypy src && \
uv run pytest --cov=seestar_mcp
```

### 🎯 Common Workflows
```bash
# Before committing (manual)
uv run pre-commit run --all-files

# Daily development
uv run black src tests
uv run flake8 src

# Before pushing (complete check)
uv run pre-commit run --all-files && uv run pytest
```

## Configuration Files

### `.pre-commit-config.yaml`
Main configuration file that defines which hooks to run and their settings.

### `.flake8`
Configuration for flake8 linter with project-specific settings:
- Line length: 88 characters (matching Black)
- Ignored errors: E203, E501, W503 (conflicts with Black)
- Per-file ignores for tests and scripts

### `pyproject.toml`
Contains configuration for other tools like Black, mypy, and pytest.

## Handling Hook Failures

When hooks fail, they typically fall into these categories:

### 1. Auto-fixable Issues
These are automatically fixed by the hooks:
- **Black**: Code formatting
- **isort**: Import sorting
- **Trailing whitespace**: Automatically removed
- **End of files**: Automatically fixed

After auto-fixes, re-add files and commit:
```bash
git add .
git commit -m "Your commit message"
```

### 2. Manual Fixes Required

#### Flake8 Issues
- **F401**: Unused imports - Remove unused imports
- **E501**: Line too long - Break long lines (though Black usually handles this)
- **F811**: Redefined function - Remove duplicate definitions

#### MyPy Issues
- **Missing type annotations**: Add type hints to functions
- **Union attribute access**: Handle None cases properly

Example fixes:
```python
# Before (mypy error)
def my_function(param):
    return param.upper()


# After (with type annotation)
def my_function(param: str) -> str:
    return param.upper()
```

#### Bandit Issues
- **B608**: SQL injection - Use parameterized queries
- **B101**: assert statements - Replace with proper error handling

### 3. Bypassing Hooks (Not Recommended)

In rare cases, you can bypass hooks:
```bash
git commit --no-verify -m "Emergency commit"
```

## Workflow Integration

### Development Workflow
1. Make your changes
2. Run tests: `pytest`
3. Stage changes: `git add .`
4. Commit: `git commit -m "Description"`
5. Pre-commit runs automatically
6. Fix any issues and re-commit if needed

### CI/CD Integration
Pre-commit hooks also run in GitHub Actions, ensuring code quality in pull requests and preventing issues from reaching the main branch.

## Customization

### Adding New Hooks
Edit `.pre-commit-config.yaml` to add new tools:

```yaml
  - repo: https://github.com/pycqa/pydocstyle
    rev: 6.3.0
    hooks:
      - id: pydocstyle
```

### Modifying Existing Hooks
Update arguments in the configuration:

```yaml
  - repo: https://github.com/psf/black
    rev: 25.1.0
    hooks:
      - id: black
        args: [--line-length=100]  # Change line length
```

### Excluding Files
Use `exclude` to skip certain files:

```yaml
  - repo: https://github.com/pycqa/flake8
    rev: 7.3.0
    hooks:
      - id: flake8
        exclude: ^(tests/legacy/|docs/)
```

## Tips and Best Practices

1. **Run pre-commit early and often**: Don't wait until commit time
2. **Fix issues incrementally**: Address one tool at a time
3. **Understand the tools**: Learn what each tool does and why it's important
4. **Keep configuration updated**: Regularly update tool versions
5. **Use pre-commit**: `uv run pre-commit run --all-files` for comprehensive checks

## Troubleshooting

### Pre-commit Not Running
```bash
# Reinstall hooks
pre-commit uninstall
pre-commit install

# Check hook installation
ls -la .git/hooks/pre-commit
```

### Hooks Taking Too Long
```bash
# Update to latest versions
pre-commit autoupdate

# Clean cache if needed
pre-commit clean
```

### Tool-Specific Issues
```bash
# Check tool-specific help
black --help
flake8 --help
mypy --help
```

## Benefits

- **Consistent code style**: Everyone follows the same formatting rules
- **Early issue detection**: Catch problems before they reach CI/CD
- **Reduced review time**: Less time spent on style discussions
- **Better code quality**: Automated type checking and security scanning
- **Documentation quality**: Ensures code in docs is properly formatted

## Integration with IDEs

Most IDEs can be configured to run these tools automatically:

### VS Code
Install extensions:
- Python (Microsoft)
- Black Formatter
- Flake8
- MyPy Type Checker

### PyCharm
Configure external tools or use built-in formatters with the same settings as pre-commit.

This setup ensures that code quality is maintained consistently across all contributors and environments.
