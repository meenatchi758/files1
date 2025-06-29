# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///recipes.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.secret_key = 'secret-key'
db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    ingredients = db.Column(db.Text, nullable=False)
    instructions = db.Column(db.Text, nullable=False)
    cuisine = db.Column(db.String(100))
    prep_time = db.Column(db.String(50))
    image = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'))

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Integer, nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'))

# Routes
@app.route('/')
def index():
    query = request.args.get('q')
    if query:
        recipes = Recipe.query.filter(
            Recipe.ingredients.contains(query) | Recipe.cuisine.contains(query)
        ).all()
    else:
        recipes = Recipe.query.order_by(Recipe.created_at.desc()).all()
    return render_template('index.html', recipes=recipes)

@app.route('/recipe/<int:id>')
def recipe_detail(id):
    recipe = Recipe.query.get_or_404(id)
    comments = Comment.query.filter_by(recipe_id=id).all()
    ratings = Rating.query.filter_by(recipe_id=id).all()
    avg_rating = round(sum([r.score for r in ratings]) / len(ratings), 1) if ratings else 'No ratings yet'
    return render_template('recipe_detail.html', recipe=recipe, comments=comments, avg_rating=avg_rating)

@app.route('/add', methods=['GET', 'POST'])
def add_recipe():
    if request.method == 'POST':
        title = request.form['title']
        ingredients = request.form['ingredients']
        instructions = request.form['instructions']
        cuisine = request.form['cuisine']
        prep_time = request.form['prep_time']
        image = request.files['image']
        filename = None
        if image:
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            image.save(upload_path)
            filename = upload_path
        new_recipe = Recipe(
            title=title,
            ingredients=ingredients,
            instructions=instructions,
            cuisine=cuisine,
            prep_time=prep_time,
            image=filename
        )
        db.session.add(new_recipe)
        db.session.commit()
        flash('Recipe added successfully!')
        return redirect(url_for('index'))
    return render_template('add_recipe.html')

@app.route('/comment/<int:recipe_id>', methods=['POST'])
def comment(recipe_id):
    content = request.form['content']
    new_comment = Comment(content=content, recipe_id=recipe_id)
    db.session.add(new_comment)
    db.session.commit()
    return redirect(url_for('recipe_detail', id=recipe_id))

@app.route('/rate/<int:recipe_id>', methods=['POST'])
def rate(recipe_id):
    score = int(request.form['score'])
    new_rating = Rating(score=score, recipe_id=recipe_id)
    db.session.add(new_rating)
    db.session.commit()
    return redirect(url_for('recipe_detail', id=recipe_id))

# Optional init route for dev/testing
@app.route('/init-db')
def init_db():
    db.create_all()
    return '✅ Database initialized.'

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
