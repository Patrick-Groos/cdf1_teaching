"""
Lecture 2.1 examples -- the nine example figures from
"02_1 Computational Geometry Examples" rebuilt with Rhino.Geometry.

Every function returns Rhino.Geometry objects, so it can be called from a
Grasshopper Python 3 Script component, e.g.

    from cdf.lecture_02_examples import create_planets
    spheres, rings = create_planets(count=n, tilt_angle=angle)

Inputs that are left unconnected in Grasshopper arrive as None, so every
optional input has a default.
"""

import math
import random

import Rhino.Geometry as rg
from Rhino.Geometry.Intersect import Intersection
from System import Array
from System.Drawing import Color

TOLERANCE = 0.001

BAUHAUS_COLORS = [
    Color.FromArgb(230, 57, 70),    # red
    Color.FromArgb(255, 200, 40),   # yellow
    Color.FromArgb(29, 90, 170),    # blue
    Color.FromArgb(240, 140, 150),  # pink
]


def _centered_box(center, size_x, size_y, size_z):
    """Axis-aligned box Brep centered on `center`."""
    plane = rg.Plane(center, rg.Vector3d.ZAxis)
    box = rg.Box(
        plane,
        rg.Interval(-size_x / 2.0, size_x / 2.0),
        rg.Interval(-size_y / 2.0, size_y / 2.0),
        rg.Interval(-size_z / 2.0, size_z / 2.0),
    )
    return box.ToBrep()


def _square_curve(center, size):
    """
    Closed square in the XY plane around `center`.

    The seam sits on the +X side (like a Rhino circle) and the square runs
    counter-clockwise, so it lofts cleanly against a circle.
    """
    h = size / 2.0
    polyline = rg.Polyline()
    for x, y in [(h, 0), (h, h), (-h, h), (-h, -h), (h, -h), (h, 0)]:
        polyline.Add(center.X + x, center.Y + y, center.Z)
    return polyline.ToNurbsCurve()


def _cap(brep):
    """Close planar openings of a Brep; return the input if that fails."""
    capped = brep.CapPlanarHoles(TOLERANCE)
    return capped if capped is not None else brep


# ----------------------------------------------------------------------
# 1. Spheres and toruses
# ----------------------------------------------------------------------
def create_planets(center=None, count=4, spacing=10.0, sphere_radius=3.0,
                   ring_radius=4.5, ring_thickness=0.5, tilt_angle=30.0):
    """
    Spheres arranged on a circle, each with a tilted torus ring ("planets").

    center         : Rhino.Geometry.Point3d -- center of the arrangement
    count          : int   -- number of planets
    spacing        : float -- distance of each planet from the center
    sphere_radius  : float -- radius of the spheres
    ring_radius    : float -- major radius of the torus (center of the tube)
    ring_thickness : float -- minor radius of the torus (tube radius)
    tilt_angle     : float -- rotation of the ring plane around the Y axis, degrees

    Returns (spheres, rings): two lists of Rhino.Geometry.Brep.
    """
    if center is None:
        center = rg.Point3d(0, 0, 2.0 * sphere_radius)

    spheres = []
    rings = []
    count = int(count)
    for i in range(count):
        angle = 2.0 * math.pi * i / count
        pt = rg.Point3d(center.X + spacing * math.cos(angle),
                        center.Y + spacing * math.sin(angle),
                        center.Z)
        spheres.append(rg.Sphere(pt, sphere_radius).ToBrep())

        # rotate the ring plane around its own Y axis by the tilt angle
        ring_plane = rg.Plane(pt, rg.Vector3d.ZAxis)
        ring_plane.Rotate(math.radians(tilt_angle), ring_plane.YAxis)
        torus = rg.Torus(ring_plane, ring_radius, ring_thickness)
        rings.append(torus.ToRevSurface().ToBrep())

    return spheres, rings


