
# Dependency Injection

from fastapi import FastAPI

app = FastAPI()

todos = [
    {"id": 1, "title": "우유 사기", "completed": False},
    {"id": 2, "title": "책 반납하기", "completed": True},
    {"id": 3, "title": "빨래하기", "completed": False},
    {"id": 4, "title": "우유 배달 확인", "completed": False},
]

# todos를 대상으로 페이지네이션을 실행
# 페이지네이션은 todos의 원하는 부분을 todos[skip : skip + limit]의 형태로 선택한 뒤 응답으로 반환

# skip, limit에 대해서 return todos[skip : skip + limit]의 예를 들면
# skip=0, limit=2  → todos[0:2]
# skip=2, limit=2  → todos[2:4]


# 함수 파라미터에 채워 넣을 값은 어디서 가져와야 하는가?

# A. 경로에 {} 형태로 함수 파라미터와 같은 이름이 있는가? → 경로 파라미터에 해당하고, URL 경로에서 가져옴
# B. 경로에 {} 형태로 함수 파라미터와 같은 이름이 없다면?
# B-1. 함수 파라미터의 타입이 단순 타입 → 쿼리 파라미터에서 가져옴
# B-2. 함수 파라미터의 타입이 BaseModel → 요청의 body에서 가져옴
@app.get("/todos")
# GET http://127.0.0.1:8000/todos?skip=0&limit=2
def get_todos(skip: int = 0, limit: int = 10):
    return todos[skip : skip + limit] # todos[0:2]

@app.get("/todos/search")
# GET http://127.0.0.1:8000/todos/search?title=우유&skip=0&limit=2
def search_todos(title: str, skip: int = 0, limit: int = 10):
    filtered = [t for t in todos if title in t["title"]] # ?title=■의 ■이 포함된 t in todos
    return filtered[skip : skip + limit]

# -------------------------------------------------------------------
# Dependency Injection의 정의
# -------------------------------------------------------------------


from fastapi import FastAPI, Depends

# A depends on B

# dependency에 해당하는 함수 및 리턴 >>> B
def pagination_params(skip: int = 0, limit: int = 10):
    return {"skip": skip, "limit": limit}

@app.get("/todos2")
def get_todos2(pagination: dict = Depends(pagination_params)): # >>> A
    # 파라미터 pagination는 딕셔너리 타입
    # Depends(pagination_params())가 아님에 주의

    # 0. 파이썬 인터프리터는 def get_todos2(pagination: dict = Depends(pagination_params)): 을 보고
    #    Depends 인스턴스를 생성, Depends 인스턴스에는 함수 객체 pagination_params를 넣음
    # 1. GET /todos2?skip=0&limit=2 요청 도착 → @app.get("/todos2") 데코리에터와 매칭됨
    # 2. FastAPI가 get_todos2의 매개변수 pagination의 값이 pagination_params 함수 객체가 들어 있는
    #    Depends() 인스턴스임을 확인
    # 3. FastAPI가 pagination_params 함수 객체를 꺼낸 뒤, 요청의 쿼리 파라미터(skip=0, limit=2)를 전달
    # 4. pagination_params(skip=0, limit=2) 호출
    # 5. 반환값 {"skip": 0, "limit": 2}를 get_todos2의 pagination 매개변수에 채움

    skip = pagination["skip"]
    limit = pagination["limit"]
    return todos[skip : skip + limit]

@app.get("/todos2/search")
def search_todos2(title: str, pagination: dict = Depends(pagination_params)): # >>> A
    # 파라미터 pagination는 딕셔너리 타입
    # Depends(pagination_params())가 아님에 주의

    # 0. 파이썬 인터프리터는 def search_todos2(title: str, pagination: dict = Depends(pagination_params)): 을 보고
    #    Depends 인스턴스를 생성, Depends 인스턴스에는 함수 객체 pagination_params를 넣음
    # 1. GET /todos2/search?title=우유&skip=0&limit=2 요청 도착 → @app.get("/todos2/search") 데코레이터와 매칭됨
    # 2. FastAPI가 search_todos2의 매개변수 pagination의 값이 pagination_params 함수 객체가 들어 있는
    #    Depends() 인스턴스임을 확인
    # 3. FastAPI가 pagination_params 함수 객체를 꺼낸 뒤, 요청의 쿼리 파라미터(skip=0, limit=2)를 전달
    # 4. pagination_params(skip=0, limit=2) 호출
    # 5. 반환값 {"skip": 0, "limit": 2}를 search_todos2의 pagination 매개변수에 채움
    # 6. title은 경로에 없고 단순 타입이므로 쿼리 파라미터로 인식되어, 요청의 title=우유가 그대로 전달됨

    skip = pagination["skip"]
    limit = pagination["limit"]
    filtered = [t for t in todos if title in t["title"]]
    return filtered[skip : skip + limit]
