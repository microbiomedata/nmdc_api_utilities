# -*- coding: utf-8 -*-
import json
import logging
from typing import Any

import requests

from nmdc_api_utilities.api_client import NMDCAPIClient
from nmdc_api_utilities.auth import NMDCAuth
from nmdc_api_utilities.config import API_BASE_URL
from nmdc_api_utilities.decorators import requires_auth

logger = logging.getLogger(__name__)


class JGISequencingProjectAPI(NMDCAPIClient):
    """
    Class to interact with the NMDC API to get JGI samples.

    Parameters
    ----------
    auth
        The NMDCAuth instance containing the credentials and API base URL for authentication.
    api_base_url
        The base URL of an instance of the NMDC Runtime API. By default, this is the base URL of the production instance.
    env
        Deprecated. Use `api_base_url` instead. Previously used to specify the API environment (e.g., "prod", "dev").
    """

    def __init__(
        self,
        auth: NMDCAuth,
        api_base_url: str = API_BASE_URL,
        env: str = "",
    ):
        self.auth = auth
        if not self.auth.has_credentials():
            raise ValueError("credentials must be provided")
        super().__init__(
            api_base_url=api_base_url,
            env=env,
        )
        # make sure the `api_base_url` is the same
        # TODO: Use a global "settings" object to store the `api_base_url` in a single place.
        #       Example: https://github.com/pydantic/pydantic-settings
        if self.auth.api_base_url != self.api_base_url:
            raise ValueError(
                "`api_base_url` must be the same for NMDCAuth and JGISequencingProjectAPI"
            )

    @requires_auth
    def create_jgi_sequencing_project(
        self,
        jgi_sequencing_project: dict,
    ) -> dict:
        """
        Create a new JGI sequencing project in the NMDC database.
        For more information on available keys, visit the NMDC API Docs
        https://api.microbiomedata.org/docs#/Workflow%20management/create_sequencing_record_wf_file_staging_jgi_sequencing_projects_post

        Parameters
        ----------
        jgi_sequencing_project
            The JGI sequencing project data to be created.

        Returns
        -------
        dict
            The created JGI sequencing project record.

        Raises
        ------
        Exception
            If the creation fails.
        """

        url = f"{self.api_base_url}/wf_file_staging/jgi_sequencing_projects"
        headers = self._build_http_request_headers(
            access_token=self.auth.get_token(),
            accept="application/json",
            content_type="application/json",
        )
        try:
            response = requests.post(url, headers=headers, json=jgi_sequencing_project)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise RuntimeError("Failed to add new JGI sequencing project") from e
        else:
            logging.debug(
                f"API request response: {response.json()}\n API Status Code: {response.status_code}"
            )

        return response.json()

    @requires_auth
    def list_jgi_sequencing_projects(
        self,
        filter: str | None = None,
        max_page_size: int = 20,
        fields: str = "",
        all_pages: bool = False,
    ) -> list[dict[str, Any]]:
        """
        List JGI sequencing projects from the NMDC database.

        Parameters
        ----------
        filter
            Filter to apply to the API call.
        max_page_size
            The maximum number of items to return per page.
        fields
            The fields to return.
        all_pages
            True to return all pages. False to return the first page.

        Returns
        -------
        list
            The list of JGI sequencing projects.
        """
        url = f"{self.api_base_url}/wf_file_staging/jgi_sequencing_projects"
        headers = self._build_http_request_headers(
            access_token=self.auth.get_token(),
            accept="application/json",
            content_type="application/json",
        )
        try:
            # Note: The `dict` is here to appease mypy, which, for some reason, doesn't infer that
            #       the dictionary being assigned here is sufficient to pass to `requests.get`.
            query_params: dict = {
                "filter": f"{json.dumps(filter)}",
                "max_page_size": max_page_size,
                "projection": fields,
            }
            response = requests.get(url, headers=headers, params=query_params)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise RuntimeError("Failed to retrieve JGI sequencing projects") from e
        else:
            logging.debug(
                f"API request response: {response.json()}\n API Status Code: {response.status_code}"
            )
        if all_pages:
            return self._get_all_pages(
                response,
                url,
                filter or "",
                max_page_size,
                fields,
                access_token=self.auth.get_token(),
            )["resources"]

        return response.json()["resources"]

    @requires_auth
    def get_jgi_sequencing_project_by_name(self, project_name: str) -> dict:
        """
        Get a specific JGI sequencing project by name.

        Parameters
        ----------
        project_name
            The name of the JGI sequencing project to retrieve.

        Returns
        -------
        dict
            The JGI sequencing project record.
        """
        url = f"{self.api_base_url}/wf_file_staging/jgi_sequencing_projects/{project_name}"
        headers = self._build_http_request_headers(
            access_token=self.auth.get_token(),
            accept="application/json",
            content_type="application/json",
        )
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise RuntimeError("Failed to retrieve JGI sequencing project") from e
        else:
            logging.debug(
                f"API request response: {response.json()}\n API Status Code: {response.status_code}"
            )

        return response.json()


