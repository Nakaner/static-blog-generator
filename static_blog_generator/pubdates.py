#! /usr/bin/env python3

import json, sys, datetime, os, re
import hashlib
from static_blog_generator.entry_writer import EntryWriter

class PubdateInfo:
    def __init__(self, language, entry_id, pubdate, md5="", moddate=None):
        self.language = language
        self.id = entry_id
        self.pubdate = pubdate
        self.md5 = md5
        self.moddate = moddate


def pubdate_from_json(information):
    lang = information["language"]
    entry_id = information["id"]
    pubdate_str = information["pubdate"]
    if pubdate_str.endswith("Z"):
        pubdate = datetime.datetime.strptime(pubdate_str, "%Y-%m-%dT%H:%M:%SZ")
    else:
        pubdate = datetime.datetime.strptime(pubdate_str, "%Y-%m-%dT%H:%M:%S%z")
    md5 = information.get("md5", "")
    moddate_str = information.get("moddate", "")
    if moddate_str is None or moddate_str == "":
        moddate = None
    elif moddate_str.endswith("Z"):
        moddate = datetime.datetime.strptime(moddate_str, "%Y-%m-%dT%H:%M:%SZ")
    elif re.search("\+[0-9]{4}$", moddate_str) is not None:
        moddate = datetime.datetime.strptime(moddate_str, "%Y-%m-%dT%H:%M:%S%z")
    else:
        raise RuntimeError("Could not parse moddate string '{}'".format(moddate_str))
    return PubdateInfo(lang, entry_id, pubdate, md5, moddate)

def time_serialize(obj):
    if isinstance(obj, datetime.datetime):
        return obj.strftime("%Y-%m-%dT%H:%M:%S%z")
    raise TypeError("Type {} not serializable".format(type(obj)))

class Pubdates:
    def __init__(self, entry_writer):
        self.entry_writer = entry_writer
        self.entries = {}
        self.current = 0

    def read_from_file(self):
        with open("pubdates.json") as data_file:
            for element in json.load(data_file):
                entry = pubdate_from_json(element)
                if entry.language in self.entries:
                    self.entries[entry.language].append(entry)
                else:
                    self.entries[entry.language] = [entry]

    def __iter__(self):
        return self

    def __next__(self):
        if self.current >= len(self.entries):
            raise StopIteration
        else:
            self.current += 1
            return self.entries[self.current - 1]

    def get_entry(self, lang, entry_id, return_none_if_error=False):
        for lang_entry in self.entries[lang]:
            if lang_entry.id == entry_id:
                return lang_entry
        if return_none_if_error:
            return None
        raise KeyError("{} of language {} not found.".format(entry_id, lang))

    def set_pubdate_if_missing(self, lang, entry_id):
        if self.get_entry(lang, entry_id, True) is not None:
            return
        pubdate = datetime.datetime.utcnow()
        self.entries[lang].append(PubdateInfo(lang, entry_id, pubdate))

    def set_moddate_if_missing(self, lang, entry_id):
        entry = self.get_entry(lang, entry_id)
        hash_md5 = hashlib.md5()
        with open(self.entry_writer.get_source_filename(lang, entry_id), "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        md5sum = hash_md5.hexdigest()
        if entry.md5 != "" and entry.md5 != md5sum:
            entry.moddate = datetime.datetime.utcnow()
        entry.md5 = md5sum

    def write_to_file(self, filename):
        outlist = []
        for lang in self.entries:
            for entry in self.entries[lang]:
                obj = {}
                obj["language"] = entry.language
                obj["id"] = entry.id
                obj["pubdate"] = entry.pubdate
                obj["md5"] = entry.md5
                obj["moddate"] = entry.moddate
                outlist.append(obj)
        with open(filename, 'w') as fp:
            json.dump(outlist, fp, indent=2, default=time_serialize)
