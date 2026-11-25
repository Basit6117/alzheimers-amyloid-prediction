# Model Card: amyloid_svm_champion_9306

## Artifact

- File inspected: `model/amyloid_svm_champion_9306.joblib`
- Object: `sklearn.pipeline.Pipeline`
- Pipeline steps: `preprocess` (`sklearn.compose.ColumnTransformer`), then `clf` (`sklearn.svm.SVC`)
- `classes_`: `[0, 1]`; `predict_proba` is available.
- Class `0` is Amyloid Negative. Class `1` is Amyloid Positive, the model's
  proxy for Alzheimer's risk over the next 20 years.

## Required input order

The backend must create model input in exactly this artifact `feature_names_in_` order:

| Position | Feature |
| --- | --- |
| 1 | `pT217_F` |
| 2 | `GFAP_to_AB_ratio` |
| 3 | `pT217_to_AB_ratio` |
| 4 | `AB42_AB40_F` |
| 5 | `AGE` |
| 6 | `APOE4` |
| 7 | `SEX` |

The processed training cohort (`notebooks/data/processed/blood_only.csv`, 238 rows)
provides these observed bounds. They are input-validation bounds for this
application, not asserted clinical reference intervals.

| Feature | Unit/coding evidenced by supplied data | Observed training-cohort range |
| --- | --- | --- |
| `pT217_F` | Unit not documented in the supplied files | `0.030`–`1.938` |
| `GFAP_to_AB_ratio` | Derived as `GFAP_Q / (AB42_AB40_F + 1e-6)`; unit not documented | `301.322009`–`5689.488910` |
| `pT217_to_AB_ratio` | Derived as `pT217_F / (AB42_AB40_F + 1e-6)`; unit not documented | `0.306289`–`15.387183` |
| `AB42_AB40_F` | Aβ42/Aβ40 ratio | `0.0615`–`0.1323` |
| `AGE` | years | `51.014374`–`91.137577` |
| `APOE4` | binary APOE ε4 carrier indicator: `0` non-carrier, `1` carrier | `0`, `1` |
| `SEX` | binary code: `0` female, `1` male | `0`, `1` |

## Dashboard raw inputs

The dashboard must collect only these direct values, in this order:
`pT217_F`, `AB42_AB40_F`, `GFAP_Q`, `APOE4`, `AGE`, `SEX`.

`GFAP_Q` is an observed raw biomarker column with an observed training-cohort
range of `33.1`-`430.7`; its unit is not documented in the supplied files.
The ratio columns are never entered by a user.

## Feature engineering and preprocessing

The two ratio features were engineered outside the saved pipeline during
training, before the model received its seven input columns:

- `GFAP_to_AB_ratio = GFAP_Q / (AB42_AB40_F + 1e-6)`
- `pT217_to_AB_ratio = pT217_F / (AB42_AB40_F + 1e-6)`

This dashboard accepts raw `GFAP_Q` and repeats the exact formulas above in the
prediction backend before every prediction. It then creates the seven-column
model input in the artifact's required order. It does not ask a user to perform
either calculation.

All fitted preprocessing is inside the saved pipeline. The backend must pass a complete, numeric, seven-column input in the required order and must **not** repeat scaling, power transformation, encoding, or imputation outside the pipeline.

| Pipeline transformer | Features | Operation |
| --- | --- | --- |
| `power_scale` | `pT217_F`, `GFAP_to_AB_ratio`, `pT217_to_AB_ratio` | `PowerTransformer` |
| `scale_only` | `AB42_AB40_F`, `AGE` | `StandardScaler` |
| `passthrough` | `APOE4`, `SEX` | passed through unchanged |

No imputer or categorical encoder appears in the fitted pipeline. Missing values must therefore be rejected by the backend rather than filled.

## Classification rule

The final serialized 0.9306 pipeline does not set a custom probability
threshold. It uses the native binary SVC decision boundary:

- `decision_function >= 0` / `model.predict(...) == 1`: Amyloid Positive
- `decision_function < 0` / `model.predict(...) == 0`: Amyloid Negative

The dashboard may display `predict_proba(...)[class 1]` as the Amyloid Positive
risk percentage. It must use `model.predict()` for the Positive/Negative label,
not a `>= 0.5` probability check: SVC probability calibration is separate from
the SVC decision boundary.

## Compatibility and inspection environment

The model was serialized by scikit-learn `1.6.1`; it fails under scikit-learn
`1.9.1` because `sklearn.compose._column_transformer._RemainderColsList` no
longer exists. The project `.venv` is pinned to and has successfully loaded the
artifact with:

- Python `3.13.14`
- scikit-learn `1.6.1`
- numpy `2.5.4`
- pandas `3.1.0`
- joblib `1.6.0`

The final-model notebook provides no package-version record. Its metadata only
identifies a generic Colab Python kernel. The versions above are therefore the
verified compatible runtime pins, not asserted original training versions. App
startup logs the installed scikit-learn version and fails before loading if it
is not exactly `1.6.1`.

## Synthetic execution examples

These are deliberately synthetic, non-patient vectors within the observed
training-cohort validation bounds. They were run against the real loaded
artifact in the project `.venv`. The probability column is the class-1
(Amyloid Positive) probability.

| Input (`pT217_F`, `GFAP_to_AB_ratio`, `pT217_to_AB_ratio`, `AB42_AB40_F`, `AGE`, `APOE4`, `SEX`) | `predict` | `predict_proba` |
| --- | ---: | --- |
| `[0.386, 1800, 4, 0.0973, 73, 0, 1]` | `1` | `0.3986122466` |
| `[0.984, 2995.4054595, 7.846736, 0.0969, 71.0759755, 0, 0]` | `1` | `0.5735937118` |
| `[1.7, 5000, 14, 0.07, 85, 1, 1]` | `1` | `0.8938293835` |
| `[0.1, 400, 0.5, 0.12, 55, 0, 1]` | `0` | `0.0357609053` |

## Open questions

1. What are the physical units and source definitions for `pT217_F` and the two ratio fields? The supplied datasets do not document them.
2. What exact training Python, numpy, pandas, and joblib versions were used?
