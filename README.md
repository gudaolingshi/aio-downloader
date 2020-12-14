# Aio-Downloaer
---
Aio-downloader is small async downloader with muti-coroutine. With this downloader you downlaod videos, audios, images from the web. Now this aio-downloader offers three ways to download media:

- download videos with cmdline
- download videos with getting task data from redis
- download videos with getting task data from a jsonfile

Here is a little example to download a video like `http://vjs.zencdn.net/v/oceans.mp4`:

```shell
$ aio-downloader cmdline --url http://clips.vorwaerts-gmbh.de/big_buck_bunny.mp4
[ 2020-12-09 14:21:14,578 ] - INFO - Start process tasks. 
[ 2020-12-09 14:21:14,578 ] - DEBUG - Start task ./big_buck_bunny.mp4.
[ 2020-12-09 14:21:16,760 ] - DEBUG - Downloading ./big_buck_bunny.mp4 now! got 0 bytes.
[ 2020-12-09 14:21:24,679 ] - DEBUG - Download ./big_buck_bunny.mp4: 1024000 from http://clips.vorwaerts-gmbh.de/big_buck_bunny.mp4, processing 0.19.
[ 2020-12-09 14:21:28,729 ] - DEBUG - Download ./big_buck_bunny.mp4: 1024000 from http://clips.vorwaerts-gmbh.de/big_buck_bunny.mp4, processing 0.37.
[ 2020-12-09 14:21:30,554 ] - DEBUG - Download ./big_buck_bunny.mp4: 1024000 from http://clips.vorwaerts-gmbh.de/big_buck_bunny.mp4, processing 0.56.
[ 2020-12-09 14:21:32,456 ] - DEBUG - Download ./big_buck_bunny.mp4: 1024000 from http://clips.vorwaerts-gmbh.de/big_buck_bunny.mp4, processing 0.74.
[ 2020-12-09 14:21:34,045 ] - DEBUG - Download ./big_buck_bunny.mp4: 1024000 from http://clips.vorwaerts-gmbh.de/big_buck_bunny.mp4, processing 0.93.
[ 2020-12-09 14:21:34,593 ] - DEBUG - Download ./big_buck_bunny.mp4: 390872 from http://clips.vorwaerts-gmbh.de/big_buck_bunny.mp4, processing 1.0.
[ 2020-12-09 14:21:34,594 ] - INFO - ./big_buck_bunny.mp4 download finished. 
[ 2020-12-09 14:21:34,728 ] - INFO - Process stopped. 
```

## **Installation**

The following dependencies are necessary:

- **[Python](https://www.python.org/downloads/)**  3.6 or above
- aiohttp
- aiofiles

### Install via pip

The official release of `aio-downloader` is distributed on [PyPI](https://pypi.python.org/pypi/you-get), and can be installed easily from a PyPI mirror via the [pip](https://en.wikipedia.org/wiki/Pip_(package_manager)) package manager. Note that you must use the Python 3 version of `pip`:

```shell
pip3 install aio-downloader
```

## **Getting Started**

### Download videos by cmdline

Usage: `aio-downloader cmdline --url videos_link [-o filedir] [--filename name]`

```shell
optional arguments:
  -h, --help            show this help message and exit
  -w WORKERS, --workers WORKERS
                        Worker count. Default 16
  -o OUTPUT_DIR, --output_dir OUTPUT_DIR
                        Set output directory. Default current directory
  --filename FILENAME   Filename to save file.
  --url URL             Download url.
```

### Download videos by redis

The aio-downloader will get video links from redis, and download these links at the same time with 16 coroutines defaultly. If you don’t set redis parameters like host, port, db..., the script will get default value.

Usage: `aio-downloader redis`

PS: links should be json like `{"url": "http://vjs.zencdn.net/v/oceans.mp4"}` stored in redis list(default key: `download_meta`)

```shell
optional arguments:
  -h, --help            show this help message and exit
  -w WORKERS, --workers WORKERS
                        Worker count. Default 16
  -o OUTPUT_DIR, --output_dir OUTPUT_DIR
                        Set output directory. Default current directory
  -rh REDIS_HOST, --redis-host REDIS_HOST
                        Default 127.0.0.1
  -rp REDIS_PORT, --redis-port REDIS_PORT
                        Default 6379
  -rd REDIS_DB, --redis-db REDIS_DB
                        Default 0
  -rk REDIS_KEY, --redis-key REDIS_KEY
                        Default `download_meta`
  --idle                Idle...
```

### Download videos by file

Do not want to use redis? aio-downloader also offer file way to store videos links, file should be json like:

```json
{"url": "http://clips.vorwaerts-gmbh.de/big_buck_bunny.mp4"}
{"url": "http://vjs.zencdn.net/v/oceans.mp4"}
{"url": "http://mirror.aarnet.edu.au/pub/TED-talks/911Mothers_2010W-480p.mp4"}
```

Usage: `aio-downloader file --path video_task.json  `

```shell
optional arguments:
  -h, --help            show this help message and exit
  -w WORKERS, --workers WORKERS
                        Worker count. Default 16
  -o OUTPUT_DIR, --output_dir OUTPUT_DIR
                        Set output directory. Default current directory
  --path PATH           Path of file which store download meta in json lines.
```
