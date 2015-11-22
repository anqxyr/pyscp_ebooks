#!/usr/bin/env python3
"""Parse wikidot html."""

###############################################################################
# Module Imports
###############################################################################

import bs4

###############################################################################


def bs(html=''):
    return bs4.BeautifulSoup(html, 'lxml')

###############################################################################


def parse(page, pages):
    soup = bs(page.html).find(id='page-content')
    for elem in soup(class_='page-rate-widget-box'):
        elem.decompose()
    for elem in soup(class_='yui-navset'):
        _tab(elem)
    for elem in soup(class_='collapsible-block'):
        _collapsible(elem)
    for elem in soup('sup', class_='footnoteref'):
        _footnote(elem)
    for elem in soup(class_='footnote-footer'):
        _footnote_footer(elem)
    for elem in soup('blockquote'):
        _quote(elem)
    for elem in soup('a'):
        _link(elem, page._wiki.site, pages)
    return str(soup)


def _tab(elem):
    """Parse wikidot tab block."""
    elem.attrs = {'class': 'tabview'}
    titles = elem.find(class_='yui-nav')('em')
    elem.find(class_='yui-nav').decompose()
    elem.div.unwrap()
    for tab, title in zip(
            elem('div', recursive=False), titles):
        tab.attrs = {'class': 'tabview-tab'}
        new_title = bs().new_tag('p', **{'class': 'tab-title'})
        new_title.string = title.text
        tab.insert(0, new_title)


def _collapsible(elem):
    """Parse collapsible block."""
    elem.attrs = {'class': 'collapsible'}
    title = bs().new_tag('p', **{'class': 'collapsible-title'})
    title.string = elem.find(class_='collapsible-block-link').text
    body = elem.find(class_='collapsible-block-content')
    elem.clear()
    elem.append(title)
    for child in list(body.contents):
        elem.append(child)


def _footnote(elem):
    """Parse a footnote."""
    elem.string = elem.a.string


def _footnote_footer(elem):
    """Parse footnote footer."""
    elem.attrs = {'class': 'footnote'}
    elem.string = ''.join(elem.stripped_strings)


def _link(elem, site, pages):
    """Parse a link; remap if links to a page, otherwise remove."""
    if 'href' not in elem.attrs:
        return
    link = elem['href']
    if not link.startswith(site):
        link = site + link
    if link not in pages:
        elem.name = 'span'
        elem.attrs = {'class': 'link'}
    else:
        elem['href'] = pages[link] + '.xhtml'


def _quote(elem):
    """Parse a block quote."""
    elem.name = 'div'
    elem.attrs = {'class': 'quote'}


def _title(page, soup):
    pass
