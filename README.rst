This is a personal project for scraping a specific blog.

*Configuration Required:*

* <WORKING_DIR>/config.yaml file with the following syntax::

            ---
            download_dir: <path-on-disk>
            initial_blog_pages:
            - <blog-page-url-1>
            - <blog-page-url-2>
            scraping_complete: false
            url_pattern_filters:
            - <regex-pattern-1>
            - <regex-pattern-2>

* Google API OAuth Credentials must be setup as per https://developers.google.com/drive/api/v3/quickstart/python. The project uses GoogleDrive API v3 and spins up a web-server on localhost:8080 for Google's OAuth Consent Page. The client credentials must be stored in <WORKING_DIR>/secrets/client_secrets.json
