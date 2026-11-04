# Prints the Merge Input per-input script context.
# Runs after each input is merged. Available values:
#   context / batch_context: Full runtime dictionary.
#   arguments / args, environment_variables / env.
#   input_path, input_index, total_inputs, namespace, load_mode, reference_node.
#   merged_nodes: Every node created by this input (long names).
#   root_nodes: Top-level transforms of this input (after grouping, if enabled).
#   input_group, merge_group: Group names, or empty strings.
#   input_record: This input's record. merged_records: Records of earlier inputs.
import sys

sys.stdout.write(f"Merge Input [{input_index}/{total_inputs}]: {input_path}\n")
sys.stdout.write(f"  Load mode: {load_mode}  Namespace: {namespace or '(root)'}\n")
sys.stdout.write(f"  Nodes: {len(merged_nodes)}  Roots: {len(root_nodes)}  Group: {input_group or '-'}\n")
if reference_node:
    sys.stdout.write(f"  Reference node: {reference_node}\n")
