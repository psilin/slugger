import enum
import json
import logging
import multiprocessing as mp
import os
import queue
import typing

import click
import psycopg2
import requests

BASE_URL = "https://support.allizom.org/api/1/kb/"
# would go for putting password in env variable in prod case
DSN = "host=localhost dbname=postgres user=postgres password=postgres"
SLUG_KEYS = [
    "id",
    "title",
    "slug",
    "url",
    "locale",
    "products",
    "topics",
    "summary",
    "html",
]

LOGGER_NAME = "Slug Downloader"


class SlugProcessStatus(enum.Enum):
    """
    Statuses of slug processing
    """

    OK = 1
    DOWNLOAD_FAILED = 2
    SLUG_INCOMPLETE = 3
    FAILED_PUT_TO_DB = 4
    FAILED_TO_WRITE_TO_FS = 5
    EXCEPTION = 6


def download_slug_names(
    slug_number: int,
) -> typing.Tuple[mp.Queue, int]:
    """
    Downloading slug names. Decided to not parallelise it as it will take
    small piece of overall execution time anyway. And relatively small for
    maximum possible number of slugs anyway.
    :slug_number: number of slugs to download
    :returns: queue with all slugs to download (again there not much of them
    so it is ok), and actual size of the queue (you can not get it directly
    on Mac OS X) due to a bug, so this value is a workaround for this.
    """
    logger = logging.getLogger(LOGGER_NAME)
    url = BASE_URL
    r = requests.get(url=url)
    r.raise_for_status()
    body = r.json()
    actual_slug_number = body["count"]
    if actual_slug_number < slug_number:
        logger.info(
            f"Total number of slug: {actual_slug_number} is less than "
            + f"what we want: {slug_number}, will download what we can."
        )
        slug_number = actual_slug_number

    task_queue: "mp.Queue[str]" = mp.Queue(maxsize=slug_number + 1)

    cnt = 0
    while True:
        for res in body["results"]:
            logger.debug(f"{cnt} added slug {res['slug']} to task queue.")
            task_queue.put(res["slug"])
            cnt += 1
            if cnt == slug_number:
                return task_queue, slug_number

        r = requests.get(url=body["next"])
        r.raise_for_status()
        body = r.json()


def process_slug(task_queue: mp.Queue, res_queue: mp.Queue, path: str) -> None:
    """
    End-to-end processing of the slug: downloading, saving to FS, putting to DB.
    Done this way instead of waterfall to not maintain a list/queue of all
    downloaded slugs simultaneously, as slugs are not that small.
    :task_queue: queue of slugs to process
    :res_queue: queue to output result per of processing per slug
    :path: configurable dir name in FS, slugs htmls will be stored there
    """

    # not the prettiest way but needed to insure correct number of statuses
    connected = True
    conn = None
    curs = None
    try:
        conn = psycopg2.connect(DSN)
        curs = conn.cursor()
    except Exception:
        connected = False

    while True:
        try:
            slug = task_queue.get_nowait()
            r = requests.get(url=BASE_URL + slug)
            if r.status_code != 200:
                res_queue.put((slug, SlugProcessStatus.DOWNLOAD_FAILED))
                continue

            body = r.json()
            body_parts = {}
            for key in SLUG_KEYS:
                body_parts[key] = body.get(key, None)

            if None in body_parts.values():
                res_queue.put((slug, SlugProcessStatus.SLUG_INCOMPLETE))
                continue

            if path is not None:
                with open(os.path.join(path, slug + ".html"), "w") as f:
                    f.write(body_parts["html"])

            if connected is False:
                res_queue.put((slug, SlugProcessStatus.FAILED_PUT_TO_DB))
                continue

            if insert_into_db(conn, curs, body_parts) is False:
                res_queue.put((slug, SlugProcessStatus.FAILED_PUT_TO_DB))
                continue

            res_queue.put((slug, SlugProcessStatus.OK))
        except queue.Empty:
            # meaning that task queue is exhausted
            break
        except OSError:
            res_queue.put((slug, SlugProcessStatus.FAILED_TO_WRITE_TO_FS))
        except Exception:
            res_queue.put((slug, SlugProcessStatus.EXCEPTION))

    # theoretically closing can raise as well
    try:
        if curs is not None:
            curs.close()
        if conn is not None:
            conn.close()
    except Exception:
        pass


