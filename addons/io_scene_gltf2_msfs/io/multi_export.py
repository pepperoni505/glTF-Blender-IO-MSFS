import bpy
import re
import io_scene_gltf2


# Override

# def _new_execute(self, context):
#     return

# io_scene_gltf2.ExportGLTF2_Base.execute = _new_execute

###

class MultiExportLOD(bpy.types.PropertyGroup):
    object: bpy.props.PointerProperty(name="", type=bpy.types.Object)
    checked: bpy.props.BoolProperty(name="", default=False)

    lod_value: bpy.props.IntProperty(name="", default=0, min=0)  # TODO: add max
    flatten_on_export: bpy.props.BoolProperty(name="", default=False)
    keep_instances: bpy.props.BoolProperty(name="", default=False)
    file_name: bpy.props.StringProperty(name="", default="")  # TODO: figure this out


class MultiExporterPropertyGroup(bpy.types.PropertyGroup):
    collection: bpy.props.PointerProperty(name="", type=bpy.types.Collection)
    expanded: bpy.props.BoolProperty(name="", default=True)
    lods: bpy.props.CollectionProperty(type=MultiExportLOD)
    folder_name: bpy.props.StringProperty(name="", default="")  # TODO: figure this out

class MSFSMultiExporterProperties():
    bpy.types.Scene.msfs_multi_exporter_current_tab = bpy.props.EnumProperty(items=
            (("OBJECTS", "Objects", ""),
            ("PRESETS", " Presets", "")),
    )


class MSFS_OT_edit_enabled_lods(bpy.types.Operator):
    bl_idname = "msfs.edit_enabled_lods"
    bl_label = "Edit Enabled LODs"

    def execute(self, context):
        return {"FINISHED"}

    def invoke(self, context, event):  # TODO: callback: glTF2_pre_export_callback
        property_collection = context.scene.msfs_multi_exporter_collection

        # Remove deleted collections and objects
        for i, property_group in enumerate(property_collection):
            if property_group.collection:
                for j, lod in enumerate(property_group.lods):
                    if not lod.object.name in context.scene.objects:
                        property_collection[i].lods.remove(j)
            else:
                property_collection.remove(i)
            

        # Add collection if not already in property group
        for collection in bpy.data.collections:
            if not collection in [property_group.collection for property_group in property_collection]:
                collection_prop_group = property_collection.add()
                collection_prop_group.collection = collection
                collection_prop_group.folder_name = collection.name
            else:
                for property_group in property_collection:
                    if property_group.collection == collection:
                        collection_prop_group = property_group
                        break
            
            for obj in collection.all_objects:
                # If the object starts with x(NUM)_ or ends with LOD_(NUM), add to lods
                if re.match("x\d_", obj.name.lower()) or re.match(".+_lod[0-9]+", obj.name.lower()):
                    if not obj in [lod.object for lod in collection_prop_group.lods]:
                        obj_item = collection_prop_group.lods.add()
                        obj_item.object = obj
                        obj_item.file_name = obj.name

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
                    box.prop(prop, "expanded", text=prop.collection.name,
                             icon="DOWNARROW_HLT" if prop.expanded else "RIGHTARROW", icon_only=True, emboss=False)
                    if prop.expanded:
                        box.prop(prop, "folder_name", text="Folder")

                        col = box.column()
                        for lod in prop.lods:
                            row = col.row()
                            row.prop(lod, "checked", text=lod.object.name)
                            subrow = row.column()
                            subrow.prop(lod, "lod_value", text="LOD Value")
                            subrow.prop(lod, "flatten_on_export", text="Flatten on Export")
                            subrow.prop(lod, "keep_instances", text="Keep Instances")
                            subrow.prop(lod, "file_name", text="Name")


class MSFS_OT_ChangeTab(bpy.types.Operator):
    bl_idname = "msfs.multi_export_change_tab"
    bl_label = "Change tab"

    current_tab: bpy.types.Scene.msfs_multi_exporter_current_tab

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

        layout.operator(MSFS_OT_edit_enabled_lods.bl_idname, text="Edit Enabled LODs")


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
    bpy.types.Scene.msfs_multi_exporter_collection = bpy.props.CollectionProperty(type=MultiExporterPropertyGroup) # for some reason this has to be here. TODO: move this to the property class

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
