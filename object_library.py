from __future__ import annotations


def _apply_transform(obj, position, rotation, scale):
    obj.location = position
    obj.rotation_euler = rotation
    obj.scale = scale


def _join_created(context, name, created):
    if not created:
        return None
    if len(created) == 1:
        created[0].name = name
        return created[0]
    for o in created:
        o.select_set(True)
        context.view_layer.objects.active = o
    import bpy

    bpy.ops.object.join()
    joined = context.view_layer.objects.active
    joined.name = name
    return joined


def create_cube(bpy, context, name, position, rotation, scale):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0))
    obj = context.active_object
    obj.name = name
    _apply_transform(obj, position, rotation, scale)
    return obj


def create_plane(bpy, context, name, position, rotation, scale):
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 0, 0))
    obj = context.active_object
    obj.name = name
    _apply_transform(obj, position, rotation, scale)
    return obj


def create_cylinder(bpy, context, name, position, rotation, scale):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=1.0, location=(0, 0, 0))
    obj = context.active_object
    obj.name = name
    _apply_transform(obj, position, rotation, scale)
    return obj


def create_sphere(bpy, context, name, position, rotation, scale):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(0, 0, 0))
    obj = context.active_object
    obj.name = name
    _apply_transform(obj, position, rotation, scale)
    return obj


def create_panel(bpy, context, name, position, rotation, scale):
    return create_cube(bpy, context, name, position, rotation, [scale[0], scale[1], max(0.03, scale[2])])


def create_table(bpy, context, name, position, rotation, scale):
    parts = []
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.45))
    top = context.active_object
    top.scale = (0.7, 0.4, 0.06)
    parts.append(top)
    leg_offsets = [(-0.6, -0.3), (0.6, -0.3), (-0.6, 0.3), (0.6, 0.3)]
    for ox, oy in leg_offsets:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(ox * 0.7, oy * 0.4, 0.2))
        leg = context.active_object
        leg.scale = (0.05, 0.05, 0.35)
        parts.append(leg)
    obj = _join_created(context, name, parts)
    _apply_transform(obj, position, rotation, scale)
    return obj


def create_chair(bpy, context, name, position, rotation, scale):
    parts = []
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.25))
    seat = context.active_object
    seat.scale = (0.35, 0.35, 0.06)
    parts.append(seat)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, -0.27, 0.6))
    back = context.active_object
    back.scale = (0.35, 0.05, 0.3)
    parts.append(back)
    leg_offsets = [(-0.28, -0.28), (0.28, -0.28), (-0.28, 0.28), (0.28, 0.28)]
    for ox, oy in leg_offsets:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(ox, oy, 0.1))
        leg = context.active_object
        leg.scale = (0.04, 0.04, 0.18)
        parts.append(leg)
    obj = _join_created(context, name, parts)
    _apply_transform(obj, position, rotation, scale)
    return obj


def create_sofa(bpy, context, name, position, rotation, scale):
    parts = []
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.25))
    base = context.active_object
    base.scale = (0.9, 0.4, 0.25)
    parts.append(base)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, -0.35, 0.65))
    back = context.active_object
    back.scale = (0.9, 0.08, 0.35)
    parts.append(back)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-0.95, 0, 0.45))
    arm_l = context.active_object
    arm_l.scale = (0.08, 0.4, 0.2)
    parts.append(arm_l)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.95, 0, 0.45))
    arm_r = context.active_object
    arm_r.scale = (0.08, 0.4, 0.2)
    parts.append(arm_r)
    obj = _join_created(context, name, parts)
    _apply_transform(obj, position, rotation, scale)
    return obj


def create_bed(bpy, context, name, position, rotation, scale):
    parts = []
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.2))
    base = context.active_object
    base.scale = (1.0, 1.6, 0.2)
    parts.append(base)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0.9, 0.45))
    headboard = context.active_object
    headboard.scale = (1.0, 0.06, 0.35)
    parts.append(headboard)
    obj = _join_created(context, name, parts)
    _apply_transform(obj, position, rotation, scale)
    return obj


def create_lamp(bpy, context, name, position, rotation, scale):
    parts = []
    bpy.ops.mesh.primitive_cylinder_add(radius=0.06, depth=0.8, location=(0, 0, 0.4))
    stem = context.active_object
    parts.append(stem)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.22, location=(0, 0, 0.88))
    shade = context.active_object
    shade.scale = (1.0, 1.0, 0.55)
    parts.append(shade)
    obj = _join_created(context, name, parts)
    _apply_transform(obj, position, rotation, scale)
    return obj


def create_monitor(bpy, context, name, position, rotation, scale):
    parts = []
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.4))
    panel = context.active_object
    panel.scale = (0.55, 0.05, 0.35)
    parts.append(panel)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.03, depth=0.25, location=(0, 0, 0.17))
    stem = context.active_object
    parts.append(stem)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.05))
    base = context.active_object
    base.scale = (0.25, 0.18, 0.03)
    parts.append(base)
    obj = _join_created(context, name, parts)
    _apply_transform(obj, position, rotation, scale)
    return obj


def create_cabinet(bpy, context, name, position, rotation, scale):
    return create_cube(bpy, context, name, position, rotation, [scale[0], scale[1], scale[2]])


OBJECT_GENERATORS = {
    "cube": create_cube,
    "box": create_cube,
    "plane": create_plane,
    "panel": create_panel,
    "cylinder": create_cylinder,
    "sphere": create_sphere,
    "table": create_table,
    "chair": create_chair,
    "sofa": create_sofa,
    "bed": create_bed,
    "lamp": create_lamp,
    "monitor": create_monitor,
    "tv": create_monitor,
    "cabinet": create_cabinet,
}
