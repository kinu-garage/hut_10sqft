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

# Helper script to post formatted AI agent interaction transaction to a GitHub issue
# with security & privacy redaction.
#
# Usage:
#   post_transaction.sh <ISSUE_TARGET> <AGENT_NAME> <MODEL_NAME> <USER_PROMPT_FILE> <AGENT_RESP_FILE>

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
case "${DISPLAY_AGENT,,}" in
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
    # Redact common tokens and secrets
    input=$(echo "$input" | sed -E 's/gh[opsu]_[A-Za-z0-9_]{36,}/[REDACTED_GITHUB_TOKEN]/g')
    input=$(echo "$input" | sed -E 's/sk-[A-Za-z0-9_-]{20,}/[REDACTED_API_KEY]/g')
    input=$(echo "$input" | sed -E 's/Bearer [A-Za-z0-9._~+/-]{20,}/Bearer [REDACTED_TOKEN]/g')
    # Redact private IPv4 addresses (10.x.x.x, 192.168.x.x, 172.16-31.x.x, 100.64-127.x.x)
    input=$(echo "$input" | sed -E 's/\b192\.168\.[0-9]{1,3}\.[0-9]{1,3}\b/[REDACTED_IP]/g')
    input=$(echo "$input" | sed -E 's/\b10\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\b/[REDACTED_IP]/g')
    input=$(echo "$input" | sed -E 's/\b172\.(1[6-9]|2[0-9]|3[0-1])\.[0-9]{1,3}\.[0-9]{1,3}\b/[REDACTED_IP]/g')
    input=$(echo "$input" | sed -E 's/\b100\.(6[4-9]|[7-9][0-9]|1[0-1][0-9]|12[0-7])\.[0-9]{1,3}\.[0-9]{1,3}\b/[REDACTED_IP]/g')
    echo "$input"
}

TMP_COMMENT=$(mktemp /tmp/gh_comment_XXXXXX.md)
trap 'rm -f "$TMP_COMMENT"' EXIT

USER_PROMPT=$(sanitize_text "$(cat "$USER_PROMPT_FILE")")
AGENT_RESP=$(sanitize_text "$(cat "$AGENT_RESP_FILE")")

FIRST_LINE=$(echo "$USER_PROMPT" | head -n 1 | cut -c 1-120)
LINE_COUNT=$(echo "$USER_PROMPT" | wc -l)

{
    echo "*Posted by ${DISPLAY_AGENT} (not a human) with ${MODEL_NAME}.*"
    echo ""
    echo "<details>"
    
    if [ "$LINE_COUNT" -le 3 ] && [ ${#USER_PROMPT} -le 240 ]; then
        echo "<summary>${USER_PROMPT}</summary>"
        echo ""
    else
        echo "<summary>${FIRST_LINE}...</summary>"
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
