import http.server
import requests
import os

def get_dmm( sub, path ):

    r = requests.get( "http://%s.dmm.co.jp/%s" % ( sub, path ), allow_redirects=False )

    return r.content if r.status_code == 200 else None

class DMMHandler( http.server.SimpleHTTPRequestHandler ):

    def do_HEAD(s):
        s.send_response(200)
        s.send_header("Content-type", "text/html")
        s.end_headers()

    def do_GET(s):
        rq = None

        if s.path.endswith('.jpg'):
            ctype = 'image/jpeg'
            rq = get_dmm( 'pics', s.path )

        elif s.path.endswith('.mp4'):
            ctype = 'video/mp4'
            rq = get_dmm( 'cc3001', s.path )

        if rq:
            s.send_response(200)
            s.send_header('Content-type', ctype)
            s.end_headers()
            s.wfile.write( rq )
        else:
            s.send_error(404)

def run(port=5000):
    port = os.getenv("PORT")
    if port: port = int(port)

    httpd = http.server.HTTPServer( ( '', port ), DMMHandler )
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()

if __name__ == '__main__':
    run()
