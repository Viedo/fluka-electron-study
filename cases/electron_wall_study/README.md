# Multi-cycle study of radiation behind a lead wall

This separate technical case preserves `electron_wall` and adds:

- four consecutive FLUKA cycles of 25,000 primaries each, for 100,000 total;
- USRBIN dose maps at 10, 20, and 50 cm behind the 10 cm lead block;
- photon spectra at all three distances;
- neutron, electron, and positron spectra in the 20 cm detector slab.
- an explicit dry-air mixture rather than relying on FLUKA's automatic
  material-name guess (mass fractions: C 0.0124%, N 75.5267%, O 23.1781%,
  Ar 1.2827%; density 1.205e-3 g/cm3).

The repeated cycles use successive random-number states managed by `rfluka`.
FLUKA's `usbsuw` and `ustsuw` utilities combine the cycle scoring and estimate
bin-wise statistical errors. A single cycle cannot provide those independent
cycle statistics.

The beam remains an assumed monoenergetic 500 MeV electron pencil with
transverse Gaussian sigma 1 mm. The source bunch charge is 20 pC (about
`1.2483e8` electrons); the 100 ns temporal FWHM is not transported as a time
distribution. Scored results are normalized to one 20 pC bunch by the analysis
script.

The lead block, air surroundings, detector dimensions, and beam centering are
technical assumptions, not measured experimental inputs. This case is not
validated for shielding design or radiological safety. Review the reported
BLCCRE least-squares-fit warnings and the per-bin statistical errors before
interpreting results.
