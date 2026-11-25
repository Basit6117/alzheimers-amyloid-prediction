# blood_only.ipynb Documentation

## Overview
This Jupyter notebook focuses on amyloid detection using blood-based biomarkers. It explores machine learning models (logistic regression and SVM) to predict amyloid positivity from plasma biomarkers. The workflow includes data loading, exploratory data analysis, feature engineering, model training, hyperparameter tuning, evaluation, and model persistence.

## Structure

### 1. Setup and Data Loading
- **Cell 0-1**: Mounts Google Drive and loads the dataset (`clean_cn_amyloid_dataset.csv`) containing biomarker features and amyloid labels.
- **Cell 2-5**: Initial data exploration including shape, data types, missing values, duplicates, class distribution, and basic statistics.

### 2. Exploratory Data Analysis (EDA)
- **Cell 3-7**: Examines feature distributions, skewness, and correlations among continuous variables (`pT217_F`, `AB42_AB40_F`, `NfL_Q`, `GFAP_Q`, `AGE`, `PTEDUCAT`).

### 3. Logistic Regression Models
- **Cell 8-11**: Implements a logistic regression pipeline with feature engineering (interaction terms: `pT217_x_APOE4`, `GFAP_to_AB_ratio`), preprocessing (power transformation for skewed features, standardization), and hyperparameter tuning (GridSearchCV for `C`). Evaluates performance using ROC-AUC, classification reports, and confusion matrices.
- **Key Result**: Achieved test ROC-AUC of **0.9259** with optimal `C=0.04`, penalty=`l2`.

### 4. Support Vector Machine (SVM) Models
- **Cell 12-30**: Progressively refines an SVM classifier with radial basis function (RBF) kernel.
  - **Baseline SVM (Cell 13)**: Initial pipeline yields test ROC-AUC of **0.9259**.
  - **Hyperparameter Tuning (Cell 14)**: Refines `C`, `gamma`, and `class_weight` using repeated stratified cross-validation (5 folds × 10 repeats). Achieves **0.9282** test ROC-AUC.
  - **Feature Refinement (Cell 16)**: Adds clinical age binning (`AGE_BIN`) but reduces performance to **0.9097**.
  - **Champion Model (Cell 20-21)**: Final blood-only SVM model with features: `pT217_F`, `GFAP_to_AB_ratio`, `AB42_AB40_F`, `AGE`, `APOE4`, `SEX`.
    - **Performance**: 
      - Test ROC-AUC: **0.9282** (95% CI: [0.843, 0.991])
      - Sensitivity at threshold 0.25: **0.9167** (95% CI: [0.615, 0.998])
      - Specificity: **0.8889**
      - Patients caught: 11/12 amyloid-positive cases in test set.
    - **Validation**: 
      - 50-fold CV ROC-AUC: **0.8975** (±0.1707)
      - Train-test AUC gap: +0.0078 (acceptable overfitting)
  - **Hybrid Enhancement (Cell 25-27)**: Adds `pT217_to_AB_ratio` feature, peaking at **0.9306** test ROC-AUC with `C=1.0`, `gamma=0.05`.
  - **Model Persistence (Cell 26, 31)**: Saves the champion pipeline as `amyloid_svm_champion_9306.joblib`.

### 5. Visualization
- **Cell 30**: Generates and saved as `biomarker_svm_oof_roc_curve.png`: Saves the final pipeline to Google Drive and local disk.

### 5. Model Evaluation and Validation
- **Cell 20, 27-29**: Comprehensive evaluation including:
  - Overfitting checks (train-test AUC gap)
  - Repeated cross-validation (50-fold stratified)
  - Confusion matrices, classification reports, and bootstrapped confidence intervals
  - Support vector analysis (100/190 training vectors = 52.6%)
- **Cell 30**: Generates ROC curve visualization for the 50-fold out-of-fold predictions.

### 6. Deployment Preparation
- **Cell 31**: Demonstrates reloading the saved model from Google Drive and verifying performance consistency.

## Key Features Used
- **Biomarkers**: `pT217_F` (phosphorylated tau217), `AB42_AB40_F` (amyloid beta ratio), `GFAP_Q` (glial fibrillary acidic protein), `NfL_Q` (neurofilament light chain, explored but not in final model)
- **Demographics**: `AGE`, `APOE4` (ε4 allele count), `SEX` (0=male, 1=female), `PTEDUCAT` (years of education)
- **Engineered Features**:
  - `GFAP_to_AB_ratio` = `GFAP_Q` / (`AB42_AB40_F` + ε)
  - `pT217_to_AB_ratio` = `pT217_F` / (`AB42_AB40_F` + ε) (in hybrid model)

## Modeling Approach
1. **Data Splitting**: Stratified 80/20 train/test split (`random_state=42`)
2. **Feature Engineering**: Performed strictly within training set to prevent leakage
3. **Preprocessing Pipeline**:
   - PowerTransformer (Yeo-Johnson) for skewed features
   - StandardScaler for normally distributed features
   - Passthrough for binary features
4. **Model Selection**:
   - Logistic Regression with L2 regularization and class weighting
   - SVM with RBF kernel, probability estimates, and class weighting
5. **Hyperparameter Tuning**: GridSearchCV with repeated stratified cross-validation
6. **Evaluation Metrics**: ROC-AUC (primary), sensitivity, specificity, F1-score, confusion matrix

## Results Summary
- **Best Model**: SVM-RBF with `C=1.0`, `gamma=0.05`, `class_weight='balanced'`
- **Input Features**: `pT217_F`, `GFAP_to_AB_ratio`, `AB42_AB40_F`, `AGE`, `APOE4`, `SEX`
- **Test Performance**: 
  - ROC-AUC: **0.9306**
  - Sensitivity @ 0.25 threshold: **91.67%**
  - Specificity: **88.89%**
- **Robustness**: Consistent performance across cross-validation folds, minimal overfitting (train-test gap <0.01)

## Usage
1. Execute cells sequentially to reproduce the analysis.
2. The final model is saved as `amyloid_svm_champion_9306.joblib` for deployment.
3. To use the model for prediction:
   ```python
   import joblib
   pipeline = joblib.load('amyloid_svm_champion_9306.joblib')
   predictions = pipeline.predict(new_data)  # or predict_proba for probabilities
   ```

## Notes
- All feature engineering and preprocessing steps are encapsulated within the scikit-learn pipeline to ensure reproducibility and prevent data leakage.
- The model focuses exclusively on blood-based biomarkers, avoiding CSF or imaging data for minimally invasive screening.
- Threshold selection (0.25) optimizes for high sensitivity in amyloid detection, suitable for screening applications where minimizing false negatives is critical.