# Freeze configuration for the duration of the forward test

The two-week paper forward test runs with configuration frozen at start (recorded via the config_snapshots table); mid-test changes are limited to bug fixes. Without the freeze, threshold or weight tuning mid-test would silently invalidate the metric series — every reported number would be an average over different strategies, making win rate, average RR, and expectancy uninterpretable. Tuning happens once, after the test, in the T8.4 review.
