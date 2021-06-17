from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.http import MediaIoBaseDownload


SCOPES = ['https://www.googleapis.com/auth/drive.readonly']


def google_drive_get_service():
    flow = InstalledAppFlow.from_client_secrets_file(
        'secrets/client_secrets.json', SCOPES)
    credentials = flow.run_local_server(port=8080)
    service = build('drive', 'v3', credentials=credentials)
    return service


def google_drive_get_files_in_folder(service, folder_id):
    file_list = []
    page_token = None
    while True:
        response = service.files().list(q=str("'" + folder_id + "' in parents"),
                                        corpora='allDrives',
                                        includeItemsFromAllDrives=True,
                                        supportsAllDrives=True,
                                        spaces='drive',
                                        fields='nextPageToken, files(id, name)',
                                        pageSize=1000,
                                        pageToken=page_token).execute()
        for file in response.get('files', []):
            file_list.append(file.get('id'))
        page_token = response.get('nextPageToken', None)
        if page_token is None:
            break
    return file_list


def google_drive_get_file_metadata(service, file_id):
    response = service.files().get(fileId=file_id, fields='id, name, size').execute()
    return response


def google_drive_download_file(service, file_id, file_name):
    request = service.files().get_media(fileId=file_id)
    fh = open(file_name, "wb+")
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print(" -- Download %d%%." % int(status.progress() * 100))