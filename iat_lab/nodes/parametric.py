"""Build editable lab assemblies from the protected source meshes.

Controllers transmit their values through named attributes on one point.
Members sample that point in Geometry Nodes: no Python handlers or drivers.
"""

import json
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

from ..materials import ALIASES, catalog
from ..blender.appearance import apply_preview_materials

CONTROLS = "00 IAT Controls"
MODIFIER = "IAT - component controls"
MEMBER_MODIFIER = "IAT - parametric geometry"
FIELDS = {"Position": "FLOAT_VECTOR", "Rotation": "FLOAT_VECTOR", "Size": "FLOAT_VECTOR",
          "Enabled": "BOOLEAN", "Absorber enabled": "BOOLEAN", "Absorber depth": "FLOAT",
          "Absorber gap": "FLOAT", "Absorber scale": "FLOAT_VECTOR",
          "Absorber offset": "FLOAT_VECTOR"}


def attribute(name):
    return "iat_" + name.lower().replace(" ", "_")


class Graph:
    def __init__(self, name):
        self.tree = bpy.data.node_groups.new(name, "GeometryNodeTree")
        self.tree.is_modifier = True
        self.tree.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
        self.tree.interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
        self.input = self.node("NodeGroupInput", "Controls", (-900, 300))
        self.output = self.node("NodeGroupOutput", "Output", (900, 300))
        self.tree.asset_mark()

    def node(self, kind, label, location=(0, 0)):
        node = self.tree.nodes.new(kind)
        node.label = label
        node.location = location
        node.width = 205
        return node

    def link(self, source, target):
        self.tree.links.new(source, target)

    def set(self, socket, value):
        if isinstance(value, bpy.types.NodeSocket):
            self.link(value, socket)
        else:
            socket.default_value = value

    def control(self, name, value, description="", minimum=None, maximum=None, subtype=None):
        kind = "NodeSocketBool" if isinstance(value, bool) else (
            "NodeSocketVector" if isinstance(value, (tuple, list, Vector)) else "NodeSocketFloat")
        socket = self.tree.interface.new_socket(name=name, in_out="INPUT", socket_type=kind)
        socket.default_value = value
        socket.description = description
        if minimum is not None:
            socket.min_value = minimum
        if maximum is not None:
            socket.max_value = maximum
        if subtype is not None:
            socket.subtype = subtype
        return self.input.outputs[name]

    def vector(self, operation, a, b, label, location=(0, 0)):
        node = self.node("ShaderNodeVectorMath", label, location)
        node.operation = operation
        self.set(node.inputs[0], a)
        self.set(node.inputs[1], b)
        return node.outputs["Vector"]

    def scalar(self, operation, a, b, label, location=(0, 0)):
        node = self.node("ShaderNodeMath", label, location)
        node.operation = operation
        self.set(node.inputs[0], a)
        self.set(node.inputs[1], b)
        return node.outputs[0]

    def transform(self, geometry, position=(0, 0, 0), rotation=(0, 0, 0), scale=(1, 1, 1), label="Transform", location=(0, 0)):
        node = self.node("GeometryNodeTransform", label, location)
        for key, val in [("Geometry", geometry), ("Translation", position), ("Rotation", rotation), ("Scale", scale)]:
            self.set(node.inputs[key], val)
        return node.outputs["Geometry"]

    def gate(self, geometry, enabled, label="Enabled", location=(650, 300)):
        node = self.node("GeometryNodeSwitch", label, location)
        node.input_type = "GEOMETRY"
        self.set(node.inputs["Switch"], enabled)
        self.set(node.inputs["True"], geometry)
        return node.outputs["Output"]

    def sample(self, controller, names):
        info = self.node("GeometryNodeObjectInfo", "Read assembly controller", (-1250, -150))
        info.inputs["Object"].default_value = controller
        info.transform_space = "ORIGINAL"
        outputs = {}
        for i, name in enumerate(names):
            attr = self.node("GeometryNodeInputNamedAttribute", name, (-1250, -450 - i * 190))
            attr.data_type = FIELDS[name]
            attr.inputs["Name"].default_value = attribute(name)
            sample = self.node("GeometryNodeSampleIndex", "Controller " + name, (-990, -450 - i * 190))
            sample.data_type = FIELDS[name]
            sample.domain = "POINT"
            self.link(info.outputs["Geometry"], sample.inputs["Geometry"])
            self.link(attr.outputs["Attribute"], sample.inputs["Value"])
            sample.inputs["Index"].default_value = 0
            outputs[name] = sample.outputs["Value"]
        return outputs


