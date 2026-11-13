"""v0.9.8: every lecture in the agreed shape, four questions each, and a study guide per area."""
import re

import pytest

from quantumscope.learn import actions
from quantumscope.learn.lessons import AREAS, builtin_lessons, search

LESSONS = builtin_lessons()
LECTURES = [l for l in LESSONS if l.kind == 'lecture']
SECTIONS = ['The idea', 'Worked example', 'Common mistakes', 'In the app', 'Check your understanding', 'Summary']


def words(lesson):
    body = re.sub(r'```.*?```', ' ', lesson.body, flags=re.S)          # questions are counted separately
    return len(re.sub(r'\$\$.*?\$\$', ' x ', body, flags=re.S).split())


@pytest.mark.parametrize('lesson', LECTURES, ids=[l.key for l in LECTURES])
def test_every_lecture_has_the_six_sections_in_order(lesson):
    headings = re.findall(r'^## (.+)$', lesson.body, re.M)
    assert headings[0] == 'The idea', lesson.key
    positions = [headings.index(name) for name in SECTIONS]
    assert positions == sorted(positions), (lesson.key, headings)
    assert headings[-1] == 'Summary'


@pytest.mark.parametrize('lesson', LECTURES, ids=[l.key for l in LECTURES])
def test_every_lecture_is_descriptive_with_at_least_four_questions(lesson):
    assert lesson.body.count('```quiz') >= 4, lesson.key
    assert words(lesson) >= 450, (lesson.key, words(lesson))
    app = lesson.body.split('## In the app', 1)[1].split('## ', 1)[0]
    assert len(app.split()) >= 25                                        # says what to do, not just a link


def test_no_stray_control_characters_or_escaped_quotes():
    for lesson in LESSONS:
        assert not re.search(r'[\x07\x08\x0b\x0c\r\t]', lesson.body), lesson.key
        assert '\\"' not in lesson.body, lesson.key


@pytest.mark.parametrize('area', list(AREAS))
def test_each_area_has_one_study_guide_that_links_everything(area):
    mine = [l for l in LESSONS if l.area == area]
    guides = [l for l in mine if l.kind == 'guide']
    assert len(guides) == 1 and guides[0].order == 0 and mine[0] is guides[0]          # listed first
    guide = guides[0]
    linked = set(re.findall(r'\(qs:lesson/([^)\s]+)\)', guide.body))
    for lesson in mine:
        if lesson is not guide:
            assert lesson.key in linked, (area, lesson.key)
    for link in re.findall(r'\]\((qs:[^)\s]+)\)', guide.body):
        action = actions.parse(link)
        assert action.kind != 'lesson' or any(l.key == action.target for l in LESSONS)
    for name in ('What this area is about', 'Before you start', 'Suggested path', 'Check yourself at the end'):
        assert f'## {name}' in guide.body


def test_lessons_count_and_questions_added():
    assert sum(l.kind == 'guide' for l in LESSONS) == 5 and len(LECTURES) == 62
    assert sum(l.body.count('```quiz') for l in LECTURES) >= 4 * 62


def test_search_prefers_a_section_about_the_word():
    assert search(LESSONS, 'hadamard')[0].key == 'circuits/02-single-qubit-gates'     # its heading is "The Hadamard gate"
    assert search(LESSONS, 'deferred')[0].key == 'circuits/16-deferred-measurement'


def test_worked_examples_match_the_physics():
    import math
    from quantumscope.physics import algorithms as A
    text = {l.key: l.body for l in LESSONS}
    assert '0.951' in text['qml/01-data-to-quantum-states']
    assert round(math.cos(0.2) ** 2 * math.cos(0.1) ** 2, 3) == 0.951
    assert '0.685' in text['circuits/21-phase-estimation']
    n = 16
    p = abs(sum(complex(math.cos(2 * math.pi * k * (1 / 3 - 5 / n)), math.sin(2 * math.pi * k * (1 / 3 - 5 / n)))
                for k in range(n)) / n) ** 2
    assert round(p, 3) == 0.685
    h2 = text['circuits/24-vqe']
    assert '-1.116998' in h2 and '1.137306' in h2
    assert A.H2_HAMILTONIAN.startswith('-0.332404256824 - 0.397937424843 Z0 + 0.397937424843 Z1 - 0.011280104256')
