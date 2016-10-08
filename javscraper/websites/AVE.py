import re
import requests
from bs4 import BeautifulSoup
from datetime import date, timedelta


class TagCategory:
    SITUATION = 0
    ATYPE = 1
    COSTUME = 2
    GENRE = 3
    PLAY = 4
    MISC = 5

    names = {
        SITUATION: 'Situation',
        ATYPE: 'Actress Type',
        COSTUME: 'Costume',
        GENRE: 'Genre',
        PLAY: 'Play',
        MISC: 'Others',
    }

    translation = {
        '女優のキャラクター': SITUATION,
        '女優のルックス': ATYPE,
        'コスチューム': COSTUME,
        '作品のジャンル': GENRE,
        'プレイ内容': PLAY,
        'その他': MISC,
    }

    def __init__(self, text=''):
        self.cat = self.translation.get(text, self.MISC)

    def __str__(self):
        return self.names[self.cat]

    def __repr__(self):
        return '<TagCategory: %s>' % str(self)


def get_soup(page, realm=None):
    r = requests.get( 'http://www.aventertainments.com/%s' % page )
    return BeautifulSoup( r.text, 'html.parser' )

def get_id(a):
    rid = re.compile(r'(?:product_id|subdept_id|StudioID)=(\d+)')
    try:
        return int( rid.search(a.get('href')).group(1) )
    except AttributeError:
        return None

def get_keywords():
    """Get tags."""

    def tags(links, category):
        c = TagCategory(category)
        for link in links:
            _id = get_id(link)
            if not _id: continue
            if '★' in link.string: continue
            yield {'_id': _id, 'name': link.string, 'category': c}

    soup = get_soup('categorylists.aspx')

    for section in soup.find_all('div', class_='row2'):
        category = next(section.h1.stripped_strings, '')
        if category in ('メインメニュー', 'セール'): continue
        yield from tags(section.div.table.find_all('a'), category)

def get_makers():
    """Get makers."""

    soup = get_soup('studiolists.aspx')
    block = soup.find_all('div', class_='row2')[1]
    for link in block.find_all('a'):
        _id = get_id(link)
        if not _id: continue
        yield {'_id': _id, 'name': link.string}

def get_studio_list(_id):
    base_url = 'studio_products.aspx?Dept_ID=29&SortBy=1&HowManyRecords=20&'
    search = 'StudioID=%s&CountPage=%s' % (_id,1)

    soup = get_soup(base_url + search)
    for detail in soup.find('div',class_='main-unit2')('table'):
        if not detail.h4: continue
        yield get_id(detail.h4.a)

if __name__ == "__main__":
    print("AVE")
    #for m in get_makers(): print(m)
    #for v in get_studio_list(): print(v)
