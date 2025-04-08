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
    def __init__(self, id, username):  # Corrected constructor name
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if user:
        return User(str(user['_id']), user['username'])
    return None

# Common CSS
common_css = '''
    <style>
        body {
            font-family: Arial, sans-serif;
            background-image: url('https://media.istockphoto.com/id/1795167728/photo/growth-in-business-and-finance-growing-graphs-and-charts.jpg?s=612x612&w=0&k=20&c=626gZ0gRzvxnmVODOIGYmIlMWnFc5Uv5fV7OrddBp-w='); /* Set the background image URL here */
            background-size: cover;
            background-position: center;
            margin: 0;
            padding: 0;
            height: 100vh;
        }
        .container {
            max-width: 800px;
            margin: auto;
            padding: 20px;
            background: rgba(255, 255, 255, 0.8); /* Semi-transparent white background */
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            text-align: center;
        }
        .input-field {
            padding: 10px;
            margin: 5px 0;
            width: 100%;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        .button {
            padding: 10px 20px;
            color: white;
            background-color: #4CAF50;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            margin: 10px 0;
            transition: background-color 0.3s ease;
        }
        .button:hover {
            background-color: #45a049;
        }
        .table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th, td {
            padding: 12px;
            border: 1px solid #ddd;
            text-align: left;
        }
        th {
            background-color: #4CAF50;
            color: white;
        }
        tr:hover {
            background-color: #f1f1f1;
        }
        h1, h2 {
            color: #333;
        }
        a {
            text-decoration: none;
            color: #4CAF50;
        }
        .actions {
            display: flex;
            justify-content: center;
            gap: 10px;
        }
        .delete-button {
            background-color: #f44336;
        }
        .delete-button:hover {
            background-color: #e53935;
        }
        .back-button {
            margin-top: 20px;
            padding: 12px 25px;
            background-color: #4CAF50;
            color: white;
            border-radius: 10px;
            text-decoration: none;
            font-size: 1.1em;
            display: inline-block;
        }
        .back-button:hover {
            background-color: #45a049;
        }
    </style>
'''
# Routes
@app.route('/')
def home():
    return render_template_string(f'''
        {common_css}
        <div class="container">
            <h1>Welcome to Personal Finance Assistant</h1>
            <h2>Empowering Financial Management: Finance Tracker Application<h2>
            <h3>The Finance Tracker is a powerful tool designed to simplify personal finance management, combining robust functionality with a user-friendly design. Built using Flask, MongoDB, and machine learning, the application provides a comprehensive solution for tracking, analyzing, and predicting financial transactions.</h3>
            <h3>Core Features</h3>
            <p>The app ensures secure access with robust user authentication using Flask’s LoginManager. Users can register, log in, and manage their profiles safely, with data stored securely in MongoDB. Once logged in, users can add, edit, view, or delete transactions. The tabular transaction view, equipped with clear action buttons, makes financial management seamless and efficient.

A standout feature is the expense prediction tool. By leveraging machine learning (linear regression), the app analyzes past transactions to forecast spending for the next 30 days. Users receive valuable insights into their financial trends, visually represented through dynamic graphs created using Matplotlib.</p>
<h2>Enhanced User Experience</h2>
<p>The app’s design prioritizes accessibility and aesthetics. A clean interface with modern styling ensures intuitive navigation, while visualizations make data engaging and easy to understand. Features like transaction editing and deletion give users full control, empowering them to align their expenses with their goals.</p>
<h2>Real-World Impact</h2>
<p>The Finance Tracker is ideal for students, professionals, and families looking to budget effectively. Its predictive capabilities enable smarter financial planning, transforming data into actionable insights.</p>
<h2>Future Potential</h2>
<p>Planned expansions include AI-driven insights, multi-currency support, and integration with payment platforms for real-time tracking.

In a world where financial literacy is key, the Finance Tracker stands out as an essential tool. Combining innovation, practicality, and scalability, it empowers users to take control of their financial journey with confidence.</p>
            <a href="/login" class="button">Login</a>
            <a href="/signup" class="button">Sign Up</a>
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
        <div class="container">
            <h1>Create Account</h1>
            <form method="POST">
                <input type="text" name="username" placeholder="Username" class="input-field" required>
                <input type="password" name="password" placeholder="Password" class="input-field" required>
                <button type="submit" class="button">Sign Up</button>
            </form>
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
        <div class="container">
            <h1>Login</h1>
            <form method="POST">
                <input type="text" name="username" placeholder="Username" class="input-field" required>
                <input type="password" name="password" placeholder="Password" class="input-field" required>
                <button type="submit" class="button">Login</button>
            </form>
            <p>Don't have an account? <a href="/signup">Sign up</a></p>
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
        <div class="container">
            <h1>Finance Tracker Dashboard</h1>
            <a href="/add_transaction" class="button">Add Transaction</a>
            <a href="/view_transactions" class="button">View Transactions</a>
            <a href="/predict_expenses" class="button">Predict Future Expenses</a>
            <a href="/logout" class="button">Logout</a>
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
        <div class="container">
            <h1>Add Transaction</h1>
            <form method="POST">
                <input type="text" name="name" placeholder="Transaction Name" class="input-field" required>
                <input type="number" name="amount" step="0.01" placeholder="Amount" class="input-field" required>
                <input type="date" name="date" class="input-field" required>
                <button type="submit" class="button">Add Transaction</button>
            </form>
        </div>
    ''')
