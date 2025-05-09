import bmesh
import math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

class BoundaryAlignedRemesher:
    def __init__(self, obj):
        self.obj = obj
        self.bm = bmesh.new()
        self.bm.from_mesh(obj.data)
        self.bvh = BVHTree.FromBMesh(self.bm)

        # Boundary_data is a list of directions and locations of boundaries.
        # This data will serve as guidance for the alignment
        self.boundary_data = []

        # Fill the data using boundary edges as source of directional data.
        for edge in self.bm.edges:
            if edge.is_boundary:
                vec = (edge.verts[0].co - edge.verts[1].co).normalized()
                center = (edge.verts[0].co + edge.verts[1].co) / 2
                self.boundary_data.append((center, vec))

        # Create a Kd Tree to easily locate the nearest boundary point
        self.boundary_kd_tree = KDTree(len(self.boundary_data))
        for index, (center, vec) in enumerate(self.boundary_data):
            self.boundary_kd_tree.insert(center, index)
        self.boundary_kd_tree.balance()

    def nearest_boundary_vector(self, location):
        """Gets the nearest boundary direction"""
        location, index, dist = self.boundary_kd_tree.find(location)
        location, vec = self.boundary_data[index]
        return vec

    def enforce_edge_length(self, edge_length=1.000, bias=0.333):
        """Replicates dyntopo behaviour"""
        upper_length = edge_length + edge_length * bias
        lower_length = edge_length - edge_length * bias

        # Subdivide Long edges
        subdivide = []
        for edge in self.bm.edges:
            if edge.calc_length() > upper_length:
                subdivide.append(edge)

        bmesh.ops.subdivide_edges(self.bm, edges=subdivide, cuts=1)
        bmesh.ops.triangulate(self.bm, faces=self.bm.faces)

        # Remove verts with less than 5 edges, this helps improve mesh quality
        dissolve_verts = []
        for vert in self.bm.verts:
            if len(vert.link_edges) < 5:
                if not vert.is_boundary:
                    dissolve_verts.append(vert)

        bmesh.ops.dissolve_verts(self.bm, verts=dissolve_verts)
        bmesh.ops.triangulate(self.bm, faces=self.bm.faces)

        # Collapse short edges but ignore boundaries and never collapse two chained edges
        lock_verts = set(vert for vert in self.bm.verts if vert.is_boundary)
        collapse = []

        for edge in self.bm.edges:
            if edge.calc_length() < lower_length and not edge.is_boundary:
                verts = set(edge.verts)
                if verts & lock_verts:
                    continue
                collapse.append(edge)
                lock_verts |= verts

        bmesh.ops.collapse(self.bm, edges=collapse)
        bmesh.ops.beautify_fill(self.bm, faces=self.bm.faces, method="ANGLE")

    def align_verts(self, rule=(-1, -2, -3, -4)):
        """Align verts to the nearest boundary by averaging neighbor vert locations"""
        for vert in self.bm.verts:
            if not vert.is_boundary:
                vec = self.nearest_boundary_vector(vert.co)
                neighbor_locations = [
                    edge.other_vert(vert).co for edge in vert.link_edges
                ]
                best_locations = sorted(
                    neighbor_locations,
                    key=lambda n_loc: abs((n_loc - vert.co).normalized().dot(vec)),
                )
                co = vert.co.copy()
                le = len(vert.link_edges)
                for i in rule:
                    co += best_locations[i % le]
                co /= len(rule) + 1
                co -= vert.co
                co -= co.dot(vert.normal) * vert.normal
                vert.co += co

    def reproject(self):
        """Recovers original shape"""
        for vert in self.bm.verts:
            location, normal, index, dist = self.bvh.find_nearest(vert.co)
            if location:
                vert.co = location

    def remesh(self, edge_length=1.0, iterations=30, quads=True):
        """Coordinates remeshing"""
        if quads:
            rule = (-1, -2, 0, 1)
        else:
            rule = (0, 1, 2, 3)

        for _ in range(iterations):
            self.enforce_edge_length(edge_length=edge_length)
            self.align_verts(rule=rule)
            self.reproject()

        if quads:
            bmesh.ops.join_triangles(
                self.bm,
                faces=self.bm.faces,
                angle_face_threshold=3.14,
                angle_shape_threshold=3.14,
            )
        return self.bm 