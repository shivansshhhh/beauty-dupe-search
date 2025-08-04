import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
import sqlite3
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # change this to a strong secret in production

DB = "dupes.db"
ADMIN_PASSWORD = 'admin123'  # Change this for security

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create upload folder if doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        query = request.form["query"]
        return redirect(url_for("search", query=query))
    return render_template("index.html")

@app.route("/search")
def search():
    query = request.args.get("query", "").strip().lower()
    conn = get_db_connection()
    c = conn.cursor()

    # Clean and normalize query (remove extra spaces)
    normalized_query = ' '.join(query.split())

    # Try exact match (normalized)
    c.execute("""
        SELECT * FROM products 
        WHERE LOWER(TRIM(name)) = ? OR LOWER(TRIM(brand || ' ' || name)) = ?
    """, (normalized_query, normalized_query))
    exact = c.fetchone()

    if exact:
        # Get dupes cheaper than original
        c.execute("""
            SELECT p.* FROM dupes d
            JOIN products p ON p.id = d.dupe_id
            WHERE d.original_id = ? AND p.price < ?
            ORDER BY p.price ASC
        """, (exact["id"], exact["price"]))
        dupes = c.fetchall()
        conn.close()
        return render_template("search_results.html", product=exact, dupes=dupes)

    else:
        # Fallback to partial search (brand + name) with better LIKE handling
        like_query = f"%{normalized_query}%"
        c.execute("""
            SELECT * FROM products
            WHERE LOWER(brand || ' ' || name) LIKE ?
               OR LOWER(name) LIKE ?
               OR LOWER(brand) LIKE ?
        """, (like_query, like_query, like_query))
        results = c.fetchall()
        conn.close()
        return render_template("search_results.html", products=results)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        password = request.form.get("password", "")
        if password != ADMIN_PASSWORD:
            flash("Incorrect password", "danger")
            return redirect(url_for("admin"))
        session['admin_authenticated'] = True
        return redirect(url_for("admin"))

    if not session.get('admin_authenticated'):
        return render_template("admin.html", authenticated=False)

    conn = get_db_connection()
    products = conn.execute("SELECT * FROM products").fetchall()

    # Get linked dupes for each product
    dupes_map = {}
    for product in products:
        dupes = conn.execute("""
            SELECT p.* FROM dupes d
            JOIN products p ON p.id = d.dupe_id
            WHERE d.original_id = ?
            ORDER BY p.price ASC
        """, (product['id'],)).fetchall()
        dupes_map[product['id']] = dupes
    conn.close()

    return render_template("admin.html", authenticated=True, products=products, dupes_map=dupes_map)

@app.route("/admin/logout")
def admin_logout():
    session.pop('admin_authenticated', None)
    flash("Logged out successfully.", "success")
    return redirect(url_for("admin"))

@app.route("/admin/add-product", methods=["POST"])
def add_product():
    if not session.get('admin_authenticated'):
        flash("Please login as admin.", "danger")
        return redirect(url_for("admin"))

    brand = request.form.get("brand", "").strip()
    name = request.form.get("name", "").strip()
    color = request.form.get("color", "").strip()
    price = request.form.get("price", "").strip()
    file = request.files.get("image")

    if not brand or not name or not price:
        flash("Brand, Name, and Price are required.", "danger")
        return redirect(url_for("admin"))

    try:
        price = float(price)
    except ValueError:
        flash("Invalid price value.", "danger")
        return redirect(url_for("admin"))

    image_filename = None
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        image_filename = filename

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO products (brand, name, color, price, image) VALUES (?, ?, ?, ?, ?)",
        (brand, name, color, price, image_filename)
    )
    conn.commit()
    conn.close()

    flash("Product added successfully!", "success")
    return redirect(url_for("admin"))

