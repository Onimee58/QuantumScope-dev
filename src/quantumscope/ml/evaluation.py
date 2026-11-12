"""Evaluating classifiers (v0.8.3, no Qt): metrics, cross-validation and hyperparameter search.

Two classes: labels are ±1 (+1 is the first chosen class). Decision values are the classifier's
real-valued output f(x), whose sign is the prediction; the ROC curve sweeps a threshold over them.

More classes (v0.9.3): labels are 0 … k−1 and decision values have one column per class. The
confusion matrix is k × k; precision, recall and F1 are per class and averaged over the classes
("macro" averages, so every class counts equally however many samples it has); each class has a
one-vs-rest ROC curve.
"""
import itertools
from dataclasses import dataclass, field

import numpy as np


# ---- metrics -----------------------------------------------------------------------------------
@dataclass
class Metrics:
    tp: int                            # +1 predicted +1
    fn: int                            # +1 predicted −1
    fp: int                            # −1 predicted +1
    tn: int                            # −1 predicted −1

    @property
    def total(self):
        return self.tp + self.fn + self.fp + self.tn

    @property
    def accuracy(self):
        return (self.tp + self.tn) / self.total if self.total else 0.0

    @property
    def precision(self):
        """Of the samples predicted +1, the share that are +1."""
        return self.tp / (self.tp + self.fp) if self.tp + self.fp else 0.0

    @property
    def recall(self):
        """Of the +1 samples, the share predicted +1 (sensitivity)."""
        return self.tp / (self.tp + self.fn) if self.tp + self.fn else 0.0

    @property
    def specificity(self):
        """Of the −1 samples, the share predicted −1."""
        return self.tn / (self.tn + self.fp) if self.tn + self.fp else 0.0

    @property
    def f1(self):
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if p + r else 0.0

    @property
    def balanced_accuracy(self):
        """The mean of recall and specificity: fair when the classes are unbalanced."""
        return (self.recall + self.specificity) / 2

    def matrix(self):
        """Rows: true +1, true −1. Columns: predicted +1, predicted −1."""
        return np.array([[self.tp, self.fn], [self.fp, self.tn]])


def metrics(y_true, y_pred):
    y_true, y_pred = np.asarray(y_true), np.asarray(y_pred)
    return Metrics(int(np.sum((y_true == 1) & (y_pred == 1))), int(np.sum((y_true == 1) & (y_pred != 1))),
                   int(np.sum((y_true != 1) & (y_pred == 1))), int(np.sum((y_true != 1) & (y_pred != 1))))


@dataclass
class MultiMetrics:
    """Metrics for k classes from the k × k confusion matrix (rows: true class, columns: predicted)."""
    confusion: np.ndarray

    @property
    def k(self):
        return len(self.confusion)

    @property
    def total(self):
        return int(self.confusion.sum())

    @property
    def accuracy(self):
        return float(np.trace(self.confusion) / self.total) if self.total else 0.0

    @property
    def recalls(self):
        """Per class: of its samples, the share predicted as it."""
        rows = self.confusion.sum(axis=1)
        return np.divide(np.diag(self.confusion), rows, out=np.zeros(self.k), where=rows > 0)

    @property
    def precisions(self):
        """Per class: of the samples predicted as it, the share that are it."""
        cols = self.confusion.sum(axis=0)
        return np.divide(np.diag(self.confusion), cols, out=np.zeros(self.k), where=cols > 0)

    @property
    def f1s(self):
        p, r = self.precisions, self.recalls
        return np.divide(2 * p * r, p + r, out=np.zeros(self.k), where=(p + r) > 0)

    @property
    def balanced_accuracy(self):
        """The mean recall over the classes present: fair when the classes are unbalanced."""
        present = self.confusion.sum(axis=1) > 0
        return float(self.recalls[present].mean()) if present.any() else 0.0

    @property
    def macro_precision(self):
        return float(self.precisions.mean())

    @property
    def macro_recall(self):
        return float(self.recalls.mean())

    @property
    def macro_f1(self):
        return float(self.f1s.mean())

    def matrix(self):
        return self.confusion


