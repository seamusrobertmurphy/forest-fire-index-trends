# Synthesis

Written 2026-10-13 from the screening table `02.inputs/derived/review-records.csv` and the
source notes under `04.references/review/notes/`, question by question, in the four parts
the library protocol asks for. Every quotation below was checked letter for letter against
the text named in its note, and a paper read from its abstract alone is marked so. Of the
1,840 records retrieved, 1,278 were unique, 956 were excluded with a code, 37 stayed
undecided for want of an abstract, 285 were kept, and 53 were read in full or to the limit
the publisher allowed, 32 of them end to end.

## Question 1

What trends in fire danger from the Fire Weather Index System have been reported for
British Columbia, the southern interior or the Okanagan, and for Canada, with which
estimator, period, autocorrelation treatment and multiple-testing correction?

**Established methods.** The pairing the manuscript adopted, the Theil-Sen slope with the
Mann-Kendall test, is the pairing the Canadian fire literature uses, but mostly on fire
counts rather than on danger. Aftergood and Flannigan (2022) estimated lightning fire
trends across western Canada 1981 to 2018 with "the nonparametric block bootstrapping and
bias corrected prewhitening method and a modified Mann-Kendall test to account for type 1
errors and serial correlation in the data (Hamed, 2009) using the modifiedmk package"
(manuscript p. 12), which is the same package and correction this study used. Ahmed and
Hassan (2023) and Dastour and others (2024, abstract only) ran Mann-Kendall with Sen's
slope on Alberta fire counts and season length without stating an autocorrelation
treatment or a multiple-testing correction. For danger itself the Canadian estimates are
gridded and parametric. Jain and others (2017), already cited, used Theil-Sen and
Mann-Kendall with field significance on reanalysis. Queen and others (2025) fitted least
squares slopes to ERA5 May to October mean Fire Weather Index over western North America
and attributed them by optimal fingerprinting, finding "Over the 1951–2021 time window,
d4PDF-G results indicate an anthropogenic contribution of 103% and a natural contribution
of −33%" (p. 4), with the ERA5 series falling into the 1980s and rising after, so the
linear slope depends on its endpoints. Barnes and others (2025, abstract only) regressed
accumulated Daily Severity Rating on global mean temperature by ecozone. Hubnerova,
Esterby and Taylor (2020, abstract only) fitted generalised extreme value distributions
with linear trends in location and scale to monthly maximum Fire Weather Index at "861
stations in British Columbia, Canada" over 1970 to 2018, and Németh and others (2020,
abstract only) built the bootstrap-corrected likelihood ratio test for that model on the
same stations. Neither abstract gives a slope, a region below the province, an
autocorrelation treatment or a correction for 861 tests.

**Known confounds.** Large interannual variability, which Amiro and others (2004, abstract
only) gave as the reason that "Most FWI System parameters did not show trends over the
41-year period"; endpoint sensitivity in a series that fell then rose (Queen and others
2025); the oscillation phases at the ends of the window, which the manuscript already
states; and the inhomogeneity of the weather record itself, treated under Question 2.

**Prior effect sizes.** No study reports an observed Fire Weather Index slope for the
Okanagan or the southern interior. The only Okanagan station test found is Spittlehouse
and Dymond (2022), who reported "no significant (p<0.2) increasing or decreasing trends in
the seasonal precipitation or air temperature over the 1984 to 2016 period at Penticton
Airport and P1" (manuscript p. 9), with a historic fire season of 209, 135 and 107 days
by elevation and projections of 14 to 32 more days by the 2050s. Nitschke and Innes (2008,
abstract only), already cited, is a projection, "a 30% increase in fire season length was
modelled to occur by 2070". Wang and others (2025, abstract only) found "About 6% (0.54 to
14.64%) of the modeled areas show significant increases in the number of days conducive
to high-severity burning during 1981 to 2020". Ahmed and Hassan (2023) found Alberta
season length "significantly longer in three ecoregions (LBH, NM, and KU) ... with the
rates ranging from 1.1 to 1.7 day/year" (p. 12). Boulanger and others (2026, abstract
only) found observed spread days per fire "more than doubled (+138%)" over 2002 to 2024.

**Where the study sits.** New work for the region. It is the first station-based
Theil-Sen estimate of Fire Weather Index trends for the Okanagan, and the first anywhere
in Canada to pair that estimator with the Hamed and Rao correction, a false discovery rate
correction and a block bootstrap on danger metrics rather than on fire counts. The
Discussion can compare its null slopes with Spittlehouse and Dymond's null weather trends
at Penticton over 1984 to 2016 and with the provincial GEV result of Hubnerova and others,
once that chapter is read in full.

## Question 2

What is known about how the weather input, hourly against once daily, and a change of
version or of record homogeneity, move the level, the tail and the trend of a fire danger
index?

