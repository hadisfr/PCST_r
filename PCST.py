#!/usr/bin/env python3

from itertools import tee
from random import sample
from sys import stderr

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import networkx as nx


class Plot:
    """Plot Graphs in multipage pdf"""
    def __init__(self, name="plots.pdf"):
        self.pages = PdfPages(name)

    def close(self):
        self.pages.close()

    def draw(self, graph, **kws):
        plt.figure()
        plt.axis('off')
        nx.draw(graph, **kws)
        self.pages.savefig()


def pairwise(iterable):
    """s -> (s0,s1), (s1,s2), (s2, s3), ..."""
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


def make_weighted(graph_list):
    for graph in graph_list:
        nx.set_edge_attributes(graph, dict((edge, 1) for edge in graph.edges), 'weight')


def stp(graph, terminals):
    """Steiner Tree Problem"""
    shortest_paths = dict(nx.all_pairs_dijkstra_path(graph))
    shortest_paths_length = dict(nx.all_pairs_dijkstra_path_length(graph))  # could be obtained from `shortest_paths`. worse performance?
    terminals_graph = nx.Graph()
    terminals_graph.add_nodes_from(terminals)
    terminals_graph = nx.complement(terminals_graph)
    mst_weight = 0
    for edge in terminals_graph.edges:
        terminals_graph.edges[edge]['weight'] = shortest_paths_length[edge[0]][edge[1]]
        mst_weight += terminals_graph.edges[edge]['weight']
    terminals_mst = nx.minimum_spanning_tree(terminals_graph)
    mst = nx.Graph()
    mst.add_nodes_from(graph)
    mst_nodes = []
    for edge in terminals_mst.edges:
        for _edge in pairwise(shortest_paths[edge[0]][edge[1]]):
            mst.add_edge(*_edge, **graph.edges[_edge])
            mst_nodes += shortest_paths[edge[0]][edge[1]]
    # mst.remove_nodes_from(list(nx.isolates(mst)))
    return mst, mst_weight, mst_nodes


def pcstp(graph, node_name_key):
    """Prize-Collecting Steiner Tree Problem"""
    terminals = [n for n in graph.nodes if int(graph.nodes[n][node_name_key]) > 0]
    total_weight = float('inf')
    new_total_weight = sum([graph.edges[e]['weight'] for e in graph.edges])

    # phase 1: using stp
    while new_total_weight < total_weight:
        print("new_total_weight: %r,\ttotal_weight: %r" % (new_total_weight, total_weight), file=stderr)
        total_weight = new_total_weight
        _, new_total_weight, terminals = stp(graph, terminals)
    print("new_total_weight: %r,\ttotal_weight: %r" % (new_total_weight, total_weight), file=stderr)

    # phase 2: pruning
    for node in [node for (node, degree) in graph.degree() if node in terminals and degree == 1]:
        for neighbor in graph.neighbors(node):
            if(graph.degree(neighbor) > 1):
                if(graph.nodes[node][node_name_key] < graph.edges[(node, neighbor)]['weight']):
                    total_weight -= graph.edges[(node, neighbor)]['weight']
                    graph.remove_edge(neighbor, node)
                    terminals.remove(node)
            else:
                if(graph.nodes[node][node_name_key] + graph.nodes[neighbor][node_name_key] < graph.edges[(node, neighbor)]['weight']):
                    total_weight -= graph.edges[(node, neighbor)]['weight']
                    graph.remove_edge(neighbor, node)
                    terminals.remove(node)
                    terminals.remove(neighbor)

    prize = sum([int(graph.nodes[n][node_name_key]) for n in graph.nodes if n in terminals])
    return graph, prize - total_weight, terminals


def main():
    # Erdos-Renyi Graph
    # graph = nx.erdos_renyi_graph(100, 1 / 10)
    # terminals = random.sample(range(0, len(graph.nodes) - 1), 5)

    # K_5
    # graph = nx.complete_graph(5)
    # terminals = [2, 4]

    # GNet
    graph = nx.read_graphml("gnet.graphml")
    terminals = ['n' + str(i) for i in sample(range(0, len(graph.nodes) - 1), 10)]

    # make_weighted([graph])
    # res, res_weight, res_nodes = stp(graph, terminals)
    res, res_weight, res_nodes = pcstp(graph, 'name')
    print("weight:\t%r\t%r nodes\t%r edges" % (res_weight, len(res_nodes), len(res.edges)))
    # print("verbose report:\nweight:\t%r\nnodes:\t%r\nedges:\t%r" % (res_weight, res_nodes, res.edges))

    res.remove_nodes_from(list(nx.isolates(res)))
    nx.draw(res, with_labels=True)
    plt.show()

    # plot = Plot()
    # plot.draw(graph)
    # plot.draw(res, with_labels=True)
    # plot.close()


if __name__ == '__main__':
    main()
