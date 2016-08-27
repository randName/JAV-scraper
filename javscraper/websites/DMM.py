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
        'シチュエーション': SITUATION,
        'ＡＶ女優タイプ': ATYPE,
        'コスチューム': COSTUME,
        'ジャンル': GENRE,
        'プレイ': PLAY,
        'その他': MISC,
        'タイプ': ATYPE,
    }

    def __init__(self, text=''):
        self.cat = self.translation.get(text, self.MISC)

    def __str__(self):
        return self.names[self.cat]

    def __repr__(self):
        return '<TagCategory: %s>' % str(self)


__all__ = [ 'get_%s' % a for a in ('article', 'article_list', 'video', 'keywords', 'makers') ]

REALMS = ('digital/videoa', 'mono/dvd')
ART_ID = re.compile(r'article=(\w+)/id=(\d+)')
VID_ID = re.compile(r'cid=(\w+)')


def get_soup(page, realm=None):
    if realm is not None:
        page = '%s/-/%s' % (REALMS[realm], page)
    r = requests.get('http://www.dmm.co.jp/%s' % page)
    return BeautifulSoup(r.text, 'html.parser')

def get_id(a):
    try:
        return int(ART_ID.search(a.get('href')).group(2))
    except AttributeError:
        return None

def get_filename(img):
    name = img.get('src').rsplit('/',1)[-1].split('.')
    return '' if name[0] == 'noimage' else name[0]

def get_page_box(soup):
    L_PAGE = 'list-boxcaptside list-boxpagenation'
    try:
        return soup.find('div',class_=L_PAGE).p.string
    except AttributeError:
        return ''

def get_image_path(pid, realm=0, param='pt'):
    IMG_REALM = ('digital/video', 'mono/movie/adult')
    if param.startswith('jp'): realm = 0
    return "{0}/{1}/{1}{2}.jpg".format( IMG_REALM[realm], pid, param )

def get_sample_vid_path(cid, param='sm'):
    path = "litevideo/freepv/{0:.1}/{0:.3}/{0}/{0}_{1}_{2}.mp4"

    def get_sample_vid_params(cid):
        flv = re.compile(r'flashvars.(\w+) = "?(\w+)"?')
        soup = get_soup("service/-/flash/=/cid=%s/" % cid)

        p = {}
        for s in soup.find_all('script',string=True):
            for fv in flv.finditer(s.string):
                p[fv.group(1)] = fv.group(2)

        return p

    # sizes = ('sm', 'dm', 'dmb')

    vp = get_sample_vid_params(cid)
    vid = vp.get('cid', '')
    if not vid: return ''
    return path.format( vid, param, vp.get('bid', ' ')[-1] )

def get_related(cid, realm=0):
    cds = re.compile(r'dmm.co.jp/(.+)/-/detail/=/cid=(\w+)')
    path = "misc/-/mutual-link/ajax-index/=/cid={0}/service={1[0]}/shop={1[1]}/"
    soup = get_soup(path.format(cid, REALMS[realm].split('/')))
    for l in soup('li'):
        r = cds.search(l.a.get('href'))
        if r.group(1) in REALMS: yield r.groups()


def get_article(article, a_id, realm=0):
    """Get article info."""

    soup = get_soup("list/=/article=%s/id=%s/" % (article, a_id), realm)
    item = {'name': re.sub(r' -[^-]+- DMM.R18$', '', soup.title.string)}

    numz = get_page_box(soup).replace(',','')
    if numz:
        item['count'] = int(re.match(r'(\d+)',numz).group(1))
    else:
        item['count'] = 0

    if article in ('actress', 'director'):
        ft = re.split(r'[()（）]+', item['name'])[:-1]
        if ft:
            item['name'] = ft[0]
            item['furi'] = ft[-1]

            if len(ft) == 3:
                item['alias'] = ft[1]
    return item

