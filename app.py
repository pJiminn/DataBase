from flask import Flask, render_template, request, redirect, url_for
from config import api_key
import requests
import sqlite3
import math
import re

# Flask 앱 생성
app = Flask(__name__)

# 데이터베이스 연결 함수
def get_db_connection():
    conn = sqlite3.connect('database/movies.db')
    conn.row_factory = sqlite3.Row
    return conn

# 태그 제거 및 모든 공백 제거 함수
def remove_tags(text):
    if text:
        # 1. !HS, !HE 태그 제거
        cleaned_text = re.sub(r'!HS|!HE', '', text)
        # 2. 모든 공백 및 탭 제거
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
        # 3. 양쪽 공백 제거
        return cleaned_text.strip()
    return ''

# 포스터 URL 처리 함수
def get_first_poster_url(poster_urls):
    if poster_urls:
        # 파이프(|)로 분리하고 첫 번째 URL 반환
        return poster_urls.split('|')[0].strip()
    return None

# 영화 검색 함수
def search_movies(search_query, search_type):
    url = f"http://api.koreafilm.or.kr/openapi-data2/wisenut/search_api/search_json2.jsp"
    params = {
        "collection": "kmdb_new2",
        "ServiceKey": api_key,
        "listCount": 100
    }

    if search_type == "title":
        params["title"] = search_query
    if search_type == "director":
        params["director"] = search_query
    elif search_type == "actor":
        params["actor"] = search_query

    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        if data.get("Data"):
            movies = data["Data"][0]["Result"]
            result = []
            for movie in movies:
                title = remove_tags(movie.get("title", "정보 없음"))
                directors = movie.get("directors", {}).get("director", [])
                directors = [remove_tags(director['directorNm']) for director in directors][:3]
                actors = movie.get("actors", {}).get("actor", [])
                main_actors = [remove_tags(actor['actorNm']) for actor in actors][:5]
                release_date = movie.get("repRlsDate", "정보 없음")
                genre = movie.get("genre", "정보 없음")
                runtime = movie.get("runtime", "정보 없음")
                poster = get_first_poster_url(movie.get("posters", "정보 없음"))
                result.append({
                    "title": title,
                    "directors": ", ".join(directors),
                    "actors": ", ".join(main_actors),
                    "release_date": release_date,
                    "genre": genre,
                    "runtime": runtime,
                    "poster": poster
                })
            return result
    return []

@app.route('/')
def index():
    conn = get_db_connection()
    latest_movie = conn.execute('SELECT poster FROM Movie ORDER BY movieID DESC LIMIT 1').fetchone()
    conn.close()

    # 최신 포스터 URL이 없으면 기본 이미지 사용
    poster_url = latest_movie['poster'] if latest_movie and latest_movie['poster'] else url_for('static', filename='images/pick.jpg')

    return render_template('index.html', weekly_pick=poster_url)


# 영화 목록 페이지
@app.route('/movies', methods=['GET', 'POST'])
def movies():
    search_results = []
    mode=''
    query = ''
    search_type = 'title'
    page = int(request.args.get('page', 1))  # 현재 페이지, 기본값 1
    per_page = 20  # 한 페이지당 영화 수

    if request.method == 'POST':
        query = request.form['search_query']
        search_type = request.form['search_type']
        search_results = search_movies(query, search_type)
        mode='add'
    elif 'query' in request.args:
        query = request.args.get('query')
        search_type = request.args.get('search_type')
        search_results = search_movies(query, search_type)

    # 페이징 처리
    total_results = len(search_results)
    total_pages = (total_results + per_page - 1) // per_page  # 전체 페이지 수 계산
    start = (page - 1) * per_page
    end = start + per_page
    paginated_results = search_results[start:end]

    return render_template(
        'movies.html',
        movies=paginated_results,
        query=query,
        search_type=search_type,
        page=page,
        total_pages=total_pages,
        mode=mode
    )

@app.route('/movies/add', methods=['GET', 'POST'])
def add_movie_page():
    if request.method == 'POST':
        query = request.form['search_query']
        search_type = request.form['search_type']
        search_results = search_movies(query, search_type)
        return render_template(
            'movies.html',
            movies=search_results,
            query=query,
            search_type=search_type,
            mode='add'
        )
    return render_template('movies.html', mode='add')

@app.route('/add_movieToDatabase', methods=['POST'])
def add_movie():
    title = request.form['title']
    poster = request.form['poster']
    directors = request.form['directors']
    actors = request.form['actors']
    release_date = request.form['release_date']
    genre = request.form['genre']
    runtime = request.form['runtime']

    conn = get_db_connection()
    try:
        # Movie 데이터 삽입
        conn.execute(
            'INSERT INTO Movie (title, genre, release_date, runtime, poster) VALUES (?, ?, ?, ?, ?)',
            (title, genre, release_date, runtime, poster)
        )
        movie_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]

        # Movie_Director 데이터 삽입
        for director in directors.split(', '):
            conn.execute(
                'INSERT INTO Movie_Director (directorName, movieID) VALUES (?, ?)',
                (director, movie_id)
            )

        # Movie_Actor 데이터 삽입
        for actor in actors.split(', '):
            conn.execute(
                'INSERT INTO Movie_Actor (actorName, movieID) VALUES (?, ?)',
                (actor, movie_id)
            )

        conn.commit()
    except Exception as e:
        print(f"Error adding movie: {e}")
        conn.rollback()
    finally:
        conn.close()

    return redirect(url_for('movies'))

@app.route('/movies/list')
def list_movies_page():
    conn = get_db_connection()

    # 영화 목록과 관련 감독 및 배우 정보 가져오기
    movies = conn.execute('''
        SELECT 
            m.movieID, 
            m.title, 
            m.genre, 
            m.release_date, 
            m.runtime, 
            m.poster,
            GROUP_CONCAT(DISTINCT md.directorName) AS directors,
            GROUP_CONCAT(DISTINCT ma.actorName) AS actors
        FROM Movie m
        LEFT JOIN Movie_Director md ON m.movieID = md.movieID
        LEFT JOIN Movie_Actor ma ON m.movieID = ma.movieID
        GROUP BY m.movieID
    ''').fetchall()
    conn.close()

    # 데이터 전달
    return render_template('movies.html', movies=movies, mode='list')

@app.route('/delete_movie/<int:movie_id>', methods=['POST'])
def delete_movie(movie_id):
    """
    Delete a movie from the database by movieID.
    """
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM Movie WHERE movieID = ?', (movie_id,))
        conn.commit()
    except Exception as e:
        print(f"Error deleting movie: {e}")
    finally:
        conn.close()

    return redirect(url_for('list_movies_page'))


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
