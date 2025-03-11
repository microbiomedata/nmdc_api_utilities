# -*- coding: utf-8 -*-
from nmdc_api_utilities.study_search import StudySearch


def test_find_study_by_attribute():
    st = StudySearch()
    stu = st.get_record_by_attribute(
        "name",
        "Lab enrichment of tropical soil microbial communities from Luquillo Experimental Forest, Puerto Rico",
    )
    assert len(stu) > 0

def test_find_study_by_id():
    st = StudySearch()
    stu = st.get_record_by_id("nmdc:sty-11-8fb6t785")
    assert len(stu) > 0
    assert stu["id"] == "nmdc:sty-11-8fb6t785"

def test_find_study_by_filter():
    st = StudySearch()
    stu = st.get_record_by_filter(
        '{"name":"Lab enrichment of tropical soil microbial communities from Luquillo Experimental Forest, Puerto Rico"}'
    )
    assert len(stu) > 0
    assert (
        stu[0]["name"]
        == "Lab enrichment of tropical soil microbial communities from Luquillo Experimental Forest, Puerto Rico"
    )


def test_get_studies_all_pages():
    st = StudySearch()
    studies = st.get_records(max_page_size=20, all_pages=True)
    print(studies)
    assert len(studies) > 32


def test_get_studies():
    st = StudySearch()
    studies = st.get_records(max_page_size=100)
    print(studies)
    assert len(studies) == 32
