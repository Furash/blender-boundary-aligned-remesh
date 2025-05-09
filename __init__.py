bl_info = {
    "name": "Boundary Aligned Remesh",
    "author": "Jean Da Costa, Titus, Cyrill",
    "version": (1, 0),
    "blender": (4, 4, 0),
    "location": "View3D > Object Context Menu",
    "description": "Rebuilds mesh out of isotropic polygons with boundary alignment.",
    "warning": "",
    "wiki_url": "",
    "category": "Remesh",
}

import bpy
from . import operators
from . import ui

def register():
    operators.register()
    ui.register()

def unregister():
    operators.unregister()
    ui.unregister()

if __name__ == "__main__":
    register() 