def world_points(obj):
    if obj.type == "MESH":
        return [obj.matrix_world @ v.co for v in obj.data.vertices]
    return [obj.matrix_world @ Vector(c) for c in obj.bound_box]


def bounds(objects):
    points = [p for obj in objects for p in world_points(obj)]
    low = Vector([min(p[i] for p in points) for i in range(3)])
    high = Vector([max(p[i] for p in points) for i in range(3)])
    return (low + high) / 2, Vector([max(high[i] - low[i], 0.001) for i in range(3)])


def make_controller(label, center, size, collection, foam=None):
    mesh = bpy.data.meshes.new("IAT controller point - " + label)
    mesh.from_pydata([(0, 0, 0)], [], [])
    obj = bpy.data.objects.new("CTRL | " + label, mesh)
    collection.objects.link(obj)
    obj["iat_role"] = "controller"
    obj["iat_export"] = False
    obj["iat_base_center"] = list(center)
    obj["iat_base_size"] = list(size)
    g = Graph("IAT | " + label + " controls")
    values = {
        "Position": list(center), "Rotation": [0.0, 0.0, 0.0], "Size": list(size), "Enabled": True,
    }
    if foam:
        values.update({"Absorber enabled": foam["enabled"], "Absorber depth": foam["depth"],
                       "Absorber gap": foam["gap"], "Absorber scale": [1.0, 1.0, 1.0],
                       "Absorber offset": [0.0, 0.0, 0.0]})
    geometry = g.input.outputs["Geometry"]
    for i, (name, default) in enumerate(values.items()):
        field = g.control(name, default, {
            "Position": "Assembly pivot in world metres; default reproduces the archived layout.",
            "Rotation": "XYZ Euler rotation about the assembly pivot; zero preserves its archived orientation.",
            "Size": "World-axis baseline extent in metres, before Rotation. Rescales all member geometry.",
            "Enabled": "Controls geometry and RF export independently of the Outliner cutaway.",
            "Absorber scale": "Panel coverage multiplier. Normal-axis scale is ignored; use Absorber depth.",
        }.get(name, "Attached absorber control; independent of presentation visibility."),
            minimum=0.0001 if name in {"Size", "Absorber depth"} else (0 if name in {"Absorber gap", "Absorber scale"} else None),
            maximum=100 if name == "Size" else None,
            subtype="EULER" if name == "Rotation" else ("TRANSLATION" if name in {"Position", "Absorber offset"} else None))
        store = g.node("GeometryNodeStoreNamedAttribute", "Publish " + name, (-550 + i * 230, 300))
        store.data_type = FIELDS[name]
        store.domain = "POINT"
        store.inputs["Name"].default_value = attribute(name)
        g.link(geometry, store.inputs["Geometry"])
        g.link(field, store.inputs["Value"])
        geometry = store.outputs["Geometry"]
    g.output.location = (-300 + len(values) * 230, 300)
    g.link(geometry, g.output.inputs["Geometry"])
    mod = obj.modifiers.new(MODIFIER, "NODES")
    mod.node_group = g.tree
    obj["iat_default_controls"] = json.dumps(values)
    return obj


def controller_values(obj):
    mod = obj.modifiers[MODIFIER]
    result = {}
    for socket in mod.node_group.interface.items_tree:
        if socket.item_type == "SOCKET" and socket.in_out == "INPUT" and socket.name != "Geometry":
            value = getattr(mod.properties.inputs, socket.identifier).value
            result[socket.name] = list(value) if hasattr(value, "__len__") else value
    return result


