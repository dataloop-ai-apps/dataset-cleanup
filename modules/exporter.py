import dtlpy as dl
import numpy as np
import threading
import datetime
import logging
import json
import time
import io
import zipfile
import pytz
import tempfile

logger = logging.getLogger('[EXPORTER]')
logging.basicConfig(level='INFO')


class Exporter:
    def __init__(self, dataset_id):
        self.dataset_id = dataset_id
        self.dataset = dl.datasets.get(dataset_id=self.dataset_id)
        self.path = f'tmp/{self.dataset.id}/json'
        self.lock = threading.Lock()
        self.timezone = 'UTC'
        self.execution_running = {'clip': {"status": 'ready', "progress": 0, "execution_id": '', 'full_status': 'created'},
                                  'quality-score-generator': {"status": 'ready', "progress": 0, "execution_id": '', 'full_status': 'created'}}
        # status
        self.export_date = ""
        self.progress = 0
        self.status = "loading"
        self.export_item_id = ""
        self.feature_sets_export = {}

        thread = threading.Thread(target=self.load)
        thread.daemon = True
        thread.start()

    def refresh(self):
        item: dl.Item = self.find_last_export()
        if item is not None:
            self.progress = 50
            self.export_date = self.change_iso_date_string(item.created_at)
            item_dir = item.download(save_locally=False)
            self.export_item_id = json.loads(item_dir.getvalue())['OutputItemId']
            logger.info(f"Found last export with item id: {self.export_item_id}")
            self.load_feature_sets()
            self.status = "ready"

    def load(self):
        command_id = self.check_active_exports()
        if command_id is not None:
            print(f"Found active export with command id: {command_id}")
            self.wait_for_command(command_id=command_id)

        else:
            self.refresh()

        if command_id is None and self.export_item_id == "":
            logger.warning("No active exports found")
            self.start_export()

    def change_iso_date_string(self, iso_datetime):
        # Parse the ISO 8601 string to a datetime object
        dt = datetime.datetime.fromisoformat(iso_datetime.replace('Z', '+00:00'))
        timezone = pytz.timezone(self.timezone)
        dt = dt.astimezone(timezone)
        # Format the datetime object to a more readable string
        readable_string = dt.strftime('%B %d, %Y %H:%M:%S')
        return readable_string

    def wait_for_command(self, command_id):
        try:
            logger.info(f"Waiting for command: {command_id}")
            timeout = 60 * 60 * 2
            max_sleep_time = 30
            backoff_factor = 1
            elapsed = 0
            start = time.time()
            if timeout is None or timeout <= 0:
                timeout = np.inf

            command = None
            num_tries = 1
            self.status = 'running'
            while elapsed < timeout:
                command = dl.commands.get(command_id=command_id)
                if not command.in_progress():
                    break
                elapsed = time.time() - start
                sleep_time = np.min([timeout - elapsed, backoff_factor * (2 ** num_tries), max_sleep_time])
                self.progress = round(command.progress / 2, 0)
                num_tries += 1
                logger.debug("Command {!r} is running for {:.2f}[s] and now Going to sleep {:.2f}[s]".format(command.id,
                                                                                                             elapsed,
                                                                                                             sleep_time))
                time.sleep(sleep_time)
            if command is None:
                raise ValueError('Nothing to wait for')
            if elapsed >= timeout:
                raise TimeoutError("command wait() got timeout. id: {!r}, status: {}, progress {}%".format(
                    command.id, command.status, command.progress))
            if command.status != dl.CommandsStatus.SUCCESS:
                raise dl.exceptions.PlatformException(error='424',
                                                      message="Command {!r} {}: '{}'".format(command.id,
                                                                                             command.status,
                                                                                             command.error))

            if 'outputItemId' not in command.spec:
                raise dl.exceptions.PlatformException(
                    error='400',
                    message="outputItemId key is missing in command id: {}".format(command_id))
            self.remove_active_exports()
            item_id = command.spec['outputItemId']
            self.save_finished_export(item_id)
            annotation_zip_item = self.dataset.items.get(item_id=item_id)
            self.export_item_id = item_id
            self.progress = 50
            self.load_feature_sets()
            self.progress = 100
            self.status = 'ready'
            self.export_date = self.change_iso_date_string(annotation_zip_item.created_at)
            return annotation_zip_item
        except Exception as e:
            logger.error(f"Error while waiting for command: {e}")
            self.status = 'error'
            self.remove_active_exports()

    def start_export(self):
        self.status = "running"
        self.progress = 0
        self.export_date = ""
        self.export_item_id = ""
        payload = {
            # 'itemsQuery': {"filter": params.get("query", {}), "join": params.get("join", {})},
            'includeItemVectors': True,
            "itemsVectorQuery": {'select': {"datasetId": 1, 'featureSetId': 1, 'value': 1}},
            'exportType': 'json'
        }
        success, response = dl.client_api.gen_request(req_type='post',
                                                      path='/datasets/{}/export'.format(self.dataset.id),
                                                      json_req=payload,
                                                      )
        if not success:
            raise dl.exceptions.PlatformException(response)

        # save command in json
        json_string = response.content.decode('utf-8')
        id_load = json.loads(json_string)['id']

        self.update_active_exports(command_id=id_load)

        thread = threading.Thread(target=self.wait_for_command, kwargs={"command_id": id_load})
        thread.daemon = True
        thread.start()
        return id_load

    def update_active_exports(self, command_id):
        b_dataset = self.dataset.project.datasets._get_binaries_dataset()
        buffer = io.BytesIO()
        buffer.write(json.dumps({"commandId": command_id}).encode('utf-8'))
        buffer.name = "active_export.json"
        logger.info(f"Uploading active_export.json to /.dataloop/exports/fv_json/{self.dataset.id}")
        b_dataset.items.upload(local_path=buffer,
                               remote_path=f'/.dataloop/exports/fv_json/{self.dataset.id}',
                               overwrite=True)

    def save_finished_export(self, item_id):
        b_dataset = self.dataset.project.datasets._get_binaries_dataset()
        buffer = io.BytesIO()
        buffer.write(json.dumps({"OutputItemId": item_id}).encode('utf-8'))
        buffer.name = f"{item_id}.json"
        logger.info(f"Uploading outputItemId to /.dataloop/exports/fv_done_json/{self.dataset.id}")
        b_dataset.items.upload(local_path=buffer,
                               remote_path=f'/.dataloop/exports/fv_done_json/{self.dataset.id}',
                               overwrite=True)

    def remove_active_exports(self):
        filters = dl.Filters(use_defaults=False)
        filters.add(field='filename', values=f'/.dataloop/exports/fv_json/{self.dataset.id}/active_export.json')
        filters.page_size = 10
        b_dataset = self.dataset.project.datasets._get_binaries_dataset()
        items = b_dataset.items.list(filters=filters)
        if items.items_count != 0:
            items.items[0].delete()
        return True

    def check_active_exports(self):
        filters = dl.Filters(use_defaults=False)
        filters.add(field='dir', values=f'/.dataloop/exports/fv_json/{self.dataset.id}/active_export.json')
        filters.page_size = 10
        b_dataset = self.dataset.project.datasets._get_binaries_dataset()
        items = b_dataset.items.list(filters=filters)
        if items.items_count != 0:
            with open(items.items[0].download(overwrite=True)) as f:
                export_data = json.load(f)
            return export_data['commandId']
        else:
            return None

    def find_last_export(self):
        filters = dl.Filters(use_defaults=False)
        filters.add(field='dir', values=f'/.dataloop/exports/fv_done_json/{self.dataset.id}')
        filters.sort_by(field='createdAt', value=dl.FiltersOrderByDirection.DESCENDING)
        filters.page_size = 10
        b_dataset = self.dataset.project.datasets._get_binaries_dataset()
        items = b_dataset.items.list(filters=filters)
        if items.items_count != 0:
            stored_output_item = items.items[0]
            item_dir = stored_output_item.download(save_locally=False)
            new_output_item_id = json.loads(item_dir.getvalue())['OutputItemId']
            item = b_dataset.items.get(item_id=new_output_item_id)
            if item.filename.endswith('.json'):
                print(f"Found last export with item id: {new_output_item_id}")
                return stored_output_item

        return None

    def load_feature_sets(self):
        try:
            item = dl.items.get(item_id=self.export_item_id)
            item_dir = item.download(local_path=f'./{self.export_item_id}.zip', save_locally=False)

            with tempfile.TemporaryDirectory() as temp_dir:
                item_dir = item.download(local_path=temp_dir, save_locally=True)
                with open(item_dir, 'r') as f:
                    download_data = json.load(f)

            feature_sets = {fs.id: fs.name for fs in self.dataset.project.feature_sets.list().all()}

            feature_sets_export = {}

            total_files = len(download_data)
            for i, data in enumerate(download_data):
                name = data.get('name', '')
                thumbnail = data.get('thumbnail', '')
                annotated = data.get('annotated', False)
                for feature_vec in data.get('itemVectors', []):
                    fs_id = feature_vec.get('featureSetId')
                    value = feature_vec.get('value')
                    item_id = data.get('id')

                    key = feature_sets.get(fs_id, fs_id)

                    if key not in feature_sets_export:
                        feature_sets_export[key] = [{'itemId': item_id, 'value': value,
                                                    'name': name, 'thumbnail': thumbnail, 'annotated': annotated}]
                    else:
                        feature_sets_export[key].append({'itemId': item_id, 'value': value, 'name': name,
                                                        'thumbnail': thumbnail, 'annotated': annotated})
                    self.progress = round(round((i + 1) / total_files * 45, 0) + 50)

            self.feature_sets_export = feature_sets_export
        except Exception as e:
            logger.error(f"Error while loading feature sets: {e}")
            self.status = 'error'
            raise

    def get_feature_sets_names(self):
        feature_dict = {}
        for key, value in self.feature_sets_export.items():
            feature_dict[key] = len(value)
        return feature_dict

    def install_start_exec(self, dpk_name, service_name, funtion_name, exec_type):
        project = self.dataset.project
        filters = dl.Filters(resource='apps')
        filters.add(field='dpkName', values=dpk_name)
        if project.apps.list(filters=filters).items_count == 0:
            dpk = project.dpks.get(dpk_name=dpk_name)
            project.apps.install(dpk=dpk)
        service = project.services.get(service_name=service_name)
        execution = project.executions.create(function_name=funtion_name, service_id=service.id, execution_input={
                                              'dataset': {'dataset_id': self.dataset.id}, 'query': None})
        thread = threading.Thread(target=self.wait_for_execution, kwargs={
                                  "execution_id": execution.id, "exec_type": exec_type})
        thread.daemon = True
        thread.start()

    def start_execution(self, exec_type):
        self.execution_running[exec_type]['status'] = 'running'
        self.execution_running[exec_type]['progress'] = 0
        self.execution_running[exec_type]['full_status'] = 'created'

        if exec_type == 'clip':
            self.install_start_exec('clip-image-search', 'clip-extraction', 'extract_dataset', 'clip')
        elif exec_type == 'quality-score-generator':
            self.install_start_exec('quality-score-generator-app', 'quality-scores-generator', 'dataset_scores_generator', 'quality-score-generator')

    def wait_for_execution(self, execution_id, exec_type):

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
                latest_status = project.executions.get(execution_id=execution_id).latest_status
                self.execution_running[exec_type]['progress'] = latest_status.get('percentComplete', 0)
                self.execution_running[exec_type]['full_status'] = latest_status['status']
                if latest_status['status'] not in ['in-progress', 'created']:
                    self.execution_running[exec_type]['status'] = latest_status['status']
                    break
                elapsed = time.time() - start
                sleep_time = np.min([timeout - elapsed, backoff_factor * (2 ** num_tries), max_sleep_time])
                num_tries += 1
                logger.debug("Execution {!r} is running for {:.2f}[s] and now Going to sleep {:.2f}[s]".format(execution_id,
                                                                                                               elapsed,
                                                                                                               sleep_time))
                time.sleep(sleep_time)

            if elapsed >= timeout:
                raise TimeoutError("execution wait() got timeout. id: {!r}, status: {}, progress {}%".format(
                    execution_id, self.execution_running[exec_type]['status'], self.execution_running[exec_type]['progress']))
            if self.execution_running[exec_type]['status'] != 'success':
                raise dl.exceptions.PlatformException(error='424',
                                                      message="Execution {!r}".format(execution_id))
            self.execution_running[exec_type]['status'] = 'ready'

            self.status = "starting"
            self.progress = 0
            self.start_export()

        except Exception as e:
            logger.error(f"Error while waiting for command: {e}")
            self.execution_running[exec_type]['status'] = 'error'
            self.status = 'error'
            raise

    def quality_score(self, qtype, min_v, max_v, limit=0, pagination=100, return_ids=False):
        dataset = self.dataset
        items_count = 0
        if qtype == 'Darkness/Brightness':
            metadata_field = 'metadata.user.quality_scores.darkness_score'
        elif qtype == 'Blurriness/Sharpness':
            metadata_field = 'metadata.user.quality_scores.blurriness_score'
        else:
            logger.error(f"Quality type {qtype} not supported")
            if return_ids:
                return 0, []
            else:
                return 0

        filters = dl.Filters()
        filters.add(field=metadata_field, values=min_v, operator=dl.FiltersOperations.GREATER_THAN)
        filters.add(field=metadata_field, values=max_v, operator=dl.FiltersOperations.LESS_THAN)
        try:
            if return_ids:
                items = dataset.items.list(filters=filters).all()
                ids = [{'itemId': item.id, 'name': item.name, 'thumbnail': item.thumbnail, 'annotated': item.annotated}
                       for item in items]
                return len(ids), ids
            else:
                items = dataset.items.list(filters=filters)
                items_count = items.items_count
                return items_count
        except dl.exceptions.BadRequest as e:
            logger.error(f"Error while filtering items: {e}")
            if return_ids:
                return 0, []
            else:
                return 0
