import os
import requests

# 공공데이터포털에서 발급받은 서비스키를 환경변수 MFDS_API_KEY로 설정해서 사용하세요.
SERVICE_KEY = os.environ.get("MFDS_API_KEY", "")
if not SERVICE_KEY:
    raise SystemExit("환경변수 MFDS_API_KEY를 설정해주세요.")

url = f"https://api.data.go.kr/openapi/tn_pubr_public_nutri_food_info_api?serviceKey={SERVICE_KEY}&pageNo=1&numOfRows=3&type=json"

payload = {}
headers = {
  'Cookie': 'clientid=040013203258'
}

response = requests.request("GET", url, headers=headers, data=payload)

print(response.text)