def multi_metrics(y_true, y_pred, k):
    """MultiMetrics for labels 0 … k−1."""
    confusion = np.zeros((k, k), int)
    np.add.at(confusion, (np.asarray(y_true, int), np.asarray(y_pred, int)), 1)
    return MultiMetrics(confusion)


def score(y_true, y_pred, k=2):
    """Metrics (two classes, ±1 labels) or MultiMetrics (k > 2, labels 0 … k−1)."""
    return metrics(y_true, y_pred) if k <= 2 else multi_metrics(y_true, y_pred, k)


def roc_by_class(y_true, scores):
    """One-vs-rest ROC curves for labels 0 … k−1 and scores with one column per class:
    {class: (fpr, tpr, auc)} for every class that has samples of its own and of the others."""
    y, s = np.asarray(y_true), np.atleast_2d(np.asarray(scores, float))
    curves = {}
    for c in range(s.shape[1]):
        target = np.where(y == c, 1, -1)
        if 0 < np.sum(target == 1) < len(target):
            fpr, tpr, _ = roc(target, s[:, c])
            curves[c] = (fpr, tpr, auc(target, s[:, c]))
    return curves


def roc(y_true, scores):
    """The ROC curve: (false-positive rates, true-positive rates, thresholds), from the highest
    threshold down; tied scores move together. Starts at (0, 0) and ends at (1, 1)."""
    y, s = np.asarray(y_true), np.asarray(scores, float)
    positives, negatives = int(np.sum(y == 1)), int(np.sum(y != 1))
    if not positives or not negatives:
        raise ValueError('The ROC curve needs samples of both classes')
    order = np.argsort(-s, kind='stable')
    s, y = s[order], y[order]
    distinct = np.r_[np.flatnonzero(np.diff(s)), len(s) - 1]          # last index of each tied group
    tp = np.cumsum(y == 1)[distinct]
    fp = np.cumsum(y != 1)[distinct]
    return (np.r_[0.0, fp / negatives], np.r_[0.0, tp / positives], np.r_[np.inf, s[distinct]])


def auc(y_true, scores):
    """The area under the ROC curve (trapezoids, so ties count half)."""
    fpr, tpr, _ = roc(y_true, scores)
    return float(np.trapezoid(tpr, fpr)) if hasattr(np, 'trapezoid') else float(np.trapz(tpr, fpr))


def auc_by_ranks(y_true, scores):
    """The same area from the Mann–Whitney statistic: the probability that a random +1 sample scores
    above a random −1 sample (ties count half). Used to check auc()."""
    y, s = np.asarray(y_true), np.asarray(scores, float)
    pos, neg = s[y == 1], s[y != 1]
    greater = (pos[:, None] > neg[None, :]).sum()
    ties = (pos[:, None] == neg[None, :]).sum()
    return float((greater + 0.5 * ties) / (len(pos) * len(neg)))


# ---- cross-validation --------------------------------------------------------------------------
def stratified_folds(y, k=5, seed=0):
    """k (training rows, validation rows) pairs; every fold keeps the classes' proportions, and each
    sample is validated exactly once."""
    y = np.asarray(y)
    rng = np.random.default_rng(seed)
    smallest = min(int(np.sum(y == c)) for c in np.unique(y))
    if k < 2 or smallest < k:
        raise ValueError(f'{k}-fold cross-validation needs at least {k} samples of each class '
                         f'(the smaller class has {smallest})')
    assignment = np.empty(len(y), int)
    for c in np.unique(y):
        members = rng.permutation(np.flatnonzero(y == c))
        assignment[members] = np.arange(len(members)) % k
    return [(np.flatnonzero(assignment != f), np.flatnonzero(assignment == f)) for f in range(k)]


@dataclass
class CrossValidation:
    scores: list                       # validation accuracy per fold
    metrics: list = field(default_factory=list)   # Metrics per fold

    @property
    def mean(self):
        return float(np.mean(self.scores))

    @property
    def std(self):
        return float(np.std(self.scores))


