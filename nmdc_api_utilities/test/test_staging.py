# -*- coding: utf-8 -*-
from nmdc_api_utilities.data_staging import (
    JGISampleSearchAPI,
    JGISequencingProjectAPI,
    GlobusTaskAPI,
)

import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def mock_get_response():
    with patch("requests.get") as mock_get:
        yield mock_get


@pytest.fixture
def mock_post_response():
    with patch("requests.post") as mock_post:
        yield mock_post


@pytest.fixture
def mock_patch_response():
    with patch("requests.patch") as mock_patch:
        yield mock_patch


@pytest.fixture
def mock_auth():
    with patch(
        "nmdc_api_utilities.data_staging.NMDCAuth",
        env="dev",
        client_id="test",
        client_secret="test",
    ) as mock_auth:
        mock_auth_api_response = MagicMock()
        mock_auth_api_response.get_token.return_value = "abcd123"
        mock_auth_api_response.has_credentials.return_value = True
        mock_auth.return_value = mock_auth_api_response
        mock_auth.status_code.return_value = 200
        yield mock_auth


def test_list_sequencing_projects(mock_auth, mock_get_response):
    mock_get_response.return_value.json.return_value = {
        "resources": [{"key1": "value1"}, {"key2": "value2"}]
    }
    client = JGISequencingProjectAPI(env="dev", auth=mock_auth)
    url = "http://example.com/api"
    result = client.list_jgi_sequencing_projects()
    assert result == [{"key1": "value1"}, {"key2": "value2"}]
    mock_get_response.assert_called_once()


def test_create_sequencing_project(mock_auth, mock_post_response):
    mock_post_response.return_value.json.return_value = {"resources": {"key": "value"}}
    client = JGISequencingProjectAPI(env="dev", auth=mock_auth)
    url = "http://example.com/api"
    result = client.create_jgi_sequencing_project({"key": "value"})
    assert result == {"resources": {"key": "value"}}
    mock_post_response.assert_called_once()


def test_get_sequencing_projects(mock_auth, mock_get_response):
    mock_get_response.return_value.json.return_value = {"resources": {"key1": "value1"}}
    client = JGISequencingProjectAPI(env="dev", auth=mock_auth)
    result = client.list_jgi_sequencing_projects()
    assert result == {"key1": "value1"}
    mock_get_response.assert_called_once()


def test_get_jgi_samples(mock_auth, mock_get_response):
    mock_get_response.return_value.json.return_value = {"resources": {"key1": "value1"}}
    client = JGISampleSearchAPI(env="dev", auth=mock_auth)
    url = "http://example.com/api"
    result = client.list_jgi_samples({"key1": "value1"})
    assert result == {"key1": "value1"}
    mock_get_response.assert_called_once()
    assert len(mock_get_response.call_args) == 2
    assert (
        mock_get_response.call_args[0][0]
        == "https://api-dev.microbiomedata.org/wf_file_staging/jgi_samples"
    )


def test_insert_jgi_samples(mock_auth, mock_post_response):
    mock_post_response.return_value.json.return_value = {"resources": {"key": "value"}}
    client = JGISampleSearchAPI(env="dev", auth=mock_auth)
    result = client.insert_jgi_sample({"key": "value"})
    assert result == {"resources": {"key": "value"}}
    mock_post_response.assert_called_once()


def test_update_jgi_samples(mock_auth, mock_patch_response):
    mock_patch_response.return_value.json.return_value = {"resources": {"key": "value"}}
    client = JGISampleSearchAPI(env="dev", auth=mock_auth)
    result = client.update_jgi_sample("sample", {"sample": "value"})
    assert result == {"resources": {"key": "value"}}
    mock_patch_response.assert_called_once()


def test_get_globus_tasks(mock_get_response, mock_auth):
    mock_get_response.return_value.json.return_value = {
        "resources": {"task_id": "54321", "task_status": "ACTIVE"}
    }
    client = GlobusTaskAPI(env="dev", auth=mock_auth)
    result = client.list_globus_tasks({"task_status": {"$ne": "SUCCEEDED"}})
    assert result == {"task_id": "54321", "task_status": "ACTIVE"}


def test_create_globus_task(mock_auth, mock_post_response):
    mock_post_response.return_value.json.return_value = {
        "resources": {"task_id": "54321", "task_status": "ACTIVE"}
    }
    client = GlobusTaskAPI(env="dev", auth=mock_auth)
    result = client.create_globus_task({"task_id": "54321", "task_status": "ACTIVE"})
    assert result == {"resources": {"task_id": "54321", "task_status": "ACTIVE"}}


def test_update_globus_task(mock_auth, mock_patch_response):
    mock_patch_response.return_value.json.return_value = {
        "resources": {"task_id": "54321", "task_status": "ACTIVE"}
    }
    client = GlobusTaskAPI(env="dev", auth=mock_auth)
    result = client.update_globus_task(
        "54321", {"task_id": "54321", "task_status": "ACTIVE"}
    )
    assert result == {"resources": {"task_id": "54321", "task_status": "ACTIVE"}}
