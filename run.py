# -*- coding: utf-8 -*-
from app import app
from flask_debugtoolbar import DebugToolbarExtension

if __name__ == '__main__':
    app.debug = True
    toolbar = DebugToolbarExtension(app)
    app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
    app.run(port=8100)
