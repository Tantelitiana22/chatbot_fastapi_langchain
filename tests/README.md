# 🧪 Test Suite - ChatGPT-like Application

This directory contains a comprehensive test suite for the ChatGPT-like application, organized using Domain-Driven Design (DDD) and Hexagonal Architecture principles.

## 📁 Test Structure

```
tests/
├── __init__.py                    # Tests package
├── run_all_tests.py              # Main test runner
├── README.md                     # This file
├── unit/                         # Unit tests
│   ├── __init__.py
│   ├── test_domain_architecture.py    # Domain architecture tests
│   ├── test_full_architecture.py      # Full architecture tests (with LLM)
│   ├── test_domain_entities.py       # Domain entities tests
│   └── test_domain_services.py       # Domain services tests
├── integration/                  # Integration tests
│   ├── __init__.py
│   ├── test_api_endpoints.py          # API endpoint tests
│   ├── test_repositories.py           # Repository integration tests
│   └── test_use_cases.py              # Use case integration tests
├── e2e/                          # End-to-end tests
│   └── __init__.py
└── frontend/                     # Frontend tests
    ├── __init__.py
    ├── test_index.html               # Main test page
    ├── test_code_appearance.html     # Code appearance tests
    ├── test_code_editor.html         # Code editor tests
    ├── test_memory_demo.html         # Memory management tests
    ├── test_smooth_streaming.html    # Streaming tests
    ├── test_streaming.html           # Basic streaming tests
    └── test_typing_indicator.html    # Typing indicator tests
```

## 🚀 Quick Start

### Run All Tests
```bash
python3 tests/run_all_tests.py
```

### Run Specific Test Categories
```bash
# Unit tests only
python3 tests/run_all_tests.py --unit

# Integration tests only
python3 tests/run_all_tests.py --integration

# Frontend tests info
python3 tests/run_all_tests.py --frontend
```

### Get Test Help
```bash
python3 tests/run_all_tests.py --help-tests
```

## 🧪 Test Categories

### 1. Unit Tests (`tests/unit/`)

**Purpose**: Test individual components in isolation

#### Domain Architecture Tests
- **`test_domain_architecture.py`**: Tests the core DDD/Hexagonal architecture
- **`test_full_architecture.py`**: Tests with full LLM integration (requires LangChain)

#### Domain Entities Tests
- **`test_domain_entities.py`**: Tests User, Conversation, Message entities
- **`test_domain_services.py`**: Tests MessageClassificationService, ConversationTitleService

**Run Unit Tests**:
```bash
# Run domain architecture test (no dependencies)
python3 tests/unit/test_domain_architecture.py

# Run with pytest (if installed)
python3 -m pytest tests/unit/ -v
```

### 2. Integration Tests (`tests/integration/`)

**Purpose**: Test component interactions and external dependencies

#### API Endpoint Tests
- **`test_api_endpoints.py`**: Tests REST API endpoints, WebSocket, authentication

#### Repository Tests
- **`test_repositories.py`**: Tests SQLite repository implementations

#### Use Case Tests
- **`test_use_cases.py`**: Tests application use cases with mocked dependencies

**Run Integration Tests**:
```bash
# Run API tests (requires server running)
python3 tests/integration/test_api_endpoints.py

# Run with pytest (if installed)
python3 -m pytest tests/integration/ -v
```

### 3. Frontend Tests (`tests/frontend/`)

**Purpose**: Test UI components, user interactions, and visual features

#### Available Tests
- **`test_index.html`**: Main test page with overview
- **`test_code_appearance.html`**: Code syntax highlighting and formatting
- **`test_code_editor.html`**: Full-screen code editor functionality
- **`test_memory_demo.html`**: Memory management (Buffer, Summary, Token Buffer)
- **`test_streaming.html`**: Basic streaming functionality
- **`test_smooth_streaming.html`**: Advanced streaming with smooth updates
- **`test_typing_indicator.html`**: Typing indicator animations

**Run Frontend Tests**:
```bash
# Start the server
python3 app_new.py

# Open in browser
open http://localhost:8000/tests/frontend/test_index.html
```

