"""v0.8.2 (18a): the preprocessing pipeline, reading new data, and model files (save, load, predict)."""
import json

import numpy as np
import pytest

from quantumscope.ml import datasets as D
from quantumscope.ml import kernels as K
from quantumscope.ml import models as M
from quantumscope.ml import variational as V


@pytest.fixture
def awkward(tmp_path):
    rng = np.random.default_rng(3)
    rows = ['size,shape,weight,kind'] + [
        f'{rng.uniform(1, 3):.3f},{"round" if k % 3 else "square" if k % 2 else "oval"},'
        f'{"" if k % 11 == 0 else f"{rng.uniform(5, 9):.2f}"},{k % 2}' for k in range(80)]
    path = tmp_path / 'awkward.csv'
    path.write_text('\n'.join(rows) + '\n')
    return D.import_file(str(path))


@pytest.mark.parametrize('name, qubits', [('mnist', 4), ('wine', 3), ('iris', 2), ('moons', 2), ('breast_cancer', 4)])
def test_the_pipeline_reproduces_the_prepared_data_from_raw_rows(name, qubits):
    ds = D.load(name)
    p = D.prepare(ds, D.check(ds, qubits=qubits)[2])
    assert np.allclose(p.pipeline.transform(ds.X[p.train_rows]), p.X_train, atol=1e-12)
    assert np.allclose(p.pipeline.transform(ds.X[p.test_rows]), p.X_test, atol=1e-12)
    assert p.pipeline.names == p.features and p.pipeline.classes == p.classes


def test_the_pipeline_handles_text_and_missing_values(awkward):
    for missing in ('drop', 'mean'):
        for text in ('encode', 'drop'):
            recipe = D.check(awkward, qubits=2)[2]
            recipe.missing, recipe.text = missing, text
            p = D.prepare(awkward, recipe)
            assert np.allclose(p.pipeline.transform(awkward.X[p.test_rows]), p.X_test, atol=1e-12, equal_nan=True)
            assert np.isfinite(p.pipeline.predict_ready(awkward.X[p.test_rows])).all()   # prediction fills gaps
    assert D.prepare(awkward, D.check(awkward, qubits=2)[2]).pipeline.label_name == 'kind'


def test_reading_new_data(tmp_path, awkward):
    pipe = D.prepare(awkward, D.check(awkward, qubits=2)[2]).pipeline
    path = tmp_path / 'new.csv'                                   # reordered, extra column, unseen text, a gap
    path.write_text('weight,notes,shape,size\n6.1,x,round,1.5\n,y,square,2.2\n7.0,z,hexagon,2.9\n')
    data = D.read_for_prediction(str(path), pipe)
    assert data.X.shape == (3, 3) and data.labels is None and len(data.notes) == 2
    assert np.isfinite(pipe.predict_ready(data.X)).all()
    path.write_text('size,shape,weight,kind\n1.5,round,6.1,0\n2.2,square,7.3,1\n')
    assert D.read_for_prediction(str(path), pipe).labels == ['0', '1']           # the training label column
    path.write_text('size,weight\n1.5,6.1\n')
    with pytest.raises(ValueError, match='lacks columns.*shape'):
        D.read_for_prediction(str(path), pipe)
    path.write_text('size,shape,weight\nbig,round,6.1\n')
    with pytest.raises(ValueError, match='"big" in column size is not a number'):
        D.read_for_prediction(str(path), pipe)
    ds = D.load('mnist')
    mnist = D.prepare(ds, D.check(ds, qubits=4)[2]).pipeline
    np.savez(tmp_path / 'img.npz', images=ds.X[:5].reshape(5, 28, 28), y=ds.y[:5])
    data = D.read_for_prediction(str(tmp_path / 'img.npz'), mnist)
    assert data.X.shape == (5, 784) and data.labels == ['7', '2', '1', '0', '4']
    np.savez(tmp_path / 'bad.npz', X=np.zeros((3, 10)))
    with pytest.raises(ValueError, match='784'):
        D.read_for_prediction(str(tmp_path / 'bad.npz'), mnist)


