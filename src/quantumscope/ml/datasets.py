"""Datasets for quantum machine learning (NumPy only, no Qt): built-in and synthetic data, CSV and
.npz import, a checker that says whether a dataset fits a quantum model, and the preprocessing
that makes it fit. Two classes since v0.8.0; any number of classes since v0.9.3.

Everything a model learns from the data (column means, PCA, scaling) is fitted on the training
split only and then applied to the test split, so the test accuracy is honest.
"""
from dataclasses import dataclass, field
import csv
import math
import os

import numpy as np

DATA = os.path.join(os.path.dirname(__file__), 'data')
MAX_QUBITS = 10
LABEL_NAMES = ('label', 'labels', 'target', 'class', 'classes', 'y', 'species', 'diagnosis', 'category')
MISSING = ('', 'na', 'nan', 'n/a', 'null', 'none', '?', '-')

BUILTIN = {
    'iris': ('Iris', 'Measurements of 150 iris flowers of three species.', 'CC BY 4.0',
             'Fisher, R. (1936). Iris [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C56C76'),
    'wine': ('Wine', 'Chemical analysis of 178 wines from three cultivars.', 'CC BY 4.0',
             'Aeberhard, S. & Forina, M. (1992). Wine [Dataset]. UCI Machine Learning Repository. '
             'https://doi.org/10.24432/C5PC7J'),
    'breast_cancer': ('Breast Cancer Wisconsin (Diagnostic)', 'Features of cell nuclei in 569 breast masses, '
                      'malignant or benign.', 'CC BY 4.0',
                      'Wolberg, W., Mangasarian, O., Street, N., & Street, W. (1993). Breast Cancer Wisconsin '
                      '(Diagnostic) [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5DW2B'),
    'digits': ('Digits (8×8)', '1,797 handwritten digits as 8×8 images (the UCI test set).', 'CC BY 4.0',
               'Alpaydin, E. & Kaynak, C. (1998). Optical Recognition of Handwritten Digits [Dataset]. '
               'UCI Machine Learning Repository. https://doi.org/10.24432/C50P49'),
    'mnist': ('MNIST (2,000-image subset)', 'The first 200 images of each digit from the MNIST test set, 28×28.',
              'CC BY-SA 3.0',
              'LeCun, Y., Cortes, C., & Burges, C. J. C. The MNIST database of handwritten digits. '
              'Copyright Yann LeCun and Corinna Cortes.'),
    # v0.9.3: more small multi-class datasets
    'fashion_mnist': ('Fashion-MNIST (2,000-image subset)', 'The first 200 images of each of ten kinds of clothing '
                      'from the Fashion-MNIST test set, 28×28: harder than digits.', 'MIT',
                      'Xiao, H., Rasul, K., & Vollgraf, R. (2017). Fashion-MNIST: a novel image dataset for '
                      'benchmarking machine learning algorithms. arXiv:1708.07747. Copyright © 2017 Zalando SE.'),
    'penguins': ('Palmer Penguins', 'Bill, flipper and body measurements of 344 penguins of three species, with '
                 'the island and sex as text, and some values missing.', 'CC0 1.0',
                 'Horst, A. M., Hill, A. P., & Gorman, K. B. (2020). palmerpenguins: Palmer Archipelago (Antarctica) '
                 'penguin data. R package version 0.1.0. https://doi.org/10.5281/zenodo.3960218. Data collected by '
                 'K. B. Gorman and the Palmer Station Long Term Ecological Research Program.'),
    'seeds': ('Seeds', 'Seven shape measurements of 210 wheat kernels of three varieties.', 'CC BY 4.0',
              'Charytanowicz, M., Niewczas, J., Kulczycki, P., Kowalski, P., & Lukasik, S. (2010). Seeds [Dataset]. '
              'UCI Machine Learning Repository. https://doi.org/10.24432/C5H30K'),
    'glass': ('Glass Identification', 'The refractive index and chemical composition of 214 glass fragments of six '
              'unevenly represented types, from forensic science.', 'CC BY 4.0',
              'German, B. (1987). Glass Identification [Dataset]. UCI Machine Learning Repository. '
              'https://doi.org/10.24432/C5WW2P'),
}
SYNTHETIC = ('moons', 'circles', 'xor', 'blobs')


