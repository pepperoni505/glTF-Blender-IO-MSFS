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

import os
import bpy
import math

from io_scene_gltf2.io.com.gltf2_io_extensions import Extension
from io_scene_gltf2.blender.imp.gltf2_blender_image import BlenderImage


class MSFSMaterial:
    bl_options = {"UNDO"}

    extension_name = "ASOBO_macro_light"

    def __new__(cls, *args, **kwargs):
        raise RuntimeError("%s should not be instantiated" % cls)

    
    @staticmethod
    def create_image(index, import_settings):
        pytexture = import_settings.data.textures[index]
        BlenderImage.create(import_settings, pytexture.source)
        pyimg = import_settings.data.images[pytexture.source]

        # Find image created
        if pyimg.name in bpy.data.images:
            return bpy.data.images[pyimg.name]
        elif os.path.basename(pyimg.uri in bpy.data.images):
            return bpy.data.images[pyimg.uri]
        elif "Image_%d" % index in bpy.data.images:
            return bpy.data.images["Image_%d" % index]

    @staticmethod
    def create(gltf_material, blender_material, import_settings):
        # Set material type
        material_type = None
        if gltf_material.extras.get("ASOBO_material_code") == "GeoDecalFrosted":
            material_type = "msfs_geo_decal"
        elif gltf_material.extras.get("ASOBO_material_code") == "Porthole":
            material_type = "msfs_porthole"
        elif gltf_material.extras.get("ASOBO_material_code") == "Windshield":
            material_type = "msfs_windshield"

        if not material_type: # Because some materials share the extension name, we need to check the extras first for material type
            if "ASOBO_material_anisotropic" in gltf_material.extensions:
                material_type = "msfs_anisotropic"
            elif "ASOBO_material_SSS" in gltf_material.extensions: # This is both hair and SSS, as they share the same properties
                material_type = "msfs_sss"
            elif "ASOBO_material_glass" in gltf_material.extensions:
                material_type = "msfs_glass"
            elif "ASOBO_material_blend_gbuffer" in gltf_material.extensions:
                material_type = "msfs_decal"
            elif "ASOBO_material_clear_coat" in gltf_material.extensions:
                material_type = "msfs_clearcoat"
            elif "ASOBO_material_fake_terrain" in gltf_material.extensions:
                material_type = "msfs_fake_terrain"
            elif "ASOBO_material_fresnel_fade" in gltf_material.extensions:
                material_type = "msfs_fresnel"
            elif "ASOBO_material_parallax_window" in gltf_material.extensions:
                material_type = "msfs_parallax"
            elif "ASOBO_material_environment_occluder" in gltf_material.extensions:
                material_type = "msfs_env_occluder"
            elif "ASOBO_material_invisible" in gltf_material.extensions:
                material_type = "msfs_invisible"
            else:
                for key in gltf_material.extensions.keys(): # Check all extensions and see if any Asobo extensions are present, and if so, it's a standard material
                    if key.upper().startswith("ASOBO_"):
                        material_type = "msfs_standard"


        blender_material.msfs_material_mode = material_type

        # Set blendmode
        if gltf_material.extensions.get("ASOBO_material_alphamode_dither", {}).get("enabled"):
            blender_material.blend_mode = "DITHER"

        # Set Asobo tags
        tags = gltf_material.extensions.get("ASOBO_tags")
        if tags:
            if "Road" in tags:
                gltf_material.msfs_road_material = True
            if "Collision" in tags:
                gltf_material.msfs_collision_material = True

        # Day/Night cycle
        if gltf_material.extensions.get("ASOBO_material_day_night_switch", {}).get("enabled"):
            gltf_material.msfs_day_night_cycle = True

        # Windshield options
        windshield = gltf_material.extensions.get("ASOBO_material_windshield_v2") # TODO: maybe add support for v1?
        if windshield:
            blender_material.msfs_rain_drop_scale = windshield.get("rainDropScale")
            blender_material.msfs_wiper_1_state = windshield.get("wiper1State")
            blender_material.msfs_wiper_2_state = windshield.get("wiper2State")
            blender_material.msfs_wiper_3_state = windshield.get("wiper3State")
            blender_material.msfs_wiper_4_state = windshield.get("wiper4State")

        # Draw order
        draw_order = gltf_material.extensions.get("ASOBO_material_draw_order")
        if draw_order:
            blender_material.msfs_draw_order = draw_order.get("drawOrderOffset")

        # Cast shadow
        cast_shadow = gltf_material.extensions.get("ASOBO_material_shadow_options")
        if cast_shadow:
            blender_material.msfs_no_cast_shadow = cast_shadow.get("noCastShadow")

        # Pearlescent
        pearl = gltf_material.extensions.get("ASOBO_material_pearlescent")
        if pearl:
            blender_material.msfs_pearl_shift = pearl.get("pearlShift")
            blender_material.msfs_pearl_range = pearl.get("pearlRange")
            blender_material.msfs_pearl_brightness = pearl.get("pearlBrightness")

        # UV Options
        uv_options = gltf_material.extensions.get("ASOBO_material_UV_options")
        if uv_options:
            blender_material.msfs_ao_use_uv2 = uv_options.get("AOUseUV2")
            blender_material.msfs_uv_clamp_x = uv_options.get("clampUVX")
            blender_material.msfs_uv_clamp_y = uv_options.get("clampUVY")
            blender_material.msfs_uv_clamp_z = uv_options.get("clampUVZ")

        # Detail maps
        detail_map = gltf_material.extensions.get("ASOBO_material_detail_map")
        if detail_map:
            detail_color_index = detail_map.get("detailColorTexture", {}).get("index")
            if detail_color_index is not None:
                blender_material.msfs_detail_albedo_texture = MSFSMaterial.create_image(detail_color_index, import_settings)

            detail_metal_index = detail_map.get("detailMetalRoughAOTexture", {}).get("index")
            if detail_metal_index is not None:
                blender_material.msfs_detail_metallic_texture = MSFSMaterial.create_image(detail_metal_index, import_settings)

            detail_normal_index = detail_map.get("detailNormalTexture", {}).get("index")
            if detail_normal_index is not None:
                blender_material.msfs_detail_normal_texture = MSFSMaterial.create_image(detail_normal_index, import_settings)

            blender_material.msfs_detail_uv_scale = detail_map.get("UVScale")
            blender_material.msfs_detail_uv_offset_x = detail_map.get("UVOffset")[0]
            blender_material.msfs_detail_uv_offset_y = detail_map.get("UVOffset")[1]
            blender_material.msfs_blend_threshold = detail_map.get("blendTreshold")
        

        # Blend gbuffer
        blend_gbuffer = gltf_material.extensions.get("ASOBO_material_blend_gbuffer")
        if blend_gbuffer:
            if material_type == "msfs_decal": # Decal and geo decal share properties but with different variable names
                blender_material.msfs_decal_blend_factor_color = blend_gbuffer.get("baseColorBlendFactor")
                blender_material.msfs_decal_blend_factor_metal = blend_gbuffer.get("metallicBlendFactor")
                blender_material.msfs_decal_blend_factor_roughness = blend_gbuffer.get("roughnessBlendFactor")
                blender_material.msfs_decal_blend_factor_normal = blend_gbuffer.get("normalBlendFactor")
                blender_material.msfs_decal_blend_factor_emissive = blend_gbuffer.get("emissiveBlendFactor")
                blender_material.msfs_decal_blend_factor_occlusion = blend_gbuffer.get("occlusionBlendFactor")
            else:
                blender_material.msfs_geo_decal_blend_factor_color = blend_gbuffer.get("baseColorBlendFactor")
                blender_material.msfs_geo_decal_blend_factor_metal = blend_gbuffer.get("metallicBlendFactor")
                blender_material.msfs_geo_decal_blend_factor_roughness = blend_gbuffer.get("roughnessBlendFactor")
                blender_material.msfs_geo_decal_blend_factor_normal = blend_gbuffer.get("normalBlendFactor")
                blender_material.msfs_geo_decal_blend_factor_melt_sys = blend_gbuffer.get("emissiveBlendFactor")
                blender_material.msfs_geo_decal_blend_factor_blast_sys = blend_gbuffer.get("occlusionBlendFactor")

        # SSS
        if material_type == "msfs_sss":
            sss_extension = blender_material.extensions.get("ASOBO_material_SSS", {})

            blender_material.msfs_color_sss = sss_extension.get("SSSColor")

        # Glass
        elif material_type == "msfs_glass":
            glass_extension = blender_material.extensions.get("ASOBO_material_glass", {})

            blender_material.msfs_glass_reflection_mask_factor = glass_extension.get("glassReflectionMaskFactor")
            blender_material.msfs_glass_deformation_factor = glass_extension.get("glassDeformationFactor")

        # Clearcoat
        elif material_type == "msfs_clearcoat":
            clearcoat_extension = blender_material.extensions.get("ASOBO_material_clear_coat", {})

            dirt_index = clearcoat_extension.get("dirtTexture", {}).get("index")
            if dirt_index is not None:
                blender_material.msfs_clearcoat_texture = MSFSMaterial.create_image(dirt_index, import_settings)

        # Fresnel
        elif material_type == "msfs_fresnel":
            fresnel_extension = blender_material.extensions.get("ASOBO_material_fresnel_fade", {})

            blender_material.msfs_fresnel_factor = fresnel_extension.get("fresnelFactor")
            blender_material.msfs_fresnel_opacity_bias = fresnel_extension.get("fresnelOpacityOffset")

        # Parallax
        elif material_type == "msfs_parallax":
            parallax_extension = blender_material.extensions.get("ASOBO_material_parallax_window", {})

            blender_material.msfs_parallax_scale = parallax_extension.get("parallaxScale")
            blender_material.msfs_parallax_room_size_x = parallax_extension.get("roomSizeXScale")
            blender_material.msfs_parallax_room_size_y = parallax_extension.get("roomSizeYScale")
            blender_material.msfs_parallax_room_number = parallax_extension.get("roomNumberXY")
            blender_material.msfs_parallax_corridor = parallax_extension.get("corridor")

            behind_window_index = parallax_extension.get("behindWindowMapTexture", {}).get("index")
            if behind_window_index is not None:
                blender_material.msfs_behind_glass_texture = MSFSMaterial.create_image(behind_window_index, import_settings)


    @staticmethod
    def export(gltf2_object, blender_object):

        extension = {}

        gltf2_object.extensions[MSFSMaterial.extension_name] = Extension(
            name=MSFSMaterial.extension_name,
            extension=extension,
            required=False
        )