def set_control(obj, name, value):
    mod = obj.modifiers[MODIFIER]
    socket = next(s for s in mod.node_group.interface.items_tree if s.item_type == "SOCKET" and s.in_out == "INPUT" and s.name == name)
    getattr(mod.properties.inputs, socket.identifier).value = value
    obj.update_tag()
    bpy.context.view_layer.update()


def member_group(label, controller, center, size):
    g = Graph("IAT | " + label)
    offset = g.control("Part offset", [0.0, 0.0, 0.0], "Offset in the assembly's baseline axes, before assembly rotation.", subtype="TRANSLATION")
    rotation = g.control("Part rotation", [0.0, 0.0, 0.0], "Rotation about this part's own baseline center.", subtype="EULER")
    scale = g.control("Part scale", [1.0, 1.0, 1.0], "Local size multiplier; assembly Size applies afterwards.", minimum=0.0001)
    pivot = g.control("Part pivot", [0.0, 0.0, 0.0], "Baseline world pivot for this part; initialized by the builder.")
    controls = g.sample(controller, ["Position", "Rotation", "Size", "Enabled"])
    negative_pivot = g.vector("MULTIPLY", pivot, (-1, -1, -1), "Center part", (-650, 0))
    geo = g.transform(g.input.outputs["Geometry"], position=negative_pivot, label="Part origin", location=(-600, 300))
    geo = g.transform(geo, rotation=rotation, scale=scale, label="Part size and angle", location=(-350, 300))
    part_position = g.vector("ADD", pivot, offset, "Part pivot plus offset", (-400, 0))
    local = g.vector("SUBTRACT", part_position, center, "Relative to assembly pivot", (-150, 0))
    geo = g.transform(geo, position=local, label="Part in assembly", location=(-100, 300))
    ratio = g.vector("DIVIDE", controls["Size"], size, "Assembly size ratio", (100, -100))
    geo = g.transform(geo, controls["Position"], controls["Rotation"], ratio, "Assembly transform", (200, 300))
    geo = g.gate(geo, controls["Enabled"])
    g.link(geo, g.output.inputs["Geometry"])
    return g.tree


def absorber_group(label, controller, wall_center, wall_size, foam_center, foam_size, axis, sign):
    g = Graph("IAT | " + label + " attached absorber")
    controls = g.sample(controller, list(FIELDS))
    ratio = g.vector("DIVIDE", controls["Size"], wall_size, "Wall size ratio", (-650, -150))
    dimensions = g.vector("MULTIPLY", foam_size, ratio, "Panel follows wall dimensions", (-400, -150))
    dimensions = g.vector("MULTIPLY", dimensions, controls["Absorber scale"], "Coverage adjustment", (-150, -150))
    sep = g.node("ShaderNodeSeparateXYZ", "Panel dimensions", (100, -150))
    g.link(dimensions, sep.inputs[0])
    combine = g.node("ShaderNodeCombineXYZ", "Independent depth", (350, -150))
    for i in range(3):
        g.set(combine.inputs[i], controls["Absorber depth"] if i == axis else sep.outputs[i])
    factor = g.vector("DIVIDE", combine.outputs[0], foam_size, "Panel size ratio", (600, -150))
    relative = g.vector("MULTIPLY", foam_center - wall_center, ratio, "Panel center follows wall", (-650, -400))
    sep_rel = g.node("ShaderNodeSeparateXYZ", "Tangential center", (-400, -400))
    g.link(relative, sep_rel.inputs[0])
    sep_wall = g.node("ShaderNodeSeparateXYZ", "Wall thickness", (-650, -650))
    g.link(controls["Size"], sep_wall.inputs[0])
    normal = g.scalar("ADD", sep_wall.outputs[axis], controls["Absorber depth"], "Wall and absorber thickness", (-400, -650))
    normal = g.scalar("MULTIPLY", normal, 0.5, "Half thicknesses", (-150, -650))
    normal = g.scalar("ADD", normal, controls["Absorber gap"], "Mounting gap", (100, -650))
    normal = g.scalar("MULTIPLY", normal, sign, "Interior side", (350, -650))
    combine_pos = g.node("ShaderNodeCombineXYZ", "Attached center", (600, -400))
    for i in range(3):
        g.set(combine_pos.inputs[i], normal if i == axis else sep_rel.outputs[i])
    position = g.vector("ADD", combine_pos.outputs[0], controls["Absorber offset"], "Panel placement", (850, -400))
    geo = g.transform(g.input.outputs["Geometry"], position=-foam_center, label="Panel origin", location=(-600, 300))
    geo = g.transform(geo, position=position, scale=factor, label="Size and mount on wall", location=(-300, 300))
    geo = g.transform(geo, controls["Position"], controls["Rotation"], label="Follow wall pose", location=(0, 300))
    geo = g.gate(geo, controls["Absorber enabled"], "Panel enabled", (300, 300))
    geo = g.gate(geo, controls["Enabled"], "Wall assembly enabled", (600, 300))
    g.link(geo, g.output.inputs["Geometry"])
    return g.tree


