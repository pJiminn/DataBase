import requests
from config import api_key

search = '기생충'

url = f'http://www.kobis.or.kr/kobisopenapi/webservice/rest/movie/searchMovieList.json?key={api_key}&movieNm={search}'

response = requests.get(url)
data = response.json()

if(data['movieListResult']['totCnt'] != 0):
    for movie in data['movieListResult']['movieList']:
        print(f"영화코드: {movie['movieCd']}, 영화명: {movie['movieNm']}, 개봉일: {movie['openDt']}, 감독명: {movie['directors'][0]['peopleNm']}")
        break
else:
    print("Nothing in our Database")
