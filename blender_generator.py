from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict


def _hex_to_rgba(color: str) -> tuple[float, float, float, float]:
    color = color.lstrip("#")
    if len(color) != 6:
        return (0.8, 0.8, 0.8, 1.0)
    return tuple(int(color[i : i + 2], 16) / 255.0 for i in (0, 2, 4)) + (1.0,)


def _make_material(bpy, mat_name: str, material_spec: Dict[str, Any]):
    mat = bpy.data.materials.new(name=mat_name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf is None:
        return mat
    bsdf.inputs["Base Color"].default_value = _hex_to_rgba(material_spec.get("color", "#bbbbbb"))
    bsdf.inputs["Roughness"].default_value = float(material_spec.get("roughness", 0.6))
    bsdf.inputs["Metallic"].default_value = float(material_spec.get("metallic", 0.0))
    alpha = float(material_spec.get("alpha", 1.0))
    if alpha < 1.0:
        mat.blend_method = "BLEND"
        bsdf.inputs["Alpha"].default_value = max(0.0, min(1.0, alpha))
    return mat


def _clear_scene(bpy):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)


def _setup_camera(bpy, scene_spec: Dict[str, Any]):
    camera_spec = scene_spec.get("scene", {}).get("camera", {})
    bpy.ops.object.camera_add(location=tuple(camera_spec.get("position", [0, -6, 2.5])))
    cam = bpy.context.active_object
    cam.rotation_euler = tuple(camera_spec.get("rotation", [1.1, 0.0, 0.0]))
    cam.data.type = "ORTHO" if camera_spec.get("projection") == "orthographic" else "PERSP"
    if cam.data.type == "PERSP":
        fov = float(camera_spec.get("fov_degrees", 50.0))
        cam.data.angle = fov * 3.1415926 / 180.0
    bpy.context.scene.camera = cam


def _add_light(bpy, name: str, light_type: str, position, energy: float):
    data = bpy.data.lights.new(name=name, type=light_type)
    data.energy = energy
    obj = bpy.data.objects.new(name, data)
    obj.location = tuple(position)
    bpy.context.collection.objects.link(obj)


def _setup_lighting(bpy, scene_spec: Dict[str, Any]):
    lighting = scene_spec.get("scene", {}).get("lighting", {})
    _add_light(bpy, "KeyLight", "AREA", lighting.get("key", {}).get("position", [4, -4, 6]), float(lighting.get("key", {}).get("energy", 700)))
    _add_light(bpy, "FillLight", "AREA", lighting.get("fill", {}).get("position", [-4, -2, 3]), float(lighting.get("fill", {}).get("energy", 250)))
    _add_light(bpy, "BackLight", "POINT", lighting.get("back", {}).get("position", [0, 4, 4]), float(lighting.get("back", {}).get("energy", 200)))
    world = bpy.data.worlds["World"]
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[1].default_value = float(lighting.get("ambient_strength", 0.25))


def _setup_background(bpy, scene_spec: Dict[str, Any]):
    bg = scene_spec.get("scene", {}).get("background", {})
    bpy.ops.mesh.primitive_plane_add(size=12.0, location=(0, 0, 0))
    floor = bpy.context.active_object
    floor.name = "Floor"
    floor_mat = _make_material(
        bpy,
        "FloorMaterial",
        {
            "color": bg.get("color", "#bdbdbd"),
            "roughness": 0.8,
            "metallic": 0.0,
        },
    )
    floor.data.materials.append(floor_mat)


def _create_object(bpy, obj_spec: Dict[str, Any]):
    from object_library import OBJECT_GENERATORS

    primitive = str(obj_spec.get("primitive", "cube")).lower()
    object_class = str(obj_spec.get("class", "")).lower()
    creator = OBJECT_GENERATORS.get(object_class) or OBJECT_GENERATORS.get(primitive) or OBJECT_GENERATORS["cube"]

    obj = creator(
        bpy,
        bpy.context,
        obj_spec.get("id", "object"),
        obj_spec.get("position", [0, 0, 0.5]),
        obj_spec.get("rotation", [0, 0, 0]),
        obj_spec.get("scale", [1, 1, 1]),
    )
    mat = _make_material(
        bpy,
        f"Mat_{obj.name}",
        obj_spec.get("material", {"color": "#aaaaaa", "roughness": 0.6, "metallic": 0.0}),
    )
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)


def generate_scene(spec_path: Path, blend_path: Path, render_path: Path, width: int = 1024, height: int = 768):
    import bpy

    with spec_path.open("r", encoding="utf-8") as f:
        spec = json.load(f)

    _clear_scene(bpy)
    _setup_camera(bpy, spec)
    _setup_lighting(bpy, spec)
    _setup_background(bpy, spec)

    for obj_spec in spec.get("objects", []):
        _create_object(bpy, obj_spec)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.filepath = str(render_path)

    blend_path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    bpy.ops.render.render(write_still=True)


def _parse_args():
    parser = argparse.ArgumentParser(description="Generate Blender scene from scene_spec.json")
    parser.add_argument("--spec", required=True)
    parser.add_argument("--blend", required=True)
    parser.add_argument("--render", required=True)
    parser.add_argument("--width", type=int, default=1024)
    parser.add_argument("--height", type=int, default=768)
    return parser.parse_args()


def _main():
    args = _parse_args()
    generate_scene(Path(args.spec), Path(args.blend), Path(args.render), args.width, args.height)


if __name__ == "__main__":
    _main()
