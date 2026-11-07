"""
Code for Assignment 01: Bauhaus composition -- "Bauhaus planet".

A cratered planet (sphere minus crater spheres) sits inside a thin, tilted
ring disc. A closed, meandering curve runs once around the planet on top of
the ring and carries a rhythmic sequence of boxes, cylinders and spheres.

Parameter logic (relationships declared in the model)
-----------------------------------------------------
* planet_radius is the master size. Every other length is a ratio of it,
  so the whole composition scales together.
* ring inner radius = planet_radius * ring_gap        (ring_gap > 1, never touches the planet)
* ring outer radius = inner radius + planet_radius * ring_width
* ring thickness    = planet_radius * ring_thickness
* crater radii      = planet_radius * [crater_min .. crater_max]
* object size       = ring width * object_scale, capped so objects always fit on the ring
* curve amplitude   = what is left of the half ring width after the largest
                      object has been placed, so objects never hang over the edge
* object gap        = object size * object_gap; objects on the same ring side are
                      shrunk (or left out) so they never touch each other

Grasshopper (Python 3 Script component):

    from cdf.assignment_01_bauhaus import create_bauhaus_planet
    planet, rims, ring, curve, objects, colors = create_bauhaus_planet(
        planet_radius=R, crater_count=nc, ring_tilt=tilt, curve_waves=w,
        object_count=no, seed=seed)
"""

import math
import random

import Rhino.Geometry as rg
from System import Array
from System.Drawing import Color

TOLERANCE = 0.001

RED = Color.FromArgb(214, 48, 39)
YELLOW = Color.FromArgb(242, 183, 5)
BLUE = Color.FromArgb(32, 84, 147)
BLACK = Color.FromArgb(25, 25, 25)
WHITE = Color.FromArgb(240, 235, 225)

OBJECT_COLORS = [RED, YELLOW, WHITE, BLUE, BLACK]


def _boolean_difference(brep, cutters):
    """
    Subtract all cutters from brep. Tries all cutters at once first and falls
    back to one cutter after another if Rhino cannot solve the combined case.

    Returns a Rhino.Geometry.Brep (the input brep if nothing could be cut).
    """
    if not cutters:
        return brep

    def _first_valid(result):
        if not result:
            return None
        for item in result:
            if item is not None and item.IsValid:
                return item
        return None

    combined = _first_valid(rg.Brep.CreateBooleanDifference(
        Array[rg.Brep]([brep]), Array[rg.Brep](cutters), TOLERANCE))
    if combined is not None:
        return combined

    # cutters that Rhino cannot subtract are skipped, the brep is never lost
    for cutter in cutters:
        cut = _first_valid(rg.Brep.CreateBooleanDifference(brep, cutter, TOLERANCE))
        if cut is not None:
            brep = cut
    return brep


