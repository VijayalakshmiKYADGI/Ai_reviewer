# Deployment Version History

## Version Format
`vMAJOR.MINOR.PATCH-description`

## Versions

### v2.1.0-hotfix-api-auth (2026-01-21)
**Changes:**
- Fixed API key authentication in GeminiLLM
- Added comprehensive warning suppression
- Added version logging on startup

**Files Modified:**
- `agents/gemini_llm.py` - Fixed Field(default_factory) issue
- `api/main.py` - Added warning filters + version logging

**How to Identify:**
Look for `deployment_info` log with `version=v2.1.0-hotfix-api-auth`

---

### v2.0.0-phase15 (2026-01-20)
**Changes:**
- Integrated CrewAI pipeline into webhook handler
- Added 422 error fallback
- Disabled verbose logging in agents
- Path validation for inline comments

**Files Modified:**
- `github_integration/webhook_handler.py`
- `github_integration/commenter.py`
- All agent files

---

## How to Update Version

When making a new deployment:

1. Edit `api/main.py` line 26:
   ```python
   VERSION = "vX.Y.Z-description"
   ```

2. Update this file with changes

3. Commit and push

4. Check Railway logs for:
   ```
   deployment_info version=vX.Y.Z-description
   ```