def cross_validate_kernel(K, y, make_model, folds, k=None):
    """Cross-validate a kernel classifier on a precomputed training kernel K (n × n): a fold's kernels
    are rows and columns of K, so no new kernel values are needed. k: the number of classes (from the
    labels if omitted)."""
    from quantumscope.ml.kernels import classes_in
    y = np.asarray(y)
    k = k or classes_in(y)
    result = CrossValidation([])
    for train, valid in folds:
        model = make_model().fit(K[np.ix_(train, train)], y[train])
        predicted = model.predict(K[np.ix_(valid, train)])
        m = score(y[valid], predicted, k)
        result.scores.append(m.accuracy)
        result.metrics.append(m)
    return result


# ---- hyperparameter search ---------------------------------------------------------------------
@dataclass
class SearchRow:
    settings: dict                     # feature_map, reps, bandwidth, method, strength
    cv: CrossValidation

    @property
    def mean(self):
        return self.cv.mean

    @property
    def std(self):
        return self.cv.std


def kernel_settings(grid):
    """Every combination to try, grouped by the kernel it needs: [(kernel settings, [classifier settings])].
    Repetitions only change the ZZ map, so angle encoding is not repeated over them."""
    groups = []
    for feature_map in grid['feature_map']:
        reps_values = grid['reps'] if feature_map == 'zz' else grid['reps'][:1]
        for reps, bandwidth in itertools.product(reps_values, grid['bandwidth']):
            classifiers = [dict(method=m, strength=float(c)) for m, c in itertools.product(grid['method'], grid['strength'])]
            groups.append((dict(feature_map=feature_map, reps=int(reps), bandwidth=float(bandwidth)), classifiers))
    return groups


def search_kernel(X, y, grid, k=5, seed=0, kernel=None, progress=None, cancelled=None):
    """Cross-validate every combination in grid (lists for feature_map, reps, bandwidth, method,
    strength) on the training data. Each kernel is computed once and shared by all its folds and
    classifier settings. Returns (rows sorted best first, best row); None if cancelled."""
    from quantumscope.ml import kernels as K
    kernel = kernel or K.kernel
    classes = K.classes_in(y)
    folds = stratified_folds(y, k, seed)
    groups = kernel_settings(grid)
    total = sum(len(c) for _, c in groups)
    rows, done = [], 0
    for kernel_settings_, classifiers in groups:
        if cancelled is not None and cancelled():
            return None
        Kx = kernel(X, kind=kernel_settings_['feature_map'], reps=kernel_settings_['reps'],
                    bandwidth=kernel_settings_['bandwidth'])
        for c in classifiers:
            make = lambda c=c: K.classifier(c['method'], c['strength'], classes)   # noqa: E731
            rows.append(SearchRow(dict(kernel_settings_, **c), cross_validate_kernel(Kx, y, make, folds, classes)))
            done += 1
            if progress is not None:
                progress(done, total)
    rows.sort(key=lambda r: (-round(r.mean, 12), round(r.std, 12)))   # best mean, then the steadiest
    return rows, rows[0]


def stratified_split(y, fraction, seed=0):
    """(kept rows, held-out rows): `fraction` of each class held out, e.g. for validation."""
    y = np.asarray(y)
    rng = np.random.default_rng(seed)
    held = np.zeros(len(y), bool)
    for c in np.unique(y):
        members = rng.permutation(np.flatnonzero(y == c))
        held[members[:int(round(fraction * len(members)))]] = True
    return np.flatnonzero(~held), np.flatnonzero(held)


def cross_validate_variational(X, y, make_model, folds, train_options=None, progress=None, cancelled=None):
    """Cross-validate a variational classifier: a fresh model trained per fold (costly: k trainings).
    progress(fold, folds) after each fold; returns None if cancelled."""
    from quantumscope.ml.kernels import classes_in
    X, y = np.asarray(X, float), np.asarray(y)
    classes = classes_in(y)
    result = CrossValidation([])
    for k, (train, valid) in enumerate(folds):
        if cancelled is not None and cancelled():
            return None
        model = make_model()
        model.train(X[train], y[train], **(train_options or {}))
        m = score(y[valid], model.predict(X[valid]), classes)
        result.scores.append(m.accuracy)
        result.metrics.append(m)
        if progress is not None:
            progress(k + 1, len(folds))
    return result
