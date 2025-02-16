import json

import requests

from lxml import etree

# Thin 'client' functions for http API on the dataverse service, not using a API lib, just the requests lib
# could be placed in a class that also keeps hold of the url and token that we initialise once!
#
# Also note that here we use the PID (persistentId) instead of the internal ID form of the requests.


def search(server_url, subtree, start=0, rows=10):
    '''
    Do a query via the public search API, only published datasets
    using the public search 'API', so no token needed

    Note that the current functionality of this function is very limited!

    :param subtree: This is the collection (dataverse alias)
                    it recurses into a collection and its children etc. very useful with nesting collection
    :param start: The cursor (zero based result index) indicating where the result page starts
    :param rows: The number of results returned in the 'page'
    :return: The 'paged' search results in a list of dictionaries
    '''

    # always type=dataset, those have pids (disregarding pids for files)
    params = {
                'q': '*',
                'subtree': subtree,
                'type': 'dataset',
                'per_page': str(rows),
                'start': str(start)
    }

    # params['fq'] = ''

    dv_resp = requests.get(server_url + '/api/search', params=params)

    # give some feedback
    # print("Status code: {}".format(dv_resp.status_code))
    # print("Json: {}".format(dv_resp.json()))
    # the json result is a dictionary... so we could check for something in it
    dv_resp.raise_for_status()
    resp_data = dv_resp.json()['data']
    # print(json.dumps(resp_data, indent=2))
    return resp_data

# TODO make exporter a param instead of hardcoded dataverse_json
# No token needed for public /published datsets
def get_dataset_metadata_export(server_url, pid):
    params = {'exporter': 'dataverse_json', 'persistentId': pid}
    dv_resp = requests.get(server_url + '/api/datasets/export',
                           params=params)

    # give some feedback
    # print("Status code: {}".format(dv_resp.status_code))
    # print("Json: {}".format(dv_resp.json()))
    # the json result is a dictionary... so we could check for something in it
    dv_resp.raise_for_status()
    # assume json, but not all exporters have that!
    resp_data = dv_resp.json()  # Note that the response json has no wrapper around the data
    return resp_data


# with a token, can also get metadata from drafts
def get_dataset_metadata(server_url, api_token, pid):
    headers = {'X-Dataverse-key': api_token}
    dv_resp = requests.get(server_url + '/api/datasets/:persistentId/versions/:latest?persistentId=' + pid,
                           headers=headers)
    # Maybe give some more feedback
    # print("Status code: {}".format(dv_resp.status_code))
    # print("Json: {}".format(dv_resp.json()))
    # the json result is a dictionary... so we could check for something in it
    dv_resp.raise_for_status()
    resp_data = dv_resp.json()['data']
    return resp_data


# note that the dataset will become a draft if it was not already
def replace_dataset_metadatafield(server_url, api_token, pid, field):
    headers = {'X-Dataverse-key': api_token}
    dv_resp = requests.put(
        server_url + '/api/datasets/:persistentId/editMetadata?persistentId=' + pid + '&replace=true',
        data=json.dumps(field, ensure_ascii=False),
        headers=headers)
    dv_resp.raise_for_status()


def get_dataset_roleassigments(server_url, api_token, pid):
    headers = {'X-Dataverse-key': api_token}
    params = {'persistentId': pid}
    try:
        dv_resp = requests.get(server_url + '/api/datasets/:persistentId/assignments',
                               params=params,
                               headers=headers)
        dv_resp.raise_for_status()
    except requests.exceptions.RequestException as re:
        print("RequestException: ", re)
        raise
    resp_data = dv_resp.json()['data']
    return resp_data


def delete_dataset_roleassigment(server_url, api_token, pid, assignment_id):
    headers = {'X-Dataverse-key': api_token}
    dv_resp = requests.delete(server_url + '/api/datasets/:persistentId/assignments/' + str(assignment_id)
                              + '?persistentId=' + pid,
                              headers=headers)
    dv_resp.raise_for_status()


def get_dataset_locks(server_url, pid):
    dv_resp = requests.get(server_url + '/api/datasets/:persistentId/locks?persistentId=' + pid)
    # give some feedback
    # print("Status code: {}".format(dv_resp.status_code))
    # print("Json: {}".format(dv_resp.json()))
    # the json result is a dictionary... so we could check for something in it
    dv_resp.raise_for_status()
    resp_data = dv_resp.json()['data']
    return resp_data


def delete_dataset_locks(server_url, api_token, pid):
    headers = {'X-Dataverse-key': api_token}
    dv_resp = requests.delete(server_url + '/api/datasets/:persistentId/locks?persistentId=' + pid,
                              headers=headers)
    dv_resp.raise_for_status()


def publish_dataset(server_url, api_token, pid, version_upgrade_type="major"):
    # version_upgrade_type must be 'major' or 'minor', indicating which part of next version to increase
    headers = {'X-Dataverse-key': api_token}
    dv_resp = requests.post(server_url + '/api/datasets/:persistentId/actions/:publish?persistentId='
                            + pid + '&type=' + version_upgrade_type,
                            headers=headers)
    dv_resp.raise_for_status()


# This is via the admin api and does not use the token,
# but instead will need to be run on localhost or via an SSH tunnel for instance!
def reindex_dataset(server_url, pid):
    dv_resp = requests.get(server_url + '/api/admin/index/dataset?persistentId=' + pid)
    dv_resp.raise_for_status()
    resp_data = dv_resp.json()['data']
    return resp_data


# Remember to get info on the OAI endpoint you can do:
# oai?verb=Identify
# oai?verb=ListSets
# oai?verb=ListMetadataFormats
# we could add function for that if we wanted
#
# Default there is no set specified and you get just all
# also no date range (with from, until)
def get_oai_records(server_url, format, set=None):
    params = {'verb': 'ListRecords', 'metadataPrefix': format}
    if set is not None:
        params['set'] = set
    dv_resp = requests.get(server_url + '/oai',
                           params=params)

    dv_resp.raise_for_status()
    # assume XML
    xml_doc = etree.fromstring(dv_resp.content)
    # alternatively we could use the parse directly and not requests.get
    # xml_doc = etree.parse(url).getroot()

    return xml_doc


def get_oai_records_resume(server_url, token):
    params = {'verb': 'ListRecords', 'resumptionToken': token}
    dv_resp = requests.get(server_url + '/oai',
                           params=params)

    dv_resp.raise_for_status()
    # assume XML
    xml_doc = etree.fromstring(dv_resp.content)
    return xml_doc

