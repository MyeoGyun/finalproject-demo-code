from fastapi import FastAPI, HTTPException
from google.cloud import bigquery
from pydantic import BaseModel
import random

app = FastAPI()

# BigQuery 클라이언트 설정
client = bigquery.Client()

# 로그인 요청 모델
class LoginRequest(BaseModel):
    user_id: int
    password: str

# 로그인 확인 함수
def verify_user(user_id: int, password: str):
    query = f"""
        SELECT user_id, password
        FROM `final-project-446409.demo_set.user_table`
        WHERE user_id = {user_id}
    """
    query_job = client.query(query)
    result = query_job.result()

    if not result.total_rows:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 비밀번호 확인
    for row in result:
        if row["password"] != password: # 비밀번호 실패 예외 처리
            raise HTTPException(status_code=400, detail="Incorrect password")
    
    return {"message": f"{user_id}님 로그인에 성공했습니다!"}

@app.post("/login")
def login(request: LoginRequest):
    try:
        return verify_user(request.user_id, request.password)
    except Exception as e:
        return {"error": str(e)}

@app.get("/friends/{user_id}")
def get_friends(user_id: int):
    # BigQuery에서 친구 목록을 가져오는 쿼리
    query = f"""
        SELECT u.user_name, u.profile_picture_url
        FROM `final-project-446409.demo_set.user_table` u
        JOIN `final-project-446409.demo_set.friends_table` f
        ON CAST(f.friend_id AS STRING) = CAST(u.user_id AS STRING)
        WHERE CAST(f.user_id AS STRING) = CAST({user_id} AS STRING)
    """
    
    query_job = client.query(query)
    result = query_job.result()

    if not result.total_rows:
        raise HTTPException(status_code=404, detail="No friends found")

    friends_info = []
    for row in result:
        friends_info.append({
            "user_name": row["user_name"],
            "profile_picture": row["profile_picture_url"]
        })

    return {"friends": friends_info}

@app.get("/vote/questions")
def get_random_questions(user_id: str):  # user_id를 STRING으로 변경
    # 이성친구 목록 가져오기
    query_gender_friends = f"""
        SELECT u.user_name, u.profile_picture_url, u.gender
        FROM `final-project-446409.demo_set.user_table` u
        JOIN `final-project-446409.demo_set.friends_table` f
        ON f.friend_id = u.user_id  -- STRING이므로 CAST 제거
        WHERE f.user_id = '{user_id}'  -- STRING이므로 따옴표 추가
    """
    
    query_job_friends = client.query(query_gender_friends)
    result_friends = query_job_friends.result()

    if not result_friends.total_rows:
        raise HTTPException(status_code=404, detail="No friends found for this user")

    # 사용자의 성별 가져오기 (이성친구와 동성친구 구분을 위해)
    query_user_gender = f"""
        SELECT gender
        FROM `final-project-446409.demo_set.user_table`
        WHERE user_id = '{user_id}'  -- STRING이므로 따옴표 추가
    """
    query_job_user = client.query(query_user_gender)
    result_user = query_job_user.result()
    user_gender = next(result_user)["gender"] if result_user.total_rows else "unknown"

    male_friends = []  # 남자 친구 리스트
    female_friends = []  # 여자 친구 리스트
    
    # 친구를 성별에 따라 분류
    for row in result_friends:
        if row["gender"] == "male":
            male_friends.append(row)
        else:
            female_friends.append(row)

    # 질문 리스트 가져오기 (점수가 NULL이 아닌 질문만)
    query_questions = """
        SELECT question, score
        FROM `final-project-446409.demo_set.sample_question_table`
        WHERE score IS NOT NULL
        ORDER BY RAND()
        LIMIT 10
    """
    
    query_job = client.query(query_questions)
    result_questions = query_job.result()

    if not result_questions.total_rows:
        raise HTTPException(status_code=404, detail="No questions found")

    questions_info = []
    for row in result_questions:
        # 이성친구가 없으면 score >= 1.25인 질문 제외
        if len(male_friends) == 0 or len(female_friends) == 0:
            if row["score"] >= 1.25:
                continue  # 이성친구가 없으면 score >= 1.25인 질문 제외
        
        questions_info.append({
            "question": row["question"],
            "score": row["score"]
        })

    all_questions = []
    for question_data in questions_info:
        question = question_data["question"]
        score = question_data["score"]

        friends_info = []  # 각 질문에 배정할 친구 리스트 초기화

        # score >= 1.25일 경우 이성친구 및 동성친구 배정 로직
        if score >= 1.25:
            # 사용자의 성별에 따라 이성친구 결정
            opposite_gender_friends = female_friends if user_gender == "male" else male_friends
            same_gender_friends = male_friends if user_gender == "male" else female_friends

            # 이성친구 수에 따라 배정
            if len(opposite_gender_friends) <= 2:
                # 이성친구가 2명 이하일 경우 모든 이성친구 배정
                for friend in opposite_gender_friends:
                    friends_info.append({
                        "user_name": friend["user_name"],
                        "profile_picture": friend["profile_picture_url"]
                    })
            else:
                # 이성친구가 4명 이상일 경우 2~4명 랜덤 선택
                num_opposite = random.randint(2, min(4, len(opposite_gender_friends)))
                random.shuffle(opposite_gender_friends)
                for friend in opposite_gender_friends[:num_opposite]:
                    friends_info.append({
                        "user_name": friend["user_name"],
                        "profile_picture": friend["profile_picture_url"]
                    })

            # 이성친구가 2~3명만 배정된 경우, 나머지 1~2명은 동성친구로 채움 (총 4명까지)
            current_count = len(friends_info)
            if 2 <= current_count <= 3:
                needed_count = 4 - current_count  # 필요한 동성친구 수 (1 또는 2)
                random.shuffle(same_gender_friends)
                for friend in same_gender_friends[:needed_count]:
                    friends_info.append({
                        "user_name": friend["user_name"],
                        "profile_picture": friend["profile_picture_url"]
                    })

        else:
            # score < 1.25일 경우 이성친구가 아닌 친구들을 무작위로 배정 (기존 로직 유지)
            query_friends = f"""
                SELECT u.user_name, u.profile_picture_url
                FROM `final-project-446409.demo_set.user_table` u
                JOIN `final-project-446409.demo_set.friends_table` f
                ON f.friend_id = u.user_id  -- STRING이므로 CAST 제거
                WHERE f.user_id = '{user_id}'  -- STRING이므로 따옴표 추가
                ORDER BY RAND()
                LIMIT 4
            """
            query_job_friends = client.query(query_friends)
            result_friends = query_job_friends.result()

            if not result_friends.total_rows:
                raise HTTPException(status_code=404, detail="No friends found for this user")

            for row in result_friends:
                friends_info.append({
                    "user_name": row["user_name"],
                    "profile_picture": row["profile_picture_url"]
                })

        # 각 질문에 대해 친구들 정보와 score 추가
        all_questions.append({
            "question": question,
            "score": score,
            "friends": friends_info  # friends_info에 담긴 친구들만 표시됨
        })

    return {"questions": all_questions}