@app.route('/view_transactions')
@login_required
def view_transactions():
    transactions = list(transactions_collection.find({'user_id': current_user.id}))
    return render_template_string('''
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f8f9fa;
                margin: 0;
                padding: 0;
            }
            .container {
                max-width: 900px;
                margin: 20px auto;
                padding: 20px;
                background: white;
                border-radius: 12px;
                box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
                text-align: center;
            }
            h1 {
                color: #4CAF50;
                font-size: 2.5em;
                margin-bottom: 20px;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 30px;
            }
            th, td {
                padding: 15px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }
            th {
                background-color: #4CAF50;
                color: white;
            }
            tr:hover {
                background-color: #f1f1f1;
            }
            .button {
                padding: 10px 20px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                text-decoration: none;
                margin: 5px;
                transition: background-color 0.3s ease;
            }
            .button:hover {
                background-color: #45a049;
            }
            .delete-button {
                background-color: #f44336;
                color: white;
            }
            .delete-button:hover {
                background-color: #e53935;
            }
            .actions {
                display: flex;
                justify-content: center;
                gap: 10px;
            }
            .back-button {
                margin-top: 20px;
                padding: 12px 25px;
                background-color: #4CAF50;
                color: white;
                border-radius: 10px;
                text-decoration: none;
                font-size: 1.1em;
                display: inline-block;
            }
            .back-button:hover {
                background-color: #45a049;
            }
        </style>

        <div class="container">
            <h1>Your Transactions</h1>
            {% if transactions %}
                <table>
                    <thead>
                        <tr>
                            <th>Transaction Name</th>
                            <th>Amount</th>
                            <th>Date</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for transaction in transactions %}
                            <tr>
                                <td>{{ transaction['name'] }}</td>
                                <td>${{ '{:,.2f}'.format(transaction['amount']) }}</td>
                                <td>{{ transaction['date'] }}</td>
                                <td class="actions">
                                    <a href="/edit_transaction/{{ transaction['_id'] }}" class="button">Edit</a>
                                    <a href="/delete_transaction/{{ transaction['_id'] }}" class="button delete-button">Delete</a>
                                </td>
                            </tr>
                        {% endfor %}
                    </tbody>
                </table>
            {% else %}
                <p>No transactions found. Start adding your expenses.</p>
            {% endif %}
            <a href="/finance_tracker" class="back-button">Back to Dashboard</a>
            <a href="/delete_all_transactions" class="button delete-button" style="margin-top: 20px;">Delete All Transactions</a>
        </div>
    ''', transactions=transactions)

