# Vorlesung 2.1 – Beispiele 1–9 in Grasshopper

Der Code liegt in `src\cdf\lecture_02_examples.py`. Jede Figur aus den Folien ist dort eine Funktion.
In Grasshopper brauchst du pro Beispiel nur einen **Python 3 Script**-Baustein mit 1–2 Zeilen Code.

## Einmalig vorbereiten

1. Rhino 8 → `Grasshopper` → `exercises\geometry-basics\geometry_basics.ghx` öffnen.
2. Prüfen, dass der Modul-Suchpfad gesetzt ist (siehe README, Schritt „Setting up Rhino/Grasshopper“):
   Script-Editor → *Tools → Options → Python 3 → Module search paths* → `...\cdf1_teaching\src`.
3. Im Bereich **„Auto-reloads cdf module on VScode changes“** den *File Path*-Baustein auf deinen `src`-Ordner setzen.
   Dann lädt Grasshopper den Code jedes Mal neu, wenn du in VS Code speicherst.

## Arbeitsweise pro Beispiel

1. Neuen **Python 3 Script**-Baustein auf die Arbeitsfläche ziehen (*Maths → Script*).
2. Mit dem Zoom am Baustein die **Inputs** (+/−) anlegen und genau wie unten benennen. Ausgänge ebenso.
3. Rechtsklick auf jeden Input → **Type hint** setzen (`float`, `int`, `bool`, `Point3d`, `Plane`).
4. Slider an die Zahlen-Inputs hängen. Nicht angeschlossene Inputs sind `None` → dann gilt der Standardwert der Funktion.
   *Achtung:* Ein Input ohne Kabel ist `None`. Wenn du ihn also anlegst, aber nichts anschließt, bekommst du einen Fehler bei Rechnungen. Lass ungenutzte Inputs daher am besten weg, oder hänge immer einen Slider dran.
5. Code einfügen (unten), Ausgänge an **Custom Preview** + **Colour Swatch** hängen (wie im Abschnitt „Visualize“ der Datei).

---

### 1. Spheres and toruses
Inputs: `n` (int), `d` (float), `r` (float), `angle` (float) · Outputs: `spheres`, `rings`
```python
from cdf.lecture_02_examples import create_planets
spheres, rings = create_planets(count=n, spacing=d, sphere_radius=r, tilt_angle=angle)
```
Lernziel: `Plane.Rotate(Winkel, Achse)` kippt die Ringebene – Slider `angle` bewegen.

### 2. Box and spheres
Inputs: `hole`, `depth`, `n`, `spacing` · Outputs: `box`, `cutter`, `spheres`
```python
from cdf.lecture_02_examples import create_box_with_spheres
box, cutter, spheres = create_box_with_spheres(hole_size=hole, hole_depth=depth,
                                               sphere_count=n, sphere_spacing=spacing)
```
Lernziel: `Brep.CreateBooleanDifference` (Box A − Box B) und `Transform.Translation` entlang Z.

### 3. Chequered boxes
Inputs: `nx`, `ny`, `nz` (int), `size` (float), `invert` (bool, Boolean Toggle) · Output: `boxes`
```python
from cdf.lecture_02_examples import create_chequered_boxes
boxes = create_chequered_boxes(nx=nx, ny=ny, nz=nz, size=size, invert=bool(invert))
```
Lernziel: `if (i + j + k) % 2 == 0` innerhalb der drei verschachtelten `for`-Schleifen.

### 4. Point cloud
Inputs: `n` (int), `seed` (int), `max_s` (float) · Outputs: `points`, `boxes`, `scales`, `colors`
```python
from cdf.lecture_02_examples import create_point_cloud
points, boxes, scales, colors = create_point_cloud(count=n, seed=seed, max_scale=max_s)
```
Farbig anzeigen: `boxes` → *Custom Preview* (Geometry), `colors` → *Custom Preview* (Material).
Skalen beschriften: `points` + `scales` → *Text Tag 3D*.

### 5. Point traces
Inputs: `r` (float), `n` (int), `seed` (int) · Outputs: `hemi`, `pts`, `proj`, `traces`
```python
from cdf.lecture_02_examples import create_point_traces
hemi, pts, proj, traces = create_point_traces(radius=r, count=n, seed=seed)
```
Lernziele: `Brep.Split` (Halbkugel), `face.PointAt(u, v)`, `Intersection.ProjectPointsToBreps`.
Dass sich die Punkte oben am Pol häufen, ist richtig: gleichverteilte u, v-Werte liegen auf der Kugel nicht gleichmäßig.

### 6. Blend surface
Inputs: `size`, `r`, `h`, `dx` · Outputs: `solid`, `curve_1`, `curve_2`
```python
from cdf.lecture_02_examples import create_blend_solid
solid, curve_1, curve_2 = create_blend_solid(base_size=size, top_radius=r, height=h, top_offset_x=dx)
```

### 7. Mirrored cones
Inputs: `tilt`, `turn` (float), optional `plane` (Plane) · Outputs: `cone`, `mirrored`, `mirror_plane`
```python
from cdf.lecture_02_examples import create_mirrored_cones
cone, mirrored, mirror_plane = create_mirrored_cones(tilt_angle=tilt, turn_angle=turn)
```
Wenn du einen eigenen Spiegel ausprobieren willst: Input `plane` anlegen und `mirror_plane=plane` übergeben.

### 8. Pyramid parts
Inputs: `parts` (int), `gap` (float) · Outputs: `pieces`, `slabs`
```python
from cdf.lecture_02_examples import create_pyramid_parts
pieces, slabs = create_pyramid_parts(part_count=parts, gap=gap)
```

### 9. Sweep
Inputs: `r`, `pitch`, `turns`, `w`, `h` (float) · Outputs: `solid`, `rail`, `profile`
```python
from cdf.lecture_02_examples import create_spiral_sweep
solid, rail, profile = create_spiral_sweep(radius=r, pitch=pitch, turns=turns,
                                           profile_width=w, profile_height=h)
```

---

## Tipps

- Fehlermeldung „No module named cdf“ → Suchpfad (Schritt 2) fehlt.
- Änderungen in VS Code kommen nicht an → AutoReloader-Pfad prüfen oder den Baustein einmal neu berechnen (Rechtsklick → *Recompute*).
- Slider sinnvoll begrenzen (z. B. `n` 1–200), damit Rhino bei Booleans nicht hängt.
