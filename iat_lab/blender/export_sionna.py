"""Deterministic Sionna RT 2.2 XML/PLY export of evaluated lab geometry."""

from collections import defaultdict
from contextlib import contextmanager
import json
import math
from pathlib import Path
import re
import struct
import xml.etree.ElementTree as ET

import bpy
from mathutils import Euler, Matrix, Vector

from ..materials import REFERENCE_HZ, load_catalog
from ..nodes.parametric import CONTROLS, MEMBER_MODIFIER, controller_values
from ..project import sha256


def slug(name):
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def write_json(path, payload):
    path.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


@contextmanager
def evaluate_all(scene):
    """Presentation hiding must not remove walls from the RF scene."""
    previous = bpy.context.window.scene
    bpy.context.window.scene = scene
    layer = scene.view_layers[0]
    saved = [(o, o.hide_viewport, o.hide_get(view_layer=layer)) for o in scene.objects]
    collection_flags = []

    def visit(lc):
        collection_flags.append((lc, lc.exclude, lc.hide_viewport, lc.collection.hide_viewport))
        lc.exclude = lc.hide_viewport = lc.collection.hide_viewport = False
        for child in lc.children:
            visit(child)
    try:
        visit(layer.layer_collection)
        for obj, _, _ in saved:
            obj.hide_viewport = False
            obj.hide_set(False, view_layer=layer)
        layer.update()
        yield bpy.context.evaluated_depsgraph_get()
    finally:
        for obj, monitor, eye in saved:
            obj.hide_viewport = monitor
            obj.hide_set(eye, view_layer=layer)
        for lc, exclude, eye, monitor in reversed(collection_flags):
            lc.exclude, lc.hide_viewport, lc.collection.hide_viewport = exclude, eye, monitor
        bpy.context.window.scene = previous


def write_ply(path, coordinates, triangles):
    used = sorted({index for triangle in triangles for index in triangle})
    mapping = {old: new for new, old in enumerate(used)}
    with path.open("wb") as stream:
        stream.write(("ply\nformat binary_little_endian 1.0\n"
                      f"element vertex {len(used)}\nproperty float x\nproperty float y\nproperty float z\n"
                      f"element face {len(triangles)}\nproperty list uchar int vertex_indices\nend_header\n").encode("ascii"))
        for index in used:
            stream.write(struct.pack("<3f", *coordinates[index]))
        for triangle in triangles:
            stream.write(struct.pack("<B3i", 3, *(mapping[index] for index in triangle)))
    return len(used)


def surface_normal_and_thickness(obj):
    if "iat_surface_axis" not in obj:
        return None, None
    axis, sign = int(obj["iat_surface_axis"]), int(obj["iat_surface_sign"])
    ctrl = bpy.data.objects[obj["iat_controller"]]
    values = controller_values(ctrl)
    base = Vector(ctrl["iat_base_size"])
    ratio = Vector(values["Size"])
    ratio = Vector([ratio[i] / base[i] for i in range(3)])
    mod = obj.modifiers[MEMBER_MODIFIER]
    part = {}
    for socket in mod.node_group.interface.items_tree:
        if socket.item_type == "SOCKET" and socket.in_out == "INPUT" and socket.name in {"Part rotation", "Part scale"}:
            part[socket.name] = getattr(mod.properties.inputs, socket.identifier).value
    transform = (obj.matrix_world.to_3x3() @ Euler(values["Rotation"]).to_matrix() @ Matrix.Diagonal(ratio)
                 @ Euler(part["Part rotation"]).to_matrix() @ Matrix.Diagonal(Vector(part["Part scale"])))
    basis = Vector([sign if i == axis else 0 for i in range(3)])
    normal = transform.inverted().transposed() @ basis
    return normal.normalized(), base[axis] / normal.length


