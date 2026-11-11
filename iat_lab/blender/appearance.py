"""Self-contained procedural preview shaders, independent of radio properties."""

import bpy


def apply_preview_materials():
    """Style the canonical materials without changing RF metadata or geometry."""
    palettes = {
        "itu_wood": ((0.11, 0.045, 0.015, 1), (0.25, 0.13, 0.05, 1), (0.45, 0.29, 0.14, 1)),
        "itu_plywood": ((0.22, 0.12, 0.055, 1), (0.39, 0.24, 0.11, 1), (0.58, 0.40, 0.22, 1)),
        # The supplied laboratory photos show a dark-faced RIS backing board.
        "itu_chipboard": ((0.006, 0.007, 0.009, 1), (0.012, 0.014, 0.018, 1), (0.020, 0.024, 0.030, 1)),
        "itu_concrete": ((0.32, 0.33, 0.34, 1), (0.40, 0.41, 0.42, 1), (0.48, 0.49, 0.50, 1)),
        "iat_absorber_proxy": ((0.012, 0.045, 0.12, 1), (0.020, 0.075, 0.20, 1), (0.035, 0.11, 0.28, 1)),
        "itu_metal": ((0.07, 0.075, 0.08, 1), (0.10, 0.105, 0.11, 1), (0.13, 0.135, 0.14, 1)),
    }
    for name, colors in palettes.items():
        mat = bpy.data.materials.get(name)
        if mat is None:
            continue
        wood = name in {"itu_wood", "itu_plywood", "itu_chipboard"}
        foam = name == "iat_absorber_proxy"
        metal = name == "itu_metal"
        mat.use_nodes = True
        tree = mat.node_tree
        tree.nodes.clear()

        def node(kind, label, location):
            result = tree.nodes.new(kind)
            result.label = label
            result.location = location
            result.width = 190
            return result

        coordinates = node("ShaderNodeTexCoord", "Procedural coordinates; no image files", (-950, 250))
        mapping = node("ShaderNodeVectorMath", "Grain direction / texture scale", (-720, 250))
        mapping.operation = "MULTIPLY"
        mapping.inputs[1].default_value = (7, 7, 0.6) if wood else (1, 1, 1)
        tree.links.new(coordinates.outputs["Generated" if wood else "Object"], mapping.inputs[0])
        noise = node("ShaderNodeTexNoise", "Wood fibers" if wood else "Fine surface variation", (-480, 250))
        noise.inputs["Scale"].default_value = 5 if wood else (550 if foam else 90)
        noise.inputs["Detail"].default_value = 3
        noise.inputs["Roughness"].default_value = 0.65
        noise.inputs["Distortion"].default_value = 0.25 if wood else 0
        tree.links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
        ramp = node("ShaderNodeValToRGB", "Surface color range", (-230, 350))
        ramp.color_ramp.elements[0].position = 0.18
        ramp.color_ramp.elements[0].color = colors[0]
        ramp.color_ramp.elements[1].position = 0.82
        ramp.color_ramp.elements[1].color = colors[2]
        ramp.color_ramp.elements.new(0.50).color = colors[1]
        tree.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
        bump = node("ShaderNodeBump", "Shading relief only; no mesh displacement", (-200, 0))
        bump.inputs["Strength"].default_value = 0.18 if wood else (0.28 if foam else 0.12)
        bump.inputs["Distance"].default_value = 0.0003 if wood or metal else 0.0006
        tree.links.new(noise.outputs["Fac"], bump.inputs["Height"])
        surface = node("ShaderNodeBsdfPrincipled", "Optical appearance, independent of RF model", (80, 300))
        surface.inputs["Roughness"].default_value = 0.48 if wood else (0.93 if foam else (0.38 if metal else 0.82))
        surface.inputs["Metallic"].default_value = 0.85 if metal else 0
        tree.links.new(ramp.outputs["Color"], surface.inputs["Base Color"])
        tree.links.new(bump.outputs["Normal"], surface.inputs["Normal"])
        output = node("ShaderNodeOutputMaterial", "Cycles / Eevee surface", (420, 300))
        tree.links.new(surface.outputs["BSDF"], output.inputs["Surface"])
        mat.diffuse_color = colors[1]
        mat["iat_appearance"] = "Procedural preview finish; illustrative, not a measured lab finish"
        mat["iat_appearance_version"] = 1

    # Keep fibers along each wooden part's longest axis, including horizontal
    # table boards. Preview variants retain the same canonical RF key/record.
    for obj in bpy.data.objects:
        materials = getattr(obj.data, "materials", None)
        if materials is None:
            continue
        axis = max(range(3), key=lambda i: obj.dimensions[i])
        if axis == 2:
            continue
        for index, mat in enumerate(list(materials)):
            if mat is None or mat.name not in {"itu_wood", "itu_plywood", "itu_chipboard"}:
                continue
            variant_name = mat.name + "_grain_" + "xyz"[axis]
            variant = bpy.data.materials.get(variant_name)
            if variant is None:
                variant = mat.copy()
                variant.name = variant_name
                mapping = next(n for n in variant.node_tree.nodes if n.label == "Grain direction / texture scale")
                scale = [7.0, 7.0, 7.0]
                scale[axis] = 0.6
                mapping.inputs[1].default_value = scale
            materials[index] = variant