# ----------------------------------------------------------------------
# Planet with craters
# ----------------------------------------------------------------------
def create_cratered_planet(center=None, radius=10.0, crater_count=12,
                           crater_min=0.08, crater_max=0.3, crater_depth=0.35,
                           rim_chance=0.4, rim_thickness=0.03, seed=1):
    """
    Sphere with craters cut out by smaller spheres (boolean difference).

    center        : Rhino.Geometry.Point3d -- planet center
    radius        : float -- planet radius
    crater_count  : int   -- number of craters (fewer if they do not fit)
    crater_min    : float -- smallest crater sphere radius, as a ratio of radius
    crater_max    : float -- largest crater sphere radius, as a ratio of radius
    crater_depth  : float -- depth of a crater as a ratio of its own radius (0..1)
    rim_chance    : float -- share of craters that get a raised rim (0..1)
    rim_thickness : float -- rim tube radius, as a ratio of radius
    seed          : int   -- random seed for crater positions and sizes

    Returns (planet, rims): a Brep and a list of torus Breps.
    """
    if center is None:
        center = rg.Point3d(0, 0, 0)

    rng = random.Random(seed)
    planet = rg.Sphere(center, radius).ToBrep()

    placed = []   # (normal, opening radius) of craters already placed
    cutters = []
    rims = []
    attempts = 0
    while len(cutters) < int(crater_count) and attempts < int(crater_count) * 30:
        attempts += 1

        # uniformly distributed direction on the sphere
        z = rng.uniform(-1.0, 1.0)
        phi = rng.uniform(0.0, 2.0 * math.pi)
        s = math.sqrt(1.0 - z * z)
        normal = rg.Vector3d(s * math.cos(phi), s * math.sin(phi), z)

        crater_radius = radius * rng.uniform(crater_min, crater_max)
        depth = crater_radius * crater_depth
        distance = radius + crater_radius - depth  # planet center -> crater sphere center

        # circle where crater sphere and planet meet (the crater opening)
        x = (distance ** 2 + radius ** 2 - crater_radius ** 2) / (2.0 * distance)
        opening = math.sqrt(max(radius ** 2 - x ** 2, 0.0))

        # keep craters apart: compare the arc distance with both openings
        overlaps = False
        for other_normal, other_opening in placed:
            angle = rg.Vector3d.VectorAngle(normal, other_normal)
            if radius * angle < opening + other_opening + 0.02 * radius:
                overlaps = True
                break
        if overlaps:
            continue

        placed.append((normal, opening))
        cutters.append(rg.Sphere(center + normal * distance, crater_radius).ToBrep())

        if rng.random() < rim_chance:
            rim_plane = rg.Plane(center + normal * x, normal)
            rims.append(rg.Torus(rim_plane, opening, radius * rim_thickness).ToRevSurface().ToBrep())

    planet = _boolean_difference(planet, cutters)
    return planet, rims


# ----------------------------------------------------------------------
# Ring disc (built flat around the origin, moved into place later)
# ----------------------------------------------------------------------
def create_ring_disc(inner_radius=13.0, outer_radius=25.0, thickness=0.4):
    """
    Flat ring disc around the origin, centered on the XY plane.

    inner_radius : float -- radius of the hole
    outer_radius : float -- outer radius
    thickness    : float -- disc thickness (from -thickness/2 to +thickness/2)

    Returns a Rhino.Geometry.Brep.
    """
    bottom = rg.Plane(rg.Point3d(0, 0, -thickness / 2.0), rg.Vector3d.ZAxis)
    outer = rg.Cylinder(rg.Circle(bottom, outer_radius), thickness).ToBrep(True, True)

    # the inner cylinder is taller so the hole is cut cleanly
    cutter_bottom = rg.Plane(rg.Point3d(0, 0, -thickness), rg.Vector3d.ZAxis)
    inner = rg.Cylinder(rg.Circle(cutter_bottom, inner_radius), 2.0 * thickness).ToBrep(True, True)

    return _boolean_difference(outer, [inner])


def create_meander_curve(mid_radius=19.0, amplitude=3.0, waves=6, height=0.2, phase=0.0):
    """
    Closed curve that runs once around the origin and swings in and out
    between mid_radius - amplitude and mid_radius + amplitude.

    The curve is a periodic B-spline (a chain of smooth Bezier-like segments)
    built from control points on r(t) = mid_radius + amplitude * sin(waves * t).
    A B-spline always stays inside its control points, so it never leaves the band.

    mid_radius : float -- radius of the center line of the band
    amplitude  : float -- how far the curve swings in and out
    waves      : int   -- number of waves on one round (whole number keeps it closed)
    height     : float -- Z height of the curve (top surface of the ring)
    phase      : float -- rotates the wave pattern around the ring, degrees

    Returns a Rhino.Geometry.NurbsCurve.
    """
    waves = max(int(waves), 1)
    sample_count = max(waves * 8, 24)
    phase = math.radians(phase)

    points = []
    for i in range(sample_count):
        t = 2.0 * math.pi * i / sample_count
        r = mid_radius + amplitude * math.sin(waves * t + phase)
        points.append(rg.Point3d(r * math.cos(t), r * math.sin(t), height))

    return rg.NurbsCurve.Create(True, 3, Array[rg.Point3d](points))


