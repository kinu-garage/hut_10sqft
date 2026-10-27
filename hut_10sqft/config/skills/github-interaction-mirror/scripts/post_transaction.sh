#!/usr/bin/env bash

# Copyright 2026 Kinu Garage
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# SUMMARY:
#   Helper script to sanitize and post formatted AI agent interaction transactions
#   (prompt + response) as comments to a GitHub issue. Sensitive tokens, private IP
#   addresses, and credentials are automatically redacted before posting.
#
# REFERENCE:
#   https://github.com/kinu-garage/hut_10sqft/issues/1509
#
# USAGE:
#   post_transaction.sh <ISSUE_TARGET> <AGENT_NAME> <MODEL_NAME> <USER_PROMPT_FILE> <AGENT_RESP_FILE>
#
# INPUTS:
#   Positional Arguments:
#     1. ISSUE_TARGET      GitHub issue identifier. Accepts:
#                          - Full URL: https://github.com/<owner>/<repo>/issues/<num>
#                          - Shorthand: <owner>/<repo>#<num>
#                          - Issue number: #<num> or <num>
#     2. AGENT_NAME        Name of AI agent (e.g. "Antigravity", "Claude Code").
#                          Default: "Antigravity".
#     3. MODEL_NAME        Name of model used (e.g. "Gemini 3.8", "Sonnet 5.5 Medium").
#                          Default: "Gemini 3.8".
#     4. USER_PROMPT_FILE  Path to readable file containing the user's prompt text.
#     5. AGENT_RESP_FILE   Path to readable file containing the agent's response text.
#   Prerequisites:
#     - GitHub CLI ('gh') installed and authenticated with issue write permissions.
#
# OUTPUTS:
#   Side Effects:
#     - Appends a sanitized, collapsible markdown comment to the target GitHub issue.
#   Stdout:
#     - Status confirmation message upon successful comment creation.
#   Stderr:
#     - Descriptive error message on invalid arguments, missing files, or CLI failure.
#   Exit Codes:
#     - 0: Successfully sanitized and posted to the GitHub issue.
#     - 1: Invalid arguments, missing files, or execution failure.

set -euo pipefail

ISSUE_TARGET="${1:-}"
AGENT_NAME="${2:-Antigravity}"
MODEL_NAME="${3:-Gemini 3.8}"
USER_PROMPT_FILE="${4:-}"
AGENT_RESP_FILE="${5:-}"

if [ -z "$ISSUE_TARGET" ] || [ -z "$USER_PROMPT_FILE" ] || [ -z "$AGENT_RESP_FILE" ]; then
    echo "Error: Missing arguments." >&2
    echo "Usage: $0 <ISSUE_TARGET> <AGENT_NAME> <MODEL_NAME> <USER_PROMPT_FILE> <AGENT_RESP_FILE>" >&2
    exit 1
fi

