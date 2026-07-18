# Black-Box Test Cases - personalized-ai-storybook

**Project**: personalized-ai-storybook - AI-Powered Children's Storybook Generator  
**Testing Type**: Black-Box Testing  
**Date**: December 9, 2025  
**Tester**: QA Team

---

## Table of Contents
1. [Equivalence Class Partitioning Test Cases](#1-equivalence-class-partitioning)
2. [Boundary Value Analysis Test Cases](#2-boundary-value-analysis)
3. [Functional Test Cases](#3-functional-test-cases)

---

## 1. Equivalence Class Partitioning

### 1.1 User Registration - Username Input

| Test Case ID | Input Class | Test Data | Expected Result | Priority |
|--------------|-------------|-----------|-----------------|----------|
| **TC-ECP-001** | Valid username (3-50 chars, alphanumeric) | "john_doe" | Registration successful | High |
| **TC-ECP-002** | Too short username (<3 chars) | "ab" | Error: "Username must be at least 3 characters long" | High |
| **TC-ECP-003** | Too long username (>50 chars) | "a" * 51 | Error: "Username must be less than 50 characters" | High |
| **TC-ECP-004** | Empty username | "" | Error: Validation failure | High |

### 1.2 User Registration - Password Input

| Test Case ID | Input Class | Test Data | Expected Result | Priority |
|--------------|-------------|-----------|-----------------|----------|
| **TC-ECP-005** | Valid password (6-72 bytes) | "password123" | Registration successful | High |
| **TC-ECP-006** | Too short password (<6 chars) | "pass1" | Error: "Password must be at least 6 characters long" | High |
| **TC-ECP-007** | Too long password (>72 bytes) | "a" * 73 | Error: "Password is too long (maximum 72 bytes)" | High |
| **TC-ECP-008** | Empty password | "" | Error: Validation failure | High |

### 1.3 User Registration - Email Input

| Test Case ID | Input Class | Test Data | Expected Result | Priority |
|--------------|-------------|-----------|-----------------|----------|
| **TC-ECP-009** | Valid email format | "user@example.com" | Registration successful | High |
| **TC-ECP-010** | Invalid email (no @) | "userexample.com" | Error: Invalid email format | High |
| **TC-ECP-011** | Invalid email (no domain) | "user@" | Error: Invalid email format | High |
| **TC-ECP-012** | Empty email | "" | Error: Validation failure | High |

### 1.4 Story Prompt Processing - Prompt Type

| Test Case ID | Input Class | Test Data | Expected Result | Priority |
|--------------|-------------|-----------|-----------------|----------|
| **TC-ECP-013** | Short meaningful prompt (3-10 words) | "boy and girl" | Prompt enhanced and story generated | High |
| **TC-ECP-014** | Normal prompt (10-50 words) | "A curious astronaut explores a forgotten planet" | Prompt processed and story generated | High |
| **TC-ECP-015** | Long prompt (>50 words) | 100-word detailed story description | Prompt summarized to ~50 words | Medium |
| **TC-ECP-016** | Invalid prompt (URL) | "https://google.com" | Error: Invalid prompt | High |
| **TC-ECP-017** | Nonsense prompt (<3 words, meaningless) | "asdf" | Error: Meaningless prompt | High |
| **TC-ECP-018** | Empty prompt | "" | Error: Missing prompt | High |
| **TC-ECP-019** | Only numbers/symbols | "12345!@#$%" | Error: Invalid prompt | High |

### 1.5 Content Safety - Prompt Filtering

| Test Case ID | Input Class | Test Data | Expected Result | Priority |
|--------------|-------------|-----------|-----------------|----------|
| **TC-ECP-020** | Safe child-friendly content | "A brave knight saves a kingdom" | Content approved, story generated | High |
| **TC-ECP-021** | Blocked keyword (explicit) | "A story about naked people" | Error: Inappropriate content blocked | Critical |
| **TC-ECP-022** | Blocked keyword (violence) | "A story with blood and murder" | Error: Inappropriate content blocked | Critical |
| **TC-ECP-023** | Blocked keyword (drugs) | "Kids drinking alcohol" | Error: Inappropriate content blocked | Critical |
| **TC-ECP-024** | Warning keyword (needs extra safety) | "A scary monster in the dark" | Content allowed with extra safety filters | Medium |

### 1.6 Image Generation Mode

| Test Case ID | Input Class | Test Data | Expected Result | Priority |
|--------------|-------------|-----------|-----------------|----------|
| **TC-ECP-025** | Standard image generation | mode="simple", no photo | Standard images generated | High |
| **TC-ECP-026** | Personalized image generation | mode="personalized", user photo provided | Personalized images with user's face | High |
| **TC-ECP-027** | No image generation (guest user) | Guest user, generate_images=false | Text-only story generated | Medium |

### 1.7 Workshop Mode

| Test Case ID | Input Class | Test Data | Expected Result | Priority |
|--------------|-------------|-----------|-----------------|----------|
| **TC-ECP-028** | New Idea mode | mode="new_idea" | Workshop session starts for new story | High |
| **TC-ECP-029** | Improvement mode | mode="improvement" | Workshop session starts for story improvement | High |
| **TC-ECP-030** | Invalid mode | mode="invalid_mode" | Error: Invalid mode | Medium |

---

## 2. Boundary Value Analysis

### 2.1 Username Length Boundaries

| Test Case ID | Boundary | Test Data (Length) | Expected Result | Priority |
|--------------|----------|-------------------|-----------------|----------|
| **TC-BVA-001** | Below minimum | "ab" (2 chars) | Error: Too short | High |
| **TC-BVA-002** | Minimum valid | "abc" (3 chars) | Registration successful | High |
| **TC-BVA-003** | Just above minimum | "abcd" (4 chars) | Registration successful | High |
| **TC-BVA-004** | Just below maximum | "a" * 49 (49 chars) | Registration successful | High |
| **TC-BVA-005** | Maximum valid | "a" * 50 (50 chars) | Registration successful | High |
| **TC-BVA-006** | Above maximum | "a" * 51 (51 chars) | Error: Too long | High |

### 2.2 Password Length Boundaries

| Test Case ID | Boundary | Test Data (Length) | Expected Result | Priority |
|--------------|----------|-------------------|-----------------|----------|
| **TC-BVA-007** | Below minimum | "pass1" (5 chars) | Error: Too short | High |
| **TC-BVA-008** | Minimum valid | "pass12" (6 chars) | Registration successful | High |
| **TC-BVA-009** | Just above minimum | "pass123" (7 chars) | Registration successful | High |
| **TC-BVA-010** | Just below maximum | "a" * 71 (71 bytes) | Registration successful | High |
| **TC-BVA-011** | Maximum valid | "a" * 72 (72 bytes) | Registration successful | High |
| **TC-BVA-012** | Above maximum | "a" * 73 (73 bytes) | Error: Too long | High |

### 2.3 Story Prompt Word Count Boundaries

| Test Case ID | Boundary | Test Data (Word Count) | Expected Result | Priority |
|--------------|----------|----------------------|-----------------|----------|
| **TC-BVA-013** | Just below truncation limit | 69-word prompt | Prompt processed fully | Medium |
| **TC-BVA-014** | At truncation limit | 70-word prompt | Prompt processed fully | Medium |
| **TC-BVA-015** | Above truncation limit | 71-word prompt | Prompt truncated to 70 words | Medium |
| **TC-BVA-016** | Very long prompt | 150-word prompt | Prompt truncated to 70 words | Medium |

### 2.4 Scene Count Boundaries

| Test Case ID | Boundary | Test Data (Scene Count) | Expected Result | Priority |
|--------------|----------|------------------------|-----------------|----------|
| **TC-BVA-017** | Minimum scenes | writer_max_scenes=1 | Story with 1 scene generated | Low |
| **TC-BVA-018** | Below default | writer_max_scenes=2 | Story with 2 scenes generated | Low |
| **TC-BVA-019** | Default scenes | writer_max_scenes=3 | Story with 3 scenes generated | High |
| **TC-BVA-020** | Above default | writer_max_scenes=4 | Story with 4 scenes generated | Low |
| **TC-BVA-021** | High scene count | writer_max_scenes=5 | Story with 5 scenes generated | Low |

### 2.5 Age Range Boundaries (Implicit in Content Safety)

| Test Case ID | Boundary | Test Data (Age) | Expected Result | Priority |
|--------------|----------|----------------|-----------------|----------|
| **TC-BVA-022** | Below minimum age | Content for age 2 | Content filtered for safety | Medium |
| **TC-BVA-023** | Minimum target age | Content for age 3 | Age-appropriate content | High |
| **TC-BVA-024** | Mid-range age | Content for age 7 | Age-appropriate content | High |
| **TC-BVA-025** | Maximum target age | Content for age 12 | Age-appropriate content | High |
| **TC-BVA-026** | Above maximum age | Content for age 13+ | Content still child-safe | Medium |

---

## 3. Functional Test Cases

### TC-FUNC-001: User Registration with Valid Credentials

**Module**: Authentication  
**Test Type**: Functional  
**Priority**: High

**Preconditions**:
- Backend API is running
- Database is accessible
- Email does not already exist in database

**Test Steps**:
1. Navigate to registration endpoint `/api/auth/register`
2. Submit POST request with valid data:
   ```json
   {
     "email": "testuser@example.com",
     "username": "testuser123",
     "password": "securepass123"
   }
   ```
3. Verify response status code
4. Verify access token is returned
5. Verify user data is returned in response

**Expected Result**:
- Status code: 201 Created
- Response contains `access_token`, `token_type`, and `user` object
- User is created in database
- Password is hashed (not stored in plaintext)

**Actual Result**: _[To be filled during execution]_

**Status**: _[Pass/Fail]_

---

### TC-FUNC-002: User Login with Correct Credentials

**Module**: Authentication  
**Test Type**: Functional  
**Priority**: High

**Preconditions**:
- User account exists in database
- User credentials are known

**Test Steps**:
1. Navigate to login endpoint `/api/auth/login`
2. Submit POST request with credentials:
   ```json
   {
     "email": "testuser@example.com",
     "password": "securepass123"
   }
   ```
3. Verify response status code
4. Verify access token is returned
5. Use token to access protected endpoint `/api/auth/me`

**Expected Result**:
- Status code: 200 OK
- Response contains valid JWT access token
- Token can be used to authenticate subsequent requests
- User information is returned

**Actual Result**: _[To be filled during execution]_

**Status**: _[Pass/Fail]_

---

### TC-FUNC-003: Story Generation from Simple Prompt

**Module**: Story Generation  
**Test Type**: Functional  
**Priority**: Critical

**Preconditions**:
- User is authenticated
- Ollama service is running
- Backend API is running

**Test Steps**:
1. Authenticate user and obtain access token
2. Submit POST request to `/api/generate` with:
   ```json
   {
     "prompt": "A brave little mouse goes on an adventure",
     "generate_images": false,
     "use_personalized_images": false,
     "mode": "simple"
   }
   ```
3. Wait for story generation to complete
4. Verify response contains story data
5. Verify story has title, scenes, and characters

**Expected Result**:
- Status code: 200 OK
- Response contains complete story JSON with:
  - `title` (string)
  - `scenes` (array with 3 scenes)
  - `characters` (array)
  - Each scene has `scene_number`, `text`, `image_description`
- Story is saved to database
- PDF is generated

**Actual Result**: _[To be filled during execution]_

**Status**: _[Pass/Fail]_

---

### TC-FUNC-004: Story Generation with Personalized Images

**Module**: Personalized Image Generation  
**Test Type**: Functional  
**Priority**: High

**Preconditions**:
- User is authenticated
- WebUI API is running on port 7860
- User photo is available (base64 encoded)
- Ollama service is running

**Test Steps**:
1. Authenticate user and obtain access token
2. Prepare user photo as base64 string
3. Submit POST request to `/api/generate` with:
   ```json
   {
     "prompt": "I am a superhero saving the city",
     "generate_images": true,
     "use_personalized_images": true,
     "user_photo": "<base64_encoded_image>",
     "mode": "personalized"
   }
   ```
4. Wait for story and image generation to complete
5. Verify images contain user's facial features

**Expected Result**:
- Status code: 200 OK
- Story generated with 3 scenes
- Each scene has `image_path` and `image_url`
- Generated images show user's face in story scenes
- Images are saved in `generated/images/` directory
- Ollama is paused during image generation

**Actual Result**: _[To be filled during execution]_

**Status**: _[Pass/Fail]_

---

### TC-FUNC-005: Content Safety Rejection of Inappropriate Prompts

**Module**: Content Safety  
**Test Type**: Functional  
**Priority**: Critical

**Preconditions**:
- Backend API is running
- Content safety filters are active

**Test Steps**:
1. Submit POST request to `/api/generate` with inappropriate prompt:
   ```json
   {
     "prompt": "A story with violence and blood",
     "generate_images": false
   }
   ```
2. Verify request is rejected
3. Test with multiple blocked keywords:
   - "naked people"
   - "scary horror nightmare"
   - "drugs and alcohol"

**Expected Result**:
- Status code: 400 Bad Request
- Error message indicates inappropriate content
- No story is generated
- Content is blocked before reaching story generation agents

**Actual Result**: _[To be filled during execution]_

**Status**: _[Pass/Fail]_

---

### TC-FUNC-006: Character Chatbot Conversation

**Module**: Chatbot  
**Test Type**: Functional  
**Priority**: High

**Preconditions**:
- Story has been generated and saved to database
- Story contains characters
- User has story_id

**Test Steps**:
1. Get story_id from previous story generation
2. Identify character name from story (e.g., "brave mouse")
3. Submit POST request to `/api/chat` with:
   ```json
   {
     "story_id": 123,
     "character_name": "brave mouse",
     "user_message": "Hello! What was your favorite part of the adventure?"
   }
   ```
4. Verify character responds in-character
5. Send follow-up message to test conversation flow

**Expected Result**:
- Status code: 200 OK
- Response contains character's reply
- Reply is contextually relevant to the story
- Character stays in-character
- No conversation history is saved (stateless)

**Actual Result**: _[To be filled during execution]_

**Status**: _[Pass/Fail]_

---

### TC-FUNC-007: Workshop Session - New Idea Mode

**Module**: Idea Workshop  
**Test Type**: Functional  
**Priority**: High

**Preconditions**:
- User is authenticated (or guest)
- Backend API is running

**Test Steps**:
1. Start workshop session with POST to `/api/workshop/start`:
   ```json
   {
     "mode": "new_idea"
   }
   ```
2. Verify initial assistant message is received
3. Send user message to `/api/workshop/chat`:
   ```json
   {
     "session_id": 1,
     "user_message": "I want a story about a dragon and a princess"
   }
   ```
4. Continue conversation with agent
5. Verify agent asks for story requirements (characters, theme, etc.)

**Expected Result**:
- Session created with unique session_id
- Initial message: "Welcome to New Idea Mode!"
- Agent asks clarifying questions about story
- Conversation history is saved to database
- Metadata tracks collected requirements

**Actual Result**: _[To be filled during execution]_

**Status**: _[Pass/Fail]_

---

### TC-FUNC-008: Workshop Session - Story Improvement Mode

**Module**: Idea Workshop  
**Test Type**: Functional  
**Priority**: High

**Preconditions**:
- User is authenticated (or guest)
- User has existing story text (max 300 words)

**Test Steps**:
1. Start workshop session with POST to `/api/workshop/start`:
   ```json
   {
     "mode": "improvement"
   }
   ```
2. Verify initial message asks for story text
3. Submit existing story (under 300 words)
4. Agent provides improvement suggestions
5. Request story generation with improvements

**Expected Result**:
- Session created successfully
- Initial message: "Please paste your story below (maximum 300 words)"
- Agent analyzes story and suggests improvements
- Improved story can be generated
- Original story is preserved in database

**Actual Result**: _[To be filled during execution]_

**Status**: _[Pass/Fail]_

---

### TC-FUNC-009: Guest User Story Generation (Text Only)

**Module**: Story Generation + Authentication  
**Test Type**: Functional  
**Priority**: Medium

**Preconditions**:
- Backend API is running
- No authentication token provided

**Test Steps**:
1. Submit POST request to `/api/generate` WITHOUT authentication token:
   ```json
   {
     "prompt": "A friendly robot helps children learn",
     "generate_images": true,
     "mode": "simple"
   }
   ```
2. Verify request is rejected for image generation
3. Submit same request with `generate_images: false`
4. Verify text-only story is generated

**Expected Result**:
- First request (with images): Status 401 Unauthorized
- Error: "Please login to generate images"
- Second request (text only): Status 200 OK
- Story generated without images
- Story saved with `user_id: null`

**Actual Result**: _[To be filled during execution]_

**Status**: _[Pass/Fail]_

---

### TC-FUNC-010: PDF Export Functionality

**Module**: Story Export  
**Test Type**: Functional  
**Priority**: Medium

**Preconditions**:
- Story has been generated successfully
- Story contains scenes with or without images

**Test Steps**:
1. Generate a complete story with images
2. Verify PDF file is created in `generated/pdfs/` directory
3. Check PDF filename format: `{story_title}_{timestamp}.pdf`
4. Open PDF and verify:
   - Story title is displayed
   - All scenes are included
   - Images are embedded (if generated)
   - Text is readable and formatted

**Expected Result**:
- PDF file is created automatically after story generation
- PDF contains all story content
- Images are properly embedded
- File is accessible via file system
- PDF is well-formatted and readable

**Actual Result**: _[To be filled during execution]_

**Status**: _[Pass/Fail]_

---

### TC-FUNC-011: Invalid Prompt Rejection

**Module**: Prompt Processing  
**Test Type**: Functional  
**Priority**: High

**Preconditions**:
- Backend API is running

**Test Steps**:
1. Submit various invalid prompts:
   - Empty string: `""`
   - Only numbers: `"12345"`
   - Only symbols: `"!@#$%^&*()"`
   - URL: `"https://example.com"`
   - Nonsense: `"asdfghjkl"`
2. Verify each is rejected appropriately

**Expected Result**:
- Status code: 400 Bad Request
- Error message: "Your prompt appears invalid or meaningless"
- No story generation is attempted
- Prompt agent correctly classifies as "invalid" or "nonsense"

**Actual Result**: _[To be filled during execution]_

**Status**: _[Pass/Fail]_

---

### TC-FUNC-012: Duplicate Email Registration Prevention

**Module**: Authentication  
**Test Type**: Functional  
**Priority**: High

**Preconditions**:
- User with email "existing@example.com" already exists in database

**Test Steps**:
1. Attempt to register new user with same email:
   ```json
   {
     "email": "existing@example.com",
     "username": "newuser",
     "password": "password123"
   }
   ```
2. Verify registration is rejected

**Expected Result**:
- Status code: 400 Bad Request
- Error message: "Email already registered"
- No new user is created
- Existing user data is unchanged

**Actual Result**: _[To be filled during execution]_

**Status**: _[Pass/Fail]_

---

## Test Execution Summary

| Category | Total Test Cases | Passed | Failed | Not Executed |
|----------|-----------------|--------|--------|--------------|
| Equivalence Class Partitioning | 30 | - | - | - |
| Boundary Value Analysis | 26 | - | - | - |
| Functional Test Cases | 12 | - | - | - |
| **TOTAL** | **68** | **-** | **-** | **-** |

---

## Notes

- All test cases should be executed in a test environment
- Database should be reset between test runs for consistency
- External services (Ollama, WebUI) must be running for relevant tests
- Actual results and status should be filled during test execution
- Priority levels: Critical > High > Medium > Low
