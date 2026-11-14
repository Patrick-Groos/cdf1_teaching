"""
Geometry basics -- reusable Rhino.Geometry functions for Grasshopper.

Adding a new function with Copilot
-----------------------------------
1. Open this file and select this chat model, then ask Copilot something like:
   "Add a function here, all in Rhino geometry, that builds a <your shape/idea>.
   Follow the same style as create_cone / create_fractal_tree (defaults for
   optional inputs, a docstring listing params, return a Rhino.Geometry object)."
2. Once the function is added, ask Copilot:
   "Give me the Python code to use this function in a Grasshopper GHPython 3
   component, importing it from computational_design_and_fabrication."
3. Copy the snippet Copilot gives you into a GHPython component, wire up the
   inputs as sliders/panels, and set the output variable (e.g. `a`).
"""

import math
import Rhino.Geometry as rg
import random

def create_fractal_tree(
    base_point=None,
    base_plane=None,
    length=10.0,
    angle=25.0,
    length_factor=0.7,
    depth=8,
    branch_count=2,
):
    """
    Build a fractal (recursively branching) tree as a list of line segments.

    base_point    : Rhino.Geometry.Point3d -- start point of the trunk
    base_plane    : Rhino.Geometry.Plane   -- plane whose YAxis is the trunk
                     direction and ZAxis is the branching rotation axis
    length        : float -- trunk length
    angle         : float -- angle in degrees between sibling branches
    length_factor : float -- length multiplier applied at each new generation
    depth         : int   -- number of recursive branching generations
    branch_count  : int   -- number of branches spawned at each node

    Returns a list of Rhino.Geometry.Line.
    """
    if base_point is None:
        base_point = rg.Point3d(0, 0, 0)
    if base_plane is None:
        base_plane = rg.Plane.WorldXY

    lines = []

    def _grow(start, direction, branch_length, remaining_depth):
        if remaining_depth <= 0 or branch_length <= 1e-6:
            return

        end = start + direction * branch_length
        lines.append(rg.Line(start, end))

        if branch_count <= 1:
            offsets = [0.0]
        else:
            span = angle * (branch_count - 1)
            offsets = [-span / 2.0 + i * angle for i in range(branch_count)]

        for offset in offsets:
            rotated_direction = rg.Vector3d(direction)
            rotated_direction.Rotate(math.radians(offset), base_plane.ZAxis)
            _grow(end, rotated_direction, branch_length * length_factor, remaining_depth - 1)

    _grow(base_point, base_plane.YAxis, length, depth)

    return lines


