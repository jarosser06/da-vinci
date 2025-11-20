# Task Completion Checklist

When completing a coding task, ensure:

## 1. Code Quality
- [ ] Code follows style conventions (100 char line length)
- [ ] Type hints are present and correct
- [ ] Docstrings follow project format (Keyword Arguments with --)

## 2. Linting
- [ ] Run `./lint.sh --fix` to auto-fix issues
- [ ] Ensure zero lint errors before committing
- [ ] Check flake8, black, isort, mypy all pass

## 3. Testing
- [ ] Run `./test.sh` to verify all tests pass
- [ ] Run `./test.sh --coverage` to check coverage
- [ ] Ensure 90% minimum coverage maintained
- [ ] Add tests for new functionality

## 4. Git Workflow
- [ ] Commits follow format (under 70 chars, active voice)
- [ ] Branch naming follows convention (feature/, fix/, issue/)
- [ ] Changes are on appropriate branch

## 5. Documentation
- [ ] Public APIs have docstrings
- [ ] Complex logic is explained
- [ ] Examples provided where helpful