@dataclass
class Dataset:
    name: str
    X: np.ndarray                      # samples × features, float (NaN = missing)
    y: np.ndarray                      # class index per sample, 0 … k−1
    features: list
    classes: list
    description: str = ''
    license: str = ''
    citation: str = ''
    image_shape: tuple = None          # e.g. (8, 8) for images
    text_columns: dict = field(default_factory=dict)   # column → its categories (values are codes)
    label_name: str = ''                                 # the label column's name in an imported file

    @property
    def counts(self):
        return np.bincount(self.y, minlength=len(self.classes))


# ---- built-in and synthetic data -----------------------------------------------------------------
def load(name, **options):
    """A built-in dataset by key, or a synthetic one ('moons', 'circles', 'xor', 'blobs')."""
    if name in SYNTHETIC:
        return synthetic(name, **options)
    if name not in BUILTIN:
        raise ValueError(f'Unknown dataset {name!r}')
    title, description, license_, citation = BUILTIN[name]
    csv_path = os.path.join(DATA, f'{name}.csv')
    if os.path.exists(csv_path):                                 # kept as published: text and missing values
        data = _import_csv(csv_path)
        data.name, data.description, data.license, data.citation = title, description, license_, citation
        return data
    with np.load(os.path.join(DATA, f'{name}.npz'), allow_pickle=False) as z:
        shape = tuple(int(v) for v in z['shape']) if 'shape' in z.files else None
        return Dataset(title, z['X'].astype(float), z['y'].astype(int), [str(f) for f in z['features']],
                       [str(c) for c in z['classes']], description, license_, citation, shape)


def synthetic(kind, samples=200, noise=0.1, seed=0):
    """Two balanced classes in 2-D, for seeing decision boundaries."""
    rng = np.random.default_rng(seed)
    half = samples // 2
    if kind == 'moons':
        t = rng.uniform(0, math.pi, half)
        a = np.c_[np.cos(t), np.sin(t)]
        b = np.c_[1 - np.cos(t), 0.5 - np.sin(t)]
    elif kind == 'circles':
        t = rng.uniform(0, 2 * math.pi, half)
        a = np.c_[np.cos(t), np.sin(t)]
        b = 0.5 * np.c_[np.cos(t), np.sin(t)]
    elif kind == 'xor':
        points = rng.uniform(-1, 1, (2 * half, 2))
        same = points[:, 0] * points[:, 1] > 0
        a, b = points[same][:half], points[~same][:half]
        while len(a) < half or len(b) < half:                  # top up the smaller class
            extra = rng.uniform(-1, 1, (half, 2))
            s = extra[:, 0] * extra[:, 1] > 0
            a = np.r_[a, extra[s]][:half]
            b = np.r_[b, extra[~s]][:half]
    elif kind == 'blobs':
        a = rng.normal((-1, -1), 0.5, (half, 2))
        b = rng.normal((1, 1), 0.5, (half, 2))
    else:
        raise ValueError(f'Unknown synthetic dataset {kind!r}')
    X = np.r_[a, b] + rng.normal(0, noise, (2 * half, 2))
    y = np.r_[np.zeros(half, int), np.ones(half, int)]
    return Dataset(kind.capitalize(), X, y, ['x₁', 'x₂'], ['class A', 'class B'],
                   f'Synthetic: {kind}, {2 * half} points, noise {noise:g}, seed {seed}.')


# ---- your own data ----------------------------------------------------------------------------------
def import_file(path):
    """A dataset from a .csv or .npz file."""
    if path.lower().endswith('.npz'):
        return _import_npz(path)
    if path.lower().endswith(('.csv', '.txt')):
        return _import_csv(path)
    raise ValueError('Use a .csv or .npz file')


def _number(text):
    try:
        return float(text)
    except ValueError:
        return None


