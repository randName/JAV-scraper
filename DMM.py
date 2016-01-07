import requests, re
from bs4 import BeautifulSoup

from datetime import timedelta

class DMM:
    """Website as an object"""

    MORAS = [ c.strip()+v for c in ' kstnhmr' for v in 'aiueo']
    MORAS.extend(['ya','yu','yo','wa','wo','nn'])

    L_PAGE = 'list-boxcaptside list-boxpagenation'

    ART_ID = re.compile(r'article=(\w+)/id=(\d+)')

    DOMAIN = ( 'digital/videoa', 'mono/dvd' )

    def normalize( self, t ):
        return re.sub('〜','～',t)

    def get_soup( self, page, domain=None ):
        """Get page as a BeautifulSoup."""

        if domain: page = '%s/-/%s' % ( domain, page )
        r = requests.get( 'http://www.dmm.co.jp/%s' % page )

        return BeautifulSoup( r.text, 'html.parser' )

    def get_id( self, a ):
        """Get ID from <a> tag href."""
        rid = re.compile(r'/id=(\d+)')
        try:
            return int( rid.search(a.get('href')).group(1) )
        except AttributeError:
            return None

    def get_string( self, tag ):
        """Returns empty string if attribute does not exist."""
        try:
            return tag.string
        except AttributeError:
            return ''

    def get_filename( self, img ):
        """Get filename from <img> tag src."""
        name = img.get('src').rsplit('/',1)[-1].split('.')
        if name[0] == 'noimage':
            return '' 
        else:
            return name[0]

    def get_article( self, domain, article, a_id ):
        """Get info of given ID."""
        item = {}
        soup = self.get_soup( "list/=/article=%s/id=%d/" % ( article, a_id ), domain )

        t = re.sub( r' -[^-]+- DMM.R18$', '', soup.title.string )
        pg = soup.find('div',class_=self.L_PAGE)

        item['count'] = int(re.match(r'(\d+)',pg.p.string).group(1)) if pg else 0

        if article == 'actress' or article == 'director':
            ft = re.match( r'(.+)\(([^)]*)\)$', t )
            item['name'] = ft.group(1)
            item['furi'] = ft.group(2)
        else:
            item['name'] = t

        return item

    def get_work_page( self, domain, cid ):
        """Get info page of given CID."""
        work = {}
        soup = self.get_soup( "detail/=/cid=%s/" % cid, domain )
        detail = soup.find('div',class_='page-detail').table

        work['sample_images'] = len( detail.find('div',id='sample-image-block')('a') ) 

        for cell in detail.table('td'):
            try:
                d = self.ART_ID.search( cell.a.get('href') ).groups()
            except AttributeError:
                continue
            if d[0] == 'director': work['director'] = d[1]

        return work

    def get_related( self, domain, cid ):
        """Get related CIDs and their domains"""
        cds = re.compile(r'dmm.co.jp/(.+)/-/detail/=/cid=(\w+)')
        p = 'misc/-/mutual-link/ajax-index/=/'

        soup = self.get_soup('%s/cid=%s/service=%s/shop=%s/'%tuple([p,cid]+domain.split('/')))

        return [ cds.search( l.a.get('href') ).groups() for l in soup('li') ]

    def get_sample_vid_id( self, cid ):
        """Get sample video ID of given CID"""
        flv = re.compile(r'flashvars.(\w+) = "?(\w+)"?')

        # flashvars = {}
        soup = self.get_soup( "service/-/flash/=/cid=%s/" % cid )

        for s in soup.find_all('script',string=True):
            for fv in flv.finditer(s.string):
                if fv.group(1) == 'cid': return fv.group(2)
                # flashvars[fv.group(1)] = fv.group(2)

        # return flashvars['cid']

    def rename( self, pid, maker=None ):
        """Get DVD name from pid"""
        id_base = re.compile(r'^((?:h_)?\d+)?([a-z]+(?:3d)?)(\d+)([a-z]+)?$')

        def get_num(p,digits=3): return '-{:0{d}d}'.format(int(p[2]),d=digits)

        def parse_tma( parts, d ):
            if parts[0] == '55':
                if parts[1] == 't':
                    return "t%s-%s" % ( parts[2][0:2], parts[2][-3:] )
                else:
                    return parts[1] + get_num(parts)
            else:
                return "%s%s-%s" % ( parts[0][-2:], parts[1], parts[2][-3:] )

        parser = {
            6350 : { 'digits': 1 }, 40039 : { 'digits': 4 }, 45667 : { 'digits': 4 },
            40041 : { 'txt': parse_tma, },
            45249 : { 'txt': ( lambda p,d: ( 'nsps' if p[1] == 'bnsps' else p[1] ) + get_num(p) ) }
        }

        makers = {
            '1'  : True, '13' : True, '53' : 40039, '59' : True, '61' : 40047, '84' : 40071,
            '118': True, '171': True, '172': 40185, '422': True, '433': True, '436': 45061,
            'h_068': True, 'h_094': True, 'h_244': True, 'h_254': True, 'h_259': True,
            'h_422': 45667, 'h_565': True, 'h_606': True, 'h_796': True, 'h_843': True,
        }

        try:
            parts = id_base.match(pid).groups()
        except AttributeError:
            print("Error: Could not identify a base for %s" % pid )
            return None

        if not parts[0]:
            if not maker: maker = True
            if parts[1] == 'bnsps': maker = 45249
            if re.match(r'ktk[xp]', parts[1]): maker = 6350
        elif parts[0].startswith('55'):
            maker = 40041
        elif parts[0] in makers:
            maker = makers[parts[0]]

        if not maker:
            print("Error: Could not identify a maker for %s" % pid )
            return None

        try:
            digits = parser[maker]['digits']
        except KeyError:
            digits = 3

        try:
            return parser[maker]['txt']( parts, digits ).upper()
        except KeyError:
            return parts[1].upper() + get_num(parts,digits)

    def get_keywords( self ):
        """Get keywords from DMM genres page"""

        def tag(link, category):
            cats = ('シチュエーション','ＡＶ女優タイプ','コスチューム','ジャンル','プレイ','その他')

            _id = self.get_id(link)
            if not _id: return None
            return { '_id': _id, 'name': link.string, 'category': cats.index(category) }

        tags = []

        soup = self.get_soup( 'genre/', self.DOMAIN[0] )

        for section in soup.find_all('div', id=re.compile('^list')):
            category = section.div.string
            if category == "おすすめジャンル": continue
            if category == "タイプ": category = "ＡＶ女優タイプ"

            tags.extend([ tag(link,category) for link in section.ul('a') ])

        soup = self.get_soup( 'genre/', self.DOMAIN[1] )

        for section in soup.find_all('table', class_='sect02'):
            category = section.get('summary')
            tags.extend([ tag(link,category) for link in section('a') ])

        return list(filter(None.__ne__, tags))

    def get_makers( self, mora, callback=print ):

        def parse_maker( maker, domain ):
            m = {}

            m['_id'] = self.get_id(maker.a)
            if not m['_id']: return None

            m['roma'] = self.get_filename(maker.img)

            if domain == self.DOMAIN[0] :
                m['name'] = maker.find(class_='d-ttllarge').string
                m['desc'] = self.get_string(maker.p).strip()
            elif domain == self.DOMAIN[1]:
                m['name'] = maker.img.get('alt')
                m['desc'] = dmm.normalize(maker.br.string.strip())

            return m

        search = 'maker/=/keyword=%s/' % mora 

        soup = self.get_soup( search, self.DOMAIN[0] )

        for maker in soup.find_all('div', class_='d-boxpicdata d-smalltmb'):
            callback( parse_maker( maker, self.DOMAIN[0] ) )

        soup = self.get_soup( search, self.DOMAIN[1] )

        for maker in soup.find_all('td',class_='w50'):
            callback( parse_maker( maker, self.DOMAIN[1] ) )

        extra_base = soup.find(class_='list-table mg-t12')
        if extra_base:
            for maker in extra_base('a'):
                _id = self.get_id(maker)
                if not _id: continue
                callback({ '_id': _id, 'name': maker.string })

    def get_actresses( self, mora, callback=print ):

        def get_pagenum( a ):
            pgn = re.compile(r'/page=(\d+)')
            try:
                return int(pgn.search(a.get('href')).group(1))
            except AttributeError:
                return 0

        def parse_actress( actress, domain ):
            a = {}

            a['_id'] = self.get_id(actress)
            if not a['_id']: return None

            a['roma'] = self.get_filename(actress.img)

            if domain == self.DOMAIN[0]:
                a['name'] = actress.img.get('alt')
                a['furi'] = actress.span.string 
            elif domain == self.DOMAIN[1]:
                a['name'] = dmm.normalize(actress.string)

            return a

        search = 'actress/=/keyword=%s/sort=count/' % mora

        soup = self.get_soup( search, self.DOMAIN[0] )

        totals = soup.find('div',class_=self.L_PAGE+' group')
        count = [ int(x) for x in re.findall(r'\d+', totals.p.string) ]
        cur_page = count[4]
        
        while cur_page <= count[3]:
            for actress in soup.find('ul',class_='d-item act-box-100 group')('a'):
                callback( parse_actress( actress, self.DOMAIN[0] ) )
        
            cur_page += 1
            soup = self.get_soup( search + "page=%d/" % cur_page, self.DOMAIN[0] )

        soup = self.get_soup( search, self.DOMAIN[1] )

        page_nums = soup.find('div',class_='d-boxcaptside d-boxpagenation')

        num_pages = max( [ get_pagenum(p) for p in page_nums('a') ] )
        if num_pages == 0 and page_nums.span : num_pages = 1

        cur_page = 1

        while cur_page <= num_pages:
            for actress in soup.find('ul',class_='act-box-100 group mg-b20')('a'):
                callback( parse_actress( actress, self.DOMAIN[1] ) )

            cur_page += 1
            soup = self.get_soup( search + "page=%d/" % cur_page, self.DOMAIN[1] )

    def get_works( self, domain, m_id, count, page=1, callback=print ):

        def get_rss( s, d, q ):

            URL = 'http://www.dmm.co.jp/{0}/-/list/{1}/article=maker/sort=release_date/{2}/' 
            RSS = ( "rss/=", "=/rss=create" )

            print( "%s %s:" % (d, q), end="\t" )
            r = s.get( URL.format( d, RSS[self.DOMAIN.index(d)], q ) )
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

            work['display_id'] = self.rename( work['pid'], work['maker'] )

            return work

        works = []
        worksession = requests.Session()

        while len(works) < count:
            soup = get_rss( worksession, domain, "id=%d/page=%d" % ( m_id, page ) )
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

    def cb( v ):
        print( "%s %s" % ( v['cid'], v['pid'] ) )

    dmm = DMM()
    # print( dmm.get_keywords() )

    #dmm.search_dmm(('star','600'))
    #for mora in dmm.MORAS:
    #    print("Getting %s ... " % mora, end="")
    #    a = dmm.get_actresses(mora)
    #    a = dmm.get_makers(mora)
    #    print("Got %d" % len(a))

    # dmm.get_works( dmm.DOMAIN[1], 45276, 30, callback=cb )
    # dmm.get_works( dmm.DOMAIN[0], 1509, 10, callback=cb )
    # dmm.get_works( dmm.DOMAIN[1], 4469, 10, callback=cb )
    # print( dmm.get_related( 'digital/videoa', '1sdde00308' ) )
    # print( dmm.get_work_page( 'mono/dvd', '1sdde308' ) )
        
    # print( sod )
    # print( len(sod) )

    # rct = dmm.get_work_page( '45371' )
    # wnz = dmm.get_work_page( '6304' )
    # kv = dmm.get_work_page('46283')
