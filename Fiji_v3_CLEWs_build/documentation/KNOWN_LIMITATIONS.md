# Known limitations

The authoritative machine-readable list is `data_sources/GAPS.csv`.

Resident crop and fish demand uses recent FAOSTAT food availability, not a
nutrition requirement. Per-capita food, import floors and export commitments
remain constant and scale only with population. Income, prices, preferences,
substitution, bilateral markets and foreign demand are absent. Tourism is
excluded. Crop export weights cannot fully separate re-exports; product-to-crop
conversions are incomplete.

Fish is one market-weight commodity. Species, preservation state, edible
fraction, processing loss and by-products are absent. Retained imports are a
same-year HS accounting proxy. The model lacks stock-linked catch limits and
explicit aquaculture feed/FCR, land, water and wastewater constraints.
Aggregate activity ceilings now proxy those missing restrictions and prevent
unlimited substitution between capture and aquaculture. The capture ceiling is
an observed-boundary proxy, not a quota; the aquaculture ceiling is a
conservative programme envelope, not a site-capacity assessment. The resulting
split is appropriate for screening only and must not be treated as a species,
fleet or farm forecast.

Inherited limitations remain: incomplete original lineage for unchanged v2.5
values, proxy energy costs/efficiencies, fixed land stocks, simplified
hydrology and a national median precipitation pathway without interannual,
cyclone or subnational detail.

The case is suitable for exploratory annual national demand, accounting and
import-resilience diagnostics—not official inventories, procurement,
nutrition planning, operational reliability or unqualified policy ranking.