@app.route("/admin/edit-product/<int:product_id>", methods=["GET", "POST"])
def edit_product(product_id):
    if not session.get('admin_authenticated'):
        flash("Please login as admin.", "danger")
        return redirect(url_for("admin"))

    conn = get_db_connection()
    product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()

    if not product:
        flash("Product not found.", "danger")
        conn.close()
        return redirect(url_for("admin"))

    if request.method == "POST":
        brand = request.form.get("brand", "").strip()
        name = request.form.get("name", "").strip()
        color = request.form.get("color", "").strip()
        price = request.form.get("price", "").strip()
        file = request.files.get("image")

        if not brand or not name or not price:
            flash("Brand, Name, and Price are required.", "danger")
            return redirect(url_for("edit_product", product_id=product_id))

        try:
            price = float(price)
        except ValueError:
            flash("Invalid price value.", "danger")
            return redirect(url_for("edit_product", product_id=product_id))

        image_filename = product['image']  # keep existing image by default
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_filename = filename

        # Update product info
        conn.execute("""
            UPDATE products SET brand=?, name=?, color=?, price=?, image=? WHERE id=?
        """, (brand, name, color, price, image_filename, product_id))
        conn.commit()

        # Handle removal of image if checkbox checked
        if request.form.get("remove_image"):
            conn.execute("UPDATE products SET image=NULL WHERE id=?", (product_id,))
            conn.commit()

        # Handle dupes updates: Multiple selection from form named 'dupes'
        selected_dupes = request.form.getlist("dupes")  # List of dupe IDs as strings

        # Remove all existing dupes for this original product
        conn.execute("DELETE FROM dupes WHERE original_id = ?", (product_id,))

        # Insert new dupe links (skip if dupe_id == product_id to avoid self-link)
        for dupe_id in selected_dupes:
            if dupe_id.isdigit() and int(dupe_id) != product_id:
                conn.execute(
                    "INSERT INTO dupes (original_id, dupe_id) VALUES (?, ?)",
                    (product_id, int(dupe_id))
                )
        conn.commit()
        conn.close()

        flash("Product and dupes updated successfully!", "success")
        return redirect(url_for("admin"))

    # On GET, load all products for dupes selection
    all_products = conn.execute("SELECT * FROM products ORDER BY brand, name").fetchall()

    # Get currently linked dupes IDs
    linked_dupes = conn.execute("SELECT dupe_id FROM dupes WHERE original_id = ?", (product_id,)).fetchall()
    linked_dupe_ids = [d['dupe_id'] for d in linked_dupes]

    conn.close()

    return render_template("edit_product.html", product=product, all_products=all_products, linked_dupe_ids=linked_dupe_ids)


@app.route("/admin/delete-product/<int:product_id>", methods=["POST"])
def delete_product(product_id):
    if not session.get('admin_authenticated'):
        flash("Please login as admin.", "danger")
        return redirect(url_for("admin"))

    conn = get_db_connection()
    conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.execute("DELETE FROM dupes WHERE original_id = ? OR dupe_id = ?", (product_id, product_id))
    conn.commit()
    conn.close()

    flash("Product and related dupe links deleted.", "success")
    return redirect(url_for("admin"))

@app.route("/admin/link-dupe", methods=["POST"])
def link_dupe():
    if not session.get('admin_authenticated'):
        flash("Please login as admin.", "danger")
        return redirect(url_for("admin"))

    original_id = request.form.get("original_id")
    dupe_id = request.form.get("dupe_id")

    if not original_id or not dupe_id:
        flash("Both products must be selected.", "danger")
        return redirect(url_for("admin"))

    if original_id == dupe_id:
        flash("Original and dupe cannot be the same.", "danger")
        return redirect(url_for("admin"))

    conn = get_db_connection()

    existing = conn.execute("""
        SELECT * FROM dupes WHERE original_id = ? AND dupe_id = ?
    """, (original_id, dupe_id)).fetchone()

    if existing:
        flash("Dupe already linked.", "info")
    else:
        conn.execute(
            "INSERT INTO dupes (original_id, dupe_id) VALUES (?, ?)",
            (original_id, dupe_id)
        )
        conn.commit()
        flash("Dupe linked successfully.", "success")

    conn.close()
    return redirect(url_for("admin"))

if __name__ == "__main__":
    app.run(debug=True)