def create_crochet_pseudosphere(
    rounds=4,
    first_round=12,
    increase=3,
    base_chain=4,
    stitch_width=1.0,
    stitch_height=2.0,
    iterations=150,
    seed=1,
    max_stitches=1500,
):
    """Build a crocheted hyperbolic form ("pseudosphere") as a mesh.

    The function follows the crochet pattern step by step:
      1. a small ring made of chain stitches,
      2. a first round of double crochets into the ring,
      3. more rounds, where every stitch gets `increase` new stitches.

    Each stitch is one mesh vertex. After every new round the stitches are
    relaxed like small springs: a stitch wants to keep its width and its
    height, and two stitches cannot be in the same place. Each round has more
    stitches than a flat circle has room for, so the surface has to ruffle.

    Params:au
        rounds (int): Number of rounds worked into the ring. Default 4.
            Stitch count is multiplied by `increase` every round, so keep
            this low (5 rounds with increase 3 is already 972 stitches).
        first_round (int): Stitches in the first round. Default 12.
        increase (int): New stitches worked into each stitch. Default 3.
            1 gives a tube, 2 gives soft ruffles, 3 gives dense ruffles.
        base_chain (int): Chain stitches in the starting ring. Default 4.
            Only sets the size of the hole in the middle.
        stitch_width (float): Width of one stitch. Default 1.0.
        stitch_height (float): Height of one round. Default 2.0
            (a double crochet is about twice as tall as it is wide).
        iterations (int): Relaxation steps after each round. Default 150.
            More steps give a smoother result but take longer.
        seed (int): Seed for the small random offsets that let the surface
            ruffle. Same seed gives the same shape. Default 1.
        max_stitches (int): Safety limit on stitches in a single round.
            Rounds that would exceed it are skipped, so the form stops
            growing instead of freezing Rhino. Default 1500.

    Returns:
        Rhino.Geometry.Mesh: The crocheted surface. Each vertex is the top
        of one stitch, each ring of vertices is one round.
    """
    rng = random.Random(seed)

    points = []    # [x, y, z] of every stitch
    fixed = []     # True for stitches that must not move (the starting ring)
    springs = []   # (i, j, rest_length, stiffness)
    linked = set() # pairs joined by a spring, these are skipped in collision
    faces = []     # (a, b, c) vertex indices

    def add_spring(i, j, rest, stiffness):
        springs.append((i, j, rest, stiffness))
        linked.add((min(i, j), max(i, j)))

    # ------------------------------------------------------------------
    # 1 + 2. Starting ring (the joined chain). It stays fixed at the origin.
    # ------------------------------------------------------------------
    ring_radius = base_chain * stitch_width / (2.0 * math.pi)
    ring = []
    for i in range(first_round):
        angle = 2.0 * math.pi * i / first_round
        points.append([ring_radius * math.cos(angle),
                       ring_radius * math.sin(angle),
                       0.0])
        fixed.append(True)
        ring.append(i)

    # ------------------------------------------------------------------
    # Relaxation: springs keep stitch sizes, collisions keep stitches apart.
    # ------------------------------------------------------------------
    collision_distance = 0.9 * stitch_width

    def relax(steps):
        for _ in range(steps):
            # springs
            for i, j, rest, stiffness in springs:
                a = points[i]
                b = points[j]
                dx = b[0] - a[0]
                dy = b[1] - a[1]
                dz = b[2] - a[2]
                length = math.sqrt(dx * dx + dy * dy + dz * dz)
                if length < 1e-9:
                    continue
                move = stiffness * (length - rest) / length
                if fixed[i] and fixed[j]:
                    continue
                if fixed[i]:
                    b[0] -= dx * move
                    b[1] -= dy * move
                    b[2] -= dz * move
                elif fixed[j]:
                    a[0] += dx * move
                    a[1] += dy * move
                    a[2] += dz * move
                else:
                    move *= 0.5
                    a[0] += dx * move
                    a[1] += dy * move
                    a[2] += dz * move
                    b[0] -= dx * move
                    b[1] -= dy * move
                    b[2] -= dz * move

            # collisions: sort stitches into a grid, compare only neighbours
            cell = collision_distance
            grid = {}
            for index, p in enumerate(points):
                key = (int(math.floor(p[0] / cell)),
                       int(math.floor(p[1] / cell)),
                       int(math.floor(p[2] / cell)))
                grid.setdefault(key, []).append(index)

            for (cx, cy, cz), members in grid.items():
                for ox in (-1, 0, 1):
                    for oy in (-1, 0, 1):
                        for oz in (-1, 0, 1):
                            others = grid.get((cx + ox, cy + oy, cz + oz))
                            if not others:
                                continue
                            for i in members:
                                for j in others:
                                    if j <= i:
                                        continue
                                    if fixed[i] and fixed[j]:
                                        continue
                                    if (i, j) in linked:
                                        continue
                                    a = points[i]
                                    b = points[j]
                                    dx = b[0] - a[0]
                                    dy = b[1] - a[1]
                                    dz = b[2] - a[2]
                                    d2 = dx * dx + dy * dy + dz * dz
                                    if d2 >= cell * cell or d2 < 1e-12:
                                        continue
                                    dist = math.sqrt(d2)
                                    push = (cell - dist) / dist
                                    if fixed[i]:
                                        b[0] += dx * push
                                        b[1] += dy * push
                                        b[2] += dz * push
                                    elif fixed[j]:
                                        a[0] -= dx * push
                                        a[1] -= dy * push
                                        a[2] -= dz * push
                                    else:
                                        push *= 0.5
                                        a[0] -= dx * push
                                        a[1] -= dy * push
                                        a[2] -= dz * push
                                        b[0] += dx * push
                                        b[1] += dy * push
                                        b[2] += dz * push

    # ------------------------------------------------------------------
    # 3 + 4. Work the rounds. Round 1 puts one stitch on each ring position,
    # every later round puts `increase` stitches into each stitch.
    # ------------------------------------------------------------------
    grow_from = {}  # stitch index -> index of the stitch it was worked into

    for round_index in range(rounds):
        per_stitch = 1 if round_index == 0 else increase
        if len(ring) * per_stitch > max_stitches:
            break  # next round would be too big, stop at the last one that fits
        new_ring = []
        children_of = []

        for parent in ring:
            p = points[parent]

            # growth direction: continue the line from grandparent to parent
            if parent in grow_from:
                g = points[grow_from[parent]]
                direction = [p[0] - g[0], p[1] - g[1], p[2] - g[2]]
            else:
                direction = [p[0], p[1], 0.0]
            size = math.sqrt(sum(c * c for c in direction)) or 1.0
            direction = [c / size for c in direction]

            children = []
            for _ in range(per_stitch):
                jitter = 0.3 * stitch_width
                points.append([
                    p[0] + direction[0] * stitch_height + rng.uniform(-jitter, jitter),
                    p[1] + direction[1] * stitch_height + rng.uniform(-jitter, jitter),
                    p[2] + direction[2] * stitch_height + rng.uniform(-jitter, jitter),
                ])
                fixed.append(False)
                child = len(points) - 1
                grow_from[child] = parent
                children.append(child)
                new_ring.append(child)
                # the post of the stitch
                add_spring(parent, child, stitch_height, 1.0)
            children_of.append(children)

        count = len(new_ring)
        for k in range(count):
            # top of the round: every stitch is one stitch_width wide
            add_spring(new_ring[k], new_ring[(k + 1) % count], stitch_width, 1.0)
            # weak spring to the stitch after next, keeps the round smooth
            if count > 4:
                add_spring(new_ring[k], new_ring[(k + 2) % count],
                           2.0 * stitch_width, 0.15)

        # faces between the old round and the new round
        parents = len(ring)
        for j in range(parents):
            children = children_of[j]
            next_parent = ring[(j + 1) % parents]
            next_child = children_of[(j + 1) % parents][0]
            for k in range(len(children) - 1):
                faces.append((ring[j], children[k], children[k + 1]))
            faces.append((ring[j], children[-1], next_child))
            faces.append((ring[j], next_child, next_parent))

        ring = new_ring
        relax(iterations)

    # ------------------------------------------------------------------
    # Build the Rhino mesh
    # ------------------------------------------------------------------
    mesh = rg.Mesh()
    for p in points:
        mesh.Vertices.Add(p[0], p[1], p[2])
    for a, b, c in faces:
        mesh.Faces.AddFace(a, b, c)
    mesh.Normals.ComputeNormals()
    mesh.Compact()
    return mesh


