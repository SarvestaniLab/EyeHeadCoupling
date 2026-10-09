#!/usr/bin/env python
"""
Fig5_cortex.py — Tree shrew V1 over-represents the central visual field.

Asks how much of primary visual cortex (V1) is devoted to the centre of the
visual field in tree shrew, squirrel monkey and mouse, and draws the
computed parts of Figure 5:
  • Flat-mounted left V1 with the Bosking et al. (2000) retinotopic grid and
             its extension to 120° azimuth
  • % of V1 devoted to the central 10° (squirrel monkey, tree shrew, mouse)
  • Over-representation ratio at 10°, 20°, 30° and the squirrel monkey (analytic) and mouse (measured) comparison values.

Remaining parts (3-D cortical renders, flat-mount curvature image, skull/binocular
field renders) are produced by other software and are not drawn here.

WHAT IS COMPUTED
  For each species, and for the central 10°, 20° and 30° of the visual field
  (eccentricity = angle away from the centre of gaze):
    pct_V1       % of V1's surface area that represents that central region
    uniform_pct  % it WOULD get if V1 gave every part of the visual field the
                 same amount of cortex
    ratio        pct_V1 / uniform_pct, the over-representation ratio. 1 means
                 no emphasis on the centre; 9 means nine times more cortex
                 than an even map would give.

HOW EACH SPECIES IS HANDLED
  Tree shrew — measured from a flat map (build_treeshrew, treeshrew_overrep)
    The input is a drawing (SVG) of flattened left V1 with the retinotopic
    grid on it: red lines of equal azimuth at -10°, -5°, 0°, +5°, +10° and
    blue lines of equal elevation from -60° to +60°. The script:
      1. reads the V1 outline, the grid lines and the 5 mm scale bar, and
         works out which line is which from their colour, thickness and
         position (text labels in the drawing are not used);
      2. covers V1 with a fine triangular mesh;
      3. gives every mesh point an azimuth and an elevation by interpolating
         smoothly between the drawn lines;
      4. extends azimuth past the last drawn line (+10°) to the far edge of
         V1, which is taken to be 120° (Kaas et al. 1980). Values in between
         are spaced so that the cortex per degree falls off as a power law
         of azimuth, whose two constants the script derives itself (see
         "HOW AZIMUTH BEYOND +10° IS CHOSEN" below). This part is an
         extrapolation, not a measurement, and is drawn dashed;
      5. adds up the cortical area of the mesh triangles that fall within
         10°, 20° and 30° of the centre.
  Squirrel monkey — calculated, not measured (squirrelmonkey)
    No map is used. Cortex per unit of visual field is assumed to fall with
    eccentricity E as 1/(E + e2)², and e2 is chosen so that the central 4°
    takes up 27% of V1, the value reported by Adams & Horton (2003).
  Mouse — measured from imaging maps (mouse)
    The inputs are the altitude and azimuth maps of the Zhuang et al. (2017)
    example dataset. V1 is outlined with those authors' visual-field-sign
    method, and the % of V1 pixels within 10°, 20° and 30° is counted.

HOW AZIMUTH BEYOND +10° IS CHOSEN  (fit_azimuth_law)
  The drawing stops at +10°, but V1 runs on to 120°, so 110° of azimuth has
  to be laid out across the cortex that is left. Measured along the
  horizontal meridian, the drawn 0-10° takes about 3.2 mm (0.32 mm per
  degree) and only about 2.4 mm remain for the other 110°. The layout is a
  law, cortex per degree M(az) ∝ ((az + e2)/e2)^-k, and its two constants
  are fitted to balance two things that cannot both be had:
    even spacing   the dashed contours (20, 30, 45, 60, 90, 120°) sit at
                   equal steps across the remaining cortex, so the periphery
                   stays legible instead of piling up at the border;
    continuity     cortex per degree just beyond +10° matches the drawn grid
                   just inside it, so there is no jump at the join.
  One number sets the balance: LAW_LAMBDA, the weight on continuity. At the
  chosen 1.0 the fit gives a plain power law (e2 → 0, k ≈ 1.02): cortex per
  degree still drops about 3-fold at the join, and 10-20° takes 28% of the
  remaining cortex. summary.json tabulates the other weights in LAW_SWEEP.

  What depends on this choice, and what does not:
    10°        nothing. Everything within 10° of the centre lies inside the
               drawn grid, so the 10° result is the same for any constants.
    20°, 30°   these do. Over the tabulated weights the tree shrew ratio at
               20° runs from about 5.9 to 7.0 (6.1 at the chosen weight) and
               at 30° from about 3.8 to 4.9 (4.1 at the chosen weight). The
               chosen weight sits toward the low, conservative end.

  LAW_OVERRIDE pins (e2, k) to the values behind the delivered figure, which
  were fitted on the first revision of the drawing. Set it to None to refit
  on whatever drawing is supplied; summary.json reports that refit either
  way, next to the values actually used.

ASSUMPTIONS WORTH KNOWING  (all set in the CONFIG block)
  • Tree shrew azimuth beyond +10° is extrapolated (step 4 above). Its
    constants are not measured from tree shrew data, which the drawing does
    not have past +10°; they come from the stated balance described above.
  • The squirrel monkey's visual field is ASSUMED to be a full hemifield, so
    its ratio is an upper bound, and its curve rests on one published number
    from two animals.
  • uniform_pct depends on how big each species' visual field is taken to be
    (FIELD): -10° to 120° azimuth by ±60° elevation for tree shrew (read off
    the map), a full hemifield for squirrel monkey (assumed), and whatever
    the mouse maps themselves cover.
  • Mouse coordinates are shifted so that the point where V1, LM and RL meet
    is (0°, 0°), following Zhuang et al.

INPUTS  (edit the CONFIG block; files live in Fig5_inputs/ next to this script)
  TS_SVG        the tree shrew flat-map SVG: V1 outline, Bosking grid, 5 mm scale bar
  MOUSE_TIFS    altitude/azimuth maps from Zhuang et al. 2017 example dataset

OUTPUTS  (written to Fig5_outputs/ next to this script)
  figure5.png / .svg                 left: the flat map (solid = drawn grid, dashed =
                                     extrapolated azimuth). Right: % of V1 within 10°, and
                                     the ratio at 10°, 20°, 30° (pale → solid bars).
  overrepresentation.csv             pct_V1, uniform_pct and ratio per species and eccentricity
  treeshrew_vertex_retinotopy.csv    every mesh point: position (mm), azimuth, elevation
  summary.json                       the same numbers plus intermediate values (V1 areas,
                                     fitted e2, mouse field extent and re-centring shift)
                                     and the azimuth law: the constants used, the refit on
                                     this drawing, the table over LAW_SWEEP, and the
                                     horizontal-meridian measurements it starts from;
                                     also printed when the script finishes

USAGE
  python Python/paper_figures/Fig5_cortex.py

Requires: numpy scipy pandas matplotlib shapely svgpathtools tifffile scikit-image (all in EyeHeadCoupling environment)
"""
import re, json, os, sys
import numpy as np, pandas as pd
import matplotlib as mpl, matplotlib.pyplot as plt
from matplotlib.tri import Triangulation
from matplotlib.lines import Line2D
from matplotlib.path import Path as MPath
from scipy.spatial import Delaunay, cKDTree
from scipy.sparse import coo_matrix, csr_matrix
from scipy.sparse.linalg import spsolve
from scipy.integrate import quad
from scipy.optimize import brentq
from scipy.interpolate import LinearNDInterpolator
from shapely.geometry import Polygon as SPoly, LineString, Point
from shapely.ops import nearest_points
from svgpathtools import parse_path

