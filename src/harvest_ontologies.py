#!/usr/bin/env python3

"""
This is a wrapper script to get a list of uuids to process for the ontology_mappings_extractor.
It queries ingest for appropriate projects after a given date and appends new data to the 'current_zooma_import' file.
It also provides a summary of the current curations for terms to check for any obvious errors.
It also creates a PR against master for the new file (?)
"""

import requests as rq
import argparse
import pandas as pd
from datetime import datetime
import time
import sys
import os
import glob
import os.path


def define_parser():
    parser = argparse.ArgumentParser(description="Parser for the arguments")
    parser.add_argument("--last-updated", "-u", action="store", dest="last_updated", type=str,
                        help="Enter date in from YYYY-MM-DD for the last time the data was updated.")
    parser.add_argument("--ingest-token", "-i", action="store", dest="ingest_token", type=str,
                        help="Enter token from ingest in order to access protected endpoints."),
    parser.add_argument("--don't get_ontologies", "-o", action="store_true", dest="dont_get_ontologies",
                        help="If specified, the program retrieves candidate projects but doesn't go on to retrieve "
                             "ontologies.")
    parser.add_argument("--uuid_file", "-f", action="store", dest="uuid_file",
                        help="Run with a text file of uuids rather than searching ingest.")
    return parser


def search_ingest(token, last_update):
    """
    Searches ingest for projects submitted after a certain date that have at least one submission and have a 'complete'
    or 'exported' status.
    :param token: auth token for ingest api
    :param last_update: The last time this script was run
    :return: 2D list of project uuids and project shortnames
    :rtype: list
    """
    ingest_api = "http://api.ingest.archive.data.humancellatlas.org/projects"
    auth_headers = {'Authorization': 'Bearer {}'.format(token), 'Content-Type': 'application/json'}
    done = False
    project_uuid_list = []
    i = 0
    while not done:
        i += 1
        response = rq.get(ingest_api, headers=auth_headers)
        if response:
            all_projects = response.json()
            total_pages = all_projects['page']['totalPages']
            print("Processing page {} of {}".format(i, total_pages), end="\r")
            for project in all_projects['_embedded']['projects']:
                if datetime.strptime(project['submissionDate'], '%Y-%m-%dT%H:%M:%S.%fZ') > last_update:
                    sub_env_response = rq.get(project['_links']['submissionEnvelopes']['href'])
                    sub_env_json = sub_env_response.json()
                    if sub_env_json['page']['totalElements'] > 0:
                        for sub_env in sub_env_json['_embedded']['submissionEnvelopes']:
                            if datetime.strptime(sub_env['submissionDate'], '%Y-%m-%dT%H:%M:%S.%fZ') > last_update:
                                if sub_env['submissionState'] in ['Exported', 'Complete']:
                                    project_uuid_list.append([project['uuid']['uuid'], project['content']['project_core']['project_short_name']])
                                    break
            if 'next' in all_projects['_links']:
                ingest_api = all_projects['_links']['next']['href']
            else:
                done = True
        else:
            print(ingest_api)
            print("Error retrieving information from the API. Try refreshing token.")
            sys.exit(0)
    return project_uuid_list


def get_ontology_mappings(file_name):
    """
    For a given set of project uuids, get ontology mappings.
    :param project_uuids:
    :type project_uuids:
    :return:
    :rtype:
    """
    os.system("python3 ontology_mappings_extractor.py -f {} -u".format(file_name))


def main(last_update, token, dont_get_ontologies, uuid_file):
    start_time = time.time()
    if uuid_file:
        get_ontology_mappings(uuid_file)
    else:
        try:
            last_update_date = datetime.strptime(last_update, '%Y-%m-%d')
        except ValueError as e:
            print(e)
            print("Please enter a valid date in YYYY-MM-DD format.")
            sys.exit(0)
        project_uuids = search_ingest(token, last_update_date)
        print("Found {} projects submitted after {}.".format(len(project_uuids), last_update_date))
        today_str = datetime.today().strftime('%Y-%m-%d')
        output_file_name = 'outputs/{}_project_uuids.txt'.format(today_str)
        with open(output_file_name, 'w') as output_file:
            tabbed_projects = ["\t".join(x) for x in project_uuids]
            output_file.write("\n".join(tabbed_projects))
        print("Wrote project uuids to {}.".format(output_file_name))
        if not dont_get_ontologies:
            get_ontology_mappings(output_file_name)
    mapping_files = glob.glob('outputs/*_property_mappings.tsv')
    new_zooma = pd.read_csv(max(mapping_files, key=os.path.getctime), sep="\t")
    old_zooma = pd.read_csv('outputs/current_zooma_import.txt', sep="\t")
    updated_zooma = pd.concat([old_zooma, new_zooma]).drop_duplicates()
    updated_zooma.to_csv('outputs/updated_zooma.txt', sep="\t", index=False)
    print("Updated the zooma file at 'outputs/updated_zooma.txt.")
    execution_time = time.time() - start_time
    print("This took {} minutes.".format(str(round(execution_time/60, 2))))


if __name__ == "__main__":
    parser = define_parser()
    args = parser.parse_args()
    main(args.last_updated, args.ingest_token, args.dont_get_ontologies, args.uuid_file)
