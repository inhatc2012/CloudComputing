# Pydantic

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

todos = [
    {"id": 1, "title": "우유 사기", "completed": False},
    {"id": 2, "title": "책 반납하기", "completed": True},
    {"id": 3, "title": "빨래하기", "completed": False},
]

class TodoCreate(BaseModel):
    title: str
    completed: bool

# 함수 파라미터에 채워 넣을 값은 어디서 가져와야 하는가?

# A. 경로에 {} 형태로 함수 파라미터와 같은 이름이 있는가? → 경로 파라미터에 해당하고, URL 경로에서 가져옴
# B. 경로에 {} 형태로 함수 파라미터와 같은 이름이 없다면?
# B-1. 함수 파라미터의 타입이 단순 타입 → 쿼리 파라미터에서 가져옴
# B-2. 함수 파라미터의 타입이 BaseModel → 요청의 body에서 가져옴 <------------- ★★★


@app.post("/todos")
# POST http://127.0.0.1:8000/todos
# Content-Type: application/json
#
# {
#   "title": "우유 사기",
#   "completed": false
# }

# 위 요청에 대해서 아래와 같은 단계로 진행

# 0. FastAPI는 함수 create_todo(todo: TodoCreate)의 파라미터가 BaseModel을 상속한 클래스임을 확인
# 1. FastAPI는 함수 create_todo(todo: TodoCreate)의 파라미터 todo의 값이 요청의 body에서 가져와야 함을 알고 있음
# 2. 클라이언트가 보낸 요청 body (타입은 json)가 TodoCreate 모델의 필드(title, completed)를 기준으로 검증/변환
# 3. 검증/변환이 성공하면 TodoCreate 인스턴스가 만들어져 create_todo() 함수의 todo 파라미터에 전달됨
# → 결국 요청의 body의 값으로 TodoCreate 인스턴스를 만들어 함수 파라미터로 전달한 것
# 4. 함수 실행
def create_todo(todo: TodoCreate):
    new_id = len(todos) + 1
    new_todo = {"id": new_id, "title": todo.title, "completed": todo.completed}
    todos.append(new_todo)
    return new_todo

# --------------------------------------------------------------------------------------


# Body를 받아서 수정
@app.put("/todos/{id}")
# PUT http://127.0.0.1:8000/todos/2
# Content-Type: application/json
#
# {
#   "title": "우유와 빵 사기",
#   "completed": true
# }

# 위 요청에 대해서 아래와 같은 단계로 진행

# 0. FastAPI는 함수 update_todo(id: int, todo: TodoCreate)의 파라미터 중
#    id는 경로에 {id}로 존재 → 경로 파라미터, todo는 BaseModel을 상속한 클래스 타입임을 확인
# 1. FastAPI는 id는 URL 경로에서, todo는 요청의 body에서 값을 가져와야 함을 알고 있음
# 2. URL 경로의 "2"가 id: int 타입에 맞게 검증/변환됨 → 정수가 아니면 에러, 문자열을 정수로 변환
# 3. 클라이언트가 보낸 요청 body (타입은 json)가 TodoCreate 모델의 필드(title, completed)를 기준으로 검증/변환
# 4. 단계 2, 3이 모두 성공하면 id=2, todo=TodoCreate(title="우유와 빵 사기", completed=True) 방식으로
#    update_todo() 함수의 각 파라미터에 전달됨
# → 결국 URL 경로의 값은 id로, 요청 body의 값은 TodoCreate 인스턴스로 만들어져 함수 파라미터 todo로 전달된 것
# 5. 함수 실행: todos를 순회하며 id가 일치하는 항목을 찾아 title, completed를 수정하고 반환
def update_todo(id: int, todo: TodoCreate):
    for t in todos:
        if t["id"] == id:
            t["title"] = todo.title             # 수정
            t["completed"] = todo.completed     # 수정
            return t
    return {"error": "찾을 수 없습니다"}