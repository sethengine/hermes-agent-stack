# Extraction Heuristics — Signal Detection for Session Knowledge

Not all session messages carry durable knowledge. Some conversations are dominated by noise: repeated commands,
argument loops, trivial back-and-forth, or "tire-kicking" (user testing the same action multiple times).
Extracting every session's every message wastes LLM tokens on wiki files no one will ever query.

## Low-Signal Patterns (skip extraction)

Signal is low when the session delta is dominated by:

- **Repeated identical commands** — User issues the same command 5+ times (e.g., "enable and disable it
  again", "do it again"). The exchange is testing or trolling, not generating durable knowledge.
- **Argument loops** — User disagrees and re-asks the same question in different words. The assistant
  re-explains the same answer. No new information after the first exchange.
- **Operation interrupted** — Multiple consecutive assistant responses are "Operation interrupted." or
  "Operation interrupted: waiting for model response". No actual content was delivered.
- **Query-only sessions** — User asks a definitional question ("what is X"), gets a Wikipedia-style
  answer, and the conversation ends. Citations may be useful; the content itself is not durable knowledge
  about *this system*.
- **Trivial confirmation** — "Done." / "Done." / "Done." loops. No config, no workaround, no learning.

## Medium-Signal Patterns (extract cautiously)

Some signal is present but concentrated. Extract only the actionable facts:

- **Frustration-driven debugging** — Long back-and-forth where the user is frustrated (caps, insults).
  The first meaningful technical exchange often contains the real fix; later messages are venting.
  Extract the fix, skip the venting.
- **Trial-and-error troubleshooting** — 10+ rounds of "try X" / "didn't work" / "try Y" with a specific
  config change buried in round 7. Only extract the config change that actually resolved the problem.
- **Question with low-quality answer** — The assistant gave a wrong or incomplete answer and had to
  be corrected. Extract the *correction*, not the initial answer.

## High-Signal Patterns (always extract)

- **First-time configuration** — New software installed, tool configured, daemon set up with specific
  flags, environment variables, or files. Extract the config.
- **Bug workaround** — A specific bug was identified (driver version, kernel parameter, config conflict)
  and a workaround was applied. Extract the workaround + affected component.
- **Diagnostic chain** — Multiple diagnostic commands were run and their output was interpreted.
  Extract the root cause + the diagnostic command that revealed it + the fix.
- **Performance analysis** — Specific benchmarks or latency measurements led to a configuration change.
  Extract the baseline metric, the change, and the resulting metric.

## When to Skip a Session Entirely

Skip extraction entirely when:

1. All messages from the session's delta are low-signal (repeated commands, interrupted operations).
2. The session has < 3 high-signal messages and no config change or fix was applied.
3. The session is purely informational (user asked a non-system question about a third-party tool,
   a concept, or a general computing topic).

In these cases, just update the manifest timestamp so the session is marked processed but no wiki
files are created. This avoids cluttering the brain with dead nodes.

## Implementation Note

When iterating over delta messages, do a quick pre-scan: count the number of distinct assistant
messages that contain actionable content (config blocks, diagnostic output, commands run, fix
descriptions). If that count is 0 or 1 across 15+ messages, the session likely has no durable
knowledge worth extracting. Proceed with manifest-only update.
