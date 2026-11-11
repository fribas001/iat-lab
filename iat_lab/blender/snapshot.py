"""Capture reviewable scene metadata without changing or saving the loaded .blend."""

import hashlib
import json
from pathlib import Path

import bpy

from ..nodes import snapshot_group
from ..nodes.library import value
from ..project import sha256


def custom_properties(block):
    try:
        keys = list(block.keys())
    except TypeError:
        return {}
    return {key: value(block[key]) for key in sorted(keys) if key != "_RNA_UI"}


def dependencies():
    records = []
    for image in bpy.data.images:
        if image.source in {"FILE", "MOVIE", "SEQUENCE", "TILED"}:
            records.append(("image", image.name, image.filepath, bool(image.packed_file)))
    for library in bpy.data.libraries:
        records.append(("library", library.name, library.filepath, False))
    for font in bpy.data.fonts:
        if font.filepath != "<builtin>":
            records.append(("font", font.name, font.filepath, bool(font.packed_file)))
    for clip in bpy.data.movieclips:
        records.append(("movieclip", clip.name, clip.filepath, False))
    for sound in bpy.data.sounds:
        records.append(("sound", sound.name, sound.filepath, bool(sound.packed_file)))
    for cache in bpy.data.cache_files:
        records.append(("cache", cache.name, cache.filepath, False))
    return [{"type": kind, "name": name, "filepath": path, "packed": packed,
             "exists": packed or Path(bpy.path.abspath(path)).is_file()}
            for kind, name, path, packed in records]


def capture():
    path = Path(bpy.data.filepath) if bpy.data.filepath else None
    return {
        "schema_version": 2,
        "blender_version": bpy.app.version_string,
        "saved_file_sha256": sha256(path) if path and path.is_file() else None,
        "unsaved_changes": bpy.data.is_dirty,
        "scenes": [{"name": s.name, "object_count": len(s.objects),
                    "camera": s.camera.name if s.camera else None,
                    "units": s.unit_settings.system, "scale_length": s.unit_settings.scale_length,
                    "frame": s.frame_current,
                    "objects": sorted(o.name for o in s.objects)}
                   for s in sorted(bpy.data.scenes, key=lambda x: x.name)],
        "collections": [{"name": c.name, "objects": sorted(o.name for o in c.objects),
                         "children": sorted(child.name for child in c.children),
                         "hide_render": c.hide_render, "hide_viewport": c.hide_viewport}
                        for c in sorted(bpy.data.collections, key=lambda x: x.name)],
        "objects": [{"name": o.name, "type": o.type,
                     "matrix_world": [list(row) for row in o.matrix_world],
                     "dimensions": list(o.dimensions),
                     "hide_render": o.hide_render, "hide_viewport": o.hide_viewport,
                     "parent": o.parent.name if o.parent else None,
                     "materials": [s.material.name if s.material else None for s in o.material_slots],
                     "properties": custom_properties(o),
                     "modifiers": [{"name": m.name, "type": m.type,
                                    "node_group": getattr(getattr(m, "node_group", None), "name", None),
                                    "properties": custom_properties(m)} for m in o.modifiers]}
                    for o in sorted(bpy.data.objects, key=lambda x: x.name)],
        "node_groups": [snapshot_group(g) for g in sorted(bpy.data.node_groups, key=lambda x: x.name)],
        "dependencies": dependencies(),
        "modifier_inputs": [{"object": o.name, "modifier": m.name,
            "inputs": {s.name: {
                "mode": getattr(getattr(m.properties.inputs, s.identifier, None), "type", None),
                "value": value(getattr(getattr(m.properties.inputs, s.identifier, None), "value", None))}
                for s in m.node_group.interface.items_tree
                if s.item_type == "SOCKET" and s.in_out == "INPUT"}}
            for o in sorted(bpy.data.objects, key=lambda x: x.name) for m in o.modifiers
            if m.type == "NODES" and m.node_group and hasattr(m, "properties")],
        "view_layers": [{"scene": s.name, "view_layer": layer.name,
            "hidden_by_eye": sorted(o.name for o in layer.objects if o.hide_get(view_layer=layer))}
            for s in sorted(bpy.data.scenes, key=lambda x: x.name) for layer in s.view_layers],
        "embedded_texts": [{"name": t.name, "use_module": t.use_module,
                            "sha256": hashlib.sha256(t.as_string().encode("utf-8")).hexdigest()}
                           for t in sorted(bpy.data.texts, key=lambda x: x.name)],
    }


def write_snapshot(output):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(capture(), indent=2) + "\n", encoding="utf-8", newline="\n")
    return output


def export_texts(directory):
    """Export exact UTF-8 bytes. Refuse unsafe or duplicate text-block names."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    names = set()
    for text in bpy.data.texts:
        name = text.name
        if Path(name).name != name or name in {".", ".."} or any(c in name for c in '<>:"/\\|?*'):
            raise ValueError(f"Text block cannot be used as a filename: {name}")
        if name.casefold() in names:
            raise ValueError(f"Duplicate text filename: {name}")
        names.add(name.casefold())
    for text in bpy.data.texts:
        (directory / text.name).write_bytes(text.as_string().encode("utf-8"))
