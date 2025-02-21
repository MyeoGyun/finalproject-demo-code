import streamlit as st
import requests

# FastAPI 서버 URL (예: 로컬 서버)
API_URL = "http://127.0.0.1:8001"

# 로그인 화면
def login_page():
    st.title("질문 투표 이성배치 알고리즘 Demo")
    user_id = st.text_input("Enter User ID to Login:")
    password = st.text_input("Enter Password", type="password")
    
    if st.button("로그인"):
        if user_id and password:
            payload = {
                "user_id": int(user_id),  # user_id는 숫자로 변환
                "password": password
            }
            response = requests.post(f"{API_URL}/login", json=payload)
            
            if response.status_code == 200:
                st.session_state.user_id = user_id  # 로그인 후 세션에 유저 ID 저장
                st.success(f"User {user_id} logged in successfully.")
                st.session_state.logged_in = True
                # 로그인 후 새로고침은 한 번만 호출
                st.rerun()  # 화면을 새로고침하여 화면 전환
            else:
                st.error("유저 ID가 존재하지 않거나 비밀번호가 틀렸습니다.")
        else:
            st.error("유저 ID와 비밀번호를 입력해 주세요.")

# 친구 목록 보기 화면
def friends_page():
    st.title("친구 목록")
    
    if "user_id" in st.session_state:
        response = requests.get(f"{API_URL}/friends/{st.session_state.user_id}")
        
        if response.status_code == 200:
            friends = response.json().get("friends", [])
            
            # 친구 목록이 비어있는지 확인
            if not friends:
                st.write("친구가 없습니다.")
            else:
                # 친구 수 표시
                st.write(f"(친구 목록에 {len(friends)}명이 있습니다.)")
                
                for friend in friends:
                    # 친구 카드 레이아웃 (반응형 카드 디자인)
                    col1, col2 = st.columns([1, 4])
                    
                    with col1:
                        # 프로필 사진을 원형으로 표시 (반응형 크기 조정)
                        st.markdown(
                            f"""
                            <div style="width: 60px; height: 60px; border-radius: 50%; overflow: hidden; margin-bottom: 10px;">
                                <img src="{friend['profile_picture']}" width="60" height="60" style="object-fit: cover;" />
                            </div>
                            """, unsafe_allow_html=True)
                    
                    with col2:
                        # 친구 이름을 표시 (스타일링된 제목)
                        st.markdown(
                            f"""
                            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                                <h3 style="margin-right: 10px; font-size: 16px; font-weight: bold;">{friend['user_name']}</h3>
                            </div>
                            """, unsafe_allow_html=True)
                
        else:
            # 실패한 상태 코드와 응답 내용 표시
            st.error(f"친구 목록을 불러오는 데 실패했습니다. 상태 코드: {response.status_code}")
            st.write(f"응답 내용: {response.text}")  # 실패한 이유를 보다 명확히 알 수 있도록 응답 텍스트도 출력
    
    if st.button("로그아웃"):
        st.session_state.logged_in = False
        st.rerun()

def vote_page():
    st.title("칭찬 투표")
    
    if "user_id" in st.session_state:
        response = requests.get(f"{API_URL}/vote/questions?user_id={st.session_state.user_id}")
        
        if response.status_code == 200:
            questions = response.json().get("questions", [])
            
            for i, question_data in enumerate(questions, 1):
                st.write(f"### {i}. {question_data['question']} (Score: {question_data['score']})")
                
                # 후보 친구들만 표시
                friends = question_data['friends']
                score = question_data['score']
                
                # 2열로 표시하려면 4명의 친구를 두 칼럼으로 나눔
                cols = st.columns(2)  # 두 열로 나누기
                
                # 첫 번째 열 친구 표시
                with cols[0]:
                    st.write(f"1. {friends[0]['user_name']}")
                    st.markdown(
                        f"""
                        <div style="width: 100px; height: 100px; border-radius: 50%; overflow: hidden; margin-bottom: 10px;">
                            <img src="{friends[0]['profile_picture']}" width="100" height="100" style="object-fit: cover;" />
                        </div>
                        """, unsafe_allow_html=True)
                    st.write(f"3. {friends[2]['user_name']}")
                    st.markdown(
                        f"""
                        <div style="width: 100px; height: 100px; border-radius: 50%; overflow: hidden; margin-bottom: 10px;">
                            <img src="{friends[2]['profile_picture']}" width="100" height="100" style="object-fit: cover;" />
                        </div>
                        """, unsafe_allow_html=True)
                
                # 두 번째 열 친구 표시
                with cols[1]:
                    st.write(f"2. {friends[1]['user_name']}")
                    st.markdown(
                        f"""
                        <div style="width: 100px; height: 100px; border-radius: 50%; overflow: hidden; margin-bottom: 10px;">
                            <img src="{friends[1]['profile_picture']}" width="100" height="100" style="object-fit: cover;" />
                        </div>
                        """, unsafe_allow_html=True)
                    st.write(f"4. {friends[3]['user_name']}")
                    st.markdown(
                        f"""
                        <div style="width: 100px; height: 100px; border-radius: 50%; overflow: hidden; margin-bottom: 10px;">
                            <img src="{friends[3]['profile_picture']}" width="100" height="100" style="object-fit: cover;" />
                        </div>
                        """, unsafe_allow_html=True)

            # # 질문 새로고침 버튼 추가
            # if st.button("질문 새로고침"):
            #     st.session_state.refresh = True
            #     st.rerun()  # 페이지를 새로고침하여 다시 질문을 불러옴
            # 질문 새로고침 버튼 추가
            if st.button("질문 새로고침"):
                st.session_state.refresh = True
                # 새로고침을 한 번만 처리하도록 리프레시 값 변경
                st.session_state["questions"] = None  # 질문 상태 초기화 후 새로 고침

        else:
            st.error(f"질문을 불러오는 데 실패했습니다. 상태 코드: {response.status_code}")
            st.write(f"응답 내용: {response.text}")
    
    if st.button("로그아웃"):
        st.session_state.logged_in = False
        st.rerun()

# 메인 페이지
def main():
    if "logged_in" not in st.session_state or not st.session_state.logged_in:
        login_page()
    else:
        option = st.selectbox("선택하세요", ["친구 목록 보기", "칭찬 투표 시작"])
        
        if option == "친구 목록 보기":
            friends_page()
        elif option == "칭찬 투표 시작":
            vote_page()

if __name__ == "__main__":
    main()