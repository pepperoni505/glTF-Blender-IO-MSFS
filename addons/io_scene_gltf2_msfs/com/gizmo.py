# Copyright 2021 The glTF-Blender-IO-MSFS authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import bpy
import bgl
import gpu
import bmesh
import numpy as np
from mathutils import Matrix
from gpu_extras.batch import batch_for_shader


class MSFSGizmoProperties():
    def gizmo_type_update(self, context):
        empties = MSFSCollisionGizmoGroup.empties
        object = context.object
        if object in empties.keys():
            if object.gizmo_type != empties[object].gizmo_type:
                empties[object].gizmo_type = object.gizmo_type
                empties[object].create_custom_shape()

    bpy.types.Object.gizmo_type = bpy.props.EnumProperty(
        name = "Type",
        description = "Type of collision gizmo to add",
        items = (("NONE", "Disabled", ""),
                ("sphere", "Sphere Collision Gizmo", ""),
                ("box", "Box Collision Gizmo", ""),
                ("cylinder", "Cylinder Collision Gizmo", "")
        ),
        update=gizmo_type_update
    )

class AddGizmo(bpy.types.Operator):
    bl_idname = "msfs_collision_gizmo.add_gizmo"
    bl_label = "Add MSFS Collision Gizmo"

    gizmo_type: bpy.types.Object.gizmo_type

    def execute(self, context):
        bpy.ops.object.empty_add()
        obj = context.active_object
        if self.gizmo_type == "sphere":
            obj.name = "Sphere Collision Gizmo"
        elif self.gizmo_type == "box":
            obj.name = "Box Collision Gizmo"
        elif self.gizmo_type == "cylinder":
            obj.name = "Cylinder Collision Gizmo"

        obj.gizmo_type = self.gizmo_type

        return {"FINISHED"}

class MSFSCollisionGizmo(bpy.types.Gizmo):
    bl_idname = "VIEW3D_GT_msfs_collision_gizmo"
    bl_label = "MSFS Collision Gizmo"

    bl_target_properties = (
        {"id": "matrix", "type": 'FLOAT', "array_length": 16}, # We can't actually store a matrix, so we "flatten" it and reconstruct it
    )

    __slots__ = (
        "empty",
        "gizmo_type",
        "custom_shape",
        "custom_shape_edges",
    )

    def _update_offset_matrix(self):
        pass

    def setup(self):
        if not hasattr(self, "custom_shape"):
            self.custom_shape = None

    def draw_line_3d(self, color, width, region, pos):
        shader = gpu.shader.from_builtin('3D_POLYLINE_UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'LINES', {"pos": pos})
        shader.bind()
        shader.uniform_float("color", color)
        shader.uniform_float("lineWidth", width)
        shader.uniform_float("viewportSize", (region.width, region.height))
        batch.draw(shader)

    def create_custom_shape(self):
        bm = bmesh.new()
        if self.gizmo_type == "sphere":
            bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=8, radius=1)
        elif self.gizmo_type == "box":
            bmesh.ops.create_cube(bm, size=2)
        elif self.gizmo_type == "cylinder":
            bmesh.ops.create_cone(bm, cap_ends=True, segments=32, radius1=1, radius2=1, depth=2) # Create cone with both ends having the same diameter - this creates a cylinder

        mesh = bpy.data.meshes.new("Gizmo Mesh")
        bm.to_mesh(mesh)
        bm.free()

        edges = []
        for edge in mesh.edges:
            edge_verts = []
            for vert in edge.vertices:
                edge_verts.append(mesh.vertices[vert])
            edges.append(edge_verts)

        self.custom_shape_edges = edges

    def get_matrix(self):
        matrix = self.target_get_value("matrix")
        formatted_matrix = Matrix()
        for i in range(4):
            for j in range(4):
                formatted_matrix[i][j] = matrix[i * 4 + j]

        return formatted_matrix

    def draw(self, context):
        if self.custom_shape_edges and not self.empty.hide_get():
            matrix = self.get_matrix()

            bgl.glEnable(bgl.GL_BLEND)
            bgl.glEnable(bgl.GL_LINE_SMOOTH)
            bgl.glEnable(bgl.GL_DEPTH_TEST)

            # Use Blender theme colors to keep everything consistent
            draw_color = list(context.preferences.themes[0].view_3d.empty)
            if self.empty.select_get():
                draw_color = list(context.preferences.themes[0].view_3d.object_active)
            
            draw_color.append(1) # Add alpha (there isn't any functions in the Color class to add an alpha, so we have to convert to a list)

            vertex_pos = []
            for edge in self.custom_shape_edges:
                line_start = self.apply_vert_transforms(edge[0], matrix=matrix)
                line_end = self.apply_vert_transforms(edge[1], matrix=matrix)

                vertex_pos.extend([line_start, line_end])

            self.draw_line_3d(draw_color, 2, context.region, vertex_pos)

            # Restore OpenGL defaults
            bgl.glLineWidth(1)
            bgl.glDisable(bgl.GL_BLEND)
            bgl.glDisable(bgl.GL_LINE_SMOOTH)

    def apply_vert_transforms(self, vert, matrix):
        vert = list(vert.co)
        vert.append(1)
        multiplied_matrix = np.array(matrix).dot(np.array(vert))
        return multiplied_matrix[:-1].tolist()

