from flask import Flask
from datetime import timedelta

app = Flask(__name__)
app.secret_key = 'Mzk3Mw.7phf8aMEbu7emM8XW-MVoooS-Ag'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///abaev.db'
app.config['MAIL_SERVER'] = 'smtp.beget.com'
app.config['MAIL_PORT'] = 2525
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USERNAME'] = 'ossetic@iranic.space'
app.config['MAIL_DEFAULT_SENDER'] = ('Ossetic Language', 'ossetic@iranic.space')
app.config['MAIL_PASSWORD'] = '%TiafM1K'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)

import Ossetic.about, Ossetic.profile, Ossetic.login,\
    Ossetic.search_page, Ossetic.results_page, Ossetic.entry

if __name__ == "__main__":
    app.run(debug=True)