def material_element(parent, identifier, entry, thickness):
    kind = {"itu": "itu-radio-material", "custom": "radio-material", "ideal_absorber": "absorber-radio-material"}[entry["model"]]
    node = ET.SubElement(parent, "bsdf", type=kind, id=identifier)
    if entry["model"] == "itu":
        ET.SubElement(node, "string", name="type", value=entry["itu_type"])
    elif entry["model"] == "custom":
        ET.SubElement(node, "float", name="relative_permittivity", value=str(entry["relative_permittivity"]))
        ET.SubElement(node, "float", name="conductivity", value=str(entry["conductivity_s_m"]))
    if entry["model"] != "ideal_absorber":
        ET.SubElement(node, "float", name="thickness", value=f"{thickness:.9g}")
        ET.SubElement(node, "float", name="scattering_coefficient", value=str(entry.get("scattering_coefficient", 0)))
        ET.SubElement(node, "float", name="xpd_coefficient", value=str(entry.get("xpd_coefficient", 0)))
    return node


def point_data(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        positions = [list(evaluated.matrix_world @ v.co) for v in mesh.vertices]
        attributes = {}
        for attr in mesh.attributes:
            if attr.domain != "POINT" or attr.name.startswith(".") or attr.name == "position":
                continue
            if attr.data_type in {"FLOAT", "INT", "BOOLEAN"}:
                attributes[attr.name] = [v.value for v in attr.data]
        return {"object": obj.name, "positions_m": positions, "attributes": attributes}
    finally:
        evaluated.to_mesh_clear()


def export_scene(output, scene_name=None, absorber_model="archived-proxy", frequency_hz=REFERENCE_HZ, materials_file=None):
    if absorber_model not in {"archived-proxy", "ideal"}:
        raise ValueError("Absorber model must be archived-proxy or ideal")
    records = load_catalog(materials_file, frequency_hz)
    output = Path(output).resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError("Choose an empty output directory; export will not overwrite an existing run")
    output.mkdir(parents=True, exist_ok=True)
    (output / "meshes").mkdir(exist_ok=True)
    scene = bpy.data.scenes[scene_name] if scene_name else bpy.context.scene
    if not scene.get("iat_parametric_version"):
        raise ValueError("Build the parametric lab before exporting")
    xml = ET.Element("scene", version="3.0.0")
    manifest = {"schema_version": 1, "target": "sionna-rt==2.2.0", "scene": scene.name,
                "frequency_hz": frequency_hz, "units": "metres", "absorber_model": absorber_model,
                "source_blend_sha256": sha256(Path(bpy.data.filepath)),
                "geometry": "evaluated Geometry Nodes; explicit RF membership, independent of cutaway visibility",
                "walls": "single interior-facing surfaces, openings retained; thickness follows Size and Part scale",
                "simulation_defaults": {"refraction": False, "diffraction": False, "diffuse_reflection": False},
                "limitations": ["RF absorber product is uncharacterized; selected model is a proxy or ideal limiting case.",
                    "Leaf and polypropylene values are archived 23.8 GHz priors, not new measurements.",
                    "Non-wall solids retain closed/multipart meshes. Refraction is disabled in the example to avoid counting slabs twice.",
                    "RIS cells and frozen states are exported as metadata. This exporter does not implement RIS scattering or an active two-hop solver.",
                    "Archived paths and heatmaps are not recomputed or exported as physical geometry.",
                    "ITU metal uses ordinary metal reflection. The archived metal-reflections-disabled solver policy is not reproduced."],
                "controllers": {o.name: controller_values(o) for o in sorted(bpy.data.collections[CONTROLS].objects, key=lambda o: o.name)},
                "objects": [], "excluded": [], "material_instances": {}}
    instances = {}
    with evaluate_all(scene) as depsgraph:
        for obj in sorted(scene.objects, key=lambda o: o.name):
            if obj.type != "MESH" or not obj.get("iat_export", False):
                manifest["excluded"].append(obj.name)
                continue
            evaluated = obj.evaluated_get(depsgraph)
            mesh = evaluated.to_mesh()
            try:
                mesh.calc_loop_triangles()
                coordinates = [evaluated.matrix_world @ v.co for v in mesh.vertices]
                if not all(math.isfinite(v) for p in coordinates for v in p):
                    raise ValueError(f"Nonfinite coordinates on {obj.name}")
                normal, slab_thickness = surface_normal_and_thickness(obj)
                partitions = defaultdict(list)
                for triangle in mesh.loop_triangles:
                    indices = tuple(triangle.vertices)
                    a, b, c = (coordinates[i] for i in indices)
                    cross = (b - a).cross(c - a)
                    if cross.length < 1e-12:
                        continue
                    if normal is not None and cross.normalized().dot(normal) < 0.999:
                        continue
                    if triangle.material_index >= len(mesh.materials) or mesh.materials[triangle.material_index] is None:
                        raise ValueError(f"Missing RF material: {obj.name}")
                    mat = mesh.materials[triangle.material_index]
                    key = mat.get("iat_radio_material")
                    if key not in records:
                        raise ValueError(f"Unregistered RF material {mat.name} on {obj.name}")
                    if key == "iat_absorber_proxy" and absorber_model == "ideal":
                        key = "iat_ideal_absorber"
                    partitions[key].append(indices)
                if len(mesh.vertices) and normal is not None and not partitions:
                    raise ValueError(f"No interior slab face found on {obj.name}")
                for key, triangles in sorted(partitions.items()):
                    entry = records[key]
                    thickness = slab_thickness if slab_thickness is not None else float(obj.get("iat_slab_thickness_m", entry.get("thickness_m", 0.1)))
                    if not math.isfinite(thickness) or thickness <= 0:
                        raise ValueError(f"Invalid slab thickness on {obj.name}")
                    identity = (key, round(thickness, 9))
                    if identity not in instances:
                        identifier = key + "__" + str(len(instances)).zfill(3)
                        instances[identity] = identifier
                        material_element(xml, identifier, entry, thickness)
                        manifest["material_instances"][identifier] = {"catalog_key": key, "thickness_m": thickness, **entry}
                        manifest["material_instances"][identifier]["thickness_m"] = thickness
                    identifier = instances[identity]
                    name = slug(obj.name) + "__" + key
                    path = output / "meshes" / (name + ".ply")
                    if path.exists():
                        raise ValueError(f"Export filename collision: {name}")
                    vertex_count = write_ply(path, coordinates, triangles)
                    shape = ET.SubElement(xml, "shape", type="ply", id=name)
                    ET.SubElement(shape, "string", name="filename", value="meshes/" + path.name)
                    ET.SubElement(shape, "ref", id=identifier, name="bsdf")
                    manifest["objects"].append({"source_object": obj.name, "shape_id": name,
                        "material": identifier, "vertices": vertex_count, "triangles": len(triangles),
                        "file": "meshes/" + path.name, "sha256": sha256(path),
                        "surface_policy": "single_slab_surface" if normal is not None else "source_topology"})
            finally:
                evaluated.to_mesh_clear()
        for filename, name in [("ris_cells.json", "RIS | exact 508 cell centres and profiles"),
                               ("receiver_grid.json", "RX grid | 2300 phase-centre samples")]:
            write_json(output / filename, point_data(scene.objects[name], depsgraph))
        anchors = {}
        for role, name in [("tx", "TX | 10 dBm horn phase centre"), ("target", "RX TARGET | report 1.2785, 0.4653, 0.96 m")]:
            positions = point_data(scene.objects[name], depsgraph)["positions_m"]
            if len(positions) not in {0, 1}:
                raise ValueError(f"Expected one point in {role} phase-centre anchor")
            anchors[role] = positions[0] if positions else None
        manifest["anchors_m"] = anchors
    ET.indent(xml, space="  ")
    ET.ElementTree(xml).write(output / "scene.xml", encoding="utf-8", xml_declaration=True)
    manifest["scene_xml_sha256"] = sha256(output / "scene.xml")
    write_json(output / "materials.json", records)
    write_json(output / "manifest.json", manifest)
    return manifest
