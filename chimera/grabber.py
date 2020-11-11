"""file download with aiohttp"""
import asyncio
import aiohttp
from tqdm import tqdm
from itertools import islice

def fetch(urls, file_names, task=None):
    """grabs a list of files
    Task is for api mode, callback to write downloaded bytes
    """

    loop = asyncio.new_event_loop()
    return loop.run_until_complete(wrapper(urls, file_names, _fetch_all, task=task))

async def wrapper(urls, file_names, func, task=None):
    async with aiohttp.ClientSession() as session:
        return await func(session, urls, file_names, task=task)

async def _fetch_all(session, urls, file_names, task=None):
    tasks = []
    bar = None
    if task == None:
        bar = tqdm(total=100, unit_scale=True, unit='B')
    for url, file_name in zip(urls, file_names):
        tasks.append(
            asyncio.create_task(_fetch(session, url, file_name, callback=bar if bar else None, task=task)))
    ts_files = await asyncio.gather(*tasks)
    if task == None:
        bar.close()
    return ts_files


async def _fetch(session, url, file_name, chunk_size=2048, callback=None, task=None):
    async with session.get(url) as response:
        with open(file_name, 'wb') as stream:
            while True:
                chunk = await response.content.read(chunk_size)
                if not chunk:
                    break
                stream.write(chunk)
                if callback is not None:
                    callback.update(chunk_size)
                if task is not None:
                    task.downloaded += chunk_size

        return file_name


async def _fetch_limit(url, file_name, chunk_size=2048, callback=None):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            with open(file_name, 'wb') as stream:
                while True:
                    chunk = await response.content.read(chunk_size)
                    if not chunk:
                        break
                    stream.write(chunk)
                    if callback is not None:
                        callback.update(chunk_size)

            return file_name



async def _wrapper(tasks):
    for res in limited_as_completed(tasks, 20):
        print('Finished: {}'.format(await res))


def fetch_list(urls, file_names):
    bar = tqdm(total=100, unit_scale=True, unit='B')
    coros = (_fetch_limit(url, file_name, callback=bar) for url, file_name in zip(urls, file_names))
    loop = asyncio.new_event_loop()
    loop.run_until_complete(_wrapper(coros))
    loop.close()
    # loop.run_until_complete(wrapper(urls, file_names, _fetch_all))

def fetch_snd(size, streams):
    """grabs a soundcloud go+ track"""
    bar = tqdm(total=size, unit_scale=True, unit='MB')
    coros = (fetch_snd_stream(stream) for stream in streams)
    loop = asyncio.new_event_loop()
    loop.run_until_complete(_wrapper_snd(coros))
    loop.close()
    return streams

async def _wrapper_snd(coros):
    for res in limited_as_completed(coros, 20):
        await res

async def fetch_snd_stream(stream):
    async with aiohttp.ClientSession() as session:
        async with session.get(stream.url) as response:
            while True:
                chunk = await response.content.read(2048)
                if not chunk:
                    break
                stream.write(chunk)


# https://github.com/andybalaam/asyncioplus/blob/master/example.py
def limited_as_completed(coros, limit):
    """
    Run the coroutines (or futures) supplied in the
    iterable coros, ensuring that there are at most
    limit coroutines running at any time.
    Return an iterator whose values, when waited for,
    are Future instances containing the results of
    the coroutines.
    Results may be provided in any order, as they
    become available.
    """
    futures = [
        asyncio.ensure_future(c)
        for c in islice(coros, 0, limit)
    ]

    async def first_to_finish():
        while True:
            await asyncio.sleep(0)
            for f in futures:
                if f.done():
                    futures.remove(f)
                    try:
                        newf = next(coros)
                        futures.append(
                            asyncio.ensure_future(newf))
                    except StopIteration as e:
                        pass
                    return f.result()
    while len(futures) > 0:
        yield first_to_finish()