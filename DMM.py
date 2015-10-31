import requests, re
from bs4 import BeautifulSoup

class DMM:
	"""Website as an object"""

	URL = "http://www.dmm.co.jp/"
	DOM = ( "digital/videoa/-/", "mono/dvd/-/" )

	MORAS = [ c.strip(' ')+v for c in ' kstnhmr' for v in 'aiueo']
	MORAS.extend(['ya','yu','yo','wa','wo','nn'])


	def get_soup( self, url ):
		r = requests.get( url )
		return BeautifulSoup( r.text, 'html.parser' )

	def get_id( self, a ):
		rid = re.compile(r'/id=(\d+)')
		try:
			return rid.search(a.get('href')).group(1)
		except AttributeError:
			return None

	def get_filename( self, img ):
		name = img.get('src').rsplit('/',1)[-1].split('.')
		if name[0] == 'noimage':
			return None
		else:
			return name[0]

	def get_tags( self ):

		tags = []
				
		soup = self.get_soup( self.URL + self.DOM[0] + 'genre/' )

		for section in soup.find_all('div', id=re.compile('^list')):
			if section.get('id') == "list01": continue
			for link in section('a'): 
				t_id = self.get_id(link)
				if t_id: tags.append( ( t_id, link.string ) )

		soup = self.get_soup( self.URL + self.DOM[1] + 'genre/' )

		for section in soup.find_all('table', class_='sect02'):
			for link in section('a'): 
				t_id = self.get_id(link)
				if t_id: tags.append( ( t_id, link.string ) )

		return list(set(tags))

	def get_makers( self, mora ):

		search = 'maker/=/keyword=' + mora + '/' 
		makers = []

		soup = self.get_soup( self.URL + self.DOM[0] + search )

		for maker in soup.find_all('div', class_='d-boxpicdata d-smalltmb'):
			name = maker.find(class_='d-ttllarge').string

			# roma = self.get_filename(maker.img)
			# if maker.p: desc = maker.p.string 

			makers.append( ( self.get_id(maker.a), name ) )

		soup = self.get_soup( self.URL + self.DOM[1] + search )

		for maker in soup.find(class_='list-table mg-t12').find_all('a'):
			makers.append( ( self.get_id(maker), maker.string ) )

		for maker in soup.find_all('td',class_='w50'):
			name = maker.img.get('alt')
			
			# roma = self.get_filename(maker.img)
			# desc = maker.br.string

			makers.append( ( self.get_id(maker.a), name ) )

		return list(set(makers))

	def get_actresses( self, mora ):

		search = 'actress/=/keyword=' + mora + '/' 
		actresses = []

		soup = self.get_soup( self.URL + self.DOM[0] + search )

		for actress in soup.find('ul',class_='d-item act-box-100 group').find_all('a'):
			name = actress.img.get('alt')
			roma = self.get_filename(actress.img)
			# furi = actress.span.string 

			actresses.append( ( self.get_id(actress), name, roma ) )

		soup = self.get_soup( self.URL + self.DOM[1] + search )

		for actress in soup.find('ul',class_='act-box-100 group mg-b20').find_all('a'):
			name = actress.string
			roma = self.get_filename(actress.img)

			actresses.append( ( self.get_id(actress), name, roma ) )

		return list(set(actresses))

if __name__ == "__main__":
	dmm = DMM()
	a = dmm.get_makers('a')
	print(a)
	print(len(a))