def create_hyperbolic_paraboloid(
    width=20.0,
    length=20.0,
    height=5.0,
    divisions=30,
    base_point=None,
):
    """Build a mesh of a hyperbolic paraboloid (saddle surface).

    width      : float -- extent in the X direction
    length     : float -- extent in the Y direction
    height     : float -- saddle depth/height
    divisions  : int   -- number of mesh divisions in each direction
    base_point : Rhino.Geometry.Point3d -- center of the surface

    Returns a Rhino.Geometry.Mesh.
    """
    if base_point is None:
        base_point = rg.Point3d(0, 0, 0)

    divisions = max(2, int(divisions))
    mesh = rg.Mesh()

    for j in range(divisions + 1):
        v = -1.0 + 2.0 * j / divisions
        y = base_point.Y + v * length / 2.0
        for i in range(divisions + 1):
            u = -1.0 + 2.0 * i / divisions
            x = base_point.X + u * width / 2.0
            z = base_point.Z + height * (u * u - v * v)
            mesh.Vertices.Add(x, y, z)

    row_size = divisions + 1
    for j in range(divisions):
        for i in range(divisions):
            index = j * row_size + i
            mesh.Faces.AddFace(
                index,
                index + 1,
                index + row_size + 1,
                index + row_size,
            )

    mesh.Normals.ComputeNormals()
    mesh.Compact()
    return mesh

