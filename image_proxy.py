import http.server, requests
from urllib.parse import urlparse, parse_qs

def get_img( path ):
    DOM = ( 'digital/video', 'mono/movie/adult' )

    p = urlparse(path)

    l = p.path

    if l == 'favicon.ico': return None

    s = 'pt'
    d = 0

    if '=' in p.query:
        qs = parse_qs(p.query)
        if 'd' in qs: d = int(qs['d'][0])
        if 's' in qs: s = qs['s'][0]
    elif p.query:
        s = p.query

    q = "http://pics.dmm.co.jp/%s/%s/%s%s.jpg" % ( DOM[d], l, l, s )
    r = requests.get( q, allow_redirects=False )

    if r.status_code == 200:
        return r.content
    else:
        return None

def empty(s):
    s.send_header("Content-type", "text/html")
    s.end_headers()
    page = "<html><head><title>t</title></head><body>%s</body></html>" % s.path
    s.wfile.write(page.encode())

class ImgHandler( http.server.SimpleHTTPRequestHandler ):

    def do_HEAD(s):
        s.send_response(200)
        s.send_header("Content-type", "text/html")
        s.end_headers()

    def do_GET(s):
        s.send_response(200)
        s.send_header("Content-type", "image/jpeg")
        s.end_headers()

        img = get_img(s.path)
        s.wfile.write( img if img else b'\xff\xd8\xff\xd9' )

def run(port=3000):
    httpd = http.server.HTTPServer( ( '', port ), ImgHandler )
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()

if __name__ == '__main__':
    run()
