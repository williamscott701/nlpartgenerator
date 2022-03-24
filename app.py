from flask import (
    Flask, 
    redirect, 
    render_template, 
    request, 
    flash, 
    send_from_directory,
    make_response,
    jsonify,
    abort
)
from src.text2art.utils import (
    get_value, 
    queue, 
    setup, 
)

setup()

app = Flask(__name__)
app.config['SECRET_KEY'] = get_value("config.yaml", 'SECRET_KEY')
QUANTITY = 6

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/generate', methods=['POST'])
def generate_art():
    name = request.form['name']
    mail_address = request.form['email']
    prompts = request.form['prompts'].lower()
    aspect = request.form['aspect']
    quality = request.form['quality']
    publish = True if request.form.get('publish') == 1 else False

    queue_no = queue(name, mail_address, prompts, aspect, quality, publish)
    flash(f'Your Art is being generated. Queue {queue_no}. Time estimated {queue_no*4}h', 'success')
    return redirect('/')

@app.route('/images/<path:filename>')
def send_images(filename):
    return send_from_directory("./data/output/", filename, as_attachment=True)

# @app.route('/images/<filename>', methods=['GET'])
# def send_images(filename):
#     return send_from_directory('./', filename)

# @app.route('/load', methods=['GET'])
# def load():
#     if request.args:
#         counter = int(request.args.get('counter'))
#         img_detail = get_img_detail(counter, QUANTITY)
#         return make_response(jsonify(img_detail))
#     return abort(404)


if __name__ == '__main__':
    app.run(debug=True)
