import requests, re
from bs4 import BeautifulSoup

class DMM:
    """Website as an object"""

    MORAS = [ c.strip()+v for c in ' kstnhmr' for v in 'aiueo']
    MORAS.extend(['ya','yu','yo','wa','wo','nn'])

    D_SMALLTMB = 'd-boxpicdata d-smalltmb' 
    L_PAGE = 'list-boxcaptside list-boxpagenation'
    D_PAGE = 'd-boxcaptside d-boxpagenation'

    def get_soup( self, domain, page ):
        """Get page as a BeautifulSoup."""
        
        DOM = ( "digital/videoa/-/", "mono/dvd/-/" )
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

    def insert_id( self, dic, key, data ):
        """Insert data into dictionary"""
        if not key: return None
        if key not in dic:
            dic[key] = data
        elif dic[key] != data:
            print("Mismatch found with ID %s:" % (key))
            print(dic[key])
            print(data)

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

    def get_tags( self ):
        """Get tags from DMM genres page"""
        tags = {}

        soup = self.get_soup( 0, 'genre/' )

        for section in soup.find_all('div', id=re.compile('^list')):
            category = section.div.string
            if category == "おすすめジャンル": continue
            if category == "タイプ": category = "ＡＶ女優タイプ"

            for link in section.ul('a'):
                self.insert_id( tags, self.get_id(link), ( link.string, category ) )

        soup = self.get_soup( 1, 'genre/' )

        for section in soup.find_all('table', class_='sect02'):
            category = section.get('summary')
            for link in section('a'):
                self.insert_id( tags, self.get_id(link), ( link.string, category ) )

        return tags

    def get_makers( self, mora ):

        search = 'maker/=/keyword=' + mora + '/' 
        makers = {}

        soup = self.get_soup( 0, search )

        for maker in soup.find_all('div', class_=self.D_SMALLTMB):
            name = maker.find(class_='d-ttllarge').string
            roma = self.get_filename(maker.img)
            desc = self.get_string(maker.p).strip()

            self.insert_id( makers, self.get_id(maker.a), ( name, roma, desc ) )

        soup = self.get_soup( 1, search )

        for maker in soup.find_all('td',class_='w50'):
            name = maker.img.get('alt')
            roma = self.get_filename(maker.img)
            desc = maker.br.string.strip()
            desc = re.sub('〜','～',desc)

            self.insert_id( makers, self.get_id(maker.a), ( name, roma, desc ) )

        extra_base = soup.find(class_='list-table mg-t12')
        if extra_base:
            for maker in extra_base('a'):
                self.insert_id( makers, self.get_id(maker.a), ( maker.string, '', '' ) )

        return makers

    def get_makers_by_tag( self, t_id ):

        search = "maker/=/article=keyword/id=%d" % t_id
        soup = self.get_soup( 1, search )
        return [ self.get_id(m.a) for m in soup.find_all('div',class_=self.D_SMALLTMB) ]

    def get_actresses( self, mora ):

        search = 'actress/=/keyword=' + mora + '/sort=count/' 
        actresses = {}

        soup = self.get_soup( 0, search )

        totals = soup.find('div',class_=self.L_PAGE+' group')
        count = [ int(x) for x in re.findall(r'\d+', totals.p.string) ]
        cur_page = count[4]
        
        while cur_page <= count[3]:
            for actress in soup.find('ul',class_='d-item act-box-100 group')('a'):
                name = actress.img.get('alt')
                roma = self.get_filename(actress.img)
                # furi = actress.span.string 

                self.insert_id( actresses, self.get_id(actress), ( name, roma ) )
        
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

                self.insert_id( actresses, self.get_id(actress), ( name, roma ) )

            cur_page += 1
            soup = self.get_soup( 1, search + "page=%d/" % cur_page )

        return actresses

    def get_works( self, domain, m_id, count ):

        def get_rss( s, domain, path ):
            RSS = ( "digital/videoa/-/list/rss/=", "mono/dvd/-/list/=/rss=create/" )

            r = s.get( 'http://www.dmm.co.jp/' + RSS[domain] + path )
            r.encoding = 'utf-8'
            # print(r.elapsed)
            return BeautifulSoup( r.text, 'xml' )

        search = "/article=maker/sort=release_date/id=%d/" % m_id

        works = []
        worksession = requests.Session()

        page = 1
        while len(works) < count:
            soup = get_rss( worksession, domain, search + "page=%d/" % page )
            works.extend( [ self.parse_work(item) for item in soup('item') ] )
            page += 1

        return works

    def get_series_list( self, mora ):

        search = 'series/=/keyword=' + mora + '/sort=ruby/' 
        series = {}

        soup = self.get_soup( 0, search )

        # soup.find('div',class_='list-boxcaptside list-boxpagenation group').p.string
        # soup.find('li',class_='terminal')

        for ser in soup.find_all('div',class_='tx-work mg-b12 left'):
            strs = [ s for s in ser.stripped_strings ]
            if len(strs) == 1: strs.append('')

            self.insert_id( series, self.get_id(ser.a), tuple(strs) )

        # soup = self.get_soup( 1, search )

        # soup.find('li',class_='terminal')

        return series

    def parse_work( self, item ):

        idc = re.compile(r'article=(\w+)/id=(\d+)')
        properties = ( 'title', 'description', 'link', 'package', 'date' )

        work = { 'tags': [], 'actresses': [] }

        for p in properties: self.insert_id( work, p, item.find(p).string )

        work['cid'] = re.search(r'cid=(\w+)', work['link']).group(1)
        work['date'] = work['date'].split('T')[0]

        content = BeautifulSoup( item.encoded.string, 'html.parser' )

        for info in content('strong'):
            if '分' in info.next_sibling:
                work['runtime'] = int( info.next_sibling.strip('分') )
                break

        for link in content('a'):
            l = idc.search( link.get('href') )
            if not l: continue
            if l.group(1) == 'keyword':
                work['tags'].append( l.group(2) )
            elif l.group(1) == 'actress':
                work['actresses'].append( l.group(2) )
            else:
                self.insert_id( work, l.group(1), l.group(2) )

        return work

if __name__ == "__main__":
    dmm = DMM()
    # a = dmm.get_tags()

    for mora in dmm.MORAS:
        print("Getting %s ... " % mora, end="")
        # a = dmm.get_actresses(mora)
        # a = dmm.get_makers(mora)
        print("Got %d" % len(a))
    # a = dmm.get_series('a')
    # print(a)
    # print(len(a))

    # sod = dmm.get_work_page( '45276' )
    # print( sod )
    # print( len(sod) )

    # rct = dmm.get_work_page( '45371' )
    # wnz = dmm.get_work_page( '6304' )
    # print([ w['cid'] for w in mkr[0] ])
    # print([ w['cid'] for w in mkr[1] ])

    # kv = dmm.get_work_page('46283')
