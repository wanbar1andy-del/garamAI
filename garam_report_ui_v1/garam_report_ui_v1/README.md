# GARAM Report/UI v1 패키지

## 포함 파일
- report_schema_v1.md : JSON 스키마 정의
- report_example.json : 예시 report.json
- generate_report_md.py : JSON -> Markdown 생성기 (MD022/MD032 준수)
- garamui_app_streamlit.py : Streamlit 기반 GaramUI 최소 구현(Overview/Checks/Details)
- ui_field_mapping.md : UI 매핑 표준

## 빠른 사용
1) 예시 보고서로 MD 생성:
   python generate_report_md.py report_example.json --out report_example.md

2) GaramUI 실행(예시):
   streamlit run garamui_app_streamlit.py

## 운영 규칙 (강제)
- SSOT는 report.json
- report.md는 report.json에서 생성(수정 금지)
- UI는 latest.json만 파싱