def canonical_materials(records=None):
    records = records or catalog()
    for obj in bpy.data.objects:
        materials = getattr(obj.data, "materials", None)
        if materials is None:
            continue
        for index, old in enumerate(list(materials)):
            if old is None:
                continue
            key = ALIASES.get(old.name, old.name if old.name in records else None)
            if key is None:
                old["iat_role"] = "visual_only_uncharacterized"
                continue
            # Preserve the five leaf preview shades; all export to one RF material.
            name = "iat_leaf_" + old.name.rsplit("_", 1)[1] if old.name.startswith("Fixed_leaf_") else key
            mat = bpy.data.materials.get(name)
            if mat is None:
                mat = old.copy()
                mat.name = name
            for legacy in ("EM_properties", "RF_epsilon_r", "RF_sigma_S_m", "RF_slab_thickness_m"):
                if legacy in mat:
                    del mat[legacy]
            mat["iat_radio_material"] = key
            mat["iat_material_record"] = json.dumps(records[key])
            mat["iat_status"] = records[key]["status"]
            materials[index] = mat


def freeze_world_geometry(objects):
    # Capture all matrices before detaching plant children.
    matrices = {obj.name: obj.matrix_world.copy() for obj in objects}
    for obj in objects:
        obj.data = obj.data.copy()
        obj.data.transform(matrices[obj.name])
        obj.parent = None
        obj.matrix_world = Matrix.Identity(4)


def organize_results():
    """Keep each variant's parent collection, with separate Paths/Heatmap children."""
    layout = []
    for scene in bpy.data.scenes:
        paths = [o for o in scene.objects if o.name.startswith("PATHS")]
        maps = [o for o in scene.objects if o.name.startswith("HEATMAP")]
        if len(paths) != 1 or len(maps) != 1:
            raise ValueError(f"Expected one path object and heatmap in {scene.name}")
        shared = set(paths[0].users_collection) & set(maps[0].users_collection)
        if len(shared) != 1:
            raise ValueError(f"Ambiguous results parent in {scene.name}")
        parent = shared.pop()
        record = {"scene": scene.name, "parent": parent.name}
        parent["iat_scope"] = "Archived baseline results; not recomputed by environment controls"
        for label, obj in [("Paths", paths[0]), ("Heatmap", maps[0])]:
            child = bpy.data.collections.new(label + " | " + scene.name)
            parent.children.link(child)
            child.objects.link(obj)
            parent.objects.unlink(obj)
            child["iat_scope"] = parent["iat_scope"]
            record[label.lower()] = child.name
        layout.append(record)
    return layout


