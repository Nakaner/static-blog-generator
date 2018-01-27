# Static Blog Generator

Generate a blog as static pages using Jinja2 template engine.
The blog may have two languages (currently partially hardcoded as English and German).

## Usage

A JSON file contains all metadata of all blog entries:

```json
[
  {
    "id": "karlsruhe-january",
    "languages": {
      "de": {
        "authors": "",
        "destination_path": "das-hackweekend-in-karlsruhe-was-sonst-noch-geschah",
        "subtitle": "",
        "title": "Das Hackweekend in Karlsruhe und was sonst noch geschah"
      },
      "en": {
        "authors": "",
        "destination_path": "karlsruhe-hack-weekend-else-happened",
        "subtitle": "",
        "title": "The Karlsruhe hack weekend and what else happend since January"
      }
    }
  },
  {
    "id": "mailing-liste",
    "languages": {
      "de": {
        "authors": "rurseekatze",
        "destination_path": "mailingliste",
        "subtitle": "",
        "title": "Mailingliste"
      },
      "en": {
        "authors": "rurseekatze",
        "destination_path": "mailing-list",
        "subtitle": "",
        "title": "Mailing list"
      }
    }
  }
]
```

Build the blog using `python3 generate-pages.py config.json`.


