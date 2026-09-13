## ---------------------------------------------------------------------------
## Statistical functions for forest-fire-index-trends.
##
## Written 2026-08-15. These are sourced by the manuscript and called from
## visible chunks, so that the manuscript shows what is being done while the
## machinery that does it is saved, reviewable and testable in one place.
##
## Three things are done here and each carries a decision that has to be stated
## wherever a number from it is reported.
##
## Trend estimation. The estimator is the Theil-Sen slope, the median of all
## pairwise slopes, chosen because seasonal counts of extreme days are skewed and
## a least squares slope on them is pulled by single seasons. Significance is
## Mann-Kendall with the Hamed and Rao (1998) variance correction, which inflates
## the variance of the S statistic by the autocorrelation actually present in the
## series rather than assuming independence. Serial correlation in seasonal fire
## danger is real and untreated Mann-Kendall over-rejects in its presence, so the
## uncorrected test is reported alongside only to show the size of the effect.
##
## Slope differences between series. The three series are computed from one
## weather record, so they are strongly dependent and a two-sample test on their
## slopes is wrong. The difference is bootstrapped by resampling whole seasons
## with replacement, recomputing both slopes on the same resampled seasons each
## time. The pairing is preserved by construction, so the interval is on the
## difference and not on two separately noisy slopes.
##
## Multiple testing. A metric family is corrected within each series by the
## Benjamini and Hochberg (1995) false discovery rate procedure. The family is
## declared at the call site, not here, because what counts as one family is a
## judgement about the question and not about the arithmetic.
## ---------------------------------------------------------------------------

# Packages are loaded once by the manuscript setup chunk (easypackages::packages).

## Theil-Sen slope with a Mann-Kendall test corrected for serial correlation.
##
## Returns one row: the slope, its bootstrap interval, the corrected and
## uncorrected p values, Kendall's tau, and the effective sample size ratio that
## the correction used. A series shorter than `min_n` returns NA rather than a
## number, because a slope over eight seasons is not an estimate.
## Moving-block bootstrap indices over an ordered season sequence.
##
## Resampling single seasons keeps the pairing between series that share a
## weather record but discards serial correlation within a series. Blocks of
## consecutive seasons keep it (Kunsch 1989). Block length is the cube root of
## the number of seasons, rounded up and at least two, which grows with the
## record but more slowly than it, as Kunsch's consistency condition requires.
## Blocks are drawn from the seasons in order of occurrence, so a gap in the
## record falls inside a block rather than being closed up.
block_length <- function(n) max(2L, as.integer(ceiling(n^(1/3))))
block_indices <- function(n, l = block_length(n)) {
  starts <- sample.int(n - l + 1L, ceiling(n / l), replace = TRUE)
  idx <- as.vector(vapply(starts, function(s) s:(s + l - 1L), integer(l)))
  idx[seq_len(n)]
}

trend_test <- function(year, value, min_n = 15, n_boot = 2000, seed = 20260815) {
  ok <- is.finite(year) & is.finite(value)
  year <- year[ok]; value <- value[ok]
  o <- order(year); year <- year[o]; value <- value[o]
  n <- length(value)

  na_row <- data.frame(n = n, slope = NA_real_, lower = NA_real_, upper = NA_real_,
                       p_corrected = NA_real_, p_uncorrected = NA_real_,
                       tau = NA_real_, n_over_nstar = NA_real_)
  if (n < min_n || length(unique(value)) < 3) return(na_row)

  mk <- tryCatch(modifiedmk::mmkh(as.vector(value)), error = function(e) NULL)
  if (is.null(mk)) return(na_row)

  ## Theil-Sen on the actual years, so a gap in the season sequence is honoured
  ## rather than treated as a step of one.
  slope <- theil_sen(year, value)

  set.seed(seed)
  bs <- vapply(seq_len(n_boot), function(i) {
    k <- block_indices(n)
    theil_sen(year[k], value[k])
  }, numeric(1))

  data.frame(
    n = n,
    slope = slope,
    lower = unname(quantile(bs, 0.025, na.rm = TRUE)),
    upper = unname(quantile(bs, 0.975, na.rm = TRUE)),
    p_corrected = unname(mk["new P-value"]),
    p_uncorrected = unname(mk["old P.value"]),
    tau = unname(mk["Tau"]),
    n_over_nstar = unname(mk["N/N*"])
  )
}

## Median of all pairwise slopes. Returns NA when fewer than two distinct x
## values survive, which happens inside a bootstrap resample.
##
## Written with outer() rather than an index expansion because the bootstraps
## above call it several hundred thousand times and the allocation cost of
## building index vectors on every call dominated the runtime.
theil_sen <- function(x, y) {
  n <- length(x)
  if (n < 3) return(NA_real_)
  dx <- outer(x, x, "-")
  dy <- outer(y, y, "-")
  keep <- lower.tri(dx) & dx != 0
  if (!any(keep)) return(NA_real_)
  median(dy[keep] / dx[keep])
}

