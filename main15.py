# 종합 예제: FastAPI + SQLAlchemy(ORM) + Pydantic
# 요청 함수의 파라미터를 채우는 네 가지 방법
# 1. Depends()      → 의존성 함수가 반환(yield)한 값
# 2. 경로 파라미터   → 경로에 {} 형태로 함수 파라미터와 같은 이름이 있음
# 3. 단순 타입       → 쿼리 파라미터에서 가져옴
# 4. BaseModel      → 요청의 body에서 가져옴

from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# ------------------------------------------------------------------
# 데이터베이스 설정

engine = create_engine(
    "sqlite:///./todos.db",
    connect_args={"check_same_thread": False},
    # FastAPI는 요청을 여러 스레드에서 처리할 수 있음
    # SQLite는 기본적으로 연결을 만든 스레드에서만 사용하도록 제한하므로 이 제한을 해제
)

SessionLocal = sessionmaker(bind=engine)   # Session을 찍어내는 팩토리 객체

Base = declarative_base()

class Todo(Base):                          # ORM 모델: todos 테이블과 대응
    __tablename__ = "todos"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    completed = Column(Boolean, default=False)

# ------------------------------------------------------------------
# Pydantic 모델: 요청/응답 검증

class TodoCreate(BaseModel):               # 요청 body 검증 (POST, PUT)
    title: str
    completed: bool = False

class TodoOut(BaseModel):                  # 응답 검증 (response_model)
    model_config = ConfigDict(from_attributes=True)
    # 라우트 함수가 반환하는 것은 딕셔너리가 아니라 Todo 객체(ORM 인스턴스)
    # from_attributes=True → todo["id"]가 아니라 todo.id처럼 속성으로 값을 읽어서 검증
    id: int
    title: str
    completed: bool

# ------------------------------------------------------------------
# 의존성: yield를 사용한 Session 관리

def get_db():
    db = SessionLocal()     # 요청마다 새로운 Session 생성
    try:
        yield db            # 라우트 함수의 db 파라미터에 주입
    finally:
        db.close()          # 응답 이후 Session 정리 (Connection을 Pool에 반납)

# ------------------------------------------------------------------

Base.metadata.create_all(engine)
# 테이블이 없으면 생성 (이미 있으면 건너뜀)
# 모듈 최상위 코드이므로 uvicorn이 main15.py를 import하는 시점에 실행

app = FastAPI()

@app.get("/todos", response_model=list[TodoOut])
# GET http://127.0.0.1:8000/todos
# GET http://127.0.0.1:8000/todos?completed=true
def get_todos(completed: bool = None, db: Session = Depends(get_db)):
    # completed → 단순 타입이므로 쿼리 파라미터
    # db        → Depends()
    query = db.query(Todo)
    if completed is not None:
        query = query.filter(Todo.completed == completed)
    return query.all()      # list[Todo 객체] → list[TodoOut] 기준으로 검증

# ------------------------------------------------------------------

@app.get("/todos/{id}", response_model=TodoOut)
# GET http://127.0.0.1:8000/todos/1
def get_todo(id: int, db: Session = Depends(get_db)):
    # id → 경로 파라미터
    # db → Depends()
    todo = db.query(Todo).filter(Todo.id == id).first()
    if todo is None:
        raise HTTPException(status_code=404, detail="찾을 수 없습니다")
    return todo

# ------------------------------------------------------------------

@app.post("/todos", response_model=TodoOut, status_code=status.HTTP_201_CREATED)
# POST http://127.0.0.1:8000/todos
def create_todo(todo: TodoCreate, db: Session = Depends(get_db)):
    # todo → BaseModel이므로 요청 body
    # db   → Depends()
    new_todo = Todo(title=todo.title, completed=todo.completed)
    db.add(new_todo)        # session.new에 추가
    db.commit()             # INSERT 확정 → id가 채워짐
    db.refresh(new_todo)    # 데이터베이스의 최신 값으로 객체를 다시 읽음
    return new_todo

# ------------------------------------------------------------------

@app.put("/todos/{id}", response_model=TodoOut)
# PUT http://127.0.0.1:8000/todos/1
def update_todo(id: int, todo: TodoCreate, db: Session = Depends(get_db)):
    # id   → 경로 파라미터
    # todo → 요청 body
    # db   → Depends()
    target = db.query(Todo).filter(Todo.id == id).first()
    if target is None:
        raise HTTPException(status_code=404, detail="찾을 수 없습니다")
    target.title = todo.title           # 속성 변경 → session.dirty
    target.completed = todo.completed
    db.commit()                         # UPDATE 확정
    db.refresh(target)
    return target

# ------------------------------------------------------------------

@app.delete("/todos/{id}", status_code=status.HTTP_204_NO_CONTENT)
# DELETE http://127.0.0.1:8000/todos/1
def delete_todo(id: int, db: Session = Depends(get_db)):
    # id → 경로 파라미터
    # db → Depends()
    target = db.query(Todo).filter(Todo.id == id).first()
    if target is None:
        raise HTTPException(status_code=404, detail="찾을 수 없습니다")
    db.delete(target)       # session.deleted에 추가
    db.commit()             # DELETE 확정
    return                  # 204: 응답 body 없음
