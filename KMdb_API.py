<!DOCTYPE html>
<html lang="ko">

<head>
    <meta charset="UTF-8">
    <title>Movie Search</title>
</head>

<body>
    <h1>Movie Search</h1>
    <form method="POST" action="/movies">
        <input type="text" name="search_query" placeholder="검색어를 입력하세요" value="{{ query }}" required>
        <select name="search_type">
            <option value="title" {% if search_type == 'title' %}selected{% endif %}>영화명</option>
            <option value="director" {% if search_type == 'director' %}selected{% endif %}>감독명</option>
            <option value="actor" {% if search_type == 'actor' %}selected{% endif %}>배우명</option>
        </select>
        <button type="submit">검색</button>
    </form>
    <hr>
    {% if movies %}
    <h2>검색 결과:</h2>
    <table border="1">
        <thead>
            <tr>
                <th>제목</th>
                <th>포스터</th>
                <th>감독</th>
                <th>배우</th>
                <th>개봉일</th>
                <th>장르</th>
            </tr>
        </thead>
        <tbody>
            {% for movie in movies %}
            <tr>
                <td>{{ movie.title }}</td>
                <td>
                    {% if movie.poster %}
                    <img src="{{ movie.poster }}" alt="포스터 이미지" style="width: 100px; height: auto;">
                    {% else %}
                    <span>이미지 없음</span>
                    {% endif %}
                </td>
                <td>{{ movie.directors }}</td>
                <td>{{ movie.actors }}</td>
                <td>{{ movie.release_date }}</td>
                <td>{{ movie.genre }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    <div>
        <p>페이지 {{ page }} / {{ total_pages }}</p>
        <div>
            {% if page > 1 %}
            <a href="/movies?page={{ page - 1 }}&query={{ query }}&search_type={{ search_type }}">이전</a>
            {% endif %}
            {% if page < total_pages %}
            <a href="/movies?page={{ page + 1 }}&query={{ query }}&search_type={{ search_type }}">다음</a>
            {% endif %}
        </div>
    </div>
    {% endif %}
</body>

</html>