# ======================================================================
# Tangent sphere growth
# ======================================================================


def random_unit_vector():
    """Return a random direction on the unit sphere."""
    z = random.uniform(-1.0, 1.0)
    t = random.uniform(0.0, 2.0 * math.pi)
    r = math.sqrt(1.0 - z * z)
    return rg.Vector3d(r * math.cos(t), r * math.sin(t), z)


def rotate_vector(v, axis, angle_rad):
    """Rotate vector v around axis by angle (radians).

    Params:
        v (Rhino.Geometry.Vector3d): Vector to rotate. It is not changed.
        axis (Rhino.Geometry.Vector3d): Rotation axis.
        angle_rad (float): Rotation angle in radians.

    Returns:
        Rhino.Geometry.Vector3d: The rotated copy of v.
    """
    # 1.1 -- copy the input vector and the axis
    vv = rg.Vector3d(v)
    ax = rg.Vector3d(axis)

    # 1.2 -- the axis must be unit length
    ax.Unitize()

    # 1.3 -- build a Rhino rotation transform around the world origin
    xform = rg.Transform.Rotation(
        angle_rad,
        ax,
        rg.Point3d.Origin,
    )

    # 1.4 -- apply the transform to the vector (in place)
    vv.Transform(xform)

    return vv


def random_deflect(dir_vec, angle_max):
    """Deflect a direction vector by a random small rotation.

    Idea:
      - build a plane perpendicular to the direction,
      - pick a random axis in that plane,
      - rotate by a random angle up to angle_max.

    Params:
        dir_vec (Rhino.Geometry.Vector3d): Direction to deflect.
        angle_max (float): Largest deflection angle in radians.

    Returns:
        Rhino.Geometry.Vector3d: The deflected direction.
    """
    # 1.5 -- copy and unitize the incoming direction
    d = rg.Vector3d(dir_vec)
    d.Unitize()

    # choose a helper vector that is not (nearly) parallel to d
    helper = rg.Vector3d(0, 0, 1)
    if abs(rg.Vector3d.Multiply(d, helper)) > 0.95:
        helper = rg.Vector3d(0, 1, 0)

    # 1.6 -- build a perpendicular frame U, V around d
    U = rg.Vector3d.CrossProduct(d, helper)
    U.Unitize()
    V = rg.Vector3d.CrossProduct(d, U)
    V.Unitize()

    # 1.7 -- pick a random axis in the perpendicular plane
    phi = random.uniform(0.0, 2.0 * math.pi)
    axis = U * math.cos(phi) + V * math.sin(phi)

    # 1.8 -- rotate by a random angle up to angle_max
    ang = random.uniform(0.0, angle_max)
    return rotate_vector(d, axis, ang)


def cell_key(pt, cs):
    """Map a 3D point to a grid cell index (ix, iy, iz) for cell size cs."""
    return (
        int(math.floor(pt.X / cs)),
        int(math.floor(pt.Y / cs)),
        int(math.floor(pt.Z / cs)),
    )


def neighbor_keys(k):
    """Yield the 27 cell keys around and including cell k (3x3x3)."""
    x, y, z = k
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                yield (x + dx, y + dy, z + dz)


def can_place_tangent(center, r_child, grid, cs, eps=1e-6):
    """Check whether a sphere can be placed without overlapping others.

    Touching is allowed, overlapping is not. Two spheres overlap when
        distance < r_child + r_existing - eps

    Params:
        center (Rhino.Geometry.Point3d): Center of the new sphere.
        r_child (float): Radius of the new sphere.
        grid (dict): Spatial hash, cell key -> list of (center, radius).
        cs (float): Cell size of the grid.
        eps (float): Tolerance so touching spheres count as free. Default 1e-6.

    Returns:
        bool: True if the sphere fits.
    """
    k = cell_key(center, cs)

    # 2.2 -- only check spheres in nearby grid cells
    for nk in neighbor_keys(k):
        if nk not in grid:
            continue

        for (c2, r2) in grid[nk]:
            # 2.1 -- overlap rule
            if center.DistanceTo(c2) < (r_child + r2 - eps):
                return False

    return True