### 4. End-to-End Tests (`tests/e2e/`)

**Purpose**: Test complete user workflows (planned for future implementation)

## 📦 Prerequisites

### Required Dependencies
```bash
# Core dependencies
pip install -r requirements.txt

# For pytest tests (optional)
pip install pytest pytest-asyncio
```

### External Services
- **Ollama**: Required for LLM integration tests
- **Server**: Required for integration and frontend tests

## 🔧 Test Configuration

### Environment Variables
```bash
# Optional test configuration
export TEST_DB_PATH="test_conversations.db"
export TEST_CACHE_SIZE=50
export TEST_TIMEOUT=30
```

### Test Database
- Unit tests use temporary databases
- Integration tests can use persistent test databases
- Production database is never modified by tests

## 📊 Test Results Interpretation

### Unit Tests
- ✅ **Pass**: Domain logic works correctly
- ❌ **Fail**: Business rules or entity validation issues

### Integration Tests
- ✅ **Pass**: Components work together correctly
- ❌ **Fail**: API issues, database problems, or service integration

### Frontend Tests
- ✅ **Pass**: UI renders correctly, interactions work
- ❌ **Fail**: JavaScript errors, CSS issues, or API connectivity

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**:
   ```bash
   # Ensure chat_app is in Python path
   export PYTHONPATH="${PYTHONPATH}:$(pwd)/chat_app"
   ```

2. **Database Errors**:
   ```bash
   # Check database permissions
   ls -la conversations.db
   ```

3. **Server Not Running**:
   ```bash
   # Start server for integration tests
   python3 app_new.py
   ```

4. **Ollama Not Available**:
   ```bash
   # Start Ollama service
   ollama serve
   ```

### Debug Mode
Enable detailed logging:
```bash
# Run tests with debug output
python3 tests/run_all_tests.py --unit 2>&1 | tee test_output.log
```

## 📈 Test Coverage

### Current Coverage
- ✅ Domain entities and value objects
- ✅ Domain services and business logic
- ✅ Repository implementations
- ✅ Use case implementations
- ✅ API endpoints
- ✅ Frontend components
- ✅ Memory management
- ✅ Streaming functionality

### Planned Coverage
- [ ] End-to-end user workflows
- [ ] Performance benchmarks
- [ ] Load testing
- [ ] Security testing
- [ ] Accessibility testing

## 🎯 Test Best Practices

### Writing Tests
1. **Arrange-Act-Assert**: Structure tests clearly
2. **Single Responsibility**: One test per behavior
3. **Descriptive Names**: Clear test method names
4. **Independent Tests**: Tests should not depend on each other
5. **Mock External Dependencies**: Use mocks for external services

### Test Data
- Use factories for creating test data
- Clean up test data after each test
- Use realistic test scenarios

### Performance
- Keep unit tests fast (< 1 second each)
- Use parallel execution where possible
- Mock expensive operations

## 📝 Adding New Tests

### Unit Tests
1. Create test file in `tests/unit/`
2. Follow naming convention: `test_<component>.py`
3. Import from `chat_app.domain.*` or `chat_app.application.*`
4. Use pytest or unittest framework

### Integration Tests
1. Create test file in `tests/integration/`
2. Test real component interactions
3. Use temporary databases
4. Mock external services when needed

### Frontend Tests
1. Create HTML file in `tests/frontend/`
2. Follow naming convention: `test_<feature>.html`
3. Include interactive demos
4. Document test scenarios in comments

## 🚀 Continuous Integration

### GitHub Actions (Example)
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: python3 tests/run_all_tests.py --unit
```

## 📚 Additional Resources

- [Domain-Driven Design Testing](https://martinfowler.com/articles/practical-test-pyramid.html)
- [Hexagonal Architecture Testing](https://alistair.cockburn.us/hexagonal-architecture/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Pytest Documentation](https://docs.pytest.org/)

---

**Note**: This test suite follows DDD principles and tests the application at multiple levels, ensuring both individual component correctness and overall system integration.
