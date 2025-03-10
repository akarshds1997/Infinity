from flask import Flask, request, render_template
from flask_basicauth import BasicAuth

app = Flask(__name__)

# Secure with Basic Auth
app.config['BASIC_AUTH_USERNAME'] = 'Infinity'   # Change username
app.config['BASIC_AUTH_PASSWORD'] = 'MvEmJsUnP'  # Change password
app.config['BASIC_AUTH_FORCE'] = True

basic_auth = BasicAuth(app)

@app.route('/')
@basic_auth.required
def run_python():
    return "Python code is running when this page loads!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
