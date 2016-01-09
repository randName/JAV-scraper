import http.server, requests
from urllib.parse import urlparse, parse_qs

def get_img( path ):

    r = requests.get( "http://pics.dmm.co.jp/" + path, allow_redirects=False )

    return r.content if r.status_code == 200 else None

def empty(s):
    s.send_header("Content-type", "text/html")
    s.end_headers()
    page = "<html><head><title>t</title></head><body>%s</body></html>" % s.path
    s.wfile.write(page.encode())

class DMMHandler( http.server.SimpleHTTPRequestHandler ):

    def do_HEAD(s):
        s.send_response(200)
        s.send_header("Content-type", "text/html")
        s.end_headers()

    def do_GET(s):
        s.send_response(200)

        if '.jpg' in s.path:
            s.send_header("Content-type", "image/jpeg")
            s.end_headers()

            img = get_img( s.path )
            s.wfile.write( img if img else b'\xff\xd8\xff\xd9' )

        elif '.mp4' in s.path:
            s.send_header("Content-type", "video/mp4")
            s.end_headers()

        else:
            s.send_header("Content-type", "text/html")
            s.end_headers()

def run(port=3000):
    httpd = http.server.HTTPServer( ( '', port ), DMMHandler )
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()

if __name__ == '__main__':
    run()
