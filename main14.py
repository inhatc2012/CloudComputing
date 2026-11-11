# Dependencies with yield

from fastapi import FastAPI, Depends

app = FastAPI()

# 기본 패턴
# depends(■)의 ■ 내에 yield가 있는 형태: def get_todos(log_file=Depends(get_log_file)):

def get_log_file():
    f = open("access.log", "a")     # 파일을 오픈
    try:
        yield f                     # yield ■의 ■가 라우트 함수 get_todos의 log_file에 주입되는 값
    finally:
        f.close()                   # 정리: finally는 무조건 실행

# next()는 FastAPI가 내부적으로 자동으로 호출
# 1. Depends(get_log_file) 처리 시점 → next() 호출 → yield까지 실행해서 f를 log_file에 할당
# 2. return 실행으로 응답을 만들어 보낸 직후 → next() 호출 → yield 이후 실행 (e.g., 자원 정리)

@app.get("/todos")
# GET http://127.0.0.1:8000/todos
def get_todos(log_file=Depends(get_log_file)):
    #                  ---------------------
    #                  제너레이터 객체가 생성됨

    # ⓐ 요청 GET http://127.0.0.1:8000/todos에 대해서 log_file=Depends(get_log_file)가 먼저 실행
    # ⓑ FastAPI에 의한 next(get_log_file) 실행 → yield까지 실행해서 f를 얻음 
    #    이 시점에서 get_log_file의 실행 흐름은 yield f에서 멈추어 있음
    # ⓒ f를 매개변수 log_file에 전달한 다음 get_todos 함수 body 실행
    
    log_file.write("GET /todos 요청 처리\n")
    return {"message": "todos 조회"}
    # ⓓ 결과로 만들어진 응답이 클라이언트에게 전송된 직후 멈추어 있던 get_log_file의 실행 흐름은
    # FastAPI에 의한 next(get_log_file)으로 yield 다음부터 실행

# --------------------------------------------------------------------------------------------------------

# 예외 처리
def get_log_file_v2():
    f = open("access.log", "a")
    try:
        yield f
    except Exception as e:
        f.write(f"에러 발생: {e}\n")
        raise   # raise e <--------- ★
    finally:
        f.close()

@app.get("/todos/error")
# GET http://127.0.0.1:8000/todos/error
def get_todo_error(log_file=Depends(get_log_file_v2)):
    log_file.write("GET /todos/error 요청 처리\n")
    raise ValueError("어떤 문제가 발생함") # throw

    # raise가 실행되면 이후 코드는 실행되지 않고 함수 get_todo_error()는 종료
    # raise로 예외를 발생시키면 FastAPI에 의해서 멈춰있는 yield 의존성에 해당 예외를 전달
    # throw()는 개발자가 직접 호출, 
    # path operation function 내에서 raise() → 자동으로 의존성의 yield  지점으로 예외를 throw

# ⓐ 요청 GET http://127.0.0.1:8000/todos/error에 대해서 log_file=Depends(get_log_file2)가 먼저 실행
# ⓑ FastAPI에 의한 next(get_log_file_v2()) 실행 → yield까지 실행해서 f를 반환 
#    (get_log_file2의 실행 흐름은 yield f에서 멈추어 있음)
# ⓒ f를 매개변수 log_file에 전달해서 get_todo_error 함수가 실행

# ⓓ get_todo_error() 함수 내에서 어떤 에러 상황이 발생
#    raise ValueError("어떤 문제가 발생함")로 그 상황을 시뮬레이션한 것
#    → 이 시점에서 get_todo_error()는 종료, 끝, 바이바이~
# ⓔ FastAPI가 ⓓ의 예외를 감지
# ⓕ FastAPI에 의해서 제너레이터 get_log_file_v2의 멈춰 있는 지점을 대상으로 throw()를 호출
#    — throw()에 전달되는 것은 ⓓ 단계의 raise ValueError("어떤 문제가 발생함")로 발생한 예외 객체
#    — "네가 멈춰있는 yield f 지점에서, 이 예외가 발생한 것처럼 해라"
# ⓖ get_log_file_v2의 except 블록 실행
# ⓗ ★ 지점: raise를 통해 현재 처리중인 예외를 바깥으로 다시 전달
# ⓘ get_log_file_v2의 finally에서 파일을 닫음
# ⓙ get_log_file_v2() 내부의 raise로 되돌아 온 예외는 갈 곳이 없음(get_todo_error()는 종료)
#    FastAPI가 되돌아온 예외를 500 Internal Server Error 응답으로 클라이언트에 전달
# --------------------------------------------------------------------------------------------------------

# HTTPException이 아닌 ValueError와 같은 일반 파이썬 예외가 FastAPI에 전달되면
# FastAPI는 그걸 자동으로 500(Internal Server Error) 응답으로 변환해서 클라이언트에게 전달

# 500 Internal Server Error
# "클라이언트 너는 잘못이 없다", "서버 잘못이야, 그런데, 어떤 잘못인지는 알려주지 않아"
# 이 에러 코드를 보면, 해당 API를 사용하는 개발자/이용자는 문제 대응을 할 수 없음
# "HTTPException으로 구체적으로 응답하자"

