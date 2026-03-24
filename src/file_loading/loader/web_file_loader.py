import os.path
from email.message import EmailMessage
from urllib.parse import unquote

import requests
import mimetypes


class WebFileLoader:
    @staticmethod
    def load_file(url: str, folder_path: str, file_name: str | None = None) -> bool:
        query_parameters = {"downloadformat": "xlsx"}
        response = requests.get(url, params=query_parameters)

        if response.status_code != 200:
            print(f"failed to load. status code: {response.status_code}")
            return False

        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        if not file_name:
            content_disposition = response.headers.get('Content-Disposition')
            file_name = WebFileLoader._get_file_name(url, content_disposition)

        content_type = response.headers.get('Content-Type', '').split(';')[0]
        file_name = WebFileLoader._form_path(file_name, url, content_type)

        full_path = os.path.join(folder_path, file_name)

        with open(full_path, 'wb') as f:
            f.write(response.content)

        print(f"loaded to {full_path}")
        return True


    @staticmethod
    def _guess_file_extension(url: str, content_type: str) -> str | None:
        mimetypes.init()

        type_from_url: str | None = mimetypes.guess_type(url=url)[0]
        if type_from_url:
            extensions_1: list[str] = mimetypes.guess_all_extensions(type_from_url)
        else:
            extensions_1: list[str] = []

        extensions_2: list[str] = mimetypes.guess_all_extensions(content_type)
        common_extensions: set[str] = set(extensions_1).intersection(extensions_2)
        return common_extensions.pop() if len(common_extensions) == 1 else None

    @staticmethod
    def _find_path_extension(path: str) -> str | None:
        extension: str | None = mimetypes.guess_file_type(path)[0]
        return extension

    @staticmethod
    def _form_path(path: str, url: str, content_type: str) -> str:
        path_ext = WebFileLoader._find_path_extension(path)
        url_ext = WebFileLoader._guess_file_extension(url, content_type)

        if path_ext == url_ext:
            return f"{path}{path_ext}" if path_ext else path
        elif url_ext:
            return f"{path}{url_ext}"
        else:
            return path

    @staticmethod
    def _get_file_name(url: str, content_disposition: str) -> str | None:
        file_name = None
        if content_disposition:
            msg = EmailMessage()
            msg['Content-Disposition'] = content_disposition
            file_name = msg.get_filename()
        if not file_name:
            file_name = unquote(url.split('/')[-1].split('?')[0])
        if not file_name:
            file_name = "downloaded_file"
        file_name = os.path.basename(file_name)
        return file_name

