import os
from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests


API_KEY = os.environ['TMDB_API_KEY']
MOVIE_DB_INFO = "https://api.themoviedb.org/3/movie"
MOVIE_DB_IMG = "https://www.themoviedb.org/t/p/w1280"

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)


class UpdateForm(FlaskForm):
    rating = StringField("Your Rating Out of 10")
    review = StringField("Your Review")
    post = SubmitField("Done")


class AddMovieForm(FlaskForm):
    movie = StringField("Movie Title", validators=[
                        DataRequired("Please fill this field")])
    submit = SubmitField("Add Movie")


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies-collection.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)

db.create_all()

@app.route("/")
def home():
    all_movies = Movie.query.order_by(Movie.rating).all()
    for i in range(len(all_movies)):
        #This line gives each movie a new ranking reversed from their order in all_movies
        all_movies[i].ranking = len(all_movies) - i
        db.session.commit()
    return render_template("index.html", movies=all_movies)


@app.route('/add', methods=['GET', 'POST'])
def add_movie():
    add_form = AddMovieForm()
    if(add_form.validate_on_submit()):
        movie_title = add_form.movie.data
        response = requests.get('https://api.themoviedb.org/3/search/movie',
                                params={"api_key": API_KEY, "query": movie_title})
        data = response.json()['results']
        return render_template('select.html', data=data)
    return render_template('add.html', form=add_form)


@app.route("/find")
def find_movie():
    movie_api_id = request.args.get("id")
    if movie_api_id:
        movie_api_url = f"{MOVIE_DB_INFO}/{movie_api_id}"
        response = requests.get(movie_api_url, params={"api_key": API_KEY, "language": "en-US"})
        data = response.json()
        new_movie = Movie(
            title=data["title"],
            year=data["release_date"].split('-')[0],
            description=data["overview"],
            img_url=f"{MOVIE_DB_IMG}{data['poster_path']}"
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for("edit", id=new_movie.id))

@app.route('/edit', methods=['GET', 'POST'])
def edit():
    update_form = UpdateForm()
    movie_id = request.args.get("id")
    movie = Movie.query.get(movie_id)
    if(update_form.validate_on_submit()):
        movie.rating = float(update_form.rating.data)
        movie.review = update_form.review.data
        db.session.commit()
        return redirect(url_for('home'))

    return render_template('edit.html', movie=movie, form=update_form)


@app.route('/delete', methods=['GET', 'POST'])
def delete_movie():
    movie_id = request.args.get('id')
    movie = Movie.query.get(movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
