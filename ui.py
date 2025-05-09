import bpy

def draw_menu(self, context):
    self.layout.operator(
        "remesh.boundary_aligned_remesh",
        text="Boundary Aligned Remesh"
    )

def register():
    bpy.types.VIEW3D_MT_object_context_menu.append(draw_menu)

def unregister():
    bpy.types.VIEW3D_MT_object_context_menu.remove(draw_menu) 