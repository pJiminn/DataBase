from flask import Flask, render_template, request, redirect, url_for
import sqlite3

# Flask 앱 생성
app = Flask(__name__)

# 데이터베이스 연결 함수


def get_db_connection():
    conn = sqlite3.connect('database/movies.db')
    conn.row_factory = sqlite3.Row
    return conn

# 홈 페이지


@app.route('/')
def index():
    return render_template('index.html')

# 영화 목록 페이지


@app.route('/movies', methods=['GET', 'POST'])
def movies():
    conn = get_db_connection()
    if request.method == 'POST':
        # 새로운 영화 추가
        title = request.form['title']
        genre = request.form['genre']
        director = request.form['director']
        actors = request.form['actors']
        conn.execute(
            'INSERT INTO movies (title, genre, director, actors) VALUES (?, ?, ?, ?)',
            (title, genre, director, actors)
        )
        conn.commit()
    movies = conn.execute('SELECT * FROM movies').fetchall()
    conn.close()
    return render_template('movies.html', movies=movies)

# 리뷰 페이지
@app.route('/review')
def review():
    return render_template('review.html') 

# 내 리뷰, 정보 볼 수 있는?
@app.route('/profile')
def profile():
    return render_template('profile.html')  # MY PROFILE 페이지

# 그냥 만들어 봤어 4칸이 예뻐보여서 쩝쩝 하하
@app.route('/about')
def about():
    return render_template('about.html')  # What's our app? 페이지

@app.route('/reviews/<int:movie_id>', methods=['GET', 'POST'])
def reviews(movie_id):
    conn = get_db_connection()
    if request.method == 'POST':
        # 새로운 리뷰 추가
        review_text = request.form['review']
        conn.execute(
            'INSERT INTO reviews (movie_id, review_text) VALUES (?, ?)',
            (movie_id, review_text)
        )
        conn.commit()
    # 영화 정보 가져오기
    movie = conn.execute(
        'SELECT * FROM movies WHERE id = ?', (movie_id,)).fetchone()
    reviews = conn.execute(
        'SELECT * FROM reviews WHERE movie_id = ?', (movie_id,)).fetchall()
    conn.close()
    return render_template('review.html', movie=movie, reviews=reviews)


if __name__ == '__main__':
    app.run(debug=True)
