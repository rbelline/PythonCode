import subprocess
import configparser
import argparse
import logging
import json

from datetime import datetime, timedelta, timezone
from azure.storage.blob import BlobServiceClient, AccountSasPermissions, generate_account_sas, ResourceTypes

logging.basicConfig(level=logging.INFO)

parser = argparse.ArgumentParser(description="Databricks Environment Variable")
env = parser.add_argument("--env", type=str, required=True, help="dev, qa, prod")
# args = parser.parse_args()
env = "dev"

def read_config():
    config = configparser.ConfigParser()
    read_config = config.read('config.ini')
    if read_config:
        print('Config file read correctly')
    else:
        print('Unable to read config file')
    return config

def strip_quotes(string):
        return string.strip('"').strip("'")
    
def generate_list(string):
    if ',' in string:
        remove_quotes = string.strip("'").strip('"')
        single_string = [item.strip() for item in remove_quotes.split(",")]
        return single_string
    else:
        remove_quotes = string.strip("'").strip('"')
        return remove_quotes.split(",")

def get_config_parameters(config):
    source_account_key = strip_quotes(config['AzureStorage']['source_account_key'])
    source_account_name = strip_quotes(config['AzureStorage']['source_account_name']) + env #this must be parametrized from env var
    source_containers_name = generate_list(config['AzureStorage']['source_container_name'])
    destination_account_key = strip_quotes(config['AzureStorage']['destination_account_key'])
    destination_account_name = strip_quotes(config['AzureStorage']['destination_account_name']) + env #this must be parametrized from env var
    destination_containers_name = generate_list(config['AzureStorage']['destination_container_name'])
    print(f"Source account name: {source_account_name}")
    print(f"Source containers: {source_containers_name}")
    return source_account_key, source_account_name, source_containers_name, destination_account_key, destination_account_name, destination_containers_name

def generate_sas_token(source_account_name, source_account_key):
    # Define permissions for the SAS token
    permissions = AccountSasPermissions(read=True, write=True, process=True, update=True, add=True, list=True)
    # Set the expiry time for the SAS token (valid for 1 hour for example)
    expiry = datetime.now() + timedelta(hours=6)
    start = datetime.now() - timedelta(hours=6)
    # Generate the SAS token
    sas_token = generate_account_sas(
        account_name=source_account_name,
        account_key=source_account_key,
        resource_types=ResourceTypes(service=True, container=True, object=True),
        permission=permissions,
        expiry=expiry,
        start=start
    )
    return sas_token