# ============================== GET THE INPUTs and set config =======================================
HERE   = os.path.dirname(os.path.abspath(__file__))   # paths resolve from the script, not the cwd
IN_DIR = os.path.join(HERE, 'Fig5_inputs')
CONFIG = dict(
    TS_SVG        = os.path.join(IN_DIR, 'treeshrew_flatmap.svg'),
    SCALE_BAR_MM  = 5.0,
    MOUSE_TIFS    = dict(alt=os.path.join(IN_DIR, 'zhuang2017_altitude_map.tif'),
                         azi=os.path.join(IN_DIR, 'zhuang2017_azimuth_map.tif')),
    MOUSE_UM_PER_PX = 12.9,                       # Zhuang et al. 2017, stated pixel size
    OUT_DIR       = os.path.join(HERE, 'Fig5_outputs'),
    # tree shrew azimuth extension
    AZ_RIM        = 120.0,                        # outermost azimuth printed in Kaas et al. 1980
    OUTER_LEVELS  = [20, 30, 45, 60, 90, 120],
    # Between the last drawn line (+10°) and the far border (AZ_RIM) no azimuth is drawn, so it
    # is spread out by a law: cortex per degree M(az) ∝ ((az+e2)/e2)^-k. Its two constants
    # (e2, k) are DERIVED by fit_azimuth_law() below — see its docstring. LAW_LAMBDA is the one
    # free choice: how much weight to put on magnification being continuous at the 10° join,
    # relative to the extrapolated contours being evenly spaced across the cortex. LAW_SWEEP
    # lists other weights to tabulate in summary.json, to show what that choice does.
    # LAW_OVERRIDE pins (e2, k) to the values used in the delivered figure (fitted at
    # LAW_LAMBDA = 1.0 on the first SVG revision and carried through the later revisions
    # unchanged); set it to None to refit on the SVG actually supplied.
    LAW_LAMBDA    = 1.0,
    LAW_SWEEP     = (0.0, 0.5, 1.0, 2.0, 4.0, 8.0, 20.0),
    LAW_OVERRIDE  = dict(e2=1e-6, k=1.0189),
    CORNER_CLIP_MM= 1.0,                          # numerical fix at the upper corner only
    MESH_H_MM     = 0.055,
    # field extents used as ratio denominators (az0, az1, el0, el1), degrees
    FIELD = dict(treeshrew=(-10, 120, -60, 60),   # measured from the map
                 squirrelmonkey=(0, 90, -90, 90), # ASSUMED full hemifield → ratio is an upper bound
                 mouse=None),                     # measured from the per-pixel maps below
    # squirrel monkey anchor: Adams & Horton 2003, central 4° = 27% of V1 (n = 2)
    SM_ANCHOR_DEG = 4.0, SM_ANCHOR_FRAC = 0.27,
    BANDS = (10, 20, 30),
)
D2R = np.pi/180
COL = {'Squirrel monkey': '#762A83', 'Tree shrew': '#B2182B', 'Mouse': '#2166AC'}
AZC, ELC = '#B2182B', '#2B9BD9'

# ============================ shared geometry ================================
def gc_ecc(az, el):
    """Eccentricity (deg): the angle between a visual-field direction, given as
    azimuth and elevation (deg), and the centre of gaze at (0, 0)."""
    return np.degrees(np.arccos(np.clip(np.cos(el*D2R)*np.cos(az*D2R), -1, 1)))

def rect_field_deg2(a0, a1, e0, e1):
    """Area (square degrees) of an azimuth × elevation rectangle on the sphere.
    Not used by main()."""
    return (a1-a0)*(np.sin(e1*D2R)-np.sin(e0*D2R))*(180/np.pi)

def uniform_frac(x, a0, a1, e0, e1, n=1400):
    """Fraction of a visual field that lies within x° of its centre.

    The field spans azimuth a0..a1 and elevation e0..e1 (deg). It is sampled on
    an n × n grid, each direction weighted by cos(elevation) so that equal
    patches of the visual field count equally. This is the share of V1 the
    central x° would get if cortex represented the field evenly: the
    denominator of the over-representation ratio."""
    A, E = np.meshgrid(np.linspace(a0, a1, n), np.linspace(e0, e1, n))
    w = np.cos(E*D2R)
    return float((w*(gc_ecc(A, E) <= x)).sum()/w.sum())