def place_objects_on_curve(curve, count=24, base_size=3.0, size_variation=0.5,
                           size_waves=3, height_variation=1.5, height_waves=2,
                           pattern="BCSB", side_pattern="U", thickness=0.0, gap=0.3):
    """
    Boxes, cylinders and spheres standing on the curve. Sizes and heights
    follow two sine rhythms along the curve, the shapes follow a text pattern.

    Objects never touch: each object is compared with every object already
    placed on the same side of the ring and shrunk until `gap` is left
    between their footprints. If even the smallest size does not fit, the
    spot stays empty.

    curve            : Rhino.Geometry.Curve -- closed curve lying in a horizontal plane
                       (the top surface of the ring)
    count            : int   -- number of spots along the curve (maximum number of objects)
    base_size        : float -- average footprint size
    size_variation   : float -- size swings between base_size * (1 -/+ size_variation)
    size_waves       : int   -- number of size waves along the curve
    height_variation : float -- extra height (as a multiple of the size) at the height peaks
    height_waves     : int   -- number of height waves along the curve
    pattern          : str   -- repeating shape order, B = box, C = cylinder, S = sphere
    side_pattern     : str   -- repeating ring side, U = on top (up), D = underneath (down)
    thickness        : float -- ring thickness, distance from the top to the bottom surface
    gap              : float -- minimum free distance between two objects

    Returns (objects, colors): a Brep list and a System.Drawing.Color list.
    """
    objects = []
    colors = []
    count = int(count)
    if count < 1 or not pattern:
        return objects, colors

    params = curve.DivideByCount(count, True)
    if params is None:
        return objects, colors

    side_pattern = side_pattern or "U"
    placed = {"U": [], "D": []}  # (point, footprint radius) of objects per ring side

    for i, t in enumerate(params):
        point = curve.PointAt(t)
        tangent = curve.TangentAt(t)
        side = rg.Vector3d.CrossProduct(rg.Vector3d.ZAxis, tangent)

        size = base_size * (1.0 + size_variation * math.sin(2.0 * math.pi * size_waves * i / count))
        size = max(size, 0.2 * base_size)
        shape = pattern[i % len(pattern)].upper()
        ring_side = "D" if side_pattern[i % len(side_pattern)].upper() == "D" else "U"

        # footprint = circle around the ground plan; a box needs its diagonal
        footprint = 0.5 if shape in ("C", "S") else 0.5 * math.sqrt(2.0)
        radius = footprint * size

        # shrink until the gap to every object on the same side is kept
        for other_point, other_radius in placed[ring_side]:
            radius = min(radius, point.DistanceTo(other_point) - other_radius - gap)
        if radius < footprint * 0.2 * base_size:
            continue  # no room left, this spot stays empty
        placed[ring_side].append((point, radius))
        size = radius / footprint

        rise = 0.5 + 0.5 * math.cos(2.0 * math.pi * height_waves * i / count)  # 0..1
        height = size * (1.0 + height_variation * rise)

        # local plane: X along the curve, Z away from the ring surface
        if ring_side == "D":
            base = point + rg.Vector3d(0, 0, -thickness)
            plane = rg.Plane(base, tangent, side * -1.0)  # Z points down
        else:
            base = point
            plane = rg.Plane(base, tangent, side)         # Z points up

        half = size / 2.0
        if shape == "C":
            obj = rg.Cylinder(rg.Circle(plane, half), height).ToBrep(True, True)
        elif shape == "S":
            obj = rg.Sphere(base + plane.ZAxis * half, half).ToBrep()
        else:
            box = rg.Box(plane, rg.Interval(-half, half), rg.Interval(-half, half),
                         rg.Interval(0, height))
            obj = box.ToBrep()

        objects.append(obj)
        colors.append(OBJECT_COLORS[i % len(OBJECT_COLORS)])

    return objects, colors