def add_to_grid(center, radius, grid, cs):
    """Store (center, radius) in its grid cell for fast lookup later."""
    key = cell_key(center, cs)
    # 2.3 -- store center and radius
    grid.setdefault(key, []).append((center, radius))


def grow_tangent_spheres(
    seed_pt=None,
    seed_radius=5.0,
    iterations=30,
    radius_decay=0.92,
    branch_chance=0.2,
    angle_max=0.8,
    min_radius=0.5,
    seed_dir=None,
    seed=None,
):
    """Grow a branching chain of touching spheres from a seed sphere.

    Every generation, each tip places one child sphere (sometimes two) that
    touches its parent. The child is a bit smaller and points in a slightly
    deflected direction. Children that would overlap an existing sphere are
    retried in another direction; growth stops when nothing fits anymore.

    Params:
        seed_pt (Rhino.Geometry.Point3d): Start point. Default world origin.
        seed_radius (float): Radius of the first sphere. Default 5.0.
        iterations (int): Maximum number of generations. Default 30.
        radius_decay (float): Shrink factor per generation. Default 0.92.
        branch_chance (float): Chance (0-1) that a tip gets a second child.
            Default 0.2.
        angle_max (float): Largest deflection per generation, in radians.
            Default 0.8. Below about 0.6 a second child never fits beside
            its sibling, so the growth does not branch.
        min_radius (float): Stop growing a branch when spheres get smaller
            than this. Default 0.5.
        seed_dir (Rhino.Geometry.Vector3d): Initial direction. None picks a
            random one. Default None.
        seed (int): Random seed; the same seed gives the same result.
            None gives a new result every time. Default None.

    Returns:
        tuple: (spheres, lines, tip_points)
            spheres    -- list of Rhino.Geometry.Sphere
            lines      -- list of Rhino.Geometry.Line, parent to child
            tip_points -- list of Rhino.Geometry.Point3d, the last tips
    """
    if seed_pt is None:
        seed_pt = rg.Point3d(0, 0, 0)
    if seed is not None:
        random.seed(seed)

    # STEP 3 -- initial direction: use seed_dir if given, otherwise random
    if seed_dir:
        # 3.1 -- copy and unitize seed_dir
        d0 = rg.Vector3d(seed_dir)
        d0.Unitize()
    else:
        d0 = random_unit_vector()

    spheres, lines = [], []

    # 4.1 -- cell size for the spatial hash. Two spheres can only collide
    # when their centers are closer than the sum of their radii, which is
    # at most 2 * seed_radius. With cells at least that big, checking the
    # 3x3x3 neighbouring cells is enough to find every possible collision.
    cell_size = max(2.0 * seed_radius, 2.0 * min_radius)

    grid = {}

    # 4.2 -- create the seed sphere and store it in the grid
    spheres.append(rg.Sphere(seed_pt, seed_radius))
    add_to_grid(seed_pt, seed_radius, grid, cell_size)

    # 4.3 -- tips are the active growth states: (point, direction, radius)
    tips = [(seed_pt, d0, seed_radius)]

    for i in range(iterations):

        new_tips = []

        # 4.4 -- grow from each active tip
        for (pt, d, r_parent) in tips:

            # child radius shrinks
            r_child = r_parent * radius_decay
            if r_child < min_radius:
                continue

            # 4.5 -- branching: usually 1 child, sometimes 2
            n_children = 1 + (1 if random.random() < branch_chance else 0)

            for c in range(n_children):

                # 4.6 -- try up to 20 directions to find a free placement
                for t in range(20):

                    # new direction = deflected parent direction
                    d_child = random_deflect(d, angle_max)
                    d_child.Unitize()

                    # 4.7 -- tangency rule:
                    # distance between centers = r_parent + r_child
                    step = r_parent + r_child
                    new_pt = pt + d_child * step

                    # 4.8 -- accept only if nothing overlaps
                    if can_place_tangent(new_pt, r_child, grid, cell_size, eps=1e-4):

                        spheres.append(rg.Sphere(new_pt, r_child))
                        add_to_grid(new_pt, r_child, grid, cell_size)

                        # connection line from parent to child
                        lines.append(rg.Line(pt, new_pt))

                        # the child becomes a new tip
                        new_tips.append((new_pt, d_child, r_child))
                        break  # placed, stop trying

        # 4.9 -- stop early if nothing new could be placed
        if not new_tips:
            break

        tips = new_tips

    # STEP 5 -- output only the tip points
    tip_points = [pt for (pt, d, r) in tips]

    return spheres, lines, tip_points


