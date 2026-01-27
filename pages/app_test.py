import streamlit as st 
st.title("앱 타이머 테스트")
name = st.text_input("작업 이름 입력")
st.write(f"안녕하세요, {name}님! 앱 타이머 테스트에 오신 것을 환영합니다.")
st.write("이곳은 앱 타이머의 기능을 테스트하는 공간입니다.")
print("App timer test running")