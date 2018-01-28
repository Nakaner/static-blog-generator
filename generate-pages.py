#! /usr/bin/env python3

import json, sys, datetime
import argparse
from jinja2 import Environment, FileSystemLoader, select_autoescape
from static_blog_generator.pubdates import Pubdates
from static_blog_generator.entry import Entry
from static_blog_generator.entry_collection import EntryCollection
from static_blog_generator.entry_writer import EntryWriter

def configure(args):
    if args.configuration is None:
        return
    with open(args.configuration) as config_file:
        file_config = json.load(config_file)
        args.output_directory = file_config.get("output_directory", args.output_directory)
        args.template_directory = file_config.get("template_directory", args.template_directory)
        args.source_directory = file_config.get("source_directory", args.source_directory)
        args.blog_configuration = file_config.get("blog_configuration", args.blog_configuration)


parser = argparse.ArgumentParser()
parser.add_argument("-o", "--output-directory", help="output directory")
parser.add_argument("-t", "--template-directory", help="template search path")
parser.add_argument("-s", "--source-directory", help="source file search path")
parser.add_argument("-c", "--configuration", help="file to load configuration from")
parser.add_argument("blog_configuration", help="JSON file describing entries")
args = parser.parse_args()
configure(args)

with open(args.blog_configuration) as data_file:
    data = json.load(data_file)
    entries_de = EntryCollection("de")
    entries_en = EntryCollection("en")
    entries_de.init_from_json(data)
    entries_en.init_from_json(data)

    writer = EntryWriter(args.template_directory, args.source_directory, args.output_directory)

    # read publication and modification dates
    pubdates = Pubdates(writer)
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

    template_single_de = "blog-de.html"
    template_single_en = "blog-en.html"

    writer.write_single_entry_pages(entries_de, template_single_de, entries_de.get_latest())
    writer.write_single_entry_pages(entries_en, template_single_en, entries_en.get_latest())

    template_overview_de = "blog-overview-de.html"
    template_overview_en = "blog-overview-en.html"

    writer.write_overview_pages(entries_de.by_date(True), template_overview_de, entries_de.get_latest())
    writer.write_overview_pages(entries_en.by_date(True), template_overview_en, entries_en.get_latest())

    writer.build_atom(entries_de.by_date(True))
    writer.build_atom(entries_en.by_date(True))

    entries_de.save_pubdates(pubdates)
    entries_en.save_pubdates(pubdates)
    pubdates.write_to_file("pubdates.json")

