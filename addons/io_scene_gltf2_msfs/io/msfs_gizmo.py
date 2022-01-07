# Copyright 2021-2022 The glTF-Blender-IO-MSFS authors.
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
import math
from typing import List

from io_scene_gltf2.io.com.gltf2_io_extensions import Extension


class GizmoObject:
    def __init__(self, translation: List[float] = None, type: str = None, params: dict = None, extensions: dict = None):
        self.translation = translation
        self.type = type
        self.params = params
        self.extensions = extensions


class MSFSGizmoExtension:
    extension_name = "ASOBO_gizmo_object"

    def __init__(self, gizmo_objects: List[GizmoObject] = None):
        self.gizmo_objects = gizmo_objects

    @staticmethod
    def from_dict(obj):
        assert isinstance(obj, dict)
        extension = obj.get(MSFSGizmoExtension.extension_name)
        if extension:
            gizmo_objects = []
            for gizmo_object in extension.get("gizmo_objects"):
                gizmo_objects.append(GizmoObject(**gizmo_object))
            return MSFSGizmoExtension(gizmo_objects=gizmo_objects)

    def to_extension(self, required=False):
        extension = Extension(name=MSFSGizmoExtension.extension_name, extension=self.__dict__, required=required)
        return extension


class MSFSGizmo():
    bl_options = {"UNDO"}

    def __new__(cls, *args, **kwargs):
            raise RuntimeError("%s should not be instantiated" % cls)

    @staticmethod
    def create(gltf_node, blender_object, import_settings): # TODO: clean this up, fix gizmo undo and drawing two gizmos on one empty
        gltf_mesh = import_settings.data.meshes[gltf_node.mesh]
        if gltf_mesh.extensions:
            extension = MSFSGizmoExtension.from_dict(gltf_mesh.extensions)
            if extension:
                for gizmo_object in extension.gizmo_objects:
                    bpy.ops.object.empty_add()
                    gizmo = bpy.context.object
                    if gizmo_object.type == "sphere":
                        gizmo.name = "Sphere Collision"
                    elif gizmo_object.type == "box":
                        gizmo.name = "Box Collision"
                    elif gizmo_object.type == "cylinder":
                        gizmo.name = "Cylinder Collision"

                    gizmo.location = gizmo_object.translation
                    gizmo.msfs_gizmo_type = gizmo_object.type

                    if gizmo_object.type == "sphere":
                        gizmo.scale[0] = gizmo_object.params.get("radius")
                        gizmo.scale[1] = gizmo_object.params.get("radius")
                        gizmo.scale[2] = gizmo_object.params.get("radius")
                    elif gizmo_object.type == "cylinder":
                        gizmo.scale[0] = gizmo_object.params.get("radius")
                        gizmo.scale[1] = gizmo_object.params.get("radius")
                        gizmo.scale[2] = gizmo_object.params.get("height")

                    if "Road" in gizmo_object.extensions:
                        gizmo.msfs_collision_is_road_collider = True

                    gizmo.parent = blender_object

                    # Set collection
                    for collection in gizmo.users_collection:
                        collection.objects.unlink(gizmo)
                    blender_object.users_collection[0].objects.link(gizmo)
                

    @staticmethod
    def export(gltf2_mesh, blender_mesh, export_settings):
        extension = MSFSGizmoExtension()
        for object in bpy.context.scene.objects:
            if object.type == "MESH" and bpy.data.meshes[object.data.name] == blender_mesh:
                for child in object.children:
                    if child.type == 'EMPTY' and child.msfs_gizmo_type != "NONE":
                        gizmo_object = GizmoObject()

                        gizmo_object.translation = list(child.location)
                        gizmo_object.type = child.msfs_gizmo_type

                        if child.msfs_gizmo_type == "sphere":
                            gizmo_object.params = {
                                "radius": abs(child.scale.x * child.scale.y * child.scale.z)
                            }
                        elif child.msfs_gizmo_type == "box":
                            gizmo_object.params = {
                                "length": abs(child.scale.x),
                                "width": abs(child.scale.y),
                                "height": abs(child.scale.z)
                            }
                        elif child.msfs_gizmo_type == "cylinder":
                            gizmo_object.params = {
                                "radius": abs(child.scale.x * child.scale.y),
                                "height": abs(child.scale.z)
                            }

                        tags = ["Collision"]
                        if child.msfs_collision_is_road_collider:
                            tags.append("Road")

                        gizmo_object.extensions = {
                            "ASOBO_tags": Extension(
                                name = "ASOBO_tags",
                                extension = {
                                    "tags": tags
                                },
                                required = False
                            )
                        }

                        if extension.gizmo_objects is None:
                            extension.gizmo_objects = []
                        extension.gizmo_objects.append(gizmo_object.__dict__)

        if extension.gizmo_objects:
            gltf2_mesh.extensions[MSFSGizmoExtension.extension_name] = extension.to_extension()