def cot_laplacian(V, F):
    """Cotangent Laplacian of a triangle mesh (V: vertex positions, F: triangles).

    The standard matrix for interpolating smoothly over a mesh. Holding some
    vertices at known values and solving with it (solve_dirichlet) gives the
    smoothest surface passing through those values."""
    n = len(V); I, J, W = [], [], []
    for a, b, c in ((0, 1, 2), (1, 2, 0), (2, 0, 1)):
        u = V[F[:, b]]-V[F[:, a]]; v = V[F[:, c]]-V[F[:, a]]
        cot = (u*v).sum(1)/np.maximum(np.abs(u[:, 0]*v[:, 1]-u[:, 1]*v[:, 0]), 1e-12)
        I += [F[:, b], F[:, c]]; J += [F[:, c], F[:, b]]; W += [cot, cot]
    L = coo_matrix((np.concatenate(W), (np.concatenate(I), np.concatenate(J))), shape=(n, n)).tocsr()
    return (csr_matrix((np.asarray(L.sum(1)).ravel(), (np.arange(n), np.arange(n)))) - L)

def solve_dirichlet(L, fixed_idx, fixed_val, n):
    """Fill in a value at every mesh vertex by smooth interpolation.

    Vertices fixed_idx are held at fixed_val (the points lying on a drawn grid
    line); the rest are solved for with the mesh Laplacian L. Returns an array
    of n values, one per vertex."""
    free = np.setdiff1d(np.arange(n), fixed_idx)
    x = np.zeros(n); x[fixed_idx] = fixed_val
    rhs = -L[free][:, fixed_idx] @ fixed_val
    x[free] = spsolve(L[free][:, free].tocsc(), rhs)
    return x

def tri_solid_angle_deg2(F, az, el):
    """Patch of visual field (square degrees) that each mesh triangle represents,
    from the azimuth and elevation at its three corners. Not used by main()."""
    a = az[F]*D2R; e = el[F]*D2R
    P = np.stack([np.cos(e)*np.cos(a), np.cos(e)*np.sin(a), np.sin(e)], -1)
    cr = np.cross(P[:, 1]-P[:, 0], P[:, 2]-P[:, 0])
    return 0.5*np.linalg.norm(cr, axis=1)*(180/np.pi)**2

# ============================ tree shrew =====================================
def hm_ladder(DRAWN_AZ, HM):
    """Where each drawn azimuth line crosses the horizontal meridian (HM).

    Returns (pos, s_far): pos maps each drawn azimuth (-10, -5, 0, 5, 10) to its
    distance along HM in mm, and s_far is the distance along HM of the end that
    lies at V1's far (peripheral) border. Together they are a ruler along HM:
    how many mm the drawn 0-10° takes, and how many mm are left for 10-120°."""
    hmL = LineString(HM)
    pos = {}
    for v, C in DRAWN_AZ.items():
        it = hmL.intersection(LineString(C))
        pt = it.centroid if not it.is_empty else nearest_points(hmL, LineString(C))[0]
        pos[v] = float(hmL.project(pt))
    s_far = 0.0 if abs(pos[0]-0.0) > abs(pos[0]-hmL.length) else hmL.length
    return pos, s_far

def fit_azimuth_law(DRAWN_AZ, HM, outer_levels, az_rim, lam, sweep=()):
    """Derive (e2, k) of the magnification law M(az) ∝ ((az+e2)/e2)^-k used outboard of 10°.

    WHY A LAW IS NEEDED. The drawing shows azimuth lines only out to +10°, but V1
    continues to its far border, taken as az_rim (120°). The 110° in between has to
    be laid out across the cortex that is left, and nothing in the drawing says how.
    This function chooses the layout from two requirements and reports the choice.

    THE PROBLEM. Measured along the horizontal meridian (see hm_ladder), the drawn
    grid gives `w10` mm to azimuth 0-10°, at a nearly constant M_drawn = (s10 - s5)/5
    mm per degree, and leaves `rem` mm before the far border for the remaining 110°.
    Two desirable properties conflict:
      (1) EVEN SPACING: the extrapolated contours (20, 30, 45, 60, 90, 120°) divide
          `rem` into equal cortical steps, so the periphery is legible rather than
          collapsing onto the border;
      (2) CONTINUITY: M just outside 10° matches M_drawn, so there is no step in
          magnification at the join.
    Forcing (2) alone makes the single 10-20° interval consume ~64% of `rem` (the drawn
    slope is far too shallow to continue into the periphery); forcing (1) alone gives
    a 6.3x step at the join.

    THE FIT. For a law f(a) = ((a+e2)/e2)^-k, the amplitude is fixed by the border:
        M0 = rem / ∫_{10}^{az_rim} f(a) da,   so the contour at a sits at w10 + M0 ∫_{10}^{a} f.
    (e2, k) are found by least squares on the residual vector
        [ step_i / mean(step) - 1  for the six intervals ]  ++  [ lam * log(M0 f(10) / M_drawn) ]
    i.e. criterion (1) as six residuals and criterion (2) as one residual weighted by `lam`.
    `lam` is the single free choice. In this project a sweep over lam was tabulated and
    lam = 1.0 chosen as the balance point: the 10-20° interval falls from 64% to 28% of
    `rem` and the step at the join is 3.1x rather than 6.3x. At lam = 1.0 the fit drives
    e2 -> 0 (the law becomes a pure power law in azimuth, i.e. contour spacing
    ~logarithmic in cortical distance) with k = 1.0189 on the first SVG revision.

    WHAT THIS IS NOT. (e2, k) are not measured from tree shrew data beyond 10°: there is
    none in the drawing. They are the outcome of a stated compromise. The region within
    10° of the centre lies entirely inside the drawn grid, so the 10° result does not
    depend on them at all; the 20° and 30° results do.

    Returns (best, table, geometry):
      best      the fit at `lam`: e2, k, step_at_join (M_drawn divided by the law's M at
                10°; 1 = no step), spacing_cv (unevenness of the six cortical steps;
                0 = perfectly even), frac_10_20 (share of `rem` taken by 10-20°)
      table     the same quantities for every weight in `sweep`
      geometry  w10_mm, rem_mm and M_drawn_mm_per_deg measured along HM
    """
    from scipy.optimize import least_squares
    pos, s_far = hm_ladder(DRAWN_AZ, HM)
    w10 = abs(pos[10]-pos[0]); M_drawn = abs(pos[10]-pos[5])/5.0
    rem = abs(s_far-pos[10])
    def widths(e2, k):
        f = lambda a: ((a+e2)/e2)**(-k)
        M0 = rem/quad(f, 10, az_rim, limit=300)[0]
        ws = np.array([M0*quad(f, 10, a, limit=300)[0] for a in outer_levels])
        return M0, ws, f
    def solve(l):
        def resid(p):
            e2, k = np.exp(p); M0, ws, f = widths(e2, k)
            sg = np.diff(np.r_[0.0, ws])
            return np.r_[sg/sg.mean()-1.0, l*np.log(max(M0*f(10), 1e-12)/M_drawn)]
        p = least_squares(resid, np.log([5.0, 1.2]), bounds=(np.log([1e-6, 0.05]), np.log([1e3, 10])),
                          xtol=1e-13).x
        e2, k = np.exp(p); M0, ws, f = widths(e2, k); sg = np.diff(np.r_[0.0, ws])
        return dict(lam=l, e2=e2, k=k, step_at_join=M_drawn/(M0*f(10)), spacing_cv=sg.std()/sg.mean(),
                    frac_10_20=sg[0]/rem)
    table = [solve(l) for l in sweep] if sweep else []
    best = solve(lam)
    return best, table, dict(w10_mm=w10, rem_mm=rem, M_drawn_mm_per_deg=M_drawn)

