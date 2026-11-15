"""v0.9.13: choosing features by annealing (no window)."""
from dataclasses import replace
from itertools import combinations

import numpy as np
import pytest

from quantumscope.ml import datasets as D
from quantumscope.ml import feature_selection as F
from quantumscope.physics import annealing as A

SOLVED = {'qml/94-lab-choose-features-by-annealing'}
MEAN = ['mean radius', 'mean texture', 'mean perimeter', 'mean area', 'mean smoothness', 'mean compactness',
        'mean concavity', 'mean concave points', 'mean symmetry', 'mean fractal dimension']


@pytest.fixture(scope='module')
def cancer():
    dataset = D.load('breast_cancer')
    recipe = D.check(dataset, qubits=3)[2]
    return dataset, recipe


@pytest.fixture(scope='module')
def task(cancer):
    dataset, recipe = cancer
    return F.make_task(dataset, recipe, 'breast_cancer', 'Breast cancer', k=3,
                       candidates=[dataset.features.index(n) for n in MEAN])


# ---- relevance and redundancy ---------------------------------------------------------------------
def test_relevance_is_the_label_correlation_for_two_classes_and_eta_for_more():
    rng = np.random.default_rng(0)
    y = rng.integers(0, 2, 300)
    X = np.c_[y + rng.normal(0, 0.5, 300), rng.normal(size=300), np.ones(300)]
    expected = abs(np.corrcoef(X[:, 0], y)[0, 1])
    rel = F.relevance(X, y)
    assert rel[0] == pytest.approx(expected) and rel[1] < 0.2 and rel[2] == 0.0
    y3 = np.repeat([0, 1, 2], 50)
    perfect = np.c_[y3 * 10.0, rng.normal(size=150)]
    rel3 = F.relevance(perfect, y3)
    assert rel3[0] == pytest.approx(1.0) and 0 <= rel3[1] < 0.3


def test_redundancy_finds_the_near_copies(task):
    R = F.redundancy(task.prepared.X_train)
    names = task.names
    assert np.allclose(R, R.T) and np.allclose(np.diag(R), 1) and R.min() >= 0
    assert R[names.index('mean radius'), names.index('mean perimeter')] > 0.99
    assert R[names.index('mean radius'), names.index('mean texture')] < 0.5


# ---- the Ising problem ------------------------------------------------------------------------------
def brute(rel, R, k, alpha):
    """The best k-subset by the energy, checked directly."""
    def energy(s):
        return -alpha * sum(rel[i] for i in s) + (1 - alpha) * sum(R[i][j] for i, j in combinations(s, 2))
    return min(combinations(range(len(rel)), k), key=energy)


def test_the_spin_form_has_the_same_energy_as_the_qubo():
    rng = np.random.default_rng(1)
    n, k, alpha, penalty = 5, 2, 0.6, 0.8
    rel = rng.uniform(0, 1, n)
    R = np.abs(np.corrcoef(rng.normal(size=(n, 40))))
    c, h, J = F.qubo(rel, R, k, alpha, penalty)
    problem = A.from_terms('t', 't', n, F.ising_terms(c, h, J))
    for x in range(1 << n):
        bits = np.array([int(b) for b in format(x, f'0{n}b')])
        direct = -alpha * rel @ bits + (1 - alpha) * bits @ np.triu(R, 1) @ bits + penalty * (bits.sum() - k) ** 2
        assert problem.diagonal[x] == pytest.approx(direct)


def test_the_lectures_worked_example():
    rel = [0.80, 0.75, 0.50]
    R = np.array([[1, 0.95, 0.20], [0.95, 1, 0.25], [0.20, 0.25, 1]])
    assert brute(rel, R, 2, 0.7) == (0, 2)                    # features 1 and 3
    assert brute(rel, R, 2, 1.0) == (0, 1)                    # α = 1: greedy, the near-copies