## Paired bootstrap on the difference between two series' Theil-Sen slopes.
##
## `wide` must hold one row per season with columns `year`, `a` and `b`. Seasons
## are resampled whole, so both slopes are recomputed on the same seasons in
## every replicate and the dependence between the series is carried through.
slope_difference <- function(wide, n_boot = 4000, seed = 20260815) {
  wide <- wide[is.finite(wide$a) & is.finite(wide$b), ]
  n <- nrow(wide)
  if (n < 15) {
    return(data.frame(n = n, slope_a = NA_real_, slope_b = NA_real_,
                      difference = NA_real_, lower = NA_real_, upper = NA_real_,
                      p_two_sided = NA_real_))
  }
  sa <- theil_sen(wide$year, wide$a)
  sb <- theil_sen(wide$year, wide$b)

  wide <- wide[order(wide$year), ]
  set.seed(seed)
  d <- vapply(seq_len(n_boot), function(i) {
    k <- block_indices(n)
    theil_sen(wide$year[k], wide$b[k]) - theil_sen(wide$year[k], wide$a[k])
  }, numeric(1))
  d <- d[is.finite(d)]

  ## Two sided bootstrap p value computed under the null hypothesis, following
  ## the first guideline of Hall and Wilson (1991): the resampled differences
  ## are centred on the observed difference, and p is the share whose distance
  ## from it is at least as large as the observed difference is from zero,
  ## floored at the resolution the number of replicates can resolve.
  obs <- sb - sa
  p <- mean(abs(d - obs) >= abs(obs))
  data.frame(
    n = n, slope_a = sa, slope_b = sb, difference = sb - sa,
    lower = unname(quantile(d, 0.025)), upper = unname(quantile(d, 0.975)),
    p_two_sided = max(p, 1 / length(d))
  )
}

## Benjamini and Hochberg false discovery rate over a declared family.
fdr <- function(p) p.adjust(p, method = "BH")

## Negative binomial count model of daily ignitions on daily fire danger.
##
## Season is a factor, so the danger coefficient is identified only from
## day-to-day variation inside a season. That is deliberate. Reporting
## completeness and cause coding both change between seasons and neither changes
## within one, so a between-season contrast would confound the danger effect with
## the record keeping, and a within-season contrast cannot.
##
## Day of year enters as a pair of annual harmonics, which absorbs the seasonal
## march of both fuel dryness and human activity without spending a parameter per
## day.
ignition_model <- function(d, response, danger, extra = NULL) {
  d <- d[is.finite(d[[danger]]) & is.finite(d[[response]]), ]
  d$.y <- d[[response]]
  d$.x <- d[[danger]]
  d$.s1 <- sin(2 * pi * d$doy / 365.25); d$.c1 <- cos(2 * pi * d$doy / 365.25)
  d$.s2 <- sin(4 * pi * d$doy / 365.25); d$.c2 <- cos(4 * pi * d$doy / 365.25)
  d$.year <- factor(d$year)
  f <- ".y ~ .x + .s1 + .c1 + .s2 + .c2 + .year"
  if (!is.null(extra)) f <- paste(f, "+", extra)
  MASS::glm.nb(as.formula(f), data = d, control = glm.control(maxit = 100))
}

## Out of sample predictive skill, by leaving one season out at a time.
##
## Returns the mean held-out log likelihood per day under the negative binomial
## fitted without that season. Comparing series on held-out likelihood rather
## than on in-sample fit is the point: three series computed from one weather
## record will all fit, and the question is which predicts.
loso_skill <- function(d, response, danger, extra = "n_stations") {
  years <- sort(unique(d$year))
  ll <- numeric(0)
  ## A coefficient can come back NA when its term is collinear inside a training
  ## fold; treating it as zero keeps the fold rather than dropping it silently.
  cf <- function(co, nm) if (nm %in% names(co) && is.finite(co[[nm]])) co[[nm]] else 0

  for (y in years) {
    train <- d[d$year != y, ]
    test <- d[d$year == y, ]
    if (nrow(test) < 30 || length(unique(train$year)) < 5) next
    m <- tryCatch(ignition_model(train, response, danger, extra = extra),
                  error = function(e) NULL)
    if (is.null(m)) next
    ## The held-out season has no fitted year effect, so prediction uses the mean
    ## of the fitted year effects: the model is asked for a typical season, which
    ## is what a forecast for an unobserved season can know.
    co <- coef(m)
    yr_terms <- co[grepl("^\\.year", names(co))]
    eta <- cf(co, "(Intercept)") + mean(c(0, yr_terms), na.rm = TRUE) +
      cf(co, ".x") * test[[danger]] +
      cf(co, ".s1") * sin(2 * pi * test$doy / 365.25) +
      cf(co, ".c1") * cos(2 * pi * test$doy / 365.25) +
      cf(co, ".s2") * sin(4 * pi * test$doy / 365.25) +
      cf(co, ".c2") * cos(4 * pi * test$doy / 365.25)
    if (!is.null(extra) && extra == "n_stations")
      eta <- eta + cf(co, "n_stations") * test$n_stations
    mu <- exp(eta)
    ll <- c(ll, dnbinom(test[[response]], size = m$theta, mu = mu, log = TRUE))
  }
  if (!length(ll)) return(data.frame(n_days = 0L, mean_loglik = NA_real_,
                                     total_loglik = NA_real_))
  data.frame(n_days = length(ll), mean_loglik = mean(ll), total_loglik = sum(ll))
}

