import json
import os
import re
from typing import List, Dict
from dataclasses import dataclass

import networkx as nx


@dataclass
class AtlasNode:
    identifier: str
    name: str
    _in: List[str]
    out: List[str]
    description: List[str]

    def __hash__(self):
        return hash(self.identifier)

    def __eq__(self, other):
        if isinstance(other, AtlasNode):
            return self.identifier == other.identifier
        return False


class AtlasGraph(nx.Graph):
    def __init__(self, atlas_json):
        super().__init__()
        self.node_to_enumeration: Dict[AtlasNode, int] = {}
        self.enumeration_to_node: Dict[int, AtlasNode] = {}
        self.nodes_by_id: Dict[str, AtlasNode] = {}  # to retrieve Nodes from their identifier field
        e = 1  # enumeration of nodes starts at 1 in STP problems

        # add all the nodes to the graph and the respective dictionaries
        for id, node in atlas_json['nodes'].items():
            # skip the one weird node with basically no entries
            if node.get('skill') is None:
                continue
            # skip nodes that are unconnected i.e masteries
            if not node["in"] and not node["out"]:
                continue
            n = AtlasNode(str(node["skill"]), str(node["name"]), node["in"], node["out"], node["stats"])
            self.add_node(n)


            self.nodes_by_id[id] = n
            self.node_to_enumeration[n] = e
            self.enumeration_to_node[e] = n
            e += 1
        self.root = self.nodes_by_id["29045"]
        # now add all the edges
        for node in self.nodes_by_id.values():
            for _in in node._in:
                self.add_edge(node, self.nodes_by_id[_in])
            for out in node.out:
                self.add_edge(self.nodes_by_id[out], node)




class STP:

    def __init__(self):
        # parse the atlas data json to generate the dictionaries that map enumeration to node and vice versa
        with open('external/skilltree/data.json') as f:
            self.atlas_graph = AtlasGraph(json.load(f))

        # check if the stp template already exists, else create it
        if os.path.exists("out/atlas_template"):
            with open("out/atlas_template", 'r') as f:
                self.stp_template = f.read()
        else:
            self.stp_template = self.create_stp_template()
        pass

    def create_stp_template(self) -> str:
        # creates the stp template and saves it at "out/atlas_template" and returns the string
        with open("out/atlas_template", 'w') as f:
            f.write("33D32945 STP File, STP Format Version 1.0\n")
            f.write("SECTION Comment\n")
            f.write("Name    \"Atlas\"\n")
            f.write("Creator \"Sniixed\"\n")
            f.write("END\n")
            f.write("\n")
            f.write("SECTION Graph\n")
            f.write(f"Nodes {len(self.atlas_graph.nodes)}\n")
            f.write(f"Edges {len(self.atlas_graph.edges)}\n")
            for u, v in self.atlas_graph.edges:
                f.write(f"E {self.atlas_graph.node_to_enumeration[u]} {self.atlas_graph.node_to_enumeration[v]} 1\n")
            f.write("END\n")
            f.write("\n")
            f.write("SECTION Terminals\n")
            # add the placeholder for number of terminals
            f.write("Terminals {}\n")
            # add the placeholder for the terminal identifiers
            f.write("{}\n")
            f.write("END\n")
            f.write("\n")
            f.write("EOF\n")

        with open("out/atlas_template", 'r') as f:
            return f.read()

    def create_stp_file(self, terminal_ids: List[str]) -> str:
        # fills in the template with the terminals' enumeration and saves it at a hashed filename
        # then returns the filename as a string
        terminal_ids.sort()
        terminals = [self.atlas_graph.nodes_by_id[str(id)] for id in terminal_ids] + [self.atlas_graph.root]

        filename = str(hash("".join(terminal_ids)))  + ".stp"
        filepath = os.path.join(os.getcwd(),"out", filename)
        with open(filepath, "w") as f:
            f.write(self.stp_template.format(len(terminals), "\n".join(
                [f"T {str(self.atlas_graph.node_to_enumeration[t])}" for t in terminals])))
        return filepath
    def read_stp_solution(self, filepath:str) -> List[str]:
        # reads in the stp solution file, looks for the Vertices section and returns the identifiers of the corresponding enumerated nodes
        with open(filepath, 'r') as f:
            lines = f.read()
        final_solution = lines.split("SECTION Finalsolution")[1].split("Edges")[0]

        pattern = "V\s+(\d+)"
        matches = re.findall(pattern, final_solution)

        return list(map(lambda x: self.atlas_graph.enumeration_to_node[int(x)].identifier, matches))
# def create_stp_file(stp: STPGraph, allocated_nodes: List[AtlasNode]):
#     with open('atlas.stp', 'w') as f:
#         f.write("33D32945 STP File, STP Format Version 1.0\n")
#         f.write("SECTION Comment\n")
#         f.write("Name    \"Atlas\"\n")
#         f.write("Creator \"Sniixed\"\n")
#         f.write("END\n")
#         f.write("\n")
#         f.write("SECTION Graph\n")
#         f.write(f"Nodes {len(stp.nodes)}\n")
#         f.write(f"Edges {len(stp.edges)}\n")
#         for edge in stp.edges():
#             f.write(f"E {edge[0].data._id + 1} {edge[1].data._id + 1} 1\n")
#         f.write("END\n")
#         f.write("\n")
#         f.write("SECTION Terminals\n")
#         f.write(f"Terminals {len(allocated_nodes)}\n")
#         for node in allocated_nodes:
#             f.write(f"T {enumerated_nodes[node.identifier] + 1}\n")
#         f.write("END\n")
#         f.write("\n")
#         f.write("EOF\n")
