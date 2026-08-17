#!/bin/sh
# Prompt before destructive git commands. Never refuse them outright.
#
# History:
#   05 Aug 2026 - `ask` rules added to settings.json after a `reset --hard`
#                 wiped seven files of another session's uncommitted work.
#   06 Aug 2026 - this hook added as a hard block after a subagent ran
#                 `git stash` in a shared tree and destroyed delivered data.
#                 It matched broad substrings (*git checkout*, *git commit*,
#                 *git push*, *git merge*) and refused ordinary work outright.
#   07 Aug 2026 - rewritten on Michael's instruction. Two corrections:
#                 (1) the pattern list now covers only work-destroying commands,
#                     not branch switching, committing, pushing or merging;
#                 (2) the decision is ASK, not DENY. An agent that hits one of
#                     these gets a confirmation prompt to the user, who decides.
#                     Refusing outright cost a working morning and is not the
#                     guardrail that was wanted.
#
# Why a hook rather than the settings.json `ask` rules alone: those rules are
# skipped under bypassPermissions ("YOLO") mode, which is the normal working
# mode here. A PreToolUse hook runs in every mode, so the prompt survives.
#
# Mechanism: PreToolUse hook on Bash. Reads the tool call as JSON on stdin.
# Emitting hookSpecificOutput.permissionDecision=ask on stdout with exit 0
# forces a confirmation prompt. Exit 0 with no output allows the call.
# Exit 2 (a hard refusal) is deliberately not used anywhere in this file.
#
# Read-only git - log, show, diff, status, ls-files, rev-parse, stash list,
# branch listing - is never touched.
#
# No Python anywhere in this file, by standing instruction.

payload=$(cat)

command=$(printf '%s' "$payload" | node -e 'let d="";process.stdin.on("data",c=>d+=c).on("end",()=>{try{process.stdout.write(String((JSON.parse(d).tool_input||{}).command||""))}catch(e){}})' 2>/dev/null)

# If the payload could not be parsed there is nothing to inspect; allow rather
# than prompt, so a parser failure never nags on every shell command.
[ -z "$command" ] && exit 0

# Commands that throw away work which may exist nowhere else. Everything here
# prompts; nothing here is refused.
#
# Deliberately NOT matched: git checkout <branch>, switch, commit, push
# (non-force), merge, rebase, revert, cherry-pick, stash list/show, worktree add.
case "$command" in
  *git\ reset\ --hard*|\
  *git\ clean\ -f*|\
  *git\ checkout\ --\ *|\
  *git\ checkout\ .*|\
  *git\ restore*|\
  *git\ push\ --force*|\
  *git\ push\ -f*|\
  *git\ branch\ -D*|\
  *git\ stash\ drop*|\
  *git\ stash\ clear*|\
  *git\ stash\ pop*|\
  *git\ stash\ push*|\
  *git\ stash\ save*|\
  *git\ reflog\ delete*|\
  *git\ filter-branch*)
    reason="Destructive git command - discards work that may exist nowhere else. Working trees here are shared with other agents and a live service, so the effect is not scoped to one session."
    printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"%s"}}\n' "$reason"
    exit 0
    ;;
esac

exit 0
