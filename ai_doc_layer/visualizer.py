# visualizer.py
from pathlib import Path
import ast
import pydot


class UMLGenerator:
    """
    Generates a CLEAN, STRUCTURED UML diagram with:
    - Each class shown exactly once
    - Correct inheritance mapping
    - Methods grouped within each class
    - File-level clusters
    """

    def __init__(self):
        self.class_map = {}   # class_name → {file, methods, bases}
        self.functions_map = {}  # file → [functions]

    # --------------------------------------------------------
    # Base name extractor (handles dotted paths)
    # --------------------------------------------------------
    def _get_base_name(self, base):
        if isinstance(base, ast.Name):     # class A(B)
            return base.id

        if isinstance(base, ast.Attribute):  # class A(module.B)
            parts = []
            node = base
            while isinstance(node, ast.Attribute):
                parts.append(node.attr)
                node = node.value
            if isinstance(node, ast.Name):
                parts.append(node.id)
            parts.reverse()
            return ".".join(parts)

        return None

    # --------------------------------------------------------
    # Parse a single file
    # --------------------------------------------------------
    def _parse_file(self, file_path: Path):
        src = file_path.read_text(encoding="utf-8")
        tree = ast.parse(src)
        fname = str(file_path)

        local_classes = {}
        local_functions = []

        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                cname = node.name
                methods = [
                    m.name for m in node.body if isinstance(m, ast.FunctionDef)
                ]

                bases = []
                for b in node.bases:
                    base = self._get_base_name(b)
                    if base:
                        bases.append(base)

                local_classes[cname] = {
                    "file": fname,
                    "methods": methods,
                    "bases": bases
                }

            elif isinstance(node, ast.FunctionDef):
                local_functions.append(node.name)

        # Merge classes into global registry
        for cname, info in local_classes.items():
            self.class_map[cname] = info

        # Save standalone functions
        self.functions_map[fname] = local_functions

    # --------------------------------------------------------
    # Generate UML
    # --------------------------------------------------------
    def generate(self, repo: Path, out_png: Path):

        # STEP 1 — Parse ALL FILES FIRST
        for py_file in repo.rglob("*.py"):
            self._parse_file(py_file)

        # STEP 2 — Build UML diagram
        graph = pydot.Dot("UML", graph_type="digraph", rankdir="TB")

        # STEP 3 — One cluster per file
        file_clusters = {}

        for cname, info in self.class_map.items():
            fname = info["file"]

            if fname not in file_clusters:
                file_clusters[fname] = pydot.Cluster(
                    fname,
                    label=f"<<b>{Path(fname).name}</b>>",
                    style="rounded",
                    color="#8888FF"
                )

            # UML style class box
            label = f"""<
            <TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0">
            <TR><TD><B>{cname}</B></TD></TR>
            <HR/>
            """
            for m in info["methods"]:
                label += f"<TR><TD ALIGN='LEFT'>{m}()</TD></TR>"

            label += "</TABLE>>"

            node = pydot.Node(
                cname,
                label=label,
                shape="plaintext"
            )
            file_clusters[fname].add_node(node)

        # Add file-level clusters
        for cluster in file_clusters.values():
            graph.add_subgraph(cluster)

        # STEP 4 — Draw inheritance arrows
        for cname, info in self.class_map.items():
            for base in info["bases"]:
                if base in self.class_map:
                    graph.add_edge(
                        pydot.Edge(
                            base,
                            cname,
                            arrowhead="onormal",
                            label="inherits"
                        )
                    )

        # STEP 5 — Save diagram
        graph.write_png(str(out_png))