class MSFSCollisionGizmoGroup(bpy.types.GizmoGroup):
    bl_idname = "VIEW3D_GT_msfs_collision_gizmo_group"
    bl_label = "MSFS Collision Gizmo Group"
    bl_space_type = "VIEW_3D"
    bl_region_type = "WINDOW"
    bl_options = {'3D', 'PERSISTENT', 'SHOW_MODAL_ALL', 'SELECT'}

    empties = {}

    @classmethod
    def poll(cls, context):
        for object in context.view_layer.objects:
            if object.type == 'EMPTY' and object.gizmo_type != "NONE":
                return True
        return False

    def setup(self, context):
        for object in context.view_layer.objects:
            if object.type == 'EMPTY' and object.gizmo_type != "NONE" and object not in self.__class__.empties.keys():
                def get_matrix():
                    # Re-calculate matrix without rotation
                    if object.gizmo_type == "sphere":
                        scale_matrix = Matrix.Scale(object.scale[0] * object.scale[1] * object.scale[2], 4, (1, 0, 0)) @ Matrix.Scale(object.scale[0] * object.scale[1] * object.scale[2], 4, (0, 1, 0)) @ Matrix.Scale(object.scale[0] * object.scale[1] * object.scale[2], 4, (0, 0, 1))
                    elif object.gizmo_type == "cylinder":
                        scale_matrix = Matrix.Scale(object.scale[0] * object.scale[1], 4, (1, 0, 0)) @ Matrix.Scale(object.scale[0] * object.scale[1], 4, (0, 1, 0)) @ Matrix.Scale(object.scale[2], 4, (0, 0, 1))
                    else:
                        scale_matrix = Matrix.Scale(object.scale[0], 4, (1, 0, 0)) @ Matrix.Scale(object.scale[1], 4, (0, 1, 0)) @ Matrix.Scale(object.scale[2], 4, (0, 0, 1))
                    object_matrix = Matrix.Translation(object.location) @ scale_matrix

                    matrix = []
                    for i in range(4):
                        for j in range(4):
                            matrix.append(object_matrix[i][j])
                    return matrix
                def set_matrix(matrix):
                    object.matrix_world = matrix

                gz = self.gizmos.new(MSFSCollisionGizmo.bl_idname)

                gz.gizmo_type = object.gizmo_type
                gz.empty = object

                gz.target_set_handler("matrix", get=get_matrix, set=set_matrix)
                gz.create_custom_shape()

                self.__class__.empties[object] = gz

    def refresh(self, context):
        # We have to get a list of gizmo empties in the scene first in order to avoid a crash due to referencing a removed object
        found_empties = []
        for object in context.view_layer.objects:
            if object.type == 'EMPTY' and object.gizmo_type != "NONE":
                found_empties.append(object)

        for _, (empty, gizmo) in enumerate(self.__class__.empties.copy().items()):
            if empty not in found_empties:
                self.gizmos.remove(gizmo)
                del self.__class__.empties[empty]

        # Check if there are any new gizmo empties, and if so create new gizmo. We can't do this in the above loop due to the crash mentioned above
        for object in context.view_layer.objects:
            if object.type == 'EMPTY' and object.gizmo_type != "NONE":
                if object not in self.__class__.empties.keys():
                    self.setup(context)


class MSFSCollisionAddMenu(bpy.types.Menu):
    bl_idname = "VIEW3D_MT_msfs_collision_add_menu"
    bl_label = "Flight Simulator Collision"

    def draw(self, context):
        self.layout.operator(AddGizmo.bl_idname, text="Add Sphere Collision Gizmo", icon="MESH_UVSPHERE").gizmo_type = "sphere"
        self.layout.operator(AddGizmo.bl_idname, text="Add Box Collision Gizmo", icon="MESH_CUBE").gizmo_type = "box"
        self.layout.operator(AddGizmo.bl_idname, text="Add Cylinder Collision Gizmo", icon="MESH_CYLINDER").gizmo_type = "cylinder"

def draw_menu(self, context):
    self.layout.menu(menu=MSFSCollisionAddMenu.bl_idname, icon="SHADING_BBOX")

def register():
    bpy.types.VIEW3D_MT_add.append(draw_menu)

def unregister():
    bpy.types.VIEW3D_MT_add.remove(draw_menu)