from fastapi import FastAPI, status, HTTPException
from pydantic import BaseModel

app = FastAPI()

todos = [
    {"id": 1, "title": "우유 사기", "completed": False},
    {"id": 2, "title": "책 반납하기", "completed": True},
    {"id": 3, "title": "빨래하기", "completed": False},
]

# 검증/변환의 대상으로서 입력 (예를 들어, 요청의 body)만 이야기 했는데
# 응답에 대해서도 검증을 하려면?
# 따라서 BaseModel 클래스가 두 개 등장
# 1. 요청 데이터의 검증
# POST(생성), PUT(수정)의 body 부분을 담당

# 2. 응답 데이터의 검증
# 예를 들어, 다른 하나는 GET에서 응답하는 부분을 담당
# 이 경우 @app.get("/todos", response_model=■)의 형태로 사용
# ■은 BaseModel을 상속한 클래스에 해당하며 응답을 검증하는 기준으로 사용

# serialization ("직렬화") → 내부 데이터(파이썬 객체)를 클라이언트에게 응답할 JSON 문자열로 바꾸는 과정
# serialization ("직렬화")는 응답 데이터 검증이 끝나면 그제서야 실행이 됨
# 즉, 검증을 통과해야 응답으로 전달한 JSON 문자열을 만든다는 의미

class TodoCreate(BaseModel):
    title: str
    completed: bool

class TodoOut(BaseModel):
    id: int
    title: str
    completed: bool

# ------------------------------------------------------------------

@app.get("/")
# GET http://127.0.0.1:8000/
def root():     
    # 함수 root()는 파라미터도 없고 response_model도 지정되지 않아서 요청/응답에 대해서 검증하지 않음
    return {"message": "hello"}

# ------------------------------------------------------------------

# Recap
# 함수 파라미터에 채워 넣을 값은 어디서 가져와야 하는가?
# 경로에 {} 형태로 함수 파라미터와 같은 이름이 있는가? → 경로 파라미터에 해당하고, URL 경로에서 가져옴
# 경로에 {} 형태로 함수 파라미터와 같은 이름이 없다면?
# 함수 파라미터의 타입이  단순 타입 → 쿼리 파라미터에서 가져옴
# 함수 파라미터의 타입이 BaseModel → 요청의 body에서 가져옴

@app.get("/todos", response_model=list[TodoOut])    # 응답은 TodoOut 클래스의 리스트
# GET http://127.0.0.1:8000/todos
# GET http://127.0.0.1:8000/todos?completed=true
# GET http://127.0.0.1:8000/todos?completed=false
def get_todos(completed: bool = None):
    if completed is None:   # GET http://127.0.0.1:8000/todos 에 해당
        return todos
    return [todo for todo in todos if todo["completed"] == completed]
    # 1. 함수가 반환한 리스트(딕셔너리들의 리스트)를 FastAPI (Pydantic)이 받음
    #    이 시점에서 받은 리스트는 다음과 같은 모습으로서 TodoOut 인스턴스는 아직 아님
    #       todos = [
    #           {"id": 1, "title": "우유 사기", "completed": False},
    #           ...
    #       ]
    # 2. response_model=list[TodoOut] 기준에 의해서 리스트 안의 딕셔너리 하나하나에 대해서
    # 3. TodoOut(id:int, title:str, completed:bool) 기준으로 검증/변환
    # 4. 검증을 모두 통과하면, TodoOut 인스턴스들의 리스트가 만들어짐
    # 5. 그 결과를 JSON으로 직렬화해서 클라이언트에게 응답으로 전송

# ------------------------------------------------------------------

@app.get("/todos/{id}", response_model=TodoOut)
# GET /todos/{id} 요청이 오면, 응답 데이터는 TodoOut 모델을 사용해서 검증

# GET http://127.0.0.1:8000/todos/1
# GET http://127.0.0.1:8000/todos/99
# GET http://127.0.0.1:8000/todos/abc  → 422 에러가 발생, 함수 시그니처는 경로 파라미터가 정수라고 정의

def get_todo(id: int): # 경로에 {} 형태로 함수 파라미터와 같은 이름이 있으므로 경로 파라미터
    for todo in todos:
        if todo["id"] == id:
            return todo
            # 1. 함수가 반환한 값은 todo, 예를 들어 {"id": 1, "title": "우유 사기", "completed": False})로서
            #    아직 TodoOut 인스턴스는 아님
            # 2. FastAPI(Pydantic)가 그 반환값을 가지고 감
            # 3. response_model=TodoOut 기준으로 가져간 딕셔너리를 
            #    TodoOut(id: int, title: str, completed: bool) 기준으로 검증/변환
            # 4. 검증을 통과하면, 그제서야 TodoOut 인스턴스가 만들어짐
            # 5. 만든 TodoOut 인스턴스를 JSON으로 직렬화해서 클라이언트에게 응답으로 전송
    
    # for 반복을 했는데 없으면 어떻게 할 것인가? 두 가지 경우
    # 1. return {"error": "찾을 수 없습니다"}
    # 2. raise HTTPException(status_code=404, detail="찾을 수 없습니다")

    # return {"error": "찾을 수 없습니다"} → 이것도 응답 검증의 대상임
    # 따라서 response_model=TodoOut 기준에 의해서 보면 문제 상황
    # 500 Internal Server Error이 발생하는데 그 이유는 클라이언트 요청 자체의 문제가 아니라 
    # 서버 측에서 response_model과 맞지 않는 값을 반환하려다 생긴 서버 측 오류이기 때문
    # 서버 오류도 다양하지만 가장 일반적인 서버 오류에 해당하는 500을 FastAPI가 사용한 것
    
    raise HTTPException(status_code=404, detail="찾을 수 없습니다")
    # 404 Not Found를 프로그래머가 명시적으로 만들어 낸 것
    # "없는데 나보고 어쩌라고?", 클라이언트가 요청한 리소스가 존재하지 않는 상황(404)에 해당
    
