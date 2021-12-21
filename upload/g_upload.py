import pickle
import os
from os import walk
from threading import Thread
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly',
          'https://www.googleapis.com/auth/drive.file']


# Function to hide/show kivy widgets
def hide_widget(wid, dohide=True):
    if hasattr(wid, 'saved_attrs'):
        if not dohide:
            wid.height, wid.size_hint_y, wid.opacity, wid.disabled = wid.saved_attrs
            del wid.saved_attrs
    elif dohide:
        wid.saved_attrs = wid.height, wid.size_hint_y, wid.opacity, wid.disabled
        wid.height, wid.size_hint_y, wid.opacity, wid.disabled = 0, None, 0, True
        
class GUpload:

    def __init__(self):
        self.upload_thread = None
        self.service = self.get_gdrive_service()
        
    def get_gdrive_service(self):
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    './upload/credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        return build('drive', 'v3', credentials=creds)

    def start_upload_thread(self, fullpath, prog_bar ):
        self.upload_thread = Thread(target=self.upload_folder, args=(fullpath, prog_bar))
        self.upload_thread.start()

    def upload_folder(self, fullpath, prog_bar):
        folder_name = os.path.basename(os.path.normpath(fullpath))
        prog_bar.value = 0

        path_files = []
        for (dirpath, dirnames, filenames) in walk(fullpath):
            path_files.extend(filenames)
            break

        # print (path_files) # DEBUG
        """
        Creates a folder and upload a file to it
        """
        # authenticate account
        # self.service = get_gdrive_service()
        # folder details we want to make
        folder_metadata = {
            "name": str(folder_name),
            "mimeType": "application/vnd.google-apps.folder"
        }
        # create the folder
        file = self.service.files().create(body=folder_metadata, fields="id").execute()
        # get the folder id
        folder_id = file.get("id")
        print("Folder ID:", folder_id)
        
        # Upload all the files in the given path 
        n = len(path_files)
        for i, f in enumerate(path_files):
            # first, define file metadata, such as the name and the parent folder ID
            file_metadata = {
                "name": str(f),
                "parents": [folder_id]
            }
            # upload
            media = MediaFileUpload(os.path.join(fullpath, f), resumable=True)
            file = self.service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            prog_bar.value = int(((i +1)* 100) / n)
            # print("File created, id:", file.get("id"))  # DEBUG
            # print("Progress: " + str(prog_bar.value) )   # DEBUG
        
        hide_widget(prog_bar, True)

        
    



    