def initial_db_cleanup() -> bool:
    """
    This function truncates the table on startup, so
    no additional cleanup is needed and script runs
    are kind of idempotent
    :returns: success status of the operation
    """
    logger = logging.getLogger(LOGGER_NAME)
    conn = None
    curs = None
    result = True
    try:
        conn = psycopg2.connect(DSN)
        curs = conn.cursor()
        curs.execute("TRUNCATE TABLE slugs;")
        conn.commit()
    except Exception as e:
        if conn is not None:
            conn.rollback()
        logger.debug(f"Failed to cleanup DB due to {e}")
        result = False

    # theoretically closing can raise as well
    try:
        if curs is not None:
            curs.close()
        if conn is not None:
            conn.close()
    except Exception as e:
        logger.debug(f"Failed to close connection/cursor due to {e}")
        result = False

    return result


def insert_into_db(
    conn: typing.Any, curs: typing.Any, body_parts: typing.Dict[str, str]
) -> bool:
    """
    Inserting slug into DB
    :conn: DB connection
    :curs: cursor
    :body_parts: dict with slug fields
    :returns: success status of operation
    """
    try:
        SQL = "INSERT INTO slugs (id, title, slug, url, locale, products, topics, summary) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);"
        data = (
            body_parts["id"],
            body_parts["title"],
            body_parts["slug"],
            body_parts["url"],
            body_parts["locale"],
            json.dumps(body_parts["products"]),
            json.dumps(body_parts["topics"]),
            # escaping for PostgreSQL (only this field requires it in fact)
            body_parts["summary"].replace("'", "''"),
        )
        curs.execute(SQL, data)
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False


def print_stats(stats: typing.Dict[SlugProcessStatus, int]) -> None:
    """
    Printing statistics
    :stats: statistics dictionary
    """
    logger = logging.getLogger(LOGGER_NAME)
    human_readable = {
        SlugProcessStatus.OK: "slug(s) were processed successfully.",
        SlugProcessStatus.DOWNLOAD_FAILED: "slug(s) failed to be downloaded.",
        SlugProcessStatus.SLUG_INCOMPLETE: "slug(s) were incomplete.",
        SlugProcessStatus.FAILED_PUT_TO_DB: "slug(s) failed to be put to DB.",
        SlugProcessStatus.FAILED_TO_WRITE_TO_FS: "slug(s) HTML file(s) failed to be written to FS.",
        SlugProcessStatus.EXCEPTION: "slug(s) - unknown exception occurred during processing.",
    }

    logger.info(f"Total number of {sum(stats.values())} slug(s) was processed:")
    for k, v in stats.items():
        if v > 0:
            logger.info(f"{v} " + human_readable[k])


@click.command()
@click.option(
    "--slugs",
    "-s",
    type=click.IntRange(
        1,
    ),
    default=50,
    help="Maximum number of slugs to download",
)
@click.option(
    "--path",
    "-p",
    type=click.Path(
        exists=True,
        file_okay=False,
        dir_okay=True,
        writable=True,
        readable=True,
        path_type=str,
    ),
    help="Path where html files should be written. (not specified - no files)",
)
@click.option(
    "--verbose", "-v", type=bool, is_flag=True, default=False, help="Verbose mode"
)
def main(slugs: click.IntRange, path: click.Path, verbose: bool) -> None:
    logging.basicConfig()
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    if verbose is True:
        logger.setLevel(logging.DEBUG)

    logger.debug(f"Script started with: slugs={slugs}, path={path}, verbose={verbose}")
    if initial_db_cleanup() is False:
        logger.info("Failed to cleanup DB, exiting...")
        return

    try:
        task_queue, tasks_size = download_slug_names(typing.cast(int, slugs))
    except Exception as exc:
        logger.error(f"Failed to download enough slug names due to: {exc}")
        return

    logger.info(f"{tasks_size} slugs are scheduled to be processed")

    res_queue: "mp.Queue[typing.Tuple[str, SlugProcessStatus]]" = mp.Queue(
        maxsize=tasks_size
    )
    processes = []
    for _ in range(mp.cpu_count()):
        p = mp.Process(target=process_slug, args=(task_queue, res_queue, path))
        p.start()
        processes.append(p)

    stats: "typing.Dict[SlugProcessStatus, int]" = {}
    # Slug processing designed the way, so on each slug single status report is
    # generated. Here we use that fact that we will receive `task_size` amount
    # of slugs precisely. Can be done another way: each producer can send a sentinel
    # message and once consumer receives them all it stops, but it is almost the
    # same way of doing it.
    for i in range(tasks_size):
        slug, status = res_queue.get()
        logger.debug(f"{i} slug {slug} processed with status: {status}")
        stats[status] = stats.get(status, 0) + 1

    print_stats(stats)

    for p in processes:
        p.join()


if __name__ == "__main__":
    main()