# ------------------------------------------------------------------    

@app.post("/todos", response_model=TodoOut, status_code=status.HTTP_201_CREATED)
# 생성에 해당하는 요청 post는 그 결과를 응답으로 돌려주는 경우 response_model=TodoOut이 적용할 수 있음
# status_code=status.HTTP_201_CREATED → "post 요청이 성공하면 이 코드를 응답 코드로 사용해줘"
# status_code=status.HTTP_201_CREATED → 성공했을 때에만 적용

# 상태 코드
# 200      OK: 일반적인 성공을 의미
# 201 Created: 구체적으로 어떤(생성) 성공인지를 명시

# POST http://127.0.0.1:8000/todos
# Content-Type: application/json
#
# {
#   "title": "운동하기",
#   "completed": false
# }
def create_todo(todo: TodoCreate): # ★★★★★ 요청 검증 && 응답 검증
    # 1. 클라이언트가 요청을 보내면서, body를 함께 전송
    # 2. FastAPI는 create_todo(todo: TodoCreate)에서 todo의 타입이 BaseModel을 상속한 TodoCreate임을 확인
    #    따라서 todo의 값은 요청 body에서 값을 가져와야 함을 FastAPI가 판단
    # 3. 클라이언트가 보낸 JSON body를, TodoCreate(title: str, completed: bool) 기준으로 검증/타입 변환
    # 4. 모든 필드가 검증을 통과하면, TodoCreate 인스턴스가 새로 생성됨
    # 5. 만들어진 TodoCreate 인스턴스가 create_todo() 함수의 todo 매개변수로 전달
    # 6. 아래 함수 코드 실행
    new_id = len(todos) + 1
    new_todo = {"id": new_id, "title": todo.title, "completed": todo.completed}
    todos.append(new_todo)
    return new_todo # 어떤 데이터가 새로 생성되었는지를 클라이언트에게 알려주는 역할

    # 1. new_todo, 예를 들어 {"id": 4, "title": "...", "completed": ...}를 return 해야 되는 상황
    #    아직 TodoOut 인스턴스는 아님, 딕셔너리 형태
    # 2. FastAPI (Pydantic)가 new_todo를 가지고 가서
    # 3. response_model=TodoOut 기준으로 TodoOut(id: int, title: str, completed: bool) 기준으로 검증/변환
    # 4. 검증을 모두 통과하면, 그제서야 TodoOut 인스턴스가 만들어짐
    # 5. 그 TodoOut 인스턴스를 JSON으로 직렬화
    # 6. status_code=status.HTTP_201_CREATED(201)와 함께, 직렬화된 JSON을 클라이언트에게 응답으로 전송

# ------------------------------------------------------------------    

@app.put("/todos/{id}", response_model=TodoOut)
# PUT http://127.0.0.1:8000/todos/2
# Content-Type: application/json
#
# {
#   "title": "우유와 빵 사기",
#   "completed": true
# }
def update_todo(id: int, todo: TodoCreate): # ★★★★★ 요청 검증 && 응답 검증
    # 요청 body는 TodoCreate 기준
    # 응답은 response_model=TodoOut 기준으로 검증

    # 1. 경로 파라미터 검증
    # URL 경로의 "2"(문자열)가 id: int 타입 기준으로 검증/변환

    # 2. 요청 body 검증
    # 클라이언트가 보낸 JSON body가 TodoCreate 필드(title: str, completed: bool) 기준으로 검증/변환

    # 3. 응답 검증
    # 아래의 return t로 반환한 값(딕셔너리)을 response_model=TodoOut 기준으로 다시 검증/변환
    # 검증을 통과하면 TodoOut 인스턴스로 만들고 JSON으로 직렬화한 다음 클라이언트에게 응답으로 전달

    for t in todos:
        if t["id"] == id:
            t["title"] = todo.title
            t["completed"] = todo.completed
            return t
    # return {"error": "찾을 수 없습니다"}
    raise HTTPException(status_code=404, detail="찾을 수 없습니다")
    # 404 Not Found: "없는데 나보고 어쩌라고?"

# ------------------------------------------------------------------    

# DELETE 요청은 삭제를 하므로 돌려줄 데이터가 없음
# 따라서 응답으로서 body를 비워서 전달 → 헤더 다음 빈 줄 이후에 아무것도 없는 응답이라는 의미

# status.HTTP_204_NO_CONTENT는 HTTP 상태 코드 204 에 해당
# 204 No Content는 "요청은 성공적으로 처리되었지만, 응답으로 돌려줄 본문(body) 내용이 없다"는 것을 의미 (표준)

@app.delete("/todos/{id}", status_code=status.HTTP_204_NO_CONTENT)
# DELETE http://127.0.0.1:8000/todos/3
def delete_todo(id: int):
    for t in todos:
        if t["id"] == id:
            todos.remove(t)
            return # return None과 동일하며 응답 본문(Body)은 비워져 있는 상태로 전달
            # status_code=status.HTTP_204_NO_CONTENT로 "이 응답은 body가 없다"고 지정
            # 실제 함수 코드에서도 그에 맞게 return(값 없이)으로 비어있는 body를 보내야 앞뒤가 맞게 됨
    # return {"error": "찾을 수 없습니다"}
    raise HTTPException(status_code=404, detail="찾을 수 없습니다")