# Copyright 2021 The FlightSim-glTF-Blender-IO authors.
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
from enum import Enum

class MaterialTypes(Enum):
    Disabled = 0, "NONE", "Disabled"
    Standard = 1, "msfs_standard", "Standard"
    Decal = 2, "msfs_decal", "Decal"
    GeoDecalFrosted = 3, "msfs_geo_decal", "Geo Decal Frosted"
    Windshield = 4, "msfs_windshield", "Windshield"
    Porthole = 5, "msfs_porthole", "Porthole"
    Glass = 6, "msfs_glass", "Glass"
    ClearCoat = 7, "msfs_clearcoat", "Clearcoat"
    ParallaxWindow = 8, "msfs_parallax", "Parallax"
    Anisotropic = 9, "msfs_anisotropic", "Anisotropic"
    Hair = 10, "msfs_hair", "Hair"
    SSS = 11, "msfs_sss", "SSS"
    Invisible = 12, "msfs_invisible", "Invisible" # TODO: might be ghost?
    FakeTerrain = 13, "msfs_fake_terrain", "FakeTerrain"
    FresnelFade = 14, "msfs_fresnel", "Fresnel Fade"
    EnvironmentOccluder = 15, "msfs_env_occluder", "Environment Occluder"

    @staticmethod
    def getTypes():
        types = ()
        for type in MaterialTypes:
            types.append(type.value[1], type.value[2], "")


class Material:

    def __init__(self, type):
        self.type = bpy.props.EnumProperty(items=MaterialTypes.getTypes())

        self.base_color = None

        self.emissive = None


        self.alpha_mode = bpy.types.EnumProperty(name = "Alpha Mode",
            items = (("opaque", "Opaque", ""),
                    ("mask", "Mask", ""),
                    ("blend", "Blend", ""),
                    ("dither", "Dither", ""))
        )

        # Render Parameters
        self.draw_order = 0 # TODO: collection property
        self.dont_cast_shadows = False
        self.double_sided = False
        self.day_night_cycle = False

        # Gameplay Parameters
        self.collision_material = False
        self.road_collision_material = False

        # UV Options
        self.uv_offset_u = 0
        self.uv_offset_v = 0 

        self.uv_tiling_u = 0
        self.uv_tiling_v = 0

        self.uv_rotation = 0

        self.uv_clamp_u = False
        self.uv_clamp_v = False

        # General Parameters
        self.roughness = 0
        self.metallic = 0
        self.normal_scale = 0
        self.alpha_cutoff = 0

        self.detail_uv_scale = 0
        self.detail_uv_offset_u = 0
        self.detail_uv_offset_v = 0
        self.detail_normal_scale = 0
        self.blend_threshold = 0

        self.rain_drop_scale = 0
        self.wiper1_state = 0
        self.wiper2_state = 0



class Standard(Material):

    use_pearl_effect = bpy.props.BoolProperty(name="Use Pearl Effect", default=False)
    pearl_color_shift = bpy.props.FloatProperty(name="Color Shift", default=0)
    pearl_color_range = bpy.props.FloatProperty(name="Color Range", default=0)
    pearl_color_brightness = bpy.props.FloatProperty(name="Color Brightness", default=0)

    def __init__(self):
        super().__init__(MaterialTypes.Standard)


class Decal(Material):

    bpy.types.Material.msfs_decal_color = bpy.props.FloatProperty(name="Color", min=0, max=1, default=0)
    bpy.types.Material.msfs_decal_metal = bpy.props.FloatProperty(name="Metal", min=0, max=1, default=0)
    bpy.types.Material.msfs_decal_normal = bpy.props.FloatProperty(name="Normal", min=0, max=1, default=0)
    bpy.types.Material.msfs_decal_roughness = bpy.props.FloatProperty(name="Roughness", min=0, max=1, default=0)
    bpy.types.Material.msfs_decal_occlusion = bpy.props.FloatProperty(name="Occlusion", min=0, max=1, default=0)
    bpy.types.Material.msfs_decal_emissive = bpy.props.FloatProperty(name="Emissive", min=0, max=1, default=0)

    def __init__(self):
        super().__init__(MaterialTypes.GeoDecalFrosted)


