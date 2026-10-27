---
name: github-interaction-mirror
description: >-
  Mirror high-value user-agent prompt transactions and technical analyses to a specified
  GitHub issue with automated screening for security and privacy, prompting the
  user for a ticket URL if not yet provided. Filters out routine operational chores
  (e.g., git commits, pushes) that lack substantive analysis. Use this skill whenever a GitHub
  issue URL or issue reference is supplied for tracking, or when requested to
  mirror/log interactions to GitHub.
---

# GitHub Interaction Mirror

Mirror high-value transactions (containing technical analysis, investigations, design decisions, or solutions) to the targeted GitHub issue using `gh issue comment`, with strict security and privacy redaction. Exclude routine operational chores (e.g., git commits, pushes) that lack substantive analysis.

## 1. Cloud Ticket / GitHub Issue Prompting & Detection

1. **Prompting the user at the start:**
   - At the very beginning of the prompt transaction / response (or before commencing actions), check if a target GitHub issue URL or ticket identifier (`https://github.com/owner/repo/issues/123`, `owner/repo#123`, or `#123`) has been specified for this conversation.
   - **If no cloud ticket / issue URL has been provided yet:**
     - Ask the user at the beginning of the prompt/response:
       > *"Please provide the target GitHub issue URL (e.g., `https://github.com/owner/repo/issues/123`) if you would like this interaction to be mirrored to a ticket."*
     - If the user has not provided a ticket, **do NOT post to GitHub**. Mention at the end of the response:
       > *Note: No cloud ticket / GitHub issue supplied; skipping post to GitHub.*
   - **If a ticket URL/ID is provided:** Use it as the destination for mirroring all qualifying transactions in the session.

## 2. Transaction Significance & Content Filtering (Substantive Analysis Threshold)

To prevent cluttering the GitHub issue with routine operational noise, filter transactions before posting:

### Do POST (Substantive Analysis):
- **Technical Investigations & Root Causes:** Explanations of why a bug occurred, system behavior analysis, or debugging conclusions.
- **Architectural & Design Decisions:** Comparisons of implementation alternatives, trade-offs, or configuration strategies.
- **Structured Guides & Solutions:** Concrete how-to solutions, troubleshooting steps, or design explanations.
- Any transaction with enduring reference value for collaborators or for reviewing later across different machines.

### Do NOT POST (Exclude Operational Noise):
- **Routine Operational Commands:** Purely operational actions such as "commit the changes", "push to remote branch", "run tests", or "format files".
- **Action Confirmations Without Analysis:** Short responses that only report that a command, script, or git operation was executed (e.g., "Committed and pushed df1750d to remote").
- **Trivial Exchanges or Simple Acknowledgments:** Turns lacking technical reasoning, code analysis, or problem-solving insights.

## 3. Security & Privacy Screening (MANDATORY BEFORE POSTING)

Before posting any content to a public or team GitHub issue, **screen and redact all sensitive information** from both the user prompt and agent response:

### Information to Screen and Redact:
1. **Credentials & Secrets:**
   - API keys, personal access tokens, OAuth tokens (e.g., `gho_...`, `ghp_...`, `sk-...`, `Bearer ...`).
   - Passwords, secret keys, private SSH keys (`-----BEGIN ... PRIVATE KEY-----`).
2. **Internal Network & Infrastructure:**
   - Private/internal IP addresses (e.g., `10.x.x.x`, `192.168.x.x`, `172.16-31.x.x`, tailscale/VPN IPs like `100.x.x.x`).
   - Internal DNS names, internal URLs, company VPN endpoints.
3. **Personal & System Identifiers:**
   - Absolute local home directories and user names: replace `/home/<username>/` with `~` or `/home/<user>/` if sensitive.
   - Machine hostnames and hardware serial numbers (e.g., serial numbers like `H7YCC...`, MAC addresses).
   - Personal emails, phone numbers, personal names not part of public package authors.

### Redaction Format:
Replace sensitive strings with clear placeholders:
`[REDACTED_TOKEN]`, `[REDACTED_IP]`, `[REDACTED_PASSWORD]`, `[REDACTED_SECRET]`.

## 4. Agent & Model Identifiers

Determine the agent runtime and model being used:
- **Agent name:**
  - Antigravity: `Antigravity`
  - Claude Code: `Claude Code`
  - Other: `<AgentName>`
- **Model label:**
  - Gemini 3.8: `Gemini 3.8`
  - Gemini 4 Argon: `Gemini 4 Argon`
  - Claude Sonnet 5.5: `Sonnet 5.5 Medium`
  - (Adapt to the active model reported in system metadata / user settings)

Example prefix:
```text
Antigravity. Gemini 3.8.
```

## 5. Formatting Contract

Each transaction posted as a comment to the GitHub issue MUST follow this exact structure:

```markdown
*Posted by <Agent Name> (not a human) with <Model Name>.*

<details>
<summary><Screened User Prompt Summary or Full Prompt></summary>

<Continued screened user prompt or logs if long, followed by a separator line if needed>
----

**<Agent Name>. <Model Name>.**

<Screened Agent Response Content>
</details>
```

### Formatting Rules:
1. **Empty Line Requirement:** You MUST leave 1 empty line after `</summary>` before any content, otherwise GitHub issue rendering fails without it.
2. **Short Prompt:** If the user prompt is brief (1-3 sentences), enclose the screened prompt inside `<summary>...</summary>`.
3. **Long Prompt / Logs:** If the user prompt is lengthy (e.g., terminal output, crash logs):
   - Place the first line or a brief title in `<summary>User Request / Logs ...</summary>`.
   - Place the screened text/logs directly beneath `</summary>`, followed by a separator line (`----` or 4 consecutive `-`).
   - Follow with the agent's identification header and screened response inside the `</details>` block.

## 6. Posting via GitHub CLI (`gh`)

Use `gh issue comment` with a temporary file or standard input to avoid shell escaping issues with backticks, quotes, and newlines:

```bash
gh issue comment "<ISSUE_URL_OR_NUMBER>" --body-file /path/to/comment.md
```

Or execute via the companion script (which automatically normalizes `owner/repo#123` to full issue URLs and `#123` to plain numbers):

- **From repository root:**
  ```bash
  hut_10sqft/config/skills/github-interaction-mirror/scripts/post_transaction.sh "<ISSUE_URL_OR_NUMBER>" "<AGENT_NAME>" "<MODEL_NAME>" "/path/to/user_prompt.txt" "/path/to/agent_response.txt"
  ```
- **From within the skill directory** (or installed skill location):
  ```bash
  ./scripts/post_transaction.sh "<ISSUE_URL_OR_NUMBER>" "<AGENT_NAME>" "<MODEL_NAME>" "/path/to/user_prompt.txt" "/path/to/agent_response.txt"
  ```

## 7. Workflow Execution Steps

1. Check if the target GitHub ticket URL is known. If not, prompt the user at the start of the response.
2. Formulate your technical solution / answer.
3. Check the **Substantive Analysis Threshold**:
   - If the user prompt is a routine operational instruction (e.g., asking to commit, push, run commands) or the response lacks substantive technical analysis/investigation, **do NOT post to GitHub**.
4. If an issue is present AND the transaction meets the substantive analysis criteria:
   - Run the security/privacy screening process on both user prompt and agent response.
   - Post the screened and formatted transaction using `gh issue comment` or `post_transaction.sh`.
5. Deliver the final response to the user.
6. If no issue was specified, omit posting and state so at the end of the prompt's response.