def parse_svg(path):
    """Read the flat-map drawing.

    Returns (paths, bar):
      paths  one dict per line in the SVG: 'pts' (900 points sampled along it,
             in SVG units), plus its 'stroke' colour and 'width' looked up in
             the SVG's style sheet. Colour and width are how build_treeshrew
             tells the outline, azimuth lines and elevation lines apart.
      bar    length of the scale bar in SVG units (the first rectangle that
             has no style class)."""
    raw = open(path, encoding='utf8', errors='replace').read()
    css = re.search(r'<style[^>]*>(.*?)</style>', raw, re.S).group(1)
    style = {}
    for m in re.finditer(r'([^{}]*)\{([^}]*)\}', css):
        for cls in re.findall(r'\.([\w-]+)', m.group(1)):
            style.setdefault(cls, {}).update(dict(kv.split(':', 1) for kv in
                [s.strip() for s in m.group(2).split(';') if ':' in s]))
    paths = []
    for m in re.finditer(r'<path([^>]*?)/?>', raw):
        at = m.group(1); d = re.search(r'\bd="([^"]*)"', at, re.S)
        if not d: continue
        cls = re.search(r'class="([^"]*)"', at)
        st = style.get(cls.group(1), {}) if cls else {}
        P = parse_path(d.group(1))
        pts = np.array([[P.point(t).real, P.point(t).imag] for t in np.linspace(0, 1, 900)])
        paths.append(dict(pts=pts, stroke=st.get('stroke', '').strip().lower(),
                          width=float(re.sub('[^0-9.]', '', st.get('stroke-width', '0')) or 0)))
    bars = [float(re.search(r'width="([-\d.]+)"', m.group(1)).group(1))
            for m in re.finditer(r'<rect([^>]*?)/?>', raw) if 'class=' not in m.group(1)]
    return paths, bars[0]

