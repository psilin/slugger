import enum
import logging
import multiprocessing as mp
import os
import typing

import click
import requests

BASE_URL = "https://support.allizom.org/api/1/kb/"


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
    logger: logging.Logger,
) -> mp.Queue:
    """
    Downloading slug names. Decided to not parallelise it as it will take
    small piece of overall execution time anyway. And relatively small for
    maximum possible number of slugs anyway.
    :slug_number: number of slugs to download
    :logger: logger to log info
    :returns: queue with all slugs to download (again there not much of them
    so it is ok)
    """
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
            logger.debug(f"Added slug {res['slug']} to task queue.")
            task_queue.put(res["slug"])
            cnt += 1
            if cnt == slug_number:
                return task_queue

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
    while not task_queue.empty():
        try:
            slug = task_queue.get()
            r = requests.get(url=BASE_URL + slug)
            if r.status_code != 200:
                res_queue.put((slug, SlugProcessStatus.DOWNLOAD_FAILED))
                continue

            body = r.json()
            body_parts = {}
            for key in (
                "id",
                "title",
                "slug",
                "url",
                "locale",
                "products",
                "topics",
                "summary",
                "html",
            ):
                body_parts[key] = body.get(key, None)

            if None in body_parts.values():
                res_queue.put((slug, SlugProcessStatus.SLUG_INCOMPLETE))
                continue

            with open(os.path.join(path, slug + ".html"), "w") as f:
                f.write(body_parts["html"])

            # need to put here to DB

            res_queue.put((slug, SlugProcessStatus.OK))

        except OSError:
            res_queue.put((slug, SlugProcessStatus.FAILED_TO_WRITE_TO_FS))
        except Exception as e:
            res_queue.put((slug, SlugProcessStatus.EXCEPTION))


@click.command()
@click.option(
    "--slugs",
    "-s",
    type=click.IntRange(
        1,
    ),
    default=50,
    help="Maximum number of slugs to downloads",
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
    help="Path where html files should be written.",
)
@click.option(
    "--verbose", "-v", type=bool, is_flag=True, default=False, help="Verbose mode"
)
def main(slugs: click.IntRange, path: click.Path, verbose: bool) -> None:
    logging.basicConfig()
    logger = logging.getLogger("Slug Downloader")
    logger.setLevel(logging.INFO)
    if verbose is True:
        logger.setLevel(logging.DEBUG)

    logger.debug(f"Script started with: slugs={slugs}, path={path}, verbose={verbose}")

    try:
        task_queue = download_slug_names(typing.cast(int, slugs), logger)
    except Exception as exc:
        logger.error(f"Failed to download enough slug names due to: {exc}")

    tasks_size = task_queue.qsize()
    logger.info(f"{tasks_size} slugs are scheduled to be processed")

    res_queue: "mp.Queue[typing.Tuple[str, SlugProcessStatus]]" = mp.Queue(
        maxsize=task_queue.qsize()
    )
    processes = []
    for _ in range(mp.cpu_count()):
        p = mp.Process(target=process_slug, args=(task_queue, res_queue, path))
        p.start()
        processes.append(p)

    # Slug processing designed the way, so on each slug single status report is
    # generated. Here we use that fact that we will receive `task_size` amount
    # of slugs precisely.
    for _ in range(tasks_size):
        slug, status = res_queue.get()
        logger.debug(f"Slug {slug} processed with status: {status}")

    for p in processes:
        p.join()


if __name__ == "__main__":
    main()