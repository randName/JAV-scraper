import requests, re
from bs4 import BeautifulSoup

class DMM:
	"""Website as an object"""

	URL = "http://www.dmm.co.jp/"
	DOM = ( "digital/videoa/-/", "mono/dvd/-/" )

	MORAS = [ c.strip(' ')+v for c in ' kstnhmr' for v in 'aiueo']
	MORAS.extend(['ya','yu','yo','wa','wo','nn'])

	def get_soup( self, url ):
		"""Get URL as a BeautifulSoup."""
		r = requests.get( url )
		return BeautifulSoup( r.text, 'html.parser' )

	def get_id( self, a ):
		"""Get ID from <a> tag href."""
		rid = re.compile(r'/id=(\d+)')
		try:
			return rid.search(a.get('href')).group(1)
		except AttributeError:
			return None

	def get_string_if_can( self, tag ):
		"""Returns empty string if attribute does not exist."""
		try:
			return tag.string
		except AttributeError:
			return ''

	def get_filename( self, img ):
		"""Get filename from <img> tag src."""
		name = img.get('src').rsplit('/',1)[-1].split('.')
		if name[0] == 'noimage':
			return None
		else:
			return name[0]

	def get_pagenum( self, a ):
		"""Get page number from <a> tag href."""
		pgn = re.compile(r'/page=(\d+)')
		try:
			return int(pgn.search(a.get('href')).group(1))
		except AttributeError:
			return None

	def insert_id( self, i_dict, key, data ):
		"""Insert data into dictionary"""
		if not key: return None
		if key not in i_dict:
			i_dict[key] = data
		elif i_dict[key] != data:
			print("Mismatch found with ID %s:" % (key))
			print(i_dict[key])
			print(data)

	def get_tags( self ):
		"""Get tags from DMM genres page"""
		tags = {}

		soup = self.get_soup( self.URL + self.DOM[0] + 'genre/' )

		for section in soup.find_all('div', id=re.compile('^list')):
			category = section.div.string
			if category == "おすすめジャンル": continue
			if category == "タイプ": category = "ＡＶ女優タイプ"

			for link in section.ul('a'):
				self.insert_id( tags, self.get_id(link), ( link.string, category ) )

		soup = self.get_soup( self.URL + self.DOM[1] + 'genre/' )

		for section in soup.find_all('table', class_='sect02'):
			category = section.get('summary')
			for link in section('a'):
				self.insert_id( tags, self.get_id(link), ( link.string, category ) )

		return tags

	def get_makers( self, mora ):

		search = 'maker/=/keyword=' + mora + '/' 
		makers = {}

		soup = self.get_soup( self.URL + self.DOM[0] + search )

		for maker in soup.find_all('div', class_='d-boxpicdata d-smalltmb'):
			name = maker.find(class_='d-ttllarge').string
			roma = self.get_filename(maker.img)
			desc = self.get_string_if_can(maker.p).strip()

			self.insert_id( makers, self.get_id(maker.a), ( name, roma, desc ) )

		soup = self.get_soup( self.URL + self.DOM[1] + search )

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

	def get_actresses( self, mora ):

		search = 'actress/=/keyword=' + mora + '/sort=count/' 
		actresses = {}

		soup = self.get_soup( self.URL + self.DOM[0] + search )

		totals = soup.find('div',class_='list-boxcaptside list-boxpagenation group')
		count = [ int(x) for x in re.findall(r'\d+', totals.p.string) ]
		cur_page = count[4]
		
		while cur_page <= count[3]:
			for actress in soup.find('ul',class_='d-item act-box-100 group').find_all('a'):
				name = actress.img.get('alt')
				roma = self.get_filename(actress.img)
				# furi = actress.span.string 

				self.insert_id( actresses, self.get_id(actress), ( name, roma ) )
			
			cur_page += 1
			soup = self.get_soup(self.URL+self.DOM[0]+search + 'page='+str(cur_page)+'/' )

		soup = self.get_soup( self.URL + self.DOM[1] + search )

		num_pages = self.get_pagenum(soup.find('li',class_='terminal').a)
		cur_page = 1

		while cur_page <= num_pages:
			for actress in soup.find('ul',class_='act-box-100 group mg-b20').find_all('a'):
				name = actress.string
				roma = self.get_filename(actress.img)

				self.insert_id( actresses, self.get_id(actress), ( name, roma ) )

			cur_page += 1
			soup = self.get_soup(self.URL+self.DOM[1]+search + 'page='+str(cur_page)+'/' )

		return actresses

	def get_series( self, mora ):

		search = 'series/=/keyword=' + mora + '/sort=ruby/' 
		series = {}

		soup = self.get_soup( self.URL + self.DOM[0] + search )

		# soup.find('div',class_='list-boxcaptside list-boxpagenation group').p.string
		# soup.find('li',class_='terminal')

		for ser in soup.find_all('div',class_='tx-work mg-b12 left'):
			strs = [ s for s in ser.stripped_strings ]
			if len(strs) == 1: strs.append('')

			self.insert_id( series, self.get_id(ser.a), tuple(strs) )

		# soup = self.get_soup( self.URL + self.DOM[1] + search )

		# soup.find('li',class_='terminal')

		return series

if __name__ == "__main__":
	dmm = DMM()
	# a = dmm.get_tags()
	# dmm.get_makers(mora) for mora in dmm.MORAS
	a = dmm.get_actresses('a')
	# a = dmm.get_series('a')
	print(a)
	print(len(a))