def build_treeshrew(cfg):
    """Turn the flat-map drawing into an azimuth and an elevation for every
    point of tree shrew V1.

    Steps, in the order they appear below:
      1. Read the SVG and convert to millimetres using the scale bar (y is
         flipped so up is up, and the outline's corner is moved to 0, 0).
      2. Sort the lines by colour and thickness. The V1 outline is the stroked
         path enclosing the largest area. Red = azimuth: the bold one is the
         vertical meridian (0°) and the thin ones are ±5° and ±10°, told apart
         by how far they lie from the vertical meridian. The +5° and +10° lines
         are a single joined path in the drawing, so it is split in two first.
         Blue = elevation: the bold one is the horizontal meridian (0°); all
         nine are numbered 60, 30, 20, 10, 0, -10, -20, -30, -60 by the order
         in which they cross the vertical meridian.
      3. Cover V1 with a triangular mesh (points every MESH_H_MM) and work out
         each triangle's area in mm².
      4. Find V1's far (peripheral) border: the outline is cut at its two ends
         along its long axis, and the half lying farther from the vertical
         meridian is the far border.
      5. Azimuth: hold each drawn azimuth line at its value and the far border
         at AZ_RIM (120°), then interpolate smoothly everywhere else. Between
         the +10° line and the far border the result is re-spaced so that
         cortex per degree declines as a power law. Its two constants come
         from fit_azimuth_law (or are pinned by LAW_OVERRIDE).
      6. Elevation: hold each drawn elevation line at its value and interpolate
         smoothly everywhere else.
      7. Check that the interpolated azimuth reproduces every drawn azimuth
         line to within 0.5°; the script stops if it does not.
      8. Trace the extrapolated azimuth lines (OUTER_LEVELS) for the figure,
         trimming them within CORNER_CLIP_MM of V1's upper corner (a numerical
         fix at that corner only; it affects the drawing, not the numbers).

    Returns a dict. The entries used elsewhere: V (mesh points, mm), F
    (triangles), Ao (triangle areas, mm²), AZ and EL (azimuth and elevation at
    each mesh point, deg), OUT (V1 outline, mm), A_V1 (V1 area, mm²), DRAWN_AZ
    and DRAWN_EL (the drawn lines, keyed by their value in degrees), NEW (the
    extrapolated azimuth lines, keyed by value), and law_used / law_fit /
    law_sweep / law_geom (the azimuth law's constants and how they were
    derived; see fit_azimuth_law)."""
    paths, bar = parse_svg(cfg['TS_SVG'])
    MM = cfg['SCALE_BAR_MM']/bar
    is_red  = lambda p: p['stroke'] in ('#ed1c24', 'red')
    is_blue = lambda p: p['stroke'] in ('#28aae2',)
    # outline = closed path of largest area among non-grid paths
    # (the file also carries a strokeless clipping copy of the outline; prefer the stroked one)
    parea = lambda p: SPoly(p['pts']).buffer(0).area
    cand = [p for p in paths if p['width'] > 0 and not is_blue(p) and not (is_red(p) and p['width'] < 0.6)]
    outline_p = max(cand, key=parea); outline = outline_p['pts']; A_out_units = parea(outline_p)
    def tomm(P):
        Q = P*MM; Q = np.c_[Q[:, 0], -Q[:, 1]]
        return Q - np.array([(outline*MM)[:, 0].min(), (-(outline*MM)[:, 1]).min()])
    OUT = tomm(outline); A_V1 = SPoly(OUT).area
    VM = tomm([p for p in paths if is_red(p)  and p['width'] >= 1.5][0]['pts'])
    HM = tomm([p for p in paths if is_blue(p) and p['width'] >= 1.5][0]['pts'])
    thin_red  = [tomm(p['pts']) for p in paths if is_red(p) and 0 < p['width'] < 1.0
                 and parea(p) < 0.5*A_out_units]                     # exclude the outline itself
    thin_blue = [tomm(p['pts']) for p in paths if is_blue(p) and 0 < p['width'] < 1.0]
    # compound +5/+10 path: the one with the largest spatial extent; split at max separation
    ext = [np.ptp(c, axis=0).sum() for c in thin_red]
    comp = thin_red.pop(int(np.argmax(ext)))
    far = int(np.argmax(np.linalg.norm(comp-comp[0], axis=1)))
    halves = [comp[:far+1], comp[far:]]
    vmL = LineString(VM); dist = lambda C: np.median([vmL.distance(Point(q)) for q in C[::30]])
    halves.sort(key=dist); thin_red.sort(key=dist)
    DRAWN_AZ = {0: VM, 5: halves[0], 10: halves[1], -5: thin_red[0], -10: thin_red[1]}
    # elevation ladder recovered from VM-crossing order (labels NOT used)
    rows = []
    for C in thin_blue + [HM]:
        l = LineString(C); it = vmL.intersection(l)
        pt = it.centroid if not it.is_empty else nearest_points(vmL, l)[0]
        rows.append((C, vmL.project(pt)))
    rows.sort(key=lambda r: r[1])
    DRAWN_EL = {ev: C for (C, _), ev in zip(rows, [60, 30, 20, 10, 0, -10, -20, -30, -60])}
    assert np.allclose(DRAWN_EL[0][:5], HM[:5]), 'bold blue path did not land on elevation 0'
    # mesh
    pth = MPath(OUT); h = cfg['MESH_H_MM']
    gx, gy = np.meshgrid(np.arange(OUT[:, 0].min(), OUT[:, 0].max(), h),
                         np.arange(OUT[:, 1].min(), OUT[:, 1].max(), h))
    q = np.c_[gx.ravel(), gy.ravel()]
    V = np.vstack([OUT[::2], q[pth.contains_points(q)]])
    tri = Delaunay(V); F = tri.simplices[pth.contains_points(V[tri.simplices].mean(1))]
    Ao = 0.5*np.abs((V[F[:, 1]]-V[F[:, 0]])[:, 0]*(V[F[:, 2]]-V[F[:, 0]])[:, 1]
                    -(V[F[:, 1]]-V[F[:, 0]])[:, 1]*(V[F[:, 2]]-V[F[:, 0]])[:, 0])
    sub = np.unique(F); remap = {g: i for i, g in enumerate(sub)}
    Ls = cot_laplacian(V, F)[sub][:, sub]
    # far (peripheral) border = outline arc farther from VM, between the PCA-extreme corners
    c0 = OUT.mean(0); ax1 = np.linalg.svd(OUT-c0, full_matrices=False)[2][0]
    t = (OUT-c0) @ ax1; i0, i1 = sorted([int(np.argmin(t)), int(np.argmax(t))])
    CA, CB = OUT[int(np.argmax(t))], OUT[int(np.argmin(t))]
    arc1 = np.arange(i0, i1+1); arc2 = np.r_[np.arange(i1, len(OUT)), np.arange(0, i0+1)]
    d = lambda arc: np.median([np.min(np.linalg.norm(OUT[arc]-qq, axis=1)) for qq in VM[::40]])
    far_arc = arc2 if d(arc1) < d(arc2) else arc1
    tree = cKDTree(V)
    def pin(curves_vals, extra_idx=None, extra_val=None):
        idx = np.concatenate([tree.query(C)[1] for C, _ in curves_vals])
        val = np.concatenate([np.full(len(C), float(v)) for C, v in curves_vals])
        if extra_idx is not None:
            idx = np.concatenate([idx, extra_idx]); val = np.concatenate([val, np.full(len(extra_idx), extra_val)])
        u, ui = np.unique(idx, return_index=True)
        fi = np.array([remap[i] for i in idx[ui] if i in remap])
        fv = np.array([v for i, v in zip(idx[ui], val[ui]) if i in remap])
        x = np.full(len(V), np.nan); x[sub] = solve_dirichlet(Ls, fi, fv, len(sub))
        x[np.isnan(x)] = np.nanmean(x); return x
    far_idx = np.unique(tree.query(OUT[far_arc])[1])
    S = pin([(C, v) for v, C in DRAWN_AZ.items()], far_idx, cfg['AZ_RIM'])
    # reparameterise 10..120 through the declining law so spacing follows magnification.
    # (e2, k) are derived here — see fit_azimuth_law() — unless LAW_OVERRIDE pins them.
    law, law_sweep, law_geom = fit_azimuth_law(DRAWN_AZ, HM, cfg['OUTER_LEVELS'], cfg['AZ_RIM'],
                                               cfg['LAW_LAMBDA'], cfg['LAW_SWEEP'])
    if cfg.get('LAW_OVERRIDE'):
        e2, k = cfg['LAW_OVERRIDE']['e2'], cfg['LAW_OVERRIDE']['k']
    else:
        e2, k = law['e2'], law['k']
    f = lambda a: ((a+e2)/e2)**(-k); grid = np.linspace(10, cfg['AZ_RIM'], 400)
    cum = np.array([quad(f, 10, a, limit=200)[0] for a in grid]); cum /= cum[-1]
    AZ = np.where(S <= 10, S, np.interp(np.clip((S-10)/(cfg['AZ_RIM']-10), 0, 1), cum, grid))
    EL = pin([(C, v) for v, C in DRAWN_EL.items()])
    # recovery check
    I = LinearNDInterpolator(V, AZ)
    rec = {v: float(np.nanmedian(I(C[:, 0], C[:, 1]))) for v, C in DRAWN_AZ.items()}
    assert all(abs(rec[v]-v) < 0.5 for v in rec), rec
    # outer contours, clipped near the upper corner only
    T = Triangulation(V[:, 0], V[:, 1], F)
    figt, axt = plt.subplots(); cs = axt.tricontour(T, AZ, levels=cfg['OUTER_LEVELS']); plt.close(figt)
    top = CA if CA[1] > CB[1] else CB
    NEW = {}
    for li, l in enumerate(cfg['OUTER_LEVELS']):
        P_ = cs.get_paths()[li]; pv, codes = P_.vertices, P_.codes
        starts = np.nonzero(codes == MPath.MOVETO)[0] if codes is not None else np.array([0])
        segs = [pv[s:e] for s, e in zip(starts, list(starts[1:]) + [len(pv)])]
        seg = max([s for s in segs if len(s) > 3], key=len)
        keep = np.linalg.norm(seg-top, axis=1) > cfg['CORNER_CLIP_MM']
        idx = np.nonzero(keep)[0]; br = np.nonzero(np.diff(idx) > 1)[0]
        pieces = np.split(idx, br+1)
        NEW[l] = seg[max(pieces, key=len)]
    return dict(V=V, F=F, Ao=Ao, AZ=AZ, EL=EL, OUT=OUT, A_V1=A_V1, DRAWN_AZ=DRAWN_AZ,
                DRAWN_EL=DRAWN_EL, NEW=NEW, T=T, CA=CA, CB=CB, MM=MM,
                law_used=dict(e2=e2, k=k), law_fit=law, law_sweep=law_sweep, law_geom=law_geom)

