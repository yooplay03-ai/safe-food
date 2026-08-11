import os
import requests

# 본인의 카카오 REST API 키를 환경변수 KAKAO_API_KEY로 설정해서 사용하세요.
KAKAO_KEY = os.environ.get("KAKAO_API_KEY", "")
if not KAKAO_KEY:
    raise SystemExit("환경변수 KAKAO_API_KEY를 설정해주세요.")

url = "https://dapi.kakao.com/v2/local/search/category.json"
headers = {"Authorization": f"KakaoAK {KAKAO_KEY}"}

# 서울 강남역 근처 좌표 예시 (경도 x, 위도 y)
params = {
    "category_group_code": "FD6", # 음식점
    "x": "127.0276",
    "y": "37.4979",
    "radius": 1000,
    "sort": "distance",
    "size": 5,
}

response = requests.get(url, headers=headers, params=params)

print(f"상태 코드: {response.status_code}")
print(f"응답 결과: {response.text}")