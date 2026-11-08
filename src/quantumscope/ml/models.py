"""Trained models: save, load and predict (v0.8.2, no Qt).

A model file holds everything a prediction needs: the fitted preprocessing (Pipeline), the
classifier's numbers, its settings, and its context (accuracies, dataset, date, app version). It is a
NumPy .npz archive with a JSON header, read without pickle, so a shared file cannot run code; in
Python it opens with numpy.load(path).

  kernel       an SVM keeps only its support vectors (the points with nonzero weight: every other
               training point contributes exactly zero) and coefficients αᵢyᵢ; kernel ridge keeps all
               its training points. Predictions use the exact kernel, even if training used shots.
  variational  the trained angles θ and the bias.
"""
from dataclasses import dataclass, field
import datetime
import json

import numpy as np

from quantumscope.ml import kernels as K
from quantumscope.ml import variational as V
from quantumscope.ml.datasets import Pipeline

FORMAT = 'quantumscope-model'
VERSION = 1
KINDS = ('kernel', 'variational')


@dataclass
class TrainedModel:
    kind: str                          # 'kernel' or 'variational'
    pipeline: Pipeline
    settings: dict                     # feature map, repetitions, bandwidth, and the classifier's own
    arrays: dict                       # kernel: points, coef, b · variational: theta, bias
    info: dict = field(default_factory=dict)   # accuracies, dataset, date, app version

    @property
    def classes(self):
        return self.pipeline.classes

    def decision(self, X):
        """The decision value for prepared rows (positive → classes[0], the +1 class)."""
        X = np.atleast_2d(np.asarray(X, float))
        s = self.settings
        if self.kind == 'kernel':
            Kx = K.kernel(X, self.arrays['points'], kind=s['feature_map'], reps=s['reps'], bandwidth=s['bandwidth'])
            return Kx @ self.arrays['coef'] + float(self.arrays['b'])
        model = V.Classifier(self.pipeline.outputs, layers=s['layers'], feature_map=s['feature_map'],
                             reps=s['reps'], bandwidth=s['bandwidth'])
        model.theta, model.bias = np.asarray(self.arrays['theta'], float), float(self.arrays['bias'])
        return model.decision(X)

    def predict(self, X_raw):
        """Raw rows → (class names, decision values). Missing values are filled with the training means."""
        values = self.decision(self.pipeline.predict_ready(X_raw))
        names = [self.classes[0] if v >= 0 else self.classes[1] for v in values]
        return names, values

    # ---- files ---------------------------------------------------------------------------------
    def save(self, path):
        if not str(path).lower().endswith('.npz'):
            path = f'{path}.npz'
        arrays, pipe_header = self.pipeline.to_arrays()
        for name, value in self.arrays.items():
            arrays['model_' + name] = np.asarray(value)
        header = dict(format=FORMAT, version=VERSION, kind=self.kind, settings=self.settings, info=self.info,
                      pipeline=pipe_header)
        np.savez_compressed(path, header=np.array(json.dumps(header)), **arrays)
        return path


def load(path):
    """Read a model file, checking that it is one and that it is complete."""
    try:
        archive = np.load(path, allow_pickle=False)
    except (OSError, ValueError) as exc:
        raise ValueError(f'This is not a QuantumScope model file ({exc})') from None
    with archive as z:
        if 'header' not in z.files:
            raise ValueError('This is not a QuantumScope model file (no header)')
        try:
            header = json.loads(str(z['header']))
        except json.JSONDecodeError:
            raise ValueError('The model file is damaged (its header cannot be read)') from None
        if header.get('format') != FORMAT:
            raise ValueError('This is not a QuantumScope model file')
        if int(header.get('version', 0)) > VERSION:
            raise ValueError('This model was saved by a newer QuantumScope; update QuantumScope to open it')
        kind = header.get('kind')
        if kind not in KINDS:
            raise ValueError(f'Unknown model kind: {kind!r}')
        arrays = {name: z[name] for name in z.files if name != 'header'}
    pipeline = Pipeline.from_arrays(arrays, header['pipeline'])
    own = {name[len('model_'):]: value for name, value in arrays.items() if name.startswith('model_')}
    needed = ('points', 'coef', 'b') if kind == 'kernel' else ('theta', 'bias')
    missing = [n for n in needed if n not in own]
    if missing:
        raise ValueError(f'The model file is incomplete (missing {", ".join(missing)})')
    model = TrainedModel(kind, pipeline, dict(header['settings']), own, dict(header.get('info', {})))
    _check_shapes(model)
    return model


def _check_shapes(model):
    k = model.pipeline.outputs
    if model.kind == 'kernel':
        points, coef = np.atleast_2d(model.arrays['points']), np.ravel(model.arrays['coef'])
        if points.shape[1] != k or len(points) != len(coef):
            raise ValueError('The model file is inconsistent (its stored points do not match its features)')
    else:
        theta = np.ravel(model.arrays['theta'])
        if len(theta) != model.settings['layers'] * k:
            raise ValueError('The model file is inconsistent (its angles do not match its layers and qubits)')


# ---- from the classifiers --------------------------------------------------------------------
def _info(prepared, train, test, dataset):
    from quantumscope import __version__
    return dict(train=float(train), test=float(test), dataset=str(dataset or ''), app_version=__version__,
                created=datetime.datetime.now().isoformat(timespec='seconds'),
                samples=[int(len(prepared.y_train)), int(len(prepared.y_test))])


def from_kernel(classifier, prepared, settings, train, test, dataset=''):
    """A trained K.SVM or K.KernelRidge, with the data and settings it was trained on."""
    s = dict(feature_map=settings['kind'], reps=int(settings['reps']), bandwidth=float(settings['bandwidth']),
             method=settings['method'], strength=float(settings['strength']), shots=int(settings.get('shots', 0)))
    if isinstance(classifier, K.SVM):
        keep = classifier.support
        arrays = dict(points=prepared.X_train[keep], coef=(classifier.alpha * classifier.y)[keep], b=classifier.b)
    else:
        arrays = dict(points=prepared.X_train, coef=classifier.alpha, b=0.0)
    return TrainedModel('kernel', prepared.pipeline, s, arrays, _info(prepared, train, test, dataset))


def from_variational(classifier, prepared, settings, train, test, dataset=''):
    """A trained V.Classifier, with the data and settings it was trained on."""
    s = dict(feature_map=classifier.feature_map, reps=int(classifier.reps), bandwidth=float(classifier.bandwidth),
             layers=int(classifier.layers), optimizer=settings.get('method', ''),
             loss=getattr(classifier, 'loss_name', 'mse'))
    arrays = dict(theta=np.array(classifier.theta, float), bias=float(classifier.bias))
    return TrainedModel('variational', prepared.pipeline, s, arrays, _info(prepared, train, test, dataset))