def treeshrew_overrep(ts, cfg):
    """Tree shrew results table: one row per eccentricity in BANDS.

    Each mesh triangle gets an eccentricity (the average of its three corners).
    pct_V1 is the area of the triangles within the band as a % of all of V1;
    cortex_mm2 is that area in mm². uniform_pct and ratio are as described at
    the top of this file."""
    F, Ao, AZ, EL = ts['F'], ts['Ao'], ts['AZ'], ts['EL']
    ecc_t = gc_ecc(AZ, EL)[F].mean(1)
    a0, a1, e0, e1 = cfg['FIELD']['treeshrew']
    rows = []
    for b in cfg['BANDS']:
        pv = 100*Ao[ecc_t <= b].sum()/Ao.sum(); uf = 100*uniform_frac(b, a0, a1, e0, e1)
        rows.append(dict(band=b, pct_V1=pv, uniform_pct=uf, ratio=pv/uf, cortex_mm2=Ao[ecc_t <= b].sum()))
    return pd.DataFrame(rows)

# ============================ squirrel monkey ================================
def squirrelmonkey(cfg):
    """Squirrel monkey results table, calculated from a formula rather than a map.

    Cortex per unit of visual field is assumed to fall with eccentricity E as
    M(E) ∝ 1/(E+e2)^2 over the assumed field (FIELD). e2 is solved so that the
    central SM_ANCHOR_DEG (4°) takes SM_ANCHOR_FRAC (27%) of V1, the single
    published anchor (Adams & Horton 2003). With e2 known, the share of V1
    within each band follows directly.

    Returns (table, e2): one row per eccentricity in BANDS, and the fitted e2
    in degrees."""
    a0, a1, e0, e1 = cfg['FIELD']['squirrelmonkey']
    A, E = np.meshgrid(np.linspace(a0, a1, 900), np.linspace(e0, e1, 900))
    dA = np.cos(E*D2R); ecc = gc_ecc(A, E)
    frac = lambda x, e2: ((dA/(ecc+e2)**2)[ecc <= x]).sum()/(dA/(ecc+e2)**2).sum()
    e2 = brentq(lambda e: frac(cfg['SM_ANCHOR_DEG'], e)-cfg['SM_ANCHOR_FRAC'], 0.01, 30)
    rows = []
    for b in cfg['BANDS']:
        pv = 100*frac(b, e2); uf = 100*uniform_frac(b, a0, a1, e0, e1)
        rows.append(dict(band=b, pct_V1=pv, uniform_pct=uf, ratio=pv/uf))
    return pd.DataFrame(rows), e2

