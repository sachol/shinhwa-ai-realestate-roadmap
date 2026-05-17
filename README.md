# 신화AI부동산 — 공인중개사 맞춤 AI 학습 로드맵 진단

공인중개사 수강생의 설문 답변을 받아, 주력 매물·관심 업무·AI 숙련도에 따른 **개인화된 AI 학습 로드맵**을 자동 생성하고 **PDF로 다운로드**할 수 있는 Streamlit 웹앱입니다.

> **제작**: 신화AI부동산
> **대상 사용자**: 공인중개사 (강사 본인이 아닌 수강생/고객이 직접 입력)

## ✨ 주요 기능

- **면책 동의 게이트** — 첫 진입 시 이용 안내·면책 조항을 명시하고 체크박스 동의 후 진단 시작
- **개인화 진단** — 사업자 상호·성함·이메일 + 주력 매물(복수+기타) + AI 활용 목표(12종+기타) + 5단계 숙련도
- **자동 로드맵 생성** — 목표별 추천 도구 + 4주 학습 트랙 (Markdown)
- **한글 PDF 다운로드** — NanumGothic 임베딩, 수신자·발행일시 표시
- **Google Sheets 저장** — 응답이 자동으로 Google Sheet에 누적, 강사가 시트에서 직접 조회·필터링·내보내기
- **관리자 모드** — 사이드바 비밀번호 입력으로 전체 응답 테이블 + CSV 다운로드 (공개 화면엔 카운트만)
- **다크 모드 자동 대응** — `prefers-color-scheme`로 라이트/다크 자동 전환

## 🏗️ 기술 스택

| 영역 | 기술 |
|------|------|
| UI | Streamlit |
| 한글 PDF | fpdf2 + NanumGothic |
| 저장소 | Google Sheets (gspread) / SQLite 폴백 |
| 데이터프레임 | pandas |
| 인증 | Google Service Account |

## 🚀 로컬 실행

```bash
pip install -r requirements.txt
streamlit run app.py
```

### Secrets 설정 (선택)

Google Sheets 모드로 사용하시려면 `.streamlit/secrets.toml`을 다음 형식으로 작성하세요. (없으면 자동으로 로컬 SQLite로 폴백)

```toml
[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "...@....iam.gserviceaccount.com"
# ... 나머지 필드도 JSON 파일 그대로 옮기기

[sheets]
spreadsheet_id = "구글시트 URL의 /d/ 와 /edit 사이 값"
worksheet_name = "responses"

[admin]
password = "강한_관리자_비밀번호"
```

서비스 계정 이메일에 해당 Google Sheet의 **편집자** 권한을 부여해야 합니다.

## 📁 프로젝트 구조

```
.
├── app.py              # Streamlit 메인 (UI · 면책 · 설문 · 관리자 모드)
├── roadmap_logic.py    # 설문 → Markdown 로드맵 생성 (매핑 + 4주 트랙)
├── pdf_export.py       # Markdown → 한글 PDF (NanumGothic, 안전 글리프 폴백)
├── storage.py          # Google Sheets 우선, SQLite 폴백 저장소 추상화
├── db.py               # SQLite 폴백 구현
├── requirements.txt
└── .streamlit/
    └── secrets.toml    # (gitignore) 서비스 계정 + 시트 ID + 관리자 비밀번호
```

## ⚖️ 면책 사항

본 도구가 제공하는 모든 결과물은 **일반적인 정보 제공 및 교육 목적**의 참고자료이며, 법률·세무·금융·투자 자문이 아닙니다. 이를 활용해 발생한 모든 의사결정과 그 결과는 사용자 본인의 책임이며, 신화AI부동산은 어떠한 책임도 지지 않습니다.

## 📝 라이선스

© 신화AI부동산. All rights reserved.