**Established methods.** Three strands. First, input timing studies compare one index
under two inputs on the same days. Rodell and others (2024) and Herrera and others (2013),
already cited, did this for hourly against daily and instantaneous against mean daily
input. Matteo and others (2025) did it for the trend, computing the global 1980 to 2023
trend in days above the 95th percentile of the Fire Weather Index from noon weather and
from four daily aggregate approximations, and testing the difference series with the
Hamed and Rao modified Mann-Kendall test. Campos and others (2026), Fox-Hughes (2011,
abstract only), Plucinski and others (2020, abstract only) and Perello and others (2025)
compared hourly or sub-daily indices with daily ones for level, timing of the peak and
skill against fire activity. Second, version comparisons run two algorithms on one input.
Quilcaille and others (2023) ran the default Fire Weather Index algorithm against one
using mean rather than minimum relative humidity and reported the level shift and its
constancy over time. The 2016 update to the United States National Fire Danger Rating
System is the only other operational version change found, and no paper evaluating it was
retrieved. Third, homogeneity studies treat a change in the observing system as a break to
be detected and adjusted before trending, the climate-science approach the manuscript
already cites through Vose and others (2012) and Santer and others (2000). Tsinko (2016)
applied it to the Fire Weather Index System itself at Canadian stations with Sen slopes,
Mann-Kendall and a Benjamini-Hochberg correction, and Wan and others (2010) to Canadian
wind, with a linear trend and lag-one autoregression fitted jointly.

**Known confounds.** The Drought Code startup, since McElhinny and others (2020) found
"there can be a significant difference in DC (and therefore also BUI, FWI, and DSR)
values, particularly at the beginning of the fire season, depending on which procedure is
employed" (p. 1830), which this study holds constant across its three series by starting
every series on 1 April. The humidity sensor change, since van Wijngaarden and Vincent
(2005, abstract only) found "the replacement of the psychrometer by the dewcel has
produced a decreasing step in relative humidity at a number of stations" and that "the
relative humidity still decreased by several percent in the spring during 1953–2003 in
western Canada"; the BC Wildfire Service record used here postdates the dewcel but its own
sensor history is not documented and is a stated limitation. Anemometer changes, since Wan
and others (2010) found that raw and homogenised wind trends in "the western mountainous
regions of Canada" were "often of the opposite signs".

**Prior effect sizes.** For input timing on the trend, Matteo and others (2025) found
"none of the daily approximations (C1–C4; see Table 1) preserve the C0 trend exactly, and
all combinations overestimate the trend, ranging from 2.86 to 3.06 days per decade"
against 2.65 days per decade from noon weather, an excess of 0.22 to 0.39 days per decade
that was significant on the difference series. That is the one measured effect of input
timing on a slope, and it is about a tenth of the 16.8 days over the window, or about 4.9
days per decade, that this record could resolve. For input timing on the level and tail,
Campos and others (2026) found hourly 500 m simulations against the daily product gave "a
positive BIAS of 3.02 and 4.53" at two Portuguese sites and "− 5.71" in Galicia (p. 17);
Mirones and others (2026) found a daily aggregate proxy "overestimates spell lengths in
Galicia and Portugal (by up to 4 d)" (p. 3424); Fox-Hughes (2011) found at Hobart "only
one-half of diurnal FFDI peaks over a critical warning level occur at 1500 LT"; Benoit
and others (2026) found that sampling hourly ERA5 at legal rather than solar noon produced
"discontinuities between time zones (up to +3.4 in July west of Alberta ...)" (p. 6002).
For a version change on the level, Quilcaille and others (2023) found "the FWI is reduced
by about −33 % (June) above 20° N" (p. 2162) under mean humidity and that "the reduction
... is roughly identical during the fire seasons across the planet, be it over 1994–2014
or 2081–2100" (p. 2164), a level shift that left the relative change alone, which is the
same shape as this study's level-not-slope result. For homogeneity, Tsinko (2016) found
"Up to 50% of the stations experienced a change in linear trend significance in P90 of
the code values, up to 40% in IQR and up to 20% in median values" (p. 48), and Tsinko and
others (2018), already cited, gave the 0.7 to 8.4 per cent level change. For the hourly
quantity itself, Luo and others (2026) found from hourly reanalysis and a random forest of
hourly burning that "annual potential burning hours were estimated to rise 36% over
1975–2024" across North America, with boreal western Canada rising by 4 to 5 hours per
year over 66 to 89 per cent of its burnable area, which is the nearest published
counterpart to the burning window this study reports from FWI2025.

**Where the study sits.** An extension of the input-timing strand to the operational
system that now runs hourly, and the first to put a version change and an input change of
the same index side by side on one observed record. The expectation table's statement that
input resolution moves only the count must be loosened, because Matteo and others measured
a slope effect, and the Discussion should say that the measured slope effect of input
timing is an order of magnitude below this record's resolution.

## Question 3

How have daily fire occurrence counts been modelled against fire danger in Canada and
British Columbia, with what distribution, seasonal terms and validation, and has the
danger to occurrence relationship been tested for change over time?

