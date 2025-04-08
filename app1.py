from flask import Flask, request, jsonify, render_template_string, redirect, url_for, flash
from flask_pymongo import PyMongo
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import numpy as np
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
import io
import base64
from bson import ObjectId

app = Flask(__name__)
app.secret_key = "abcdefghijklmnopqrstuvwxyz1234567890"

# MongoDB setup
app.config["MONGO_URI"] = "mongodb://localhost:27017/finance_tracker"
mongo = PyMongo(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Collections
users_collection = mongo.db.users
transactions_collection = mongo.db.transactions

# User authentication
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if user:
        return User(str(user['_id']), user['username'])
    return None

# Common CSS with background image
common_css = '''
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 0; height: 100vh; }
        .container { max-width: 800px; margin: auto; padding: 20px; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; color: white; }
        h1, h2 { color: white; font-size: 3em; }
        .button { padding: 15px 30px; font-size: 1.2em; color: white; background-color: #4CAF50; border: none; border-radius: 5px; cursor: pointer; text-decoration: none; }
        .button:hover { background-color: #45a049; }
        .project-description { font-size: 1.3em; margin-top: 20px; }
        .background-image {
            position: absolute;
            top: 0; bottom: 0; left: 0; right: 0;
            background-image: url('https://media.istockphoto.com/id/1795167728/photo/growth-in-business-and-finance-growing-graphs-and-charts.jpg?s=612x612&w=0&k=20&c=626gZ0gRzvxnmVODOIGYmIlMWnFc5Uv5fV7OrddBp-w=');
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            height: 100%;
            width: 100%;
        }
        .button-container { display: flex; gap: 20px; justify-content: center; margin-top: 30px; }
        .input-field { width: 100%; padding: 10px; margin: 10px 0; font-size: 1em; border-radius: 5px; border: 1px solid #ddd; }
        .table-container { overflow-x: auto; margin-top: 20px; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 15px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #4CAF50; color: white; }
        tr:hover { background-color: #f1f1f1; }
        .delete-button { background-color: #f44336; }
        .delete-button:hover { background-color: #e53935; }
    </style>
'''

# Routes

@app.route('/')
def home():
    return render_template_string(f'''
        {common_css}
        <div class="background-image">
            <div class="container">
                <h1>Welcome to Finance Tracker</h1>
                <h2>Manage your finances easily and efficiently!</h2>
                <p class="project-description">
                    Track your expenses, predict future financial trends, and more.
                    Get insights into your spending and set goals to save more effectively.
                </p>
                <div class="button-container">
                    <a href="/login" class="button">Login</a>
                    <a href="/signup" class="button">Sign Up</a>
                </div>
            </div>
        </div>
    ''')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        existing_user = users_collection.find_one({'username': username})
        if existing_user:
            flash("Username already exists!")
            return redirect(url_for('signup'))
        users_collection.insert_one({'username': username, 'password': password})
        user = users_collection.find_one({'username': username})
        login_user(User(str(user['_id']), user['username']))
        return redirect(url_for('finance_tracker'))
    return render_template_string(f'''
        {common_css}
        <div class="background-image">
            <div class="container">
                <h1>Create Account</h1>
                <form method="POST">
                    <input type="text" name="username" placeholder="Username" class="input-field" required>
                    <input type="password" name="password" placeholder="Password" class="input-field" required>
                    <button type="submit" class="button">Sign Up</button>
                </form>
            </div>
        </div>
    ''')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users_collection.find_one({'username': username, 'password': password})
        if user:
            login_user(User(str(user['_id']), user['username']))
            return redirect(url_for('finance_tracker'))
        flash("Invalid credentials, please try again.")
    return render_template_string(f'''
        {common_css}
        <div class="background-image">
            <div class="container">
                <h1>Login</h1>
                <form method="POST">
                    <input type="text" name="username" placeholder="Username" class="input-field" required>
                    <input type="password" name="password" placeholder="Password" class="input-field" required>
                    <button type="submit" class="button">Login</button>
                </form>
                <p>Don't have an account? <a href="/signup" class="button">Sign up</a></p>
            </div>
        </div>
    ''')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/finance_tracker')
@login_required
def finance_tracker():
    return render_template_string(f'''
        {common_css}
        <div class="background-image">
            <div class="container">
                <h1>Finance Tracker Dashboard</h1>
                <a href="/add_transaction" class="button">Add Transaction</a>
                <a href="/view_transactions" class="button">View Transactions</a>
                <a href="/predict_expenses" class="button">Predict Future Expenses</a>
                <a href="/logout" class="button">Logout</a>
            </div>
        </div>
    ''')

@app.route('/add_transaction', methods=['GET', 'POST'])
@login_required
def add_transaction():
    if request.method == 'POST':
        name = request.form['name']
        amount = float(request.form['amount'])
        date = request.form['date']
        transactions_collection.insert_one({
            'user_id': current_user.id,
            'name': name,
            'amount': amount,
            'date': date
        })
        return redirect(url_for('finance_tracker'))
    return render_template_string(f'''
        {common_css}
        <div class="background-image">
            <div class="container">
                <h1>Add Transaction</h1>
                <form method="POST">
                    <input type="text" name="name" placeholder="Transaction Name" class="input-field" required>
                    <input type="number" name="amount" step="0.01" placeholder="Amount" class="input-field" required>
                    <input type="date" name="date" class="input-field" required>
                    <button type="submit" class="button">Add Transaction</button>
                </form>
            </div>
        </div>
    ''')
@app.route('/view_transactions')
@login_required
def view_transactions():
    transactions = list(transactions_collection.find({'user_id': current_user.id}))
    return render_template_string('''
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 0; height: 100vh; }
            .container { max-width: 800px; margin: auto; padding: 20px; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; color: white; }
            h1, h2 { color: white; font-size: 3em; }
            .background-image {
                position: absolute;
                top: 0; bottom: 0; left: 0; right: 0;
                background-image: url('https://www.example.com/your-image.jpg');
                background-size: cover;
                background-position: center;
                background-attachment: fixed;
                height: 100%;
                width: 100%;
            }
            .button { padding: 15px 30px; font-size: 1.2em; color: white; background-color: #4CAF50; border: none; border-radius: 5px; cursor: pointer; text-decoration: none; }
            .button:hover { background-color: #45a049; }
            .table-container { overflow-x: auto; margin-top: 20px; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { padding: 15px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background-color: #4CAF50; color: white; }
            tr:hover { background-color: #f1f1f1; }
            .delete-button { background-color: #f44336; }
            .delete-button:hover { background-color: #e53935; }
        </style>
        <div class="background-image">
            <div class="container">
                <h1>Your Transactions</h1>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Amount</th>
                                <th>Date</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for transaction in transactions %}
                                <tr>
                                    <td>{{ transaction['name'] }}</td>
                                    <td>${{ transaction['amount'] }}</td>
                                    <td>{{ transaction['date'] }}</td>
                                    <td class="actions">
                                        <a href="/edit_transaction/{{ transaction['_id'] }}" class="button">Edit</a>
                                        <a href="/delete_transaction/{{ transaction['_id'] }}" class="button delete-button">Delete</a>
                                    </td>
                                </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                <a href="/finance_tracker" class="button">Back to Dashboard</a>
            </div>
        </div>
    ''', transactions=transactions)


@app.route('/edit_transaction/<transaction_id>', methods=['GET', 'POST'])
@login_required
def edit_transaction(transaction_id):
    transaction = transactions_collection.find_one({'_id': ObjectId(transaction_id), 'user_id': current_user.id})
    if request.method == 'POST':
        name = request.form['name']
        amount = float(request.form['amount'])
        date = request.form['date']
        transactions_collection.update_one(
            {'_id': ObjectId(transaction_id)},
            {'$set': {'name': name, 'amount': amount, 'date': date}}
        )
        return redirect(url_for('view_transactions'))
    return render_template_string(f'''
        {common_css}
        <div class="background-image">
            <div class="container">
                <h1>Edit Transaction</h1>
                <form method="POST">
                    <input type="text" name="name" value="{{ transaction['name'] }}" class="input-field" required>
                    <input type="number" name="amount" value="{{ transaction['amount'] }}" step="0.01" class="input-field" required>
                    <input type="date" name="date" value="{{ transaction['date'] }}" class="input-field" required>
                    <button type="submit" class="button">Update Transaction</button>
                </form>
            </div>
        </div>
    ''', transaction=transaction)

@app.route('/delete_transaction/<transaction_id>', methods=['GET'])
@login_required
def delete_transaction(transaction_id):
    transactions_collection.delete_one({'_id': ObjectId(transaction_id), 'user_id': current_user.id})
    return redirect(url_for('view_transactions'))

@app.route('/predict_expenses')
@login_required
def predict_expenses():
    # For this example, we are assuming the transactions are already in a format
    # to predict future trends based on linear regression
    transactions = list(transactions_collection.find({'user_id': current_user.id}))
    if not transactions:
        return redirect(url_for('finance_tracker'))
    
    # Example: Predicting expenses based on the past month
    expenses = [t['amount'] for t in transactions]
    dates = [t['date'] for t in transactions]

    # Prepare data for regression (simplified)
    X = np.array(range(len(expenses))).reshape(-1, 1)  # simple sequential data
    y = np.array(expenses)

    model = LinearRegression()
    model.fit(X, y)
    future_x = np.array(range(len(expenses), len(expenses) + 6)).reshape(-1, 1)
    predictions = model.predict(future_x)

    # Plotting the predictions
    plt.figure(figsize=(10, 6))
    plt.plot(range(len(expenses)), expenses, label='Historical Expenses')
    plt.plot(range(len(expenses), len(expenses) + 6), predictions, label='Predicted Expenses', linestyle='--')
    plt.xlabel('Months')
    plt.ylabel('Amount')
    plt.title('Expense Prediction')
    plt.legend()

    # Save plot to a base64 string
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    graph_url = base64.b64encode(img.read()).decode('utf-8')

    return render_template_string(f'''
        {common_css}
        <div class="background-image">
            <div class="container">
                <h1>Predict Future Expenses</h1>
                <img src="data:image/png;base64,{graph_url}" alt="Expense Prediction Graph">
                <a href="/finance_tracker" class="button">Back to Dashboard</a>
            </div>
        </div>
    ''')
if __name__ == '__main__':  # Corrected here
    app.run(debug=True)

