import requests
import json
import re 
from config import api_key

# 태그 제거 및 공백 제거 함수
def remove_tags(text):
    if text:
        return re.sub(r'!HS|!HE', '', text).strip()
    return ''


# 검색 파라미터
search_query = "기생충"  # 검색할 영화 제목
url = f"http://api.koreafilm.or.kr/openapi-data2/wisenut/search_api/search_json2.jsp?collection=kmdb_new2&ServiceKey={api_key}&title={search_query}"

# API 요청 보내기
response = requests.get(url)

# 응답 확인
if response.status_code == 200:
    data = response.json()  # JSON 응답 데이터
    if data.get("Data"):
        movies = data["Data"][0]["Result"]
        for movie in movies:
            title = remove_tags(movie.get("title", "정보 없음"))
            directors = movie.get("directors", "정보 없음")
            directors = directors.get("director", "정보 없음")
            directors = [director['directorNm'] for director in directors][:3]
            actors = movie.get("actors", "정보 없음")
            actors = actors.get("actor", "정보 없음")
            actors = [actor['actorNm'] for actor in actors][:5]
            release_date = movie.get("repRlsDate", "정보 없음")
            genre = movie.get("genre", "정보 없음")
            
            print(f"제목: {title}")
            print(f"감독: {directors}")
            print(f"배우: {actors}")
            print(f"개봉일: {release_date}")
            print(f"장르: {genre}")
            print("-" * 40)
    else:
        print("검색 결과가 없습니다.")
else:
    print(f"API 요청 실패: {response.status_code}")
