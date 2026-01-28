# Comprehensive AI Review System - Execution Methodology

This document details the exact execution flow, function calls, agent interactions, data inputs, and outputs for every step of the Code Review Pipeline.

## 1. Trigger & Entry Point

### A. Local Execution (`run_local.py`)
-   **Function Call**: `asyncio.run(run_local_review(repo_name, pr_number))`
-   **Step 1**: `PRFetcher.get_full_pr_data`
    -   **Input**: `repo_name` (str), `pr_number` (int)
    -   **Output**: `PRData` object (containing `full_diff`, `files_changed` list)
-   **Step 2**: `ReviewInput` Instantiation
    -   **Input**: Metadata from `PRData`
    -   **Output**: `ReviewInput` Pydantic model

### B. Webhook Execution (`github_integration/webhook_handler.py`)
-   **Function Call**: `WebhookHandler.handle_opened`
-   **Step 1**: Extract payload data (repo, PR number)
-   **Step 2**: `PRFetcher.get_full_pr_data` (Same as local)
-   **Step 3**: `_execute_review_pipeline`
    -   **Input**: `PRData`
    -   **Output**: `GitHubReview` object (after pipeline completion)

---

## 2. Core Execution Pipeline (`core/execution.py`)

**Function**: `execute_review_pipeline(review_input: ReviewInput)`

### Step 1: Database Initialization
-   **Function**: `save_review_start(review_input)`
-   **Input**: `ReviewInput` object
-   **Output**: `review_id` (Integer, Primary Key in `reviews` table)
-   **Action**: Inserts a record with status="running" into the database.

### Step 2: Crew Assembly (`core/crew.py`)
-   **Class**: `ReviewCrew`
-   **Method**: `kickoff(review_input)` -> calls `assemble`
-   **Action**: 
    1.  Initializes **Google Gemini 1.5 Flash** (via `ChatGoogleGenerativeAI`).
    2.  Instantiates Agents from `agents/agent_registry.py`.
    3.  Builds Task Sequence from `tasks/task_graph.py`.

---

## 3. Agent & Task Execution Flow (The "Brain")

The `ReviewCrew` runs tasks **sequentially**.

### Task 1: Parse Code Changes
-   **Task File**: `tasks/parse_code_task.py`
-   **Agent**: **Lead Software Engineer** (`ComprehensiveReviewAgent`)
-   **Goal**: Analyze the raw diff to understand what changed.
-   **Tool Used**: `Diff Parsing Tool` (if enabled) or LLM's internal capability.
-   **Input**: `diff_content` string from `ReviewInput`.
-   **Output**: A structured summary of changed files (e.g., `[{"file": "config.py", "status": "modified"}]`).

### Task 2: Comprehensive Technical Review
-   **Task File**: `tasks/comprehensive_review_task.py`
-   **Agent**: **Lead Software Engineer** (`ComprehensiveReviewAgent`)
-   **Goal**: Perform deep-dive analysis on Quality, Security, Performance, Architecture.
-   **Input**: Output from Task 1 (Parsed Files) + Raw Diff.
-   **Internal Logic**:
    -   The Agent reads the diff line-by-line.
    -   It checks against rules:
        -   **Security**: Hardcoded secrets, injection flaws.
        -   **Quality**: PEP8, naming, docstrings.
        -   **Performance**: Loops, complexity.
    -   **CRITICAL**: It must identify the **exact line number**.
-   **Output**: A `ComprehensiveReviewAnalysis` Pydantic object containing a list of `ReviewFinding` items.
    -   *Example Finding*: `{"file_path": "config.py", "line_number": 4, "severity": "CRITICAL", "message": "Hardcoded DB credentials"}`

### Task 3: Format Findings
-   **Task File**: `tasks/format_comments_task.py`
-   **Agent**: **Technical Report Writer** (`ReportAggregatorAgent`)
-   **Goal**: Convert technical findings into GitHub-ready comments.
-   **Input**: `ComprehensiveReviewAnalysis` object from Task 2.
-   **Action**: 
    -   Filters low-confidence findings.
    -   Formats logic into a friendly "Comment" string.
    -   Generates a high-level **Summary**.
-   **Output**: `GitHubReview` Pydantic object.
    -   Contains: `inline_comments` (List), `summary_comment` (Str), `review_state` (Enum).

---

## 4. Result Handling & Persistence (`core/execution.py`)

**Context**: Back in `execute_review_pipeline` after `crew.kickoff()` returns.

### Step 1: Result Validation
-   The system checks if the output is a valid `GitHubReview` object.
-   If `kickoff` returned raw text (rare failure case), it attempts to parse it into the object.

### Step 2: Database Save
-   **Function**: `save_full_review_results`
-   **Input**: `review_id`, `GitHubReview` object, `execution_time`.
-   **Action**: Updates the DB record to status="completed" and stores the JSON results.

---

## 5. GitHub Integration Phase (`github_integration/commenter.py`)

**Function**: `post_review(repo, pr, review, ...)`

### Step 1: Format Summary
-   **Action**: Posts the `summary_comment` as the main body of the GitHub Review.
-   **Visuals**: Adds emojis/formatting (e.g., "✅ Code Review Summary").

### Step 2: Post Inline Comments
-   **Action**: Iterates through `inline_comments`.
-   **API Call**: `client.create_review(..., comments=[...])`
-   **Logic**:
    -   Maps `file_path` and `line_number` to the GitHub Diff.
    -   **Smart Fallback**: If a line is "out of context" (GitHub API sometimes rejects lines not in the current diff view), it catches the error and posts those findings as a general comment instead of crashing.

### Step 3: Final Status
-   **Action**: Submits the review event.
    -   `APPROVE`: If no issues found.
    -   `REQUEST_CHANGES`: If critical/high issues found.
    -   `COMMENT`: If only nitpicks/suggestions found.

---

## Summary of Data Flow through Functions

1.  `run_local.py` -> `PRFetcher` -> **ReviewInput**
2.  `execute_review_pipeline(ReviewInput)` -> `save_review_start` -> **DB(Running)**
3.  `ReviewCrew.kickoff(ReviewInput)`
    4.  `ParseCodeTask` -> **List[File]**
    5.  `ComprehensiveReviewTask` -> **List[ReviewFinding]**
    6.  `FormatCommentsTask` -> **GitHubReview**
7.  `execute_review_pipeline` -> `save_full_review_results` -> **DB(Completed)**
8.  `GitHubCommenter.post_review(GitHubReview)` -> **GitHub API**
