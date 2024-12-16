from flask import Flask, render_template, request, redirect, url_for
from config import api_key
import requests
import sqlite3
from datetime import datetime
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
                directors = [remove_tags(director['directorNm'])
                             for director in directors][:3]
                actors = movie.get("actors", {}).get("actor", [])
                main_actors = [remove_tags(actor['actorNm'])
                               for actor in actors][:5]
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

    # 최신 포스터 URL 가져오기
    latest_movie = conn.execute(
        'SELECT poster FROM Movie ORDER BY movieID DESC LIMIT 1'
    ).fetchone()

    # 최신 포스터 URL이 없으면 기본 이미지 사용
    weekly_pick = latest_movie['poster'] if latest_movie and latest_movie['poster'] else url_for(
        'static', filename='images/pick.jpg'
    )

    # 평점 평균이 높은 TOP 3 영화 가져오기
    top_movies = conn.execute('''
        SELECT m.poster, AVG(r.rating) as avg_rating
        FROM Movie m
        JOIN Review r ON m.movieID = r.movieID
        GROUP BY m.movieID
        ORDER BY avg_rating DESC
        LIMIT 3
    ''').fetchall()

    # 데이터베이스 연결 닫기
    conn.close()

    # Top 3 포스터 URL 리스트
    top_posters = [movie['poster'] for movie in top_movies]

    # 템플릿 렌더링
    return render_template('index.html', weekly_pick=weekly_pick, top_posters=top_posters)


# 영화 목록 페이지
@app.route('/movies', methods=['GET', 'POST'])
def movies():
    search_results = []
    mode = ''
    query = ''
    search_type = 'title'
    page = int(request.args.get('page', 1))  # 현재 페이지, 기본값 1
    per_page = 20  # 한 페이지당 영화 수

    if request.method == 'POST':
        query = request.form['search_query']
        search_type = request.form['search_type']
        search_results = search_movies(query, search_type)
        mode = 'add'
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
    query = request.args.get('query', '')  # GET 요청에서 쿼리 가져오기
    search_type = request.args.get('search_type', 'title')  # 기본 검색 유형
    page = int(request.args.get('page', 1))  # 현재 페이지, 기본값 1
    per_page = 20  # 한 페이지당 영화 수

    search_results = []

    if request.method == 'POST':
        query = request.form['search_query']
        search_type = request.form['search_type']
        search_results = search_movies(query, search_type)
    elif query:  # GET 요청에서 query 값이 있으면 검색 수행
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
        mode='add'
    )



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
        # 기존에 동일한 영화 제목과 감독이 있는지 확인
        existing_movie = conn.execute('''
            SELECT m.movieID
            FROM Movie m
            JOIN Movie_Director md ON m.movieID = md.movieID
            WHERE m.title = ? AND md.directorName IN (?)
        ''', (title, directors)).fetchone()

        if existing_movie:
            return '''
            <script>
                alert("이미 동일한 영화와 감독이 존재합니다. 추가할 수 없습니다.");
                window.history.back();
            </script>
            '''

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
        return '''
        <script>
            alert("영화 추가 중 오류가 발생했습니다.");
            window.history.back();
        </script>
        '''
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
        ORDER BY m.movieID ASC
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


@app.route('/profile')
def profile():
    return render_template('profile.html')  # MY PROFILE 페이지


@app.route('/profile/input', methods=['GET'])
def profile_input():
    return render_template('profile_input.html')  # 이름 입력 페이지


@app.route('/profile/check', methods=['GET', 'POST'])
def check_user():
    if request.method == 'POST':
        username = request.form['username']
    elif request.method == 'GET':
        username = request.args.get('username')

    if not username:
        return '''
        <script>
            alert("사용자 이름이 필요합니다.");
            window.location.href = "/profile";
        </script>
        '''

    conn = get_db_connection()

    # User 테이블에서 이름 확인
    user = conn.execute(
        'SELECT UserID FROM User WHERE UserID = ?',
        (username,)
    ).fetchone()

    if not user:
        conn.execute(
            'INSERT INTO User (UserID) VALUES (?)',
            (username,)
        )
        conn.commit()
        user_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    else:
        user_id = user['UserID']

    # 해당 UserID의 리뷰 가져오기
    reviews = conn.execute(
        '''
        SELECT r.reviewID, m.title AS movie_title, r.comment, r.reviewDate, r.watchedDate, r.rating
        FROM Review r
        JOIN Movie m ON r.movieID = m.movieID
        WHERE r.UserID = ?
        ''',
        (user_id,)
    ).fetchall()

    conn.close()

    return render_template('profile.html', user_name=username, reviews=reviews)


@app.route('/review/popup', methods=['GET'])
def review_popup():
    username = request.args.get('username')  # 부모 창에서 전달된 사용자 이름
    return render_template('review_popup.html', username=username)