def _import_csv(path):
    with open(path, newline='', encoding='utf-8-sig') as handle:
        sample = handle.read(4096)
        handle.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=',;\t')
        except csv.Error:
            dialect = csv.excel
        rows = [r for r in csv.reader(handle, dialect) if any(cell.strip() for cell in r)]
    if len(rows) < 2:
        raise ValueError('The file has fewer than two rows')
    header = any(_number(c) is None and c.strip().lower() not in MISSING for c in rows[0])
    names = [c.strip() or f'column {i + 1}' for i, c in enumerate(rows[0])] if header else \
        [f'column {i + 1}' for i in range(len(rows[0]))]
    body = rows[1:] if header else rows
    width = len(names)
    body = [r + [''] * (width - len(r)) if len(r) < width else r[:width] for r in body]
    label_column = next((i for i, n in enumerate(names) if n.lower() in LABEL_NAMES), width - 1)
    labels = [r[label_column].strip() for r in body]
    keep = [i for i in range(width) if i != label_column]
    columns, text_columns = [], {}
    for out_index, i in enumerate(keep):
        cells = [r[i].strip() for r in body]
        values = [math.nan if c.lower() in MISSING else _number(c) for c in cells]
        if any(v is None for v in values):                     # text: categories become codes
            categories = sorted({c for c in cells if c.lower() not in MISSING})
            codes = {c: float(k) for k, c in enumerate(categories)}
            values = [math.nan if c.lower() in MISSING else codes[c] for c in cells]
            text_columns[out_index] = categories
        columns.append(values)
    X = np.array(columns, float).T if columns else np.empty((len(body), 0))
    classes = sorted(set(labels), key=lambda v: (_number(v) is None, _number(v) or 0, v))
    y = np.array([classes.index(v) for v in labels], int)
    return Dataset(os.path.basename(path), X, y, [names[i] for i in keep], classes,
                   f'Imported from {os.path.basename(path)}.', text_columns=text_columns,
                   label_name=names[label_column] if header else '')


def _import_npz(path):
    with np.load(path, allow_pickle=False) as z:
        keys = {k.lower(): k for k in z.files}
        x_key = next((keys[k] for k in ('x', 'data', 'features', 'images', 'inputs') if k in keys), None)
        y_key = next((keys[k] for k in ('y', 'labels', 'label', 'target', 'targets', 'classes') if k in keys), None)
        if x_key is None or y_key is None:
            raise ValueError(f'The file needs arrays named X and y (found: {", ".join(z.files)})')
        X, raw = np.asarray(z[x_key]), np.asarray(z[y_key]).ravel()
        names = [str(n) for n in z[keys['feature_names']]] if 'feature_names' in keys else None
    shape = None
    if X.ndim > 2:                                             # images: flatten, remember the shape
        shape = tuple(X.shape[1:3]) if X.ndim == 3 else tuple(X.shape[1:])
        X = X.reshape(len(X), -1)
    if len(X) != len(raw):
        raise ValueError(f'X has {len(X)} samples but y has {len(raw)}')
    values = [str(v) for v in raw]
    classes = sorted(set(values), key=lambda v: (_number(v) is None, _number(v) or 0, v))
    y = np.array([classes.index(v) for v in values], int)
    names = names if names and len(names) == X.shape[1] else [f'feature {i + 1}' for i in range(X.shape[1])]
    return Dataset(os.path.basename(path), X.astype(float), y, names, classes,
                   f'Imported from {os.path.basename(path)}.', image_shape=shape)


# ---- the checker ------------------------------------------------------------------------------------
@dataclass
class Finding:
    level: str              # 'ok', 'fix' (preprocessing will handle it), 'stop' (cannot be used)
    message: str
    suggestion: str = ''


@dataclass
class Recipe:
    """The preprocessing steps, in order. Every step is optional and visible."""
    classes: tuple = (0, 1)            # the classes to separate: two, or more (v0.9.3)
    missing: str = 'none'              # 'none', 'drop' rows, or 'mean' (fill with the training mean)
    text: str = 'encode'               # text columns: 'encode' (as category codes) or 'drop'
    per_class: int = 0                 # at most this many samples per class (0 = all)
    components: int = 0                # PCA down to this many features (0 = keep)
    drop_constant: bool = True
    scale: str = 'pi'                  # 'pi': each feature to [0, π] (the encoding range); 'none'
    test_fraction: float = 0.25
    seed: int = 0


MIN_PER_CLASS = 10                     # fewer samples than this cannot be both learned and tested