@app.route('/edit_transaction/<transaction_id>', methods=['GET', 'POST'])
@login_required
def edit_transaction(transaction_id):
    # Fetch the transaction from the database
    transaction = transactions_collection.find_one({'_id': ObjectId(transaction_id), 'user_id': current_user.id})
    
    if not transaction:
        flash("Transaction not found!")
        return redirect(url_for('view_transactions'))
    
    if request.method == 'POST':
        # Get updated transaction details from the form
        name = request.form['name']
        amount = float(request.form['amount'])
        date = request.form['date']
        
        # Update the transaction in the database
        transactions_collection.update_one(
            {'_id': ObjectId(transaction_id)},
            {'$set': {'name': name, 'amount': amount, 'date': date}}
        )
        flash("Transaction updated successfully!")
        return redirect(url_for('view_transactions'))

    # Pre-fill the form with current transaction details
    return render_template_string('''
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f8f9fa;
                margin: 0;
                padding: 0;
            }
            .container {
                max-width: 600px;
                margin: 50px auto;
                padding: 20px;
                background: white;
                border-radius: 12px;
                box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
            }
            h1 {
                color: #4CAF50;
                font-size: 2.5em;
                margin-bottom: 20px;
            }
            .input-field {
                padding: 10px;
                margin: 10px 0;
                width: 100%;
                border: 1px solid #ddd;
                border-radius: 5px;
                box-sizing: border-box;
            }
            .button {
                padding: 10px 20px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                margin-top: 20px;
                width: 100%;
                font-size: 1.1em;
            }
            .button:hover {
                background-color: #45a049;
            }
        </style>

        <div class="container">
            <h1>Edit Transaction</h1>
            <form method="POST">
                <input type="text" name="name" class="input-field" placeholder="Transaction Name" value="{{ transaction['name'] }}" required>
                <input type="number" name="amount" class="input-field" placeholder="Amount" value="{{ transaction['amount'] }}" required step="0.01">
                <input type="date" name="date" class="input-field" value="{{ transaction['date'] }}" required>
                <button type="submit" class="button">Update Transaction</button>
            </form>
            <a href="/view_transactions" class="button" style="background-color: #f44336;">Cancel</a>
        </div>
    ''', transaction=transaction)


@app.route('/delete_transaction/<transaction_id>')
@login_required
def delete_transaction(transaction_id):
    transactions_collection.delete_one({'_id': ObjectId(transaction_id)})
    return redirect(url_for('view_transactions'))

@app.route('/delete_all_transactions')
@login_required
def delete_all_transactions():
    transactions_collection.delete_many({'user_id': current_user.id})
    return redirect(url_for('view_transactions'))

@app.route('/predict_expenses')
@login_required
def predict_expenses():
    transactions = list(transactions_collection.find({'user_id': current_user.id}))
    if len(transactions) < 2:
        return render_template_string(f'''
            {common_css}
            <div class="container">
                <h1>Future Expenses Prediction</h1>
                <p>Not enough data to predict future expenses. Add more transactions.</p>
                <a href="/finance_tracker" class="button">Back to Dashboard</a>
            </div>
        ''')

    amounts = np.array([transaction['amount'] for transaction in transactions])
    dates = np.array([np.datetime64(transaction['date']) for transaction in transactions])
    days = np.array([(date - dates.min()).astype(int) for date in dates]).reshape(-1, 1)
    model = LinearRegression()
    model.fit(days, amounts)
    future_days = np.arange(days.max() + 1, days.max() + 31).reshape(-1, 1)
    predicted_amounts = model.predict(future_days)
    
    predicted_monthly_expense = predicted_amounts.sum()
    predicted_monthly_expense_formatted = f"{predicted_monthly_expense:.2f}"

    plt.figure(figsize=(8, 5))
    plt.scatter(days, amounts, color='blue', label='Past Transactions')
    plt.plot(future_days, predicted_amounts, color='red', label='Predicted Expenses')
    plt.xlabel('Days')
    plt.ylabel('Amount')
    plt.title('Expense Prediction for Next 30 Days')
    plt.legend()
    plt.grid()
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    
    return render_template_string(f'''
    {common_css}
    <div class="container">
        <h1>Future Expenses Prediction</h1>
        <p>Estimated total expense for the next month: <strong>${{{{{ predicted_monthly_expense }}}}}</strong></p>
        <img src="data:image/png;base64,{{{{ plot_url }}}}" alt="Prediction Graph">
        <a href="/finance_tracker" class="button">Back to Dashboard</a>
    </div>
''', plot_url=plot_url, predicted_monthly_expense=predicted_monthly_expense_formatted)

if __name__ == '__main__':  # Corrected here
    app.run(debug=True)
