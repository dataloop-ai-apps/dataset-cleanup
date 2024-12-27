import dtlpy as dl
import numpy as np
import threading
import datetime
import logging
import json
import time
import io
import pytz
import tempfile
from dtlpy_exporter import ExportBase, ExportStatus

logger = logging.getLogger('[EXPORTER]')
logging.basicConfig(level='INFO')


class Exporter(ExportBase):
    """
    A class used to export dataset features and manage execution of various tasks.

    Attributes
    ----------
    execution_running : dict
        A dictionary to track the status and progress of different execution types.
    feature_sets_export : dict
        A dictionary to store exported feature sets.

    Methods
    -------
    process_data(**kwargs)
        Processes the dataset and extracts feature sets.
    get_feature_sets_names()
        Returns a dictionary with feature set names and their counts.
    install_start_exec(dpk_name, service_name, funtion_name, exec_type)
        Installs and starts the execution of a specified function.
    start_execution(exec_type)
        Starts the execution of a specified type.
    wait_for_execution(execution_id, exec_type)
        Waits for the execution to complete and updates the status and progress.
    quality_score(qtype, min_v, max_v, limit=0, pagination=100, return_ids=False)
        Filters items in the dataset based on quality scores and returns the count or item details.
    """

    def __init__(self, dataset_id):
        super().__init__(dataset_id)
        if not hasattr(self, 'feature_sets_export'):
            self.execution_running = {
                'clip': {
                    "status": 'ready',
                    "progress": 0,
                    "execution_id": '',
                    'full_status': 'created',
                },
                'quality-score-generator': {
                    "status": 'ready',
                    "progress": 0,
                    "execution_id": '',
                    'full_status': 'created',
                },
            }
            # status

            self.feature_sets_export = {}

    def process_data(self, **kwargs):
        """
        Processes the data by extracting feature sets and organizing them into a dictionary.

        This method iterates over the `download_data` attribute, extracts relevant information,
        and organizes it into a dictionary where the keys are feature set names and the values
        are lists of dictionaries containing item details.

        Args:
            **kwargs: Arbitrary keyword arguments.

        Raises:
            Exception: If an error occurs during the processing of feature sets, it logs the error
                       and sets the status to 'error'.

        Attributes:
            feature_sets_export (dict): A dictionary where keys are feature set names and values
                                        are lists of dictionaries containing item details.
            progress (int): An integer representing the progress of the data processing.
            status (str): A string representing the status of the data processing.
        """
        try:
            feature_sets = {
                fs.id: fs.name for fs in self.dataset.project.feature_sets.list().all()
            }

            feature_sets_export = {}

            total_files = len(self.download_data)
            for i, data in enumerate(self.download_data):
                name = data.get('name', '')
                thumbnail = data.get('thumbnail', '')
                annotated = data.get('annotated', False)
                for feature_vec in data.get('itemVectors', []):
                    fs_id = feature_vec.get('featureSetId')
                    value = feature_vec.get('value')
                    item_id = data.get('id')

                    key = feature_sets.get(fs_id, fs_id)

                    if key not in feature_sets_export:
                        feature_sets_export[key] = [
                            {
                                'itemId': item_id,
                                'value': value,
                                'name': name,
                                'thumbnail': thumbnail,
                                'annotated': annotated,
                            }
                        ]
                    else:
                        feature_sets_export[key].append(
                            {
                                'itemId': item_id,
                                'value': value,
                                'name': name,
                                'thumbnail': thumbnail,
                                'annotated': annotated,
                            }
                        )
                    self.progress = round(round((i + 1) / total_files * 45, 0) + 50)

            self.feature_sets_export = feature_sets_export
        except Exception as e:
            logger.error("Error while loading feature sets: %s", e)
            self.status = ExportStatus.ERROR
            raise

    def get_feature_sets_names(self):
        """
        Retrieves the names and sizes of feature sets.

        This method iterates over the `feature_sets_export` dictionary,
        counts the number of features in each set, and returns a new
        dictionary with the feature set names as keys and their respective
        sizes as values.

        Returns:
            dict: A dictionary where the keys are feature set names (str)
                  and the values are the number of features in each set (int).
        """
        feature_dict = {}
        for key, value in self.feature_sets_export.items():
            feature_dict[key] = len(value)
        return feature_dict

    def install_start_exec(self, dpk_name, service_name, funtion_name, exec_type):
        """
        Installs and starts the execution of a specified function within a service.

        Args:
            dpk_name (str): The name of the DPK (Data Package) to be installed.
            service_name (str): The name of the service where the function will be executed.
            funtion_name (str): The name of the function to be executed.
            exec_type (str): The type of execution to be performed.

        Returns:
            None
        """
        project = self.dataset.project
        filters = dl.Filters(resource='apps')
        filters.add(field='dpkName', values=dpk_name)
        if project.apps.list(filters=filters).items_count == 0:
            dpk = project.dpks.get(dpk_name=dpk_name)
            project.apps.install(dpk=dpk)
        service = project.services.get(service_name=service_name)
        execution = project.executions.create(
            function_name=funtion_name,
            service_id=service.id,
            execution_input={'dataset': {'dataset_id': self.dataset.id}, 'query': None},
        )
        thread = threading.Thread(
            target=self.wait_for_execution,
            kwargs={"execution_id": execution.id, "exec_type": exec_type},
        )
        thread.daemon = True
        thread.start()

    def start_execution(self, exec_type):
        """
        Starts the execution process for the given execution type.

        This method updates the execution status and progress for the specified
        execution type and initiates the corresponding execution process.

        Args:
            exec_type (str): The type of execution to start. Supported values are
                             'clip' and 'quality-score-generator'.

        Raises:
            KeyError: If the provided exec_type is not found in the execution_running dictionary.
        """
        self.execution_running[exec_type]['status'] = 'running'
        self.execution_running[exec_type]['progress'] = 0
        self.execution_running[exec_type]['full_status'] = 'created'

        if exec_type == 'clip':
            self.install_start_exec(
                'clip-image-search', 'clip-extraction', 'extract_dataset', 'clip'
            )
        elif exec_type == 'quality-score-generator':
            self.install_start_exec(
                'quality-score-generator-app',
                'quality-scores-generator',
                'dataset_scores_generator',
                'quality-score-generator',
            )

    def wait_for_execution(self, execution_id, exec_type):
        """
        Waits for the execution of a given execution ID to complete.

        This method polls the execution status at regular intervals until the execution
        completes, times out, or encounters an error. It updates the execution status
        and progress in the `execution_running` dictionary.

        Args:
            execution_id (str): The ID of the execution to wait for.
            exec_type (str): The type of execution being waited on.

        Raises:
            TimeoutError: If the execution does not complete within the specified timeout.
            dl.exceptions.PlatformException: If the execution does not complete successfully.
            Exception: If any other error occurs during the wait.

        Updates:
            self.execution_running[exec_type]['progress']: The progress percentage of the execution.
            self.execution_running[exec_type]['full_status']: The full status of the execution.
            self.execution_running[exec_type]['status']: The final status of the execution.
            self.status: The status of the export process.
            self.progress: The progress of the export process.
        """

        try:
            project = dl.projects.get(project_id=self.dataset.project.id)
            timeout = 60 * 60 * 2
            max_sleep_time = 10
            backoff_factor = 1
            elapsed = 0
            start = time.time()
            if timeout is None or timeout <= 0:
                timeout = np.inf

            num_tries = 1
            while elapsed < timeout:
                latest_status = project.executions.get(
                    execution_id=execution_id
                ).latest_status
                self.execution_running[exec_type]['progress'] = latest_status.get(
                    'percentComplete', 0
                )
                self.execution_running[exec_type]['full_status'] = latest_status[
                    'status'
                ]
                if latest_status['status'] not in ['in-progress', 'created']:
                    self.execution_running[exec_type]['status'] = latest_status[
                        'status'
                    ]
                    break
                elapsed = time.time() - start
                sleep_time = np.min(
                    [timeout - elapsed, backoff_factor * (2**num_tries), max_sleep_time]
                )
                num_tries += 1
                logger.debug(
                    "Execution %s is running for %s[s] and now Going to sleep %s[s]",
                    execution_id,
                    elapsed,
                    sleep_time,
                )
                time.sleep(sleep_time)

            if elapsed >= timeout:
                raise TimeoutError(
                    f"execution wait() got timeout. id: {execution_id}, status: {self.execution_running[exec_type]['status']}, progress {self.execution_running[exec_type]['progress']}%"
                )
            if self.execution_running[exec_type]['status'] != 'success':
                raise dl.exceptions.PlatformException(
                    error='424', message=f"Execution {execution_id}"
                )
            self.execution_running[exec_type]['status'] = 'ready'

            self.progress = 0
            self.run_whole_process()

        except Exception as e:
            logger.error("Error while waiting for command: %s", e)
            self.execution_running[exec_type]['status'] = 'error'
            self.status = ExportStatus.ERROR
            raise

    def quality_score(
        self, qtype, min_v, max_v, limit=0, pagination=100, return_ids=False
    ):
        """
        Calculate the quality score of items in the dataset based on specified criteria.

        Parameters:
        - qtype (str): The type of quality score to filter by. Supported values are 'Darkness/Brightness' and 'Blurriness/Sharpness'.
        - min_v (float): The minimum value for the quality score filter.
        - max_v (float): The maximum value for the quality score filter.
        - limit (int, optional): The maximum number of items to return. Default is 0 (no limit).
        - pagination (int, optional): The number of items to return per page. Default is 100.
        - return_ids (bool, optional): Whether to return item IDs and metadata. Default is False.

        Returns:
        - tuple: If return_ids is True, returns a tuple containing the count of items and a list of dictionaries with item metadata.
             If return_ids is False, returns the count of items.

        Raises:
        - dl.exceptions.BadRequest: If there is an error while filtering items.

        Notes:
        - If the specified quality type is not supported, an error is logged and the function returns 0 or an empty list based on return_ids.
        """

        dataset = self.dataset
        items_count = 0
        if qtype == 'Darkness/Brightness':
            metadata_field = 'metadata.user.quality_scores.darkness_score'
        elif qtype == 'Blurriness/Sharpness':
            metadata_field = 'metadata.user.quality_scores.blurriness_score'
        else:
            logger.error("Quality type %s not supported", qtype)
            if return_ids:
                return 0, []
            else:
                return 0

        filters = dl.Filters()
        filters.add(
            field=metadata_field,
            values=min_v,
            operator=dl.FiltersOperations.GREATER_THAN,
        )
        filters.add(
            field=metadata_field, values=max_v, operator=dl.FiltersOperations.LESS_THAN
        )
        try:
            if return_ids:
                items = dataset.items.list(filters=filters).all()
                ids = [
                    {
                        'itemId': item.id,
                        'name': item.name,
                        'thumbnail': item.thumbnail,
                        'annotated': item.annotated,
                    }
                    for item in items
                ]
                return len(ids), ids
            else:
                items = dataset.items.list(filters=filters)
                items_count = items.items_count
                return items_count
        except dl.exceptions.BadRequest as e:
            logger.error("Error while filtering items: %s", e)
            if return_ids:
                return 0, []
            else:
                return 0