## Minimum trend a window of n seasons can detect, at the observed noise level.
##
## Solves for the slope at which a Mann-Kendall test would reject at alpha with
## power 1 - beta, given the residual standard deviation of the series about its
## own Theil-Sen line. This is the quantitative form of what a 35 season window
## cannot resolve, and it is computed rather than asserted.
minimum_detectable_trend <- function(year, value, alpha = 0.05, power = 0.8) {
  ok <- is.finite(year) & is.finite(value)
  year <- year[ok]; value <- value[ok]
  n <- length(value)
  if (n < 10) return(NA_real_)
  s <- theil_sen(year, value)
  resid <- value - (s * (year - mean(year)) + median(value - s * (year - mean(year))))
  sigma <- sd(resid)
  ## Standard error of an ordinary least squares slope is the relevant scale;
  ## Theil-Sen is about 93 per cent as efficient as least squares under normal
  ## errors, so the result is divided by that efficiency to stay honest.
  se <- sigma / sqrt(sum((year - mean(year))^2))
  ## Serial correlation inflates the standard error of a trend by
  ## sqrt((1 + phi) / (1 - phi)) for first-order autoregressive noise with lag-one
  ## autocorrelation phi (Weatherhead et al. 1998). phi is estimated from the
  ## residuals in season order and bounded to [0, 0.9], so that a negative sample
  ## estimate cannot shrink the detectable trend below the independent case.
  r <- resid[order(year)]
  phi <- if (length(r) > 2) suppressWarnings(stats::cor(r[-1], r[-length(r)])) else 0
  phi <- min(max(ifelse(is.finite(phi), phi, 0), 0), 0.9)
  (qnorm(1 - alpha / 2) + qnorm(power)) * se * sqrt((1 + phi) / (1 - phi)) / 0.93
}


## Percentile exceedance counts with the in-base bootstrap correction of Zhang,
## Hegerl, Zwiers and Kenyon (2005).
##
## A threshold estimated from a fixed base period carries sampling error that
## biases counts low inside the base period and high outside it, which a trend
## fitted across the boundary reads as a trend. Zhang et al. removed the jump by
## estimating the count for each in-base year from thresholds that exclude that
## year. For each in-base season j, the base sample is rebuilt with season j
## removed and another base season i duplicated in its place, the threshold is
## re-estimated, and the count in season j is taken; the count for j is the mean
## over every i other than j. Out-of-base seasons use the threshold from the whole
## base period. Zhang et al. estimated calendar-day thresholds; here, as in the
## uncorrected metric, the threshold is estimated from all days of the season
## pooled, so the procedure is adapted to a seasonal rather than daily threshold.
## Quantiles use type 7, the numpy default the uncorrected metric used, and the
## comparison is strictly greater than, as in the uncorrected metric.
inbase_corrected_counts <- function(daily, series, probs = c(90, 95),
                                    reference = c(1991, 2020), min_ref = 500) {
  col <- paste0(series, "_fwi")
  out <- list()
  for (stn in unique(daily$station_name)) {
    g <- daily[daily$station_name == stn & is.finite(daily[[col]]), c("year", col)]
    names(g)[2] <- "v"
    by_year <- split(g$v, g$year)
    years <- as.integer(names(by_year))
    base <- years[years >= reference[1] & years <= reference[2]]
    base_vals <- unlist(by_year[as.character(base)], use.names = FALSE)
    for (p in probs) {
      if (length(base_vals) < min_ref) {
        cnt <- rep(NA_real_, length(years))
      } else {
        full <- unname(stats::quantile(base_vals, p / 100, type = 7))
        cnt <- vapply(years, function(y) {
          v <- by_year[[as.character(y)]]
          if (!(y %in% base)) return(sum(v > full))
          others <- setdiff(base, y)
          without <- unlist(by_year[as.character(others)], use.names = FALSE)
          mean(vapply(others, function(i) {
            thr <- stats::quantile(c(without, by_year[[as.character(i)]]), p / 100,
                                   type = 7, names = FALSE)
            sum(v > thr)
          }, numeric(1)))
        }, numeric(1))
      }
      out[[length(out) + 1]] <- data.frame(station_name = stn, series = series,
                                           year = years, prob = p, count = cnt)
    }
  }
  do.call(rbind, out)
}
