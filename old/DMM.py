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

        id_base = ( r'^(?:h_)?(?:\d+)?', r'((?:d1)?[a-z]+(?:3d)?[a-z]*)', r'(\d+)([a-z]+|(?:-_)\d)?$' )

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
