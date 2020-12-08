# -*- coding:utf-8 -*-

import os
import re
import json
import aiohttp
import aiofiles
import asyncio
import traceback

from .utils import readexactly
from .utils import get_logger
from .utils import fake_headers


class DownloadWrapper(object):

    async def __call__(self, *args, **kwargs):
        self.downloader = AsyncDownloader()
        return await self.downloader.run(*args, **kwargs)
        

class AsyncDownloader(object):
    """
    支持断点续传
    """
    def __init__(self, conn_timeout=10, read_timeout=1800):
        self.session = aiohttp.ClientSession(
            conn_timeout=conn_timeout, read_timeout=read_timeout)
        self.failed_times_max = 3
        self.tries = 0
        self.logger = get_logger(__name__)

    async def run(self, url, filename, failed_times=0):
        # 失败次数超过上限,直接放弃
        if failed_times > self.failed_times_max:
            self.logger.error(
                f"Abandon {filename} of {url} failed for {failed_times} times.")
            await self.close()
            return
        # 如果filename存在,表示下载完成,直接返回
        if os.path.exists(filename):
            self.logger.info(f"Abandon {filename} for download completed.")
            await self.close()
            return
        received, total= 0, 0
        # 判断文件夹是否存在,不存在就创建
        if not os.path.exists(os.path.dirname(filename)):
            os.mkdir(os.path.dirname(filename))
        # 判断临时文件是否存在,如果存在更新received
        tmp_file = filename + '.download'
        if os.path.exists(tmp_file):
            received = os.path.getsize(tmp_file)
        # 获取URL对应的file大小,如果获取失败,说明url访问失败
        total = await self.get_url_file_size(url)
        if total is None:
            self.logger.error(f"Abandon {filename} for getting urlsize failed.")
            await self.close()
            return
        # 正式尝试下载文件
        headers = fake_headers.copy()
        self.logger.debug(f"Downloading {filename} now! got {received} bytes.")
        while self.tries < 2:
            try:
                # 每一次重新请求,都需要更新Range
                headers["Range"] = f"bytes={received}-"
                resp = None
                resp = await self.session.get(url, headers=headers)
                if resp.status < 300:
                    # 开始写入文件
                    async with aiofiles.open(tmp_file, 'ab') as f:
                        chunk = await readexactly(resp.content, 1024 * 1000)
                        while chunk:
                            received += len(chunk)
                            self.logger.debug(
                                f"Download {filename}: {len(chunk)} from {url}"
                                f", processing {round(received/total, 2)}.")
                            await f.write(chunk)
                            chunk = await readexactly(resp.content, 1024 * 1000)
                        self.logger.info(f"{filename} download finished. ")
                        break
                else:
                    raise RuntimeError(f"Haven't got any data from {url}.")
            # ClientPayloadError不算计入失败数
            except aiohttp.client_exceptions.ClientPayloadError:
                self.logger.error(f"{filename} download error, try to continue.")
                await asyncio.sleep(2)  # if first request failed, sleep some secods
            except Exception as e:
                self.logger.error(f"{filename} got Error: {e}")
                self.tries += 1
                await asyncio.sleep(2)  # if first request failed, sleep some secods
            finally:
                resp and resp.close()
                # pass
        # 检测下载的文件存在与否,大小如何?;进一步判断下载是否正常结束
        if not os.path.exists(tmp_file) or os.path.getsize(tmp_file) != total:
            failed_times += 1
            self.logger.error(
                f"{filename} of {url} failed for {failed_times} times.")
            await self.close()
            return json.dumps(
                {"url": url, "filename": filename, "failed_times": failed_times})
        # 下载成功了
        else:
            # 重命名文件
            os.rename(tmp_file, filename)
            await self.close()

    async def get_url_file_size(self, url):
        """
        Requests target url, parse the video/iamge file size.
        If request failed, process will try again.
        """
        while self.tries < 2:
            try:
                headers = fake_headers.copy()
                headers['Range'] = 'bytes=0-4' # Only get headers
                resp = await self.session.get(url, headers=headers)
                content_range = resp.headers.get('Content-Range')
                if not content_range:
                    raise Exception("Content-Range is empty!!")
                file_size = int(re.search(r'/(\d+)', content_range).group(1))
                return file_size if file_size else 0
            except Exception as e:
                self.logger.error(f"Failed to get url filesize: {e}\n URL is {url}")
                self.tries += 1
                await asyncio.sleep(2)
        # If request failed twice, return None!
        else:
            return None

    async def close(self):
        await self.session.close()