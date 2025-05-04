from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql
from pymysql.cursors import DictCursor
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a random secret key

# Database configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'fantasy_football_db'

def get_db_connection():
    return pymysql.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        db=app.config['MYSQL_DB'],
        cursorclass=DictCursor
    )

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('Please log in to access this page', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Only one login route definition
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        try:
            connection = get_db_connection()
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
                user = cursor.fetchone()
                
                if user and check_password_hash(user['password'], password):
                    session['logged_in'] = True
                    session['user_id'] = user['id']
                    session['username'] = user['username']
                    flash('Login successful!', 'success')
                    return redirect(url_for('index'))
                else:
                    flash('Invalid username or password', 'danger')
        except Exception as e:
            flash(f"Database error: {str(e)}", "danger")
        finally:
            if 'connection' in locals():
                connection.close()
    
    return render_template('auth/login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)

# Database connection helper
def get_db_connection():
    try:
        connection = pymysql.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD'],
            db=app.config['MYSQL_DB'],
            cursorclass=DictCursor
        )
        return connection
    except pymysql.Error as e:
        flash(f"Database connection failed: {str(e)}", "danger")
        return None





@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/players')
@login_required
def players():
    connection = get_db_connection()
    if not connection:
        return render_template('players.html', players=[])
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT p.*, t.name as team_name 
                FROM players p
                JOIN teams t ON p.team_id = t.team_id
                ORDER BY p.total_points DESC
            """)
            players = cursor.fetchall()
        return render_template('players.html', players=players)
    except pymysql.Error as e:
        flash(f"Error fetching players: {str(e)}", "danger")
        return render_template('players.html', players=[])
    finally:
        connection.close()

@app.route('/teams')
@login_required
def teams():
    connection = get_db_connection()
    if not connection:
        return render_template('teams.html', teams=[])
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT t.*, 
                    COUNT(p.player_id) as player_count,
                    SUM(p.total_points) as total_points
                FROM teams t
                LEFT JOIN players p ON t.team_id = p.team_id
                GROUP BY t.team_id
                ORDER BY total_points DESC
            """)
            teams = cursor.fetchall()
        return render_template('teams.html', teams=teams)
    except pymysql.Error as e:
        flash(f"Error fetching teams: {str(e)}", "danger")
        return render_template('teams.html', teams=[])
    finally:
        connection.close()

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        
        connection = get_db_connection()
        if not connection:
            return redirect(url_for('register'))
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO users (username, password) VALUES (%s, %s)",
                    (username, password)
                )
                connection.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except pymysql.Error as e:
            flash(f"Registration failed: {str(e)}", "danger")
        finally:
            connection.close()
    
    return render_template('auth/register.html')

if __name__ == '__main__':
    app.run(debug=True, port=5001)