# ============================ mouse ==========================================
def mouse(cfg):
    """Mouse results table, measured from the Zhuang et al. 2017 altitude/azimuth maps.

    Field-sign segmentation of V1, using the authors' own notebook procedure and
    parameters (phaseSigma 0.5, signSigma 8, signThr 0.4, open/close 3, dilation 15,
    smallPatch 100), then per-pixel eccentricity inside V1.

    In plain terms:
      1. Each imaging pixel has an altitude and an azimuth. From how those two
         change across the cortex, compute the "field sign": whether the map is
         mirrored (+) or not (-) at that pixel. Neighbouring visual areas have
         opposite signs, so thresholding the sign splits cortex into patches.
      2. V1 is the patch that covers the largest part of the visual field.
      3. Shift altitude and azimuth so that the point where V1 meets its two
         lowest-azimuth neighbours (LM and RL) is (0°, 0°). This corrects for
         where the monitor happened to sit.
      4. Compute each V1 pixel's eccentricity and count the % within each band.
         Pixels are all the same size, so a % of pixels is a % of area.

    Returns (table, V1 area in mm², field extent as (az0, az1, el0, el1) in
    degrees, the (altitude, azimuth) shift applied in step 3)."""
    import tifffile, scipy.ndimage as ni
    from skimage.morphology import skeletonize
    alt = tifffile.imread(cfg['MOUSE_TIFS']['alt']).astype(float)
    azi = tifffile.imread(cfg['MOUSE_TIFS']['azi']).astype(float)
    def sign_map(a, z):
        g1 = np.gradient(a); g2 = np.gradient(z)
        return np.sin(np.angle(np.exp(1j*np.arctan2(g1[1], g1[0]))*np.exp(-1j*np.arctan2(g2[1], g2[0]))))
    def separate(raw, dilationIter=15):
        total = ni.binary_dilation(raw, iterations=dilationIter).astype(int)
        border = skeletonize((total-raw).astype(bool)).astype(int)
        newP = (-(border-1))*total
        lab, n = ni.label(newP); out = np.zeros_like(newP)
        for i in range(1, n+1):
            cp = lab == i
            if (cp & (raw > 0)).sum() > 0: out[cp] = 1
        return out
    altf = ni.gaussian_filter(alt, 0.5); azif = ni.gaussian_filter(azi, 0.5)
    smf = ni.gaussian_filter(sign_map(altf, azif), 8.0)
    pm = ((smf >= 0.4) | (smf <= -0.4)).astype(int)
    pm = ni.binary_opening(pm, iterations=3).astype(int)
    lab, n = ni.label(pm); pm2 = np.zeros_like(pm)
    for i in range(1, n+1): pm2 |= ni.binary_closing(lab == i, iterations=3).astype(int)
    lab, n = ni.label(separate(pm2))
    patches = [dict(mask=lab == i, sign=int(np.sign(smf[lab == i].sum()))) for i in range(1, n+1)
               if (lab == i).sum() >= 100]
    # V1 = the patch with the greatest visual-field coverage (authors' getVisualSpace)
    def coverage(mask):
        a = altf[mask]; z = azif[mask]; vs = np.zeros((200, 280), int)
        ok = (a >= -40) & (a < 60) & (z >= -20) & (z < 120)
        vs[((a[ok]+40)//0.5).astype(int), ((z[ok]+20)//0.5).astype(int)] = 1
        return ni.binary_closing(vs, iterations=15).sum()*0.25
    v1 = max(patches, key=lambda p: coverage(p['mask']))['mask']
    mmpp = cfg['MOUSE_UM_PER_PX']/1000
    A_V1 = v1.sum()*mmpp**2
    # monitor-position correction, per Zhuang et al.: define the V1/LM/RL triple junction as
    # (0° altitude, 0° azimuth). Junction = pixel minimizing summed distance to V1 and to its two
    # lowest-azimuth neighbouring patches; offsets = mean map values within 8 px of it inside V1.
    others = [p['mask'] for p in patches if not np.array_equal(p['mask'], v1)]
    nbr = ni.binary_dilation(v1, iterations=20)
    others = [m for m in others if (m & nbr).any()]
    others.sort(key=lambda m: np.nanmedian(azif[m]))
    dsum = sum(ni.distance_transform_edt(~m) for m in [v1] + others[:2])
    jy, jx = np.unravel_index(np.argmin(dsum), dsum.shape)
    yy, xx = np.mgrid[0:v1.shape[0], 0:v1.shape[1]]
    near = ((yy-jy)**2+(xx-jx)**2 <= 8**2) & v1
    off_alt = float(altf[near].mean()); off_azi = float(azif[near].mean())
    a = alt[v1]-off_alt; z = azi[v1]-off_azi
    extent = (float(z.min()), float(z.max()), float(a.min()), float(a.max()))
    ecc = gc_ecc(z, a)
    rows = []
    for b in cfg['BANDS']:
        pv = 100*(ecc <= b).mean(); uf = 100*uniform_frac(b, *extent)
        rows.append(dict(band=b, pct_V1=pv, uniform_pct=uf, ratio=pv/uf))
    return pd.DataFrame(rows), A_V1, extent, (off_alt, off_azi)

# ============================ figure =========================================
def draw_flatmap(ax, ts, cfg):
    """Draw the tree shrew flat map: V1 outline (black), elevation lines (blue),
    azimuth lines (red). Bold lines are the horizontal and vertical meridians.
    Solid red lines are the drawn grid; dashed red lines are the extrapolated
    azimuths, labelled with their value. A 2 mm scale bar sits bottom-left."""
    OUT, DRAWN_AZ, DRAWN_EL, NEW = ts['OUT'], ts['DRAWN_AZ'], ts['DRAWN_EL'], ts['NEW']
    ax.plot(OUT[:, 0], OUT[:, 1], color='0.12', lw=1.9, zorder=6)
    for ev, C in DRAWN_EL.items(): ax.plot(C[:, 0], C[:, 1], color=ELC, lw=2.4 if ev == 0 else 0.95, zorder=4)
    for av, C in DRAWN_AZ.items(): ax.plot(C[:, 0], C[:, 1], color=AZC, lw=2.4 if av == 0 else 1.0, zorder=5)
    for l, v in NEW.items(): ax.plot(v[:, 0], v[:, 1], color=AZC, lw=1.0, ls=(0, (5, 2)), zorder=3)
    for l, frac in zip(cfg['OUTER_LEVELS'], np.linspace(0.42, 0.62, len(NEW))):
        v = NEW[l]; qq = v[int(frac*len(v))]
        ax.text(qq[0], qq[1], f'{l}°', fontsize=6.2, color=AZC, ha='center', va='center',
                bbox=dict(fc='w', ec='none', alpha=.85, pad=0.4), zorder=8)
    for av in (-10, 5, 10):
        qq = DRAWN_AZ[av][len(DRAWN_AZ[av])//2]
        ax.text(qq[0], qq[1], f'{av}°', fontsize=6.2, color=AZC, ha='center', va='center',
                bbox=dict(fc='w', ec='none', alpha=.85, pad=0.4), zorder=8)
    ax.set_aspect('equal'); ax.axis('off')
    x0 = OUT[:, 0].min()-0.15; y0 = OUT[:, 1].min()-0.6
    ax.plot([x0, x0+2], [y0, y0], 'k-', lw=2.6, clip_on=False)
    ax.text(x0+1, y0-0.3, '2 mm', ha='center', va='top', fontsize=7)

def draw_bars(axD, axE, res, cfg):
    """Draw the two bar plots from the per-species results tables in res.

    axD: % of V1 within 10° eccentricity, one bar per species.
    axE: over-representation ratio on a log axis, three bars per species for
         10°, 20° and 30° (pale to solid)."""
    order = ['Squirrel monkey', 'Tree shrew', 'Mouse']; xx = np.arange(3)
    pv = [res[s].loc[res[s].band == 10, 'pct_V1'].iloc[0] for s in order]
    axD.bar(xx, pv, 0.58, color=[COL[s] for s in order])
    for i, v in enumerate(pv): axD.text(i, v+1.2, f'{v:.1f}%', ha='center', fontsize=7)
    axD.set_xticks(xx); axD.set_xticklabels([s.replace(' ', '\n') for s in order], fontsize=7)
    axD.set_ylabel('% of V1 within 10° eccentricity'); axD.set_ylim(0, 55)
    w = 0.25
    for i, b in enumerate(cfg['BANDS']):
        axE.bar(xx+(i-1)*w, [res[s].loc[res[s].band == b, 'ratio'].iloc[0] for s in order], w,
                color=[COL[s] for s in order], alpha=[0.42, 0.70, 1.0][i], edgecolor='w', lw=0.4)
    axE.set_xticks(xx); axE.set_xticklabels([s.replace(' ', '\n') for s in order], fontsize=7)
    axE.set_yscale('log'); axE.set_ylim(0.9, 60); axE.set_ylabel('over-representation ratio')

def main(cfg=CONFIG):
    """Run the whole analysis and write every output to OUT_DIR.

    Computes the three species' tables, saves the two CSVs, draws and saves the
    figure, and writes summary.json. If the mouse TIFFs are missing, the mouse
    is skipped and the bar plots are left out (they need all three species).
    Returns the summary as a dict."""
    os.makedirs(cfg['OUT_DIR'], exist_ok=True)
    ts = build_treeshrew(cfg); ts_tab = treeshrew_overrep(ts, cfg)
    sm_tab, e2 = squirrelmonkey(cfg)
    try:
        ms_tab, ms_area, ms_extent, ms_off = mouse(cfg)
    except FileNotFoundError:
        print('mouse TIFFs not found — mouse panel skipped'); ms_tab = None
    res = {'Tree shrew': ts_tab, 'Squirrel monkey': sm_tab}
    if ms_tab is not None: res['Mouse'] = ms_tab
    # tables
    out = []
    for s, tab in res.items():
        t = tab.copy(); t.insert(0, 'species', s); out.append(t)
    pd.concat(out).to_csv(f"{cfg['OUT_DIR']}/overrepresentation.csv", index=False)
    pd.DataFrame(dict(vertex=np.arange(len(ts['V'])), x_mm=ts['V'][:, 0], y_mm=ts['V'][:, 1],
                      azimuth_deg=ts['AZ'], elevation_deg=ts['EL'])).to_csv(
                      f"{cfg['OUT_DIR']}/treeshrew_vertex_retinotopy.csv", index=False)
    # figure
    fig = plt.figure(figsize=(9.9, 5.6))
    gs = fig.add_gridspec(2, 3, width_ratios=[1.9, 1.1, 1.1], height_ratios=[1, 1], wspace=0.35, hspace=0.35)
    draw_flatmap(fig.add_subplot(gs[:, 0]), ts, cfg)
    if ms_tab is not None: draw_bars(fig.add_subplot(gs[0, 1]), fig.add_subplot(gs[0, 2]), res, cfg)
    labels = [a.yaxis.label for a in fig.axes]   # tight bbox otherwise crops labels taller than their axes
    fig.savefig(f"{cfg['OUT_DIR']}/figure5.png", dpi=400, bbox_inches='tight', bbox_extra_artists=labels)
    fig.savefig(f"{cfg['OUT_DIR']}/figure5.svg", bbox_inches='tight', bbox_extra_artists=labels)
    summary = dict(treeshrew_V1_mm2=ts['A_V1'], treeshrew=ts_tab.round(3).to_dict('records'),
                   azimuth_law_used=ts['law_used'], azimuth_law_fit_on_this_svg=ts['law_fit'],
                   azimuth_law_lambda_sweep=ts['law_sweep'], azimuth_law_hm_geometry=ts['law_geom'],
                   squirrelmonkey_e2_deg=e2, squirrelmonkey=sm_tab.round(3).to_dict('records'))
    if ms_tab is not None:
        summary.update(mouse_V1_mm2=ms_area, mouse_extent_az0_az1_el0_el1=ms_extent,
                       mouse_frame_offset_alt_az_deg=ms_off,
                       mouse=ms_tab.round(3).to_dict('records'))
    json.dump(summary, open(f"{cfg['OUT_DIR']}/summary.json", 'w'), indent=1)
    return summary

if __name__ == '__main__':
    print(json.dumps(main(), indent=1))
