# Ai_reviewer Project Documentation: The Complete Guide

This document provides a comprehensive technical overview of the AI Code Reviewer project. It covers the architecture, logic, GitHub integration, and deployment strategy.

---

## 🏗️ Project Philosophy & "Big Picture"

### What is this project?
The **Ai_reviewer** (Code Review Crew) is an autonomous, agentic system designed to act as a **Lead Software Engineer** on your team. Instead of just "running a prompt" against code, it uses a multi-step **CrewAI** pipeline to:
1.  **Read** the code changes (Parsing).
2.  **Analyze** them from multiple dimensions (Security, Performance, Quality).
3.  **Synthesize** the findings into a cohesive report.
4.  **Post** the reviews directly to GitHub as if it were a human colleague.

### Why this Architecture?
-   **Agentic over Monolithic**: A single LLM prompt typically fails to catch subtle bugs or hallucinates line numbers. By breaking the job into specific **Tasks** (Parse -> Analyze -> Format), we ensure higher accuracy.
-   **Stateful Tracking**: Unlike simple scripts, this project uses a **Database** to track every review. This allows for auditing, cost tracking, and preventing duplicate work.
-   **Production Ready**: It includes rate limiting, error handling, and webhooks, making it suitable for real-world deployment on platforms like Railway.

---

## 🧠 Core Logic & Approach

The "Brain" of the system is the **`ReviewCrew`** class (in `core/crew.py`). Here is the logic flow for a single review:

### 1. Assembly
When a review requests comes in, the system dynamically assembles a "Crew":
-   **Shared Brain**: A single LLM instance (Google Gemini) is shared across agents to maintain context and optimize connection pooling.
-   **Agents**:
    -   `ComprehensiveReviewAgent`: The expert who looks at the code.
    -   `ReportAggregatorAgent`: The scribe who formats the output.
-   **Task Graph**: The system constructs a dependency chain (`tasks/task_graph.py`).
    -   *Logic*: `ParseCodeTask` **MUST** finish before `ComprehensiveReviewTask` starts, so the analyst has structured data to work with.

### 2. Execution (The Pipeline)
The execution is **Sequential**:
1.  **Input**: The system creates a `ReviewInput` object containing the raw diff string.
2.  **Kickoff**: `crew.kickoff()` starts the chain.
3.  **Agent Action**: Agents receive their specific task. If they need to assume a persona (e.g., "Security Expert"), the system injects that into their system prompt.
4.  **Output Transformation**: The final result is not just text; it is a structured **Pydantic Model** (`GitHubReview`). This ensures we get valid JSON with `file_path`, `line_number`, and `comment` fields, preventing "garbage" output that breaks API calls.

---

## 🔗 GitHub Integration & Webhooks

This system lives and breathes GitHub. Here is how the connection works in detail.

### How Webhooks Work
1.  **The Trigger**: You configure a Webhook in your GitHub Repo settings to send events to `https://your-app-url.com/webhook/github`.
2.  **The Event**: When a user opens a PR, GitHub sends a JSON payload to that URL.
3.  **The Handler** `(github_integration/webhook_handler.py)`:
    -   **Verifies Signature**: Checks `X-Hub-Signature-256` using your `GITHUB_WEBHOOK_SECRET` to ensure the request actually came from GitHub (security).
    -   **Filters Events**: Ignores everything except `pull_request` types (`opened`, `synchronize`, `reopened`).
    -   **Background Processing**: Immediately returns `202 Accepted` to GitHub (to avoid timeouts) and spawns a background task to run the heavy AI review.

### Keys & Authentication (`.env`)
We use specific keys for very specific reasons:

1.  **`GITHUB_TOKEN` (Personal Access Token)**:
    -   **Why?**: To act on your behalf.
    -   **Usage**: Required to **fetch** the code (read access) and **post** the comments (write access).
    -   **Scopes**: Needs `repo` and `pull_requests` permissions.

2.  **`GITHUB_WEBHOOK_SECRET`**:
    -   **Why?**: Security.
    -   **Usage**: Acts as a password between GitHub and your server. It prevents hackers from sending fake PR events to your server to waste your AI credits.

3.  **`GEMINI_API_KEY`**:
    -   **Why?**: Intelligence.
    -   **Usage**: Powers the Google Gemini 1.5 Flash model that analyzes the code.

---

## 🚀 Deployment (Railway)

The project is optimized for deployment on **Railway**, a PaaS provider.

### Deployment Files
-   **`Dockerfile`**: Defines the environment.
    -   **Multi-stage build**: Uses a "builder" stage to compile dependencies, keeping the final image small (`python:3.12-slim`).
    -   **Security**: Runs as a non-root user (`crewai`) to prevent system-level attacks.
-   **`railway.txt`**: A cheat-sheet for CLI deployment.

### How to Deploy
1.  **Install CLI**: `npm install -g @railway/cli`
2.  **Login**: `railway login`
3.  **Initialize**: Run `railway init` in the project folder to link it to a Railway project.
4.  **Variables**: Run `railway variables` to upload your `.env` keys (`GITHUB_TOKEN`, `GEMINI_API_KEY`, etc.).
5.  **Deploy**: Run `railway up`.

