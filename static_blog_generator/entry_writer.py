#! /usr/bin/env python3

import sys, os, datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape
from werkzeug.contrib.atom import AtomFeed
from static_blog_generator.entry import Entry
from static_blog_generator.entry_collection import EntryCollection

def en_timestamp(timestamp):
    return timestamp.strftime("%Y-%m-%d")

def de_timestamp(timestamp):
    return timestamp.strftime("%d.%m.%Y")

class EntryWriter:
    def __init__(self, template_searchpath, source_directory, output_directory):
        self.env = Environment(
            loader=FileSystemLoader(searchpath=template_searchpath),
            trim_blocks=True,
            autoescape=select_autoescape(enabled_extensions=(), default_for_string=True, default=False)
        )
        self.env.filters["de_timestamp"] = de_timestamp
        self.env.filters["en_timestamp"] = en_timestamp
        self.output_directory = output_directory
        self.source_directory = source_directory
        self.create_directories()

    def create_directories(self):
        os.makedirs(self.output_directory, exist_ok=True)
        os.makedirs("{}/de".format(self.output_directory), exist_ok=True)
        os.makedirs("{}/en".format(self.output_directory), exist_ok=True)
        os.makedirs("{}/overview".format(self.output_directory), exist_ok=True)

    def get_overview_destination_path(self, language, page_number):
        if page_number > 1:
            return "{}/overview/blog-{}_{}.html".format(self.output_directory, language, str(page_number))
        return "{}/overview/blog-{}.html".format(self.output_directory, language)

    def get_source_filename(self, language, entry_id):
        return "src/{}/{}.html.source".format(language, entry_id)

    
    def write_overview_pages(self, entries, template_filename, latest):
        template = self.env.get_template(template_filename)
        sources = [""] * len(entries)
        # read source files
        for entry in entries:
            entry.source_filename = self.get_source_filename(entry.language, entry.id)
        # render in slices á 5 postings
        page_number = 1
        maxpages = int(len(entries) / 5.0 + 1)
        html_base_path = "overview/blog-{}".format(entries[0].language)
        for i in range(0, len(entries), 5):
            postings_end = i + 5
            html_path = self.get_overview_destination_path(entries[0].language, page_number)
            with open(html_path, "wb") as posting_html:
                result = template.render(postings=entries[i:i+5], pagenumber=page_number, maxpages=maxpages, html_base_path=html_base_path, latest_entries=latest)
                posting_html.write(result.encode("utf-8"))
                posting_html.close()
            page_number += 1

    def build_atom(self, entries):
        lang = entries[0].language
        feed_title = "OpenRailwayMap ({})".format(lang)
        feed_url = "https://blog.openrailwaymap.org/{}.atom".format(lang)
        feed = AtomFeed(feed_title, feed_url=feed_url, title_type="text", author="OpenRailwayMap developers")
        for entry in entries:
            dest_path = "https://blog.openrailwaymap.org/{}/{}".format(lang, entry.destination_path)
            updated = entry.moddate
            if entry.moddate is None or entry.moddate == "":
                updated = entry.pubdate
            with open(self.get_source_filename(entry.language, entry.id), "r") as entry_src:
                entry_text = entry_src.read()
                feed.add(entry.title, entry_text, content_type="html", author=entry.authors,
                        url=dest_path, updated=updated, published=entry.pubdate)
        with open("{}/{}.atom".format(self.output_directory, lang), "w") as feedfile:
            feedfile.write(feed.to_string())
    
    def write_entry(self, template_filename, entry, previous_entry, next_entry, latest_entries):
        template = self.env.get_template(template_filename)
        text = ""
        input_filename = self.get_source_filename(entry.language, entry.id)
        sourcefile = open(input_filename, "r")
        text = sourcefile.read()
        if text == "":
            raise Exceptiong("Input file {} is empty.".format(input_filename))
        posting_html = open("{}/{}".format(self.output_directory, entry.destination_path), "wb")
        result = template.render(metadata=entry, posting_source=text, latest_entries=latest_entries, previous_entry=previous_entry, next_entry=next_entry)
        posting_html.write(result.encode("utf-8"))
        posting_html.close()
    
    
    def write_single_entry_pages(self, entries, template_filename, latest):
        template = self.env.get_template(template_filename)
        for idx in range(0, entries.size()):
            previous_entry = None
            if idx != 0:
                previous_entry = entries.at(idx - 1)
            next_entry = None
            if idx != entries.size() - 1:
                next_entry = entries.at(idx + 1)
            self.write_entry(template, entries.at(idx), previous_entry, next_entry, latest)
