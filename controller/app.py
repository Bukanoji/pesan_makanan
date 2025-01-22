from flask import Flask
from flask import render_template

app = flask(__name__)

@app.route('/')
@app.route('/<nama>')
def index(nama = None):
    nama = 'admin'
    return render_template('index.html', user = nama)

if __name__ == '__main__':
    app.run()