**Established methods.** Canadian practice models presence, not counts. Nadeem and
others (2019, abstract only) built "three models of daily human- and lightning-caused
fire occurrence ... using a lasso-logistic framework" across British Columbia with areas
under the curve above 0.9, and Taylor and others (2022, abstract only) linked such models
to initial attack demand. Magnussen and Taylor (2012), already cited, used logistic
regression with leave-one-year-out validation and reported that "Because the influence of
the explanatory variables in the models varied from year to year, model coefficients were
estimated for each year". Count models with overdispersion appear in Hanes and others
(2020), a zero-inflated Poisson of daily spring counts on a Fine Fuel Moisture Code
polynomial chosen after "Over-dispersion was observed in the fitted Poisson Generalized
Linear Models (GLM) in all regions" (p. 5), and in Boateng and Granville (2026), negative
binomial monthly counts with month indicators tested on a held-out 2011 to 2023, whose
dispersion estimates ran from 29 to 194. Plucinski and others (2014, abstract only)
remains the only daily negative binomial precedent, in Western Australia, "evaluated using
data from an independent year". Phelps and Woolford (2021, abstracts only) set out the
evaluation guidelines, including "choosing a testing dataset" and "using temporal and
spatial visualisations to assess model performance", and found logistic generalised
additive models matched machine learning. Coogan and others (2025) fitted a quadratic in
day of year to lightning ignition efficiency and found the peak "81 flashes per fire on 09
August" (p. 7), which supports a seasonal term beside danger.

**Known confounds.** Reporting completeness and cause coding between seasons, which this
study's season fixed effect absorbs; the absence of a strike record, which Wotton and
Martell (2005), already cited, showed matters; population and fuel change, for which Hanes
and others (2020) chose a 40 year window "to reduce non-stationarity in the records due to
population fluctuations and potential fuel type changes" (p. 4).

**Prior effect sizes.** One Canadian study tested change over time in the danger to
occurrence relationship. Granville and others (2022) fitted period by intensity
interactions in a conditional logistic model of industrial fires in Ontario 1976 to 2019
and found "insufficient evidence to justify the inclusion of interaction terms for low
HFI (p-value > 0.3, Table 3). That is, it was OK to consider a single term for low HFI to
represent this linear relationship for all three considered time periods" (pp. 232 to
233), with a difference at high intensity only against the period before 1989. Woolford
and others (2014, abstract only), already cited, found "statistically significant
increases in lightning-caused fire risk between 1963 and 2009" in northwestern Ontario
"associated with temperature and fire danger rating index anomalies", a trend in
occurrence rather than a changed slope. Hanes and others (2025) found Montane Cordillera
large lightning fires rising at "β = 0.50 fires·yr-1" and that "human-caused fires, which
were previously detected as decreasing in annual area burned, have now been increasing
with high confidence since the mid-2000's", without a fire weather term.

**Where the study sits.** The negative binomial daily count model with season fixed
effects and two harmonics has no Canadian precedent and is reported as adopted from
Plucinski and others (2014) and Martell and others (1989); the stationarity interaction is
a replication, in count form, of the period interaction test of Granville and others
(2022), and the null result here agrees with their null at low intensity.

## Question 4

Has FWI2025 been evaluated, compared with FWI1987 on an observed record, or used in a trend
or occurrence study since its release, and has any study separated the version change
from the input change?

**Established methods.** None. The search term returned one record, an Icelandic thesis
excluded for language. OpenAlex lists two works citing the 2025 report. Wilkinson and
others (2026) name the update three times and compare nothing, writing that their daily
code "will serve as the methodological basis for the hourly PMC that is to be
incorporated into the next-generation Canadian Forest Fire Danger Rating System (CFFDRS)
FWI2025". The Russian review of 2026 cites the report in one sentence on the need for new
generation models and never names FWI2025. Han and others (2026), reviewing five national
systems in April 2026, wrote that "CFFDRS and KFDRS primarily rely on daily index-based
predictions". Benoit and others (2026), building a daily gridded Canadian dataset from
hourly ERA5, followed Van Wagner (1987) and did not name the update. The Canadian Forest
Service repository's February 2026 notice says agencies "can implement FWI2025 in parallel
with FWI1987 to take advantage of its new capabilities and help us with ongoing testing",
that "Work is ongoing to quantify the differences between FWI2025 and FWI1987 in relation
to the effect on fire behaviour using the current FBP System (FBP1992)", and that
"FWI2025 should not be used as an input to the FBP System".

**Known confounds.** The search reached only indexed and web-visible work; a provincial
agency comparison run internally would not appear.

**Prior effect sizes.** None published.

**Where the study sits.** New work. The sentence "no study has separated them" stands on
the full texts of every record that cites or names the update, and the Methods should
state the search that supports it. The Canadian Forest Service's own quantification is
announced as ongoing and concerns fire behaviour, not danger trends.
