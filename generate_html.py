import json
from pathlib import Path
from networkx.readwrite import json_graph
from graphify.cluster import cluster, score_all
from graphify.analyze import god_nodes, surprising_connections, suggest_questions
from graphify.report import generate
from graphify.export import to_html

# Load the raw data you just generated
data = json.loads(Path('graphify-out/graph.json').read_text())
G = json_graph.node_link_graph(data, edges='links')

# Run the clustering math
communities = cluster(G)
cohesion = score_all(G, communities)
gods = god_nodes(G)
surprises = surprising_connections(G, communities)
labels = {cid: f'Community {cid}' for cid in communities}
questions = suggest_questions(G, communities, labels)

# Generate the Markdown Report
report = generate(
    G, communities, cohesion, labels, gods, surprises,
    detection={'total_files': 0, 'total_words': 0, 'needs_graph': True, 'warning': None, 'files': {'code': [], 'document': [], 'paper': [], 'image': []}},
    tokens={'input': 0, 'output': 0}, project_path='.', suggested_questions=questions,
)
Path('graphify-out/GRAPH_REPORT.md').write_text(report)

# Generate the interactive HTML visualization
to_html(G, communities, 'graphify-out/graph.html', community_labels=labels)
print("Success! graph.html has been generated.")