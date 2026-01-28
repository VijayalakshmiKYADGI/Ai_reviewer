# AI Code Reviewer - System Workflow Documentation

This document explains the end-to-end logic of the AI Code Review system, detailing how a Pull Request (PR) triggers the pipeline and how the review is processed and posted back to GitHub.

## 1. System Trigger
The pipeline can be triggered in two ways:
1.  **GitHub Webhook**: Real-time event when a PR is opened or updated (`github_integration/webhook_handler.py`).
2.  **Local Execution**: Manual run via CLI for testing (`run_local.py`).

## 2. Input Preparation
Regardless of the trigger, the system first prepares a `ReviewInput` object containing:
-   **Repository Name**: e.g., `owner/repo`
-   **PR Number**: e.g., `42`
-   **Diff Content**: The raw git diff of the changes.
-   **Files Changed**: A list of filenames involved in the PR.

**Key File**: `data/models.py` (defines `ReviewInput`)

## 3. Pipeline Orchestration
The core logic resides in `core/execution.py`.
The function `execute_review_pipeline(review_input)` is the main entry point.

### Logic Steps:
1.  **Database Initialization**:
    -   Calls `save_review_start` in `core/results.py`.
    -   Creates a record in the `reviews` table with status `running`.
2.  **Crew Initialization**:
    -   Instantiates `ReviewCrew` from `core/crew.py`.
    -   Calls `crew_runner.kickoff(review_input)`.

## 4. CrewAI Assembly & Execution
The `ReviewCrew` class (`core/crew.py`) orchestrates the AI agents.

### A. Assembly (`assemble` method)
1.  **LLM Configuration**: Initializes Google Gemini (via `ChatGoogleGenerativeAI`) with a shared instance to manage throttling.
2.  **Agent Creation** (`agents/agent_registry.py`):
    -   **Lead Software Engineer** (`ComprehensiveReviewAgent`): The primary agent responsible for analyzing code quality, security, performance, and architecture.
    -   **Technical Report Writer** (`ReportAggregatorAgent`): Responsible for formatting the final output.
3.  **Task Sequence** (`tasks/task_graph.py`):
    -   The system defines a sequential logic flow:
        1.  **Parse Code Task**: analyzing the diff to understand what files changed.
        2.  **Comprehensive Review Task**: The main analysis. The Lead Engineer reviews the code line-by-line using strict criteria.
        3.  **Format Comments Task**: Converts the logical findings into a structured JSON/Pydantic object compatible with GitHub's API.

### B. Execution (`kickoff` method)
-   The `crew.kickoff()` method runs the tasks sequentially.
-   **Crucial Logic**: The system enforces **Structured Output** using Pydantic models (`GitHubReview`). This ensures the AI returns valid data (file paths, line numbers, comments) instead of unstructured text.
-   **Result**: The final output is a `GitHubReview` object containing a list of `InlineComment` objects.

## 5. Result Handling & Storage
Back in `core/execution.py`:

1.  **Result Standardization**:
    -   The system checks if the result is a valid `GitHubReview` object.
    -   It ensures all findings have valid line numbers and file paths.
2.  **Database Persistence**:
    -   Calls `save_full_review_results` in `core/results.py`.
    -   Updates the database record with the final status (`completed`), the execution time, and the serialized findings.

## 6. GitHub Integration (Posting Results)
If running via Webhook or if confirmed in Local Mode:

1.  **Commenter** (`github_integration/commenter.py`):
    -   Receives the `GitHubReview` object.
    -   Formats the **Summary** (posted as the PR body or a top-level comment).
    -   Formats **Inline Comments** (posted on specific lines of the diff).
2.  **API Logic**:
    -   Uses `PyGithub` (wrapped in `GitHubClient`) to interact with the GitHub API.
    -   **Smart Fallback**: If posting inline comments fails (e.g., due to line number mismatches in complex diffs), it falls back to posting a single comprehensive comment on the PR.

## Summary of Data Flow

```mermaid
graph TD
    A[GitHub PR Event] --> B(Webhook / Local Script)
    B --> C{Pipeline Execution}
    C --> D[Initialize DB Record]
    C --> E[Assemble AI Crew]
    
    subgraph "CrewAI Process"
        E --> F[Parse Diff]
        F --> G[Comprehensive Review (Lead Engineer)]
        G --> H[Format Output (Report Writer)]
    end
    
    H --> I[Structured Pydantic Model]
    I --> J[Save to DB]
    I --> K[Post to GitHub API]
```
