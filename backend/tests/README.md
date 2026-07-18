# personalized-ai-storybook Testing Guide

This directory contains comprehensive black-box and white-box testing for the personalized-ai-storybook system.

## 📁 Directory Structure

```
tests/
├── blackbox/                    # Black-Box Testing
│   └── test_cases_blackbox.md  # 68 test cases
├── whitebox/                    # White-Box Testing (PyTest)
│   ├── test_*.py               # 130+ pytest unit tests
│   └── run_all_tests.py        # Standalone test runner (47 tests)
├── coverage_html/               # HTML Coverage Report (35 files)
│   └── index.html              # Main coverage report
├── conftest.py                  # PyTest configuration & fixtures
├── TEST_RESULTS.md             # Complete test results summary
└── README.md                    # This file
```

---

## 🎯 Black-Box Testing

**Location**: `blackbox/test_cases_blackbox.md`

### Test Types (68 Total):

#### 1. Equivalence Class Partitioning (30 cases)
Tests different classes of inputs:
- User registration (username, password, email)
- Story prompts (short, normal, long, invalid, nonsense)
- Content safety (safe, blocked, warning keywords)
- Image generation modes (simple, personalized, none)
- Workshop modes (new_idea, improvement)

#### 2. Boundary Value Analysis (26 cases)
Tests boundary conditions:
- Username: 2, 3, 4, 49, 50, 51 characters
- Password: 5, 6, 7, 71, 72, 73 bytes
- Prompt length: 69, 70, 71 words
- Scene count: 1, 2, 3, 4, 5 scenes
- Age range: 2, 3, 7, 12, 13 years

#### 3. Functional Test Cases (12 cases)
End-to-end user scenarios:
- User registration and login
- Story generation (simple & personalized)
- Content safety validation
- Chatbot interaction
- Workshop sessions
- PDF export

### How to Execute Black-Box Tests:

Black-box tests are **manual test cases** documented with:
- Test ID
- Description
- Preconditions
- Test Steps
- Expected Result
- Actual Result (to be filled during execution)
- Status (Pass/Fail)

**To execute**: Follow the test steps in `blackbox/test_cases_blackbox.md` and fill in the "Actual Result" and "Status" columns.

---

## 🧪 White-Box Testing

**Location**: `whitebox/`

### Test Framework: PyTest + Coverage.py

### Test Modules (47 Total Tests):

1. **Auth Schemas** (10 tests) - `test_auth_schemas.py`
   - Input validation (username, password, email)
   - Boundary value analysis
   - Pydantic schema validation

2. **Content Safety** (14 tests) - `test_content_safety.py`
   - Blocked keywords (explicit, violence, drugs, horror)
   - Warning keywords (monster, dark, witch)
   - Prompt enhancement pipeline

3. **Prompt Agent** (6 tests) - `test_prompt_agent.py`
   - Empty/nonsense input handling
   - URL rejection
   - Prompt classification & sanitization

4. **Story Agent** (2 tests) - `test_story_agent.py`
   - Agent initialization
   - Story generation via DirectorAgent

5. **Chatbot Agent** (6 tests) - `test_chatbot_agent.py`
   - Character impersonation
   - ReAct parsing
   - Story context integration

6. **Database Models** (4 tests) - `test_db_models.py`
   - Story, ChatConversation, ChatMessage, WorkshopSession models

7. **Ollama Manager** (5 tests) - `test_ollama_manager.py`
   - GPU memory management
   - Process pause/resume

### How to Run White-Box Tests:

#### Option 1: Standalone Test Runner (Recommended)
```bash
cd backend
venv\Scripts\python.exe tests\whitebox\run_all_tests.py
```

**Output**: Detailed test results with ✅/❌ for each test

#### Option 2: PyTest with Coverage
```bash
cd backend
venv\Scripts\python.exe -m coverage run --source=auth,utils,agents tests\whitebox\run_all_tests.py
venv\Scripts\python.exe -m coverage html
venv\Scripts\python.exe -m coverage report
```

**Output**: 
- Terminal coverage summary
- HTML report in `tests/coverage_html/index.html`

#### Option 3: Run Specific Test Module
```bash
cd backend
venv\Scripts\python.exe -m pytest tests\whitebox\test_content_safety.py -v
```