# ----------------------------------------------------------------------
# 2. Box and spheres
# ----------------------------------------------------------------------
def create_box_with_spheres(base_point=None, box_size=20.0, box_height=6.0,
                            hole_size=6.0, hole_depth=3.0, sphere_radius=2.5,
                            sphere_count=4, sphere_spacing=5.0):
    """
    Box A with a square recess cut out by box B (boolean difference) and a
    column of spheres above the recess, made by translating one sphere.

    base_point     : Rhino.Geometry.Point3d -- center of the box's bottom face
    box_size       : float -- width and depth of box A
    box_height     : float -- height of box A
    hole_size      : float -- width and depth of box B (the recess)
    hole_depth     : float -- how deep box B cuts into box A
    sphere_radius  : float -- radius of the spheres
    sphere_count   : int   -- number of spheres
    sphere_spacing : float -- Z distance between consecutive spheres

    Returns (box, cutter, spheres): the cut Brep, box B and a list of Breps.
    """
    if base_point is None:
        base_point = rg.Point3d(0, 0, 0)

    box_a = _centered_box(base_point + rg.Vector3d(0, 0, box_height / 2.0),
                          box_size, box_size, box_height)

    # box B sticks out above box A so the cut is clean
    cutter_height = hole_depth + 1.0
    cutter_z = box_height - hole_depth + cutter_height / 2.0
    box_b = _centered_box(base_point + rg.Vector3d(0, 0, cutter_z),
                          hole_size, hole_size, cutter_height)

    result = rg.Brep.CreateBooleanDifference(box_a, box_b, TOLERANCE)
    box = result[0] if result else box_a

    # the first sphere sits in the recess, the others are translated copies
    first_center = base_point + rg.Vector3d(0, 0, box_height - hole_depth + sphere_radius)
    sphere = rg.Sphere(first_center, sphere_radius).ToBrep()
    spheres = []
    for i in range(int(sphere_count)):
        copy = sphere.DuplicateBrep()
        copy.Transform(rg.Transform.Translation(rg.Vector3d(0, 0, sphere_spacing * i)))
        spheres.append(copy)

    return box, box_b, spheres


# ----------------------------------------------------------------------
# 3. Chequered boxes
# ----------------------------------------------------------------------
def create_chequered_boxes(base_point=None, nx=3, ny=3, nz=3, size=5.0, invert=False):
    """
    3D chequerboard: a box is placed in every second cell of an nx*ny*nz grid.

    base_point : Rhino.Geometry.Point3d -- corner of the grid
    nx, ny, nz : int   -- number of cells in X, Y and Z
    size       : float -- edge length of one cell / box
    invert     : bool  -- fill the other half of the cells instead

    Returns a list of Rhino.Geometry.Brep.
    """
    if base_point is None:
        base_point = rg.Point3d(0, 0, 0)

    boxes = []
    for i in range(int(nx)):
        for j in range(int(ny)):
            for k in range(int(nz)):
                filled = (i + j + k) % 2 == 0
                if invert:
                    filled = not filled
                if filled:
                    center = base_point + rg.Vector3d((i + 0.5) * size,
                                                      (j + 0.5) * size,
                                                      (k + 0.5) * size)
                    boxes.append(_centered_box(center, size, size, size))
    return boxes


# ----------------------------------------------------------------------
# 4. Point cloud
# ----------------------------------------------------------------------
def create_point_cloud(base_point=None, count=60, size_x=30.0, size_y=30.0,
                       size_z=30.0, box_size=2.0, min_scale=0.2, max_scale=2.0,
                       seed=1, use_palette=True):
    """
    Random points inside a box-shaped domain, each carrying a cube that is
    scaled by a random factor and gets a random color.

    base_point  : Rhino.Geometry.Point3d -- corner of the domain
    count       : int   -- number of points
    size_x/y/z  : float -- extent of the domain
    box_size    : float -- edge length of a cube before scaling
    min_scale   : float -- smallest random scale factor
    max_scale   : float -- largest random scale factor
    seed        : int   -- random seed, same seed gives the same cloud
    use_palette : bool  -- pick from the Bauhaus palette instead of any RGB color

    Returns (points, boxes, scales, colors): Point3d list, Brep list,
    float list and System.Drawing.Color list (same order).
    """
    if base_point is None:
        base_point = rg.Point3d(0, 0, 0)

    rng = random.Random(seed)
    points, boxes, scales, colors = [], [], [], []
    for _ in range(int(count)):
        pt = base_point + rg.Vector3d(rng.uniform(0, size_x),
                                      rng.uniform(0, size_y),
                                      rng.uniform(0, size_z))
        scale = rng.uniform(min_scale, max_scale)

        # scale transformation around the point itself
        box = _centered_box(pt, box_size, box_size, box_size)
        box.Transform(rg.Transform.Scale(pt, scale))

        if use_palette:
            color = rng.choice(BAUHAUS_COLORS)
        else:
            color = Color.FromArgb(rng.randint(0, 255), rng.randint(0, 255), rng.randint(0, 255))

        points.append(pt)
        boxes.append(box)
        scales.append(round(scale, 2))
        colors.append(color)

    return points, boxes, scales, colors


