# Contributing to gh-unfollow

Thanks for your interest in contributing! 🎉

## How to Contribute

### Reporting Bugs
1. Check the [existing issues](https://github.com/uthumany/gh-unfollow/issues) first
2. Use the Bug Report template when creating a new issue
3. Include: steps to reproduce, expected behavior, actual behavior, and environment details

### Requesting Features
1. Check the [existing issues](https://github.com/uthumany/gh-unfollow/issues) first
2. Use the Feature Request template
3. Describe: what problem it solves, proposed solution, alternatives considered

### Pull Requests
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Run tests: `python -m pytest tests/ -v`
5. Commit with a descriptive message: `git commit -m 'feat: add amazing feature'`
6. Push: `git push origin feature/amazing-feature`
7. Open a Pull Request

### Commit Convention
We follow [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `test:` Adding or updating tests
- `refactor:` Code restructuring
- `chore:` Maintenance tasks

### Development Setup
```bash
# Clone
git clone https://github.com/uthumany/gh-unfollow.git
cd gh-unfollow

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dev dependencies
pip install -e ".[dev]"

# Run tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ -v --cov=src --cov-report=html
```

### Code Style
- Python 3.8+ compatible
- Standard library only for production code
- Type hints where useful
- Docstrings for public functions
- Follow PEP 8

### Testing
- Write tests for new features
- Ensure all tests pass before submitting a PR
- Aim for >80% test coverage

## License
By contributing, you agree that your contributions will be licensed under the MIT License.
