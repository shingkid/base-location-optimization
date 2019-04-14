import os
import time
import zipfile

import pandas as pd

from flask import Flask, request, redirect, url_for, flash, render_template, send_from_directory
from werkzeug.utils import secure_filename

import solve

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'io')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
ALLOWED_EXTENSIONS = set(['zip'])

app = Flask(__name__)
app.config['SECRET_KEY'] = ''


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    return render_template("index.html")


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'zip_file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        file = request.files['zip_file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            zip_ref = zipfile.ZipFile(os.path.join(UPLOAD_FOLDER, filename), 'r')
            zip_ref.extractall(UPLOAD_FOLDER)
            zip_ref.close()
            
            radius = float(request.form['radius'])
            num_cars = request.form['num_cars']

            DATA_DIR = os.path.join(UPLOAD_FOLDER, filename[:-4])
            outfile = os.path.join(UPLOAD_FOLDER, 'sol.csv')
            if num_cars == '':
                num_cars = 15
            optimize(DATA_DIR, radius, int(num_cars), outfile) # TODO: Form input for number of cars
                
    return render_template('index.html')


def optimize(data_dir, radius, num_cars, outfile):
    t0 = time.time()

    data_files = os.listdir(data_dir)
    print("Loading grid specs...")
    grids = pd.read_csv('grid_spec.csv')
    print("Loading distance matrix...")
    # distances = compute_distances()
    distances = pd.read_csv('distances.csv')

    print("Computing adjacency matrix...")
    adj_mat = solve.compute_adj_mat(distances, radius)

    print("Solving minimum bases required...")
    base_list = solve.find_min_bases(adj_mat)

    print("Calculating grids covered by each base...")
    regions = {}
    for i in base_list:
        regions[i] = adj_mat[i-1]

    print("Loading data...")
    df = solve.load_dataset(data_dir, data_files, grids, regions, distances) # Load all data
    worst_days = solve.find_worst_day_by_grid(df, grids)
    wd_incidences = solve.get_worst_day_incidences(df, grids, worst_days)
    mode = wd_incidences.day.mode().values[0]
    df = df[df.day==mode]

    print("Finding overlaps in incidence times...")
    clashes = solve.find_clashes(df)

    print("Solving...")
    solution = solve.allocate(df.spf_base, clashes, num_cars, outfile)

    print("Time taken:", time.time() - t0)

    plot_map(solution)

    return redirect(url_for('allocation_file', filename=outfile))


@app.route('/solution/<filename>')
def allocation_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)


def plot_map(solution):
    print(solution)


if __name__ == "__main__":
    app.run(debug=True)
