#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import pkgutil
import re
import arrow

from . import builder, parser

###############################################################################


class Book(builder.Book):

    def __init__(self, wiki, heap, **kwargs):
        super().__init__(wiki, heap, author='Various Authors', **kwargs)
        self.book.set_cover(pkgutil.get_data(
            'pyscp_ebooks',
            'resources/wanderers_library/cover.png'))
        self.book.set_stylesheet(pkgutil.get_data(
            'pyscp_ebooks',
            'resources/wanderers_library/stylesheet.css').decode('UTF-8'))

    def add_intro(self):
        """Add cover, title, and license pages."""
        page = lambda x: pkgutil.get_data(
            'pyscp_ebooks',
            'resources/wanderers_library/{}.xhtml'.format(x)).decode('UTF-8')
        self.add_page('Cover Page', page('cover'))
        self.add_page('Introduction', page('intro'))
        license = parser.bs(page('license'))
        license.find(class_='footer').string = arrow.now().format('YYYY-MM-DD')
        self.add_page('License', license.div.prettify())
        self.add_page('Title Page', page('title'))

    def add_library(self):
        """Add library books to the ebook."""
        library = self.new_section('The Library')
        books = self.wiki('the-library')._soup(class_='boxbook')
        template = (
            '<div class="book-title">{}</div>'
            '<div class="book-description">{}</div>')
        for b in books:
            title = b.find(class_='booktitle').string
            description = b.find(class_='boxleft')('div')[0].text.strip()
            excerpts = [self.wiki.site + a['href']
                        for a in b.find(class_='boxright')('a')]
            if title == 'The Journal of Aframos Longjourney':
                links = self.wiki(excerpts[1])._soup.select('#page-content a')
                links = [
                    'http://wanderers-library.wikidot.com/' +
                    l['href'].split('/')[-1] for l in links]
                excerpts = [excerpts[0]] + links
            book = self.add_page(
                title, template.format(title, description), library)
            for url in excerpts:
                self.add_url(url, book)

    def add_archives(self):
        self.new_section(
            'The Archives', sorted(self.wiki('the-archives').links))

    def add_prompts(self):
        main_section = self.new_section('Writing Prompts')
        titles = ('Wanderlust', 'Space Witch', 'Relationship')
        prompts = self.wiki('prompt-archive')._soup.find(
            id='page-content')('div', recursive=False)
        template = (
            '<div class="book-title">{}</div>'
            '<div class="book-description">{}</div>')
        for title, prompt in zip(titles, prompts):
            description = prompt.find('blockquote').text
            links = [self.wiki.site + a['href'] for a in prompt('a')]
            subsection = self.add_page(
                title, template.format(title, description), main_section)
            for url in links:
                self.add_url(url, subsection)

    def _add_goi_page(self, soup, parent):
        title = soup.div.text
        poem, description, quote = soup(
            'div', style=re.compile('border[^;]*#004F00'))
        footnotes = soup('p')[-1]
        poem.attrs = {'class': 'goi-poem'}
        description.attrs = {'class': 'goi-description'}
        quote.attrs = {'class': 'goi-quote'}
        footnotes.attrs = {'class': 'goi-footnotes'}
        source = parser.bs('<p class="goi-title">{}</p>{}{}{}{}'.format(
            title, poem, description, quote, footnotes))
        for a in source('a'):
            a.name = 'span'
            a.attrs = {'class': 'link'}
        goi_page = self.add_page(title, source.prettify(), parent)
        for url in [self.wiki.site + a['href'] for a in soup('a')]:
            self.add_url(url, goi_page)

    def add_goi(self):
        goi_page = self.wiki('thearchivistslog')._soup.find(id='page-content')
        title = goi_page.div('p')[0].text
        section = self.new_section(title)
        for block in goi_page(
                'div', style=re.compile('background[^;]*#f2f2c2')):
            self._add_goi_page(block, section)


def build_complete(wiki, output_path):
    book = Book(wiki, wiki.list_pages(), title="Wanderers' Library")
    book.add_intro()
    book.add_library()
    book.add_archives()
    book.add_prompts()
    book.add_goi()
    book.add_credits()
    book.save(output_path + book.book.title.replace(':', ' -') + '.epub')
