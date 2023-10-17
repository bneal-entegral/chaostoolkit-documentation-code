from datetime import date, datetime
import os
import logging

from astral import Astral
import cherrypy
from cherrypy.process.plugins import PIDFile
import cherrypy_cors
import pytz
import json


class AstralController:
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def get_sunset(self, city_name):
        logging.error("let's go")
        """
        Compute sunrise and sunset for the given city.
        """
        a = Astral()
        a.solar_depression = 'civil'

        try:
            city = a[city_name]
        except KeyError:
            return {"error": "unknown city"}

        tz = pytz.timezone(city.timezone)

        sun = city.sun(date=date.today(), local=False)
        result = {}
        for k, v in sun.items():
            if isinstance(v, datetime):
                result[k] = v.astimezone(tz).isoformat()
            else:
                result[k] = v
        
        return result

def jsonify_error(status, message, traceback, version): \
        # pylint: disable=unused-argument

    """JSONify all CherryPy error responses (created by raising the
    cherrypy.HTTPError exception)
    """

    cherrypy.response.headers['Content-Type'] = 'application/json'
    response_body = json.dumps(
        {
            'error': {
                'http_status': status,
                'message': message,
            }
        })

    cherrypy.response.status = status

    return response_body

def run():
    cherrypy_cors.install()

    cur_dir = os.path.abspath(os.path.dirname(__file__))

    dispatcher = cherrypy.dispatch.RoutesDispatcher()

    dispatcher.connect(name='city',
                       route='/city/{city_name}',
                       action='get_sunset',
                       controller=AstralController(),
                       conditions={'method': ['GET']})
    
    config = {
        '/': {
            'request.dispatch': dispatcher,
            'error_page.default': jsonify_error,
            'cors.expose.on': True,
            'tools.auth_basic.on': False,
            #'tools.auth_basic.realm': 'localhost',
            #'tools.auth_basic.checkpassword': validate_password,
        },
    }
    
    cherrypy.tree.mount(root=None, config=config)
    
    cherrypy.config.update({
        'request.dispatch': dispatcher,
        "environment": "production",
        "log.screen": True,
        "server.socket_port": 8443,
        "server.ssl_module": "builtin",
        'cors.expose.on': True,
        "server.ssl_private_key": os.path.join(cur_dir, "key.pem"),
        "server.ssl_certificate": os.path.join(cur_dir, "cert.pem")
    })

    PIDFile(cherrypy.engine, 'astre.pid').subscribe()

    cherrypy.engine.start()
    cherrypy.engine.block()


if __name__ == '__main__':
    run()