# ----------------------------------------------------------------------
# Full composition
# ----------------------------------------------------------------------
def create_bauhaus_planet(center=None, planet_radius=10.0,
                          crater_count=12, crater_min=0.08, crater_max=0.3,
                          crater_depth=0.35, rim_chance=0.0,
                          ring_gap=1.3, ring_width=1.2, ring_thickness=0.04,
                          ring_tilt=20.0, ring_turn=30.0,
                          curve_waves=6, curve_amplitude=0.8, curve_phase=0.0,
                          object_count=24, object_scale=0.25, size_variation=0.5,
                          size_waves=3, height_variation=1.5, height_waves=2,
                          pattern="BCSB", side_pattern="U", object_gap=0.15, seed=1):
    """
    The whole Bauhaus planet composition.

    center           : Rhino.Geometry.Point3d -- planet center
    planet_radius    : float -- master size, all other lengths are ratios of it
    crater_count     : int   -- number of craters
    crater_min       : float -- smallest crater radius / planet_radius
    crater_max       : float -- largest crater radius / planet_radius
    crater_depth     : float -- crater depth / crater radius (0..1)
    rim_chance       : float -- share of craters with a raised rim (0..1), off by default
    ring_gap        : float -- ring inner radius / planet_radius (> 1)
    ring_width       : float -- ring width / planet_radius
    ring_thickness   : float -- ring thickness / planet_radius
    ring_tilt        : float -- tilt of the ring around its X axis, degrees
    ring_turn        : float -- rotation of the tilted ring around world Z, degrees
    curve_waves      : int   -- waves of the meander on one round
    curve_amplitude  : float -- 0..1, share of the free band width the meander uses
    curve_phase      : float -- rotates the meander around the ring, degrees
    object_count     : int   -- number of objects on the curve
    object_scale     : float -- object size / ring width
    size_variation   : float -- see place_objects_on_curve
    size_waves       : int   -- see place_objects_on_curve
    height_variation : float -- see place_objects_on_curve
    height_waves     : int   -- see place_objects_on_curve
    pattern          : str   -- shape order, B = box, C = cylinder, S = sphere
    side_pattern     : str   -- ring side order, U = on top, D = underneath (e.g. "UD")
    object_gap       : float -- minimum gap between objects / object base size
    seed            : int   -- random seed for the craters

    Returns (planet, rims, ring, curve, objects, colors).
    """
    if center is None:
        center = rg.Point3d(0, 0, 0)

    planet, rims = create_cratered_planet(center, planet_radius, crater_count,
                                          crater_min, crater_max, crater_depth,
                                          rim_chance, seed=seed)

    # ring dimensions derived from the planet
    ring_gap = max(ring_gap, 1.05)  # the hole must stay larger than the planet
    inner_radius = planet_radius * ring_gap
    band = planet_radius * ring_width
    outer_radius = inner_radius + band
    thickness = planet_radius * ring_thickness
    ring = create_ring_disc(inner_radius, outer_radius, thickness)

    # objects must fit on the band: cap the size, then use the rest for the meander
    max_size = band * object_scale * (1.0 + size_variation)
    largest_allowed = 0.9 * band / math.sqrt(2.0)  # diagonal of a box footprint
    if max_size > largest_allowed:
        object_scale *= largest_allowed / max_size
        max_size = largest_allowed
    free_half_band = band / 2.0 - max_size / math.sqrt(2.0)
    amplitude = max(0.0, min(curve_amplitude, 1.0)) * max(free_half_band, 0.0)

    curve = create_meander_curve(inner_radius + band / 2.0, amplitude, curve_waves,
                                 thickness / 2.0, curve_phase)
    base_size = band * object_scale
    objects, colors = place_objects_on_curve(curve, object_count, base_size,
                                             size_variation, size_waves,
                                             height_variation, height_waves, pattern,
                                             side_pattern, thickness, base_size * object_gap)

    # move the flat ring system into its tilted position around the planet
    ring_plane = rg.Plane(center, rg.Vector3d.ZAxis)
    ring_plane.Rotate(math.radians(ring_tilt), ring_plane.XAxis)
    ring_plane.Rotate(math.radians(ring_turn), rg.Vector3d.ZAxis)
    placement = rg.Transform.PlaneToPlane(rg.Plane.WorldXY, ring_plane)

    ring.Transform(placement)
    curve.Transform(placement)
    for obj in objects:
        obj.Transform(placement)

    return planet, rims, ring, curve, objects, colors