def check(dataset, qubits=4, max_samples=200, max_classes=2):
    """What stands between this dataset and a quantum classifier on `qubits` qubits, and the recipe
    that fixes it. Returns (verdict, findings, recipe); verdict is 'ready', 'preprocess' or 'stop'.
    max_classes=2 suggests the two largest classes; max_classes=None uses every class with enough
    samples (v0.9.3: one-vs-rest)."""
    X, y = dataset.X, dataset.y
    findings = [Finding('ok', f'{len(X)} samples, {X.shape[1]} features, {len(dataset.classes)} classes.')]
    recipe = Recipe()
    counts = dataset.counts
    if X.shape[1] == 0:
        return 'stop', findings + [Finding('stop', 'There are no feature columns.')], recipe
    if len(dataset.classes) < 2:
        return 'stop', findings + [Finding('stop', 'Only one class: there is nothing to separate.')], recipe
    order = np.argsort(-counts, kind='stable')
    if len(dataset.classes) > 2 and max_classes == 2:
        a, b = sorted(int(c) for c in order[:2])
        recipe.classes = (a, b)
        findings.append(Finding('fix', f'{len(dataset.classes)} classes: separate two of them, or all at once.',
                                f'Suggested pair: {dataset.classes[a]} and {dataset.classes[b]}; or choose All classes.'))
    elif len(dataset.classes) > 2:
        enough = [c for c in range(len(dataset.classes)) if counts[c] >= MIN_PER_CLASS]
        left_out = [f'{dataset.classes[c]} ({int(counts[c])})' for c in range(len(dataset.classes)) if counts[c] < MIN_PER_CLASS]
        if len(enough) >= 2:
            recipe.classes = tuple(enough)
            findings.append(Finding('ok', f'{len(dataset.classes)} classes, all separated at once (one-vs-rest).'))
            if left_out:
                findings.append(Finding('fix', f'Too few samples (under {MIN_PER_CLASS}) to learn and test: '
                                               f'{", ".join(left_out)}.', 'Leave those classes out.'))
    small = [dataset.classes[c] for c in recipe.classes if counts[c] < MIN_PER_CLASS]
    if small:
        return 'stop', findings + [Finding('stop', f'Too few samples (under {MIN_PER_CLASS}) in: '
                                                   f'{", ".join(small)}.')], recipe
    missing = int(np.isnan(X).sum())
    if missing:
        rows = int(np.isnan(X).any(axis=1).sum())
        recipe.missing = 'drop' if rows <= 0.05 * len(X) else 'mean'
        findings.append(Finding('fix', f'{missing} missing values in {rows} samples.',
                                'Drop those samples (few of them).' if recipe.missing == 'drop' else
                                'Fill each with its column\'s mean (too many samples to drop).'))
    if dataset.text_columns:
        names = ', '.join(dataset.features[i] for i in dataset.text_columns)
        findings.append(Finding('fix', f'Text columns: {names}.', 'Encode their categories as numbers, or drop them.'))
    chosen = np.isin(y, recipe.classes)
    with np.errstate(all='ignore'):
        constant = int(np.sum(np.nanstd(X[chosen], axis=0) == 0))
    if constant:
        findings.append(Finding('fix', f'{constant} features never change.', 'Drop them: they carry no information.'))
    usable = X.shape[1] - constant
    if usable > qubits:
        recipe.components = qubits
        findings.append(Finding('fix', f'{usable} features but {qubits} qubits (one feature per qubit).',
                                f'Reduce to {qubits} features with PCA (principal component analysis).'))
    total = int(sum(counts[c] for c in recipe.classes))
    per_class = max(max_samples // len(recipe.classes), 40)      # enough of each class to learn from
    if total > max_samples and per_class < max(counts[c] for c in recipe.classes):
        recipe.per_class = per_class
        findings.append(Finding('fix', f'{total} samples: a quantum kernel compares every pair (N² circuits).',
                                f'Use at most {recipe.per_class} samples per class, chosen at random.'))
    kept = [min(counts[c], recipe.per_class or counts[c]) for c in recipe.classes]
    ratio = min(kept) / max(kept)
    if ratio < 0.5:
        which = 'two classes are' if len(recipe.classes) == 2 else 'classes are'
        findings.append(Finding('ok', f'The {which} unbalanced (the smallest has {ratio:.0%} of the largest\'s samples); '
                                      f'accuracy alone can mislead: see the balanced accuracy.'))
    with np.errstate(all='ignore'):
        lo, hi = np.nanmin(X[chosen], axis=0), np.nanmax(X[chosen], axis=0)
    if np.nanmin(lo) < 0 or np.nanmax(hi) > math.pi or np.nanmax(hi - lo) > 10 * max(1e-12, np.nanmin(hi - lo)):
        findings.append(Finding('fix', 'Features are on different scales or outside the angle range.',
                                'Scale each feature to [0, π] for angle encoding.'))
    verdict = 'preprocess' if any(f.level == 'fix' for f in findings) else 'ready'
    return verdict, findings, recipe


# ---- preprocessing -----------------------------------------------------------------------------------
@dataclass
class Pipeline:
    """Every fitted preprocessing step, so new raw data is transformed exactly like the training
    data (v0.8.2). Fitted on the training split only; transform() applies it to any rows with the
    dataset's raw columns. At prediction time, missing values are always filled with the training
    means (a sample to be predicted cannot be dropped)."""
    features: list                     # raw feature names, in the dataset's column order
    text_columns: dict                 # raw column → its categories (codes are positions in this list)
    classes: tuple                     # (name of +1, name of −1), or all k names in label order
    keep: np.ndarray                   # raw columns used (text columns may be dropped)
    means: np.ndarray                  # training means of the kept columns
    fill: bool                         # the recipe fills missing values with the means
    varying: np.ndarray = None         # kept columns that vary (constant ones dropped), or None
    pca_mean: np.ndarray = None
    pca_components: np.ndarray = None  # k × columns, or None
    lo: np.ndarray = None              # scaling to [0, π]: (x − lo) / span · π, or None
    span: np.ndarray = None
    names: list = field(default_factory=list)   # the prepared features' names
    label_name: str = ''               # the training file's label column, if it had a name

    @property
    def inputs(self):
        return len(self.features)

    @property
    def outputs(self):
        return len(self.names)

    def transform(self, X, fill_missing=None):
        """Raw rows (samples × raw features, text as category codes) → prepared features."""
        X = np.atleast_2d(np.asarray(X, float))
        if X.shape[1] != self.inputs:
            raise ValueError(f'Expected {self.inputs} raw features, got {X.shape[1]}')
        X = X[:, self.keep]
        if (self.fill if fill_missing is None else fill_missing) and np.isnan(X).any():
            X = np.where(np.isnan(X), self.means, X)
        if self.varying is not None:
            X = X[:, self.varying]
        if self.pca_components is not None:
            X = (X - self.pca_mean) @ self.pca_components.T
        if self.lo is not None:
            X = (X - self.lo) / self.span * math.pi
        return X

    def predict_ready(self, X):
        """transform() for prediction: missing values always filled with the training means."""
        return self.transform(X, fill_missing=True)

    def to_arrays(self, prefix='pipe_'):
        """Arrays and a JSON-ready header, for saving (no pickle)."""
        arrays = {prefix + 'keep': self.keep, prefix + 'means': self.means}
        for name in ('varying', 'pca_mean', 'pca_components', 'lo', 'span'):
            value = getattr(self, name)
            if value is not None:
                arrays[prefix + name] = value
        header = dict(features=list(self.features), classes=list(self.classes), fill=bool(self.fill),
                      names=list(self.names), text_columns={str(k): list(v) for k, v in self.text_columns.items()},
                      label_name=self.label_name)
        return arrays, header

    @classmethod
    def from_arrays(cls, arrays, header, prefix='pipe_'):
        get = lambda name: np.asarray(arrays[prefix + name]) if prefix + name in arrays else None   # noqa: E731
        return cls(list(header['features']), {int(k): list(v) for k, v in header['text_columns'].items()},
                   tuple(header['classes']), get('keep').astype(int), get('means').astype(float), bool(header['fill']),
                   None if get('varying') is None else get('varying').astype(bool), get('pca_mean'),
                   get('pca_components'), get('lo'), get('span'), list(header['names']), header.get('label_name', ''))


@dataclass
class Prepared:
    X_train: np.ndarray
    X_test: np.ndarray
    y_train: np.ndarray                # two classes: ±1 (+1 = the first); more: 0 … k−1 (v0.9.3)
    y_test: np.ndarray
    features: list
    classes: tuple                     # class names: (name of +1, name of −1), or in label order
    steps: list                        # what was done, in words
    pipeline: Pipeline = None          # the fitted steps, to prepare new data the same way
    train_rows: np.ndarray = None      # which dataset rows went into training and testing
    test_rows: np.ndarray = None

    @property
    def k(self):
        """The number of classes."""
        return len(self.classes)

    def label_name(self, label):
        """The class name for a label (±1, or 0 … k−1)."""
        if self.k == 2:
            return self.classes[0] if label == 1 else self.classes[1]
        return self.classes[int(label)]


def prepare(dataset, recipe):
    """Apply a recipe: choose classes, clean, split, then fit on the training split only.
    The fitted steps are kept in a Pipeline, which prepares new raw data the same way."""
    import warnings
    rng = np.random.default_rng(recipe.seed)
    chosen_classes = tuple(int(c) for c in recipe.classes)
    if len(set(chosen_classes)) != len(chosen_classes) or len(chosen_classes) < 2:
        raise ValueError('Choose at least two different classes')
    names_of = tuple(dataset.classes[c] for c in chosen_classes)
    if len(chosen_classes) == 2:
        steps = [f'Classes: {names_of[0]} (+1) and {names_of[1]} (−1).']
    else:
        steps = [f'{len(chosen_classes)} classes: {", ".join(names_of)}.']
    rows = np.flatnonzero(np.isin(dataset.y, chosen_classes))       # dataset rows still in play
    X, y = dataset.X[rows].copy(), dataset.y[rows]
    keep = np.arange(dataset.X.shape[1])
    if recipe.text == 'drop' and dataset.text_columns:
        keep = np.array([i for i in range(X.shape[1]) if i not in dataset.text_columns], int)
        X = X[:, keep]
        steps.append(f'Dropped {len(dataset.text_columns)} text columns.')
    elif dataset.text_columns:
        steps.append(f'Encoded {len(dataset.text_columns)} text columns as category codes.')
    names = [dataset.features[i] for i in keep]
    if recipe.missing == 'drop':
        good = ~np.isnan(X).any(axis=1)
        steps.append(f'Dropped {int((~good).sum())} samples with missing values.')
        X, y, rows = X[good], y[good], rows[good]
    if recipe.per_class:
        chosen = np.concatenate([rng.permutation(np.flatnonzero(y == c))[:recipe.per_class] for c in chosen_classes])
        X, y, rows = X[chosen], y[chosen], rows[chosen]
        steps.append(f'Kept at most {recipe.per_class} samples per class.')
    test = np.zeros(len(y), bool)                              # stratified split
    for c in chosen_classes:
        members = rng.permutation(np.flatnonzero(y == c))
        test[members[:int(round(recipe.test_fraction * len(members)))]] = True
    Xtr, Xte = X[~test], X[test]
    steps.append(f'Split: {int((~test).sum())} for training, {int(test.sum())} for testing.')
    with warnings.catch_warnings():                             # an all-missing column has no mean
        warnings.simplefilter('ignore', RuntimeWarning)
        means = np.nanmean(Xtr, axis=0) if len(Xtr) else np.zeros(Xtr.shape[1])
    means = np.where(np.isnan(means), 0.0, means)
    pipe = Pipeline(list(dataset.features), dict(dataset.text_columns), names_of, keep, means, recipe.missing == 'mean')
    if recipe.missing == 'mean' and (np.isnan(Xtr).any() or np.isnan(Xte).any()):   # either split
        Xtr = np.where(np.isnan(Xtr), means, Xtr)
        Xte = np.where(np.isnan(Xte), means, Xte)
        steps.append('Filled missing values with the training means.')
    if recipe.drop_constant:
        varying = np.nanstd(Xtr, axis=0) > 0
        if not varying.all():
            steps.append(f'Dropped {int((~varying).sum())} constant features.')
            Xtr, Xte, names = Xtr[:, varying], Xte[:, varying], [n for n, v in zip(names, varying) if v]
            pipe.varying = varying
    if recipe.components and recipe.components < Xtr.shape[1]:
        mean = Xtr.mean(axis=0)
        _, s, vt = np.linalg.svd(Xtr - mean, full_matrices=False)
        k = recipe.components
        explained = float((s[:k] ** 2).sum() / max(1e-300, (s ** 2).sum()))
        Xtr, Xte = (Xtr - mean) @ vt[:k].T, (Xte - mean) @ vt[:k].T
        names = [f'PC{i + 1}' for i in range(k)]
        steps.append(f'PCA: {k} components keep {explained:.0%} of the variance.')
        pipe.pca_mean, pipe.pca_components = mean, vt[:k]
    if recipe.scale == 'pi':
        lo, hi = Xtr.min(axis=0), Xtr.max(axis=0)
        span = np.where(hi > lo, hi - lo, 1.0)
        Xtr, Xte = (Xtr - lo) / span * math.pi, (Xte - lo) / span * math.pi
        steps.append('Scaled each feature to [0, π] (from the training data).')
        pipe.lo, pipe.span = lo, span
    pipe.names = list(names)
    pipe.label_name = dataset.label_name
    if len(chosen_classes) == 2:
        to_label = lambda v: np.where(v == chosen_classes[0], 1, -1)                      # noqa: E731
    else:
        position = {c: i for i, c in enumerate(chosen_classes)}
        to_label = lambda v: np.array([position[int(c)] for c in v], int)                 # noqa: E731
    return Prepared(Xtr, Xte, to_label(y[~test]), to_label(y[test]), names, names_of, steps, pipe,
                    rows[~test], rows[test])


@dataclass
class NewData:
    """Raw rows to predict, aligned to a pipeline's features (v0.8.2)."""
    X: np.ndarray                      # samples × the pipeline's raw features (text as category codes)
    labels: list = None                # the true class names, when the file has a label column
    notes: list = field(default_factory=list)


def read_for_prediction(path, pipeline):
    """Read a .csv or .npz file of new samples for a trained model's pipeline. CSV columns are
    matched by header name (order and extra columns do not matter); without a header they must be in
    the training order. A label column is optional. Text values map through the model's categories;
    unseen ones become missing values, which prediction fills with the training means."""
    if path.lower().endswith('.npz'):
        with np.load(path, allow_pickle=False) as z:
            keys = {k.lower(): k for k in z.files}
            x_key = next((keys[k] for k in ('x', 'data', 'features', 'images', 'inputs') if k in keys), None)
            if x_key is None:
                raise ValueError(f'The file needs an array named X (found: {", ".join(z.files)})')
            X = np.asarray(z[x_key], float)
            y_key = next((keys[k] for k in ('y', 'labels', 'label', 'target', 'targets', 'classes') if k in keys), None)
            labels = [str(v) for v in np.asarray(z[y_key]).ravel()] if y_key else None
        X = X.reshape(len(X), -1)
        if X.shape[1] != pipeline.inputs:
            raise ValueError(f'The model expects {pipeline.inputs} features per sample; this file has {X.shape[1]}')
        return NewData(X, labels)
    with open(path, newline='', encoding='utf-8-sig') as handle:
        sample = handle.read(4096)
        handle.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=',;\t')
        except csv.Error:
            dialect = csv.excel
        rows = [r for r in csv.reader(handle, dialect) if any(cell.strip() for cell in r)]
    if not rows:
        raise ValueError('The file is empty')
    expected = [f.strip().lower() for f in pipeline.features]
    first = [c.strip().lower() for c in rows[0]]
    header = any(_number(c) is None and c not in MISSING for c in first)
    notes = []
    if header:
        missing = [f for f, low in zip(pipeline.features, expected) if low not in first]
        if missing:
            shown = ', '.join(missing[:6]) + (f' and {len(missing) - 6} more' if len(missing) > 6 else '')
            raise ValueError(f'The file lacks columns the model needs: {shown}')
        positions = [first.index(low) for low in expected]
        wanted = pipeline.label_name.strip().lower()                       # the training file's label column first
        label_at = next((i for i, c in enumerate(first) if wanted and c == wanted), None)
        if label_at is None:
            label_at = next((i for i, c in enumerate(first) if c in LABEL_NAMES and c not in expected), None)
        body = rows[1:]
    else:
        width = len(rows[0])
        if width not in (pipeline.inputs, pipeline.inputs + 1):
            raise ValueError(f'The model expects {pipeline.inputs} columns (plus an optional label); '
                             f'this file has {width}')
        positions = list(range(pipeline.inputs))
        label_at = pipeline.inputs if width == pipeline.inputs + 1 else None
        body = rows
    X = np.full((len(body), pipeline.inputs), np.nan)
    unseen = 0
    for r, row in enumerate(body):
        for j, at in enumerate(positions):
            cell = row[at].strip() if at < len(row) else ''
            if cell.lower() in MISSING:
                continue
            if j in pipeline.text_columns:
                categories = pipeline.text_columns[j]
                if cell in categories:
                    X[r, j] = categories.index(cell)
                else:
                    unseen += 1
            else:
                value = _number(cell)
                if value is None:
                    raise ValueError(f'Row {r + 1}: "{cell}" in column {pipeline.features[j]} is not a number')
                X[r, j] = value
    if unseen:
        notes.append(f'{unseen} text values the model never saw were treated as missing.')
    gaps = int(np.isnan(X).sum()) - unseen
    if gaps:
        notes.append(f'{gaps} missing values were filled with the training means.')
    labels = [row[label_at].strip() if label_at < len(row) else '' for row in body] if label_at is not None else None
    return NewData(X, labels, notes)
