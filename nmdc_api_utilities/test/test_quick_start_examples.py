# -*- coding: utf-8 -*-


def example_study_to_biosamples_to_data_objects(study_name: str) -> dict:
    """Example 1: from study name to biosamples and linked data objects."""

    from nmdc_api_utilities.nmdc_search import NMDCSearch
    from nmdc_api_utilities.study_search import StudySearch

    study_client = StudySearch()
    search_client = NMDCSearch()

    studies = study_client.get_record_by_attribute(
        attribute_name="name",
        attribute_value=study_name,
        exact_match=True,
    )
    if not studies:
        return {
            "study": None,
            "study_id": None,
            "biosamples": [],
            "data_objects": [],
        }

    study = studies[0]
    study_id = study["id"]

    biosamples = search_client.get_linked_instances(
        ids=[study_id],
        types=["nmdc:Biosample"],
        hydrate=True,
    )
    biosample_ids = [record["id"] for record in biosamples if "id" in record]

    data_objects = []
    if biosample_ids:
        data_objects = search_client.get_linked_instances(
            ids=biosample_ids,
            types=["nmdc:DataObject"],
            hydrate=True,
        )

    return {
        "study": study,
        "study_id": study_id,
        "biosamples": biosamples,
        "data_objects": data_objects,
    }


def example_data_object_type_to_objects_with_biosamples(data_object_type: str) -> dict:
    """Example 2: from data object type to data objects and associated biosample metadata."""

    import json

    from nmdc_api_utilities.data_object_search import DataObjectSearch
    from nmdc_api_utilities.nmdc_search import NMDCSearch

    data_object_client = DataObjectSearch()
    search_client = NMDCSearch()

    filter_str = json.dumps({"data_object_type": data_object_type})
    data_objects = data_object_client.get_record_by_filter(
        filter=filter_str,
        all_pages=True,
    )
    data_object_ids = [record["id"] for record in data_objects if "id" in record]

    if not data_object_ids:
        return {
            "data_objects": [],
            "biosamples_by_data_object": {},
        }

    associations = search_client.get_linked_instances_and_associate_ids(
        ids=data_object_ids,
        types=["nmdc:Biosample"],
        hydrate=False,
    )
    for data_object_id in data_object_ids:
        associations.setdefault(data_object_id, [])

    biosample_ids = sorted(
        {
            biosample_id
            for linked_ids in associations.values()
            for biosample_id in linked_ids
        }
    )

    biosample_records = []
    if biosample_ids:
        biosample_records = search_client.get_records_by_id(ids=biosample_ids)

    biosamples_by_id = {
        record["id"]: record for record in biosample_records if "id" in record
    }

    biosamples_by_data_object = {}
    for data_object_id in data_object_ids:
        linked_ids = associations.get(data_object_id, [])
        biosamples_by_data_object[data_object_id] = [
            biosamples_by_id[biosample_id]
            for biosample_id in linked_ids
            if biosample_id in biosamples_by_id
        ]

    return {
        "data_objects": data_objects,
        "biosamples_by_data_object": biosamples_by_data_object,
    }


def test_example_study_to_biosamples_to_data_objects(monkeypatch):
    def mock_get_record_by_attribute(
        self,
        attribute_name,
        attribute_value,
        max_page_size=25,
        fields="",
        all_pages=False,
        exact_match=False,
    ):
        assert attribute_name == "name"
        assert exact_match is True
        return [{"id": "nmdc:sty-11-demo", "name": attribute_value}]

    def mock_get_linked_instances(
        self, ids, hydrate=False, types=None, max_page_size=500
    ):
        if types == ["nmdc:Biosample"]:
            assert ids == ["nmdc:sty-11-demo"]
            return [{"id": "nmdc:bsm-11-a"}, {"id": "nmdc:bsm-11-b"}]
        if types == ["nmdc:DataObject"]:
            assert ids == ["nmdc:bsm-11-a", "nmdc:bsm-11-b"]
            return [{"id": "nmdc:dobj-11-1"}]
        raise AssertionError("Unexpected types")

    from nmdc_api_utilities.nmdc_search import NMDCSearch
    from nmdc_api_utilities.study_search import StudySearch

    monkeypatch.setattr(
        StudySearch, "get_record_by_attribute", mock_get_record_by_attribute
    )
    monkeypatch.setattr(NMDCSearch, "get_linked_instances", mock_get_linked_instances)

    result = example_study_to_biosamples_to_data_objects("Demo Study")

    assert result["study_id"] == "nmdc:sty-11-demo"
    assert len(result["biosamples"]) == 2
    assert len(result["data_objects"]) == 1


def test_example_study_to_biosamples_to_data_objects_no_match(monkeypatch):
    def mock_get_record_by_attribute(
        self,
        attribute_name,
        attribute_value,
        max_page_size=25,
        fields="",
        all_pages=False,
        exact_match=False,
    ):
        return []

    from nmdc_api_utilities.study_search import StudySearch

    monkeypatch.setattr(
        StudySearch, "get_record_by_attribute", mock_get_record_by_attribute
    )

    result = example_study_to_biosamples_to_data_objects("Missing Study")

    assert result["study_id"] is None
    assert result["biosamples"] == []
    assert result["data_objects"] == []


def test_example_data_object_type_to_objects_with_biosamples(monkeypatch):
    def mock_get_record_by_filter(
        self, filter: str, max_page_size=25, fields="", all_pages=False
    ):
        assert '"data_object_type": "Metagenome Raw Reads"' in filter
        assert all_pages is True
        return [{"id": "nmdc:dobj-11-1"}, {"id": "nmdc:dobj-11-2"}]

    def mock_get_linked_instances_and_associate_ids(
        self,
        ids,
        types=None,
        hydrate=False,
        max_page_size=500,
    ):
        assert ids == ["nmdc:dobj-11-1", "nmdc:dobj-11-2"]
        assert types == ["nmdc:Biosample"]
        return {
            "nmdc:dobj-11-1": ["nmdc:bsm-11-a", "nmdc:bsm-11-b"],
            "nmdc:dobj-11-2": ["nmdc:bsm-11-b"],
        }

    def mock_get_records_by_id(self, ids, fields=""):
        assert ids == ["nmdc:bsm-11-a", "nmdc:bsm-11-b"]
        return [
            {"id": "nmdc:bsm-11-a", "name": "A"},
            {"id": "nmdc:bsm-11-b", "name": "B"},
        ]

    from nmdc_api_utilities.data_object_search import DataObjectSearch
    from nmdc_api_utilities.nmdc_search import NMDCSearch

    monkeypatch.setattr(
        DataObjectSearch, "get_record_by_filter", mock_get_record_by_filter
    )
    monkeypatch.setattr(
        NMDCSearch,
        "get_linked_instances_and_associate_ids",
        mock_get_linked_instances_and_associate_ids,
    )
    monkeypatch.setattr(NMDCSearch, "get_records_by_id", mock_get_records_by_id)

    result = example_data_object_type_to_objects_with_biosamples("Metagenome Raw Reads")

    assert len(result["data_objects"]) == 2
    assert set(result["biosamples_by_data_object"].keys()) == {
        "nmdc:dobj-11-1",
        "nmdc:dobj-11-2",
    }
    assert len(result["biosamples_by_data_object"]["nmdc:dobj-11-1"]) == 2
    assert len(result["biosamples_by_data_object"]["nmdc:dobj-11-2"]) == 1
