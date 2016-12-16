# -*- coding: utf-8 -*-
from os import listdir
from os.path import isfile, join
import random
import datetime

def files_in_dir(directory):
    """
    :param directory: The directory
    :return: List of all files in directory
    """
    return [f for f in listdir(directory) if isfile(join(directory,f))]

def random_string(length):
    """
    :param length: Legnth of the returned string
    :return: String og random characters
    """
    chars = 'QAZWSXEDCRFVTGBYHNUJMKLP23456789'
    return ''.join([random.choice(chars) for i in range(length)])

def is_christmas():
    now = datetime.datetime.now()
    if now.month != 12:
        return False
    if now.day < 30 and now.day > 10:
        return True
    return False