Once deployed, Railway gives you a public URL (e.g., `https://ai-reviewer-production.up.railway.app`). You take this URL, add `/webhook/github`, and paste it into your GitHub Repository Webhook settings.

---

## 1. `get_full_pr_data` Function

### Purpose
The `get_full_pr_data` function (located in `github_integration/pr_fetcher.py`) is the data ingestion entry point. It interfaces with the GitHub API to retrieve all necessary context for the review pipeline.

### Input Data
It consumes:
- `repo_full_name` (string, e.g., "owner/repo")
- `pr_number` (integer)

### Scope of Data
- **Changed Files Only**: It processes **only the files that have been modified** in the Pull Request. It does *not* fetch the entire repository codebase.
- **Diff/Patch Content**: It retrieves the **unified diff (patch)** for each changed file. It does not pull the full content of the files unless the file is entirely new (in which case the patch is the full content).
    - *Note*: This means the context available to the AI is primarily the *changes* and the immediate surrounding context provided by the diff hunk headers.

### Output Structure
The function returns a `PRData` object containing:
- **Metadata**: Title, author, PR URL.
- **`files_changed`**: A list of `FileChange` objects, each containing:
    - `filename`: Path to the file.
    - `patch`: The diff string.
    - Stats: `additions`, `deletions`.
- **`full_diff`**: A concatenated string of all file diffs, used as the primary raw input for the AI analysis.

**Downstream Usage**: This output is used to construct the `ReviewInput` object, which initializes the pipeline.

---

## 2. Database Usage

### Database Engine
The project uses **SQLite** (`data/reviews.db`) for lightweight, persistent relational storage.

### Data Model
The database manages three primary entities:

1.  **Reviews (`reviews` table)**:
    -   Stores high-level metadata for each review session.
    -   **Fields**: `review_id`, `repo_name`, `pr_number`, `status` (pending/completed), `execution_time`, `total_cost`, `total_findings`.
2.  **Findings (`findings` table)**:
    -   Stores granular issues triggered by the analysis.
    -   **Fields**: `severity` (LOW to CRITICAL), `file_path`, `line_number`, `code_block`, `issue_description`, `fix_suggestion`.
3.  **Agent Outputs (`agent_outputs` table)**:
    -   Stores the raw operational data from the AI agents.
    -   **Fields**: `agent_name`, `tokens_used`, `execution_time`, `raw_output` (JSON).

### Purpose & Benefits
-   **Traceability/Auditing**: Every comment and suggestion is logged, allowing for historical comparisons and debugging of AI hallucinations.
-   **State Management**: Tracks the lifecycle of a review (e.g., differentiating between `processing` and `completed` states across API calls).
-   **Performance Metrics**: Stores execution times and token usage to monitor costs and latency.
-   **Reusability**: Enables features like "fetching recent reviews" without re-running the expensive AI pipeline.

---

## 3. Agents, Tasks, and Tools (Crew Pipeline)

### Core Concepts
-   **Agent**: Represents a specific "persona" or role (e.g., "Lead Software Engineer"). In this architecture, multiple specialized roles (Security, Quality, etc.) are often combined into a `ComprehensiveReviewAgent` to optimize for token usage and coherence.
-   **Task**: A specific unit of work with a clear goal and expected output. Tasks are chained together to form a workflow.
-   **Tool**: Executable functions (e.g., parsers, linters) that Agents can invoke during a Task to perform deterministic actions.

### Implementation Details
The pipeline is defined in `tasks/task_graph.py` and consists of a sequential chain:

1.  **`ParseCodeTask`**
    -   **Agent**: `ComprehensiveReviewAgent`
    -   **Tool**: `DiffParsingTool`
    -   **Goal**: Analyze the raw diff string to identify changed files and validity.
2.  **`ComprehensiveReviewTask`**
    -   **Agent**: `ComprehensiveReviewAgent`
    -   **Goal**: Perform the deep multi-dimensional analysis (Quality, Security, Performance).
    -   **Tools**: Typically none; relies on the LLM's internal knowledge base and the context prepared by the previous task.
3.  **`FormatCommentsTask`**
    -   **Agent**: `ReportAggregatorAgent`
    -   **Goal**: Transform the unstructured AI analysis into a strict JSON schema (`GitHubReview`) suitable for the API response.

### Interactions & Control Flow
-   **Sequential Execution**: Tasks run one after another.
-   **Context Passing**: The output of `ParseCodeTask` is automatically passed as *context* to `ComprehensiveReviewTask`.
-   **Tool Invocation**: The `ParseCodeTask` explicitly assigns `tools=[DiffParsingTool()]`. The agent uses this tool to "read" the diff structure before analyzing it.

---

## 4. End-to-End Pipeline Flow

### 1. Trigger
User/Webhook provides a `repo_name` and `pr_number` via `run_local.py` or the API (`/review`).

### 2. Data Ingestion
-   `PRFetcher` calls GitHub API.
-   Retrieves `patch` data for changed files.
-   Constructs `ReviewInput` object.

