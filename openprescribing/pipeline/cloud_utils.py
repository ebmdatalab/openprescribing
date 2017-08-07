# This was copied from openprescribing-data/utils/cloud.py

# Copyright 2012 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# gs://ebmdatalab/hscic/prescribing/T201601PDPI%2BBNFT.CSV
# https://www.googleapis.com/storage/v1/b/ebmdatalab/o/hscic%2Faddresses%2FT201602ADDR%20BNFT.CSV
import httplib2
import json
import random
import sys
import time
import re

from apiclient.errors import HttpError
from oauth2client.client import GoogleCredentials
from googleapiclient import discovery
from apiclient.http import MediaFileUpload
from apiclient.http import MediaIoBaseDownload

# Retry transport and file IO errors.
RETRYABLE_ERRORS = (httplib2.HttpLib2Error, IOError)

# Number of times to retry failed downloads.
NUM_RETRIES = 5

# Number of bytes to send/receive in each request.
CHUNKSIZE = 2 * 1024 * 1024

# Mimetype to use if one can't be guessed from the file extension.
DEFAULT_MIMETYPE = 'application/octet-stream'


class CloudHandler(object):
    def __init__(self):
        super(CloudHandler, self).__init__()
        credentials = GoogleCredentials.get_application_default()
        self.bigquery = discovery.build('bigquery', 'v2',
                                        credentials=credentials)
        self.cloud = discovery.build('storage', 'v1', credentials=credentials)

    def handle_progressless_iter(self, error, progressless_iters):
        if progressless_iters > NUM_RETRIES:
            print 'Failed to make progress for too many consecutive iterations'
            raise error

        sleeptime = random.random() * (2**progressless_iters)
        print(
            'Caught exception (%s). Sleeping for %s seconds before retry #%d' %
             (str(error), sleeptime, progressless_iters)
        )
        time.sleep(sleeptime)

    def print_with_carriage_return(self, s):
        sys.stdout.write('\r' + s)
        sys.stdout.flush()

    def _load_payload(
            self, uri, table_id=None, mode=None, schema='prescribing.json'):
        if mode == 'replace':
            mode = 'WRITE_TRUNCATE'
        elif mode == 'append':
            mode = 'WRITE_APPEND'
        else:
            raise StandardError("invalid mode")
        with open("pipeline/schemas/%s" % schema, 'rb') as f:
            schema = json.load(f)
            payload = {
                "configuration": {
                    "load": {
                        "schema": {
                            "fields": schema,
                        },
                        "sourceUris": [uri],
                        "fieldDelimiter": ",",
                        "skipLeadingRows": 1,
                        "sourceFormat": "CSV",
                        "destinationTable": {
                            "projectId": 'ebmdatalab',
                            "tableId": table_id,
                            "datasetId": 'hscic'
                        },
                        "writeDisposition": mode,
                    }
                }
            }
            return payload

    def _query_payload(self, query, table_id=None, mode=None):
        if mode == 'replace':
            mode = 'WRITE_TRUNCATE'
        elif mode == 'append':
            mode = 'WRITE_APPEND'
        else:
            raise StandardError("invalid mode")
        with open('schemas/prescribing.json', 'rb') as f:
            schema = json.load(f)
            payload = {
                "configuration": {
                    "query": {
                        "query": query,
                        "flattenResuts": False,
                        "allowLargeResults": True,
                        "schema": {
                            "fields": schema,
                        },
                        "destinationTable": {
                            "projectId": 'ebmdatalab',
                            "tableId": table_id,
                            "datasetId": 'hscic'
                        },
                        "writeDisposition": mode,
                    }
                }
            }
            return payload

    def _run_and_wait(self, payload):
        response = self.bigquery.jobs().insert(
            projectId='ebmdatalab',
            body=payload,
        ).execute()
        print "Waiting for job to complete..."
        counter = 0
        job_id = response['jobReference']['jobId']
        while True:
            time.sleep(1)
            if counter % 5 == 0:
                sys.stdout.write(".")
                sys.stdout.flush()
            response = self.bigquery.jobs().get(
                projectId='ebmdatalab',
                jobId=job_id).execute()
            counter += 1
            if response['status']['state'] == 'DONE':
                if 'errors' in response['status']:
                    raise StandardError(
                        json.dumps(response, indent=2))
                else:
                    print "DONE!"
                    return

    def query_and_save(self, query, dest_table='', mode=''):
        assert dest_table and mode
        payload = self._query_payload(query,
                                      table_id=dest_table,
                                      mode=mode)
        self._run_and_wait(payload)

    def load(self,
             uri,
             table_name='prescribing_temp',
             schema='prescribing.json'):
        assert table_name
        payload = self._load_payload(
            uri, table_id=table_name, mode='replace', schema=schema)
        self._run_and_wait(payload)

    def dataset_exists(self, bucket, name):
        return len(self.list_raw_datasets(bucket, prefix=name)) > 0

    def list_raw_datasets(self, bucket, prefix='', name_regex=''):
        """List datasets in the specified bucket in order of created-at date

        Optionally filtered by prefex and name regex.
        """
        dataset_ids = []
        response = self.cloud.objects().list(
            bucket=bucket,
            prefix=prefix).execute()
        page_token = response.get('nextPageToken', None)
        if 'items' in response:
            dataset_ids += response["items"]
            while page_token:
                response = self.cloud.objects().list(
                    bucket='ebmdatalab',
                    pageToken=page_token,
                    prefix='hscic/prescribing').execute()
                if 'items' not in response:
                    break
                dataset_ids += response["items"]
                page_token = response.get('nextPageToken', None)
            if name_regex:
                dataset_ids = filter(
                    lambda x: re.findall(name_regex, x['name']), dataset_ids)
            dataset_ids = sorted(
                dataset_ids, key=lambda x: x['timeCreated'])
            dataset_ids = map(
                lambda x: x['name'], dataset_ids)
            return dataset_ids
        else:
            return []

    def list_tables(self):
        page_token = None
        table_ids = []
        response = self.bigquery.tables().list(
            projectId='ebmdatalab',
            datasetId='hscic',
            maxResults=1
        ).execute()
        page_token = response.get('nextPageToken', None)
        table_ids.append(
            map(lambda x: x['tableReference']['tableId'], response['tables'])
        )
        while page_token:
            response = self.bigquery.tables().list(
                projectId='ebmdatalab',
                datasetId='hscic',
                pageToken=page_token,
                maxResults=1
            ).execute()
            if 'tables' not in response:
                break
            table_ids += (
                map(lambda x: x['tableReference']['tableId'],
                    response['tables'])
            )
            page_token = response.get('nextPageToken', None)
        return table_ids

    def rows_to_dict(self, bigquery_result):
        fields = bigquery_result['schema']['fields']
        for row in bigquery_result['rows']:
            dict_row = {}
            for i, item in enumerate(row['f']):
                value = item['v']
                key = fields[i]['name']
                dict_row[key] = value
            yield dict_row

    def download(self, filename, bucket_name, object_name):
        with open(filename, 'wb') as f:
            req = self.cloud.objects().get_media(
                bucket=bucket_name, object=object_name)
            downloader = MediaIoBaseDownload(f, req)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                print("Download {}%.".format(int(status.progress() * 100)))

    def upload(self, filename, bucket_name, object_name):
        assert bucket_name and object_name
        print 'Building upload request...'
        media = MediaFileUpload(filename, chunksize=CHUNKSIZE, resumable=True)
        if not media.mimetype():
            media = MediaFileUpload(filename, DEFAULT_MIMETYPE, resumable=True)
        request = self.cloud.objects().insert(bucket=bucket_name,
                                              name=object_name,
                                              media_body=media)
        print 'Uploading file: %s to bucket: %s object: %s ' % (filename,
                                                                bucket_name,
                                                                object_name)
        progressless_iters = 0
        response = None
        while response is None:
            error = None
            try:
                progress, response = request.next_chunk()
                if progress:
                    self.print_with_carriage_return(
                        'Upload %d%%' % (100 * progress.progress()))
            except HttpError, err:
                error = err
                if err.resp.status < 500:
                    raise
            except RETRYABLE_ERRORS, err:
                error = err

            if error:
                progressless_iters += 1
                self.handle_progressless_iter(error, progressless_iters)
            else:
                progressless_iters = 0

        print '\nUpload complete!'
