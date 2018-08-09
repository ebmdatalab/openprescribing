'''
This script produces graphs to show how data flows through the openprescribing
app.  It reads data from the .yml files in this directory, and currently shows
tables, API endpoints, and pages.  In the future it should include BQ tables,
management commands, and data sources.  These files will need to be manuualy
kept up to date.

To use, run:

    $ python draw_data_flow.py [label, [label...]]

The full output is hard to make sense of, so you can pass labels of nodes you
are interested in.  For instance, the following command will only show API
endpoints and pages that use MeasureValue:

    $ python draw_data_flow.py tables.MeasureValue

Output is produced in a file called openp-data-flow.svg.  (This could be made
configurable.)
'''



from collections import defaultdict
import os
import sys

from graphviz import Digraph
import networkx as nx
from networkx.algorithms.dag import ancestors, descendants
import yaml


CATEGORIES = ['tables', 'api_endpoints', 'pages']


def build_graph():
    G = nx.DiGraph()

    for category in CATEGORIES:
        with open(category + '.yml') as f:
            records = yaml.load(f)

        for record in records:
            full_label = '{}.{}'.format(category, record['label'])
            G.add_node(full_label)

            for dependency_label in record.get('dependencies') or []:
                dependency_category, _ = dependency_label.split('.')

                # We can remove this `if` once all .yml files are complete.
                if dependency_category not in CATEGORIES:
                    continue

                G.add_edge(dependency_label, full_label)

    return G


def filter_graph(G, nodes):
    nbunch = set()
    for node in nodes:
        nbunch.add(node)
        nbunch |= ancestors(G, node)
        nbunch |= descendants(G, node)
    return G.subgraph(nbunch)


def draw_graph(G):
    graph = Digraph(format='svg')
    graph.graph_attr['rankdir'] = 'LR'

    nodes_by_category = defaultdict(list)
    for node in G.nodes():
        category, label = node.split('.')
        nodes_by_category[category].append(node)

    for category in CATEGORIES:
        with graph.subgraph(name=category, graph_attr={'rank': 'same'}) as subgraph:
            for node in nodes_by_category[category]:
                subgraph.node(node)

    for node1, node2 in G.edges():
        graph.edge(node1, node2)

    graph.render('openp-data-flow', cleanup=True)


if __name__ == '__main__':
    G = build_graph()

    if len(sys.argv) > 1:
        G = filter_graph(G, sys.argv[1:])

    draw_graph(G)
