"""
Contains utilities to help maintain safe naming conventions when creating files and folders.
"""
import re


def replace_forward_slash(file_name):
    """
    This method takes a string representing a file name and replaces forward slashes with ":"
    This approach is consistent with how other clients deal with attempts to upload files with forward slashes
    in the name.
    """

    return file_name.replace("/", ":")


def contains_special_characters(name):
    """
    https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-keys.html
    :param name: string evaluating special characters
    :return: True if string has special characters, False otherwise
    """
    regex = re.compile('[\[\]@_!#$%^&*()\\\<>?/\|}{~:]')

    if regex.search(name) is None:
        return False
    else:
        return True
