# Tests Directory

This directory contains all test files and demo pages for the ChatGPT-like chatbot application.

## 📁 Test Files Overview

### 🎨 Frontend Tests

#### `test_code_appearance.html`
- **Purpose**: Demonstrates enhanced code appearance with syntax highlighting
- **Features**: 
  - Professional code block styling
  - Syntax highlighting for multiple languages
  - Copy-to-clipboard functionality
  - Interactive hover effects
  - Language-specific color schemes
- **Usage**: Open in browser to see enhanced code rendering

#### `test_code_editor.html`
- **Purpose**: Demonstrates full-screen code editor functionality
- **Features**:
  - Full-screen code editor modal
  - Edit code in dedicated interface
  - Copy, download, and format capabilities
  - Language-specific file extensions
  - Real-time line and character counting
  - Professional dark theme
- **Usage**: Click "Edit" button on code blocks to open editor

#### `test_typing_indicator.html`
- **Purpose**: Demonstrates the typing indicator functionality
- **Features**:
  - Animated typing dots
  - Smooth fade-in/out animations
  - Interactive demo buttons
  - Visual feedback during AI response generation
- **Usage**: Test different typing scenarios (quick, long, error responses)

### 🧠 Memory Tests

#### `test_memory_demo.html`
- **Purpose**: Comprehensive demonstration of memory functionality
- **Features**:
  - Memory type comparison (Buffer, Summary, Token Buffer)
  - Interactive memory testing
  - Live memory statistics
  - Conversation context examples
- **Usage**: Test different memory types and see their impact

### 🔄 Streaming Tests

#### `test_streaming.html`
- **Purpose**: Basic streaming functionality test
- **Features**:
  - Server-Sent Events (SSE) testing
  - WebSocket streaming test
  - Response time measurement
  - Error handling demonstration
- **Usage**: Test streaming performance and reliability

#### `test_smooth_streaming.html`
- **Purpose**: Advanced streaming with smooth updates
- **Features**:
  - Throttled updates to prevent flickering
  - Smooth text appearance
  - Performance optimization
  - Visual comparison with previous implementation
- **Usage**: Compare smooth vs. flickering streaming behavior

## 🚀 How to Run Tests

### Prerequisites
1. Ensure the backend server is running:
   ```bash
   uv run uvicorn backend.app:app --reload --port 8000
   ```

2. Ensure Ollama service is running:
   ```bash
   ollama serve
   ```

### Running Individual Tests

1. **Code Appearance Test**:
   ```bash
   # Open in browser
   open http://localhost:8000/tests/test_code_appearance.html
   ```

2. **Typing Indicator Test**:
   ```bash
   # Open in browser
   open http://localhost:8000/tests/test_typing_indicator.html
   ```

3. **Memory Demo**:
   ```bash
   # Open in browser
   open http://localhost:8000/tests/test_memory_demo.html
   ```

4. **Streaming Tests**:
   ```bash
   # Open in browser
   open http://localhost:8000/tests/test_streaming.html
   open http://localhost:8000/tests/test_smooth_streaming.html
   ```

### Running All Tests
```bash
# Start the server
uv run uvicorn backend.app:app --reload --port 8000

# Open the main application
open http://localhost:8000

# Then open individual test files as needed
```

## 🧪 Test Categories

### 1. **Visual/UI Tests**
- Code appearance and syntax highlighting
- Typing indicators and animations
- Responsive design and mobile support
- Theme switching (light/dark mode)

### 2. **Functionality Tests**
- Memory management (Buffer, Summary, Token Buffer)
- Streaming responses (SSE and WebSocket)
- Conversation persistence
- Error handling and recovery

### 3. **Performance Tests**
- Response time measurement
- Memory usage tracking
- Streaming smoothness
- Large conversation handling

### 4. **Integration Tests**
- Backend API endpoints
- Database operations
- LLM integration
- Authentication and authorization

## 📊 Test Results Interpretation

### Code Appearance Test
- ✅ **Pass**: Code blocks render with proper syntax highlighting
- ✅ **Pass**: Copy functionality works correctly
- ✅ **Pass**: Hover effects and animations are smooth
- ❌ **Fail**: Check CSS loading and JavaScript functionality

### Typing Indicator Test
- ✅ **Pass**: Indicator appears when sending messages
- ✅ **Pass**: Animation is smooth and professional
- ✅ **Pass**: Indicator hides when response starts
- ❌ **Fail**: Check JavaScript event handlers and CSS animations

### Memory Demo Test
- ✅ **Pass**: Different memory types work correctly
- ✅ **Pass**: Memory statistics are displayed
- ✅ **Pass**: Conversation context is maintained
- ❌ **Fail**: Check LangChain integration and memory configuration

### Streaming Tests
- ✅ **Pass**: Responses stream smoothly without flickering
- ✅ **Pass**: SSE and WebSocket both work
- ✅ **Pass**: Error handling works correctly
- ❌ **Fail**: Check backend streaming implementation and network connectivity

## 🔧 Troubleshooting

### Common Issues

1. **Tests not loading**:
   - Ensure server is running on port 8000
   - Check browser console for errors
   - Verify file paths are correct

2. **Streaming not working**:
   - Check Ollama service is running
   - Verify models are loaded (`ollama list`)
   - Check network connectivity

3. **Memory tests failing**:
   - Ensure LangChain packages are installed
   - Check database permissions
   - Verify memory configuration

4. **Styling issues**:
   - Check CSS file loading
   - Verify font imports (Google Fonts)
   - Clear browser cache

### Debug Mode
Enable debug logging by opening browser developer tools and checking the console for detailed error messages.

## 📝 Adding New Tests

When adding new test files:

1. **Naming Convention**: Use `test_<feature_name>.html`
2. **Documentation**: Update this README with test description
3. **Structure**: Follow existing test patterns
4. **Dependencies**: Ensure all required resources are available
5. **Error Handling**: Include proper error handling and user feedback

## 🎯 Test Coverage

Current test coverage includes:
- ✅ Frontend UI components
- ✅ Code appearance and syntax highlighting
- ✅ Typing indicators and animations
- ✅ Memory management functionality
- ✅ Streaming response handling
- ✅ Error handling and recovery
- ✅ Performance optimization
- ✅ Mobile responsiveness

## 📈 Future Test Plans

- [ ] Automated testing with Selenium/Playwright
- [ ] Unit tests for JavaScript functions
- [ ] API endpoint testing with pytest
- [ ] Load testing for concurrent users
- [ ] Cross-browser compatibility testing
- [ ] Accessibility testing (WCAG compliance)
