#!/usr/bin/env python3
"""Create ebooks from wikidot-hosted sites."""


###############################################################################
# Module Imports
###############################################################################

import logging

from . import epub, parser, utils


###############################################################################

log = logging.getLogger(__name__)

###############################################################################


class Book:

    """
    Build epub files from wikidot sites.

    This class provides common functionality for turning wikidot websites
    into epub ebooks. This includes html parsing, placing and overwriting
    placeholder pages, and constructing credits.
    """

    def __init__(self, wiki, heap, **kwargs):
        self.wiki = wiki
        self.heap = {p.url for p in heap}
        self.book = epub.Book(**kwargs)
        self.urls = {}
        self.pb = utils.PBar(
            '{:40.40}'.format(self.book.title.upper()), len(self.heap) * 3)

    def add_page(self, title, content, parent=None):
        return self.book.add_page(title, content, parent)

    def add_url(self, url, parent=None):
        """
        Add the page at the given url to the ebook.

        Places a placeholder empty page into the ebook.
        This is later overwritten by the correct data post-parsing.

        If the url is not in the heap, silently does nothing.
        """
        if url not in self.heap:
            return
        self.pb.update()
        self.heap.remove(url)
        page = self.book.add_page(url, '-', parent)
        self.urls[url] = page.uid
        return page

    def _replace_placeholders(self, parent):
        """
        Find and replace placeholders in the page tree.

        Recursively iterates over the pages of the book, overwrites placeholder
        pages and updates title information.
        """
        parent.children[:] = [self._overwrite(i) for i in parent.children]
        for i in parent.children:
            self._replace_placeholders(i)

    def _overwrite(self, item):
        """Overwrite the placeholder page with parsed data."""
        if item.title not in self.urls:
            return item
        self.pb.update()
        page = self.wiki(item.title)
        content = parser.parse(page, self.urls)
        self.book._write_page(item.uid, page.title, content)
        return item._replace(title=page.title)

    def _add_section_header(self, title, parent=None):
        """Add an empty page with the title of the new section"""
        return self.add_page(
            title, '<div class="title2">{}</div>'.format(title), parent)

    def new_section(self, title, urls=None, parent=None):
        """
        Add a new section.

        Adds a header-page with the name of the section, and pages for the
        urls as children of the header-page.

        If none of the urls are in the heap, the header will not be added.
        """
        if urls is not None and not set(urls) & self.heap:
            return
        header = self._add_section_header(title, parent)
        if urls:
            for url in urls:
                self.add_url(url, header)
        return header

    def add_credits(self):
        """
        Add author credits.

        Constructs credit pages based on the sections and urls already added
        to the book, and add them as a separate section.
        """
        log.info('Constructing credits.')
        self.pb.max_value = len(self.urls) * 3
        credits = self._add_section_header('Acknowledgments and Attributions')
        subsections = []
        for page in epub.flatten(self.book.root):
            if page.title not in self.urls and page.children:
                subsections.append([page.title, ''])  # new major section
            if page.title not in self.urls:
                continue
            subsections[-1][1] += self._get_page_credits(page.title)
        subsections = ((t, c) for t, c in subsections if c)
        for title, content in subsections:
            content = '<div class="attrib">{}</div>'.format(content)
            self.add_page(title, content, credits)
        return credits

    def _get_page_credits(self, url):
        """Generate attribution text for the given url."""
        # this method is messy, but I can't think of a way to improve it atm.
        self.pb.update()
        page = self.wiki(url)
        if not page.author:
            return ''
        source = (
            '<b><a href="{}.xhtml">{}</a></b> ({}) was written by <b>{}</b>'
            .format(self.urls[url], page.title, page.url, page.author))
        if page.rewrite_author:
            source += ', rewritten by <b>{}</b>'.format(page.rewrite_author)
        return '<p>{}.</p>'.format(source)

    def save(self, filename):
        for page in self.book.root:
            self._replace_placeholders(page)
        self.book.save(filename)
        self.pb.finish()