def trained(kind, name='iris', qubits=3):
    ds = D.load(name)
    p = D.prepare(ds, D.check(ds, qubits=qubits)[2])
    if kind == 'variational':
        clf = V.Classifier(p.X_train.shape[1], layers=2, seed=1)
        clf.train(p.X_train, p.y_train, steps=20)
        return ds, p, clf.decision(p.X_test), M.from_variational(clf, p, {'method': 'BFGS'}, 1.0, 1.0, name)
    Ktr, Kte = K.kernel(p.X_train, kind='zz', bandwidth=0.5), K.kernel(p.X_test, p.X_train, kind='zz', bandwidth=0.5)
    clf = K.SVM().fit(Ktr, p.y_train) if kind == 'svm' else K.KernelRidge(0.1).fit(Ktr, p.y_train)
    settings = dict(kind='zz', reps=2, bandwidth=0.5, method=kind, strength=1.0)
    return ds, p, clf.decision(Kte), M.from_kernel(clf, p, settings, 1.0, 1.0, name)


@pytest.mark.parametrize('kind', ['svm', 'ridge', 'variational'])
def test_save_load_predict_round_trip(tmp_path, kind):
    ds, p, before, model = trained(kind)
    loaded = M.load(model.save(str(tmp_path / 'model')))
    names, values = loaded.predict(ds.X[p.test_rows])                            # raw rows in
    assert np.allclose(values, before, atol=1e-12)
    assert names == [p.classes[0] if v >= 0 else p.classes[1] for v in before]
    assert loaded.info['dataset'] == 'iris' and loaded.info['app_version'] and loaded.classes == p.classes
    if kind == 'svm':                                                            # only support vectors are stored
        assert len(loaded.arrays['points']) < len(p.X_train)


def test_loading_refuses_bad_files(tmp_path):
    _, _, _, model = trained('svm')
    good = model.save(str(tmp_path / 'good'))
    with pytest.raises(ValueError, match='not a QuantumScope model'):
        M.load(str(tmp_path / 'missing.npz'))
    np.savez(tmp_path / 'other.npz', X=np.zeros(3))
    with pytest.raises(ValueError, match='not a QuantumScope model'):
        M.load(str(tmp_path / 'other.npz'))
    np.save(tmp_path / 'pickled.npy', np.array([{'evil': 1}], dtype=object), allow_pickle=True)
    with open(tmp_path / 'pickled.npy', 'rb') as src, open(tmp_path / 'pickled.npz', 'wb') as dst:
        dst.write(src.read())
    with pytest.raises(ValueError, match='not a QuantumScope model'):
        M.load(str(tmp_path / 'pickled.npz'))                                    # never unpickled
    with np.load(good, allow_pickle=False) as z:
        arrays = {k: z[k] for k in z.files}
    header = json.loads(str(arrays['header']))

    def variant(name, **changes):
        h = dict(header, **{k: v for k, v in changes.items() if k in header or k in ('version',)})
        a = dict(arrays, header=np.array(json.dumps(h)))
        for key in changes.get('drop', ()):
            a.pop(key)
        if 'points' in changes:
            a['model_points'] = changes['points']
        np.savez(tmp_path / name, **a)
        return str(tmp_path / name)
    with pytest.raises(ValueError, match='newer QuantumScope'):
        M.load(variant('newer.npz', version=99))
    with pytest.raises(ValueError, match='incomplete'):
        M.load(variant('incomplete.npz', drop=('model_coef',)))
    with pytest.raises(ValueError, match='inconsistent'):
        M.load(variant('inconsistent.npz', points=np.zeros((2, 7))))
    np.savez(tmp_path / 'damaged.npz', header=np.array('{not json'))
    with pytest.raises(ValueError, match='damaged'):
        M.load(str(tmp_path / 'damaged.npz'))
