# Contributing to sqlite-worker

Thank you for your interest in contributing to sqlite-worker! We welcome contributions from the community and appreciate your help in making this project better.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Guidelines](#coding-guidelines)
- [Submitting Changes](#submitting-changes)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)
- [Good First Issues](#good-first-issues)

## Code of Conduct

This project follows a Code of Conduct that all contributors are expected to adhere to. Please be respectful and professional in all interactions.

**Our Pledge:** We are committed to providing a welcoming and inclusive experience for everyone, regardless of background or identity.

## How Can I Contribute?

There are many ways to contribute to sqlite-worker:

### 🐛 Report Bugs
Found a bug? [Create a bug report](https://github.com/roshanlam/sqlite-worker/issues/new?template=bug_report.yml)

### 💡 Suggest Features
Have an idea? [Submit a feature request](https://github.com/roshanlam/sqlite-worker/issues/new?template=feature_request.yml)

### 📝 Improve Documentation
- Fix typos or clarify explanations
- Add more examples
- Create tutorials
- Improve code comments

### 🔧 Write Code
- Fix bugs
- Implement new features
- Optimize performance
- Add tests

### 🎨 Create Examples
- Add real-world use cases
- Create framework integrations
- Build starter templates
- Write tutorials

### 🤝 Help Others
- Answer questions in [Discussions](https://github.com/roshanlam/sqlite-worker/discussions)
- Review pull requests
- Share your experience

## Getting Started

### Prerequisites

- Python 3.7 or higher
- Git
- Basic understanding of SQLite and threading

### Setting Up Development Environment

1. **Fork the Repository**
   ```bash
   # Click "Fork" on GitHub, then clone your fork
   git clone https://github.com/YOUR_USERNAME/sqlite-worker.git
   cd sqlite-worker
   ```

2. **Create a Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run Tests**
   ```bash
   python tests.py
   python test_new_features.py
   ```

5. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/bug-description
   ```

## Development Workflow

### Making Changes

1. **Update Your Fork**
   ```bash
   git remote add upstream https://github.com/roshanlam/sqlite-worker.git
   git fetch upstream
   git merge upstream/main
   ```

2. **Make Your Changes**
   - Write clean, readable code
   - Follow the coding guidelines below
   - Add tests for new functionality
   - Update documentation as needed

3. **Test Your Changes**
   ```bash
   # Run all tests
   python tests.py
   python test_new_features.py
   
   # Test specific functionality
   python -c "from sqlite_worker import SqliteWorker; worker = SqliteWorker(':memory:'); print('OK')"
   ```

4. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "Clear, descriptive commit message"
   ```

   **Commit Message Guidelines:**
   - Use present tense ("Add feature" not "Added feature")
   - Use imperative mood ("Move cursor to..." not "Moves cursor to...")
   - Limit first line to 72 characters
   - Reference issues and PRs when relevant (#123)

5. **Push to Your Fork**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request**
   - Go to your fork on GitHub
   - Click "New Pull Request"
   - Fill out the PR template
   - Link related issues

## Coding Guidelines

### Python Style

- Follow [PEP 8](https://pep8.org/) style guide
- Use 4 spaces for indentation (no tabs)
- Maximum line length: 100 characters
- Use descriptive variable names

### Code Structure

```python
# Good example
def add_user(self, name: str, email: str) -> int:
    """
    Add a new user to the database.
    
    Args:
        name: User's full name
        email: User's email address
    
    Returns:
        User ID of the created user
    
    Raises:
        ValueError: If email is invalid
    """
    if not self._validate_email(email):
        raise ValueError("Invalid email address")
    
    token = self.worker.insert('users', {
        'name': name,
        'email': email
    })
    return self._get_last_insert_id()
```

### Documentation

- Add docstrings to all public functions and classes
- Use Google-style docstrings
- Include type hints
- Provide usage examples for complex functionality

### Testing

- Write tests for all new features
- Ensure tests are independent and can run in any order
- Use descriptive test names
- Aim for high test coverage

Example:
```python
def test_user_creation(self):
    """Test that users are created correctly"""
    user_id = self.platform.create_user(
        email="test@example.com",
        name="Test User"
    )
    
    self.assertIsNotNone(user_id)
    user = self.platform.get_user(user_id)
    self.assertEqual(user['email'], "test@example.com")
```

### Security

- **Never** commit sensitive data (passwords, API keys, etc.)
- Use parameterized queries to prevent SQL injection
- Validate all user inputs
- Handle errors gracefully

## Submitting Changes

### Pull Request Process

1. **Update Documentation**
   - Update README.md if needed
   - Add/update examples
   - Update CHANGELOG (if applicable)

2. **Ensure Tests Pass**
   - All existing tests must pass
   - Add tests for new functionality
   - No warnings or errors

3. **Fill Out PR Template**
   - Describe what changed and why
   - Link related issues
   - List breaking changes (if any)
   - Add screenshots for UI changes

4. **Request Review**
   - PRs require at least one review
   - Address review comments
   - Keep discussions constructive

5. **Merge**
   - Once approved, a maintainer will merge your PR
   - Squash commits may be used for cleaner history

### PR Checklist

- [ ] Code follows the style guidelines
- [ ] Tests added/updated and passing
- [ ] Documentation updated
- [ ] No breaking changes (or clearly documented)
- [ ] Commit messages are clear
- [ ] PR description is complete

## Reporting Bugs

When reporting bugs, please include:

- **Description**: Clear description of the bug
- **Expected Behavior**: What you expected to happen
- **Actual Behavior**: What actually happened
- **Steps to Reproduce**: Minimal steps to reproduce the issue
- **Code Sample**: Minimal code that demonstrates the bug
- **Environment**: OS, Python version, sqlite-worker version
- **Error Messages**: Full error message and stack trace

## Suggesting Features

When suggesting features, please include:

- **Problem Statement**: What problem does this solve?
- **Proposed Solution**: How would you like it to work?
- **Example Usage**: Show example code
- **Alternatives**: Other solutions you considered
- **Use Case**: Real-world scenario where this helps

## Good First Issues

New to the project? Look for issues labeled `good first issue`:

- [Good First Issues](https://github.com/roshanlam/sqlite-worker/labels/good%20first%20issue)

These issues are:
- Well-defined and scoped
- Good for learning the codebase
- Have clear acceptance criteria
- Include guidance from maintainers

**Example Good First Issues:**
- Adding a new example to the examples directory
- Improving documentation clarity
- Adding test coverage for existing features
- Fixing small bugs with clear reproduction steps

## Development Tips

### Running Individual Tests

```bash
python -m unittest tests.TestSqliteWorker.test_create_table_and_insert
```

### Debugging

```python
# Add logging to debug issues
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Performance Testing

```bash
python test_performance.py
```

### Code Coverage

```bash
pip install coverage
coverage run -m unittest tests
coverage report
coverage html  # Generate HTML report
```

## Getting Help

Need help? Here's where to ask:

- **Questions**: [GitHub Discussions](https://github.com/roshanlam/sqlite-worker/discussions)
- **Bugs**: [Issue Tracker](https://github.com/roshanlam/sqlite-worker/issues)
- **Chat**: (If you have a Discord/Slack channel)

## Recognition

Contributors are recognized in:
- README.md contributors section
- Release notes
- GitHub contributors page

Thank you for contributing to sqlite-worker! 🎉

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (see [LICENSE](LICENSE)).
