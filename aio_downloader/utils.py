# -*- coding:utf-8 -*-

import os
import sys
import re

import logging
from functools import wraps
from argparse import Action, _SubParsersAction

import aiohttp
import asyncio
from urllib import parse

fake_headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',  # noqa
    'Accept-Charset': 'UTF-8,*;q=0.5',
    'Accept-Encoding': 'gzip,deflate,sdch',
    'Accept-Language': 'en-US,en;q=0.8',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.74 Safari/537.36 Edg/79.0.309.43',  # noqa
}


class ArgparseHelper(Action):
    """
        显示格式友好的帮助信息
    """

    def __init__(self,
                 option_strings,
                 dest="",
                 default="",
                 help=None):
        super(ArgparseHelper, self).__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        parser.print_help()
        subparsers_actions = [
            action for action in parser._actions
            if isinstance(action, _SubParsersAction)]
        for subparsers_action in subparsers_actions:
            for choice, subparser in subparsers_action.choices.items():
                print("Command '{}'".format(choice))
                print(subparser.format_usage())

        parser.exit()


def load_function(function_str):
    """
    返回字符串表示的函数对象
    :param function_str: module1.module2.function
    :return: function
    """
    if not function_str:
        return
    mod_str, _sep, function_str = function_str.rpartition('.')
    return getattr(__import__(
        mod_str, fromlist=mod_str.split(".")[-1]), function_str)


async def readexactly(steam, n):
    if steam._exception is not None:
        raise steam._exception

    blocks = []
    while n > 0:
        block = await steam.read(n)
        if not block:
            break
        blocks.append(block)
        n -= len(block)

    return b''.join(blocks)


def find_source():
    sys.path.insert(0, os.getcwd())
    try:
        source = __import__("sources")
        sources = dict()
        for k in dir(source):
            if k.endswith("Source") and k != "Source":
                sources[k] = getattr(source, k)
        return sources
    except ImportError:
        pass


async def get_filename(url):
    """
    extract filename from url
    """
    if not url:
        return None
    url_trunk = url.split('?')[0]  # strip query string
    filename = parse.unquote(url_trunk.split('/')[-1]) or \
               parse.unquote(url_trunk.split('/')[-2])
    all_exts = {'3gp','flv','mp4','ts','mov','webm',
                'asf','mp3','wav','jpg','png','gif','pdf'}
    if filename and any([1 for _ in all_exts if filename.endswith(_)]):
        return filename
    if filename:
        type, ext, size = await url_info(url)
        if ext: filename = f'{filename}.{ext}'
        return filename
    return url


def r1(pattern, text):
    m = re.search(pattern, text)
    if m:
        return m.group(1)


async def url_info(url):
    """
    Get target url content-type, file_size and file_extension
    """
    header = fake_headers.copy()
    header['Range'] = 'bytes=0-'
    response = await request_with_retry(url, headers=header, timeout=10)
    headers = response.headers
    # Get type of target file:
    type = headers.get('content-type')
    if type == 'image/jpg; charset=UTF-8' or type == 'image/jpg':
        type = 'audio/mpeg'  # fix for netease
    mapping = {
        'video/3gpp': '3gp',
        'video/f4v': 'flv',
        'video/mp4': 'mp4',
        'video/MP2T': 'ts',
        'video/quicktime': 'mov',
        'video/webm': 'webm',
        'video/x-flv': 'flv',
        'video/x-ms-asf': 'asf',
        'audio/mp4': 'mp4',
        'audio/mpeg': 'mp3',
        'audio/wav': 'wav',
        'audio/x-wav': 'wav',
        'audio/wave': 'wav',
        'image/jpeg': 'jpg',
        'image/png': 'png',
        'image/gif': 'gif',
        'application/pdf': 'pdf',
    }
    if type in mapping:
        ext = mapping[type]
    else:
        type = None
        # Check if filepath exist or not
        if headers.get('content-disposition'):
            try:
                filename = parse.unquote(
                    r1(r'filename="?([^"]+)"?', headers.get('content-disposition'))
                )
                if len(filename.split('.')) > 1:
                    ext = filename.split('.')[-1]
                else:
                    ext = None
            except:
                ext = None
        else:
            ext = None
    if headers.get('transfer-encoding') != 'chunked':
        size = headers.get('Content-Range') and \
            int(re.search(r'/(\d+)', headers.get('Content-Range')).group(1))
    else:
        size = None
    # print(f"type, ext, size are: {type}, {ext}, {size}")
    return type, ext, size


async def request_with_retry(*args, **kwargs):
    """
    Request the tartget url with max_retry
    """
    retry_time = 3
    for i in range(retry_time):
        try:
            session = aiohttp.ClientSession()
            response = await session.get(*args, **kwargs)
            await session.close()
            # print(response.headers)
            return response
        except Exception as e:
            await session.close()
            if i + 1 == retry_time:
                raise e


def get_logger(logger_name):
    """得到日志对象"""
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('[ %(asctime)s ] - %(levelname)s - %(message)s')
    # formatter = logging.Formatter('[ %(asctime)s ]-(%(funcName)s:%(lineno)s)-%(levelname)s - %(message)s')
    if not logger.handlers:
        # 用于输出至屏幕
        screen_handler = logging.StreamHandler(sys.stdout)
        screen_handler.setFormatter(formatter)
        # logger绑定处理对象
        logger.addHandler(screen_handler)  # message logging to screen
    return logger


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    # url = 'http://npm.taobao.org/mirrors/python/3.8.6/Python-3.8.6.tgz'
    # url = "http://clips.vorwaerts-gmbh.de/big_buck_bunny.mp4"
    url = "http://183.230.74.182/wxsv.qpic.cn/0bf264etgaajhqag2vvwvbpvn56dgp3qsmya.f103000.mp4?dis_k=942f75033d64de8f96788812ec3b5153&dis_t=1606461681&cip=183.228.101.66&mkey=4df4fd5f1c58e4a55fb0907135dcb0cf&arrive_key=658569043864"
    a = get_filename(url)
    loop.run_until_complete(a)