# Secret Snowflake Project Guide

## Commands
- Run the application: `python main.py`
- Lint code: `pylint main.py configs/`
- Type check: `mypy main.py configs/`
- Sort imports: `isort main.py configs/`

## Code Style Guidelines
- **Imports**: Group by standard library → third-party → local (blank line separator)
- **Type Annotations**: Use full type hints with Python's typing module
- **Naming**: snake_case for variables/functions, UPPER_CASE for constants
- **Indentation**: 4 spaces
- **Line Length**: Maximum 100 characters
- **Docstrings**: Required for all functions with parameter descriptions
- **Data Structures**: Prefer namedtuple for structured data
- **Function Design**: Write pure functions with clear input/output
- **Comments**: Minimal, focus on explaining purpose not implementation
- **Error Handling**: Use explicit try/except blocks for expected errors
- **File Organization**: Keep configuration separated in configs/