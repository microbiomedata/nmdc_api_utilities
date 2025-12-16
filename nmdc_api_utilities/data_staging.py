# -*- coding: utf-8 -*-
from nmdc_api_utilities.nmdc_search import NMDCSearch
import logging
import requests
from nmdc_api_utilities.auth import NMDCAuth
from nmdc_api_utilities.decorators import requires_auth
import json

logger = logging.getLogger(__name__)


class JGISequencingProjectAPI(NMDCSearch):
    """
    Class to interact with the NMDC API to get JGI samples.
    """

    def __init__(
        self,
        env="prod",
        auth: NMDCAuth = None,
        client_id: str = None,
        client_secret: str = None,
    ):
        self.env = env
        self.auth = auth or NMDCAuth(env=self.env)
        if client_id and client_secret:
            self.auth = NMDCAuth(
                client_id=client_id, client_secret=client_secret, env=self.env
            )
        elif not self.auth.has_credentials():
            raise ValueError("credentials must be provided")
        super().__init__(env=env)

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
        jgi_sequencing_project : dict
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

        url = f"{self.base_url}/wf_file_staging/jgi_sequencing_projects"
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.auth.get_token()}",
        }
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
        filter: str = None,
        max_page_size: int = 20,
        fields: str = "",
        all_pages: bool = False,
    ) -> dict:
        """
        List JGI sequencing projects from the NMDC database.

        Parameters
        ----------
        filter : str, optional
            Filter to apply to the API call.
        max_page_size : int, optional
            The maximum number of items to return per page.
        fields : str, optional
            The fields to return.
        all_pages : bool, optional
            True to return all pages. False to return the first page.

        Returns
        -------
        dict
            The list of JGI sequencing projects.
        """
        url = f"{self.base_url}/wf_file_staging/jgi_sequencing_projects"
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.auth.get_token()}",
        }
        try:
            query_params = {
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
            return self._get_all_pages(response, url, filter, max_page_size, fields)[
                "resources"
            ]

        return response.json()["resources"]

    @requires_auth
    def get_jgi_sequencing_project(self, sequencing_project_name: str) -> dict:
        """
        Get a specific JGI sequencing project by name.

        Parameters
        ----------
        project_name : str
            The name of the JGI sequencing project to retrieve.

        Returns
        -------
        dict
            The JGI sequencing project record.
        """
        url = f"{self.base_url}/wf_file_staging/jgi_sequencing_projects/{sequencing_project_name}"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self.auth.get_token()}",
        }
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


class JGISampleSearchAPI(NMDCSearch):
    """
    Class to interact with the NMDC API to get JGI samples.
    """

    def __init__(
        self,
        auth: NMDCAuth = None,
        env="prod",
        client_id: str = None,
        client_secret: str = None,
    ):
        self.env = env
        self.auth = auth or NMDCAuth(env=self.env)
        if client_id and client_secret:
            self.auth = NMDCAuth(
                client_id=client_id, client_secret=client_secret, env=self.env
            )
        else:
            raise ValueError("client_id and client_secret must be provided")
        super().__init__(env=env)

    @requires_auth
    def get_jgi_samples(
        self,
        filter: str = None,
        max_page_size: int = 20,
        fields: str = "",
        all_pages: bool = False,
    ) -> dict:
        """
        Get a specific JGI sample by name.

        Parameters
        ----------
        sample_name : str
            The name of the JGI sample to retrieve.

        Returns
        -------
        dict
            The JGI sample record.
        """

        try:
            query = filter if filter else {}
            query_params = {
                "filter": f"{json.dumps(query)}",
                "max_page_size": max_page_size,
                "projection": fields,
            }
            response = requests.get(
                self.base_url + "/wf_file_staging/jgi_samples",
                headers={"Authorization": f"Bearer {self.auth.get_token()}"},
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
                self.base_url + "/wf_file_staging/jgi_samples",
                filter,
                max_page_size,
                fields,
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
        jgi_samples : list
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
        url = f"{self.base_url}/wf_file_staging/jgi_samples"
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.auth.get_token()}",
        }
        print(headers)
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
        jgi_file_id : str
            The JGI file ID of the sample to be updated.
        jgi_sample : dict
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
        url = f"{self.base_url}/wf_file_staging/jgi_samples/{jgi_file_id}"
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.auth.get_token()}",
        }
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


class GlobusTaskAPI(NMDCSearch):
    """
    Class to interact with the NMDC API for Globus tasks.
    """

    def __init__(
        self,
        env="prod",
        auth: NMDCAuth = None,
        client_id: str = None,
        client_secret: str = None,
    ):
        self.env = env
        self.auth = auth or NMDCAuth(env=self.env)
        if client_id and client_secret:
            self.auth = NMDCAuth(
                client_id=client_id, client_secret=client_secret, env=self.env
            )
        else:
            raise ValueError("client_id and client_secret must be provided")
        super().__init__(env=env)

    @requires_auth
    def get_globus_tasks(
        self,
        filter: str = None,
        max_page_size: int = 20,
        fields: str = "",
        all_pages: bool = False,
    ) -> dict:
        """
        Get Globus tasks, optionally filtered by task_id.

        Parameters
        ----------
        task_id : str, optional
            The task_id to filter Globus tasks.

        Returns
        -------
        dict
            The list of Globus tasks.
        """
        url = f"{self.base_url}/wf_file_staging/globus_tasks"
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.auth.get_token()}",
        }
        query = filter if filter else {}
        query_params = {"filter": f"{json.dumps(query)}", "max_page_size": 20}
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
            return self._get_all_pages(response, url, filter, max_page_size, fields)[
                "resources"
            ]
        return response.json()["resources"]

    @requires_auth
    def create_globus_task(
        self,
        globus_task: dict,
    ) -> dict:
        """
        Create a new Globus task in the NMDC database.

        Parameters
        ----------
        globus_task : dict
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

        url = f"{self.base_url}/wf_file_staging/globus_tasks"
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.auth.get_token()}",
        }
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

        Parameters
        ----------
        globus_task_id: str
            The ID of the Globus task to be updated.
        globus_task : dict
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
        url = f"{self.base_url}/wf_file_staging/globus_tasks/{globus_task_id}"
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.auth.get_token()}",
        }
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
