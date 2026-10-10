Inputs for Fig5_cortex.py.

treeshrew_flatmap.svg        flat-map SVG (V1 outline + Bosking grid + 5 mm scale bar).

zhuang2017_altitude_map.tif  Mouse altitude map, Zhuang et al. 2017 eLife example dataset.
zhuang2017_azimuth_map.tif   Mouse azimuth map, same source.

(no file)                    Squirrel monkey. The measured V1 areas between rings of equal
                             eccentricity come from Table 1 of Adams & Horton 2003 (J Neurosci
                             23:3771) and are typed into the CONFIG block of Fig5_cortex.py
                             (SM_RINGS_DEG, SM_BELT_MM2).

widefield_retinotopy.npz     Tree shrew widefield (GCaMP6s) retinotopy, one session
                             (animal Charlie, session 9, 26 Jan 2021), 540 x 640 pixels:
                               phase_azimuth    response phase (0-1 of a sweep) to a bar
                                                moving right; NaN outside the window
                               phase_elevation  the same for a bar moving up
                               coherence        how repeatable the phase is across trials
                                                (0-1), the lower of the two sweeps
                               midline_xy       points along the midline (pixel x, y)
                               vessels          blood-vessel image of the window
                               sweep_azimuth, sweep_elevation, source   text notes
                             The window (the circular mask, where phase is not NaN) is
                             505 pixels across, which is 8.3 mm: the visible part of
                             the 10 mm chamber.

                             How it was made: cut out of the imaging analysis workspace
                             Retino_Charlie_Fourier_MovingBar_Session9.mat (1 GB, saved by
                             getRetinoFourier.m; fields Azimuth/Elevation.PhaseFullBVFreeMasked,
                             .freqData, .V1border) and Session_9/BV.png, both kept in
                             X:\Papers\Active_vision_ts\Figure5_CorticalRepresentation\Charlie_Data.
                             To remake it:
                               python Python/paper_figures/Fig5_cortex.py --extract-widefield
                             (paths are in WF_SOURCE in the script's CONFIG block; see
                             extract_widefield() for exactly what is kept).
