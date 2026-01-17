# Sample Test Project

This is a **deliberately flawed** project used for end-to-end testing of the [Code Review Crew](https://github.com/your-username/code-review-crew).

**⚠️ WARNING: DO NOT USE THIS CODE IN PRODUCTION.**

It contains intentional:
- Security vulnerabilities (Hardcoded secrets, SQL injection)
- Code quality issues (Linting errors)
- Performance bottlenecks (O(n²) loops)
- Architectural anti-patterns (God objects)

## Usage

This repo works with the Code Review Crew's GitHub Webhook.
Pushing to specific branches triggers automated Pull Requests and Code Reviews.

### Triggers:
- `test-quality` branch -> Triggers Pylint review PR
- `test-security` branch -> Triggers Security review PR
- `test-performance` branch -> Triggers Performance review PR
- `test-architecture` branch -> Triggers Architecture review PR
