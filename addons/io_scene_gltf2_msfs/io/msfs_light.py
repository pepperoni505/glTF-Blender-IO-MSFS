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

import math
from enum import Enum

from io_scene_gltf2.io.com.gltf2_io_extensions import Extension

class MSFSLightProperties(Enum):
    color = "color",
    intensity = "intensity",
    cone_angle = "cone_angle",
    has_symmetry = "has_symmetry",
    flash_frequency = "flash_frequency",
    flash_duration = "flash_duration",
    flash_phase = "flash_phase",
    rotation_speed = "rotation_speed",
    day_night_cycle = "day_night_cycle",

class MSFSLightExtension():
    extension_name = "ASOBO_macro_light"

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    @staticmethod
    def from_dict(obj):
        assert isinstance(obj, dict)
        extension = obj.get(MSFSLightExtension.extension_name)
        if extension:
            kwargs = {}
            for i in MSFSLightProperties:
                kwargs[i.name] = extension.get(i.value[0])
            return MSFSLightExtension(**kwargs)

    def to_extension(self, required=False):
        result = {}
        for i in MSFSLightProperties:
            result[i[1]] = self[i.name]

        extension = Extension(name=MSFSLightExtension.extension_name, extension=result, required=required)
        return extension


class MSFSLight():
    def __new__(cls, *args, **kwargs):
            raise RuntimeError("%s should not be instantiated" % cls)

    @staticmethod
    def create(gltf_node, blender_node, blender_light, import_settings):
        parent_light = import_settings.data.nodes[gltf_node.parent] # The glTF exporter creates the actual light as a child of the node that has the Asobo extension
        if parent_light.extensions:
            extension = MSFSLightExtension.from_dict(parent_light.extensions)
            if extension:
                # Set Blender light properties
                blender_light.color = extension.color
                blender_light.energy = extension.intensity
                if blender_light.type == "SPOT":
                    blender_light.spot_size = extension.cone_angle

                # Set MSFS light properties
                blender_node.msfs_light_has_symmetry = extension.has_symmetry
                blender_node.msfs_light_flash_frequency = extension.flash_frequency
                blender_node.msfs_light_flash_duration = extension.flash_duration
                blender_node.msfs_light_flash_phase = extension.flash_phase
                blender_node.msfs_light_rotation_speed = extension.rotation_speed
                blender_node.msfs_light_day_night_cycle = extension.day_night_cycle

    @staticmethod
    def export(gltf2_object, blender_object, export_settings):
        angle = 360.0
        if blender_object.data.type == 'SPOT':
            angle = (180.0 / math.pi) * blender_object.data.spot_size

        properties = {}
        properties[MSFSLightProperties.color.name] = blender_object.color
        properties[MSFSLightProperties.intensity.name] = blender_object.energy
        properties[MSFSLightProperties.cone_angle.name] = angle
        properties[MSFSLightProperties.has_symmetry.name] = blender_object.msfs_light_has_symmetry
        properties[MSFSLightProperties.flash_frequency.name] = blender_object.msfs_light_flash_frequency
        properties[MSFSLightProperties.flash_duration.name] = blender_object.msfs_light_flash_duration
        properties[MSFSLightProperties.flash_phase.name] = blender_object.msfs_light_flash_phase
        properties[MSFSLightProperties.rotation_speed.name] = blender_object.msfs_light_rotation_speed
        properties[MSFSLightProperties.day_night_cycle.name] = blender_object.msfs_light_day_night_cycle

        extension = MSFSLightExtension(**properties)
        gltf2_object.extensions[MSFSLightExtension.extension_name] = extension.to_extension()
