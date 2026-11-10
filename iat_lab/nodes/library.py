"""Keep existing node groups available as reusable assets without rewriting them."""

from pathlib import Path

import bpy


def value(item):
    if item is None or isinstance(item, (bool, int, float, str)):
        return item
    if isinstance(item, bpy.types.ID):
        return {"datablock": item.name, "type": type(item).__name__}
    try:
        return [value(v) for v in item]
    except TypeError:
        return str(item)


def snapshot_group(group):
    """Review metadata, not a lossless graph serializer or rebuild specification."""
    return {
        "name": group.name, "type": group.bl_idname,
        "interface": [{"name": s.name, "identifier": s.identifier,
                       "direction": s.in_out, "socket_type": s.socket_type,
                       "default": value(getattr(s, "default_value", None)),
                       "description": s.description}
                      for s in group.interface.items_tree if s.item_type == "SOCKET"],
        "nodes": [{"name": n.name, "type": n.bl_idname, "label": n.label,
                   "node_group": getattr(getattr(n, "node_tree", None), "name", None),
                   "settings": {key: value(getattr(n, key)) for key in
                                ("operation", "data_type", "domain", "mode", "input_type")
                                if hasattr(n, key)},
                   "inputs": [{"name": s.name, "identifier": s.identifier,
                               "default": value(getattr(s, "default_value", None))}
                              for s in n.inputs]}
                  for n in sorted(group.nodes, key=lambda x: x.name)],
        "links": sorted([{"from_node": l.from_node.name, "from_socket": l.from_socket.identifier,
                          "to_node": l.to_node.name, "to_socket": l.to_socket.identifier}
                         for l in group.links],
                        key=lambda l: (l["from_node"], l["from_socket"], l["to_node"], l["to_socket"])),
    }


def build_library(output):
    """Extract loaded Geometry Nodes plus dependencies into a generated .blend library."""
    output = Path(output).resolve()
    if bpy.data.filepath and output == Path(bpy.data.filepath).resolve():
        raise ValueError("Library output must not overwrite the loaded scene")
    groups = {g for g in bpy.data.node_groups if g.bl_idname == "GeometryNodeTree"}
    if not groups:
        raise ValueError("Loaded scene contains no Geometry Nodes groups")
    output.parent.mkdir(parents=True, exist_ok=True)
    bpy.data.libraries.write(str(output), groups, fake_user=True, compress=True)
    return sorted(g.name for g in groups)
