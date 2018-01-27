from static_blog_generator.entry import Entry

class EntryCollection:
    """
    Collection of all entries of one langage
    """
    def __init__(self, language):
        self.entries = []
        self.language = language

    def by_id(self, entry_id, throw_exception=True):
        for entry in self.entries:
            if entry.id == entry_id:
                return entry
        if throw_exception:
            raise KeyError("No entry found with ID {} and language {}".format(entry_id, self.language))
        return None

    def init_from_json(self, payload):
        """
        Populate this instance with the configuration of a blog.

        Args:
            payload (list) : list returned by json.load(config_file_pointer)
        """
        for entry in payload:
            entry_id = entry["id"]
            for lang in entry["languages"]:
                if lang != self.language:
                    continue
                if "title" not in entry["languages"][lang]:
                    raise Exception("Entry {} has no title for language {}, skipping.".format(entry_id, lang))
                new_entry = Entry(entry_id, lang, entry["languages"][lang])
                self.entries.append(new_entry)

    def add_pubdate_moddate_information(self, info):
        for lang in info.entries:
            if lang != self.language:
                continue
            for e in info.entries[lang]:
                # get entry from our internal list
                try:
                    this_entry = self.by_id(e.id)
                    this_entry.set_pubdate(e.pubdate, e.moddate, e.md5)
                except KeyError as err:
                    sys.stderr.write("Pubdate file contains an entry with ID {} which does not exist.".format(e.id))

    def sort_by_date(self, reverse=False):
        self.entries = self.by_date(False)

    def by_date(self, reverse=False):
        return sorted(self.entries, key=lambda e: e.pubdate, reverse=reverse)

    def get_latest(self):
        return self.by_date(True)[:3]

    def add_cross_language_links(self, other_collection):
        for entry in other_collection.entries:
            this_lang_entry = self.by_id(entry.id, False)
            if this_lang_entry is None:
                continue
            this_lang_entry.set_cross_language_link(entry.language, entry.destination_path)

    def size(self):
        return len(self.entries)

    def at(self, index):
        return self.entries[index]

    def save_pubdates(self, pubdates):
        for e in self.entries:
            pubdate_info = pubdates.get_entry(e.language, e.id, True)
            pubdate_info.pubdate = e.pubdate
            pubdate_info.moddate = e.moddate
            pubdate_info.md5 = e.md5
