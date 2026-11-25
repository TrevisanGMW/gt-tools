# Prints the Merge Input post-merge script context.
# Runs once after every input is merged and the time range is set, before saving. Available values:
#   context / batch_context, arguments / args, environment_variables / env.
#   output_path: Merged scene path (empty when Keep Open is used).
#   merged_records: One record per input (path, name, index, status, namespace, nodes, root_nodes,
#                   reference_node, group, display_layer, time_range, time_offset, message).
#   merged_inputs / failed_inputs: Records filtered by status.
#   merge_group: Group holding every input, or an empty string.
#   time_range: (start, end) applied to the scene, or None.
import sys

sys.stdout.write(f"Merge Input post script. Output: {output_path or '(not saved)'}\n")
sys.stdout.write(f"  Merged: {len(merged_inputs)}  Failed: {len(failed_inputs)}  Time range: {time_range}\n")
for record in merged_records:
    sys.stdout.write(f"  [{record['index']}] {record['status']}: {record['name']} {record['message']}\n")