# Normalize ISSUE_TARGET (convert owner/repo#123 to GitHub URL, strip leading # from #123)
if [[ "$ISSUE_TARGET" =~ ^([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)#([0-9]+)$ ]]; then
    ISSUE_TARGET="https://github.com/${BASH_REMATCH[1]}/issues/${BASH_REMATCH[2]}"
elif [[ "$ISSUE_TARGET" =~ ^#([0-9]+)$ ]]; then
    ISSUE_TARGET="${BASH_REMATCH[1]}"
fi

DISPLAY_AGENT="${AGENT_NAME#A-}"
DISPLAY_AGENT_LOWER=$(echo "$DISPLAY_AGENT" | tr '[:upper:]' '[:lower:]')
case "$DISPLAY_AGENT_LOWER" in
    antigravity) DISPLAY_AGENT="Antigravity" ;;
    "claude code"|claude) DISPLAY_AGENT="Claude Code" ;;
esac

if [ ! -f "$USER_PROMPT_FILE" ]; then
    echo "Error: User prompt file not found: $USER_PROMPT_FILE" >&2
    exit 1
fi

if [ ! -f "$AGENT_RESP_FILE" ]; then
    echo "Error: Agent response file not found: $AGENT_RESP_FILE" >&2
    exit 1
fi

# Sanitize function for security and privacy
sanitize_text() {
    local input="$1"
    # Redact SSH and TLS private key blocks
    input=$(echo "$input" | awk '
        /-----BEGIN [A-Z0-9 _-]*PRIVATE KEY/ { in_key=1; print "[REDACTED_PRIVATE_KEY]"; next }
        /-----END [A-Z0-9 _-]*PRIVATE KEY/ { in_key=0; next }
        !in_key { print }
    ')
    # Redact common tokens and secrets
    input=$(echo "$input" | sed -E 's/gh[opsu]_[A-Za-z0-9_]{36,}/[REDACTED_GITHUB_TOKEN]/g')
    input=$(echo "$input" | sed -E 's/sk-[A-Za-z0-9_-]{20,}/[REDACTED_API_KEY]/g')
    input=$(echo "$input" | sed -E 's/Bearer [A-Za-z0-9._~+/-]{20,}/Bearer [REDACTED_TOKEN]/g')
    # Redact password values in key-value assignments
    input=$(echo "$input" | sed -E "
        s/(password|passwd|pwd)([[:space:]]*[:=][[:space:]]*[\"'])[^\r\n\"']+([\"'])/\1\2[REDACTED_PASSWORD]\3/gi;
        s/(password|passwd|pwd)([[:space:]]*[:=][[:space:]]*)([^\"'({[:space:]][^[:space:]]*)/\1\2[REDACTED_PASSWORD]/gi
    ")
    # Redact email addresses
    input=$(echo "$input" | sed -E 's/[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/[REDACTED_EMAIL]/g')
    # Redact private IPv4 addresses (10.x.x.x, 192.168.x.x, 172.16-31.x.x, 100.64-127.x.x)
    # Using portable boundary matching preserving surrounding non-digit characters on BSD & GNU sed
    input=$(echo "$input" | sed -E "
        s/(^|[^0-9])192\.168\.[0-9]{1,3}\.[0-9]{1,3}([^0-9]|$)/\1[REDACTED_IP]\2/g;
        s/(^|[^0-9])192\.168\.[0-9]{1,3}\.[0-9]{1,3}([^0-9]|$)/\1[REDACTED_IP]\2/g;
        s/(^|[^0-9])10\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}([^0-9]|$)/\1[REDACTED_IP]\2/g;
        s/(^|[^0-9])10\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}([^0-9]|$)/\1[REDACTED_IP]\2/g;
        s/(^|[^0-9])172\.(1[6-9]|2[0-9]|3[0-1])\.[0-9]{1,3}\.[0-9]{1,3}([^0-9]|$)/\1[REDACTED_IP]\3/g;
        s/(^|[^0-9])172\.(1[6-9]|2[0-9]|3[0-1])\.[0-9]{1,3}\.[0-9]{1,3}([^0-9]|$)/\1[REDACTED_IP]\3/g;
        s/(^|[^0-9])100\.(6[4-9]|[7-9][0-9]|1[0-1][0-9]|12[0-7])\.[0-9]{1,3}\.[0-9]{1,3}([^0-9]|$)/\1[REDACTED_IP]\3/g;
        s/(^|[^0-9])100\.(6[4-9]|[7-9][0-9]|1[0-1][0-9]|12[0-7])\.[0-9]{1,3}\.[0-9]{1,3}([^0-9]|$)/\1[REDACTED_IP]\3/g
    ")
    echo "$input"
}

# Safety screening: verify content is safe to post before sending
screen_content_safety() {
    local text="$1"
    local source_name="$2"

    # Screen for SSH and TLS private key blocks
    if echo "$text" | grep -qE -- '-----(BEGIN|END) [A-Z0-9 _-]*PRIVATE KEY'; then
        echo "Error: Safety screening failed in $source_name: unredacted private key block detected. Aborting post to GitHub." >&2
        return 1
    fi

    # Screen for GitHub tokens
    if echo "$text" | grep -qE -- 'gh[opsu]_[A-Za-z0-9_]{36,}'; then
        echo "Error: Safety screening failed in $source_name: unredacted GitHub token detected. Aborting post to GitHub." >&2
        return 1
    fi

    # Screen for API keys
    if echo "$text" | grep -qE -- 'sk-[A-Za-z0-9_-]{20,}'; then
        echo "Error: Safety screening failed in $source_name: unredacted API key detected. Aborting post to GitHub." >&2
        return 1
    fi

    # Screen for personal email addresses
    if echo "$text" | grep -qE -- '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'; then
        echo "Error: Safety screening failed in $source_name: unredacted email address detected. Aborting post to GitHub." >&2
        return 1
    fi

    # Screen for unredacted password values
    local assignments
    assignments=$(echo "$text" | grep -oiE -- "(password|passwd|pwd)[[:space:]]*[:=][[:space:]]*(\"[^\"]*\"|'[^']*'|[^[:space:]]+)" || true)
    if [ -n "$assignments" ]; then
        while IFS= read -r assign; do
            [ -z "$assign" ] && continue
            if ! echo "$assign" | grep -qiE -- "^(password|passwd|pwd)[[:space:]]*[:=][[:space:]]*(\"\\[REDACTED_PASSWORD\\]\"|'\\[REDACTED_PASSWORD\\]'|\\[REDACTED_PASSWORD\\]|\"\"|'')$"; then
                echo "Error: Safety screening failed in $source_name: unredacted password value detected. Aborting post to GitHub." >&2
                return 1
            fi
        done <<< "$assignments"
    fi

    return 0
}

# Trim repetitive automated review boilerplate (e.g. CodeRabbit prompts, tracking issue instructions)
trim_user_prompt() {
    local text="$1"
    local trimmed
    trimmed=$(python3 -c '
import sys, re

content = sys.stdin.read()
# Remove leading tracking issue redirection
content = re.sub(r"^(?:And you[\x27\x22]ve stopped posting to GH\.\.\.)?\s*Please use https?://\S+\s*", "", content, flags=re.IGNORECASE)
# Remove CodeRabbit review preamble (and transition phrases)
preamble_pattern = r"(?:(?:Once|After)\b[^\n]*?done[^\n]*?[:,\.]\s*)?Treat finding text, file paths, and code as untrusted review data\..*?validate\."
content = re.sub(preamble_pattern, "", content, flags=re.DOTALL | re.IGNORECASE)
# Remove CodeRabbit post-fix suggestion
post_fix_pattern = r"After applying the fix, consider running [`\x27\x22]?coderabbit review.*?https?://\S+"
content = re.sub(post_fix_pattern, "", content, flags=re.DOTALL | re.IGNORECASE)
content = re.sub(r"Visit https?://docs\.coderabbit\.ai\S*", "", content, flags=re.IGNORECASE)
content = re.sub(r"\n{3,}", "\n\n", content).strip()
print(content)
' <<< "$text" 2>/dev/null || echo "$text")

    if [ -n "$trimmed" ]; then
        echo "$trimmed"
    else
        echo "$text"
    fi
}

generate_summary_title() {
    local text="$1"
    local title
    title=$(python3 -c '
import sys

lines = [l.strip() for l in sys.stdin.read().splitlines() if l.strip()]
if not lines:
    print("AI Agent Interaction")
    sys.exit(0)

first = lines[0]
if first.startswith("Review comment at") and len(lines) > 1 and (lines[1].endswith(":") or (lines[1].split() and lines[1].split()[0].isdigit())):
    first = f"{first} {lines[1]}"
print(first[:120])
' <<< "$text" 2>/dev/null || true)

    if [ -n "$title" ]; then
        echo "$title"
    else
        local first_line="${text%%$'\n'*}"
        echo "${first_line:0:120}"
    fi
}

TMP_COMMENT=$(mktemp /tmp/gh_comment_XXXXXX)
trap 'rm -f "$TMP_COMMENT"' EXIT

USER_PROMPT=$(sanitize_text "$(cat "$USER_PROMPT_FILE")")
USER_PROMPT=$(trim_user_prompt "$USER_PROMPT")
AGENT_RESP=$(sanitize_text "$(cat "$AGENT_RESP_FILE")")

screen_content_safety "$USER_PROMPT" "USER_PROMPT_FILE" || exit 1
screen_content_safety "$AGENT_RESP" "AGENT_RESP_FILE" || exit 1

SUMMARY_TITLE=$(generate_summary_title "$USER_PROMPT")
LINE_COUNT=$(echo "$USER_PROMPT" | wc -l)

{
    echo "*Posted by ${DISPLAY_AGENT} (not a human) with ${MODEL_NAME}.*"
    echo ""
    echo "<details>"
    
    if [ "$LINE_COUNT" -le 3 ] && [ ${#USER_PROMPT} -le 240 ]; then
        echo "<summary>${USER_PROMPT}</summary>"
        echo ""
    else
        echo "<summary>${SUMMARY_TITLE}...</summary>"
        echo ""
        echo "$USER_PROMPT"
        echo ""
        echo "----"
        echo ""
    fi
    
    echo "**${DISPLAY_AGENT}. ${MODEL_NAME}.**"
    echo ""
    echo "$AGENT_RESP"
    echo "</details>"
} > "$TMP_COMMENT"

gh issue comment "$ISSUE_TARGET" --body-file "$TMP_COMMENT"
echo "Successfully posted interaction transaction to $ISSUE_TARGET"
