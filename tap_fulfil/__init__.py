#!/usr/bin/env python3
import os
import json
from datetime import datetime, date
import pytz
import singer
from singer import utils
from singer.catalog import Catalog
from singer.bookmarks import write_bookmark, get_bookmark
from singer.messages import write_record, write_state, write_schema
from fulfil_client import Client

REQUIRED_CONFIG_KEYS = ["subdomain", "api_key"]
LOGGER = singer.get_logger()


def get_abs_path(path):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), path)


# Load schemas from schemas folder
def load_schemas():
    schemas = {}

    for filename in os.listdir(get_abs_path('schemas')):
        path = get_abs_path('schemas') + '/' + filename
        file_raw = filename.replace('.json', '')
        with open(path) as file:
            schemas[file_raw] = json.load(file)

    return schemas


DEFAULT_PROPERTIES = {
    "create_date": {
        "type": ["null", "string"],
        "format": "date-time",
    },
    "write_date": {
        "type": ["null", "string"],
        "format": "date-time",
    },
    "rec_name": {
        "type": ["null", "string"],
    },
    "id": {
        "type": ["integer"],
    },
}


def discover():
    raw_schemas = load_schemas()
    streams = []

    for schema_name, schema in raw_schemas.items():
        stream_metadata = [
            {
                "metadata": {
                    "inclusion": "available",
                    "table-key-properties": ["id"],
                    "forced-replication-method": MODEL_REPLICATION_METHOD[
                        STREAM_MODEL_MAP[schema_name]
                    ]
                },
                "breadcrumb": []
            },
            {
                "metadata": {
                    "inclusion": "automatic",
                },
                "breadcrumb": ["properties", "id"]
            },
            {
                "metadata": {
                    "inclusion": "automatic",
                },
                "breadcrumb": ["properties", "create_date"]
            },
            {
                "metadata": {
                    "inclusion": "automatic",
                },
                "breadcrumb": ["properties", "write_date"]
            },
            {
                "metadata": {
                    "inclusion": "available",
                },
                "breadcrumb": ["properties", "rec_name"]
            },
        ]
        stream_key_properties = ['id']
        schema["properties"].update(DEFAULT_PROPERTIES)

        # create and add catalog entry
        catalog_entry = {
            'stream': schema_name,
            'tap_stream_id': schema_name,
            'schema': schema,
            'metadata' : stream_metadata,
            'key_properties': stream_key_properties,
        }
        streams.append(catalog_entry)

    return Catalog.from_dict({'streams': streams})


def get_selected_streams(catalog):
    '''
    Gets selected streams.  Checks schema's 'selected' first (legacy)
    and then checks metadata (current), looking for an empty breadcrumb
    and mdata with a 'selected' entry
    '''
    selected_streams = []
    for stream in catalog.streams:
        stream_metadata = stream.metadata
        if stream.schema.selected:
            selected_streams.append(stream.tap_stream_id)
        else:
            for entry in stream_metadata:
                # stream metadata will have empty breadcrumb
                if not entry['breadcrumb'] and \
                        entry['metadata'].get('selected', None):
                    selected_streams.append(stream.tap_stream_id)

    return selected_streams


def sync(config, state, catalog):

    selected_stream_ids = get_selected_streams(catalog)

    # Loop over streams in catalog
    for stream in catalog.streams:
        if stream.tap_stream_id in selected_stream_ids:
            LOGGER.info('Syncing stream: %s', stream.tap_stream_id)
            sync_records(config, state, stream)
            LOGGER.info('Syncing completed: %s', stream.tap_stream_id)


STREAM_MODEL_MAP = {
    'contacts': 'party.party',
    'sales_orders': 'sale.sale',
}
MODEL_REPLICATION_METHOD = {
    'party.party': 'FULL_TABLE',
    'sale.sale': 'INCREMENTAL',
}


def get_sync_domain(state, stream, model_name):
    """
    Return a domain (a filter expression) that can be used to filter
    records.

    If the model's replication methd
    """
    domain = []
    for entry in stream.metadata:
        # stream metadata will have empty breadcrumb
        if not entry['breadcrumb'] and \
                entry['metadata'].get('replication-method', None) == 'FULL_TABLE':
            return domain

    last_updated_at = get_bookmark(
        state, stream.tap_stream_id, 'last_updated_at'
    )
    if last_updated_at:
        last_updated_at = utils.strptime(last_updated_at)
        domain.extend([
            'OR',
            [('write_date', '>', last_updated_at)],
            [('create_date', '>', last_updated_at)],
        ])
    last_record_id = get_bookmark(
        state, stream.tap_stream_id, 'last_record_id'
    )
    if last_record_id:
        domain.append(
            ('id', '>', last_record_id)
        )
    return domain


def sync_records(config, state, stream):
    write_schema(
        stream.tap_stream_id,
        stream.schema.to_dict(),
        stream.key_properties,
    )

    client = Client(config['subdomain'], config['api_key'])
    model_name = STREAM_MODEL_MAP[stream.tap_stream_id]
    model = client.model(model_name)
    domain = get_sync_domain(state, stream, model_name)
    sort_order = [
        ('write_date', 'asc'),
        ('create_date', 'asc'),
        ('id', 'asc'),
    ]

    # Get all fields defined in schema now
    fields = list(stream.schema.properties.keys())

    # Add create and write date to keep track of state
    fields.extend(['id', 'create_date', 'write_date'])
    for record in model.search_read_all(domain, sort_order, fields):
        transform(record)
        write_record(
            stream.tap_stream_id,
            record,
            time_extracted=utils.now()
        )
        state = write_bookmark(
            state,
            stream.tap_stream_id,
            'last_updated_at',
            record['write_date'] or record['create_date']
        )
        state = write_bookmark(
            state,
            stream.tap_stream_id,
            'last_record_id',
            record['id']
        )
        write_state(state)


def transform(record_dict):
    """
    Transform complex objects into simpler objects for JSON serialization
    """
    for key, value in record_dict.items():
        if isinstance(value, datetime):
            record_dict[key] = utils.strftime(
                value.replace(tzinfo=pytz.UTC)
            )
        elif isinstance(value, date):
            record_dict[key] = value.isoformat()
    return record_dict


@utils.handle_top_exception(LOGGER)
def main():

    # Parse command line arguments
    args = utils.parse_args(REQUIRED_CONFIG_KEYS)

    # If discover flag was passed, run discovery mode and dump output to stdout
    if args.discover:
        catalog = discover()
        catalog.dump()
    # Otherwise run in sync mode
    else:

        # 'catalog' is the current name
        if args.catalog:
            catalog = args.catalog
        else:
            catalog = discover()

        sync(args.config, args.state, catalog)


if __name__ == "__main__":
    main()