@app.route('/add_review', methods=['POST'])
def add_review():
    movie_title = request.form['movieTitle']  # 영화 제목
    comment = request.form['comment']  # 리뷰 내용
    watched_date = request.form['watchedDate']  # 영화 본 날짜
    rating = int(request.form['rating'])  # 평점
    review_date = datetime.now().strftime('%Y-%m-%d')  # 현재 날짜
    username = request.form['username']  # 사용자 이름 (폼에서 전달)
    print(f"Received username: {username}")

    conn = get_db_connection()

    try:
        # Movie 테이블에서 movieID 가져오기
        movie = conn.execute(
            'SELECT movieID FROM Movie WHERE title = ?',
            (movie_title,)
        ).fetchone()

        if not movie:
            raise Exception("해당 영화가 데이터베이스에 없습니다.")

        movie_id = movie['movieID']

        # User 테이블에서 UserID 가져오기
        user = conn.execute(
            'SELECT UserID FROM User WHERE UserID = ?',
            (username,)
        ).fetchone()
        print(f"Queried user: {user}")
        if not user:
            raise Exception("사용자가 데이터베이스에 없습니다.")

        user_id = user['UserID']

        # 리뷰 테이블에 데이터 삽입
        conn.execute(
            '''
            INSERT INTO Review (movieID, userID, comment, reviewDate, watchedDate ,rating)
            VALUES (?, ?, ?, ?, ?,?)
            ''',
            (movie_id, user_id, comment, review_date, watched_date, rating)
        )

        # 트랜잭션 커밋
        conn.commit()
    except Exception as e:
        conn.rollback()  # 오류 발생 시 롤백
        return f'''
        <script>
            alert("오류 발생: {str(e)}");
            window.close();
        </script>
        '''
    finally:
        conn.close()

    # 성공 메시지 및 팝업 닫기
    return '''
    <script>
        alert("리뷰가 저장되었습니다!");
        window.opener.location.reload();  // 부모 창 새로고침
        window.close();  // 팝업 닫기
    </script>
    '''


@app.route('/review/edit', methods=['GET'])
def edit_review():
    review_id = request.args.get('review_id')  # URL 파라미터에서 리뷰 ID 가져오기

    conn = get_db_connection()
    review = conn.execute(
        '''
        SELECT r.reviewID, r.comment, r.watchedDate ,m.title AS movie_title,r.rating 
        FROM Review r
        JOIN Movie m ON r.movieID = m.movieID
        WHERE r.reviewID = ?
        ''',
        (review_id,)
    ).fetchone()
    conn.close()

    return render_template('edit_review.html', review=review)


@app.route('/review/update', methods=['POST'])
def update_review():
    review_id = request.form['review_id']
    comment = request.form['comment']
    watched_date = request.form['watchedDate']
    rating = int(request.form['rating'])

    print(
        f"Debug: review_id={review_id}, comment={comment}, watched_date={watched_date}, rating={rating}")

    conn = get_db_connection()
    try:
        conn.execute(
            '''
            UPDATE Review
            SET comment = ?, watchedDate = ?, rating = ?
            WHERE reviewID = ?
            ''',
            (comment, watched_date, rating, review_id)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        return f'''
        <script>
            alert("오류 발생: {str(e)}");
            window.close();
        </script>
        '''
    finally:
        conn.close()

    return '''
    <script>
        alert("리뷰가 수정되었습니다!");
        window.opener.location.reload();
        window.close();
    </script>
    '''


@app.route('/review/delete', methods=['POST'])
def delete_review():
    review_id = request.form['review_id']  # 폼에서 리뷰 ID 가져오기
    username = request.form['user_name']  # 폼에서 사용자 이름 가져오기

    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM Review WHERE reviewID = ?', (review_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        return f'''
        <script>
            alert("오류 발생: {str(e)}");
            window.location.href = "{url_for('check_user', username=username)}";
        </script>
        '''
    finally:
        conn.close()

    # 삭제 성공 후 사용자 이름과 함께 리디렉션
    return redirect(url_for('check_user', username=username))



@app.route('/review', methods=['GET'])
def all_reviews():
    page = int(request.args.get('page', 1))  # 현재 페이지, 기본값 1
    per_page = 10  # 한 페이지당 리뷰 수
    offset = (page - 1) * per_page

    # 검색 및 정렬 조건 받기
    search_movie = request.args.get('movie', '')  # 영화 이름 검색
    search_user = request.args.get('user', '')  # 유저 검색
    sort_by = request.args.get('sort', 'date')  # 정렬 기준 (기본값: 날짜)

    conn = get_db_connection()

    # 총 리뷰 개수 가져오기 (필터 포함)
    count_query = '''
        SELECT COUNT(*) 
        FROM Review r
        JOIN Movie m ON r.movieID = m.movieID
        JOIN User u ON r.userID = u.UserID
        WHERE m.title LIKE ? AND u.UserID LIKE ?
    '''
    total_reviews = conn.execute(
        count_query,
        (f"%{search_movie}%", f"%{search_user}%")
    ).fetchone()[0]
    total_pages = (total_reviews + per_page - 1) // per_page  # 전체 페이지 수

    # 정렬 기준에 따라 동적 쿼리 작성
    if sort_by == 'movie':
        order_clause = 'ORDER BY m.title ASC, r.reviewDate DESC'
    elif sort_by == 'user':
        order_clause = 'ORDER BY u.UserID ASC, r.reviewDate DESC'
    else:  # 기본값: 날짜별
        order_clause = 'ORDER BY r.reviewDate DESC'

    # 특정 페이지에 해당하는 리뷰 가져오기 (필터 및 정렬 포함)
    reviews_query = f'''
        SELECT 
            r.comment, 
            r.reviewDate, 
            r.watchedDate, 
            m.title AS movie_title, 
            u.UserID AS user_name,
            r.rating
        FROM Review r
        JOIN Movie m ON r.movieID = m.movieID
        JOIN User u ON r.userID = u.UserID
        WHERE m.title LIKE ? AND u.UserID LIKE ?
        {order_clause}
        LIMIT ? OFFSET ?
    '''
    reviews = conn.execute(
        reviews_query,
        (f"%{search_movie}%", f"%{search_user}%", per_page, offset)
    ).fetchall()

    conn.close()

    # 템플릿에 데이터 전달
    return render_template(
        'all_reviews.html',
        reviews=reviews,
        page=page,
        total_pages=total_pages,
        search_movie=search_movie,
        search_user=search_user,
        sort_by=sort_by
    )


@app.route('/about')
def about():
    return render_template('about.html')  # What's our app? 페이지


if __name__ == '__main__':
    app.run(debug=True)