class JGISampleSearchAPI(NMDCAPIClient):
    """
    Class to interact with the NMDC API to get JGI samples.

    Parameters
    ----------
    auth
        The NMDCAuth instance containing the credentials and API base URL for authentication.
    api_base_url
        The base URL of an instance of the NMDC Runtime API. By default, this is the base URL of the production instance.
    env
        Deprecated. Use `api_base_url` instead. Previously used to specify the API environment (e.g., "prod", "dev").
    """

    def __init__(
        self,
        auth: NMDCAuth,
        api_base_url: str = API_BASE_URL,
        env: str = "",
    ):
        self.auth = auth
        if not self.auth.has_credentials():
            raise ValueError("credentials must be provided")
        super().__init__(
            api_base_url=api_base_url,
            env=env,
        )
        # make sure the `api_base_url` is the same
        # TODO: Use a global "settings" object to store the `api_base_url` in a single place.
        #       Example: https://github.com/pydantic/pydantic-settings
        if self.auth.api_base_url != self.api_base_url:
            raise ValueError(
                "`api_base_url` must be the same for NMDCAuth and JGISampleSearchAPI"
            )

    @requires_auth
    def list_jgi_samples(
        self,
        filter: str | None = None,
        max_page_size: int = 20,
        fields: str = "",
        all_pages: bool = False,
    ) -> list[dict]:
        """
        Get a specific JGI sample by name.

        Parameters
        ----------
        filter
            Filter to apply to the API call.
        max_page_size
            The maximum number of items to return per page.
        fields
            The fields to return.
        all_pages
            True to return all pages. False to return the first page.

        Returns
        -------
        list[dict]
            The list of JGI sample records.
        """
        url = f"{self.api_base_url}/wf_file_staging/jgi_samples"
        try:
            query = filter if filter else {}
            query_params: dict[str, str | int] = {
                "filter": f"{json.dumps(query)}",
                "max_page_size": max_page_size,
                "projection": fields,
            }
            response = requests.get(
                url,
                headers=self._build_http_request_headers(
                    access_token=self.auth.get_token(),
                    accept="application/json",
                    content_type="application/json",
                ),
                params=query_params,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise RuntimeError("Failed to retrieve JGI samples") from e
        else:
            logging.debug(
                f"API request response: {response.json()}\n API Status Code: {response.status_code}"
            )
        if all_pages:
            return self._get_all_pages(
                response,
                url,
                filter or "",
                max_page_size,
                fields,
                self.auth.get_token(),
            )["resources"]

        return response.json()["resources"]

    @requires_auth
    def insert_jgi_sample(
        self,
        jgi_sample: dict,
    ) -> dict:
        """
        Insert JGI samples into the NMDC database.
        For more information on keys, visit the NMDC API Docs
        https://api.microbiomedata.org/docs#/Workflow%20management/create_jgi_sample_wf_file_staging_jgi_samples_post

        Parameters
        ----------
        jgi_sample
            The JGI sample data to be inserted.

        Returns
        -------
        dict
            The response from the insertion operation.

        Raises
        ------
        Exception
            If the insertion fails.
        """
        url = f"{self.api_base_url}/wf_file_staging/jgi_samples"
        headers = self._build_http_request_headers(
            access_token=self.auth.get_token(),
            accept="application/json",
            content_type="application/json",
        )
        try:
            response = requests.post(url, headers=headers, json=jgi_sample)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise RuntimeError("Failed to insert JGI samples") from e
        else:
            logging.debug(
                f"API request response: {response.json()}\n API Status Code: {response.status_code}"
            )

        return response.json()

    @requires_auth
    def update_jgi_sample(
        self,
        jgi_file_id: str,
        jgi_sample: dict,
    ) -> dict:
        """
        Update JGI samples in the NMDC database.
        For more information on available keys, visit the NMDC API Docs
        https://api.microbiomedata.org/docs#/Workflow%20management/update_jgi_samples_wf_file_staging_jgi_samples__jdp_file_id__patch

        Parameters
        ----------
        jgi_file_id
            The JGI file ID of the sample to be updated.
        jgi_sample
            The updated JGI sample data.

        Returns
        -------
        dict
            The response from the update operation.

        Raises
        ------
        Exception
            If the update fails.
        """
        url = f"{self.api_base_url}/wf_file_staging/jgi_samples/{jgi_file_id}"
        headers = self._build_http_request_headers(
            access_token=self.auth.get_token(),
            accept="application/json",
            content_type="application/json",
        )
        try:
            response = requests.patch(url, headers=headers, json=jgi_sample)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise RuntimeError("Failed to update JGI samples") from e
        else:
            logging.debug(
                f"API request response: {response.json()}\n API Status Code: {response.status_code}"
            )

        return response.json()


class GlobusTaskAPI(NMDCAPIClient):
    """
    Class to interact with the NMDC API for Globus tasks.

    Parameters
    ----------
    auth
        The NMDCAuth instance containing the credentials and API base URL for authentication.
    api_base_url
        The base URL of an instance of the NMDC Runtime API. By default, this is the base URL of the production instance.
    env
        Deprecated. Use `api_base_url` instead. Previously used to specify the API environment (e.g., "prod", "dev").
    """

    def __init__(
        self,
        auth: NMDCAuth,
        api_base_url: str = API_BASE_URL,
        env: str = "",
    ):
        self.auth = auth
        if not self.auth.has_credentials():
            raise ValueError("credentials must be provided")
        super().__init__(
            api_base_url=api_base_url,
            env=env,
        )
        # make sure the `api_base_url` is the same
        # TODO: Use a global "settings" object to store the `api_base_url` in a single place.
        #       Example: https://github.com/pydantic/pydantic-settings
        if self.auth.api_base_url != self.api_base_url:
            raise ValueError(
                "`api_base_url` must be the same for NMDCAuth and GlobusTaskAPI"
            )

    @requires_auth
    def list_globus_tasks(
        self,
        filter: str | None = None,
        max_page_size: int = 20,
        fields: str = "",
        all_pages: bool = False,
    ) -> list[dict]:
        """
        Get Globus tasks from the NMDC database.

        Parameters
        ----------
        filter
            Filter to apply to the API call.
        max_page_size
            The maximum number of items to return per page.
        fields
            The fields to return.
        all_pages
            True to return all pages. False to return the first page.

        Returns
        -------
        list[dict]
            The list of Globus task records.
        """
        url = f"{self.api_base_url}/wf_file_staging/globus_tasks"
        headers = self._build_http_request_headers(
            access_token=self.auth.get_token(),
            accept="application/json",
            content_type="application/json",
        )
        query_params: dict[str, str | int] = {
            "filter": f"{json.dumps(filter)}",
            "max_page_size": max_page_size,
            "projection": fields,
        }
        try:
            response = requests.get(url, headers=headers, params=query_params)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise RuntimeError("Failed to retrieve Globus tasks") from e
        else:
            logging.debug(
                f"API request response: {response.json()}\n API Status Code: {response.status_code}"
            )
        if all_pages:
            return self._get_all_pages(
                response,
                url,
                filter or "",
                max_page_size,
                fields,
                self.auth.get_token(),
            )["resources"]
        return response.json()["resources"]

    @requires_auth
    def create_globus_task(
        self,
        globus_task: dict,
    ) -> dict:
        """
        Create a new Globus task in the NMDC database.
        For more information on available keys, visit the NMDC API Docs
        https://api.microbiomedata.org/docs#/Workflow%20management/create_globus_tasks_wf_file_staging_globus_tasks_post

        Parameters
        ----------
        globus_task
            The Globus task data to be created.

        Returns
        -------
        dict
            The created Globus task record.

        Raises
        ------
        Exception
            If the creation fails.
        """

        url = f"{self.api_base_url}/wf_file_staging/globus_tasks"
        headers = self._build_http_request_headers(
            access_token=self.auth.get_token(),
            accept="application/json",
            content_type="application/json",
        )
        try:
            response = requests.post(url, headers=headers, json=globus_task)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise RuntimeError("Failed to add new Globus task") from e
        else:
            logging.debug(
                f"API request response: {response.json()}\n API Status Code: {response.status_code}"
            )

        return response.json()

    @requires_auth
    def update_globus_task(
        self,
        globus_task_id: str,
        globus_task: dict,
    ) -> dict:
        """
        Update a Globus task in the NMDC database.
        For more information on available keys, visit the NMDC API Docs
        https://api.microbiomedata.org/docs#/Workflow%20management/update_globus_tasks_wf_file_staging_globus_tasks__task_id__patch

        Parameters
        ----------
        globus_task_id
            The ID of the Globus task to be updated.
        globus_task
            The Globus task data to be updated.

        Returns
        -------
        dict
            The updated Globus task record.

        Raises
        ------
        Exception
            If the update fails.
        """
        url = f"{self.api_base_url}/wf_file_staging/globus_tasks/{globus_task_id}"
        headers = self._build_http_request_headers(
            access_token=self.auth.get_token(),
            accept="application/json",
            content_type="application/json",
        )
        try:
            response = requests.patch(url, headers=headers, json=globus_task)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise RuntimeError("Failed to update Globus task") from e
        else:
            logging.debug(
                f"API request response: {response.json()}\n API Status Code: {response.status_code}"
            )

        return response.json()