# ======================================================================
# Assignment 2.1 -- hyperbolic forms (geometric algorithm, no simulation)
#   create_hyperbolic_strip   : flat on one side, ruffled on the other
#   create_hyperbolic_trumpet : tube that opens into a ruffled rim
#
# Hyperbolic idea used by both: the length available along an edge grows
# EXPONENTIALLY (like the circumference of a circle in the hyperbolic plane).
# A straight edge cannot hold the extra length, so the edge becomes a wave.
# The wave amplitude is chosen so the wavy edge has exactly the extra length.
# ======================================================================


def _wave_amplitude(stretch, wavelength):
    """Amplitude of a sine wave that is `stretch` times longer than straight.

    A sine z = a * sin(2*pi*x / wavelength) is about
    sqrt(1 + (2*pi*a / wavelength)**2 / 2) times longer than its straight
    base line. Solving for a gives the formula below.
    """
    if stretch <= 1.0:
        return 0.0
    return wavelength / (2.0 * math.pi) * math.sqrt(2.0 * (stretch * stretch - 1.0))


def _profile_value(u, profile):
    """Where the strip ruffles: 0 = flat, 1 = full growth. u runs 0..1."""
    if profile == "peak":
        return math.sin(math.pi * u)
    if profile == "wave":
        return 0.5 - 0.5 * math.cos(4.0 * math.pi * u)
    return u  # "linear"


def _grid_mesh(grid, closed):
    """Quad mesh from a grid of points (list of rows).

    closed=True joins the last point of every row back to the first one.
    """
    mesh = rg.Mesh()
    rows = len(grid)
    cols = len(grid[0])
    for row in grid:
        for p in row:
            mesh.Vertices.Add(p.X, p.Y, p.Z)
    last = cols if closed else cols - 1
    for i in range(rows - 1):
        for j in range(last):
            jn = (j + 1) % cols
            mesh.Faces.AddFace(i * cols + j, i * cols + jn,
                               (i + 1) * cols + jn, (i + 1) * cols + j)
    mesh.Normals.ComputeNormals()
    mesh.Compact()
    return mesh


