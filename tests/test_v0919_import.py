"""v0.9.19: a .csv is read as a table first, then the label column and the columns to use are
chosen (no window)."""
import numpy as np
import pytest

from quantumscope.ml import datasets as D

CSV = 'id,height,colour,group,width\n1,1.5,red,A,2\n2,2.0,blue,B,?\n3,1.7,red,A,2.5\n4,2.2,,B,3\n5,1.9,red,A,2.8\n'


@pytest.fixture
def path(tmp_path):
    p = tmp_path / 'plants.csv'
    p.write_text(CSV)
    return str(p)


def test_the_table_is_read_with_its_columns_described(path):
    t = D.read_table(path)
    assert t.header and t.names == ['id', 'height', 'colour', 'group', 'width'] and len(t.rows) == 5
    assert t.describe(1) == ('number', 5, 0) and t.describe(2) == ('text', 2, 1) and t.describe(4)[2] == 1
    assert t.looks_like_an_id(0) and not t.looks_like_an_id(1) and not t.looks_like_an_id(3)
    assert t.guess_label() == 4                                      # no column named label: the last


def test_any_column_can_be_the_label_and_any_left_out(path):
    t = D.read_table(path)
    ds = D.table_dataset(t, 'group', leave_out=['id'])
    assert ds.classes == ['A', 'B'] and ds.y.tolist() == [0, 1, 0, 1, 0] and ds.label_name == 'group'
    assert ds.features == ['height', 'colour', 'width'] and ds.text_columns == {1: ['blue', 'red']}
    by_index = D.import_file(path, label=3, leave_out=[0, 2])
    assert by_index.features == ['height', 'width'] and np.array_equal(by_index.y, ds.y)


def test_a_wrong_choice_is_explained(path):
    t = D.read_table(path)
    with pytest.raises(ValueError, match='empty cells'):
        D.table_dataset(t, 'width')                                   # '?' is missing: a sample without a class
    with pytest.raises(ValueError, match='at least one column'):
        D.table_dataset(t, 'group', leave_out=['id', 'height', 'colour', 'width'])
    with pytest.raises(ValueError, match='no column named'):
        D.table_dataset(t, 'species')


def test_only_one_class_is_refused(tmp_path):
    p = tmp_path / 'one.csv'
    p.write_text('x,label\n1,a\n2,a\n')
    with pytest.raises(ValueError, match='only one value'):
        D.import_file(str(p))


def test_the_header_can_be_overruled(tmp_path):
    p = tmp_path / 'numbers.csv'
    p.write_text('1,2,0\n3,4,1\n5,6,1\n')
    assert not D.read_table(str(p)).header
    t = D.read_table(str(p), header=True)                           # the first row taken as names
    assert t.names == ['1', '2', '0'] and len(t.rows) == 2