# --------------------------------------------------------------------------------------------------------

# HTTPException으로 바꿔서 던지기
from fastapi import HTTPException

def get_log_file_v3():
    f = open("access.log", "a")
    try:
        yield f
    except Exception as e:
        f.write(f"에러 발생: {e}\n")
        # raise 대신, HTTPException으로 바꿔서 던짐
        raise HTTPException(status_code=400, detail=f"요청 처리 중 문제가 발생했습니다: {e}")
        # HTTPException(status_code=..., detail=...)는 원하는 상태 코드(400, 404, 403,...)와 메시지를 직접 지정
    finally:
        f.close()


@app.get("/todos/error2")
# GET http://127.0.0.1:8000/todos/error2
def get_todo_error2(log_file=Depends(get_log_file_v3)):
    log_file.write("GET /todos/error2 요청 처리\n")
    raise ValueError("어떤 문제가 발생함")  # 이 지점에서 get_todo_error2()은 끝, 종료, 바이바이~
    # 만약 이 부분이 raise HTTPException(status_code=400, detail="어떤 문제가 발생함")이면
    # get_log_file_v3()의 raise HTTPException(status_code=400, detail=f"요청 처리 중 문제가 발생했습니다: {e}")는
    # raise로 해도 OK
    
    # get_log_file_v3의 yield 지점으로 전달된 이 ValueError는 except에서 HTTPException(400)으로 바꿔서 바깥으로 전달
    # 이를 FastAPI가 받아서 응답 형태로 클라이언트에 전달
    # 클라이언트는 500이 아니라 400 응답과, 지정한 detail 메시지를 받게 됨


# --------------------------------------------------------------------------------------------------------


# Sub-dependencies의 정리 순서 — 여러 개의 yield 의존성이 체인을 이룰 때, 정리 코드 finally가 실행되는 순서
def get_dependency_a2():
    print("A 준비")
    try:
        yield "a"
    finally:
        print("A 정리")


def get_dependency_b2(a=Depends(get_dependency_a2)):
    print("B 준비")
    try:
        yield "b"
    finally:
        print("B 정리")

@app.get("/todos/chain")
# GET http://127.0.0.1:8000/todos/chain
def get_todos_chain(b=Depends(get_dependency_b2)):
    print("라우트 함수 실행")
    return {"message": "완료"}
    # get_dependency_b2, get_dependency_a2의 멈추어 있는 yield는 멈춘 상태 유지

@app.get("/todos/chain-error")
# GET http://127.0.0.1:8000/todos/chain-error
def get_todos_chain_error(b=Depends(get_dependency_b2)):
    # ⓐ b=Depends(get_dependency_b2)가 실행되어야 함
    
    # ⓑ get_dependency_b2의 a=Depends(get_dependency_a2)가 실행되어야 함
    
    # ⓒ get_dependency_a2()가 실행, yield "a", get_dependency_b2의 a='a'가 됨
    
    # ⓓ get_todos_chain_error의 b='b' # get_dependency_b2()는 그냥 yield "b"임
    
    # 현재 get_dependency_b2, def get_dependency_a2() 모두 yield에 멈추어 있음
    print("라우트 함수 실행 (예외 발생 예정)")
    raise ValueError("체인 중 에러") # 이 지점에서 get_todos_chain_error()는 끝, 종료, 바이바이~
    
    # ⓔ FastAPI는 get_todos_chain_error 함수의 실행을 그 즉시 중단

    # ⓕ 멈춰있는 의존성들에게 순서대로 throw()로 전달하는데

    # ⓕ-1 get_dependency_b2의 "yield 'b'" 지점에 예외 주입
    # ⓕ-2 get_dependency_b2의 finally: print("B 정리") 실행

    # ⓕ-3 get_dependency_a2의 "yield 'a'" 지점에 예외 주입
    # ⓕ-4 get_dependency_a2의 finally: print("A 정리") 실행

    # ⓕ-5 최종적으로 FastAPI가 500 에러 응답을 만들어 클라이언트에게 전송
    # 왜냐하면, get_dependency_b2와 get_dependency_a2 모두 except 없이 try/finally만 있음
    # 따라서 각자 finally 부분만 실행되어 예외 자체는 처리하지 않았으므로 예외는 그대로 바깥으로 계속 전파


    # finally가 실행되는 경우
    # 1. 멈추어 있던 yield 지점에, 외부에서 던져 넣은 예외 처리 흐름, except → finally
    # 2. 멈추어 있던 yield 지점에서 다시 한번 더 next()가 호출
    #    2.1. yield 이후 코드 자체에서 새로운 예외가 발생하지 않으면 → 그대로 finally
    #    2.2. yield 이후 코드 자체에서 예외가 발생하면 → except (있다면) → finally
    #         yield 이후 코드 자체에서 예외가 발생하면 → except (없다면) → finally, 예외는 의존성 흐름의 이전 단계로 전파