# ----------------------------------------------------------------------
# Universe: several Bauhaus planets
# ----------------------------------------------------------------------
PLANET_COLORS = [YELLOW, RED, BLUE, WHITE, BLACK]


def create_bauhaus_universe(center=None, planet_count=6, radius_min=4.0, radius_max=12.0,
                            spread=1.5, max_tilt=45.0, crater_count=12, object_count=24,
                            seed=1, **planet_options):
    """
    Several Bauhaus planets scattered in space. Each planet gets a random
    size, its own ring tilt and turn and its own planet and ring color.

    Relationships:
    * crater count and object count grow with the planet size
      (the largest planet gets crater_count / object_count)
    * planets never overlap: each one is treated as a sphere enclosing
      planet and ring, and positions are retried until they are free
    * the space grows with the number and size of the planets (spread)
    * the ring color is never the color of its own planet

    center         : Rhino.Geometry.Point3d -- center of the universe
    planet_count   : int   -- number of planets (fewer if they do not fit)
    radius_min     : float -- smallest planet radius
    radius_max     : float -- largest planet radius
    spread         : float -- size of the space; 1 = tightly packed, larger = more empty space
    max_tilt       : float -- largest ring tilt in degrees (every planet gets a random tilt)
    crater_count   : int   -- craters on the largest possible planet
    object_count   : int   -- objects on the ring of the largest possible planet
    seed           : int   -- random seed for sizes, positions, angles and colors
    planet_options : any other create_bauhaus_planet parameter (e.g. ring_width,
                     pattern, side_pattern), used for every planet

    Returns (planets, rings, curves, objects, object_colors, planet_colors, ring_colors):
    lists; planets/planet_colors and rings/ring_colors match item by item,
    objects/object_colors as well.
    """
    if center is None:
        center = rg.Point3d(0, 0, 0)

    rng = random.Random(seed)
    planet_count = int(planet_count)
    radius_max = max(radius_max, radius_min)

    # radius of a sphere that encloses planet and ring, per unit of planet radius
    ring_gap = max(planet_options.get("ring_gap", 1.3), 1.05)
    ring_width = planet_options.get("ring_width", 1.2)
    enclose = ring_gap + ring_width

    # cube the planets are scattered in; grows with count and size
    half = spread * enclose * radius_max * max(planet_count, 1) ** (1.0 / 3.0)

    planets, rings, curves, objects = [], [], [], []
    object_colors, planet_colors, ring_colors = [], [], []
    placed = []  # (center, enclosing radius)

    for i in range(planet_count):
        radius = rng.uniform(radius_min, radius_max)
        reach = radius * enclose

        # random position that keeps clear of all planets placed so far
        position = None
        for _ in range(200):
            candidate = center + rg.Vector3d(rng.uniform(-half, half),
                                             rng.uniform(-half, half),
                                             rng.uniform(-half, half))
            if all(candidate.DistanceTo(c) > reach + r for c, r in placed):
                position = candidate
                break
        if position is None:
            continue  # no free spot found, universe is full
        placed.append((position, reach))

        size_ratio = radius / radius_max
        planet_color = rng.choice(PLANET_COLORS)
        ring_color = rng.choice([c for c in PLANET_COLORS if c != planet_color])

        planet, rims, ring, curve, objs, cols = create_bauhaus_planet(
            center=position, planet_radius=radius,
            crater_count=int(round(crater_count * size_ratio)),
            object_count=max(int(round(object_count * size_ratio)), 3),
            ring_tilt=rng.uniform(0.0, max_tilt), ring_turn=rng.uniform(0.0, 360.0),
            seed=seed * 1000 + i, **planet_options)

        planets.append(planet)
        rings.append(ring)
        curves.append(curve)
        objects.extend(objs)
        object_colors.extend(cols)
        planet_colors.append(planet_color)
        ring_colors.append(ring_color)

    return planets, rings, curves, objects, object_colors, planet_colors, ring_colors
