# Prints the Validate Animation post-script context.
# Available values:
#   evaluation: Full evaluation report (score, status, checks with spans and offenders).
#   score / status: Overall score (0-100) and status (passed, warning, failed).
#   score_write: Result of the score attribute write ({"written", "node", "attribute", "message"}).
#   context / batch_context, arguments / args, environment_variables / env,
#   project, task, work_item, output_path / log_dir.
import sys

sys.stdout.write(f"Validate Animation post script: score {score} ({status})\n")
sys.stdout.write(f"Input: {args.get('input') or work_item.current_path}\n")
for entry in evaluation.get("checks", []):
    if entry.get("status") in ("warning", "failed"):
        spans = ", ".join(f"{start}-{end}" for start, end in entry.get("spans", [])[:5])
        sys.stdout.write(f"  {entry['label']}: {entry['score']} [{entry['status']}] frames {spans}\n")
sys.stdout.write(f"Score attribute: {score_write.get('message')}\n")