# ----------------------------------------------------------------------
# 5. Point traces
# ----------------------------------------------------------------------
def create_point_traces(center=None, radius=10.0, count=80, ground_z=0.0, seed=1):
    """
    Split a sphere into a hemisphere, place random points on it through
    u, v parameters and project them down onto a ground Brep.

    center   : Rhino.Geometry.Point3d -- sphere center (= height of the cut)
    radius   : float -- sphere radius
    count    : int   -- number of points on the hemisphere
    ground_z : float -- height of the ground plane the points are projected on
    seed     : int   -- random seed for the u, v values

    Returns (hemisphere, surface_points, projected_points, traces):
    a Brep, two Point3d lists and a list of Rhino.Geometry.Line.
    """
    if center is None:
        center = rg.Point3d(0, 0, 8.0)

    # split the sphere with a planar Brep through its center
    sphere = rg.Sphere(center, radius).ToBrep()
    extent = rg.Interval(-2.0 * radius, 2.0 * radius)
    cutter = rg.PlaneSurface(rg.Plane(center, rg.Vector3d.ZAxis), extent, extent).ToBrep()
    pieces = sphere.Split(cutter, TOLERANCE)
    if not pieces:
        raise ValueError("Splitting the sphere failed.")
    hemisphere = max(pieces, key=lambda b: b.GetBoundingBox(True).Center.Z)

    # random u, v pairs; skip those that fall on the trimmed-away half
    face = hemisphere.Faces[0]
    u_domain = face.Domain(0)
    v_domain = face.Domain(1)
    rng = random.Random(seed)
    surface_points = []
    attempts = 0
    while len(surface_points) < int(count) and attempts < int(count) * 20:
        attempts += 1
        u = u_domain.ParameterAt(rng.random())
        v = v_domain.ParameterAt(rng.random())
        if face.IsPointOnFace(u, v) == rg.PointFaceRelation.Exterior:
            continue
        surface_points.append(face.PointAt(u, v))

    # project every point straight down onto the ground Brep
    ground_plane = rg.Plane(rg.Point3d(center.X, center.Y, ground_z), rg.Vector3d.ZAxis)
    ground = rg.PlaneSurface(ground_plane, extent, extent).ToBrep()
    down = rg.Vector3d(0, 0, -1)
    projected_points = []
    traces = []
    for pt in surface_points:
        hits = Intersection.ProjectPointsToBreps(
            Array[rg.Brep]([ground]), Array[rg.Point3d]([pt]), down, TOLERANCE)
        if hits:
            projected_points.append(hits[0])
            traces.append(rg.Line(pt, hits[0]))

    return hemisphere, surface_points, projected_points, traces


# ----------------------------------------------------------------------
# 6. Blend surface
# ----------------------------------------------------------------------
def create_blend_solid(base_point=None, base_size=20.0, top_radius=4.0,
                       height=15.0, top_offset_x=0.0, top_offset_y=0.0):
    """
    Solid made by lofting a square (curve_2) at the bottom into a circle
    (curve_1) at the top and capping both ends.

    base_point   : Rhino.Geometry.Point3d -- center of the bottom square
    base_size    : float -- edge length of the square
    top_radius   : float -- radius of the circle
    height       : float -- height of the circle above the square
    top_offset_x : float -- shifts the circle sideways in X
    top_offset_y : float -- shifts the circle sideways in Y

    Returns (solid, curve_1, curve_2): a Brep and the two curves.
    """
    if base_point is None:
        base_point = rg.Point3d(0, 0, 0)

    curve_2 = _square_curve(base_point, base_size)
    top_center = base_point + rg.Vector3d(top_offset_x, top_offset_y, height)
    curve_1 = rg.Circle(rg.Plane(top_center, rg.Vector3d.ZAxis), top_radius).ToNurbsCurve()

    lofts = rg.Brep.CreateFromLoft(Array[rg.Curve]([curve_2, curve_1]),
                                   rg.Point3d.Unset, rg.Point3d.Unset,
                                   rg.LoftType.Normal, False)
    if not lofts:
        raise ValueError("Loft failed.")
    solid = _cap(lofts[0])

    return solid, curve_1, curve_2


