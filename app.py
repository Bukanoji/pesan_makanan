from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Konfigurasi Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:mxGTzqdmGxGLFtvYrnGxVxHtsqyRlIWY@monorail.proxy.rlwy.net:19310/railway'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Model User
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Buat database
with app.app_context():
    db.create_all()

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    item = db.Column(db.String(200), nullable=False)
    jumlah = db.Column(db.Integer, nullable=False)
    total_harga = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), default="Pending")

with app.app_context():
    db.create_all()


@app.route('/')
def home():
    return render_template('index.html')


daftar_menu = [
    {"id": 1, "nama": "Nasi Goreng", "harga": 20000, "gambar": "nasi_goreng.jpg"},
    {"id": 2, "nama": "Mie Ayam", "harga": 15000, "gambar": "mie_ayam.jpg"},
    {"id": 3, "nama": "Ayam Bakar", "harga": 25000, "gambar": "ayam_bakar.jpg"},
    {"id": 4, "nama": "Es Teh Manis", "harga": 5000, "gambar": "es_teh.jpg"}
]

@app.route('/menu')
def menu():
    return render_template('menu.html', menu=daftar_menu)

@app.route('/keranjang')
def keranjang():
    # Ambil daftar belanja dari session (defaultnya kosong)
    cart = session.get('cart', [])
    total_harga = sum(item['harga'] * item['jumlah'] for item in cart)
    return render_template('keranjang.html', cart=cart, total_harga=total_harga)

@app.route('/tambah_ke_keranjang/<int:id>')
def tambah_ke_keranjang(id):
    # Cari item berdasarkan ID
    item = next((m for m in daftar_menu if m["id"] == id), None)
    if item:
        # Ambil data keranjang dari session
        cart = session.get('cart', [])

        # Cek apakah item sudah ada di keranjang
        for makanan in cart:
            if makanan["id"] == id:
                makanan["jumlah"] += 1
                break
        else:
            cart.append({"id": item["id"], "nama": item["nama"], "harga": item["harga"], "gambar": item["gambar"], "jumlah": 1})

        # Simpan kembali ke session
        session['cart'] = cart
    return redirect(url_for('keranjang'))

@app.route('/hapus_dari_keranjang/<int:id>')
def hapus_dari_keranjang(id):
    cart = session.get('cart', [])
    cart = [item for item in cart if item["id"] != id]
    session['cart'] = cart
    return redirect(url_for('keranjang'))

@app.route('/update_status/<int:order_id>/<status>')
@login_required
def update_status(order_id, status):
    if current_user.username != 'admin':
        return "Akses Ditolak!", 403

    order = Order.query.get(order_id)
    if order:
        order.status = status
        db.session.commit()

    return redirect(url_for('admin_dashboard'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Cek apakah username sudah ada
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username sudah digunakan, coba yang lain!', 'danger')
            return redirect(url_for('register'))

        # Simpan user ke database
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('Registrasi berhasil! Silakan login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            next_page = request.args.get('next')
            if next_page:  # Redirect ke halaman yang diminta sebelumnya
                return redirect(next_page)

            # Jika tidak ada, redirect ke halaman default
            if user.username == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('home'))
        
            flash('Login berhasil!', 'success')  
        else:
            flash('Login gagal, periksa username dan password!', 'danger')

    return render_template('login.html')

@app.route('/admin')
@login_required
def admin_dashboard():
    if current_user.username != 'admin':
        return "Akses Ditolak!", 403

    orders = Order.query.all()
    return render_template('admin.html', orders=orders)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Anda telah logout.', 'info')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)
