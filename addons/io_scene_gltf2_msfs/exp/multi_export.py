import bpy
import re
import io_scene_gltf2


# Override

# def _new_execute(self, context):
#     return

# io_scene_gltf2.ExportGLTF2_Base.execute = _new_execute

###

class MultiExportLOD(bpy.types.PropertyGroup):
    object_name: bpy.props.StringProperty(name="", default="")
    checked: bpy.props.BoolProperty(name="", default=False)

    lod_value: bpy.props.IntProperty(name="", default=0, min=0)  # TODO: add max
    flatten_on_export: bpy.props.BoolProperty(name="", default=False)
    keep_instances: bpy.props.BoolProperty(name="", default=False)
    export_path: bpy.props.StringProperty(name="", default="")  # TODO: figure this out


class MultiExporterPropertyGroup(bpy.types.PropertyGroup):
    collection_name: bpy.props.StringProperty(name="", default="")
    expanded: bpy.props.BoolProperty(name="", default=True)
    lods: bpy.props.CollectionProperty(type=MultiExportLOD)


class MSFS_OT_EditEnabledLODs(bpy.types.Operator):
    bl_idname = "msfs.edit_enabled_lods"
    bl_label = "Edit Enabled LODs"

    def execute(self, context):
        return {"FINISHED"}

    def invoke(self, context, event):  # TODO: fix clearing settings on open. callback: glTF2_pre_export_callback
        property_collection = context.scene.msfs_multi_exporter_collection
        # property_collection.clear()
        for collection in bpy.data.collections:  # TODO: remove collections and lods that are no longer used
            collection_exists = False
            item = None
            for prop in property_collection:
                if prop.collection_name == collection.name:
                    item = prop
                    collection_exists = True

            if not collection_exists:
                item = property_collection.add()
                item.collection_name = collection.name
                item.checked = False

            for obj in collection.all_objects:
                if re.match("x\d_", obj.name.lower()) or re.match(".+_lod[0-9]+", obj.name.lower()):
                    obj_exists = False
                    for lod in item.lods:
                        if object.name == lod.object_name:
                            obj_exists = True

                    if not obj_exists:
                        obj_item = item.lods.add()
                        obj_item.object_name = obj.name
                        obj_item.checked = False

        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout

        property_collection = bpy.context.scene.msfs_multi_exporter_collection
        total_lods = 0
        for prop in property_collection:
            total_lods += len(prop.lods)
        if total_lods == 0:
            box = layout.box()
            box.label(text="No LODs found in scene")
        else:
            for prop in property_collection:
                row = layout.row()
                if len(prop.lods) > 0:
                    box = row.box()
                    box.prop(prop, "expanded", text=prop.collection_name,
                             icon="DOWNARROW_HLT" if prop.expanded else "RIGHTARROW", icon_only=True, emboss=False)
                    if prop.expanded:
                        col = box.column()
                        for lod in prop.lods:
                            row = col.row()
                            row.prop(lod, "checked", text=lod.object_name)
                            subrow = row.column()
                            subrow.prop(lod, "lod_value", text="LOD Value")
                            subrow.prop(lod, "flatten_on_export", text="Flatten on Export")
                            subrow.prop(lod, "keep_instances", text="Keep Instances")
                            subrow.prop(lod, "export_path", text="Path")


class MSFS_OT_ChangeTab(bpy.types.Operator):
    bl_idname = "msfs.multi_export_change_tab"
    bl_label = "Change tab"

    current_tab: bpy.props.EnumProperty(items=
                                        (("OBJECTS", "Objects", ""),
                                         ("PRESETS", " Presets", "")),
                                        )

    def execute(self, context):
        context.scene.msfs_multi_exporter_current_tab = self.current_tab
        return {"FINISHED"}


class MSFS_PT_MultiExporterObjectsView(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Multi-Exporter"
    bl_parent_id = "MSFS_PT_MultiExporter"
    bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        return operator.bl_idname == "EXPORT_SCENE_OT_gltf" and context.scene.msfs_multi_exporter_current_tab == "OBJECTS"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        # property_collection = bpy.context.scene.msfs_multi_exporter_collection
        # layout.label(text="Enabled LODs")
        # enabled_lods = 0
        # for prop in property_collection:
        #     for lod in prop.lods:
        #         if lod.checked:
        #             enabled_lods += 1

        # if enabled_lods == 0:
        #     box = layout.box()
        #     box.label(text="None")
        # else:
        #     for prop in property_collection:
        #         box = layout.box()
        #         box.prop(prop, "expanded", text=prop.collection_name, icon="DOWNARROW_HLT" if prop.expanded else "RIGHTARROW", icon_only=True, emboss=False)
        #         if prop.expanded:
        #             row = box.row()
        #             for lod in prop.lods:
        #                 row.label(text=lod.object_name)

        layout.operator(MSFS_OT_EditEnabledLODs.bl_idname, text="Edit Enabled LODs")


class MSFS_PT_MultiExporter(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Multi-Exporter"
    bl_parent_id = "FILE_PT_operator"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        return operator.bl_idname == "EXPORT_SCENE_OT_gltf" and context.scene.msfs_ExtAsoboProperties.enabled

    # def draw_header(self, context):
    #     layout = self.layout
    #     layout.label(text="test", icon='TOOL_SETTINGS')

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        current_tab = context.scene.msfs_multi_exporter_current_tab

        row = layout.row(align=True)
        row.operator(MSFS_OT_ChangeTab.bl_idname, text="Objects",
                     depress=(current_tab == "OBJECTS")).current_tab = "OBJECTS"
        row.operator(MSFS_OT_ChangeTab.bl_idname, text="Presets",
                     depress=(current_tab == "PRESETS")).current_tab = "PRESETS"


def register():
    bpy.types.Scene.msfs_multi_exporter_collection = bpy.props.CollectionProperty(type=MultiExporterPropertyGroup)
    bpy.types.Scene.msfs_multi_exporter_current_tab = bpy.props.EnumProperty(items=
            (("OBJECTS", "Objects", ""),
            ("PRESETS", " Presets", "")),
    )  # TODO: move to separate class and remove duplicated current_tab code


def register_panel():
    # Register the panel on demand, we need to be sure to only register it once
    # This is necessary because the panel is a child of the extensions panel,
    # which may not be registered when we try to register this extension
    try:
        bpy.utils.register_class(MSFS_PT_MultiExporter)
    except Exception:
        pass

    # If the glTF exporter is disabled, we need to unregister the extension panel
    # Just return a function to the exporter so it can unregister the panel
    return unregister_panel


def unregister_panel():
    try:
        bpy.utils.unregister_class(MSFS_PT_MultiExporter)
    except Exception:
        pass
