from Ossetic import app
from flask import render_template, request, redirect, url_for
from Ossetic.models import Languages
from Ossetic.supplement import Amend, Check

@app.route('/dict', methods=['GET', 'POST'])
@app.route('/dict/<string:query>', methods=['GET', 'POST'])
@app.route('/<string:en>/dict', methods=['GET', 'POST'])
@app.route('/<string:en>/dict/<string:query>', methods=['GET', 'POST'])
def search(query='', en=''):
    Check.update()
    if request.method == 'GET':
        if en == 'en':
            return render_template("search_en.html",
                               query=query,
                               Languages=Languages)
        return render_template('search.html',
                               query=query,
                               Languages=Languages
                               )
    if request.method == 'POST':
        query = request.form.get('query_text')
        param = request.form.get('query_area')
        langs = ','.join(request.form.to_dict(flat=False).get('languages', 1))
        if request.form.get('full/sub'):
            type = 'full'
        else:
            type = 'sub'
        if request.form.get('diacritics'):
            lengths = 'l'
        else:
            lengths = 'nl'
        query = query.replace('=', '-')
        return redirect(url_for('results', query=query, param=param, type=type, lengths=lengths, langs=langs, en=en))