# ----------------------------------------------------------------------
# 7. Mirrored cones
# ----------------------------------------------------------------------
def create_mirrored_cones(apex=None, height=10.0, radius=4.0, tilt_angle=45.0,
                          turn_angle=45.0, mirror_plane=None):
    """
    A tilted cone and its mirror image, meeting at the apex.

    apex         : Rhino.Geometry.Point3d -- tip of the cone
    height       : float -- distance from the apex to the base circle
    radius       : float -- radius of the base circle
    tilt_angle   : float -- rotation of the cone axis around the X axis, degrees
    turn_angle   : float -- rotation of the cone axis around the Z axis, degrees
    mirror_plane : Rhino.Geometry.Plane -- plane to mirror across; defaults to
                   the plane through the apex perpendicular to the cone axis

    Returns (cone, mirrored_cone, mirror_plane).
    """
    if apex is None:
        apex = rg.Point3d(0, 0, 12.0)

    axis = rg.Vector3d(0, 0, 1)
    axis.Rotate(math.radians(tilt_angle), rg.Vector3d.XAxis)
    axis.Rotate(math.radians(turn_angle), rg.Vector3d.ZAxis)

    # cone = base circle extruded to the apex point, then capped
    base_center = apex + axis * height
    base_circle = rg.Circle(rg.Plane(base_center, axis), radius).ToNurbsCurve()
    surface = rg.Surface.CreateExtrusionToPoint(base_circle, apex)
    cone = _cap(surface.ToBrep())

    if mirror_plane is None:
        mirror_plane = rg.Plane(apex, axis)
    mirrored = cone.DuplicateBrep()
    mirrored.Transform(rg.Transform.Mirror(mirror_plane))

    return cone, mirrored, mirror_plane


# ----------------------------------------------------------------------
# 8. Pyramid parts
# ----------------------------------------------------------------------
def create_pyramid_parts(base_point=None, size=20.0, height=20.0, part_count=3, gap=1.0):
    """
    Upside-down pyramid cut into horizontal parts by subtracting thin slabs
    (boolean difference).

    base_point : Rhino.Geometry.Point3d -- position of the pyramid tip (bottom)
    size       : float -- edge length of the square top face
    height     : float -- height of the pyramid
    part_count : int   -- number of parts the pyramid is cut into
    gap        : float -- thickness of each cutting slab

    Returns (parts, slabs): two lists of Rhino.Geometry.Brep.
    """
    if base_point is None:
        base_point = rg.Point3d(0, 0, 0)

    top = _square_curve(base_point + rg.Vector3d(0, 0, height), size)
    pyramid = _cap(rg.Surface.CreateExtrusionToPoint(top, base_point).ToBrep())
    pyramid.Faces.SplitKinkyFaces()

    slabs = []
    for i in range(1, int(part_count)):
        z = height * i / float(part_count)
        slabs.append(_centered_box(base_point + rg.Vector3d(0, 0, z),
                                   size * 1.5, size * 1.5, gap))

    # subtract the slabs one after another
    parts = [pyramid]
    for slab in slabs:
        next_parts = []
        for part in parts:
            result = rg.Brep.CreateBooleanDifference(part, slab, TOLERANCE)
            if result:
                next_parts.extend(result)
            else:
                next_parts.append(part)  # slab does not touch this part
        parts = next_parts

    return parts, slabs


# ----------------------------------------------------------------------
# 9. Sweep
# ----------------------------------------------------------------------
def create_spiral_sweep(start_point=None, direction=None, radius=3.0, pitch=8.0,
                        turns=3.0, profile_width=0.6, profile_height=2.0):
    """
    A spiral (helix) along an axis, with a rectangular profile swept along it.

    start_point    : Rhino.Geometry.Point3d -- start of the spiral axis
    direction      : Rhino.Geometry.Vector3d -- direction of the spiral axis
    radius         : float -- spiral radius
    pitch          : float -- distance along the axis for one full turn
    turns          : float -- number of turns
    profile_width  : float -- width of the swept rectangle
    profile_height : float -- height of the swept rectangle

    Returns (solid, rail, profile): the swept Brep and the two curves.
    """
    if direction is None:
        direction = rg.Vector3d(1, 0, 0)
    if start_point is None:
        start_point = rg.Point3d(0, 0, radius + profile_height / 2.0)

    # the spiral starts below the axis, so it touches the ground first
    radius_point = start_point + rg.Vector3d(0, 0, -radius)
    rail = rg.NurbsCurve.CreateSpiral(start_point, direction, radius_point,
                                      pitch, turns, radius, radius)
    if rail is None:
        raise ValueError("Spiral could not be created; check the direction and radius.")

    # rectangle in the plane perpendicular to the rail at its start
    ok, frame = rail.PerpendicularFrameAt(rail.Domain.Min)
    profile = rg.Rectangle3d(frame,
                             rg.Interval(-profile_width / 2.0, profile_width / 2.0),
                             rg.Interval(-profile_height / 2.0, profile_height / 2.0)).ToNurbsCurve()

    sweeps = rg.Brep.CreateFromSweep(rail, profile, False, TOLERANCE)
    if not sweeps:
        raise ValueError("Sweep failed.")
    solid = _cap(sweeps[0])

    return solid, rail, profile