def get_video(cid, realm=0):
    """Get video info."""

    work = {'cid': cid, 'realm': realm, 'keywords': (), 'actresses': ()}
    soup = get_soup("detail/=/cid=%s/" % cid, realm)
    
    work['title'] = soup.find('h1').string

    pkg = soup.find('meta',attrs={'property':'og:image'}).get('content')
    work['pid'] = re.search(r'/(video|adult)/(\w+)', pkg).group(2)

    detail = soup.find('div',class_='page-detail').table
    if not detail.table: return None

    for cell in detail.table('td'):
        try:
            d = ART_ID.search(cell.a.get('href')).groups()
            if d[0] in ('actress', 'keyword'):
                l = d[0] + ('es' if d[0].endswith('s') else 's')
                ad = lambda x: ART_ID.search(x.get('href')).group(2)
                work[l] = tuple(ad(i) for i in cell.find_all('a'))
            else:
                work[d[0]] = d[1]
        except AttributeError:
            cstring = next(cell.stripped_strings,'')
            try:
                dur_mins = int(re.match(r'(\d+)分',cstring).group(1))
                work['runtime'] = timedelta(minutes=dur_mins)
            except AttributeError:
                pass

            if 'released_date' in work: continue
            try:
                dt = re.match(r'(\d+)/(\d+)/(\d+)',cstring).groups()
                work['released_date'] = date(*tuple(int(i) for i in dt))
            except ValueError:
                print( cid, dt )
            except AttributeError:
                pass

    sample_imgs = detail.find('div',id='sample-image-block')
    if sample_imgs: work['sample_images'] = len(sample_imgs('a'))

    return work

def get_keywords():
    """Get tags from both realms."""

    def tags(links, category):
        c = TagCategory(category)
        for link in links:
            _id = get_id(link)
            if _id is None: continue
            yield {'_id': _id, 'name': link.string, 'category': c}

    search = 'genre/'

    soup = get_soup(search, 0)
    for section in soup.find_all('div', id=re.compile('^list')):
        category = section.div.string
        if category == "おすすめジャンル": continue
        yield from tags(section.ul('a'), category)

    soup = get_soup(search, 1)
    for section in soup.find_all('table', class_='sect02'):
        yield from tags(section('a'), section.get('summary'))

def get_makers(mora=None):
    """Get makers from both realms."""

    def makers(boxes):
        for item in boxes:
            _id = get_id(item.a)
            if not _id: continue

            try:
                name = item.find(class_='d-ttllarge').string
            except AttributeError:
                name = item.img.get('alt')

            m = {'_id': _id, 'name': name, 'roma': get_filename(item.img)}

            for a in ('br', 'p'):
                try:
                    m['description'] = getattr(item, a).string.strip()
                except AttributeError:
                    pass
            yield m

    search = 'maker/=/keyword=%s/' % mora 

    soup = get_soup(search, 0)
    yield from makers(soup.find_all('div', class_='d-boxpicdata d-smalltmb'))

    soup = get_soup(search, 1)
    yield from makers(soup.find_all('td',class_='w50'))

    extra_base = soup.find(class_='list-table mg-t12')
    if extra_base:
        for link in extra_base('a'):
            _id = get_id(link)
            if _id: yield {'_id': _id, 'name': link.string}

def get_article_list(article, a_id, realm=0, start=1, end=None, count=None):
    """Get list of works."""

    search = "list/=/article=%s/id=%s/sort=release_date/page=%s"
    retrieved = 0
    page = start
    while page != end:
        soup = get_soup( search % (article, a_id, page), realm)
        try:
            nz = get_page_box(soup).split()[2]
        except IndexError:
            break
        cur = int(re.match(r'(\d+)', nz).group(1))
        if cur != page: break
        for i in soup.find('div',class_='d-item').ul('li'):
            yield VID_ID.search(i.a.get('href')).group(1)
            retrieved += 1
            if count and retrieved == count: break
        if count and retrieved > count: break
        page += 1

if __name__ == "__main__":
    print("DMM")
