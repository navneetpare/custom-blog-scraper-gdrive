import os
import requests
import re
import yaml
from bs4 import BeautifulSoup

from google.api_wrappers import google_drive_get_file_metadata, google_drive_download_file, google_drive_get_service, \
    google_drive_get_files_in_folder


def get_links_on_pages(page_url):
    links_on_page = []
    response = requests.get(page_url)
    soup = BeautifulSoup(response.text, "html.parser")
    a_tags = soup.findAll("a")
    for i in a_tags:
        try:
            link_on_page = i['href']
            links_on_page.append(link_on_page)
        except KeyError:
            pass
    return links_on_page


def filter_links(link_list, pattern):
    r = re.compile(pattern)
    return list(filter(r.match, link_list))


def download_file(drive_service, directory, file_id):
    metadata = google_drive_get_file_metadata(drive_service, file_id)
    skip_download = False
    file_size_google_drive = metadata.get('size')
    file_name = metadata.get('name')
    file = os.path.join(directory, file_name)
    file_exists = os.path.exists(file)

    if file_exists:
        file_size_on_disk = os.stat(os.path.join(directory, file_name)).st_size
        if int(file_size_google_drive) == int(file_size_on_disk):
            skip_download = True
            print(' -- ' + file_name + " : Already downloaded. Skipping.")
        elif int(file_size_google_drive) != int(file_size_on_disk):
            skip_download = False
            print(" -- " + file_name + " : Previous incomplete download. Deleting.")
            try:
                print('-- Deleted')
            except Exception as e:
                print('-- Unable to delete. Skipping this file. Error: ' + str(e))

    if not skip_download:
        print("-- " + file_name + " : Starting download.")
        google_drive_download_file(drive_service, file_id, file)


def scrape():
    # init
    with open('conf/config.yaml') as config_file:
        config = yaml.load(config_file, Loader=yaml.FullLoader)

    initial_blog_pages = config['initial_blog_pages']
    url_pattern_filters = config['url_pattern_filters']
    scraping_complete = config['scraping_complete']
    all_blog_pages = []

    if not scraping_complete:
        # scrape the initial pages and build list of nested blog pages
        print('-- Scraping the initial pages and building list of nested blog pages')
        for url in initial_blog_pages:
            all_blog_pages.extend(get_links_on_pages(url))
        all_blog_pages = list(dict.fromkeys(all_blog_pages))

        # filter nested blog pages by certain patterns, e.g., #comments pages
        print('-- Filtering nested blog pages')
        for pattern in url_pattern_filters:
            all_blog_pages = filter_links(all_blog_pages, pattern)

        # scrape each nested blog page for GDrive links
        print('-- Scraping for Google Drive Links')
        google_drive_links = []
        for page in all_blog_pages:
            google_drive_links.extend(filter_links(get_links_on_pages(page), '.*drive.google*'))

        # separate GDrive file links from folder links
        google_file_ids = ([i.split("/")[5] for i in google_drive_links if '/file/d' in i])
        google_folder_ids = ([i.split("/")[6].split("?")[0] for i in google_drive_links if '/folders/' in i])

        print('-- Scraped File IDs:')
        print(google_file_ids)
        print('-- Scraped Folder IDs:')
        print(google_folder_ids)

        # Search files within Google Drive folders and get file links, append to main file list
        print('-- Searching inside GDrive folders')
        drive_service = google_drive_get_service()  # init GDrive connection

        if len(google_folder_ids) > 0:
            for folder_id in google_folder_ids:
                google_file_ids.extend(google_drive_get_files_in_folder(drive_service, folder_id))
        print('-- Search complete')
        google_file_ids = list(dict.fromkeys(google_file_ids))  # Deduplication
        print('-- ' + str(google_file_ids))

        try:
            with open('conf/index.yaml', 'w+') as index_file:
                yaml.dump(google_file_ids, index_file)
                print('-- Saved scraped ids')
                config['scraping_complete'] = True
        except IOError:
            print('-- Unable to save scraped ids')

        try:
            with open('conf/config.yaml', 'w+') as config_file:
                yaml.dump(config, config_file)
                print('-- Config updated')
        except IOError:
            print('-- Unable to overwrite config. Please try manually.')


def execute():

    scrape()
    with open('conf/config.yaml') as config_file:
        config = yaml.load(config_file, Loader=yaml.FullLoader)

    with open('conf/index.yaml') as index_file:
        google_file_ids = yaml.load(index_file, Loader=yaml.FullLoader)

    download_dir = config['download_dir']
    scraping_complete = config['scraping_complete']

    drive_service = google_drive_get_service()

    if scraping_complete:

        for file_id in google_file_ids:
            try:
                download_file(drive_service, download_dir, file_id)
            except Exception:
                drive_service = google_drive_get_service()
                download_file(drive_service, download_dir, file_id)

    print('-- Finished.')