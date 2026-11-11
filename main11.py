# Sub-dependencies
# 의존성이 또 다른 의존성을 필요로 하는 것 — sub-dependency
# 여러 개의 의존성이 연쇄적으로 이어지는 전체 구조 — dependency chain(의존성 체인)

from fastapi import FastAPI, Depends

app = FastAPI()

todos = [
    {"id": 1, "title": "우유 사기", "completed": False},
    {"id": 2, "title": "책 반납하기", "completed": True},
    {"id": 3, "title": "빨래하기", "completed": False},
    {"id": 4, "title": "우유 배달 확인", "completed": False},
]


# 1. 기본 개념: 의존성이 또 다른 의존성을 가질 수 있음 (중첩)
# A = Depends(B)
# B = Depends(C)
# A > B > C

def get_completed_filter(completed: bool | None = None):
    # completed는 타입이 bool 아니면 None인데 디폴트 값은 None
    # 디폴트 값은 전달한 argument가 없는 경우에 적용
    print("get_completed_filter 실행됨")
    return completed # 전달한 값을 리턴, 없으면 None 리턴

def get_filtered_todos(completed: bool | None = Depends(get_completed_filter), keyword: str | None = None):
    # completed는 타입이 bool 아니면 None인데 디폴트 값이 Depends(get_completed_filter)
    result = todos # completed도 None이고, keyword도 None이면 전체가 리턴됨
    if completed is not None:
        result = [t for t in result if t["completed"] == completed]
        # t["completed"]가 전달받은 completed와 일치하는 대상만 result에서 추려서 리스트에 저장
    if keyword is not None:
        result = [t for t in result if keyword in t["title"]]   # 이 지점의 result는 직전 if 문에서 만든 result임
        # 전달받은 keyword가 t["title"]에 포함된 대상만 추려서 리스트에 저장
    return result


@app.get("/todos")
# GET http://127.0.0.1:8000/todos?completed=false&keyword=우유
def get_todos(filtered: list = Depends(get_filtered_todos)):
    # dependency chain
    # get_todos → get_filtered_todos → get_completed_filter
    
    # 1. GET http://127.0.0.1:8000/todos?completed=false&keyword=우유 요청
    # 2. FastAPI가 get_todos의 매개변수 filtered의 값은 Depends(get_filtered_todos)
    #    먼저 get_filtered_todos를 실행해야 함
    # 3. get_filtered_todos의 매개변수 completed의 값은 Depends(get_completed_filter)
    #    먼저 get_completed_filter를 실행해야 함 
    # 4. 가장 안쪽 의존성부터 해결하는 형태
    #    실행 순서는 get_completed_filter → get_filtered_todos → get_todos 순으로, 가장 안쪽 의존성부터 먼저 실행
    # 5. get_completed_filter(completed=False) 실행 → 쿼리 파라미터 completed(false)를 받아서 그대로 False 반환
    
    #    dependency chain에 있는 함수들은 자신이 호출되는 시점에 요청으로 넘어온 쿼리 파라미터 값을 읽어 간다 ★★★
    #    dependency chain에 있는 함수들은 파라미터에 값을 채우는 방식이 동일
    
    # 함수 파라미터에 채워 넣을 값은 어디서 가져와야 하는가?

    # 0. 기본값이 Depends(...)인가? → 그 callable을 실행한 결과값으로 채움 (최우선)

    # (Depends가 아니라면, 아래 순서로 판단)
    # A. 경로에 {} 형태로 함수 파라미터와 같은 이름이 있는가? → 경로 파라미터, URL 경로에서 가져옴
    # B. 경로에 {} 형태로 함수 파라미터와 같은 이름이 없다면?
    # B-1. 함수 파라미터의 타입이 단순 타입 → 쿼리 파라미터에서 가져옴
    # B-2. 함수 파라미터의 타입이 BaseModel → 요청의 body에서 가져옴

    # 6. 5의 반환값(False)이 get_filtered_todos의 completed 매개변수로 전달됨
    # 7. get_filtered_todos(completed=False, keyword="우유") 실행
    # 8. 7의 리턴 값(필터링된 리스트)이 get_todos의 filtered 매개변수로 전달됨
    # 9. 아래 코드 실행; return filtered
    # A. filtered = [
    #     {"id": 1, "title": "우유 사기", "completed": False},
    #     {"id": 4, "title": "우유 배달 확인", "completed": False},
    # ]에 대해서
    # B. FastAPI가 filtered에 대해서 직렬화를 실행해서 JSON 형태의 응답으로 클라이언트에 전달
    # [
    #   {
    #     "id": 1,
    #     "title": "우유 사기",
    #     "completed": false
    #   },
    #   {
    #     "id": 4,
    #     "title": "우유 배달 확인",
    #     "completed": false
    #   }
    # ]
    return filtered


# 2. 캐싱: 어떤 sub-dependency가 한 요청 안에서 여러 번 쓰이면 한 번만 실행됨

@app.get("/todos/debug")
# GET http://127.0.0.1:8000/todos/debug?completed=false
def get_todos_debug(
    filtered: list = Depends(get_filtered_todos),
    # Dependency chain의 형태는
    # filtered → get_filtered_todos → get_completed_filter
    #                                 ------------------
    #                                 이 부분이 아래에서 다시 호출

    completed_again: bool | None = Depends(get_completed_filter), 
    # 위에서 이미 호출한 get_completed_filter의 리턴을 재사용
):
    # 콘솔에 "get_completed_filter 실행됨"이 한 번만 출력됨 (캐시되어 재사용됨)
    # Depends()의 파라미터 중 use_cache: bool = True가 디폴트
    return {"filtered": filtered, "completed_again": completed_again}


# 3. use_cache=False: 캐싱을 끄고 매번 새로 실행하고 싶은 경우

@app.get("/todos/no-cache")
# GET http://127.0.0.1:8000/todos/no-cache?completed=false
def get_todos_no_cache(
    filtered: list = Depends(get_filtered_todos),
    completed_again: bool | None = Depends(get_completed_filter, use_cache=False),
    # use_cache=False: 캐시된 결과가 있어도 재사용하지 말고 매번 새로 실행
):
    # 콘솔에 "get_completed_filter 실행됨"이 두 번 출력됨
    return {"filtered": filtered, "completed_again": completed_again}

# 어떤 경우에 use_cache=False를 사용?

# 랜덤 값을 생성해서 활용하는 경우 이전 랜덤 값을 다시 사용하면 안됨
# 매번 새로운 ID(request ID)를 생성해서 발급하는 경우
# 증가/감소된 전역 카운터 리턴해서 참조/사용하는 경우