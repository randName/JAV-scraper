import re
import requests
from bs4 import BeautifulSoup
from datetime import timedelta

class DMM:
    """Website as an object."""

    REALMS = ( 'digital/videoa', 'mono/dvd' )

    MORAS = [ c.strip()+v for c in ' kstnhmr' for v in 'aiueo' ]
    MORAS.extend(['ya','yu','yo','wa','wo','nn'])

    L_PAGE = 'list-boxcaptside list-boxpagenation'

    ART_ID = re.compile(r'article=(\w+)/id=(\d+)')

    def normalize( self, t ):
        """Standardize characters over realms."""
        return re.sub('〜','～',t)

    def get_soup( self, page, realm=None ):
        """Get page as a BeautifulSoup."""

        if realm is not None: page = '%s/-/%s' % ( self.REALMS[realm], page )
        r = requests.get( 'http://www.dmm.co.jp/%s' % page )

        return BeautifulSoup( r.text, 'html.parser' )

    def get_id( self, a ):
        """Get ID from <a> tag href."""
        rid = re.compile(r'/id=(\d+)')
        try:
            return int( rid.search(a.get('href')).group(1) )
        except AttributeError:
            return None

    def get_filename( self, img ):
        """Get filename from <img> tag src."""
        name = img.get('src').rsplit('/',1)[-1].split('.')
        if name[0] == 'noimage':
            return ''
        else:
            return name[0]

    def get_article( self, realm, article, a_id ):
        """Get info of given ID."""
        item = {}
        soup = self.get_soup( "list/=/article=%s/id=%s/" % ( article, a_id ), realm )

        pg = soup.find('div',class_=self.L_PAGE)

        item['count'] = 0
        if pg:
            numz = pg.p.string.replace(',','')
            item['count'] = int(re.match(r'(\d+)',numz).group(1))

        item['name'] = re.sub( r' -[^-]+- DMM.R18$', '', soup.title.string )

        if article == 'actress' or article == 'director':
            ft = re.split( r'[()（）]+', item['name'] )[:-1]

            if ft:
                item['name'] = ft[0]
                item['furi'] = ft[-1]

                if len(ft) == 3:
                    item['alias'] = ft[1]

        return item

    def get_work_page( self, realm, cid ):
        """Get info page of given CID."""

        work = {}
        soup = self.get_soup( "detail/=/cid=%s/" % cid, realm )

        detail = soup.find('div',class_='page-detail').table

        sample_imgs = detail.find('div',id='sample-image-block')
        if sample_imgs: work['sample_images'] = len( sample_imgs('a') )

        for cell in detail.table('td'):
            try:
                d = self.ART_ID.search( cell.a.get('href') ).groups()
            except AttributeError:
                dt = re.match(r'(\d+)/(\d+)/(\d+)',next(cell.stripped_strings,''))
                if 'date' not in work and dt: work['date'] = '-'.join(dt.groups())
                continue
            if d[0] == 'director': work['director'] = d[1]

        return work

    def get_related( self, realm, cid ):
        """Get related CIDs and their realms."""
        cds = re.compile(r'dmm.co.jp/(.+)/-/detail/=/cid=(\w+)')
        path = "misc/-/mutual-link/ajax-index/=/cid={0}/service={1[0]}/shop={1[1]}/"

        related = []
        soup = self.get_soup( path.format( cid, self.REALMS[realm].split('/') ) )

        for l in soup('li'):
            r = cds.search( l.a.get('href') )
            if r.group(1) in ( 'mono/dvd', 'digital/videoa' ): related.append( r.groups() )

        return related

    def get_image_path( self, realm, pid, param='pt' ):
        """Get image path."""
        IMG_REALM = ( 'digital/video', 'mono/movie/adult' )

        if param.startswith('jp'): realm = 0

        return "{0}/{1}/{1}{2}.jpg".format( IMG_REALM[realm], pid, param )

    def get_sample_vid_path( self, cid, param='sm' ):
        """Get sample video path."""

        def get_sample_vid_id( cid ):
            flv = re.compile(r'flashvars.(\w+) = "?(\w+)"?')

            soup = self.get_soup( "service/-/flash/=/cid=%s/" % cid )

            for s in soup.find_all('script',string=True):
                for fv in flv.finditer(s.string):
                    if fv.group(1) == 'cid': return fv.group(2)

        # sizes = ( 'sm', 'dm', 'dmb' )

        vid = get_sample_vid_id( cid )

        if not vid: return ''

        return "litevideo/freepv/{0:.1}/{0:.3}/{0}/{0}_{1}_w.mp4".format( vid, param )

    def identify_maker( self, pid ):

        makers = {
            '1'  : True, '13' : True, '53' : 40039, '59' : True, '61' : 40047, '84' : 40071,
            '118': True, '171': True, '172': 40185, '422': True, '433': True, '436': 45061,
            'h_068': True, 'h_094': True, 'h_244': True, 'h_254': True, 'h_259': True,
            'h_422': 45667, 'h_565': True, 'h_606': True, 'h_796': True, 'h_843': True,
        }

        if not parts[0]:
            maker = True
            if parts[1] == 'bnsps': maker = 45249
        elif parts[0].startswith('55'):
            maker = 40041
        elif parts[0] in makers:
            maker = makers[parts[0]]

        if not maker:
            return None

    def rename( self, pid, maker ):
        """Get DVD name from pid and maker."""

        def get_num(p,digits=3): return '-{:0{d}d}'.format(int(p[1]),d=digits)

        def get_suffix(p):
            if not p[2]: return ''
            return p[2] if '_' in p[2] else '-%s' % p[2]

        def get_txt(p,digits): return p[0] + get_num(p,digits) + get_suffix(p)

        id_base = ( r'^(?:h_)?(?:\d+)?', r'((?:d1)?[a-z]+(?:3d)?[a-z]*)', r'(\d+)([a-z]+|_\d)?$' )

        default_parser = { 're': ''.join(id_base), 'digits': 3, 'txt': get_txt }

        parsers = {
            1398 : { 're': r'^(d1clymax|dcb1|[a-z]+)' + id_base[2] },
            40039 : { 'digits': 4 }, 45667 : { 'digits': 4 },
            40041 : { 're': r'^(?:55|57)(t28|\d*[a-z]+)(\d+)([a-z])?$' },
            45249 : { 'massage': lambda p: ('nsps',p[1]) if p[0] == 'bnsps' else p }
        }

        try:
            parser = parsers[int(maker)]
            for k in ( 're', 'digits', 'txt' ):
                if k not in parser: parser[k] = default_parser[k]
        except KeyError:
            parser = default_parser
        except ( TypeError, ValueError ):
            print( "Error: Could not get maker %s" % maker )
            return None

        try:
            parts = re.match(parser['re'],pid).groups()
        except AttributeError:
            print( "Error: Could not identify a base for %s" % pid )
            return None

        if 'massage' in parser: parts = parser['massage']( parts )

        return parser['txt']( parts, parser['digits'] ).upper()

    def get_keywords( self ):
        """Get keywords in array."""

        def tag(link, category):
            cats = ('シチュエーション','ＡＶ女優タイプ','コスチューム','ジャンル','プレイ','その他')

            _id = self.get_id(link)
            if not _id: return None

            return { '_id': _id, 'name': link.string, 'category': cats.index(category) }

        tags = []

        soup = self.get_soup( 'genre/', 0 )

        for section in soup.find_all('div', id=re.compile('^list')):
            category = section.div.string
            if category == "おすすめジャンル": continue
            if category == "タイプ": category = "ＡＶ女優タイプ"

            tags.extend([ tag(link,category) for link in section.ul('a') ])

        soup = self.get_soup( 'genre/', 1 )

        for section in soup.find_all('table', class_='sect02'):
            category = section.get('summary')
            tags.extend([ tag(link,category) for link in section('a') ])

        return list(filter(None.__ne__, tags))

    def get_makers( self, mora, callback=print ):

        def maker( item, realm ):
            m = {}

            m['_id'] = self.get_id(item.a)
            if not m['_id']: return None

            m['roma'] = self.get_filename(item.img)

            if realm == 0:
                m['name'] = item.find(class_='d-ttllarge').string
                try:
                    m['description'] = item.p.string.strip()
                except AttributeError:
                    pass

            elif realm == 1:
                m['name'] = item.img.get('alt')
                m['description'] = self.normalize(item.br.string.strip())

            return m

        search = 'maker/=/keyword=%s/' % mora 

        soup = self.get_soup( search, 0 )

        for div in soup.find_all('div', class_='d-boxpicdata d-smalltmb'):
            callback( maker( div, 0 ) )

        soup = self.get_soup( search, 1 )

        for cell in soup.find_all('td',class_='w50'):
            callback( maker( cell, 1 ) )

        extra_base = soup.find(class_='list-table mg-t12')
        if extra_base:
            for link in extra_base('a'):
                _id = self.get_id(link)
                if not _id: continue
                callback({ '_id': _id, 'name': link.string })

    def get_works( self, realm, m_id, count, page=1, callback=print ):

        def get_rss( s, r, q ):

            URL = 'http://www.dmm.co.jp/{0}/-/list/{1}/article=maker/sort=release_date/{2}/' 
            RSS = ( "rss/=", "=/rss=create" )

            print( "%s %s:" % (r, q), end="\t" )
            r = s.get( URL.format( self.REALMS[r], RSS[r], q ) )
            print( r.elapsed, end="\r" )

            r.encoding = 'utf-8'
            return BeautifulSoup( r.text, 'xml' )

        def parse_work_rss( soup ):

            properties = ( 'title', 'description', 'link', 'package', 'date' )

            work = { 'keywords': [], 'actresses': [] }

            for p in properties: work[p] = soup.find(p).string

            work['cid'] = re.search(r'cid=(\w+)', work['link']).group(1)
            work['pid'] = re.search(r'/(video|adult)/(\w+)', work['package']).group(2)
            work['released_date'] = work['date'].split('T')[0]

            content = BeautifulSoup( soup.encoded.string, 'html.parser' )

            for info in content('strong'):
                if '分' in info.next_sibling:
                    dur_mins = int( info.next_sibling.strip('分') )
                    work['runtime'] = timedelta( minutes = dur_mins )
                    break

            for link in content('a'):
                l = self.ART_ID.search( link.get('href') )
                if not l: continue
                if l.group(1) == 'keyword':
                    work['keywords'].append( l.group(2) )
                elif l.group(1) == 'actress':
                    work['actresses'].append( l.group(2) )
                else:
                    work[l.group(1)] = l.group(2)

            work['_id'] = self.rename( work['pid'], work['maker'] )
            work['realm'] = realm

            return work

        works = []
        worksession = requests.Session()

        while len(works) < count:
            soup = get_rss( worksession, realm, "id=%d/page=%d" % ( m_id, page ) )
            for item in soup('item'): works.append( callback( parse_work_rss(item) ) )
            page += 1

        return works

    def search_dmm( self, terms ):

        soup = self.get_soup( 'search/=/searchstr=%s/' % '%20'.join(terms) )

        for a in soup.find('div',class_='d-item')('a'):
            link = a.get('href') 

            for d in ('digital','mono'):
                if d not in link: continue
                try:
                    cid = re.search(r'cid=(\w+)', link).group(1)
                except AttributeError:
                    continue

                for t in terms:
                    if t not in cid: break
                else:
                    print( cid )

if __name__ == "__main__":

    dmm = DMM()
    # print( dmm.get_keywords() )
