# QML Forge Description

QML Forge is a Streamlit application for preparing tabular datasets, selecting machine-learning
algorithms, comparing classical and simulated quantum models, and preserving benchmark runs as
immutable versions.

## The data flow

The application has two related data representations:

1. **The original dataset** is the CSV received from the user. It is parsed into a pandas
   `DataFrame` and stored in the project's `data/uploads/` directory. The database keeps its
   filename, SHA-256 hash, size metadata, and storage path.
2. **The working dataset** is an in-memory copy used by the current Streamlit session. Cleaning
   operations modify this copy, while the original copy is retained by `CleaningPipeline` so the
   steps can be undone or replayed.

The main flow is:

```text
CSV upload / public URL / Kaggle file
              |
              v
      Parse bytes into DataFrame
              |
              v
  Save original CSV and dataset metadata
              |
              v
     Create CleaningPipeline
              |
              v
 Apply cleaning operations to working DataFrame
              |
              v
      Define task and target
              |
              v
 Build X (features) and y (target)
              |
              v
  Train and evaluate selected models
              |
              v
 Save settings and results as an immutable version
```

### What cleaning does

The **Upload & Clean** page applies operations such as standardizing column names, trimming
whitespace, converting values to numbers, parsing dates, removing duplicates, imputing missing
values, clipping outliers, dropping columns or rows, and encoding categorical columns.

Each operation is recorded as a small entry containing its operation name and parameters. For
example, the log can record that `impute` was applied to two columns using the `median` strategy.
Because the log is replayable:

- **Undo** removes the last log entry and rebuilds the working DataFrame from the original data.
- **Revert** can restore an older version's cleaning log and replay it on the stored original CSV.
- The cleaning log is saved in the version configuration, not as a mutation of an old version.

The **Download cleaned CSV** button creates a CSV for the user to download, but that downloaded
file is not automatically uploaded again or used as a separate dataset.

### Does machine learning use the cleaned data?

Yes. When the user goes to **Define Task**, QML Forge uses the current cleaned
`CleaningPipeline.df`. It separates the selected target column into `y` and uses the remaining
columns as `X`. Datetime columns are removed, and categorical features are one-hot encoded.
Classification targets are converted to numeric labels.

The resulting `X` and `y` are kept in Streamlit session state and passed to **Train & Compare**.
Therefore, the benchmark uses the cleaned in-memory DataFrame directly; it does not need to read
the downloaded cleaned CSV from disk.

### What happens during training?

The selected model receives a scikit-learn `Pipeline`. The pipeline keeps model preprocessing
inside cross-validation, including median imputation, the selected scaler, feature selection,
and optional PCA. This prevents preprocessing statistics from leaking from validation folds into
training.

For quantum models, the application optionally samples the cleaned `X` and `y` first. The sample
is capped by the quantum row limit, PCA reduces features to the qubit limit, and the quantum
models are simulated classically. Classical models can optionally run on that same sample for a
fair comparison.

## Algorithms and how they work

The available models depend on the selected task. The user can choose models manually or use the
**Recommended** preset, which selects a practical starting group based on dataset size and
characteristics. Every selected model is evaluated using the same prepared data and
cross-validation settings.

### Classification

Classification predicts a discrete label, such as `spam` versus `not spam`.

- **Logistic Regression** learns weighted feature coefficients and converts their combined score
  into class probabilities. It is a fast, interpretable baseline.
- **K-Nearest Neighbors (KNN)** predicts a label from the labels of nearby training rows. It is
  simple and useful for smaller datasets, but depends on meaningful feature distances.
- **Naive Bayes** calculates class probabilities from feature probabilities while assuming the
  features are conditionally independent given the class. It is often fast on relatively simple
  data.
- **Decision Tree** repeatedly splits rows using feature thresholds to form a tree of decisions.
  It can model nonlinear relationships but may overfit without depth limits.
- **Random Forest** trains many decision trees on randomized subsets of rows and features, then
  combines their votes. This usually improves stability over one tree.
- **Gradient Boosting** builds trees sequentially, with each new tree focusing on errors made by
  the previous trees. It can model complex tabular patterns.
- **SVM (RBF)** finds a separating boundary using support vectors. The RBF kernel allows a
  nonlinear boundary by measuring similarity between rows.
- **MLP** is a feed-forward neural network with learned layers of weighted connections. It can
  learn nonlinear patterns but generally needs scaled features and sufficient data.
- **XGBoost**, when the optional `xgboost` package is installed, is a regularized gradient
  boosting implementation that combines many small trees.

### Regression

Regression predicts a continuous value, such as a price or measurement.

- **Linear Regression** estimates a linear relationship between features and the numeric target.
- **Ridge** is linear regression with L2 regularization, which discourages very large
  coefficients and helps with correlated features.
- **Lasso** is linear regression with L1 regularization, which can shrink some coefficients to
  zero and therefore perform feature selection.
- **KNN Regressor** averages the target values of nearby training rows.
- **Decision Tree Regressor** predicts by following feature-based splits to a leaf containing a
  numeric prediction.
- **Random Forest Regressor** averages predictions from many randomized regression trees.
- **Gradient Boosting Regressor** adds trees sequentially to reduce prediction error.
- **SVR (RBF)** uses support-vector regression with an RBF similarity function to fit a
  nonlinear function while controlling the size of prediction errors.
- **MLP Regressor** uses a neural network to learn nonlinear relationships for continuous output.
- **XGBoost Regressor**, when installed, uses regularized boosted trees for continuous targets.

### Clustering

Clustering groups rows without a target column. The application currently provides:

- **K-Means** assigns rows to the nearest of `k` learned centroids and repeatedly updates those
  centroids.
- **Agglomerative Clustering** starts with individual rows and repeatedly merges the closest
  groups to create a hierarchy, stopping at the requested number of clusters.
- **Gaussian Mixture** models the data as a mixture of Gaussian probability distributions and
  assigns each row to the most likely component.
- **DBSCAN** forms dense regions into clusters and labels sparse points as noise. It does not
  require a requested number of clusters, although the current UI shares the clustering control
  with the other clusterers.

### Optional simulated quantum models

Quantum models are off by default and are simulated on a classical computer with PennyLane; they
are not evidence of quantum advantage.

- **Quantum Kernel SVM** maps each row into a simulated quantum state and uses the state fidelity
  between pairs of rows as an SVM kernel.
- **Variational Quantum Classifier** is a binary classifier with a parameterized circuit. The
  circuit parameters are trained with Adam to produce a score whose sign selects the class.
- **Variational Quantum Regressor** uses the same style of trainable circuit and rescales its
  expectation value to predict a continuous target.

Quantum models require the feature count to be reduced to the configured qubit count. QML Forge
therefore applies PCA and angle scaling inside the pipeline, and limits the number of rows used
for quantum experiments.

After evaluation, QML Forge stores:

- the cleaning steps;
- optimization settings;
- task and target;
- selected algorithms;
- seed and cross-validation folds; and
- each model's metrics, errors, and rows used.

The original dataset and old versions are not overwritten. A revert or a new benchmark creates a
new version, preserving the history of the experiment.

The application supports:

- Local CSV uploads and public CSV URLs
- Kaggle dataset imports with selectable CSV files
- Replayable data-cleaning operations
- Classification, regression, and clustering tasks
- Leakage-safe preprocessing and optimization
- Classical and optional simulated quantum models
- Benchmark metrics and leaderboard results
- Version history, comparison, and revert workflows

For an overview of the repository layout, see [FILE_STRUCTURE.md](./FILE_STRUCTURE.md).
