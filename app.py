import os
import os
import time
import zipfile
import re

import pandas as pd

from flask import Flask, request, redirect, url_for, flash, render_template, send_file, jsonify, make_response
from flask_cors import CORS
from werkzeug.utils import secure_filename

import solve
import evaluate

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'io')
if os.path.exists(UPLOAD_FOLDER):
    os.rmdir(UPLOAD_FOLDER)
os.makedirs(UPLOAD_FOLDER)
ALLOWED_EXTENSIONS = set(['zip'])
ALLOWED_EXTENSIONS_2 = set(['csv'])

app = Flask(__name__)
app.config['SECRET_KEY'] = 'aaaa'
CORS(app)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_file_2(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS_2

           
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
        if file and allowed_file_2(file.filename):

            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            
            day = int(re.search(r'\d+', filename).group(0))
            print(day)
            
            radius = float(request.form['radius'])
            num_cars = request.form['num_cars']
            time_varying = request.form.get('time-varying')
            
            DATA_DIR = UPLOAD_FOLDER
            outfile = os.path.join(UPLOAD_FOLDER, 'sol.csv')
            if num_cars == '':
                num_cars = 15
            optimize(DATA_DIR, radius, int(num_cars), outfile, time_varying = time_varying, day = day)
            evaluator(filename)
            
        elif file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            zip_ref = zipfile.ZipFile(os.path.join(UPLOAD_FOLDER, filename), 'r')
            zip_ref.extractall(UPLOAD_FOLDER)
            zip_ref.close()
            
            radius = float(request.form['radius'])
            num_cars = request.form['num_cars']
            multi_method = request.form['multi-method']
            time_varying = request.form.get('time-varying')
            
            DATA_DIR = os.path.join(UPLOAD_FOLDER, filename[:-4])
            outfile = os.path.join(UPLOAD_FOLDER, 'sol.csv')
            if num_cars == '':
                num_cars = 15
            optimize(DATA_DIR, radius, int(num_cars), outfile, multi_method = multi_method, time_varying = time_varying)
                
    # return render_template('index.html')
    return redirect(url_for('allocation_file', filename='sol.csv'))


def optimize(data_dir, radius, num_cars, outfile, multi_method = None, time_varying = None, day = None):
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
    df = solve.load_dataset(data_dir, len(data_files), grids, regions, distances, day = day) # Load all data
    
    if multi_method != None:
        worst_days = solve.find_worst_day_by_grid(df, grids)
        wd_incidences = solve.get_worst_day_incidences(df, grids, worst_days)
        if multi_method == "mode":
            mode = wd_incidences.day.mode().values[0]
            df = df[df.day==mode]
        elif multi_method == "aggregated":
            df = wd_incidences

    if time_varying != None:
        print("X-factor")
        for index, row in df.iterrows():
            if row.start_time < 480:
                df.at[index,'window'] = "00-08"
            elif row.start_time < 960:
                df.at[index,'window'] = "08-16"
            elif row.start_time <= 1440:
                df.at[index,'window'] = "16-24"
        
        intervals = ['00-08', '08-16', '16-24']
        for i in intervals:
            print("Finding overlaps in incidence times during %s..." % i)
            clashes = solve.find_clashes(df[df.window==i])
            print(clashes)
            outfile = os.path.join(UPLOAD_FOLDER, '%s_sol.csv' % i)
            print("Solving for interval %s..." % i)
            allocation = solve.allocate(grids, df[df.window==i].spf_base, clashes, num_cars, outfile)
    else:
        print("Finding overlaps in incidence times...")
        clashes = solve.find_clashes(df)

        print("Solving...")
        allocation = solve.allocate(grids, df.spf_base, clashes, num_cars, outfile)

        print("Time taken:", time.time() - t0)

    # return redirect(url_for('allocation_file', filename='sol.csv'))

@app.route('/solution', methods=['GET'])
def plot_map():
    allocation = pd.read_csv(os.path.join(UPLOAD_FOLDER, 'sol.csv'))
    data = []
    for index, row in allocation.iterrows():
        base = {
            'lat': row.lat,
            'lng': row.lng,
            'frc_supply': row.frc_supply
        }
        data.append(base)
    return jsonify(data)


@app.route('/solution/<filename>',)
def allocation_file(filename):
    try:
        return send_file('io/' + filename, as_attachment=True)
    except:
        return make_response(jsonify({'error': 'Not found'}), 404)

def evaluator(filename):
    
    df = pd.read_csv(os.path.join(UPLOAD_FOLDER, filename), index_col='id').sort_values(by=['start_time'])
    allocation = pd.read_csv(os.path.join(UPLOAD_FOLDER, 'sol.csv'))

    supply = {int(row.Grid_ID): [0]*int(row.frc_supply) for index, row in allocation.iterrows()}
    grids = pd.read_csv('grid_spec.csv')
    
    for index, row in df.iterrows():
        gid = int(grids[grids.long==row.lng][grids.lat==row.lat].Grid_ID.values[0])
        df.at[index, 'Grid_ID'] = gid

    success = evaluate.assign_cars(df, supply)
    risk = (len(df) - success) / len(df)

    print("Risk: {0:.2f}%".format(risk * 100))
    result = pd.DataFrame(columns=['filename', 'risk'])
    # for k, v in hash.items():
        # g = grids[grids.Grid_ID==k]
        # a = {
            # 'lng': g.long.values[0],
            # 'lat': g.lat.values[0],
            # 'frc_supply': len(v),
            # 'Grid_ID': k
        # }
    a = {'filename': filename, 'risk': risk}
    result = result.append(a, ignore_index=True)
    outputFolder = os.path.join(UPLOAD_FOLDER, 'results.csv')
    result.to_csv(outputFolder, index=False)
 
@app.route('/getResult', methods=['GET']) 
def getResult():
    results = pd.read_csv(os.path.join(UPLOAD_FOLDER, 'results.csv'))
    data = []
    for index, row in results.iterrows():
        result = {
            'filename': row.filename,
            'risk': row.risk,
        }
        data.append(result)
    return jsonify(data)

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


if __name__ == "__main__":
    app.run(debug=True)
