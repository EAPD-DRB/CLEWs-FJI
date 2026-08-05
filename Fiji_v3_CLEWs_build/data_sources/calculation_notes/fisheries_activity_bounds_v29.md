# Fiji v2.9 aggregate Fisheries activity ceilings

The fix treats official production observations and programme deliverables as
continuing aggregate screening limits. They are not production floors,
biological stocks or legal quotas. `FSHCAPHARV` and `FSHAQHARV` remain annual
mass-link conversions; `FSHFOOD` remains final demand; `IMPFSHFOOD` remains the
open backstop; and both domestic technologies retain `TAL=0`.

Capture uses 12,661 tonnes offshore longline plus 11,000 tonnes coastal
commercial: `0.023661 Mt/year` in `RYT.json/TAU` for 2020–2050. Aquaculture
uses 216.925 tonnes of reported tilapia and freshwater prawn through 2023, then
the detailed Aquaculture Development Plan Table 18 sums of 350, 530, 800,
1,180 and 1,450 tonnes for 2024–2028, holding 1,450 tonnes thereafter.

The active equation is `AAC2_TotalAnnualTechnologyActivityUpperLimit`. Exactly
62 source values changed. Generation, preprocessing and `glpsol --check`
passed; the 178,353 by 137,090 matrix was unchanged. Bounded candidate and
final live CBC solves were optimal at objective 4182.52681513, versus
4170.87205658 for the unchanged control (+0.279432%). Both ceilings bind in all
31 years and the maximum Fisheries balance residual is `4.31e-10` Mt/PJ.

This provides a national screening representation only. Feed, sites, farm
stock, water, wastewater, biological stocks and quotas remain explicit gaps.
