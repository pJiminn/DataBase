import requests
import json
from DataBase.config import api_key

search = '아이언맨'

url = f'http://www.kobis.or.kr/kobisopenapi/webservice/rest/movie/searchMovieList.json?key={api_key}&movieNm={search}'

response = requests.get(url)
data = response.json()

if(data['movieListResult']['totCnt'] != 0):
    for movie in data['movieListResult']['movieList']:
        find_movie_code = movie['movieCd']
        break

    url2 = f'http://www.kobis.or.kr/kobisopenapi/webservice/rest/movie/searchMovieInfo.json?key={api_key}&movieCd={find_movie_code}'

    response2 = requests.get(url2)
    data2 = response2.json()

    # 상세 정보 출력
    movie_info = data2['movieInfoResult']['movieInfo']

    movie_name = movie_info['movieNm']
    movie_genre = [genre['genreNm'] for genre in movie_info['genres']]
    movie_opendate = movie_info['openDt']
    movie_runningtime = movie_info['showTm']
    movie_directors = [director['peopleNm']
                       for director in movie_info['directors']]
    movie_actors = [actor['peopleNm'] for actor in movie_info['actors']]

    print(movie_name)
    print(movie_genre)
    print(movie_opendate)
    print(movie_runningtime)
    print(movie_directors)
    print(movie_actors)
else:
    print("Nothing in our Database")