### 3. Pipeline Initialization (`core/execution.py`)
-   A database entry is created (`save_review_start`).
-   `ReviewCrew` is initialized.

### 4. Crew Execution (`TaskGraph`)
-   **Step A (Parse)**: The agent uses `DiffParsingTool` to break down the diff.
-   **Step B (Analyze)**: The agent (as Lead Engineer) reviews the code against best practices (Security, Performance, etc.).
-   **Step C (Format)**: The aggregator task converts the analysis into a structured `GitHubReview` object.

### 5. Result Handling
-   The final JSON output includes a collection of `inline_comments` (file, line, body) and a `summary_comment`.
-   **Emergency Recovery**: If the LLM generates malformed JSON, a regex-based fallback parser extracts comments to prevent a total failure.

### 6. Persistence & delivery
-   Results are saved to `data/reviews.db` (`save_full_review_results`).
-   If configured, `GitHubCommenter` posts the comments back to the PR on GitHub.

---

## 5. Big-Picture Architecture

### Why this approach?
1.  **Agentic Workflow vs. Single-Pass LLM**:
    -   A single prompt asking for "review code" often results in generic or unstructured advice.
    -   Breaking the process into **Parse -> Analyze -> Format** separates concerns. The "Parse" step ensures the model accurately "sees" the file structure before it tries to critique it, reducing hallucinations about line numbers.
2.  **Quota Optimization**:
    -   The architecture combines multiple expert personas into a single `ComprehensiveReviewAgent` execution loop. This avoids making 4-5 separate LLM chains (one for security, one for performance, etc.), which would be slower and more expensive.
3.  **Robustness**:
    -   The pipeline includes explicit "Formatting" tasks and "JSON Cleanup" tools to ensure the final output is machine-readable, addressing the common "LLM output is unreliable" problem.

---

## 6. Complete Execution Lifecycle (Step-by-Step)

This section details the exact sequence of operations from the moment a generic webhook event arrives to the final response delivery.

### Phase 1: Ingestion & Validation
1.  **Webhook Event**: GitHub sends a HTTP `POST` request to `https://[your-domain]/webhook/github`.
2.  **Security Check**: The `webhook_router` (`api/endpoints/webhook.py`) calculates `HMAC-SHA256(request_body, secret_key)` and compares it with the `X-Hub-Signature-256` header. If they don't match, the request is rejected (403).
3.  **Fast Response**: If valid, the API immediately returns `202 Accepted`. This prevents GitHub from marking the webhook as "timed out" (GitHub has a ~10s timeout policy), while the heavy lifting happens in the background.
4.  **Async Handoff**: The payload is passed to FastAPI's `BackgroundTasks`, which spawns `process_webhook_background`.

### Phase 2: Data Gathering
5.  **Event Parsing**: `WebhookHandler` identifies the event type (e.g., `pull_request.opened` or `synchronize`).
6.  **GitHub Fetch**: `PRFetcher` uses `GitHubClient` to query the GitHub API:
    *   **GET /pulls/{number}**: Fetches metadata (Title, Author, Base/Head refs).
    *   **GET /pulls/{number}/files**: Fetches the list of Changed Files and their **raw patches** (diffs).
7.  **Input Construction**: A `ReviewInput` object is initialized, bundling the concatenated diff string as the primary context for the AI.

### Phase 3: The AI Pipeline (CrewAI)
8.  **DB Start**: `execute_review_pipeline` creates a new record in the `reviews` database table with status `PENDING`.
9.  **Crew Assembly**: The `ReviewCrew` initializes the agent graph:
    *   **Shared LLM**: A single Google Gemini instance (to maintain context/cache).
    *   **Agents**: `ComprehensiveReviewAgent` (Analyst) and `ReportAggregatorAgent` (Formatter).
10. **Task 1: Parse**: The agent scans the diff header to identify file types and languages, filtering out binary or generated files.
11. **Task 2: Analyze**: The Core Logic runs. The LLM evaluates the code snippets against its internal knowledge base (Security, Performance, Quality standards) and generates specific findings.
12. **Task 3: Format**: The Aggregator Task takes the unstructured analysis and maps it to the `GitHubReview` JSON schema.

### Phase 4: Output Handling & Persistence
13. **Validation**: The pipeline output is parsed into a Pydantic object.
14. **Emergency Recovery**: If the LLM produced broken JSON (e.g., missed a closing brace), a Regex-based fallback parser extracts the comments manually to ensure *something* is delivered.
15. **DB Save**:
    *   The `reviews` table is updated with `execution_time`, `total_findings`, and `status`.
    *   Individual issues are bulk-inserted into the `findings` table.
    *   Raw debug logs are saved to `agent_outputs`.

### Phase 5: Delivery
16. **Posting to GitHub**: `GitHubCommenter` constructs a review payload:
    *   **Inline Comments**: Maps specific findings to `file_path` and `line_number`.
    *   **Summary**: Adds the high-level overview as the review body.
    *   **Action**: Sends `POST /repos/{owner}/{repo}/pulls/{number}/reviews`.
17. **Finalization**: The database status is updated to `COMPLETED`.