def azcopy(source_container_url, destination_container_url, path, include_after):
    try:
        azcopy_command = [
            'azcopy', 'copy', source_container_url, destination_container_url,
            '--recursive=true', '--overwrite=ifSourceNewer', '--log-level=ERROR', '--check-length=false'
        ]
        if path:
            azcopy_command.append(f'--include-regex={path}')
        if include_after:
            azcopy_command.append(f'--include-after={include_after}')
            logging.info(f"Copying blobs from last backup date {include_after}")
        else:
            logging.info(f"Copying all blobs")
        logging.info(f"Executing AzCopy command: {' '.join(azcopy_command)}")
        subprocess.run(azcopy_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info(f"Blob copied successfully: {destination_container_url}")
    except subprocess.CalledProcessError as e:
        logging.error(f"AzCopy failed: {e.stderr.decode() if e.stderr else str(e)}")
    except Exception as e:
        logging.error(f"Error during blob copy: {e}")

def azset_properties(destination_container_url):
    try:
        azsetproperties_archive_command = [
            'azcopy', 'set-properties',
            destination_container_url,  # Provide the container or directory URL here
            '--block-blob-tier=hot',  # Specify the tier or other properties
            '--recursive=true'  # Apply properties recursively
        ]
        subprocess.run(azsetproperties_archive_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info(f"Blob properties set to archive: {destination_container_url}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Az set properties failed: {e.stderr.decode() if e.stderr else str(e)}")
    except Exception as e:
        logging.error(f"Error during blob property setting: {e}")

def connection_strings(source_account_name, source_account_key, destination_account_name, destination_account_key):
    source_connection_string = f"DefaultEndpointsProtocol=https;AccountName={source_account_name};AccountKey={source_account_key};EndpointSuffix=core.windows.net"
    destination_connection_string = f"DefaultEndpointsProtocol=https;AccountName={destination_account_name};AccountKey={destination_account_key};EndpointSuffix=core.windows.net"
    return source_connection_string, destination_connection_string

def blob_clients(source_connection_string, destination_connection_string):
    source_blob_service_client = BlobServiceClient.from_connection_string(source_connection_string)
    destination_blob_service_client = BlobServiceClient.from_connection_string(destination_connection_string)
    return source_blob_service_client, destination_blob_service_client

def check_container_exists(destination_blob_service_client, destination_container):
    try:
        container_client = destination_blob_service_client.get_container_client(destination_container)
        if not container_client.exists():
            container_client.create_container()
            logging.info(f"Container '{destination_container}' created.")
        else:
            logging.info(f"Container '{destination_container}' already exists.")
    except Exception as e:
        logging.error(f"Error checking if {destination_container} exists {e}")
    
def check_container_metadata_exists(destination_blob_service_client):
    try:
        metadata_container = "backup-metadata"
        container_client = destination_blob_service_client.get_container_client(metadata_container)
        if not container_client.exists():
            container_client.create_container()
            logging.info(f"container {metadata_container} created")
        else:
            logging.info(f"container {metadata_container} alrteady exists")
    except Exception as e:
        logging.error(f"Error checking if {metadata_container} exists {e}")

def save_metadata(destination_blob_service_client, env, backup_start_time):
    try:
        metadata_container = "backup-metadata"
        metadata_filename = "backup_metadata.json"

        container_client = destination_blob_service_client.get_container_client(metadata_container)
        blob_client = container_client.get_blob_client(metadata_filename)

        metadata = {"env": env, "last_backup_timestamp":backup_start_time}
        logging.info(f"Metadata to save: {metadata}")

        try:
            existing_blob = blob_client.download_blob()
            # If it exists, read its content and append the new metadata
            existing_metadata = json.loads(existing_blob.readall())
            existing_metadata.append(metadata)
        except Exception as e:
            # If the blob doesn't exist (error), initialize an empty list for metadata
            logging.warning(f"Blob not found, creating a new one. Error: {e}")
            existing_metadata = [metadata]  # Start with the first metadata entry

        metadata_json = json.dumps(existing_metadata)
        blob_client.upload_blob(metadata_json, overwrite=True)  # Upload the updated JSON
        logging.info(f"Metadata saved to blob: {metadata_filename}")

    except Exception as e:
        logging.error(f"Error to save metadata: {e}")
        raise

def load_metadata(destination_blob_service_client, target_env):
    try:
        metadata_container = "backup-metadata"
        metadata_filename = "backup_metadata.json"

        container_client = destination_blob_service_client.get_container_client(metadata_container)
        blob_client = container_client.get_blob_client(metadata_filename)

        if blob_client.exists():
            downloaded_blob = blob_client.download_blob()
            metadata_json = downloaded_blob.readall().decode('utf-8')
            all_metadata = json.loads(metadata_json)

            filtered_metadata = [data for data in all_metadata if data.get('env') == target_env]

            if not filtered_metadata:
                logging.warning(f"no metadata found for environment: {target_env}")
                return None
            
            latest_metadata = max(
                filtered_metadata,
                key=lambda x: x.get('last_backup_timestamp', ''),
            )

            logging.info(f"metadata loaded for env: {target_env}, {latest_metadata}")
            return latest_metadata
        else:
            logging.warning(f"metadata file {metadata_filename} does not exists")
            return None
    except Exception as e:
        logging.error(f"error loading metadata: {e}")
        raise

def copy_blobs_with_azcopy(
    source_account_name, source_account_key, 
    destination_account_name, destination_account_key, 
    source_containers_name, destination_containers_name, 
    source_connection_string, destination_connection_string):

    source_blob_service_client, destination_blob_service_client = blob_clients(source_connection_string, destination_connection_string)

    source_sas_token = generate_sas_token(source_account_name, source_account_key)
    destination_sas_token = generate_sas_token(destination_account_name, destination_account_key)

    check_container_metadata_exists(destination_blob_service_client)

    metadata = load_metadata(destination_blob_service_client, env)
    if metadata:
        include_after = metadata['last_backup_timestamp']
        print(f"data will be backup from this date: {include_after}")
    else:
        include_after = None
    
    # Get current time in local CET timezone
    local_time = datetime.now()

    # Define CET timezone as UTC+1 (standard time) or UTC+2 (daylight saving)
    cet_offset = timedelta(hours=1)  # Adjust to +2 if daylight saving time is active
    cet_timezone = timezone(cet_offset)

    # Local CET time to UTC
    local_time_cet = local_time.replace(tzinfo=cet_timezone)
    utc_time = local_time_cet.astimezone(timezone.utc)

    # Format the UTC time for Azure
    include_after_timestamp = utc_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    print(include_after_timestamp)
    backup_start_time = datetime.now()
    logging.info(f"Backup started at {backup_start_time}")

    path = 'ee125af1-7446-4cf1-9e3a-d75c16a74ba6'

    # Loop through containers to copy blobs
    for source_container, destination_container in zip(source_containers_name, destination_containers_name):
        check_container_exists(destination_blob_service_client, destination_container)
        # Generate source and destination container URLs with SAS token
        source_container_url = f"https://{source_account_name}.blob.core.windows.net/{source_container}?{source_sas_token}"
        destination_container_url = f"https://{destination_account_name}.blob.core.windows.net/{destination_container}?{destination_sas_token}"

        azcopy(source_container_url, destination_container_url, path, include_after)
        azset_properties(destination_container_url)

    save_metadata(destination_blob_service_client, env, include_after_timestamp)
    backup_end_time = datetime.now()
    elapsed_time = backup_end_time - backup_start_time
    logging.info(f"Total backup time: {elapsed_time}")
    print("end of for loop")

def main():
    config = read_config()
    get_config_parameters(config)
    source_account_key, \
    source_account_name, \
    source_containers_name, \
    destination_account_key, \
    destination_account_name, \
    destination_containers_name = get_config_parameters(config)

    source_connection_string, destination_connection_string = connection_strings(source_account_name, source_account_key, destination_account_name, destination_account_key)
    copy_blobs_with_azcopy(
        source_account_name,
        source_account_key,
        destination_account_name,
        destination_account_key,
        source_containers_name,
        destination_containers_name,
        source_connection_string,
        destination_connection_string,
    )
    
if __name__ == "__main__":
    main()
