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

    def __init__(self, env="prod", auth: NMDCAuth = None):
        self.env = env
        self.auth = auth or NMDCAuth()
        super().__init__(env=env)
    
    @requires_auth
    def create_jgi_sequencing_project(
        self,
        jgi_sequencing_project: dict,
        client_id: str = None,
        client_secret: str = None,
    ) -> dict:
        """
        Create a new JGI sequencing project in the NMDC database.

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
        if client_id and client_secret:
            self.auth = NMDCAuth(
                client_id=client_id, client_secret=client_secret, env=self.env
            )
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
    
    def list_jgi_sequencing_projects(self, params: dict = None) -> dict:
        """
        List JGI sequencing projects from the NMDC database.

        Parameters
        ----------
        params : dict, optional
            Query parameters to filter the JGI sequencing projects.

        Returns
        -------
        dict
            The list of JGI sequencing projects.
        """
        url = f"{self.base_url}/wf_file_staging/jgi_sequencing_projects"
        headers = {
            "accept": "application/json",
        }
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise RuntimeError("Failed to retrieve JGI sequencing projects") from e
        else:
            logging.debug(
                f"API request response: {response.json()}\n API Status Code: {response.status_code}"
            )

        return response.json()['resources']
    
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

        return response.json()['resources'][0]
    

class JGISampleSearchAPI(NMDCSearch):
    """
    Class to interact with the NMDC API to get JGI samples.
    """

    def __init__(self, env="prod"):
        self.env = env
        super().__init__(collection_name="jgi_samples", env=env) 

    def get_jgi_samples(self, sequencing_project_name: str) -> dict:
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
        url = f"{self.base_url}/wf_file_staging/jgi_samples/{sequencing_project_name}"
        headers = {
            "accept": "application/json",
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise RuntimeError("Failed to retrieve JGI samples") from e
        else:
            logging.debug(
                f"API request response: {response.json()}\n API Status Code: {response.status_code}"
            )

        return response.json()['resources']
    
    @requires_auth
    def insert_jgi_samples(self, 
                           jgi_samples: list,
                           client_id: str = None,
                           client_secret: str = None,) -> dict:
        """
        Insert JGI samples into the NMDC database.

        Parameters
        ----------
        jgi_samples : list
            The list of JGI sample data to be inserted.

        Returns
        -------
        dict
            The response from the insertion operation.

        Raises
        ------
        Exception
            If the insertion fails.
        """
        if client_id and client_secret:
            self.auth = NMDCAuth(
                client_id=client_id, client_secret=client_secret, env=self.env
            )
        url = f"{self.base_url}/wf_file_staging/jgi_samples"
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.auth.get_token()}",
        }
        try:
            response = requests.post(url, headers=headers, json=jgi_samples)
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
    def update_jgi_sample(self,
                          jgi_file_id: str,
                          jgi_sample: dict,
                          client_id: str = None,
                          client_secret: str = None,) -> dict:
        """
        Update JGI samples in the NMDC database.

        Parameters
        ----------
        jgi_file_id : str
            The JGI file ID of the sample to be updated.
        jgi_sample : dict
            The updated JGI sample data.
        client_id : str, optional
            The client ID for authentication.
        client_secret : str, optional
            The client secret for authentication.

        Returns
        -------
        dict
            The response from the update operation.

        Raises
        ------
        Exception
            If the update fails.
        """
        if client_id and client_secret:
            self.auth = NMDCAuth(
                client_id=client_id, client_secret=client_secret, env=self.env
            )
        url = f"{self.base_url}/wf_file_staging/jgi_samples/{jgi_file_id}"
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.auth.get_token()}",
        }
        try:
            response = requests.put(url, headers=headers, json=jgi_sample)
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

    def __init__(self, env="prod"):
        self.env = env
        super().__init__(collection_name="globus_tasks", env=env) 
    
    def get_globus_tasks(self, task_id: str = None) -> dict:
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
        }
        params = {}
        if task_id:
            params['task_id'] = task_id
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise RuntimeError("Failed to retrieve Globus tasks") from e
        else:
            logging.debug(
                f"API request response: {response.json()}\n API Status Code: {response.status_code}"
            )

        return response.json()['resources']
    
    @requires_auth
    def create_globus_task(self, 
                           globus_task: dict,
                           client_id: str = None,
                           client_secret: str = None,) -> dict:
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
        if client_id and client_secret:
            self.auth = NMDCAuth(
                client_id=client_id, client_secret=client_secret, env=self.env
            )
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
    def update_globus_task(self, 
                           globus_task: dict,
                           client_id: str = None,
                           client_secret: str = None,) -> dict:
        """
        Update a Globus task in the NMDC database.

        Parameters
        ----------
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
        if client_id and client_secret:
            self.auth = NMDCAuth(
                client_id=client_id, client_secret=client_secret, env=self.env
            )
        url = f"{self.base_url}/wf_file_staging/globus_tasks"
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.auth.get_token()}",
        }
        try:
            response = requests.put(url, headers=headers, json=globus_task)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise RuntimeError("Failed to update Globus task") from e
        else:
            logging.debug(
                f"API request response: {response.json()}\n API Status Code: {response.status_code}"
            )

        return response.json()

