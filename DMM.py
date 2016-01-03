import requests, re
from bs4 import BeautifulSoup

from datetime import timedelta

class DMM:
    """Website as an object"""

    MORAS = [ c.strip()+v for c in ' kstnhmr' for v in 'aiueo']
    MORAS.extend(['ya','yu','yo','wa','wo','nn'])

    D_SMALLTMB = 'd-boxpicdata d-smalltmb' 
    L_PAGE = 'list-boxcaptside list-boxpagenation'
    D_PAGE = 'd-boxcaptside d-boxpagenation'

    def get_soup( self, domain, page ):
        """Get page as a BeautifulSoup."""
        
        DOM = ( "digital/videoa/-/", "mono/dvd/-/", "" )
        r = requests.get( 'http://www.dmm.co.jp/' + DOM[domain] + page )
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

    def get_pagenum( self, a ):
        """Get page number from <a> tag href."""
        pgn = re.compile(r'/page=(\d+)')
        try:
            return int(pgn.search(a.get('href')).group(1))
        except AttributeError:
            return 0

    def get_count( self, domain, article, a_id ):
        """Get total work count of given ID"""
        query = "list/=/article=%s/id=%d/" % ( article, a_id )

        soup = self.get_soup( domain, query )
        info = soup.find('div',class_=self.L_PAGE)
        if info: return int(re.match(r'(\d+)',info.p.string).group(1))
        return 0
                    
    def get_title( self, article, a_id ):
        """Get title of given ID"""
        query = "list/=/article=%s/id=%s/" % ( article, a_id )

        title = []

        for domain in ( 0, 1 ):
            soup = self.get_soup( domain, query )
            t = soup.title.string.split(' - ')[:-2]
            if len(t) == 1:
                if article == 'actress':
                    t[0] = re.sub( r'\([^)]*\)', '', t[0] )
                title.append(t[0])
            else:
                title.append(' - '.join(t))

        return title[0]

    def get_sample_vid_url( self, cid ):
        """Get URL of sample video given ID"""
        query = "service/-/flash/=/cid=%s/" % cid

        flv = re.compile(r'flashvars.(\w+) = "?(\w+)"?')

        flashvars = {}

        soup = self.get_soup( 2, query )

        for s in soup.find_all('script',string=True):
            for fv in flv.finditer(s.string): flashvars[fv.group(1)] = fv.group(2)

        ncid = flashvars['cid']

        return "%s/%s/%s/%s_%s_w.mp4" % (ncid[0],ncid[0:3],ncid,ncid,'sm')

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

        soup = self.get_soup( 0, 'genre/' )

        for section in soup.find_all('div', id=re.compile('^list')):
            category = section.div.string
            if category == "おすすめジャンル": continue
            if category == "タイプ": category = "ＡＶ女優タイプ"

            tags.extend([ tag(link,category) for link in section.ul('a') ])

        soup = self.get_soup( 1, 'genre/' )

        for section in soup.find_all('table', class_='sect02'):
            category = section.get('summary')
            tags.extend([ tag(link,category) for link in section('a') ])

        return list(filter(None.__ne__, tags))

    def get_makers( self, mora, callback=print ):

        search = 'maker/=/keyword=%s/' % mora 

        soup = self.get_soup( 0, search )

        for maker in soup.find_all('div', class_=self.D_SMALLTMB):
            _id = self.get_id(maker.a)
            if not _id: continue
            name = maker.find(class_='d-ttllarge').string
            roma = self.get_filename(maker.img)
            desc = self.get_string(maker.p).strip()

            callback({ '_id': _id, 'name': name, 'roma': roma, 'description': desc })

        soup = self.get_soup( 1, search )

        for maker in soup.find_all('td',class_='w50'):
            _id = self.get_id(maker.a)
            if not _id: continue
            name = maker.img.get('alt')
            roma = self.get_filename(maker.img)
            desc = maker.br.string.strip()
            desc = re.sub('〜','～',desc)

            callback({ '_id': _id, 'name': name, 'roma': roma, 'description': desc })

        extra_base = soup.find(class_='list-table mg-t12')
        if extra_base:
            for maker in extra_base('a'):
                _id = self.get_id(maker)
                if not _id: continue
                callback({ '_id': _id, 'name': maker.string })

    def get_actresses( self, mora, callback=print ):

        search = 'actress/=/keyword=%s/sort=count/' % mora

        soup = self.get_soup( 0, search )

        totals = soup.find('div',class_=self.L_PAGE+' group')
        count = [ int(x) for x in re.findall(r'\d+', totals.p.string) ]
        cur_page = count[4]
        
        while cur_page <= count[3]:
            for actress in soup.find('ul',class_='d-item act-box-100 group')('a'):
                name = actress.img.get('alt')
                roma = self.get_filename(actress.img)
                furi = actress.span.string 

                callback( { '_id': self.get_id(actress), 'name': name, 'roma': roma, 'furi': furi } )
        
            cur_page += 1
            soup = self.get_soup( 0, search + "page=%d/" % cur_page )

        soup = self.get_soup( 1, search )

        page_nums = soup.find('div',class_=self.D_PAGE)

        num_pages = max( [ self.get_pagenum(p) for p in page_nums('a') ] )
        if num_pages == 0 and page_nums.span : num_pages = 1

        cur_page = 1

        while cur_page <= num_pages:
            for actress in soup.find('ul',class_='act-box-100 group mg-b20')('a'):
                name = actress.string
                name = re.sub('〜','～',name)
                roma = self.get_filename(actress.img)

                callback( { '_id': self.get_id(actress), 'name': name, 'roma': roma } )

            cur_page += 1
            soup = self.get_soup( 1, search + "page=%d/" % cur_page )

    def get_works( self, domain, m_id, count, page=1, callback=print ):

        def get_rss( s, domain, path ):
            RSS = ( "digital/videoa/-/list/rss/=", "mono/dvd/-/list/=/rss=create/" )

            r = s.get( 'http://www.dmm.co.jp/' + RSS[domain] + path )
            r.encoding = 'utf-8'
            print( r.elapsed, end="\r" )
            return BeautifulSoup( r.text, 'xml' )

        search = "/article=maker/sort=release_date/id=%d/" % m_id

        works = []
        worksession = requests.Session()

        while len(works) < count:
            soup = get_rss( worksession, domain, search + "page=%d/" % page )
            for item in soup('item'): works.append( callback( self.parse_work(item) ) )
            page += 1

        return works

    def parse_work( self, item ):

        idc = re.compile(r'article=(\w+)/id=(\d+)')
        properties = ( 'title', 'description', 'link', 'package', 'date' )

        work = { 'keywords': [], 'actresses': [] }

        for p in properties: work[p] = item.find(p).string

        work['cid'] = re.search(r'cid=(\w+)', work['link']).group(1)
        work['pid'] = re.search(r'/(video|adult)/(\w+)', work['package']).group(2)
        work['released_date'] = work['date'].split('T')[0]

        content = BeautifulSoup( item.encoded.string, 'html.parser' )

        for info in content('strong'):
            if '分' in info.next_sibling:
                dur_mins = int( info.next_sibling.strip('分') )
                work['runtime'] = timedelta( minutes = dur_mins )
                break

        for link in content('a'):
            l = idc.search( link.get('href') )
            if not l: continue
            if l.group(1) == 'keyword':
                work['keywords'].append( l.group(2) )
            elif l.group(1) == 'actress':
                work['actresses'].append( l.group(2) )
            else:
                work[l.group(1)] = l.group(2)

        work['display_id'] = self.rename( work['pid'], work['maker'] )

        return work

    def search_dmm( self, terms ):

        soup = self.get_soup( 2, 'search/=/searchstr=%s/' % '%20'.join(terms) )

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

    dmm.search_dmm(('star','600'))
    #for mora in dmm.MORAS:
    #    print("Getting %s ... " % mora, end="")
    #    a = dmm.get_actresses(mora)
    #    a = dmm.get_makers(mora)
    #    print("Got %d" % len(a))
    # a = dmm.get_series('a')
    # print(a)
    # print(len(a))

    #def cb( v ): print( v )
        # print( "%s %s" % ( v['cid'], v['pid'] ) )

    # dmm.get_works( 1, 45276, 30, callback=cb )
    # dmm.get_works( 0, 1509, 10, callback=cb )
    # dmm.get_works( 1, 4469, 10, callback=cb )
    # print( dmm.get_sample_vid_url( '1sdde00428' ) )
    # print( sod )
    # print( len(sod) )

    # rct = dmm.get_work_page( '45371' )
    # wnz = dmm.get_work_page( '6304' )
    # print([ w['cid'] for w in mkr[0] ])
    # print([ w['cid'] for w in mkr[1] ])

    # kv = dmm.get_work_page('46283')
