# Water phantom behind the lead wall

This separate case preserves `electron_wall_study` and adds a 10 x 10 x 10 cm
water phantom whose upstream face is 100 cm behind the rear face of the 10 cm
lead block. The phantom is centered on the beam axis and scored in three
dimensions with 1 cm voxels using both `DOSE-EM` and `DOSE`.

The case retains the air dose maps and particle spectra at 10, 20, and 50 cm.
It uses four consecutive FLUKA cycles of 25,000 primaries each (100,000 total)
for independent-cycle uncertainty estimates. The scoring results are
normalized to the existing assumed 20 pC electron pulse.

The source remains the assumed 500 MeV monoenergetic electron beam with a
transverse Gaussian sigma of 1 mm and a 20 pC bunch charge. No angular
divergence is assigned because no source data are available; the input uses
the existing beam direction. The 100 ns temporal FWHM remains integrated,
not time-resolved. These assumptions must not be confused with measurements.

The water score is absorbed dose in water, not ambient dose equivalent or an
effective dose. Review the per-voxel statistical errors and BLCCRE warnings.
This case is not a validated shielding or radiological-safety assessment.

The run `20261009T090627Z_electron_wall_water_TrYgQ1Q5` was stopped on request
after 50,000 primaries in two complete cycles and 15,419 primaries in the
third cycle. It is incomplete; its partial scoring files were not merged, and
no final water-dose result is available. Do not treat those files as results
or resume the run without explicitly checking the saved seeds and cycle state.