class GeoDecalFrosted(Decal):

    bpy.types.Material.msfs_geo_decal_blend_factor_color = bpy.props.FloatProperty(name="Color", min=0, max=1, default=0)
    bpy.types.Material.msfs_geo_decal_blend_factor_metal = bpy.props.FloatProperty(name="Metal", min=0, max=1, default=0)
    bpy.types.Material.msfs_geo_decal_blend_factor_normal = bpy.props.FloatProperty(name="Normal", min=0,max=1, default=0)
    bpy.types.Material.msfs_geo_decal_blend_factor_roughness = bpy.props.FloatProperty(name="Roughness", min=0, max=1, default=0)
    bpy.types.Material.msfs_geo_decal_blend_factor_blast_sys = bpy.props.FloatProperty(name="Blast Sys", min=0, max=1, default=0)
    bpy.types.Material.msfs_geo_decal_blend_factor_melt_sys = bpy.props.FloatProperty(name="Melt Sys", min=0, max=1, default=0)

    def __init__(self):
        super().__init__(MaterialTypes.GeoDecalFrosted)


class Windshield(Material):

    def __init__(self):
        super().__init__(MaterialTypes.Windshield)


class Porthole(Material):

    def __init__(self):
        super().__init__(MaterialTypes.Porthole)


class Glass(Material):

    bpy.types.Material.msfs_glass_reflection_mask_factor = bpy.props.FloatProperty(name="Glass Reflection Mask Factor", min=0, max=1, default=0)
    bpy.types.Material.msfs_glass_deformation_factor = bpy.props.FloatProperty(name="Glass Deformation Factor", min=0, max=1, default=0)

    def __init__(self):
        super().__init__(MaterialTypes.Glass)


class ClearCoat(Material):

    def __init__(self):
        super().__init__(MaterialTypes.ClearCoat)


class ParallaxWindow(Material):

    bpy.types.Material.msfs_parallax_scale = bpy.props.FloatProperty(name="Parallax Scale", default=0)
    bpy.types.Material.msfs_parallax_room_scale_x = bpy.props.FloatProperty(name="Room Scale X", default=0)
    bpy.types.Material.msfs_parallax_room_scale_y = bpy.props.FloatProperty(name="Room Scale Y", default=0)
    bpy.types.Material.msfs_parallax_room_number_xy = bpy.props.IntProperty(name="Room Number XY", default=0)
    bpy.types.Material.msfs_parallax_corridor = bpy.props.BoolProperty(name="Corridor", default=False)

    def __init__(self):
        super().__init__(MaterialTypes.ParallaxWindow)


class Anisotropic(Material):

    def __init__(self):
        super().__init__(MaterialTypes.Anisotropic)


class Hair(Material):

    def __init__(self):
        super().__init__(MaterialTypes.Hair)


class SSS(Material):

    def __init__(self):
        super().__init__(MaterialTypes.SSS)


class Invisible(Material):

    def __init__(self):
        super().__init__(MaterialTypes.Invisible)


class FakeTerrain(Material):

    def __init__(self):
        super().__init__(MaterialTypes.FakeTerrain)


class FresnelFade(Material):

    bpy.types.Material.msfs_fresnel_factor = bpy.props.FloatProperty(name="Fresnel Factor", default=0)
    bpy.types.Material.msfs_fresnel_opacity_bias = bpy.props.FloatProperty(name="Fresnel Opacity Bias", default=0)

    def __init__(self):
        super().__init__(MaterialTypes.FresnelFade)


class EnvironmentOccluder(Material):

    def __init__(self):
        super().__init__(MaterialTypes.EnvironmentOccluder)
