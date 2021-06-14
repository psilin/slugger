# slugger
Small service for downloading slugs from [https://support.allizom.org/api/1/kb/](https://support.allizom.org/api/1/kb/) and serving it via FastAPI web service.

## Operating serving stack

All the following commands are supposed to be run from repo root.

How to start `PostgreSQL` docker container:
```shell
docker-compose up -d postgres
```
How to stop `PostgreSQL` docker container:
```shell
docker-compose stop postgres
```
How to start `FastAPI` docker container:
```shell
docker-compose up -d fastapi
```
How to stop `FastAPI` docker container:
```shell
docker-compose stop fastapi
```
Note that `FastAPI` container depends on `PostgreSQL` container.

All stack can be started/stopped with:
```shell
docker-compose up -d
```
and
```shell
docker-compose stop
```
respectively.

## How to run downloader script.

Note that downloader script cleans DB table before start to avoid conflicts while inserting data. Note that downloading script has dependencies. First of all, `PostgreSQL` container should be up for script to successfully insert data there. Second if you plan to download files to FS, corresponding directory should be created. So again, assume that you are in the repo root directory. To run the downloader script you need the following:
```shell
# deal with virtual environment
virtualenv venv
source venv/bin/activate
# FROM HERE YOU ARE IN VIRTULA ENVIRONMENT
# install requirements
 pip3 install -r requirements.txt
# create directory to store HTML files
mkdir htmls
# run script, where:
# -v designates debug output
# -s is a number of slugs to download (will be limited to actual size if bigger)
# -p is a path to where to store html files (if you decide to avoid it - just not specify this option)
python3 ./scripts/slug_downloader.py -v -s 800 -p htmls
```

## ToDo
 * update enpoint with input data validation;
 * httpx-based unit-testing;
 * pydantic model-based approach to data-structures.
