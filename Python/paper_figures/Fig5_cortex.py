#!/usr/bin/env python
"""
Fig5_cortex.py — Tree shrew V1 over-represents the central visual field.

Asks how much of primary visual cortex (V1) is devoted to the centre of the
visual field in tree shrew, squirrel monkey and mouse, and draws the
computed parts of Figure 5:
  • Widefield imaging maps of elevation and azimuth across V1 of both
             hemispheres, in degrees, with contour lines at the flat map's
             grid values
  • Flat-mounted left V1 with the Bosking et al. (2000) retinotopic grid and
             its extension to 120° azimuth
  • % of V1 devoted to the central 10° (squirrel monkey, tree shrew, mouse)
  • Over-representation ratio at 10°, 20°, 30°, with squirrel monkey and mouse
             values from published measurements for comparison

Remaining parts (stimulus and imaging schematics, 3-D cortical renders, flat-mount
curvature image, skull/binocular field renders) are produced by other software and
are not drawn here.

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
  Squirrel monkey — published area measurements (squirrelmonkey)
    Adams & Horton (2003) built a retinotopic map of V1 from four hemispheres
    of two animals and measured, on their mean map, the area of cortex
    between rings of equal eccentricity at 1°, 2°, 4°, 8°, 16°, 24°, 32°, 50°
    and 72° (their Table 1). Those nine areas are typed into the CONFIG
    block. Adding them up from the centre gives the share of V1 within each
    ring (27% within 4° and 48% within 8°, as the paper states); the shares
    within 10°, 20° and 30° are read off a smooth curve through those
    points. No model of magnification is assumed.
  Mouse — measured from imaging maps (mouse)
    The inputs are the altitude and azimuth maps of the Zhuang et al. (2017)
    example dataset. V1 is outlined with those authors' visual-field-sign
    method, and the % of V1 pixels within 10°, 20° and 30° is counted. Where
    0° lies in these maps depends on where the mouse and monitor sat, so, as
    in the paper, the maps are first shifted to put the point where V1, LM
    and RL meet at 0° altitude, 0° azimuth. The script finds LM and RL by the
    properties the paper gives them, checks the junction against a landmark
    placed by eye and against the paper's numbers, and repeats the count with
    the origin moved by up to 5° (mouse_origin_check.png, summary.json).

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

HOW THE WIDEFIELD MAPS GET THEIR DEGREES  (fit_widefield)
  The imaging gives each pixel a phase: the point in the bar's sweep, from 0
  to 1, at which that bit of cortex responded. Turning phase into degrees
  takes two numbers per sweep: how many degrees one sweep covered, and which
  phase is 0° (straight ahead, at eye level). The first is known from the
  stimulus: the bar travelled 50° per sweep in azimuth and 60° in elevation
  (WF_SWEEP_DEG). The second is not, because it depends on where the eyes
  were pointing. It is found by laying the window on the flat map, which
  does carry degrees:
    1. the image-right half of the window is mirrored across the midline, so
       that both hemispheres can be laid on the one left-hemisphere flat map;
    2. a placement of the window on the flat map is tried: a rotation and a
       position of the window centre (mm per pixel follows from the window
       diameter, WF_WINDOW_MM = 8.3 mm, the visible part of the 10 mm
       chamber);
    3. for that placement, each pixel's phase is compared with the azimuth
       and elevation the flat map has where the pixel lands. One straight
       line per sweep, degrees = slope × phase + zero, the same two lines
       for both hemispheres, turns one into the other;
    4. the placement is adjusted until those two lines explain as much of
       the two phase maps as they can.
  This is done twice. With the two slopes held at those known values, only
  the placement and the two zeros are free. That fit gives the degrees
  drawn on the widefield maps (WF_DEGREES_FROM = 'screen'), and with it the
  flat map explains 95% of the azimuth map and 93% of the elevation map.
  With the slopes left free as well, the fit says what the sweep extents
  would have to be for this animal's V1 to be laid out exactly like the flat
  map, which makes it a test of the flat map (below). The contours on the
  widefield maps are drawn at the flat map's grid values (azimuth 0, ±5,
  ±10°; elevation 0, -10, -20°) and the colour bars span what the window
  holds. widefield_registration_check.png lays those contours on the flat
  map to show how near they fall to its grid, and where the imaged cortex
  lies within V1.

  What the free-slope fit shows:
    0° azimuth    The vertical meridian sits at the same phase (0.436 of a
                  sweep) whatever window size is assumed, and in both fits.
    window size   cannot be fitted. A bigger window covers more of the flat
                  map, so more degrees, and the fitted degree scale just
                  stretches to suit; the maps are explained equally well at
                  every size tried (6 to 9 mm). It has to be given, and is
                  (8.3 mm). summary.json tabulates the sizes in
                  WF_WINDOW_SWEEP.
    sweep extent  PREDICTED, then checked. At 8.3 mm the free fit needs 50°
                  of azimuth and 74° of elevation per sweep. The bar really
                  travelled 50° and 60°. So azimuth agrees to within 1%,
                  and along elevation this animal has about 1.24 times the
                  flat map's cortex per degree (prediction ÷ real value;
                  summary.json: sweep_check). Its map is stretched along
                  elevation relative to the drawn grid, and so holds about
                  1.24 times the flat map's cortex per square degree.
    left, right   cannot be fitted. A mirror-flipped brain looks the same, so
                  which hemisphere is on the left of the image has to be
                  given (WF_IMAGE_LEFT_IS). The recorded sweep directions
                  (bar moving right, bar moving up) fit with anterior at the
                  top of the image and the RIGHT hemisphere on its left.
                  Choosing 'left' instead flips the sign of the azimuth
                  scale and changes nothing else.

ASSUMPTIONS WORTH KNOWING  (all set in the CONFIG block)
  • Tree shrew azimuth beyond +10° is extrapolated (step 4 above). Its
    constants are not measured from tree shrew data, which the drawing does
    not have past +10°; they come from the stated balance described above.
  • Squirrel monkey values cover the part of V1 that Adams & Horton measured
    ring by ring: the visual field within 72° of the centre, which is 97% of
    V1. The rest is the monocular crescent, whose extent in the visual field
    the paper does not give, so it is left out of both the cortex and the
    visual field. Shares at 10°, 20° and 30° fall between measured rings and
    are interpolated; other reasonable interpolations move the 10° share by
    up to 3 points (summary.json lists them).
  • uniform_pct depends on how big each species' visual field is taken to be:
    -10° to 120° azimuth by ±60° elevation for tree shrew (read off the
    map), the hemifield within 72° eccentricity for squirrel monkey (the
    extent of the published measurements), and whatever the mouse maps
    themselves cover.
  • Mouse coordinates are shifted so that the point where V1, LM and RL meet
    is (0°, 0°), following Zhuang et al. Every pixel's eccentricity depends
    on that origin. After the shift V1 runs from 0° to 87° azimuth and 28°
    above and below 0° altitude, as the paper describes, and the centre of
    its coverage is at the paper's azimuth (38°) but about 6° lower in
    altitude than the paper's average. Moving the origin by up to 5° in any
    direction puts 3-10% of V1 within 10° (7.1% at the origin used) and the
    ratio at 1.7-2.5 (2.0).
  • The widefield maps are drawn in the screen's degrees (WF_DEGREES_FROM =
    'screen'): 50° of azimuth and 60° of elevation per sweep, in PsychoPy
    'deg' units on a flat screen 25 cm away. Those are true degrees at the
    screen centre and about 2% fewer over the stretch of each sweep that
    the window holds, and they assume the eye sat straight in front of the
    screen centre. Only the positions of 0° are taken from the flat map.
    'flatmap' would instead borrow the whole degree scale from the flat map
    (50° and 74° per sweep): the contours then fall on its grid, but
    elevation is overstated by about 24%.

INPUTS  (edit the CONFIG block; files live in Fig5_inputs/ next to this script)
  TS_SVG        the tree shrew flat-map SVG: V1 outline, Bosking grid, 5 mm scale bar
  MOUSE_TIFS    altitude/azimuth maps from Zhuang et al. 2017 example dataset
  WF_FILE       widefield_retinotopy.npz: the two phase maps, the trial-to-trial
                coherence, the midline and the vessel image of one imaging session,
                cut out of the 1 GB imaging workspace by extract_widefield()

OUTPUTS  (written to Fig5_outputs/ next to this script)
  figure5.png / .svg                 top: the widefield elevation and azimuth maps in
                                     degrees. Below, left: the flat map (solid = drawn
                                     grid, dashed = extrapolated azimuth). Below, right:
                                     % of V1 within 10°, and the ratio at 10°, 20°, 30°
                                     (pale → solid bars).
  widefield_registration_check.png   not a paper panel: the widefield contours laid on
                                     the flat map, and the cortex under the window
  mouse_origin_check.png             not a paper panel: mouse V1, LM, RL and the junction
                                     used as the origin, the shifted maps, and the result
                                     with the origin moved
  overrepresentation.csv             pct_V1, uniform_pct and ratio per species and eccentricity
  treeshrew_vertex_retinotopy.csv    every mesh point: position (mm), azimuth, elevation
  summary.json                       the same numbers plus intermediate values (V1 areas,
                                     squirrel monkey shares at the measured rings, mouse
                                     field extent and re-centring shift)
                                     and the azimuth law: the constants used, the refit on
                                     this drawing, the table over LAW_SWEEP, and the
                                     horizontal-meridian measurements it starts from;
                                     and the widefield calibration: placement, degrees
                                     per sweep and zero, colour limits, contour values,
                                     the table over WF_WINDOW_SWEEP, the check against
                                     the real sweep extents and the fit in the screen's
                                     own degrees;
                                     also printed when the script finishes

USAGE
  python Python/paper_figures/Fig5_cortex.py
  python Python/paper_figures/Fig5_cortex.py --extract-widefield    (only to remake WF_FILE)

Requires: numpy scipy pandas matplotlib shapely svgpathtools tifffile scikit-image (all in EyeHeadCoupling environment)
"""
import re, json, os, sys
import numpy as np, pandas as pd
import matplotlib as mpl, matplotlib.pyplot as plt
from matplotlib import patheffects
from matplotlib.tri import Triangulation
from matplotlib.lines import Line2D
from matplotlib.path import Path as MPath
from scipy.spatial import Delaunay, cKDTree
from scipy.sparse import coo_matrix, csr_matrix
from scipy.sparse.linalg import spsolve
from scipy.integrate import quad
from scipy.optimize import minimize
from scipy.interpolate import LinearNDInterpolator, PchipInterpolator
from scipy.ndimage import gaussian_filter, gaussian_filter1d, map_coordinates
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
    # Mouse origin. Zhuang et al. correct for where mouse and monitor happened to sit by
    # defining the point where V1, LM and RL meet as 0° altitude, 0° azimuth. mouse() finds
    # that junction itself (see its docstring) and checks it three ways: against
    # MOUSE_JUNCTION_BY_EYE, a landmark placed by eye on the field-sign map (pixel x, y; the
    # script stops if the two are more than MOUSE_JUNCTION_TOL_PX apart); against what the
    # paper reports (MOUSE_PUBLISHED: mean and ± as printed there, 14 mice); and by repeating
    # the analysis with the origin moved by every combination of MOUSE_ORIGIN_SHIFTS_DEG in
    # altitude and azimuth. mouse_origin_check.png shows all of it.
    MOUSE_BORDER_GAP_PX = 3,                      # a patch borders V1 if it comes this close to it
    MOUSE_JUNCTION_BY_EYE = (144, 298),
    MOUSE_JUNCTION_TOL_PX = 10,                   # 10 px = 0.13 mm, about 2° of altitude
    MOUSE_ORIGIN_RADIUS_PX = 8,                   # the origin is the mean of V1's map values this near the junction
    MOUSE_ORIGIN_SHIFTS_DEG = (-5.0, -2.5, 0.0, 2.5, 5.0),
    MOUSE_PUBLISHED = dict(correction_alt=(0.3, 1.8), correction_az=(14.9, 2.0),
                           coverage_centre_alt=(7.4, 2.1), coverage_centre_az=(37.8, 1.4)),
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
                 squirrelmonkey=None,             # the hemifield within the outermost ring below (72°)
                 mouse=None),                     # measured from the per-pixel maps below
    # Squirrel monkey: measured area of V1 between rings of equal eccentricity, on the mean
    # retinotopic map of four hemispheres of two animals (Adams & Horton 2003, J Neurosci
    # 23:3771, Table 1, "Striate cortex area (mm2)"). SM_RINGS_DEG are the rings; SM_BELT_MM2
    # is the area between each ring and the one inside it (the first is 0-1°). They sum to
    # 778.5 mm2. The monocular crescent, beyond 72°, is a further 23.5 mm2 (2.9% of V1); its
    # extent in the visual field is not given in the paper, so it is left out throughout.
    SM_RINGS_DEG  = (1, 2, 4, 8, 16, 24, 32, 50, 72),
    SM_BELT_MM2   = (49.3, 64.9, 97.3, 164.5, 168.2, 85.3, 43.7, 63.9, 41.4),
    SM_CRESCENT_MM2 = 23.5,
    BANDS = (10, 20, 30),
    # ---- widefield retinotopy (the two imaging maps), calibrated against the flat map ----
    WF_FILE       = os.path.join(IN_DIR, 'widefield_retinotopy.npz'),
    # Diameter of the imaging window, i.e. of the circular analysis mask (505 px across):
    # 8.3 mm, the visible part of the 10 mm chamber. A known size, not a fitted one: the fit
    # cannot choose it (see fit_widefield). It sets the scale bar, and the degree scale that
    # the free-slope fit reads off the flat map (degrees per sweep grow in proportion to it).
    # WF_WINDOW_SWEEP lists other sizes to tabulate in summary.json, to show how much an
    # error in it would matter.
    WF_WINDOW_MM  = 8.3,
    WF_WINDOW_SWEEP = (7.5, 8.0, 8.3, 8.5, 9.0),
    # Degrees the bar really travelled in one sweep: 50° of azimuth and 60° of elevation, as
    # confirmed by the experimenters for this session. (The stimulus scripts logged with the
    # run are Session_9/t00002/Retinotopy_LR.py and t00003/Retinotopy_UD.py. The elevation
    # script sweeps -30 to +30; the azimuth script as logged has startPointR = -25 and
    # endPointR = 35.) Each trial was an 8 s sweep and a 3 s blank, and the analysis took
    # phase over the sweep alone (readFourierMaps3_ISI with ISI = 3), so one unit of phase is
    # one whole sweep. These are PsychoPy 'deg' on a flat screen 25 cm away: true degrees at
    # the screen centre, about 2% fewer over the stretch of each sweep that the window holds.
    # Positive = phase grows rightward / upward, as recorded.
    # WF_DEGREES_FROM says which degree scale the drawn maps use. 'screen': these values, with
    # only the positions of 0° taken from the flat map (the fit with the slopes held at these
    # values). 'flatmap': the scale the free-slope fit reads off the flat map, so that the
    # contours fall on the flat map's grid. Either way summary.json reports both fits and
    # compares the two scales (sweep_check).
    WF_SWEEP_DEG  = dict(azimuth=50.0, elevation=60.0),
    WF_DEGREES_FROM = 'screen',
    # Which hemisphere is on the LEFT of the image: 'right' or 'left'. The image cannot say (a
    # mirror-flipped brain looks the same). 'right' is what the recorded sweep direction
    # implies (bar moving right, so phase grows toward the right visual field); 'left' means
    # the sweep ran the other way. It flips the sign of the azimuth scale and nothing else.
    WF_IMAGE_LEFT_IS = 'right',
    # Where the fit starts: rotation (deg, counter-clockwise) and the flat-map position (mm)
    # of the window centre. Set to None to search every placement first (about 15 s).
    WF_START      = dict(rot_deg=-12.2, x_mm=6.96, y_mm=7.03),
    WF_AZ_TRUST_MAX = 12.0,                       # flat-map azimuth beyond this is extrapolated: not used to judge the fit
    WF_MIN_COHERENCE = 0.5,                       # fit only pixels whose phase repeats across trials
    WF_FIT_SMOOTH_PX = 3.0, WF_SAMPLE_PX = 6,     # fit: light smoothing, then every 6th pixel
    WF_MIDLINE_MARGIN_PX = 14,                    # fit: leave out a strip either side of the midline (sinus)
    WF_GRID_MM    = 0.02,                         # spacing of the flat-map lookup grid
    WF_CONTOUR_SMOOTH_PX = 12.0,                  # drawing: smoothing before contouring
    WF_CONTOUR_MIN_PX = 110,                      # drawing: drop contour pieces shorter than this
    WF_CLIM       = dict(azimuth=None, elevation=None),   # colour limits (deg); None = from the data
    WF_SHADE_FLOOR = 0.55,                        # darkest the vessel image may make a colour (0 = black, 1 = no shading)
    # only for extract_widefield(), which made WF_FILE; not read by main()
    WF_SOURCE     = dict(mat=r'X:\Papers\Active_vision_ts\Figure5_CorticalRepresentation\Charlie_Data'
                             r'\Retino_Charlie_Fourier_MovingBar_Session9.mat',
                         vessels=r'X:\Papers\Active_vision_ts\Figure5_CorticalRepresentation\Charlie_Data'
                                 r'\Session_9\BV.png'),
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
    """Area (square degrees) of an azimuth × elevation rectangle on the sphere."""
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
    """Squirrel monkey results table, from the published area measurements of
    Adams & Horton (2003).

    Their Table 1 gives the area of V1 between rings of equal eccentricity
    (SM_RINGS_DEG, SM_BELT_MM2). Summed from the centre outward these give the
    area of V1 within each ring: measured points on the curve "cortex within
    x° of the centre". The bands wanted here (10°, 20°, 30°) fall between
    rings, so the curve is read off between its measured points with a smooth
    interpolation that cannot overshoot them (monotone cubic, against the
    logarithm of eccentricity). pct_V1 is that area as a % of the area within
    the outermost ring (72°), and uniform_pct is the % of the hemifield within
    72° that lies within the band, both taken as solid angle: (1 - cos x) /
    (1 - cos 72°). The monocular crescent beyond 72° is left out of both.

    Returns (table, info). table: one row per eccentricity in BANDS. info: the
    areas, the share of V1 within each measured ring (which reproduces the
    paper's 27% within 4° and 48% within 8°), pct_V1 recomputed as a share of
    all of V1 with the crescent included, and pct_V1 under four other ways of
    reading the curve between the measured rings, to show how much the
    interpolation matters."""
    rings = np.asarray(cfg['SM_RINGS_DEG'], float); cum = np.cumsum(cfg['SM_BELT_MM2'])
    bands = np.asarray(cfg['BANDS'], float); total = cum[-1]
    cap = lambda x: 1-np.cos(np.asarray(x, float)*D2R)                 # ∝ solid angle within x° of the centre
    area = PchipInterpolator(np.log(rings), cum)(np.log(bands))
    rows = [dict(band=int(b), pct_V1=100*a/total, uniform_pct=100*cap(b)/cap(rings[-1]),
                 ratio=(a/total)/(cap(b)/cap(rings[-1])), cortex_mm2=a) for b, a in zip(bands, area)]
    other = {'straight line against log eccentricity': np.interp(np.log(bands), np.log(rings), cum),
             'straight line against eccentricity': np.interp(bands, rings, cum),
             'monotone cubic against eccentricity': PchipInterpolator(np.r_[0, rings], np.r_[0, cum])(bands),
             'even cortex per square degree within each belt': np.interp(cap(bands), cap(rings), cum)}
    info = dict(V1_within_72deg_mm2=float(total), monocular_crescent_mm2=cfg['SM_CRESCENT_MM2'],
                pct_V1_within_each_ring={int(r): float(100*c/total) for r, c in zip(rings, cum)},
                pct_of_all_V1_including_crescent=[float(100*a/(total+cfg['SM_CRESCENT_MM2'])) for a in area],
                pct_V1_by_other_interpolations={k: [float(100*a/total) for a in v] for k, v in other.items()})
    return pd.DataFrame(rows), info

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
      3. Find areas LM and RL. They are the two patches that (a) share a border
         with V1, (b) have the opposite field sign to V1 and (c) represent the
         nasal side of V1's visual field (median azimuth below V1's). Of the
         two, LM is the one representing the upper field and RL the lower
         field (median altitude above / below V1's). This is how Zhuang et al.
         describe them, and the script stops unless exactly one patch fits
         each description.
      4. The junction is the pixel closest to V1, LM and RL together. The
         script stops if the three do not actually meet there, or if the
         junction is far from the landmark placed by eye (CONFIG).
      5. Shift altitude and azimuth so that the junction is (0°, 0°): subtract
         the mean of V1's values within MOUSE_ORIGIN_RADIUS_PX of it. This
         corrects for where mouse and monitor happened to sit, as Zhuang et
         al. do.
      6. Compute each V1 pixel's eccentricity and count the % within each band.
         Pixels are all the same size, so a % of pixels is a % of area.
      7. Check the origin. Compare the shifted maps with what the paper says
         of them (V1 runs from about 0° to 90° azimuth and 25-35° above and
         below 0° altitude; the size of the correction; the centre of V1's
         coverage; LM upper nasal, RL lower nasal). Then repeat step 6 with the
         origin moved by a few degrees in every direction, with the origin
         taken at the by-eye landmark, with other averaging radii, and with
         two other corrections (none, and the paper's mean), to see how much
         the result depends on it.

    Returns a dict: table (one row per band), A_V1 (mm²), extent (az0, az1, el0,
    el1 of V1 after the shift, degrees), offset (the altitude and azimuth
    subtracted), check (the numbers from steps 3, 4 and 7, written to
    summary.json) and the arrays draw_mouse_check needs."""
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
    v1p = max(patches, key=lambda p: coverage(p['mask'])); v1 = v1p['mask']
    mmpp = cfg['MOUSE_UM_PER_PX']/1000
    A_V1 = v1.sum()*mmpp**2
    # LM and RL, by what defines them (see the docstring), not by rank
    med = lambda img, m: float(np.median(img[m]))
    d_v1 = ni.distance_transform_edt(~v1); v1_az, v1_alt = med(azif, v1), med(altf, v1)
    nbrs = [dict(p, az=med(azif, p['mask']), alt=med(altf, p['mask'])) for p in patches
            if p is not v1p and d_v1[p['mask']].min() <= cfg['MOUSE_BORDER_GAP_PX']]
    nasal = [p for p in nbrs if p['sign'] == -v1p['sign'] and p['az'] < v1_az]
    lm = [p for p in nasal if p['alt'] > v1_alt]; rl = [p for p in nasal if p['alt'] <= v1_alt]
    if len(lm) != 1 or len(rl) != 1:
        raise RuntimeError(f'mouse: expected one LM and one RL among the patches bordering V1, found {len(lm)} and '
                           f'{len(rl)}; candidates (sign, median azimuth, altitude): '
                           f"{[(p['sign'], round(p['az'], 1), round(p['alt'], 1)) for p in nbrs]}")
    lm, rl = lm[0], rl[0]
    # the junction: the pixel closest to V1, LM and RL together
    dsum = sum(ni.distance_transform_edt(~m) for m in (v1, lm['mask'], rl['mask']))
    jy, jx = (int(v) for v in np.unravel_index(np.argmin(dsum), dsum.shape))
    if dsum[jy, jx] > 3*cfg['MOUSE_BORDER_GAP_PX']:
        raise RuntimeError(f'mouse: V1, LM and RL do not meet (closest approach {dsum[jy, jx]:.1f} px in total)')
    eye = cfg.get('MOUSE_JUNCTION_BY_EYE'); eye_px = float(np.hypot(jx-eye[0], jy-eye[1])) if eye else None
    if eye and eye_px > cfg['MOUSE_JUNCTION_TOL_PX']:
        raise RuntimeError(f'mouse: junction found at pixel ({jx}, {jy}) is {eye_px:.0f} px from the by-eye landmark {eye}; '
                           'look at mouse_origin_check.png from an earlier run and correct whichever is wrong')
    yy, xx = np.mgrid[0:v1.shape[0], 0:v1.shape[1]]
    def origin_at(x, y, r):
        near = ((yy-y)**2+(xx-x)**2 <= r**2) & v1
        return float(altf[near].mean()), float(azif[near].mean())
    def overrep(o_alt, o_azi):
        a = alt[v1]-o_alt; z = azi[v1]-o_azi; ecc = gc_ecc(z, a)
        ext = (float(z.min()), float(z.max()), float(a.min()), float(a.max()))
        rows = []
        for b in cfg['BANDS']:
            pv = 100*(ecc <= b).mean(); uf = 100*uniform_frac(b, *ext)
            rows.append(dict(band=b, pct_V1=pv, uniform_pct=uf, ratio=pv/uf if uf > 0 else np.nan))
        return pd.DataFrame(rows), ext
    off_alt, off_azi = origin_at(jx, jy, cfg['MOUSE_ORIGIN_RADIUS_PX'])
    tab, extent = overrep(off_alt, off_azi)
    # ---- checks on the origin (step 7) ----
    brief = lambda t: dict(pct_V1=[round(float(v), 2) for v in t.pct_V1],
                           ratio=[round(float(v), 3) if np.isfinite(v) else None for v in t.ratio])
    shifts = cfg['MOUSE_ORIGIN_SHIFTS_DEG']
    grid = [dict(d_alt=da, d_az=dz, **brief(overrep(off_alt+da, off_azi+dz)[0])) for da in shifts for dz in shifts]
    pub = cfg['MOUSE_PUBLISHED']
    other = {f'origin averaged within {r} px of the junction': origin_at(jx, jy, r) for r in (4, 12)}
    if eye: other['origin at the by-eye landmark'] = origin_at(eye[0], eye[1], cfg['MOUSE_ORIGIN_RADIUS_PX'])
    other["the paper's mean correction, not this animal's junction"] = (pub['correction_alt'][0], pub['correction_az'][0])
    other['no correction (maps as supplied)'] = (0.0, 0.0)
    other = {k: dict(offset_alt_az=[round(o[0], 2), round(o[1], 2)], **brief(overrep(*o)[0])) for k, o in other.items()}
    # centre of V1's coverage of the visual field (the middle of the patch of visual field V1 represents)
    a = altf[v1]-off_alt; z = azif[v1]-off_azi
    cov = np.zeros((240, 320), bool); cov[np.clip(((a+60)//0.5).astype(int), 0, 239), np.clip(((z+30)//0.5).astype(int), 0, 319)] = True
    cov = ni.binary_closing(cov, iterations=15); cyx = ni.center_of_mass(cov)
    check = dict(
        V1=dict(field_sign=v1p['sign'], median_azimuth=v1_az-off_azi, median_altitude=v1_alt-off_alt),
        LM=dict(field_sign=lm['sign'], median_azimuth=lm['az']-off_azi, median_altitude=lm['alt']-off_alt),
        RL=dict(field_sign=rl['sign'], median_azimuth=rl['az']-off_azi, median_altitude=rl['alt']-off_alt),
        other_patches_bordering_V1=[dict(field_sign=p['sign'], median_azimuth=p['az']-off_azi, median_altitude=p['alt']-off_alt)
                                    for p in nbrs if p is not lm and p is not rl],
        junction_pixel_xy=[jx, jy], V1_LM_RL_summed_distance_px=float(dsum[jy, jx]),
        by_eye_landmark_xy=list(eye) if eye else None, junction_to_landmark_px=eye_px,
        correction_alt_az_deg=[off_alt, off_azi],
        published_correction_mean_and_pm=dict(altitude=pub['correction_alt'], azimuth=pub['correction_az']),
        V1_extent_after_shift=dict(azimuth=extent[:2], altitude=extent[2:], published='about 0 to 90 azimuth; 25-35 above and below 0 altitude'),
        V1_coverage_centre_after_shift=dict(altitude=float(cyx[0]*0.5-60), azimuth=float(cyx[1]*0.5-30),
                                            published_mean_and_pm=dict(altitude=pub['coverage_centre_alt'], azimuth=pub['coverage_centre_az'])),
        result=brief(tab), origin_shift_grid=grid,
        range_over_shift_grid={k: [[min(g[k][i] for g in grid if g[k][i] is not None), max(g[k][i] for g in grid if g[k][i] is not None)]
                                   for i in range(len(cfg['BANDS']))] for k in ('pct_V1', 'ratio')},
        other_origins=other)
    return dict(table=tab, A_V1=A_V1, extent=extent, offset=(off_alt, off_azi), check=check,
                smf=smf, alt=altf-off_alt, azi=azif-off_azi, v1=v1, lm=lm['mask'], rl=rl['mask'],
                others=[p['mask'] for p in patches if p is not v1p and p is not lm and p is not rl], junction=(jx, jy))

# ============================ widefield retinotopy ===========================
def extract_widefield(cfg):
    """One-off helper, not called by main(): cut the small widefield input file (WF_FILE)
    out of the 1 GB MATLAB workspace saved by the imaging analysis (getRetinoFourier.m).

    Run with:  python Python/paper_figures/Fig5_cortex.py --extract-widefield
    Reads the two files named in WF_SOURCE and keeps:
      phase_azimuth, phase_elevation   Azimuth/Elevation.PhaseFullBVFreeMasked: response
                                       phase of each pixel to the bar sweep, 0-1 of a sweep,
                                       vessel artefacts filtered out, NaN outside the window
      coherence                        how repeatable each pixel's phase is across trials
                                       (|mean of the trials' complex responses| / mean of
                                       their amplitudes; 1 = same phase on every trial),
                                       the lower of the two sweeps
      midline_xy                       the midline points clicked in the analysis (saved
                                       there as 'V1border'), as 0-based pixel x, y
      vessels                          the blood-vessel image of the window (BV.png)
      sweep_azimuth, sweep_elevation   recorded bar direction ('right', 'up')"""
    from scipy.io import loadmat
    from PIL import Image
    src = cfg['WF_SOURCE']
    mat = loadmat(src['mat'], variable_names=['Azimuth', 'Elevation'], struct_as_record=False, squeeze_me=True)
    keep, coh = {}, []
    for name in ('Azimuth', 'Elevation'):
        st = mat[name]; fd = np.asarray(st.freqData)[:, :, :-1]     # the analysis leaves out the last trial
        keep[f'phase_{name.lower()}'] = np.asarray(st.PhaseFullBVFreeMasked, np.float32)
        keep[f'sweep_{name.lower()}'] = np.array(str(st.MotionDir))
        coh.append(np.abs(fd.mean(2))/(np.abs(fd).mean(2)+1e-12))
    keep['coherence'] = np.minimum(*coh).astype(np.float16)
    keep['midline_xy'] = np.asarray(mat['Azimuth'].V1border, np.float32)-1.0   # MATLAB counts from 1
    keep['vessels'] = np.asarray(Image.open(src['vessels']))
    keep['source'] = np.array(f"{os.path.basename(src['mat'])} + {os.path.basename(src['vessels'])}")
    np.savez_compressed(cfg['WF_FILE'], **keep)
    print(f"wrote {cfg['WF_FILE']} ({os.path.getsize(cfg['WF_FILE'])/1e6:.1f} MB)")

def nan_smooth(img, sigma):
    """Gaussian blur that ignores NaN pixels and leaves them NaN."""
    ok = np.isfinite(img)
    num = gaussian_filter(np.where(ok, img, 0.0), sigma, mode='nearest')
    den = gaussian_filter(ok.astype(float), sigma, mode='nearest')
    out = np.divide(num, den, out=np.full_like(num, np.nan), where=den > 1e-6)
    out[~ok] = np.nan
    return out

def load_widefield(cfg):
    """Read the widefield input file and measure the window in the image.

    Returns a dict: paz and pel (phase maps of the azimuth and elevation sweeps, 0-1, NaN
    outside the window), coh (trial-to-trial coherence, 0-1), bv (vessel image), mask
    (pixels inside the window), cx, cy and diam_px (window centre and diameter, pixels),
    mid (a, b of the midline x = a*y + b), X and Y (pixel coordinates) and side (how far
    each pixel is to the right of the midline, pixels; negative = image-left half)."""
    d = np.load(cfg['WF_FILE'])
    paz, pel = d['phase_azimuth'].astype(float), d['phase_elevation'].astype(float)
    mask = np.isfinite(paz) & np.isfinite(pel)
    ys, xs = np.nonzero(mask)
    a, b = np.polyfit(d['midline_xy'][:, 1], d['midline_xy'][:, 0], 1)
    Y, X = np.mgrid[0:paz.shape[0], 0:paz.shape[1]]
    return dict(paz=paz, pel=pel, coh=d['coherence'].astype(float), bv=d['vessels'].astype(float), mask=mask,
                cx=0.5*(xs.min()+xs.max()), cy=0.5*(ys.min()+ys.max()), diam_px=float(np.ptp(xs)+1),
                mid=(float(a), float(b)), X=X, Y=Y, side=X-(a*Y+b))

def wf_reflect(x, y, wf):
    """Mirror image points across the midline (the two hemispheres are mirror images)."""
    a, b = wf['mid']; dx, dy = a/np.hypot(a, 1), 1/np.hypot(a, 1)
    par = (x-b)*dx+y*dy
    return b+2*par*dx-(x-b), 2*par*dy-y

def wf_to_flatmap(x, y, cal, wf):
    """Image pixel → position on the flat map (mm), for a pixel on the image-left side of
    the midline (mirror image-right pixels with wf_reflect first).

    cal holds the placement: window_mm (window diameter, which sets the mm per pixel),
    rot_deg (counter-clockwise rotation of the image on the flat map) and x_mm, y_mm (where
    the window centre lands). Image y runs downward and the flat map's upward, hence -y."""
    s = cal['window_mm']/wf['diam_px']; th = np.radians(cal['rot_deg'])
    u, v = x-wf['cx'], -(y-wf['cy'])
    return s*(np.cos(th)*u-np.sin(th)*v)+cal['x_mm'], s*(np.sin(th)*u+np.cos(th)*v)+cal['y_mm']

def wf_samples(wf, cfg):
    """The pixels the fit uses.

    Both phase maps are lightly smoothed and every WF_SAMPLE_PX-th pixel is taken, leaving
    out pixels whose phase does not repeat across trials (WF_MIN_COHERENCE) and a strip
    along the midline. Pixels of the image-right half are mirrored across the midline, so
    both hemispheres can be laid on the one (left-hemisphere) flat map with one placement.
    hemi is +1 for pixels of the left hemisphere and -1 for the right: the flat map counts
    azimuth as positive toward the opposite side of the visual field, so the azimuth on the
    screen (positive = right) is hemi × the flat map's."""
    st = cfg['WF_SAMPLE_PX']; sl = (slice(None, None, st), slice(None, None, st))
    paz, pel = (nan_smooth(wf[k], cfg['WF_FIT_SMOOTH_PX'])[sl] for k in ('paz', 'pel'))
    side = wf['side'][sl]
    ok = wf['mask'][sl] & (wf['coh'][sl] >= cfg['WF_MIN_COHERENCE']) & (np.abs(side) > cfg['WF_MIDLINE_MARGIN_PX'])
    x, y, side = wf['X'][sl][ok].astype(float), wf['Y'][sl][ok].astype(float), side[ok]
    xr, yr = wf_reflect(x, y, wf)
    left_is = +1 if cfg['WF_IMAGE_LEFT_IS'] == 'left' else -1
    return dict(x=np.where(side > 0, xr, x), y=np.where(side > 0, yr, y), paz=paz[ok], pel=pel[ok],
                hemi=np.where(side < 0, left_is, -left_is),
                sd_az=float(np.std(paz[ok])), sd_el=float(np.std(pel[ok])))

def rasterise_flatmap(ts, cfg):
    """The flat map's azimuth and elevation on a regular grid (every WF_GRID_MM), so that
    thousands of positions can be looked up quickly. 'inside' marks grid points within V1;
    'drawn' marks those whose azimuth comes from the drawn grid rather than from the
    extrapolation (azimuth up to WF_AZ_TRUST_MAX)."""
    V, h = ts['V'], cfg['WF_GRID_MM']
    gx = np.arange(V[:, 0].min()-0.5, V[:, 0].max()+0.5, h); gy = np.arange(V[:, 1].min()-0.5, V[:, 1].max()+0.5, h)
    GX, GY = np.meshgrid(gx, gy); pts = np.c_[GX.ravel(), GY.ravel()]
    az = LinearNDInterpolator(V, ts['AZ'])(pts).reshape(GX.shape)
    el = LinearNDInterpolator(V, ts['EL'])(pts).reshape(GX.shape)
    inside = MPath(ts['OUT']).contains_points(pts).reshape(GX.shape) & np.isfinite(az) & np.isfinite(el)
    return dict(x0=gx[0], y0=gy[0], h=h, az=np.where(inside, az, 0.0), el=np.where(inside, el, 0.0),
                inside=inside.astype(float), drawn=(inside & (az <= cfg['WF_AZ_TRUST_MAX'])).astype(float))

def _phase_line(flat, phase, ok, sd, slope=None, iters=4):
    """Straight line phase ≈ a × flat + b through the pixels in `ok`, refitted a few times
    while leaving out pixels more than 1 SD (`sd`) off the line. If `slope` is given, a is
    held at it and only b is fitted."""
    use = ok.copy(); a, b = 0.0, float(np.mean(phase))
    for _ in range(iters):
        if use.sum() < 30 or np.std(flat[use]) < 1e-6:
            return 0.0, float(np.mean(phase[use])) if use.any() else float(np.mean(phase))
        if slope is None: a, b = np.polyfit(flat[use], phase[use], 1)
        else: a, b = slope, np.mean(phase[use]-slope*flat[use])
        use = ok & (np.abs(phase-(a*flat+b)) < sd)
    return float(a), float(b)

def wf_score(q, D, S, fm, wf, detail=False, sweep_deg=None):
    """How badly the flat map explains the widefield maps at one placement (0 = perfectly,
    0.5 = not at all). q = (rot_deg, x_mm, y_mm); D = window diameter in mm. sweep_deg, if
    given, is (azimuth, elevation) degrees per sweep: the two lines' slopes are then held
    at those values and only their zeros are fitted.

    Each sampled pixel is put on the flat map, which says what azimuth and elevation that
    spot of V1 represents. If the placement is right, the pixel's phase in each sweep is a
    straight-line function of those degrees (the bar moved at constant speed). So a line is
    fitted for each sweep, and the score is the share of the phase maps' variance the lines
    leave unexplained (each pixel's miss capped at 1 SD). Pixels landing outside V1 count as
    a neutral 0.5 (the window does hold cortex that is not V1), and so does the azimuth of
    pixels landing where the flat map's azimuth is extrapolated.

    With detail=True returns the calibration instead: the placement, degrees = slope × phase
    + zero for each sweep, the share of each phase map's variance explained, and the share
    of the sampled pixels that land in V1."""
    cal = dict(window_mm=float(D), rot_deg=float(q[0]), x_mm=float(q[1]), y_mm=float(q[2]))
    x, y = wf_to_flatmap(S['x'], S['y'], cal, wf)
    look = lambda k: map_coordinates(fm[k], [(y-fm['y0'])/fm['h'], (x-fm['x0'])/fm['h']],
                                     order=1, mode='constant', cval=0.0)
    inside, drawn = look('inside') > 0.999, look('drawn') > 0.999
    azf, elf = S['hemi']*look('az'), look('el')
    a1, b1 = _phase_line(azf, S['paz'], drawn, S['sd_az'], None if sweep_deg is None else 1/sweep_deg[0])
    a2, b2 = _phase_line(elf, S['pel'], inside, S['sd_el'], None if sweep_deg is None else 1/sweep_deg[1])
    e_az = np.minimum(((S['paz']-(a1*azf+b1))/S['sd_az'])**2, 1.0)
    e_el = np.minimum(((S['pel']-(a2*elf+b2))/S['sd_el'])**2, 1.0)
    score = float(np.where(inside, 0.5*(np.where(drawn, e_az, 0.5)+e_el), 0.5).mean())
    if not detail:
        return score
    inv = lambda a, b: (1/a, -b/a) if abs(a) > 1e-9 else (np.nan, np.nan)     # phase = a·deg + b  →  deg = phase/a - b/a
    (cal['az_slope'], cal['az_zero']), (cal['el_slope'], cal['el_zero']) = inv(a1, b1), inv(a2, b2)
    cal.update(explained_az=float(1-e_az[drawn].mean()) if drawn.any() else np.nan,
               explained_el=float(1-e_el[inside].mean()) if inside.any() else np.nan,
               frac_in_V1=float(inside.mean()), score=score)
    return cal

def wf_footprint(cal, wf, n=400):
    """Outline, on the flat map (mm), of one half of the window: the part of the circular
    window that lies on the image-left side of the midline."""
    th = np.linspace(0, 2*np.pi, n); r = wf['diam_px']/2; a, b = wf['mid']
    y0, y1 = wf['cy']-2*r, wf['cy']+2*r
    half = SPoly(np.c_[wf['cx']+r*np.cos(th), wf['cy']+r*np.sin(th)]).intersection(
        SPoly([(a*y0+b, y0), (a*y1+b, y1), (a*y1+b-4*r, y1), (a*y0+b-4*r, y0)]))
    P = np.array(half.exterior.coords)
    return np.c_[wf_to_flatmap(P[:, 0], P[:, 1], cal, wf)]

def fit_widefield(ts, wf, cfg):
    """Put the widefield maps in degrees by registering them onto the flat map.

    WHY A FIT IS NEEDED. The imaging gives, for every pixel, the phase (0-1) of the bar
    sweep at which that pixel responded. Phase is not degrees: how many degrees one sweep
    covered, and which phase corresponds to 0°, depend on the screen's geometry and on
    where the animal was looking. The flat map does carry degrees. So the window is laid
    on the flat map and the degree scale is read off it.

    THE MODEL. Both hemispheres are in the window. They are mirror images, so the image-
    right half is reflected across the midline and both halves are placed on the (left-
    hemisphere) flat map with ONE placement: a rotation and a position of the window
    centre. The scale (mm per pixel) follows from the window diameter. One stimulus was
    shown to both hemispheres, so both also share ONE degree calibration:
        azimuth on the screen = az_slope × phase + az_zero       (positive = right)
        elevation             = el_slope × phase + el_zero       (positive = up)
    For a trial placement, wf_score fits those two lines and says how much of the two phase
    maps they explain. The placement is refined (Nelder-Mead) from WF_START, or from the
    best of a search over all rotations and positions if WF_START is None.

    WHAT THE FIT CANNOT DO: CHOOSE THE WINDOW SIZE. A larger window covers more of the flat
    map, hence more degrees, and the degree scale simply stretches to match: the maps are
    explained equally well at every diameter tried (6 to 9 mm). The diameter therefore has
    to be given (WF_WINDOW_MM), and the degrees per sweep are proportional to it. What does
    not depend on it is the phase at which azimuth is 0° (the vertical meridian). The table
    over WF_WINDOW_SWEEP in summary.json shows the rest.

    WHAT IT ALSO CANNOT DO: TELL LEFT FROM RIGHT. Swapping which hemisphere is which flips
    the sign of az_slope and az_zero and fits exactly as well (WF_IMAGE_LEFT_IS).

    THE CHECK, AND A STRICTER FIT. With the window size known, az_slope and el_slope are
    predictions: the degrees the bar must have travelled per sweep if this animal's V1 is
    laid out exactly like the flat map. If the degrees it really travelled are given
    (WF_SWEEP_DEG), the prediction divided by the real value is this animal's cortex per
    degree relative to the flat map's, along each axis (1 = the same). The fit is then
    also repeated with the two slopes held at the real values, leaving only the placement
    and the two zeros free: the widefield maps in the screen's own degrees, which is what
    is drawn when WF_DEGREES_FROM = 'screen'.

    Returns (cal, table, strict): cal is the calibration at WF_WINDOW_MM (see wf_score),
    with the range of azimuth and elevation found in the window (1st-99th percentile of the
    fitted pixels), the area of V1 under one half of the window, and the stretch of visual
    field that half holds as a share of the whole visual field (FIELD); table holds the same
    for every diameter in WF_WINDOW_SWEEP; strict is None without WF_SWEEP_DEG, otherwise a
    dict with sweep_check (prediction, real value and their ratio per axis) and calibration
    (the fit with the slopes held at the real values)."""
    fm = rasterise_flatmap(ts, cfg); S = wf_samples(wf, cfg); v1 = SPoly(ts['OUT']).buffer(0)
    def refine(D, q0, sweep_deg=None):
        # the score is slightly bumpy (pixels drop in and out of the line fits), so restart the
        # simplex from wherever it stopped until that no longer helps
        best = (np.asarray(q0, float), np.inf)
        for _ in range(6):
            r = minimize(lambda q: wf_score(q, D, S, fm, wf, sweep_deg=sweep_deg), best[0], method='Nelder-Mead',
                         options=dict(xatol=1e-4, fatol=1e-7, maxiter=4000,
                                      initial_simplex=best[0]+np.vstack([np.zeros(3), np.diag([4, 0.25, 0.25])])))
            if r.fun > best[1]-1e-6: break
            best = (r.x, r.fun)
        return best
    def describe(D, q, sweep_deg=None):
        c = wf_score(q, D, S, fm, wf, detail=True, sweep_deg=sweep_deg)
        c['rot_deg'] = (c['rot_deg']+180) % 360-180
        for name, ph in (('azimuth', S['paz']), ('elevation', S['pel'])):
            deg = c[f'{name[:2]}_slope']*ph+c[f'{name[:2]}_zero']
            c[f'{name}_in_window_deg'] = [float(v) for v in np.percentile(deg, [1, 99])]
        c['V1_under_half_window_mm2'] = float(SPoly(wf_footprint(c, wf)).buffer(0).intersection(v1).area)
        c['V1_under_half_window_pct'] = 100*c['V1_under_half_window_mm2']/ts['A_V1']
        # the stretch of visual field one hemisphere's half of the window holds (az0, az1, el0, el1;
        # + azimuth = the opposite side, as on the flat map), as a share of the whole visual field,
        # and how that share compares with the share of V1 lying under the half-window
        az = S['hemi']*(c['az_slope']*S['paz']+c['az_zero'])
        box = [float(v) for v in np.percentile(az, [1, 99])]+c['elevation_in_window_deg']
        c['field_under_half_window_deg'] = box
        c['field_under_half_window_pct'] = 100*rect_field_deg2(*box)/rect_field_deg2(*cfg['FIELD']['treeshrew'])
        c['overrepresentation_under_window'] = c['V1_under_half_window_pct']/c['field_under_half_window_pct']
        return c
    D0 = cfg['WF_WINDOW_MM']
    if cfg.get('WF_START'):
        starts = [[cfg['WF_START'][k] for k in ('rot_deg', 'x_mm', 'y_mm')]]
    else:
        V = ts['V']
        grid = [(th, tx, ty) for th in np.arange(0, 360, 15)
                for tx in np.arange(V[:, 0].min()-2, V[:, 0].max()+2.01, 0.75)
                for ty in np.arange(V[:, 1].min()-2, V[:, 1].max()+2.01, 0.75)]
        starts = sorted(grid, key=lambda q: wf_score(q, D0, S, fm, wf))[:5]
    q_best = min((refine(D0, q) for q in starts), key=lambda r: r[1])[0]
    cal = describe(D0, q_best)
    if min(cal['explained_az'], cal['explained_el']) < 0.8:
        print('widefield fit explains less than 80% of a phase map — try WF_START = None')
    # the other window sizes: walk outward from the chosen one, each starting from its neighbour
    table, sizes = [], sorted(cfg['WF_WINDOW_SWEEP'])
    for seq in ([D for D in sizes if D >= D0], [D for D in sizes if D < D0][::-1]):
        q = q_best
        for D in seq:
            if D == D0: table.append(cal); continue
            q = refine(D, q)[0]; table.append(describe(D, q))
    strict, real = None, cfg.get('WF_SWEEP_DEG') or {}
    if real.get('azimuth') and real.get('elevation'):
        sweep_deg = (real['azimuth'], real['elevation'])
        strict = dict(sweep_check={name: dict(predicted_deg_per_sweep=cal[f'{name[:2]}_slope'], real_deg_per_sweep=float(v),
                                              cortex_per_degree_vs_flatmap=cal[f'{name[:2]}_slope']/v)
                                   for name, v in real.items()},
                      calibration=describe(D0, refine(D0, q_best, sweep_deg)[0], sweep_deg))
    return cal, sorted(table, key=lambda c: c['window_mm']), strict

def wf_contours(deg, levels, wf, cfg):
    """Lines of equal azimuth or elevation across the window, as (level, line, label) with
    each line an array of image pixel x, y, and label True for the longest line of its
    level in its hemisphere (the one to write the value on).

    Each hemisphere is contoured on its own (smoothing across the midline would blend the
    two), after a WF_CONTOUR_SMOOTH_PX blur. Closed loops and pieces shorter than
    WF_CONTOUR_MIN_PX are dropped, leaving the lines that run across the map."""
    out = []
    figt, axt = plt.subplots()
    for half in (wf['side'] < -9, wf['side'] > 9):
        sm = nan_smooth(np.where(half & wf['mask'], deg, np.nan), cfg['WF_CONTOUR_SMOOTH_PX'])
        lv = [l for l in levels if np.nanmin(sm) < l < np.nanmax(sm)]
        if not lv: continue
        cs = axt.contour(sm, levels=lv)
        for level, segs in zip(cs.levels, cs.allsegs):
            keep = []
            for v in segs:
                closed = len(v) > 2 and np.allclose(v[0], v[-1])
                if closed or np.hypot(*np.diff(v, axis=0).T).sum() < cfg['WF_CONTOUR_MIN_PX']: continue
                s = gaussian_filter1d(v, 6.0, axis=0, mode='nearest'); s[0], s[-1] = v[0], v[-1]
                keep.append(s)
            keep.sort(key=len, reverse=True)                 # longest first: the one that gets the label
            out += [(float(level), s, i == 0) for i, s in enumerate(keep)]
    plt.close(figt)
    return out

def widefield_maps(wf, cal, ts, cfg):
    """The two widefield maps in degrees, ready to draw.

    For 'azimuth' and 'elevation' returns deg (the map, degrees = slope × phase + zero),
    levels (the flat map's drawn grid values that occur in the window, so the contours can
    be set against the flat map's lines), lines (those contours, see wf_contours) and lim
    (colour limits: WF_CLIM, or the range found in the window rounded outward to 2.5°,
    symmetric about 0° for azimuth)."""
    out = {}
    for name, ph, drawn in (('azimuth', wf['paz'], ts['DRAWN_AZ']), ('elevation', wf['pel'], ts['DRAWN_EL'])):
        deg = cal[f'{name[:2]}_slope']*ph+cal[f'{name[:2]}_zero']
        lo, hi = cal[f'{name}_in_window_deg']
        signs = (1, -1) if name == 'azimuth' else (1,)       # each hemisphere has the flat map's azimuths, mirrored
        levels = sorted({float(s*l) for l in drawn for s in signs if lo < s*l < hi})
        lim = cfg['WF_CLIM'][name]
        if lim is None:
            lim = (np.floor(lo/2.5)*2.5, np.ceil(hi/2.5)*2.5)
            if name == 'azimuth': lim = (-max(abs(lim[0]), abs(lim[1])), max(abs(lim[0]), abs(lim[1])))
        out[name] = dict(deg=deg, levels=levels, lim=tuple(float(v) for v in lim),
                         lines=wf_contours(deg, levels, wf, cfg))
    return out

def wf_rotate(img, wf):
    """Rotate an image about the window centre so that the midline is vertical (NaN-aware).
    Used for display only."""
    phi = np.arctan(wf['mid'][0]); c, s = np.cos(phi), np.sin(phi)
    dx, dy = wf['X']-wf['cx'], wf['Y']-wf['cy']
    src = [wf['cy']-s*dx+c*dy, wf['cx']+c*dx+s*dy]
    ok = np.isfinite(img)
    num = map_coordinates(np.where(ok, img, 0.0), src, order=1, cval=0.0)
    den = map_coordinates(ok.astype(float), src, order=1, cval=0.0)
    return np.divide(num, den, out=np.full_like(num, np.nan), where=den > 0.99)

def wf_display_xy(x, y, wf):
    """Image pixel → pixel of the rotated image that wf_rotate makes."""
    phi = np.arctan(wf['mid'][0]); c, s = np.cos(phi), np.sin(phi)
    return wf['cx']+c*(x-wf['cx'])-s*(y-wf['cy']), wf['cy']+s*(x-wf['cx'])+c*(y-wf['cy'])

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
    axD.set_ylabel('% of V1 within 10° eccentricity'); axD.set_ylim(0, 65)
    w = 0.25
    for i, b in enumerate(cfg['BANDS']):
        axE.bar(xx+(i-1)*w, [res[s].loc[res[s].band == b, 'ratio'].iloc[0] for s in order], w,
                color=[COL[s] for s in order], alpha=[0.42, 0.70, 1.0][i], edgecolor='w', lw=0.4)
    axE.set_xticks(xx); axE.set_xticklabels([s.replace(' ', '\n') for s in order], fontsize=7)
    axE.set_yscale('log'); axE.set_ylim(0.9, 60); axE.set_ylabel('over-representation ratio')

def draw_mouse_check(ms, cfg, path):
    """Check figure (not a paper panel): where the mouse origin was put, and how much it matters.

    Top row: the field-sign map with every patch outlined and V1, LM and RL named; the
    azimuth map and the altitude map after the shift, with contours every 10° (0° bold).
    The star is the junction the script found, the cross the landmark placed by eye.
    Bottom row: the junction enlarged, with the circle of V1 pixels averaged to give the
    origin; eccentricity inside V1 with the 10°, 20° and 30° rings; and the share of V1
    within each band when the origin is moved (dots: every shift in MOUSE_ORIGIN_SHIFTS_DEG;
    line: the origin used), with the comparison against the paper's numbers written out."""
    import scipy.ndimage as ni
    ck = ms['check']; jx, jy = ms['junction']; eye = cfg.get('MOUSE_JUNCTION_BY_EYE'); r = cfg['MOUSE_ORIGIN_RADIUS_PX']
    fig = plt.figure(figsize=(16.5, 11.6)); gs = fig.add_gridspec(3, 3, height_ratios=[1, 1, 0.16])
    axes = np.array([[fig.add_subplot(gs[i, j]) for j in range(3)] for i in range(2)])
    seen = ni.binary_dilation(ms['v1'] | ms['lm'] | ms['rl'] | np.any(ms['others'], axis=0), iterations=12)   # where there is a map to contour
    def outlines(ax, lw=1.0):
        for m in ms['others']: ax.contour(m, [0.5], colors='0.35', linewidths=0.6)
        for m, c in ((ms['v1'], 'k'), (ms['lm'], '#1B7837'), (ms['rl'], '#762A83')):
            ax.contour(m, [0.5], colors=c, linewidths=1.8*lw)
    def marks(ax, ms_=15):
        ax.plot(jx, jy, '*', color='yellow', mec='k', ms=ms_, zorder=9)
        if eye: ax.plot(eye[0], eye[1], 'x', color='k', ms=0.6*ms_, mew=2, zorder=10)
    ax = axes[0, 0]; ax.imshow(ms['smf'], cmap='RdBu_r', vmin=-1, vmax=1); outlines(ax); marks(ax)
    for name, m, c in (('V1', ms['v1'], 'k'), ('LM', ms['lm'], '#1B7837'), ('RL', ms['rl'], '#762A83')):
        cy, cx = ni.center_of_mass(m)
        ax.text(cx, cy, name, ha='center', va='center', fontsize=11, weight='bold', color=c,
                bbox=dict(fc='w', ec='none', alpha=.75, pad=1))
    ax.set_title('field sign (red +, blue -); star = junction found, cross = placed by eye', fontsize=9)
    for ax, key, lv in ((axes[0, 1], 'azi', np.arange(-20, 121, 10)), (axes[0, 2], 'alt', np.arange(-60, 61, 10))):
        img = ms[key]; lim = np.percentile(img[ms['v1']], [0, 100])
        im = ax.imshow(img, cmap='Spectral_r', vmin=lim[0]-10, vmax=lim[1]+10)
        sm = np.where(seen, ni.gaussian_filter(img, 3), np.nan)
        cs = ax.contour(sm, levels=[l for l in lv if l != 0], colors='k', linewidths=0.5); ax.clabel(cs, fmt='%g', fontsize=6)
        ax.contour(sm, levels=[0], colors='k', linewidths=2.0)
        outlines(ax, 0.7); marks(ax, 12); fig.colorbar(im, ax=ax, fraction=0.04)
        ax.set_title(('azimuth' if key == 'azi' else 'altitude')+' after the shift (deg); bold line = 0°', fontsize=9)
    ax = axes[1, 0]; ax.imshow(ms['smf'], cmap='RdBu_r', vmin=-1, vmax=1, interpolation='nearest'); outlines(ax); marks(ax, 20)
    th = np.linspace(0, 2*np.pi, 100); ax.plot(jx+r*np.cos(th), jy+r*np.sin(th), 'k--', lw=1)
    ax.set_xlim(jx-55, jx+55); ax.set_ylim(jy+55, jy-55)
    ax.set_title(f'the junction enlarged; V1 pixels inside the circle ({r} px) give the origin', fontsize=9)
    ax = axes[1, 1]
    ecc = np.where(ms['v1'], gc_ecc(ms['azi'], ms['alt']), np.nan)
    im = ax.imshow(ecc, cmap='viridis_r'); fig.colorbar(im, ax=ax, fraction=0.04)
    cs = ax.contour(np.where(ms['v1'], gc_ecc(ni.gaussian_filter(ms['azi'], 2), ni.gaussian_filter(ms['alt'], 2)), np.nan),
                    levels=list(cfg['BANDS']), colors='w', linewidths=1.6)
    ax.clabel(cs, fmt='%g°', fontsize=8); ax.contour(ms['v1'], [0.5], colors='k', linewidths=1.2); marks(ax, 12)
    ys, xs = np.nonzero(ms['v1']); ax.set_xlim(xs.min()-25, xs.max()+25); ax.set_ylim(ys.max()+25, ys.min()-25)
    ax.set_title('eccentricity inside V1 (deg), with the bands that are counted', fontsize=9)
    ax = axes[1, 2]
    for i, b in enumerate(cfg['BANDS']):
        v = [g['pct_V1'][i] for g in ck['origin_shift_grid']]
        ax.plot(np.full(len(v), i)+np.linspace(-0.18, 0.18, len(v)), v, '.', color=COL['Mouse'], alpha=.6)
        ax.plot([i-0.3, i+0.3], [ck['result']['pct_V1'][i]]*2, 'k-', lw=2)
        ax.text(i, max(v)+1.5, f"{ck['result']['pct_V1'][i]:.1f}%\n({min(v):.1f}-{max(v):.1f})", ha='center', fontsize=8)
    ax.set_xticks(range(len(cfg['BANDS']))); ax.set_xticklabels([f'within {b}°' for b in cfg['BANDS']])
    ax.set_ylabel('% of V1'); ax.set_ylim(0, 1.45*max(g['pct_V1'][-1] for g in ck['origin_shift_grid']))
    s = cfg['MOUSE_ORIGIN_SHIFTS_DEG']; e, c = ck['V1_extent_after_shift'], ck['V1_coverage_centre_after_shift']
    p = ck['published_correction_mean_and_pm']
    ax.set_title(f'share of V1 when the origin is moved by {min(s):g}° to {max(s):+g}° in altitude and azimuth', fontsize=9)
    axt = fig.add_subplot(gs[2, :]); axt.axis('off')
    axt.text(0.0, 1.0, '\n'.join([
        f"correction: alt {ck['correction_alt_az_deg'][0]:.1f}°, az {ck['correction_alt_az_deg'][1]:.1f}°"
        f"   (paper: {p['altitude'][0]} ± {p['altitude'][1]}, {p['azimuth'][0]} ± {p['azimuth'][1]})",
        f"V1 after the shift: az {round(e['azimuth'][0]):d} to {round(e['azimuth'][1]):d}°, alt {round(e['altitude'][0]):d} to {round(e['altitude'][1]):+d}°"
        "   (paper: ~0 to 90; 25-35 above and below 0)",
        f"centre of V1's coverage: alt {c['altitude']:.1f}°, az {c['azimuth']:.1f}°   (paper: 7.4 ± 2.1, 37.8 ± 1.4)",
        f"LM: az {ck['LM']['median_azimuth']:.0f}°, alt {ck['LM']['median_altitude']:+.0f}°;  "
        f"RL: az {ck['RL']['median_azimuth']:.0f}°, alt {ck['RL']['median_altitude']:+.0f}°;  "
        f"V1: az {ck['V1']['median_azimuth']:.0f}°, alt {ck['V1']['median_altitude']:+.0f}°   (paper: LM upper nasal, RL lower nasal)",
        f"junction ({jx}, {jy})" + (f", {ck['junction_to_landmark_px']:.1f} px from the by-eye landmark" if eye else '')]),
        transform=axt.transAxes, va='top', fontsize=9, family='monospace')
    fig.suptitle('Mouse (Zhuang et al. 2017 example maps): where the origin of the visual field was put, and how much it matters', fontsize=11)
    fig.tight_layout(); fig.savefig(path, dpi=150); plt.close(fig)

def draw_widefield(ax_el, ax_az, wf, cal, maps, cfg):
    """Draw the two widefield maps: elevation (ax_el) and azimuth (ax_az), in degrees.

    Colour is degrees (red = low, blue = high), darkened by the blood-vessel image so the
    vessels show. Black lines are the contours from widefield_maps, at the flat map's grid
    values; the bold ones are 0° (horizontal and vertical meridian). The image is rotated
    so the midline is vertical. Elevation gets a vertical colour bar and the 2 mm scale
    bar (set by WF_WINDOW_MM); azimuth gets a horizontal colour bar."""
    r, cx, cy = wf['diam_px']/2, wf['cx'], wf['cy']; px_mm = wf['diam_px']/cal['window_mm']
    shade = wf_rotate(np.where(wf['mask'], wf['bv'], np.nan), wf)
    shade = np.clip(shade/np.nanpercentile(shade, 99.5), 0, 1)**0.5
    f = cfg['WF_SHADE_FLOOR']; shade = f+(1-f)*(shade-np.nanmin(shade))/(np.nanmax(shade)-np.nanmin(shade))
    cmap = plt.get_cmap('Spectral'); th = np.linspace(0, 2*np.pi, 400)
    halo = lambda w: [patheffects.withStroke(linewidth=w, foreground='w')]
    for ax, name in ((ax_el, 'elevation'), (ax_az, 'azimuth')):
        m = maps[name]; lim = m['lim']; deg = wf_rotate(m['deg'], wf)
        rgba = cmap(np.clip((deg-lim[0])/(lim[1]-lim[0]), 0, 1)); rgba[..., :3] *= shade[..., None]
        rgba[~np.isfinite(deg)] = (1, 1, 1, 0)
        ax.imshow(rgba, interpolation='nearest')
        for level, v, label in m['lines']:
            x, y = wf_display_xy(v[:, 0], v[:, 1], wf); bold = level == 0
            ax.plot(x, y, color='k', lw=2.0 if bold else 1.0, path_effects=halo(3.4 if bold else 2.4), zorder=4)
            if not label: continue
            ax.text(x[len(x)//2], y[len(y)//2], f'{level:g}°', fontsize=6.2, ha='center', va='center',
                    bbox=dict(fc='w', ec='none', alpha=.85, pad=0.4), zorder=8)
        ax.plot(cx+r*np.cos(th), cy+r*np.sin(th), color='0.12', lw=1.0, zorder=6)
        ax.set_xlim(cx-r-6, cx+r+6); ax.set_ylim(cy+r+6, cy-r-6); ax.set_aspect('equal'); ax.axis('off')
        sm = mpl.cm.ScalarMappable(norm=mpl.colors.Normalize(*lim), cmap=cmap)
        if name == 'elevation':
            cax = ax.inset_axes([-0.13, 0.22, 0.04, 0.56]); cb = ax.figure.colorbar(sm, cax=cax)
            cax.yaxis.set_ticks_position('left'); cax.set_title('Elevation (°)', fontsize=7, pad=4)
            x0, y0 = cx-r, cy+r+16
            ax.plot([x0, x0+2*px_mm], [y0, y0], 'k-', lw=2.6, solid_capstyle='butt', clip_on=False)
            ax.text(x0+px_mm, y0-8, '2 mm', ha='center', va='bottom', fontsize=7)
        else:
            cax = ax.inset_axes([0.05, -0.09, 0.90, 0.04])
            cb = ax.figure.colorbar(sm, cax=cax, orientation='horizontal')
            cb.set_label('Azimuth (°)', fontsize=7, labelpad=1)
        cb.set_ticks(m['levels']); cax.tick_params(labelsize=7, length=2)

def draw_registration_check(ts, wf, cal, maps, cfg, path):
    """Check figure (not a paper panel): the widefield contour lines laid on the flat map.

    Left, azimuth; right, elevation. Coloured lines are the flat map's drawn grid. Black
    lines are the widefield contours carried onto the flat map with the fitted placement:
    solid for the image-left half, dashed for the image-right half (mirrored), each
    numbered with the grid line it should fall on. The grey patch is the part of the flat
    map under one half of the window: where the imaged cortex lies within V1."""
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 6.2))
    fp = wf_footprint(cal, wf); a, b = wf['mid']
    left_is = +1 if cfg['WF_IMAGE_LEFT_IS'] == 'left' else -1
    for ax, name, drawn, col in ((axes[0], 'azimuth', ts['DRAWN_AZ'], AZC), (axes[1], 'elevation', ts['DRAWN_EL'], ELC)):
        ax.fill(fp[:, 0], fp[:, 1], color='0.88', zorder=0)
        ax.plot(ts['OUT'][:, 0], ts['OUT'][:, 1], color='0.12', lw=1.6, zorder=6)
        for v, C in drawn.items():
            ax.plot(C[:, 0], C[:, 1], color=col, lw=2.6 if v == 0 else 1.2, zorder=3)
            ax.text(*C[len(C)//2], f'{v}°', fontsize=6.5, color=col, ha='center', va='center',
                    bbox=dict(fc='w', ec='none', alpha=.85, pad=0.4), zorder=5)
        if name == 'azimuth':
            for l, C in ts['NEW'].items(): ax.plot(C[:, 0], C[:, 1], color=col, lw=0.8, ls=(0, (5, 2)), zorder=2)
        for level, v, label in maps[name]['lines']:
            x, y = v[:, 0], v[:, 1]; right = np.median(x-(a*y+b)) > 0
            if right: x, y = wf_reflect(x, y, wf)
            X, Y = wf_to_flatmap(x, y, cal, wf)
            ax.plot(X, Y, color='k', lw=1.3, ls=(0, (4, 2)) if right else '-', zorder=7)
            if not label: continue
            on_map = (level*(left_is*(-1 if right else 1)) if name == 'azimuth' else level)+0.0   # +0.0: no '-0'
            ax.text(X[len(X)//4], Y[len(Y)//4], f'{on_map:g}', fontsize=6, ha='center', va='center',
                    bbox=dict(fc='w', ec='k', lw=0.4, alpha=.9, pad=0.6), zorder=8)
        ax.set_aspect('equal'); ax.axis('off')
        ax.set_title(f"{name}: {abs(cal[name[:2]+'_slope']):.0f}° per sweep, "
                     f"{100*cal['explained_'+name[:2]]:.0f}% of the widefield map explained", fontsize=9)
    fig.legend(handles=[Line2D([], [], color='0.3', lw=1.4, label='flat map: drawn grid (in colour)'),
                        Line2D([], [], color='k', lw=1.3, label='widefield, image-left half'),
                        Line2D([], [], color='k', lw=1.3, ls=(0, (4, 2)), label='widefield, image-right half (mirrored)'),
                        mpl.patches.Patch(color='0.88', label='cortex under one half of the window')],
               loc='lower center', ncol=4, fontsize=7.5, frameon=False)
    fig.suptitle(f"Widefield maps registered on the flat map — window {cal['window_mm']:g} mm, "
                 f"{cal['V1_under_half_window_pct']:.0f}% of V1 under each half", fontsize=10)
    fig.savefig(path, dpi=200, bbox_inches='tight'); plt.close(fig)

def main(cfg=CONFIG):
    """Run the whole analysis and write every output to OUT_DIR.

    Computes the three species' tables, saves the two CSVs, calibrates the
    widefield maps against the flat map, draws and saves the figure and the
    registration check, and writes summary.json. If the mouse TIFFs are missing,
    the mouse is skipped and the bar plots are left out (they need all three
    species); if the widefield file is missing, the widefield maps are left out.
    Returns the summary as a dict."""
    os.makedirs(cfg['OUT_DIR'], exist_ok=True)
    ts = build_treeshrew(cfg); ts_tab = treeshrew_overrep(ts, cfg)
    sm_tab, sm_info = squirrelmonkey(cfg)
    try:
        ms = mouse(cfg); ms_tab = ms['table']
        draw_mouse_check(ms, cfg, f"{cfg['OUT_DIR']}/mouse_origin_check.png")
    except FileNotFoundError:
        print('mouse TIFFs not found — mouse panel skipped'); ms_tab = None
    wf = None
    if os.path.exists(cfg['WF_FILE']):
        wf = load_widefield(cfg); wf_cal, wf_table, wf_strict = fit_widefield(ts, wf, cfg)
        in_screen_deg = cfg['WF_DEGREES_FROM'] == 'screen' and wf_strict is not None
        wf_shown = wf_strict['calibration'] if in_screen_deg else wf_cal      # the scale the drawn maps use
        wf_maps = widefield_maps(wf, wf_shown, ts, cfg)
    else:
        print('widefield file not found — widefield maps skipped')
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
    # widefield maps (if any) on top, in the right-hand columns; flat map and bar plots below
    if wf is not None:
        fig = plt.figure(figsize=(9.9, 10.6))
        outer = fig.add_gridspec(2, 1, height_ratios=[4.8, 5.6], hspace=0.16)
        gw = outer[0].subgridspec(2, 3, width_ratios=[1.9, 1.1, 1.1], hspace=0.2)
        draw_widefield(fig.add_subplot(gw[0, 1:]), fig.add_subplot(gw[1, 1:]), wf, wf_shown, wf_maps, cfg)
        draw_registration_check(ts, wf, wf_shown, wf_maps, cfg, f"{cfg['OUT_DIR']}/widefield_registration_check.png")
    else:
        fig = plt.figure(figsize=(9.9, 5.6)); outer = fig.add_gridspec(1, 1)
    gs = outer[-1].subgridspec(2, 3, width_ratios=[1.9, 1.1, 1.1], height_ratios=[1, 1], wspace=0.35, hspace=0.35)
    draw_flatmap(fig.add_subplot(gs[:, 0]), ts, cfg)
    if ms_tab is not None: draw_bars(fig.add_subplot(gs[0, 1]), fig.add_subplot(gs[0, 2]), res, cfg)
    labels = [a.yaxis.label for a in fig.axes]   # tight bbox otherwise crops labels taller than their axes
    fig.savefig(f"{cfg['OUT_DIR']}/figure5.png", dpi=400, bbox_inches='tight', bbox_extra_artists=labels)
    fig.savefig(f"{cfg['OUT_DIR']}/figure5.svg", bbox_inches='tight', bbox_extra_artists=labels)
    summary = dict(treeshrew_V1_mm2=ts['A_V1'], treeshrew=ts_tab.round(3).to_dict('records'),
                   azimuth_law_used=ts['law_used'], azimuth_law_fit_on_this_svg=ts['law_fit'],
                   azimuth_law_lambda_sweep=ts['law_sweep'], azimuth_law_hm_geometry=ts['law_geom'],
                   squirrelmonkey_measured=sm_info, squirrelmonkey=sm_tab.round(3).to_dict('records'))
    if ms_tab is not None:
        summary.update(mouse_V1_mm2=ms['A_V1'], mouse_extent_az0_az1_el0_el1=ms['extent'],
                       mouse_frame_offset_alt_az_deg=ms['offset'],
                       mouse=ms_tab.round(3).to_dict('records'), mouse_origin_check=ms['check'])
    if wf is not None:
        summary.update(widefield=dict(
            image_left_is=cfg['WF_IMAGE_LEFT_IS'], pixels_per_mm=wf['diam_px']/wf_cal['window_mm'],
            degrees_shown='screen' if in_screen_deg else 'flatmap',
            calibration=wf_cal, calibration_by_window_mm=wf_table,
            **({} if wf_strict is None else dict(sweep_check=wf_strict['sweep_check'],
                                                 calibration_screen_degrees=wf_strict['calibration'])),
            contour_levels_deg={k: m['levels'] for k, m in wf_maps.items()},
            colour_limits_deg={k: m['lim'] for k, m in wf_maps.items()}))
    json.dump(summary, open(f"{cfg['OUT_DIR']}/summary.json", 'w'), indent=1)
    return summary

if __name__ == '__main__':
    if '--extract-widefield' in sys.argv:
        extract_widefield(CONFIG)
    else:
        print(json.dumps(main(), indent=1))
