---
title: "Supplementary Material"
subtitle: "Updates to fuel moisture code, spread index and hourly weather variables in the 2025 Canadian Forest Fire Danger Rating System tested across 31 seasons of fire danger trends in the Okanagan basin"
---

Checks of the FWI1987 implementation against the R package cffdrs and the BC Wildfire Service's operational codes, and the effect of the daily summary hour on FWI2025 counts.

# S1 Implementation Checks

Over the Petawawa Research Forest test record, the FWI1987 implementation agreed with the R package cffdrs [@wang2017cffdrs] to 5.4e-13 across all seven components. That was machine precision, because the two were the same arithmetic, so the check confirmed the transcription and not the equations themselves.

At the Okanagan stations, against the FWI1987 codes BC Wildfire Service computed at the time, the weighted mean correlation over 18,178 station-days was 0.986. By component it ranged from 0.952 for the Drought Code to 0.998 for the Initial Spread Index. The one large disagreement was a mean absolute bias of 165 units in the Drought Code and 10.7 in the Buildup Index computed partly from it. No other component had a mean absolute bias above 1.8 units. BC Wildfire Service overwintered the Drought Code, keeping the previous autumn's value as the spring starting value, whereas this study restarted it at 15 on 1 April. The difference was one of convention, in the known direction that a restarted Drought Code is lower than an overwintered one. It entered every absolute Drought Code and Buildup Index value reported in the article but no comparison between the three series, which all restarted identically.

The Fine Fuel Moisture Code, on which the version comparison principally depended, correlated 0.996 with the operational value.

Timestamps in the data mart were in Pacific Standard Time, UTC-8, year round. This showed in the daily FWI1987 codes, computed from the 13:00 local daylight time observation, which appeared at hour 12 in 39,095 records and at other hours in 0.

# S2 Summary Hour

Over the study record, taking the daily maximum of the 24 hourly values instead of the value at 16:00 Local Standard Time raised every count in both FWI2025 series. On hourly observation, days above a Fine Fuel Moisture Code of 91 rose from 61.9 to 72.7 per season. Days above a Fire Weather Index of 19 rose from 77.8 to 92.7. On the 13:00 observation the same counts rose from 55.4 to 56.3 and from 85.4 to 86.5. The daily maximum was not the primary summary, because part of the rise came from taking the largest of 24 values and not from the System.

# References

