# Contributing to ChatGPT-like Chatbot

Thank you for your interest in contributing to this project! This document provides guidelines and information for contributors.

## 🚀 Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/chatgpt-like.git
   cd chatgpt-like
   ```
3. **Set up the development environment**:
   ```bash
   uv sync  # or pip install -r requirements.txt
   ```
4. **Create a new branch** for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 📝 Development Guidelines

### Code Style

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions small and focused

### Frontend Guidelines

- Use semantic HTML5 elements
- Follow CSS best practices with custom properties
- Ensure responsive design for all screen sizes
- Test accessibility features

### Testing

- Test your changes thoroughly
- Ensure the application works with different browsers
- Test both SSE and WebSocket functionality
- Verify conversation persistence works correctly

## 🐛 Reporting Issues

When reporting issues, please include:

1. **Clear description** of the problem
2. **Steps to reproduce** the issue
3. **Expected behavior** vs actual behavior
4. **Environment details** (OS, Python version, browser)
5. **Relevant logs** or error messages

## ✨ Feature Requests

For feature requests, please:

1. Check existing issues first
2. Provide a clear description of the feature
3. Explain the use case and benefits
4. Consider implementation complexity

## 🔧 Pull Request Process

1. **Update documentation** if needed
2. **Add tests** for new functionality
3. **Ensure all tests pass**
4. **Update the README** if you add new features
5. **Create a clear PR description** explaining your changes

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tested locally
- [ ] Tested with different browsers
- [ ] Tested SSE and WebSocket functionality

## Screenshots (if applicable)
Add screenshots to help explain your changes
```

## 🏷️ Commit Messages

Use clear, descriptive commit messages:

- `feat: add conversation title generation`
- `fix: resolve WebSocket connection issue`
- `docs: update installation instructions`
- `style: improve mobile responsiveness`

## 📋 Code Review Process

- All PRs require review before merging
- Address review comments promptly
- Keep PRs focused and reasonably sized
- Respond to feedback constructively

## 🎯 Areas for Contribution

- **UI/UX improvements**: Better mobile experience, accessibility
- **Performance optimization**: Faster response times, better caching
- **New features**: Additional language support, export functionality
- **Documentation**: Better examples, tutorials, API docs
- **Testing**: Unit tests, integration tests, E2E tests

## 📞 Getting Help

- Check existing issues and discussions
- Join our community discussions
- Ask questions in issues with the `question` label

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing! 🎉