def test_the_answer_keeps_k_and_is_the_best_choice(task):
    problem = F.problem(task)
    answers = problem.solutions()
    rel = task.relevance[task.candidates]
    R = F.redundancy(task.prepared.X_train[:, task.candidates])
    assert all(a.count('1') == 3 for a in answers)
    assert tuple(F.subset(answers[0])) == brute(rel, R, 3, task.alpha)
    assert [task.candidate_names[i] for i in F.subset(answers[0])] == ['mean texture', 'mean perimeter',
                                                                         'mean concave points']
    coefficients = [abs(v) for v, q in problem.terms if q]
    assert max(coefficients) == pytest.approx(1.0)            # scaled like the other problems
    assert problem.penalty < F.penalty_for(rel, R, 3, task.alpha)       # smaller than the safe bound
    weaker = replace(task, alpha=1.0)
    assert [weaker.candidate_names[i] for i in F.subset(F.problem(weaker).solutions()[0])] == \
        ['mean radius', 'mean perimeter', 'mean concave points']          # greedy
    assert F.greedy(task) == F.subset(F.problem(weaker).solutions()[0])


def test_the_choice_never_sees_the_test_samples(cancer, task):
    dataset, recipe = cancer
    p = task.prepared
    assert not set(p.train_rows) & set(p.test_rows)
    assert np.allclose(task.relevance, F.relevance(p.X_train, p.y_train))
    scrambled = replace(dataset, X=dataset.X.copy())
    scrambled.X[p.test_rows] = np.random.default_rng(3).normal(size=scrambled.X[p.test_rows].shape)
    again = F.make_task(scrambled, recipe, 'breast_cancer', 'scrambled', k=3, candidates=task.candidates)
    assert np.allclose(again.relevance, task.relevance)


def test_bad_tasks_are_refused(cancer, task):
    with pytest.raises(ValueError, match='candidate'):
        F.problem(replace(task, candidates=list(range(11))))
    with pytest.raises(ValueError, match='Keep between'):
        F.problem(replace(task, k=10))
    penguins = D.load('penguins')                             # values are missing
    recipe = replace(D.check(penguins, qubits=3)[2], missing='none')
    with pytest.raises(ValueError, match='missing'):
        F.make_task(penguins, recipe, 'penguins', 'Penguins')


def test_the_default_candidates_are_the_most_relevant(cancer):
    dataset, recipe = cancer
    t = F.make_task(dataset, recipe, 'breast_cancer', 'Breast cancer', k=3)
    assert len(t.candidates) == 10
    assert min(t.relevance[t.candidates]) >= max(np.delete(t.relevance, t.candidates))


# ---- reads -------------------------------------------------------------------------------------------
def test_reads_keep_the_best_valid_choice(task):
    problem = F.problem(task)
    slow = A.anneal(problem, 20, record=2)
    reads = F.read_out(problem, slow.probabilities[-1], shots=100, seed=0)
    assert sum(reads.counts.values()) == 100 and reads.choices == 120
    assert reads.best in problem.solutions() and reads.rank == 1 and reads.hits >= 1
    assert reads.valid == sum(c for b, c in reads.counts.items() if b.count('1') == 3)
    assert F.read_out(problem, slow.probabilities[-1], shots=100, seed=0) == reads          # repeatable
    uniform = np.full(1 << 10, 1 / 1024)
    fast = F.read_out(problem, uniform, shots=2000, seed=1)
    assert fast.valid / 2000 == pytest.approx(120 / 1024, abs=0.03)                           # random bitstrings
    nothing = F.read_out(problem, np.eye(1 << 10)[0], shots=10)                               # all zeros: none valid
    assert nothing.best == '' and nothing.rank == 0 and nothing.valid == 0


def test_the_comparison_scores_every_way_of_reducing(task):
    rows = F.compare(task, F.subset(F.problem(task).solutions()[0]))
    assert [r.method for r in rows] == ['Annealed', 'Most relevant alone (greedy)', 'PCA (3 components of all 30)',
                                        'All 10 candidates']
    assert all(0 <= r.accuracy <= 1 for r in rows)
    assert rows[0].redundancy < 0.6 < rows[1].redundancy           # the annealed choice repeats itself less


