#! /usr/bin/env python3

import json, sys, datetime, os
import hashlib
from jinja2 import Environment, FileSystemLoader, select_autoescape
from static_blog_generator.pubdates import Pubdates
from static_blog_generator.pubdates import get_source_filename
from static_blog_generator.entry import Entry
from static_blog_generator.entry_collection import EntryCollection

templateLoader = FileSystemLoader(searchpath=".")
env = Environment(
    loader=FileSystemLoader(searchpath="."),
    trim_blocks=True,
    autoescape=select_autoescape(enabled_extensions=(), default_for_string=True, default=False)
)
output_directory = "./"

def get_overview_destination_path(language, page_number):
    if page_number > 1:
        return "overview/blog-{}_{}.html".format(language, str(page_number))
    return "overview/blog-{}.html".format(language)

def write_overview_pages(entries, template, latest):
    sources = [""] * len(entries)
    # read source files
    for entry in entries:
        entry.source_filename = get_source_filename(entry.language, entry.id)
    # render in slices á 5 postings
    page_number = 1
    maxpages = int(len(entries) / 5.0 + 1)
    html_base_path = "overview/blog-{}".format(entries[0].language)
    for i in range(0, len(entries), 5):
        postings_end = i + 5
        html_path = get_overview_destination_path(entries[0].language, page_number)
        with open("{}/{}".format(output_directory, html_path), "wb") as posting_html:
            result = template.render(postings=entries[i:i+5], pagenumber=page_number, maxpages=maxpages, html_base_path=html_base_path, latest_entries=latest)
            posting_html.write(result.encode("utf-8"))
            posting_html.close()
        page_number += 1

def build_rss(entries, template):
    for entry in entries:
        entry.source_filename = get_source_filename(entry.language, entry.id)
    pubtimes = [entry.pubdate for entry in entries]
    latest_pubtime = max(pubtimes)
    latest_update = datetime.datetime.strptime(latest_pubtime, "%Y-%m-%d").strftime("%a, %d %b %Y 12:00:00 +0000")
    latest_build = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")
    language = entries[0].language
    with open("{}/{}.rss".format(output_directory, language), "wb") as feedfile:
        result = template.render(latest_update=latest_update, latest_build=latest_build, description="", postings=entries, language=language)
        feedfile.write(result.encode("utf-8"))

def write_entry(template, entry, previous_entry, next_entry, latest_entries):
    text = ""
    input_filename = get_source_filename(entry.language, entry.id)
    sourcefile = open(input_filename, "r")
    text = sourcefile.read()
    if text == "":
        raise Exceptiong("Input file {} is empty.".format(input_filename))
    posting_html = open("{}/{}".format(output_directory, entry.destination_path), "wb")
    result = template.render(metadata=entry, posting_source=text, latest_entries=latest_entries, previous_entry=previous_entry, next_entry=next_entry)
    posting_html.write(result.encode("utf-8"))
    posting_html.close()


def write_single_entry_pages(entries, template, latest):
    for idx in range(0, entries.size()):
        previous_entry = None
        if idx != 0:
            previous_entry = entries.at(idx - 1)
        next_entry = None
        if idx != entries.size() - 1:
            next_entry = entries.at(idx + 1)
        write_entry(template, entries.at(idx), previous_entry, next_entry, latest)


config_file_name = sys.argv[1]
with open(config_file_name) as data_file:
    data = json.load(data_file)
    entries_de = EntryCollection("de")
    entries_en = EntryCollection("en")
    entries_de.init_from_json(data)
    entries_en.init_from_json(data)

    # read publication and modification dates
    pubdates = Pubdates()
    pubdates.read_from_file()
    entries_de.add_pubdate_moddate_information(pubdates)
    entries_en.add_pubdate_moddate_information(pubdates)
    
    # add missing pubdates
    for entry in entries_de.entries:
        pubdates.set_pubdate_if_missing("de", entry.id)
        pubdates.set_moddate_if_missing("de", entry.id)
    for entry in entries_en.entries:
        pubdates.set_pubdate_if_missing("en", entry.id)
        pubdates.set_moddate_if_missing("en", entry.id)

    # add cross language links
    entries_de.add_cross_language_links(entries_en)
    entries_en.add_cross_language_links(entries_de)

    entries_de.sort_by_date()
    entries_en.sort_by_date()

    template_single_de = env.get_template("blog-de.html")
    template_single_en = env.get_template("blog-en.html")

    write_single_entry_pages(entries_de, template_single_de, entries_de.get_latest())
    write_single_entry_pages(entries_en, template_single_en, entries_de.get_latest())

    template_overview_de = env.get_template("blog-overview-de.html")
    template_overview_en = env.get_template("blog-overview-en.html")

    write_overview_pages(entries_de.by_date(True), template_overview_de, entries_de.get_latest())
    write_overview_pages(entries_en.by_date(True), template_overview_en, entries_de.get_latest())

    rss_template = env.get_template("rss-template.rss")
    build_rss(entries_de.by_date(True), rss_template)
    build_rss(entries_en.by_date(True), rss_template)

    entries_de.save_pubdates(pubdates)
    entries_en.save_pubdates(pubdates)
    pubdates.write_to_file("pubdates.json")

