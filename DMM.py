import requests, re
from bs4 import BeautifulSoup

class DMM:
        """Website as an object"""

        MORAS = [ c.strip()+v for c in ' kstnhmr' for v in 'aiueo']
        MORAS.extend(['ya','yu','yo','wa','wo','nn'])

        D_SMALLTMB = 'd-boxpicdata d-smalltmb' 
        L_PAGE = 'list-boxcaptside list-boxpagenation'

        def get_soup( self, domain, page ):
                """Get page as a BeautifulSoup."""
                
                DOM = ( "digital/videoa/-/", "mono/dvd/-/" )
                r = requests.get( 'http://www.dmm.co.jp/' + DOM[domain] + page )
                return BeautifulSoup( r.text, 'html.parser' )

        def get_id( self, a ):
                """Get ID from <a> tag href."""
                rid = re.compile(r'/id=(\d+)')
                try:
                        return rid.search(a.get('href')).group(1)
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
                        return None

        def insert_id( self, dic, key, data ):
                """Insert data into dictionary"""
                if not key: return None
                if key not in dic:
                        dic[key] = data
                elif dic[key] != data:
                        print("Mismatch found with ID %s:" % (key))
                        print(i_dict[key])
                        print(data)

        def get_count( self, article, a_id ):
                """Get total work count"""
                query = 'list/=/article=' + article + '/id=' + a_id + '/'

                def get_p(domain):
                        soup = self.get_soup( domain, query )
                        info = soup.find('div',class_=self.L_PAGE)
                        if info: return int(re.match(r'(\d+)',info.p.string).group(1))
                        return 0
                        
                return [ get_p(d) for d in ( 0, 1 ) ]


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
                        for maker in extra_base.find_all('a'):
                                self.insert_id( makers, self.get_id(maker.a), ( maker.string, '', '' ) )

                return makers

        def get_makers_by_tag( self, t_id ):

                search = 'maker/=/article=keyword/id=' + t_id + '/'
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
                        for actress in soup.find('ul',class_='d-item act-box-100 group').find_all('a'):
                                name = actress.img.get('alt')
                                roma = self.get_filename(actress.img)
                                # furi = actress.span.string 

                                self.insert_id( actresses, self.get_id(actress), ( name, roma ) )
                        
                        cur_page += 1
                        soup = self.get_soup( 0, search + "page=%d/" % cur_page )

                soup = self.get_soup( 1, search )

                num_pages = self.get_pagenum(soup.find('li',class_='terminal').a)
                cur_page = 1

                while cur_page <= num_pages:
                        for actress in soup.find('ul',class_='act-box-100 group mg-b20').find_all('a'):
                                name = actress.string
                                roma = self.get_filename(actress.img)

                                self.insert_id( actresses, self.get_id(actress), ( name, roma ) )

                        cur_page += 1
                        soup = self.get_soup( 1, search + "page=%d/" % cur_page )

                return actresses

        def get_series( self, mora ):

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

        def get_work( self, item ):

                idc = re.compile(r'article=(\w+)/id=(\d+)')
                properties = ( 'title', 'description', 'link', 'package', 'date' )

                work = { 'tags': [], 'actresses': [] }

                for p in properties: self.insert_id( work, p, item.find(p).string )

                work['cid'] = re.search(r'cid=(\w+)', work['link']).group(1)

                content = BeautifulSoup( item.encoded.string, 'html.parser' )

                for info in content('strong'):
                    if '分' in info.next_sibling:
                        work['runtime'] = int( info.next_sibling.strip('分') )
                        break

                for link in content('a'):
                        l = idc.search( link.get('href') )
                        if not l: continue
                        if l.group(1) == 'keyword':
                                work['tags'].append(l.group(2))
                        elif l.group(1) == 'actress':
                                work['actresses'].append(l.group(2))
                        else:
                                self.insert_id( work, l.group(1), l.group(2) )

                return work

        def get_work_page( self, m_id ):

                def get_rss( domain, path ):
                        RSS = ( "digital/videoa/-/list/rss/=", "mono/dvd/-/list/=/rss=create/" )

                        r = requests.get( 'http://www.dmm.co.jp/' + RSS[domain] + path )
                        r.encoding = 'utf-8'
                        return BeautifulSoup( r.text, 'xml' )

                step = 125
                search = "/article=maker/sort=release_date/id=%s/limit=%d/" % ( m_id, step )

                counts = self.get_count( 'maker', m_id )

                num_pages = [ round(p/step)+1 for p in counts ]

                cur_page = 1
        
                works = []

                while cur_page <= num_pages[0]:
                        soup = get_rss( 0, search + "page=%d/" % cur_page )
                        works.extend([ self.get_work(item) for item in soup('item') ])
                        cur_page += 1

                return works

if __name__ == "__main__":
        dmm = DMM()
        # a = dmm.get_tags()
        # dmm.get_makers(mora) for mora in dmm.MORAS
        # a = dmm.get_actresses('a')
        # a = dmm.get_series('a')
        # print(a)
        # print(len(a))

        # sod = dmm.get_work_page( '45276' )
        # print( sod )
        # print( len(sod) )

        kv = dmm.get_work_page('46283')
        print(kv)
        # print(len(kv))