# ---- the Datasets tab keeps the chosen features --------------------------------------------------------
def test_prepare_keeps_the_chosen_features_instead_of_pca(cancer):
    dataset, recipe = cancer
    chosen = ('mean texture', 'mean perimeter', 'mean concave points')
    p = D.prepare(dataset, replace(recipe, select=chosen, components=3))
    assert p.features == list(chosen) and p.X_train.shape[1] == 3
    assert any('Kept 3 chosen features' in step for step in p.steps) and not any('PCA' in s for s in p.steps)
    assert np.allclose(p.pipeline.transform(dataset.X[p.test_rows]), p.X_test)    # new data: the same columns
    arrays, header = p.pipeline.to_arrays()
    again = D.Pipeline.from_arrays(arrays, header)
    assert np.array_equal(again.select, p.pipeline.select)
    assert np.allclose(again.transform(dataset.X[p.test_rows]), p.X_test)
    with pytest.raises(ValueError, match='not in the data'):
        D.prepare(dataset, replace(recipe, select=('no such feature',)))


def test_the_problem_is_listed_but_needs_data():
    assert ('Feature selection (from data)', 'features') in A.PROBLEMS
    with pytest.raises(ValueError, match='dataset'):
        A.build('features')


def test_a_tolerance_counts_near_best_answers():
    problem = A.from_terms('t', 't', 2, [(1.0, (0,)), (0.02, (1,))])        # 11: −1.02, 10: −0.98
    assert problem.solutions() == ['11']
    assert len(replace(problem, tolerance=0.05).solutions()) == 2


# ---- the lab -------------------------------------------------------------------------------------------
def test_the_lab_can_be_completed(task):
    from quantumscope.learn import labs, progress as learn
    from quantumscope.learn.lessons import builtin_lessons
    from quantumscope.learn.render import steps_of
    from quantumscope.editor.circuit_model import CircuitModel
    from quantumscope.ml import kernels as K, progress
    lesson = next(l for l in builtin_lessons() if l.key == 'qml/94-lab-choose-features-by-annealing')
    steps = steps_of(lesson.body)
    learn.reset()
    progress.reset()
    model = CircuitModel(1)
    assert not any(labs.progress(model, steps).values())

    def anneal(t, T):
        problem = F.problem(t)
        result = A.anneal(problem, T, record=2, ground=False)
        reads = F.read_out(problem, result.probabilities[-1], 100)
        chosen = [t.candidate_names[i] for i in F.subset(reads.best)]
        learn.record('features', dataset=t.source, k=t.k, alpha=t.alpha, candidates=len(t.candidates), T=T,
                     reads=100, valid=reads.valid, hits=reads.hits, rank=reads.rank, chosen='+'.join(chosen))
        return chosen
    chosen = anneal(task, 20)
    assert chosen == ['mean texture', 'mean perimeter', 'mean concave points']
    anneal(task, 0.5)
    anneal(replace(task, alpha=1.0), 20)
    p = D.prepare(task.dataset, replace(task.recipe, select=tuple(chosen), scale='pi'))
    learn.record('featuresused', dataset='breast_cancer', k=3, chosen='+'.join(chosen))
    progress.prepared('breast_cancer', 3, p.classes)
    Ktr, Kte = K.kernel(p.X_train, kind='angle'), K.kernel(p.X_test, p.X_train, kind='angle')
    svm = K.classifier('svm', 1.0).fit(Ktr, p.y_train)
    progress.trained('kernel', train=K.accuracy(p.y_train, svm.predict(Ktr)), test=K.accuracy(p.y_test, svm.predict(Kte)),
                     map='angle', bandwidth=1.0, shots=0)
    done = labs.progress(model, steps)
    assert all(done.values()), (done, learn.EVENTS)
    learn.reset()
    progress.reset()
