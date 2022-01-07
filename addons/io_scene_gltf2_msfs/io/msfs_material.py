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

from io_scene_gltf2.io.com.gltf2_io_extensions import Extension
from io_scene_gltf2.blender.imp.gltf2_blender_image import BlenderImage
from io_scene_gltf2.blender.exp.gltf2_blender_gather_texture_info import gather_texture_info


class MSFSMaterial:
    bl_options = {"UNDO"}

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
        elif os.path.basename(pyimg.uri) in bpy.data.images:
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

        if not material_type:  # Because some materials share the extension name, we need to check the extras first for material type
            if "ASOBO_material_anisotropic" in gltf_material.extensions:
                material_type = "msfs_anisotropic"
            elif "ASOBO_material_SSS" in gltf_material.extensions:  # This is both hair and SSS, as they share the same properties
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
                for key in gltf_material.extensions.keys():  # Check all extensions and see if any Asobo extensions are present, and if so, it's a standard material
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
        windshield = gltf_material.extensions.get("ASOBO_material_windshield_v2")  # TODO: maybe add support for v1?
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
            if material_type == "msfs_decal":  # Decal and geo decal share properties but with different variable names
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
    def export(gltf2_material, blender_material, export_settings):
        # Set blendmode
        if blender_material.msfs_show_blend_mode == True:
            if blender_material.msfs_blend_mode == 'DITHER':
                gltf2_material.extensions["ASOBO_material_alphamode_dither"] = Extension(
                    name="ASOBO_material_alphamode_dither",
                    extension={"enabled": True},
                    required=False
                )

        # Set Asobo tags
        if (blender_material.msfs_show_road_material == True or blender_material.msfs_show_collision_material == True):
            if (blender_material.msfs_road_material == True or blender_material.msfs_collision_material == True):
                tags = []
                if blender_material.msfs_road_material == True:
                    tags.append("Road")
                if blender_material.msfs_collision_material == True:
                    tags.append("Collision")

                gltf2_material.extensions["ASOBO_tags"] = Extension(
                    name="ASOBO_tags",
                    extension={
                        "tags": tags
                    },
                    required=False
                )

        # Day/Night cycle
        if blender_material.msfs_show_day_night_cycle == True:
            if blender_material.msfs_day_night_cycle == True:
                gltf2_material.extensions["ASOBO_material_day_night_switch"] = Extension(
                    name="ASOBO_material_day_night_switch",
                    extension={"enabled": True},
                    required=False
                )

        # Windshield options
        if blender_material.msfs_show_windshield_options == True:
            if blender_material.msfs_rain_drop_scale > 0:
                gltf2_material.extensions["ASOBO_material_windshield_v2"] = Extension(
                    name="ASOBO_material_windshield_v2",
                    extension={"rainDropScale": blender_material.msfs_rain_drop_scale,
                               "wiper1State": blender_material.msfs_wiper_1_state,
                               "wiper2State": blender_material.msfs_wiper_2_state,
                               "wiper3State": blender_material.msfs_wiper_3_state,
                               "wiper4State": blender_material.msfs_wiper_4_state},
                    required=False
                )

        # Draw order
        if blender_material.msfs_show_draworder == True:
            if blender_material.msfs_draw_order > 0:
                gltf2_material.extensions["ASOBO_material_draw_order"] = Extension(
                    name="ASOBO_material_draw_order",
                    extension={"drawOrderOffset": blender_material.msfs_draw_order},
                    required=False
                )

        # Cast shadow
        if blender_material.msfs_show_no_cast_shadow == True:
            if blender_material.msfs_no_cast_shadow == True:
                gltf2_material.extensions["ASOBO_material_shadow_options"] = Extension(
                    name="ASOBO_material_shadow_options",
                    extension={"noCastShadow": blender_material.msfs_no_cast_shadow},
                    required=False
                )

        # Pearlescent
        if blender_material.msfs_show_pearl == True:
            if blender_material.msfs_use_pearl_effect == True:
                gltf2_material.extensions["ASOBO_material_pearlescent"] = Extension(
                    name="ASOBO_material_pearlescent",
                    extension={"pearlShift": blender_material.msfs_pearl_shift,
                               "pearlRange": blender_material.msfs_pearl_range,
                               "pearlBrightness": blender_material.msfs_pearl_brightness},
                    required=False
                )

        # UV Options
        if (blender_material.msfs_show_ao_use_uv2 == True or blender_material.msfs_show_uv_clamp == True):
            if (blender_material.msfs_ao_use_uv2 == True or blender_material.msfs_uv_clamp_x == True or
                    blender_material.msfs_uv_clamp_y == True or blender_material.msfs_uv_clamp_z == True):
                gltf2_material.extensions["ASOBO_material_UV_options"] = Extension(
                    name="ASOBO_material_UV_options",
                    extension={"AOUseUV2": blender_material.msfs_ao_use_uv2,
                               "clampUVX": blender_material.msfs_uv_clamp_x,
                               "clampUVY": blender_material.msfs_uv_clamp_y,
                               "clampUVZ": blender_material.msfs_uv_clamp_z},
                    required=False
                )

        # Detail maps
        if (blender_material.msfs_show_detail_albedo == True or blender_material.msfs_show_detail_metallic == True or blender_material.msfs_show_detail_normal == True):
            nodes = blender_material.node_tree.nodes

            detail_extension = {}
            if blender_material.msfs_detail_albedo_texture != None:
                # let's find the node:
                node = nodes.get("albedo_detail_mix")
                if node != None:
                    inputs = (node.inputs["Color2"],)
                    albedo_detail_texture = gather_texture_info(inputs[0], inputs, export_settings)
                    if albedo_detail_texture != None:
                        detail_extension["detailColorTexture"] = albedo_detail_texture
            if blender_material.msfs_detail_metallic_texture != None:
                # let's find the node:
                node = nodes.get("metallic_detail_mix")
                if node != None:
                    inputs = (node.inputs["Color2"],)
                    metallic_detail_texture = gather_texture_info(inputs[0], inputs, export_settings)
                    if metallic_detail_texture != None:
                        detail_extension["detailMetalRoughAOTexture"] = metallic_detail_texture
            if blender_material.msfs_detail_normal_texture != None:
                # let's find the node:
                node = nodes.get("normal_detail_mix")
                if node != None:
                    inputs = (node.inputs["Color2"],)
                    normal_detail_texture = gather_texture_info(inputs[0], inputs, export_settings)
                    if normal_detail_texture != None:
                        detail_extension["detailNormalTexture"] = normal_detail_texture
            if len(detail_extension) > 0:
                detail_extension["UVScale"] = blender_material.msfs_detail_uv_scale
                detail_extension["UVOffset"] = (
                    blender_material.msfs_detail_uv_offset_x, blender_material.msfs_detail_uv_offset_y)
                detail_extension["blendTreshold"] = blender_material.msfs_blend_threshold

                gltf2_material.extensions["ASOBO_material_detail_map"] = Extension(
                    name="ASOBO_material_detail_map",
                    extension=detail_extension,
                    required=False
                )

        # Blend gbuffer
        if blender_material.msfs_show_geo_decal_parameters == True:
            gltf2_material.extensions["ASOBO_material_blend_gbuffer"] = Extension(
                name="ASOBO_material_blend_gbuffer",
                extension={"enabled": True,
                           "baseColorBlendFactor": blender_material.msfs_geo_decal_blend_factor_color,
                           "metallicBlendFactor": blender_material.msfs_geo_decal_blend_factor_metal,
                           "roughnessBlendFactor": blender_material.msfs_geo_decal_blend_factor_roughness,
                           "normalBlendFactor": blender_material.msfs_geo_decal_blend_factor_normal,
                           "emissiveBlendFactor": blender_material.msfs_geo_decal_blend_factor_melt_sys,
                           "occlusionBlendFactor": blender_material.msfs_geo_decal_blend_factor_blast_sys,
                           },
                required=False
            )

        if blender_material.msfs_show_decal_parameters == True:
            gltf2_material.extensions["ASOBO_material_blend_gbuffer"] = Extension(
                name="ASOBO_material_blend_gbuffer",
                extension={"enabled": True,
                           "baseColorBlendFactor": blender_material.msfs_decal_blend_factor_color,
                           "metallicBlendFactor": blender_material.msfs_decal_blend_factor_metal,
                           "roughnessBlendFactor": blender_material.msfs_decal_blend_factor_roughness,
                           "normalBlendFactor": blender_material.msfs_decal_blend_factor_normal,
                           "emissiveBlendFactor": blender_material.msfs_decal_blend_factor_emissive,
                           "occlusionBlendFactor": blender_material.msfs_decal_blend_factor_occlusion,
                           },
                required=False
            )

            # Check the material mode of the material and attach the correct extension:
        if blender_material.msfs_material_mode == 'msfs_anisotropic':
            gltf2_material.extensions["ASOBO_material_anisotropic"] = Extension(
                name="ASOBO_material_anisotropic",
                extension={},
                required=False
            )
        elif blender_material.msfs_material_mode == 'msfs_sss':
            gltf2_material.extensions["ASOBO_material_SSS"] = Extension(
                name="ASOBO_material_SSS",
                extension={"SSSColor": [blender_material.msfs_color_sss[0], blender_material.msfs_color_sss[1],
                                        blender_material.msfs_color_sss[2], blender_material.msfs_color_sss[3]]},
                required=False
            )
        elif blender_material.msfs_material_mode == 'msfs_hair':
            gltf2_material.extensions["ASOBO_material_SSS"] = Extension(
                name="ASOBO_material_SSS",
                extension={"SSSColor": [blender_material.msfs_color_sss[0], blender_material.msfs_color_sss[1],
                                        blender_material.msfs_color_sss[2], blender_material.msfs_color_sss[3]]},
                required=False
            )
        elif blender_material.msfs_material_mode == 'msfs_glass':
            gltf2_material.extensions["ASOBO_material_glass"] = Extension(
                name="ASOBO_material_glass",
                extension={"glassReflectionMaskFactor": blender_material.msfs_glass_reflection_mask_factor,
                           "glassDeformationFactor": blender_material.msfs_glass_deformation_factor},
                required=False
            )
        elif blender_material.msfs_material_mode == 'msfs_clearcoat':
            gltf2_material.extensions["ASOBO_material_clear_coat"] = Extension(
                name="ASOBO_material_clear_coat",
                extension={"dirtTexture": blender_material.msfs_clearcoat_texture},
                required=False
            )
        elif blender_material.msfs_material_mode == 'msfs_fake_terrain':
            gltf2_material.extensions["ASOBO_material_fake_terrain"] = Extension(
                name="ASOBO_material_fake_terrain",
                extension={"enabled": True},
                required=False
            )
        elif blender_material.msfs_material_mode == 'msfs_fresnel':
            gltf2_material.extensions["ASOBO_material_fresnel_fade"] = Extension(
                name="ASOBO_material_fresnel_fade",
                extension={"fresnelFactor": blender_material.msfs_fresnel_factor,
                           "fresnelOpacityOffset": blender_material.msfs_fresnel_opacity_bias},
                required=False
            )
        elif blender_material.msfs_material_mode == 'msfs_parallax':

            nodes = blender_material.node_tree.nodes

            parallax_extension = {"parallaxScale": blender_material.msfs_parallax_scale,
                                  "roomSizeXScale": blender_material.msfs_parallax_room_size_x,
                                  "roomSizeYScale": blender_material.msfs_parallax_room_size_y,
                                  "roomNumberXY": blender_material.msfs_parallax_room_number,
                                  "corridor": blender_material.msfs_parallax_corridor
                                  }
            if blender_material.msfs_behind_glass_texture != None:
                # let's find the node:
                node = nodes.get("albedo_detail_mix")
                if node != None:
                    inputs = (node.inputs["Color2"],)
                    behind_glass_texture = gather_texture_info(inputs[0], inputs, export_settings)
                    if behind_glass_texture != None:
                        parallax_extension["behindWindowMapTexture"] = behind_glass_texture

            gltf2_material.extensions["ASOBO_material_parallax_window"] = Extension(
                name="ASOBO_material_parallax_window",
                extension=parallax_extension,
                required=False
            )
        elif blender_material.msfs_material_mode == 'msfs_env_occluder':
            gltf2_material.extensions["ASOBO_material_environment_occluder"] = Extension(
                name="ASOBO_material_environment_occluder",
                extension={"enabled": True},
                required=False
            )
        elif blender_material.msfs_material_mode == 'msfs_invisible':
            gltf2_material.extensions["ASOBO_material_invisible"] = Extension(
                name="ASOBO_material_invisible",
                extension={"enabled": True},
                required=False
            )

        # Add extras:
        if blender_material.msfs_material_mode == 'msfs_geo_decal':
            gltf2_material.extras["ASOBO_material_code"] = "GeoDecalFrosted"
        elif blender_material.msfs_material_mode == 'msfs_porthole':
            gltf2_material.extras["ASOBO_material_code"] = "Porthole"
        elif blender_material.msfs_material_mode == 'msfs_windshield':
            gltf2_material.extras["ASOBO_material_code"] = "Windshield"