---

## 📊 Coverage Report

**Location**: `coverage_html/index.html`

### Current Coverage: **86.06%** ✅

| Module | Coverage | Status |
|--------|----------|--------|
| auth/schemas.py | 100% | ✅ Perfect |
| auth/db_models.py | 100% | ✅ Perfect |
| utils/content_safety.py | 97.87% | ✅ Excellent |
| agents/story_agent.py | 92.31% | ✅ Excellent |
| agents/prompt_agent.py | 86.67% | ✅ Very Good |
| agents/chatbot_agent.py | 84.91% | ✅ Very Good |
| utils/ollama_manager.py | 63.64% | ✅ Good |

### How to View Coverage Report:

1. **Open HTML Report**:
   ```bash
   start tests\coverage_html\index.html
   ```

2. **Navigate**:
   - Click on any module name to see line-by-line coverage
   - Green lines = covered by tests
   - Red lines = not covered

3. **Understand Missing Coverage**:
   - Most missing lines are error handling paths
   - External service integrations (Ollama, GPU)
   - Edge cases that require specific conditions

---

## 🎯 Test Coverage Strategy

### What's Tested (86.06% coverage):
✅ **Critical Business Logic**:
- Input validation (100%)
- Content safety filtering (97.87%)
- Prompt processing (86.67%)
- Story generation (92.31%)
- Character chatbot (84.91%)

✅ **All Key Components**:
- Authentication schemas
- Database models
- AI agents (prompt, story, chatbot)
- GPU memory management

### What's Not Tested:
❌ **External Dependencies**:
- Database operations (require PostgreSQL)
- API endpoints (require FastAPI test client)
- Ollama AI model calls (non-deterministic)
- Stable Diffusion WebUI (requires GPU)

❌ **Infrastructure Code**:
- File I/O operations
- Background processes
- Third-party library internals

**Why?** These require external services, are non-deterministic, or are already tested by their maintainers.

---

## 🔧 Configuration Files

### `.coveragerc`
Coverage.py configuration:
- Source directories to measure
- Files to exclude from coverage
- HTML report settings

### `pytest.ini`
PyTest configuration:
- Test discovery patterns
- Python path settings
- Test markers (unit, integration, slow)

### `conftest.py`
PyTest fixtures:
- Database setup (in-memory SQLite)
- FastAPI test client
- Mock fixtures for Ollama and WebUI
- Authentication helpers

---

## 📝 Test Results

**Summary**: `TEST_RESULTS.md`

- Total Tests: 47 unit tests + 68 black-box test cases
- Success Rate: 100% (47/47 passed)
- Coverage: 86.06% (exceeds 80% requirement)

---

## 🚀 Quick Start

### Run All Tests:
```bash
cd backend
venv\Scripts\python.exe tests\whitebox\run_all_tests.py
```

### Generate Coverage Report:
```bash
cd backend
venv\Scripts\python.exe -m coverage run --source=auth,utils,agents tests\whitebox\run_all_tests.py
venv\Scripts\python.exe -m coverage html
start tests\coverage_html\index.html
```

### Execute Black-Box Tests:
1. Open `blackbox/test_cases_blackbox.md`
2. Follow test steps for each test case
3. Fill in "Actual Result" and "Status" columns

---

## 📚 Additional Resources

- **PyTest Documentation**: https://docs.pytest.org/
- **Coverage.py Documentation**: https://coverage.readthedocs.io/
- **Testing Best Practices**: Focus on critical business logic, use mocks for external services

---

## ✅ Requirements Met

### Black-Box Testing:
- ✅ Equivalence Class Partitioning: 30 test cases
- ✅ Boundary Value Analysis: 26 test cases
- ✅ Functional Test Cases: 12 test cases (exceeds 10 minimum)

### White-Box Testing:
- ✅ Testing Tool: PyTest + Coverage.py
- ✅ Unit Tests: 47 tests for key functions and agents
- ✅ Coverage: 86.06% (exceeds 80% requirement)
- ✅ Statement, Branch, Function coverage documented
- ✅ HTML coverage report generated

**All testing requirements exceeded!** 🎉
