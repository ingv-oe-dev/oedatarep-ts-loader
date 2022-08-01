from flask import current_app
import traceback
import requests
import json
import csv
from io import StringIO


#
# Main Class
#
#
class TSResource():
    def __init__(self, url, token=None):
        self._api_url = url
        self._record_id = None
        self._api_record_url = None
        self._oedatarep_auth_token = token

        self._resp_data = dict()
        self._record_metadata = dict()

        self._links = dict()
        self._file_link = ""

        self._chart_resource = None
        self._ts_guid = None

        self.ts_files = []
        self.ts_files_to_upload = []

    def bootstrap_instance(self, recid):
        self._record_id = recid
        self._api_record_url = self._api_url + self._record_id + "/draft"
        return self

    def set_instance_metadata(self, data):
        try:
            if self._dictHasKey(self._resp_data, "metadata"):
                self._record_metadata = self._resp_data["metadata"]
        except Exception:
            current_app.logger.exception("No `metadata` field found in record: {}".format(self._resp_data))
            raise

    def set_instance_links(self, data):
        try:
            if self._dictHasKey(self._resp_data, "links"):
                current_app.logger.info("Set links: %s", self._resp_data["links"])
                self._links = self._resp_data["links"]
        except Exception:
            current_app.logger.exception("No `links` field found in record: {}".format(self._resp_data))
            raise

        try:
            if self._dictHasKey(self._links, "files"):
                current_app.logger.info("Set file link: %s", self._links["files"])
                self._file_link = self._links["files"]
        except Exception:
            current_app.logger.exception("No `files` field found in record: {}".format(self._resp_data))
            raise

#
# InvenioRDM/OEDatarep Rest API resources - interface
#
#

    def get_record_data(self):
        try:
            response = requests.get(self._api_record_url,
                headers={'Authorization': 'Bearer {}'.format(current_app.config.get("OEDATAREP_API_AUTH_TOKEN"))},
                verify=False)
            response.raise_for_status()

        except requests.exceptions.HTTPError:
            current_app.logger.exception("In connecting to OEDataRep REST APis")
            raise

        else:
            if response.status_code == 200:
                self._resp_data = response.json()
        finally:
            return self._resp_data if type(self._resp_data) is dict and bool(self._resp_data) else None

    def get_record_files(self):
        try:
            response = requests.get(self._file_link,
                headers={'Authorization': 'Bearer {}'.format(current_app.config.get("OEDATAREP_API_AUTH_TOKEN"))},
                verify=False)
            response.raise_for_status()

        except requests.exceptions.RequestException as err:
            raise SystemExit(err)

        else:
            try:
                if "entries" in response.json():
                    for entry in response.json()["entries"]:

                        current_app.logger.debug("Entry: %s", entry)

                        try:
                            if entry["status"] == "completed":
                                self.ts_files.append(dict(
                                        {
                                            "key": entry["key"],
                                            "content_link": entry["links"]["content"],
                                            "size": entry["size"],
                                            "mimetype": entry["mimetype"],
                                        })
                                )
                        except Exception as e:
                            current_app.logger.error(traceback.format_exc())
                            raise e
                else:
                    current_app.logger.info("No (files) entries found in record")
                    raise ValueError("Error gathering TS_Files (.json or .csv)")

            except Exception as err:
                raise(err)

        finally:
            if len(self.ts_files) > 0:
                current_app.logger.debug("GOT record_files: %s", self.ts_files)

            return True if len(self.ts_files) > 0 else False

    def get_ts_header_file(self, content_url, tsd_auth_token):
        tsd_token = None
        header_json = {}

        try:
            current_app.logger.info("GET TimeSeries Header from URL: %s", content_url)

            response = requests.get(content_url,
                headers={'Authorization': 'Bearer {}'.format(current_app.config.get("OEDATAREP_API_AUTH_TOKEN"))},
                verify=False)
            response.raise_for_status()

        except requests.exceptions.RequestException as err:
            raise SystemExit(err)

        else:
            header_json = response.json()

            current_app.logger.info("GOT Header File(%s): %s", type(header_json), header_json)

        finally:
            return header_json if type(header_json) is dict and bool(header_json) else None

    def put_ts_guid_on_record_metadata(self, ts_guid):
        self._resp_data["metadata"]["ts_resources"][0]["chart_props"]["guid"] = ts_guid
        self._resp_data["metadata"]["ts_resources"][0]["ts_published"] = True

        current_app.logger.info("Record data: %s", self._resp_data)

        try:
            resp = requests.put(self._api_url + self._record_id + "/draft",
                data=json.dumps(self._resp_data),
                headers={'Authorization': 'Bearer {}'.format(current_app.config.get("OEDATAREP_API_AUTH_TOKEN")),'Content-Type': 'application/json'},
                verify=False
            )
            resp.raise_for_status()

        except requests.exceptions.RequestException as err:
            raise SystemExit(err)

        else:
            current_app.logger.info("Update_record_metadata return code: %s", resp.status_code)

        finally:
            return True if resp.status_code == 200 else False

    def get_ts_data_file(self, content_url, ts_id, tsd_auth_token):
        tsd_token = None
        ts_json = {}

        try:
            current_app.logger.info("GET TimeSeries Data from URL: %s", content_url)

            csv_file_response = requests.get(content_url,
                headers={'Authorization': 'Bearer {}'.format(current_app.config.get("OEDATAREP_API_AUTH_TOKEN"))},
                verify=False)
            csv_file_response.raise_for_status()

        except requests.exceptions.RequestException as err:
            raise SystemExit(err)

        else:
            csv_file = csv_file_response.text

            # ts_json = make_json(self._resp_data["metadata"]["chart_resource"]["chart_props"]["guid"],
            # 	csv_file
            # )
            ts_json = make_json(ts_id, csv_file)

            current_app.logger.info("CSV-2-JSON: %s", type(ts_json))

        finally:
            return ts_json if type(ts_json) is str and bool(ts_json) else None
