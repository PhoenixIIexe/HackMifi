from flask import Flask, render_template, request

app = Flask(__name__)


@app.route('/')
def index():
    params = {
    }
    return render_template('map_input.html', **params)


@app.route('/map_output', methods=['POST'])
def map_output():
    file = request.files['file']
    file.save('uploads/' + file.filename)

    return render_template('map_output.html')


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5001)