def create_hyperbolic_strip(
    length=20.0,
    width=8.0,
    growth=4.0,
    profile="linear",
    waves=6,
    curve_count=8,
    resolution=120,
):
    """Build a strip that is flat along its base edge and ruffles towards the top.

    Algorithm:
      1. Walk over a grid: x along the strip (0..length), y across it (0..width).
      2. At every point compute how much longer the row is there than a flat
         row would be. This stretch grows exponentially with y (hyperbolic):
             stretch = growth ** (profile(x) * y / width)
         profile(x) decides WHERE the strip grows (0 = never, 1 = fully).
      3. Turn the extra length into a wave: z = a * sin(2*pi*x / wavelength),
         with the amplitude a that gives exactly that stretch.
      4. Build a mesh and some row curves from the grid.

    Params:
        length (float): Length of the strip along X. Default 20.0.
        width (float): Width of the strip along Y. Default 8.0.
        growth (float): How much longer the top edge is than the base edge
            where profile = 1. 1 = flat strip. Default 4.0.
        profile (str): Where the strip ruffles. "linear" = flat left,
            ruffled right; "peak" = ruffled in the middle; "wave" = two
            ruffled zones. Default "linear".
        waves (int): Number of waves along the strip. Default 6.
        curve_count (int): Number of row curves for the drawing. Default 8.
        resolution (int): Grid points along the strip; across the strip a
            quarter of it is used. Default 120.

    Returns:
        tuple: (mesh, curves)
            mesh    -- Rhino.Geometry.Mesh
            curves  -- list of Rhino.Geometry.PolylineCurve, rows across the strip
    """
    length = float(length)
    width = float(width)
    growth = max(1.0, float(growth))
    profile = str(profile).strip().lower()
    waves = max(1, int(waves))
    nx = max(8, int(resolution))
    ny = max(4, nx // 4)
    wavelength = length / waves
    k = math.log(growth)

    def point(x, y):
        stretch = math.exp(k * _profile_value(x / length, profile) * y / width)
        a = _wave_amplitude(stretch, wavelength)
        return rg.Point3d(x, y, a * math.sin(2.0 * math.pi * x / wavelength))

    # 1.-3. grid of points: one row per y value
    grid = []
    for i in range(ny + 1):
        y = width * i / ny
        grid.append([point(length * j / nx, y) for j in range(nx + 1)])

    # 4. geometry
    mesh = _grid_mesh(grid, closed=False)
    curves = []
    for c in range(max(2, int(curve_count))):
        y = width * c / (max(2, int(curve_count)) - 1)
        polyline = rg.Polyline()
        for j in range(nx * 2 + 1):
            polyline.Add(point(length * j / (nx * 2), y))
        curves.append(rg.PolylineCurve(polyline))
    return mesh, curves


def create_hyperbolic_trumpet(
    radius=2.0,
    height=10.0,
    flare=3.0,
    growth=2.0,
    waves=7,
    curve_count=10,
    resolution=144,
):
    """Build a trumpet: a narrow tube that opens into a ruffled, hyperbolic rim.

    Algorithm:
      1. Walk up the trumpet with t from 0 (bottom) to 1 (rim).
      2. The opening: the radius widens slowly at first, then fast
             R(t) = radius * flare ** (t ** 2)
      3. The ruffle: each ring is longer than a circle of radius R by
             stretch(t) = growth ** (t ** 3)
         so the extra length appears only near the rim and then grows fast.
      4. Turn the extra length into a wave around the ring:
             z = height * t + a * sin(waves * angle)
         with the amplitude a that gives exactly that stretch.
      5. Build a mesh and some ring curves.

    Params:
        radius (float): Radius of the tube at the bottom. Default 2.0.
        height (float): Height of the trumpet. Default 10.0.
        flare (float): Rim radius divided by bottom radius. Default 3.0.
        growth (float): How much longer the rim is than a plain circle.
            1 = smooth rim, higher = stronger ruffles. Default 2.0.
        waves (int): Number of waves around the rim. Default 7.
        curve_count (int): Number of ring curves for the drawing. Default 10.
        resolution (int): Points around each ring; up the trumpet a quarter
            of it is used. Default 144.

    Returns:
        tuple: (mesh, curves)
            mesh    -- Rhino.Geometry.Mesh
            curves  -- list of closed Rhino.Geometry.PolylineCurve (rings)
    """
    radius = float(radius)
    height = float(height)
    flare = max(1.0, float(flare))
    growth = max(1.0, float(growth))
    waves = max(1, int(waves))
    na = max(12, int(resolution))
    nt = max(6, na // 4)

    def point(t, angle):
        r = radius * flare ** (t * t)
        stretch = growth ** (t ** 3)
        a = _wave_amplitude(stretch, 2.0 * math.pi * r / waves)
        return rg.Point3d(r * math.cos(angle), r * math.sin(angle),
                          height * t + a * math.sin(waves * angle))

    # 1.-4. grid of points: one closed ring per t value
    grid = []
    for i in range(nt + 1):
        t = i / float(nt)
        grid.append([point(t, 2.0 * math.pi * j / na) for j in range(na)])

    # 5. geometry
    mesh = _grid_mesh(grid, closed=True)
    curves = []
    count = max(2, int(curve_count))
    for c in range(count):
        t = c / float(count - 1)
        polyline = rg.Polyline()
        for j in range(na * 2 + 1):
            polyline.Add(point(t, 2.0 * math.pi * j / (na * 2)))
        curves.append(rg.PolylineCurve(polyline))
    return mesh, curves
