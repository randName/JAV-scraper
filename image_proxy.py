import http.server, requests

def get_img( p, rear='pt' ):
    DOM = ( 'digital/video', '' )

    if '?' in p:
        ps = p.split('?')
        p = ps[0]
        if ps[1]: rear = ps[1]

    q = "http://pics.dmm.co.jp/%s/%s/%s%s.jpg" % ( DOM[0], p, p, rear )
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