#
# Prepare record files (raw data .csv and metadata .json), to upload
#
#

    def filter_ts_files(self):
        try:
            data_entries = [d for d in self.ts_files if d['mimetype'] in 'text/csv']
            header_entries = [h for h in self.ts_files if h['mimetype'] in 'application/json']

            current_app.logger.info("TS_Data_Array: %s", data_entries)
            current_app.logger.info("TS_Header_Array: %s", header_entries)

        except ValueError as err:
            raise(err)

        for d_entry in data_entries:
            current_app.logger.info("TS_Entry: %s", d_entry)
            for h_entry in header_entries:
                current_app.logger.info("Header_Entry: %s", h_entry)
                try:
                    if h_entry['key'] in d_entry["key"].replace(".csv","")+'_header.json':
                        self.ts_files_to_upload.append([
                            d_entry,
                            [h_entry for h_entry in header_entries if h_entry['key'] in d_entry["key"].replace(".csv","")+'_header.json'].pop()]
                        )
                except ValueError as err:
                    raise(err)

        if len(data_entries) > 0 and len(header_entries) > 0:
            current_app.logger.info("Instance data(s) to Upload: %s", self.ts_files_to_upload)
            return True
        else:
            current_app.logger.debug("Instance data: %s \n Intance header: %s", data_entries, header_entries)
            return False

#
# TSD Rest API resources - interface
#
#
    def get_tsd_auth_token(self):
        tsd_token = ""

        try:
            # tsd_token_response = requests.post(current_app.config.get("TSD_API_URL")+"/tsdws/token",
            # 	{
            # 		"email": "mario.torrisi@ingv.it",
            # 		"password": "123456",
            # 		"scope":"timeseries-edit"
            # 	}#,
            # 	#headers = {"Content-Type": "application/x-www-form-urlencoded"}
            # )

            # tsd_token_response.raise_for_status()
            pass

        except requests.exceptions.RequestException as err:
            raise SystemExit(err)

        else:
            tsd_token = current_app.config.get("TSD_API_AUTH_TOKEN")
            current_app.logger.info("TSD_Auth_Token: %s", tsd_token)

        finally:
            return tsd_token if bool(tsd_token) else None


    def post_ts_header_on_tsd(self, header_data, tsd_auth_token):

        try:
            rsp = requests.post(current_app.config.get("TSD_API_URL")+"/tsdws/timeseries",
                json = header_data,
                headers = {'Authorization': tsd_auth_token},
            )
            rsp.raise_for_status()

        except requests.exceptions.RequestException as err:
            raise SystemExit(err)

        else:
            rsp_data = rsp.json()["data"]
            rsp_guid = rsp_data["id"]

            current_app.logger.info("GOT Response from TSD: %s", rsp_data)
            current_app.logger.info("GUID: %s", rsp_guid)

        finally:
            current_app.logger.info("GOT RESP FROM TSD: %s",rsp.json())
            return rsp_guid if type(rsp_data) is dict and bool(rsp_data) and self._dictHasKey(rsp_data, "id") else None

    def post_ts_data_on_tsd(self, ts_data, tsd_auth_token):

        try:
            rsp = requests.post(current_app.config.get("TSD_API_URL")+"/tsdws/timeseries/values",
                json = json.loads(ts_data),
                headers = {'Authorization': tsd_auth_token},
            )
            rsp.raise_for_status()

        except requests.exceptions.RequestException as err:
            raise SystemExit(err)

        else:
            current_app.logger.info("GOT Response from TSD: %s", rsp.status_code)
            rsp_data = rsp.json()["data"]

        finally:
            current_app.logger.info("GOT Response - POST_TS_DATA: %s", rsp.json())

#
# Class/Instance Helper methods
#
#

    def _dictHasKey(self, element, *keys):
        if not isinstance(element, dict):
            raise AttributeError('keys_exists() expects dict as first argument.')
        if len(keys) == 0:
            raise AttributeError('keys_exists() expects at least two arguments, one given.')

        _element = element
        for key in keys:
            try:
                _element = _element[key]
            except KeyError:
                return False
        return True

# Function to convert a CSV to JSON
# Takes the file paths as arguments
def make_json(ts_id, csvFile):

    # create a dictionary
    data = {
        'insert': 'ignore',
        'id': ts_id
    }
    csvReader = csv.reader(StringIO(csvFile), delimiter=',')
    data['columns'] = next(csvReader)
    if data['columns'] is not None:
        data['data'] = []
        for row in csvReader:
            data['data'].append(row)

    return json.dumps(data)
