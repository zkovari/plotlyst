from dataclasses import dataclass

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QPen, QColor
from PyQt6.QtWidgets import QMainWindow, QGraphicsScene, QGraphicsView

GML = """
Creator "yFiles"  
Version 2.2  
graph  
[ hierarchic  1  
  directed  1  
  node  
  [ id  0  
    graphics  
    [ x 200.0     
      y 0.0  
    ]  
    LabelGraphics  
    [ text  "January" ]  
  ]  
  node  
  [ id  1  
    graphics  
    [ x 425.0  
      y 75.0  
    ]  
    LabelGraphics  
    [ text  "December"  ]  
  ]  
  edge  
  [ source  1  
    target  0  
    graphics  
    [ Line  
      [ point  
        [ x 425.0  
          y 75.0  
        ]  
        point  
        [ x 425.0  
          y 0.0  
        ]  
        point  
        [ x 200.0  
          y 0.0  
        ]  
      ]  
    ]  
    LabelGraphics  
    [ text  "Happy New Year!"  
      model "six_pos"  
      position  "head"  
    ]  
  ]  
]  
"""


class MindmapViewer(QMainWindow):
    def __init__(self, gml_file):
        super().__init__()

        # with open(gml_file, 'r') as file:
        #     gml_content = file.read()
        gml_content = """
      graph [
directed 1
node [
  id 1
  label "Node 1"
  graphics [
    x 16.0
    y 24.0
    w 36.0
    h 36.0
  ]
]
node [
  id 2
  label "Node 2"
  graphics [
    x 105.0
    y 24.0
    w 36.0
    h 36.0
  ]
]
edge [
  source 1
  target 2
]
]
        """

        # Parse the GML content and extract the nodes and edges
        nodes = {}
        edges = []
        in_node = False
        node_id = None
        node_label = None
        node_x = None
        node_y = None
        node_w = None
        node_h = None
        lines = gml_content.splitlines()
        for line in lines:
            if line.startswith("node ["):
                node_id = None
                node_label = None
                node_x = None
                node_y = None
                node_w = None
                node_h = None
                in_node = True
            elif line.startswith("]"):
                in_node = False
                nodes[node_id] = (node_label, node_x, node_y, node_w, node_h)
            elif in_node:
                if line.startswith("id "):
                    node_id = int(line.split()[-1])
                elif line.startswith("label "):
                    node_label = line.split("\"")[-2]
                elif line.startswith("x "):
                    node_x = float(line.split()[-1])
                elif line.startswith("y "):
                    node_y = float(line.split()[-1])
                elif line.startswith("w "):
                    node_w = float(line.split()[-1])
                elif line.startswith("h "):
                    node_h = float(line.split()[-1])
            elif line.startswith("edge ["):
                edge_source = int(line.split("source ")[-1])
                edge_target = int(line.split("target ")[-1])
                edges.append((edge_source, edge_target))

        # Create a QGraphicsScene and add the nodes and edges to it
        self.scene = QGraphicsScene()
        for node_id, (node_label, node_x, node_y, node_w, node_h) in nodes.items():
            node = self.scene.addRect(node_x - node_w / 2, node_y - node_h / 2, node_w, node_h,
                                      pen=QPen(Qt.GlobalColor.black),
                                      brush=QBrush(QColor("lightgray")))
            self.scene.addText(node_label, node.pos())
        for edge_source, edge_target in edges:
            source_x, source_y = nodes[edge_source][1:3]
            target_x, target_y = nodes[edge_target][1:3]
            self.scene.addLine(source_x, source_y, target_x, target_y, pen=QPen(Qt.GlobalColor.black))

        # Create a QGraphicsView and set the scene
        self.view = QGraphicsView(self.scene)
        self.setCentralWidget(self.view)


@dataclass
class Node:
    id: int
    x: float
    y: float
    label: str


@dataclass
class Edge:
    source: int
    target: int
    label: str


def parse_gml(content: str):
    nodes = {}
    edges = []

    in_node = False
    in_edge = False
    node_id = None
    node_x = None
    node_y = None
    node_label = None
    edge_source = None
    edge_target = None
    edge_label = None

    for line in content.splitlines():
        line = line.strip()
        print(line)

        if line == "node":
            print('in node')
            in_node = True
        elif line == "edge":
            in_edge = True
        elif line.startswith("id"):
            print('id')
            node_id = int(line.split()[1])
        elif line.startswith("x"):
            node_x = float(line.split()[1])
        elif line.startswith("y"):
            node_y = float(line.split()[1])
        elif line.startswith("text"):
            node_label = line.split('"')[1]
        elif line.startswith("source"):
            edge_source = int(line.split()[1])
        elif line.startswith("target"):
            edge_target = int(line.split()[1])

        if line == "]":
            if in_node:
                in_node = False
                nodes[node_id] = Node(node_id, node_x, node_y, node_label)
                node_id = None
                node_x = None
                node_y = None
                node_label = None
            elif in_edge:
                in_edge = False
                edges.append(Edge(edge_source, edge_target, edge_label))
                edge_source = None
                edge_target = None
                edge_label = None

    return nodes, edges


dot_content = """
digraph Dedmo {
  rankdir = "LR"
  node[shape=box width=2.3 height=0.3 fontname="Arial"];
  comment="I am a graph"
  A [shape=diamond]
  B [comment="I am node B"]
  C [shape=circle]

  A -> B [style=dashed, color=grey]
  A -> C [color="black:invis:black"]
  A -> D [penwidth=5, arrowhead=none]
  C -> E [comment="I am node A"]
  C -> F
  node[shape=box width=2.3 height=1 fontname="Arial"];
  C -> G
  B -> H
  B ->I
  D -> Jesdfdffgrvbfgh
  H -> H

}
"""

# nodes, edges = parse_gml("mindmap.gml")

if __name__ == '__main__':
    nodes, edges = parse_gml(GML)
    print(nodes)
    print(edges)
    # app = QApplication(sys.argv)
    # mindmap_viewer = MindmapViewer("mindmap.gml")
    # mindmap_viewer.show()
    # sys.exit(app.exec())
