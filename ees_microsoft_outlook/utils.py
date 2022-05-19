#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""This module contains utility methods.
"""
import csv
import os
import time
import urllib.parse
from datetime import datetime

import exchangelib
import pytz
from bs4 import BeautifulSoup
from exchangelib import EWSTimeZone
from tika import parser

from .adapter import SCHEMA
from .constant import DEFAULT_TIME_ZONE, RFC_3339_DATETIME_FORMAT


def extract(content):
    """Extracts the contents
    :param content: content to be extracted
    Returns:
        parsed_test: parsed text
    """
    parsed = parser.from_buffer(content)
    parsed_text = parsed["content"]
    return parsed_text


def url_encode(object_name):
    """Performs encoding on the name of objects
    containing special characters in their url, and
    replaces single quote with two single quote since quote
    is treated as an escape character in data
    :param object_name: name that contains special characters
    """
    name = urllib.parse.quote(object_name, safe="'")
    return name.replace("'", "''")


def retry(exception_list):
    """Decorator for retrying in case of server exceptions.
    Retries the wrapped method `times` times if the exceptions listed
    in ``exceptions`` are thrown
    :param exception_list: Lists of exceptions on which the connector should retry
    """

    def decorator(func):
        """This function used as a decorator."""

        def execute(self, *args, **kwargs):
            """This function execute the retry logic."""
            retry = 1
            while retry <= self.retry_count:
                try:
                    return func(self, *args, **kwargs)
                except exception_list as exception:
                    self.logger.exception(
                        f"Error while creating a connection. Retry count: {retry} out of {self.retry_count}. "
                        f"Error: {exception}"
                    )
                    time.sleep(2**retry)
                    retry += 1

        return execute

    return decorator


def fetch_users_from_csv_file(user_mapping, logger):
    """This method is used to map sid to username from csv file.
    :param user_mapping: path to csv file containing source user to enterprise search mapping
    :param logger: logger object
    :returns: dictionary of sid and username
    """
    rows = {}
    if (
        user_mapping and os.path.exists(user_mapping) and os.path.getsize(user_mapping) > 0
    ):
        with open(user_mapping, encoding="utf-8") as mapping_file:
            try:
                csvreader = csv.reader(mapping_file)
                for row in csvreader:
                    rows[row[0]] = row[1]
            except csv.Error as e:
                logger.exception(
                    f"Error while reading user mapping file at the location: {user_mapping}. Error: {e}"
                )
    return rows


def split_list_into_buckets(documents, total_buckets):
    """Divide large number of documents amongst the total buckets
    :param documents: list to be partitioned
    :param total_buckets: number of buckets to be formed
    """
    if documents:
        groups = min(total_buckets, len(documents))
        group_list = []
        for i in range(groups):
            group_list.append(documents[i::groups])
        return group_list
    else:
        return []


def split_documents_into_equal_chunks(documents, chunk_size):
    """This method splits a list or dictionary into equal chunks size
    :param documents: List or Dictionary to be partitioned into chunks
    :param chunk_size: Maximum size of a chunk
    Returns:
        list_of_chunks: List containing the chunks
    """
    list_of_chunks = []
    for i in range(0, len(documents), chunk_size):
        if type(documents) is dict:
            partitioned_chunk = list(documents.items())[i: i + chunk_size]
            list_of_chunks.append(dict(partitioned_chunk))
        else:
            list_of_chunks.append(documents[i: i + chunk_size])
    return list_of_chunks


def get_current_time():
    """Returns current time in rfc 3339 format"""
    return (datetime.utcnow()).strftime(RFC_3339_DATETIME_FORMAT)


def html_to_text(content):
    """Convert html content to text format
    :param content: HTML content
    Returns:
        text: Converted Text
    """
    if content:
        soup = BeautifulSoup(content, "html.parser")
        text = soup.get_text().strip()
        return text


def change_datetime_ews_format(utc_datetime):
    """Change datetime format to EWS timezone
    :param utc_datetime: Datetime in UTC format
    Returns:
        Datetime: Datetime with EWS format
    """
    return datetime.strptime(utc_datetime, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=EWSTimeZone(DEFAULT_TIME_ZONE)
    )


def change_datetime_format(datetime, timezone):
    """Change datetime format to user account timezone
    :param utc_datetime: Datetime in UTC format
    :param timezone: User account timezone
    Returns:
        Datetime: Date format as user account timezone
    """
    if isinstance(datetime, exchangelib.ewsdatetime.EWSDateTime):
        return (datetime.astimezone(pytz.timezone(str(timezone)))).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    elif isinstance(datetime, exchangelib.ewsdatetime.EWSDate):
        return datetime.strftime("%Y-%m-%d")
    else:
        return None


def insert_document_into_doc_id_storage(ids_list, id, parent_id, type, platform):
    """This function is used to prepare item for deletion and insert into global variable.
    :param ids_list: Pass "global_keys" of doc ids JSON file
    :param id: Pass id of mail, contacts, calendar events, tasks
    :param parent_id: Pass parent id of id property
    :param type: Pass type of each document for deletion.
    :param platform: Pass platform of document like Office365, Microsoft Exchange
    Returns:
        ids_list: Updated ids_list
    """
    new_item = {
        "id": str(id),
        "parent id": parent_id,
        "type": type,
        "platform": platform,
    }
    if new_item not in ids_list:
        return ids_list.append(new_item)
    else:
        return ids_list


def get_schema_fields(document_name, objects):
    """Returns the schema of all the include_fields or exclude_fields specified in the configuration file.
    :param document_name: Document name from Mails, Calendar, Tasks, Contacts etc.
    Returns:
        schema: Included and excluded fields schema
    """
    fields = objects.get(document_name)
    adapter_schema = SCHEMA[document_name]
    field_id = adapter_schema["id"]
    if fields:
        include_fields = fields.get("include_fields")
        exclude_fields = fields.get("exclude_fields")
        if include_fields:
            adapter_schema = {
                key: val for key, val in adapter_schema.items() if val in include_fields
            }
        elif exclude_fields:
            adapter_schema = {
                key: val
                for key, val in adapter_schema.items()
                if val not in exclude_fields
            }
        adapter_schema["id"] = field_id
    return adapter_schema


class CustomException(Exception):
    """Exception raised when there is an error in user fetching.
    Attributes:
        message -- Error message
    """

    def __init__(self, message):
        self.message = message


def split_date_range_into_chunks(start_time, end_time, number_of_threads):
    """Divides the timerange in equal partitions by number of threads
    :param start_time: Start time of the interval
    :param end_time: End time of the interval
    :param number_of_threads: Number of threads defined into config file for producer process
    """
    start_time = datetime.strptime(start_time, RFC_3339_DATETIME_FORMAT)
    end_time = datetime.strptime(end_time, RFC_3339_DATETIME_FORMAT)

    diff = (end_time - start_time) / number_of_threads
    datelist = []
    for idx in range(number_of_threads):
        date_time = start_time + diff * idx
        datelist.append(date_time.strftime(RFC_3339_DATETIME_FORMAT))
    formatted_end_time = end_time.strftime(RFC_3339_DATETIME_FORMAT)
    datelist.append(formatted_end_time)
    return datelist


def is_document_in_present_data(document_item, id):
    """This method is used filter removed document by id
    :param document_item: Pass document
    :param id: Pass id of the document which you want to match
    """
    return document_item["id"] == id
