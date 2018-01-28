def get_full_destination_path(language, destination_path):
    return "/{}/{}.html".format(language, destination_path)

class Entry:
    def __init__(self, entry_id, language, value_dict):
        self.id = entry_id
        self.title = value_dict["title"]
        self.language = language 
        self.subtitle = value_dict.get("subtitle", "")
        self.destination_path = get_full_destination_path(language, value_dict.get("destination_path", ""))
        self.authors = value_dict.get("authors", "")
        self.other_paths = {}

    def set_pubdate(self, pubdate, moddate, md5sum):
        self.pubdate = pubdate
        self.md5 = md5sum
        self.moddate = moddate

    def set_cross_language_link(self, language, path):
        self.other_paths[language] = path
