from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import pandas as pd
import numpy as np
import pickle

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Load model and dataset
model = pickle.load(open('LinearRegressionModel.pkl', 'rb'))
car = pd.read_csv('Cleaned_Car_data.csv')

# In-memory user store
users = {}

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users:
            return render_template('register.html', error="User already exists.")
        users[username] = password
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if users.get(username) == password:
            session['user'] = username
            return redirect(url_for('predictor'))
        else:
            return render_template('login.html', error="Invalid credentials.")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/predictor')
def predictor():
    if 'user' not in session:
        return redirect(url_for('login'))
    companies = sorted(car['company'].unique())
    models = sorted(car['name'].unique())
    years = sorted(car['year'].unique(), reverse=True)
    fuel_types = car['fuel_type'].unique()
    return render_template('predictor.html', companies=companies, car_models=models, years=years, fuel_types=fuel_types)

@app.route('/predict', methods=['POST'])
def predict():
    try:
        company = request.form.get('company')
        car_model = request.form.get('car_model')
        year = int(request.form.get('year'))
        fuel_type = request.form.get('fuel_type')
        driven = int(request.form.get('kilo_driven'))

        input_df = pd.DataFrame([[car_model, company, year, driven, fuel_type]],
                                columns=['name', 'company', 'year', 'kms_driven', 'fuel_type'])
        prediction = model.predict(input_df)
        return jsonify({'price': np.round(prediction[0], 2)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_car_models', methods=['POST'])
def get_car_models():
    data = request.get_json()
    company = data.get('company')
    models = sorted(car[car['company'] == company]['name'].unique())
    return jsonify({'models': models})

@app.route('/price_trend', methods=['POST'])
def price_trend():
    data = request.get_json()
    model_name = data.get('car_model')
    trend = car[car['name'] == model_name].groupby('year')['price'].mean().reset_index()
    return jsonify({
        'years': trend['year'].tolist(),
        'prices': [round(p, 2) for p in trend['price']]
    })

if __name__ == '__main__':
    app.run(debug=True)
