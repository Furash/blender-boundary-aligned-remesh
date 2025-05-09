import bpy
from . import remesher

class Remesher(bpy.types.Operator):
    bl_idname = "remesh.boundary_aligned_remesh"
    bl_label = "Boundary Aligned Remesh"
    bl_options = {"REGISTER", "UNDO"}

    edge_length: bpy.props.FloatProperty(
        name="Edge Length",
        min=0,
        default=1,
        description="Target edge length for the remeshed result"
    )

    iterations: bpy.props.IntProperty(
        name="Iterations",
        min=1,
        default=30,
        description="Number of remeshing iterations to perform"
    )

    quads: bpy.props.BoolProperty(
        name="Quads",
        default=True,
        description="Try to create quad faces instead of triangles"
    )

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'MESH'

    def invoke(self, context, event):
        # Calculate default edge length based on object dimensions
        obj = context.active_object
        if obj and obj.type == "MESH":
            avg_len = (obj.dimensions[0] + obj.dimensions[1] + obj.dimensions[2]) / 3
            self.edge_length = round((5 * avg_len) / 10, ndigits=2)
        return self.execute(context)

    def execute(self, context):
        obj = context.active_object
        if obj.type == "MESH":
            remesher_obj = remesher.BoundaryAlignedRemesher(obj)
            bm = remesher_obj.remesh(self.edge_length, self.iterations, self.quads)
            bm.to_mesh(obj.data)
            context.area.tag_redraw()
            self.report({"INFO"}, f"Remeshed {obj.name}")
            return {"FINISHED"}
        else:
            self.report({"WARNING"}, "Active object is not MESH")
            return {"CANCELLED"}

def register():
    bpy.utils.register_class(Remesher)

def unregister():
    bpy.utils.unregister_class(Remesher) 