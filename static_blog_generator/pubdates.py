#! /usr/bin/env python3

import json, sys, datetime, csv, os
import hashlib

def get_source_filename(language, entry_id):
    return "src/{}/{}.html.source".format(language, entry_id)

class PubdateInfo:
    def __init__(self, language, entry_id, pubdate, md5="", moddate=""):
        self.language = language
        self.id = entry_id
        self.pubdate = pubdate
        self.md5 = md5
        self.moddate = moddate


def pubdate_from_json(information):
    lang = information["language"]
    entry_id = information["id"]
    pubdate = information["pubdate"]
    md5 = information["md5"]
    moddate = information.get("moddate", "")
    return PubdateInfo(lang, entry_id, pubdate, md5, moddate)


class Pubdates:
    def __init__(self):
        self.entries = {}
        self.current = 0

    def read_from_file(self):
        with open("pubdates.json") as data_file:
            for element in json.load(data_file):
                try:
                    entry = pubdate_from_json(element)
                    if entry.language in self.entries:
                        self.entries[entry.language].append(entry)
                    else:
                        self.entries[entry.language] = [entry]
                except KeyError as e:
                    sys.stderr.write("Failed to load pubdate/moddate information of an entry.")

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
        pubdate = datetime.date.today()
        self.entries[lang].append(PubdateInfo(lang, entry_id, pubdate.strftime("%Y-%m-%d")))

    def get_and_set_pubdate(self, entry_id, lang):
        """
        Legacy, might not work any more.
        """
        pubdate = datetime.date.today()
        for entry in self.entries:
            if entry["id"] == entry_id and entry["language"] == lang and ("pubdate" in entry):
                pubdate = datetime.datetime.strptime(entry["pubdate"], "%Y-%m-%d")
                return pubdate.strftime("%Y-%m-%d")
        # Entry not found, let's create it.
        entry = {"id": id, "language": lang, "pubdate": pubdate.strftime("%Y-%m-%d")}
        self.entries.append(entry)
        return pubdate.strftime("%Y-%m-%d")
#        raise KeyError("""Could not find entry with id == "%s" and lang == "%s" to get/set pubdate.\n""" % (id, lang))

    def set_moddate_if_missing(self, lang, entry_id):
        entry = self.get_entry(lang, entry_id)
        hash_md5 = hashlib.md5()
        with open(get_source_filename(lang, entry_id), "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        md5sum = hash_md5.hexdigest()
        if entry.md5 != "" and entry.md5 != md5sum:
            entry.md5 = md5sum
            entry.moddate = datetime.date.today().strftime("%Y-%m-%d")

    def get_and_set_moddate(self, id, lang):
        """
        Legacy, might not work any more.
        """
        hash_md5 = hashlib.md5()
        with open(get_source_filename(lang, id), "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        md5sum = hash_md5.hexdigest()
        for entry in self.entries:
            if entry["id"] == id and entry["language"] == lang and ("md5" in entry):
                if entry["md5"] != md5sum:
                    entry["md5"] = md5sum
                    entry["moddate"] = datetime.date.today().strftime("%Y-%m-%d")
                if "moddate" in entry:
                    return entry["moddate"]
                else:
                    return ""
            elif entry["id"] == id and entry["language"] == lang and ("md5" not in entry):
                entry["md5"] = md5sum
                return ""
        raise KeyError("""Could not find entry with id == "%s" and lang == "%s" to get/set moddate.\n""" % (id, lang))

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
            json.dump(outlist, fp, indent=2)
