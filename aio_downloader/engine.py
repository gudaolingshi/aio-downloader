# -*- coding:utf-8 -*-

import sys
import os
import json
import logging
import asyncio

from functools import partial
from argparse import ArgumentParser

from .sources import *
from .downloader import DownloadWrapper
from .utils import load_function, ArgparseHelper, find_source, get_filename, get_logger


class AsyncEngine(object):
    """
    异步多协程引擎
    """

    def __init__(self):
        super(AsyncEngine, self).__init__()
        self.sources = [globals()[k] for k in globals() if k.endswith("Source")]
        args = self.parse_args()
        self.idle = getattr(args, "idle", False)
        self.workers = args.workers
        self.source = globals()[args.source.capitalize() + "Source"](**vars(args))
        self.downfilepath = args.output_dir
        self.generator = self.gen_task(self.source)
        self.download = DownloadWrapper()
        self.logger = get_logger(__name__)

    def parse_args(self):
        base_parser = ArgumentParser(
            description=self.__class__.__doc__, add_help=False)
        base_parser.add_argument(
            "-w", "--workers", default=16, type=int, help="Worker count. Default 16")
        base_parser.add_argument(
            "-o", "--output_dir", default=".", help="Set output directory. Default current directory")
        parser = ArgumentParser(description="Async downloader", add_help=False)
        parser.add_argument('-h', '--help', action=ArgparseHelper,
                            help='show this help message and exit. ')
        sub_parsers = parser.add_subparsers(dest="source", help="Source. ")
        for source in self.sources:
            sub_parser = sub_parsers.add_parser(
                source.__name__.replace("Source", "").lower(),
                parents=[base_parser], help=source.__doc__)
            source.enrich_parser(sub_parser)
        if len(sys.argv) < 2:
            parser.print_help()
            exit(1)
        return parser.parse_args()

    def start(self):
        loop = asyncio.get_event_loop()
        task = loop.create_task(self.process(loop))
        try:
            loop.run_until_complete(task)
        except KeyboardInterrupt:
            self.logger.info("Wait to close...")
            # 发送一个False，使用异步生成器跳出循环
            stop_task = loop.create_task(self.generator.asend(False))
            loop.run_until_complete(asyncio.gather(task, stop_task))
            loop.close()

    @staticmethod
    async def gen_task(source):
        # 预激专用，预激操作不返回有用的数据。
        yield
        async with source as iterable:
            async for data in iterable:
                # data可能是None,也可能是" ":
                if not (yield data and data.strip() and json.loads(data)):
                    break
        # 关闭时走到这，返回None
        yield
        yield "exit"

    async def process(self, loop):
        self.logger.info("Start process tasks. ")
        # 预激
        await self.generator.asend(None)
        free_workers, tasks, alive, got_task = self.workers, [], True, False
        # 当没有关闭或者有任务时，会继续循环
        while alive or tasks:
            # 当任务未满且未关闭时，才会继续产生新任务
            while free_workers > 0 and alive:
                data = await self.generator.asend(True)
                # 返回exit表示要退出了
                if data == "exit":
                    got_task = False
                    alive = False
                # 有data证明有下载任务
                elif data:
                    free_workers -= 1
                    # 如果没有filename,自动补充
                    if not data.get('filename',None):
                        filename = await get_filename(data.get('url'))
                    else:
                        filename = data.get('filename')
                    data.update({'filename': os.path.join(self.downfilepath, filename)})
                    self.logger.debug(f"Start task {data['filename']}.")
                    tasks.append(loop.create_task(self.download(**data)))
                    got_task = True
                # 否则休息一秒钟
                else:
                    got_task = False
                    if not self.idle:
                        break
                    self.logger.debug("Haven't got tasks. ")
                    await asyncio.sleep(1)
            # 清除完成的任务
            task_index = len(tasks) - 1
            while task_index >= 0:
                if tasks[task_index].done():
                    # 默认成功没有返回值，否则为失败，退回source
                    rs = tasks.pop(task_index).result()
                    if rs:
                        self.logger.info(f"Push back {rs}. ")
                        await self.source.push_back(rs)
                    free_workers += 1
                task_index -= 1
            # 任务队列是满的，休息一秒钟
            if not free_workers:
                await asyncio.sleep(1)
            # 用来减缓任务队列有但不满且要关闭时产生的大量循环。
            await asyncio.sleep(.1)
            # 如果没有任务且不允许空转且上一次循环未发现任务，则停止程序。
            if not (tasks or self.idle or got_task):
                alive = False
        self.logger.info("Process stopped. ")
        await self.generator.aclose()


def main():
    globals().update(find_source() or {})
    AsyncEngine().start()


if __name__ == "__main__":
    main()