def build(output_reference=None, material_catalog=None):
    if bpy.data.collections.get(CONTROLS):
        raise ValueError("Scene already has IAT controls. Rebuild from the protected baseline instead.")
    canonical_materials(material_catalog)
    apply_preview_materials()
    collection = bpy.data.collections.new(CONTROLS)
    for scene in bpy.data.scenes:
        scene.collection.children.link(collection)
    # One-vertex mesh anchors can follow the same node transforms as their assemblies.
    # They have no renderable faces; cross/horn/glyph display geometry is retained.
    for obj in list(bpy.data.objects):
        if obj.type == "EMPTY":
            name = obj.name
            matrix = obj.matrix_world.copy()
            children = [(child, child.matrix_world.copy()) for child in obj.children]
            eyes = [(scene.view_layers[0], obj.hide_get(view_layer=scene.view_layers[0]))
                    for scene in bpy.data.scenes if name in scene.objects]
            mesh = bpy.data.meshes.new("IAT anchor - " + obj.name)
            mesh.from_pydata([(0, 0, 0)], [], [])
            anchor = bpy.data.objects.new(name + " live", mesh)
            anchor.matrix_world = matrix
            anchor.hide_viewport, anchor.hide_render = obj.hide_viewport, obj.hide_render
            for key in obj.keys():
                anchor[key] = obj[key]
            for owner in obj.users_collection:
                owner.objects.link(anchor)
            obj.user_remap(anchor)
            bpy.data.objects.remove(obj, do_unlink=True)
            anchor.name = name
            for child, child_matrix in children:
                child.parent = anchor
                child.matrix_world = child_matrix
            for layer, hidden in eyes:
                anchor.hide_set(hidden, view_layer=layer)
            anchor["iat_point_anchor"] = True
    all_shapes = [o for o in bpy.data.objects if o.type in {"MESH", "CURVE"} and not o.name.startswith(("PATHS", "HEATMAP", "Original bench"))]
    freeze_world_geometry(all_shapes)
    for obj in bpy.data.objects:
        obj["iat_export"] = bool(obj.get("RF_included_in_saved_simulation", False))
        obj["iat_role"] = "rf" if obj["iat_export"] else "visual_or_reference"
    reference = {"schema_version": 1, "controls_collection": CONTROLS, "assemblies": []}
    used = set()

    def assembly(label, names, foam_name=None, axis=None, sign=None, foam_enabled=True):
        members = [bpy.data.objects[n] for n in names]
        center, size = bounds([obj for obj in members if not obj.get("iat_point_anchor")])
        foam = bpy.data.objects.get(foam_name) if foam_name else None
        foam_info = None
        if foam:
            foam_center, foam_size = bounds([foam])
            gap = sign * (foam_center[axis] - center[axis]) - (size[axis] + foam_size[axis]) / 2
            foam_info = {"enabled": foam_enabled, "depth": foam_size[axis], "gap": max(gap, 0)}
        ctrl = make_controller(label, center, size, collection, foam_info)
        tree = member_group(label, ctrl, center, size)
        for obj in members:
            pivot, _ = bounds([obj])
            mod = obj.modifiers.new(MEMBER_MODIFIER, "NODES")
            mod.node_group = tree
            socket = next(s for s in tree.interface.items_tree if s.name == "Part pivot")
            getattr(mod.properties.inputs, socket.identifier).value = pivot
            obj["iat_controller"] = ctrl.name
            used.add(obj.name)
        if foam:
            mod = foam.modifiers.new(MEMBER_MODIFIER, "NODES")
            mod.node_group = absorber_group(label, ctrl, center, size, foam_center, foam_size, axis, sign)
            foam["iat_controller"] = ctrl.name
            foam["iat_absorber"] = True
            used.add(foam.name)
        if axis is not None:
            members[0]["iat_surface_axis"] = axis
            members[0]["iat_surface_sign"] = sign
        reference["assemblies"].append({"name": label, "controller": ctrl.name,
            "members": names, "absorber": foam_name, "defaults": controller_values(ctrl),
            "surface_axis": axis, "surface_sign": sign})

    # The previously bare Y-max wall receives a mirrored copy, disabled by default.
    template = bpy.data.objects["Absorber_Wall_Y_Min | RF 07"]
    new = template.copy()
    new.data = template.data.copy()
    new.name = "Absorber_Wall_Y_Max | optional"
    wall = bpy.data.objects["Wall_Y_Max | RF 06"]
    inner_y = min(v.co.y for v in wall.data.vertices)
    mirror = Matrix.Identity(4)
    mirror[1][1] = -1
    mirror[1][3] = inner_y
    new.data.transform(mirror)
    new.data.flip_normals()
    wall.users_collection[0].objects.link(new)
    new.hide_render = wall.hide_render
    for scene in bpy.data.scenes:
        new.hide_set(True, view_layer=scene.view_layers[0])
    new["iat_export"] = True
    new["iat_role"] = "rf"
    for label, wall_name, foam_name, axis, sign, enabled in [
        ("Wall X min", "Wall_X_Min | RF 03", template.name.replace("Y_Min | RF 07", "X_Min | RF 08"), 0, 1, True),
        ("Wall X max", "Wall_X_Max | RF 04", "Absorber_Wall_X_Max | RF 09", 0, -1, True),
        ("Wall Y min", "Wall_Y_Min | RF 05", template.name, 1, 1, True),
        ("Wall Y max", wall.name, new.name, 1, -1, False),
    ]:
        assembly(label, [wall_name], foam_name, axis, sign, enabled)
    assembly("Floor", ["Lab_Floor | RF 01"], axis=2, sign=1)
    assembly("Ceiling", ["Lab_Ceiling | RF 02"], axis=2, sign=-1)
    families = {
        "RIS aperture": ["RIS_508_Mount_and_Stand | RF 21", "RIS | exact 508 cell centres and profiles", "RIS cell glyphs | active ON blue, OFF dark", "RIS glyphs | reflective phase states", "RIS physical frame | W01133"],
        "RIS stand": ["RIS_508_Mount_and_Stand | RF 22"],
        "Scanner table": ["Scanner_Static | RF 18", "Scanner_Static | RF 19", "Scanner_Static | RF 20", "Assumed plant support plane | display only", "Assumed plant support plane | display only.001"],
        "Scanner mechanics": ["Scanner_X_Bridge", "Scanner_Y_Carriage", "Scanner_RX_Assembly"],
        "Scanner sampling plane": ["RX grid | 2300 phase-centre samples"] + [o.name for o in all_shapes if o.name.startswith("Scanner AOI boundary")],
        "TX assembly": ["TX_Tripod | RF 23", "TX_Tripod | RF 24", "TX_Head | RF 25", "TX_Horn_Display", "TX | 10 dBm horn phase centre"],
        "Blocker": ["Blocker_Wood | RF 11", "Blocker_Supports | RF 12", "Absorber_Blocker_Face | RF 10"],
        "Door": ["Door_Assembly | RF 13", "Door_Assembly | RF 14"],
        "Pipes": ["Pipes_All | RF 15"],
        "Light fixtures": ["Light_Fixtures | RF 16", "Light_Fixtures | RF 17"],
        "Plant 1": [o.name for o in all_shapes if o.name.startswith("Plant1_")],
        "Plant 2": [o.name for o in all_shapes if o.name.startswith("Plant2_")],
        "Target marker": [o.name for o in all_shapes if o.name.startswith("Confirmed target cross")] + ["RX TARGET | report 1.2785, 0.4653, 0.96 m", "RIS_Custom_Target"],
    }
    for label, names in families.items():
        assembly(label, names)
    for obj in all_shapes:
        if obj.name not in used:
            raise ValueError(f"Unassigned editable geometry: {obj.name}")
    for scene in bpy.data.scenes:
        scene["iat_parametric_version"] = 1
        scene["iat_saved_results_scope"] = "Archived baseline only; geometry/material edits do not recompute paths, heatmaps or RIS phases."
    reference["results_layout"] = organize_results()
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action="DESELECT")
    selected = bpy.data.objects["CTRL | Wall Y min"]
    selected.select_set(True)
    bpy.context.view_layer.objects.active = selected
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == "PROPERTIES":
                area.spaces.active.context = "MODIFIER"
    if output_reference:
        Path(output_reference).parent.mkdir(parents=True, exist_ok=True)
        Path(output_reference).write_text(json.dumps(reference, indent=2) + "\n", encoding="utf-8", newline="\n")
    return reference
