#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import arrow
import itertools
import functools
import pkgutil
import re

from . import builder, parser

###############################################################################


class Parser(parser.Parser):

    def __init__(self, pages, images):
        super().__init__(pages)
        self.images = images

    def _image(self, elem):
        if elem.name is None or 'src' not in elem.attrs:
            return
        if elem['src'] in self.images:
            elem['src'] = '../images/{}_{}'.format(
                *elem['src'].split('/')[-2:])
            return
        for parent in elem.parents:
            if 'scp-image-block' in parent.attrs.get('class', ''):
                parent.decompose()
                return
        elem.decompose()

    def _title(self, soup, page):
        super()._title(soup, page)
        class_name = 'scp-title' if 'scp' in page.tags else 'tale-title'
        soup.find(class_='title').attrs = {'class': class_name}


class Book(builder.Book):

    """
    Create scp-wiki ebook.

    Much of this functionality could have been implemented as module-level
    functions instead. The reason why this is a class is trifold:

    1. I wanted to limit the module-level functions to those actually creating
    the ebook variants.
    2. Passing a book instance as the first argument of each functions is
    analogous to a 'self' argument, and implies a class-like hierarchy.
    2. The api for creating a book via class methods is neater than an
    analogous api done via functions.
    """

    def __init__(self, wiki, heap, cover, **kwargs):
        super().__init__(wiki, heap, author='Various Authors', **kwargs)
        self.book.set_cover(pkgutil.get_data(
            'pyscp_ebooks', 'resources/scp_wiki/' + cover))
        self.book.set_stylesheet(pkgutil.get_data(
            'pyscp_ebooks',
            'resources/scp_wiki/stylesheet.css').decode('UTF-8'))

    def _get_content(self, page):
        if not hasattr(self, '_parser'):
            images = [
                i.url for i in self.wiki.list_images()
                if i.status in ('BY-SA CC', 'PUBLIC DOMAIN')]
            self._parser = Parser(self.urls, images)
        return self._parser.parse(page)

    ###########################################################################

    def add_url(self, url, parent=None):
        page = super().add_url(url, parent)
        for i in self._get_children(url):
            self.add_url(i, page)
        return page

    def _get_children(self, url):
        # edge-cases first
        edge_cases = {
            'http://www.scp-wiki.net/scp-076': [
                'http://www.scp-wiki.net/scp-076-2'],
            'http://www.scp-wiki.net/scp-2998': [
                'http://www.scp-wiki.net/scp-2998-{}'.format(i)
                for i in range(2, 11)]}
        if url in edge_cases:
            return edge_cases[url]

        # now the rest
        if url in self._tags('scp', 'splash'):
            return self._children_skip(url)
        elif url in (
                self._tags('hub') & self._tags('tale', 'goi2014') -
                self._tags('_sys')):
            return self._children_hub(url)
        else:
            return []

    def _children_skip(self, url):
        return [u for u in self.wiki(url).links
                if u in self._tags('supplement', 'splash')]

    def _children_hub(self, url):
        candidates = [
            i for i in self.wiki(url).links if i in
            (self._tags('tale', 'goi-format', 'goi2014') - self._tags('hub'))]
        confirmed = [
            i for i in candidates
            if url in self.wiki(i).links or url == self.wiki(i).parent]
        return confirmed if confirmed else candidates

    ###########################################################################

    @functools.lru_cache()
    def _tags(self, *tags):
        """Return a set of urls with matching tags."""
        result = set()
        for tag in tags:
            result |= {p.url for p in self.wiki.list_pages(tag=tag)}
        return result

    def add_intro(self):
        """Add cover, title, and license pages."""
        page = lambda x: pkgutil.get_data(
            'pyscp_ebooks',
            'resources/scp_wiki/{}.xhtml'.format(x)).decode('UTF-8')
        self.add_page('Cover Page', page('cover'))
        self.add_page('Introduction', page('intro'))
        self.add_page('License', page('license'))
        self.add_page('Title Page', page('title'))

    def _add_skip_block(self, block_number, parent=None):
        """Add a 100-skip block to the book."""
        pattern = re.compile(r'[0-9]{3,4}$')
        # X00-X99 for X > 0, 002-099 for X == 0
        start, end = block_number * 100 or 2, block_number * 100 + 99
        skips = sorted([
            i for i in self._tags('scp') if pattern.search(i)
            and start <= int(pattern.search(i).group()) <= end])
        return self.new_section(
            'Articles {:03}-{:03}'.format(start, end), skips, parent)

    def _add_misc_skips(self, parent=None):
        """Add 001 proposals, jokes, and explained articles."""
        self.new_section('001 Proposals', self.wiki('scp-001').links, parent)
        self.new_section('Joke Articles', self._tags('joke'), parent)
        self.new_section(
            'Explained Phenomena', self._tags('explained'), parent)

    def add_skips(self, start=0, end=30, misc=False):
        section = self.new_section('SCP Database')
        for i in range(start, end):
            self._add_skip_block(i, section)
        if misc:
            self._add_misc_skips(section)

    def add_hubs(self, start='0', end='Z'):
        section = self.new_section('Canons and Series')
        for i in sorted(self._tags('hub') - self._tags('_sys')):
            if (start.lower() <= i.split('/')[-1][0] <= end.lower()
                    and self._get_children(i)):
                self.add_url(i, section)

    def add_tales(self, start='0', end='Z'):
        section = self.new_section('Assorted Tales')
        tales = self._tags('tale') - self._tags('hub', 'goi2014')
        # I could have used the first letter of the title instead
        # but that sometimes gives weird stuff like punctuation or
        # non-english symbols
        # urls are always fine
        key = lambda x: x.split('/')[-1][0]
        tales = itertools.groupby(sorted(tales, key=key), key)
        for k, v in tales:
            self.new_section(
                'Tales {}'.format(k.upper()), sorted(list(v)), section)

###############################################################################


def build_complete(wiki, output_path):
    book = Book(
        wiki, wiki.list_pages(rating='>0'), 'complete.png',
        title='SCP Foundation: The Complete Collection')
    book.add_intro()
    book.add_skips(misc=True)
    book.add_hubs()
    book.add_tales()
    book.add_credits()
    book.save(output_path + book.book.title.replace(':', '') + '.epub')


def build_tomes(wiki, output_path):
    heap = list(wiki.list_pages(rating='>0'))
    for tome in range(12):
        book = Book(wiki, heap, 'complete.png',
                    title='SCP Foundation: Tome {}'.format(tome + 1))
        book.add_intro()
        if tome < 6:
            book.add_skips(tome * 5, tome * 5 + 5, misc=tome == 5)
        elif tome < 8:
            book.add_hubs(*('0L', 'MZ')[tome - 6])
        else:
            book.add_tales(*('0D', 'EL', 'MS', 'TZ')[tome - 8])
        book.add_credits()
        book.save(output_path + book.book.title.replace(':', '') + '.epub')


def build_digest(wiki, output_path):
    """Create Monthly Digest ebook."""
    date = arrow.now().replace(months=-1)
    short_date = date.format('YYYY-MM')
    long_date = date.format('MMMM YYYY')
    book = Book(
        wiki, wiki.list_pages(rating='>0', created=short_date), 'complete.png',
        title='SCP Foundation Monthly Digest: ' + long_date)
    book.add_intro()
    book.add_skips(misc=True)
    book.add_hubs()
    book.add_tales()
    book.add_credits()
    book.save(output_path + book.book.title.replace(':', '') + '.epub')
