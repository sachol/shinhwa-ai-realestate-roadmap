# HANDOFF — 신화AI부동산 공인중개사 AI 학습 진단 웹앱

> 본 문서는 작업 세션 간 컨텍스트 유지를 위한 인수인계 노트입니다.
> 다음 세션 시작 시 Claude Code가 이 파일을 가장 먼저 읽습니다.

## 1. 프로젝트 정체성

- **제작 주체**: 신화AI부동산 (대표: 노제승 / 닉네임 sachol)
- **최종 사용자**: 공인중개사 수강생 — 본 앱을 직접 사용해 진단을 받습니다.
- **대표님의 역할**: 공급자/강사. 진단 결과는 강의·컨설팅·수강생 트렌드 분석에 활용.
- **호칭**: 대표님께는 "신화 대표님"으로 호칭, 한국어 존댓말 사용.

## 2. 현재 배포 상태 (✅ Production)

| 항목 | 값 |
|------|---|
| GitHub | https://github.com/sachol/shinhwa-ai-realestate-roadmap (Public) |
| 배포 URL | https://shinhwa-ai-realestate-roadmap-rsaaiforumfighting.streamlit.app/ |
| 호스팅 | Streamlit Community Cloud (무료) |
| 데이터 저장소 | Google Sheets (`신화AI부동산_진단응답`) — gspread + 서비스 계정 |
| 강사 알림 | Gmail SMTP + 앱 비밀번호 → `sachol.cap@gmail.com` |
| 관리자 모드 | 사이드바 비밀번호 입력 (커스텀 비밀번호 설정 완료, 코드에는 미포함) |

### 활성 시크릿 (Streamlit Cloud Secrets에만 존재, .gitignore로 보호)
- `[gcp_service_account]` — 서비스 계정 JSON 키
- `[sheets]` — spreadsheet_id, worksheet_name="responses"
- `[admin]` — password (대표님이 설정한 강한 비밀번호)
- `[notify]` — Gmail 앱 비밀번호 + 발신/수신 이메일

## 3. 구현 완료된 기능

1. ✅ 면책조항 동의 게이트 (체크박스 + 시작 버튼)
2. ✅ 사업자 상호 / 본인 성함 / 이메일(필수) 입력
3. ✅ 주력 매물 10종 복수 선택 + 기타 자유 입력
4. ✅ AI 활용 목표 12종 복수 선택 + 기타 자유 입력
5. ✅ 5단계 숙련도 (입문 → 전문가 자동화)
6. ✅ 자동 로드맵 생성 (Markdown, 한글 PDF)
7. ✅ Google Sheets 자동 저장
8. ✅ 강사에게 진단 제출 즉시 이메일 알림 (HTML, 시트 바로가기 버튼 포함)
9. ✅ 관리자 모드 (전체 응답 테이블 + CSV 다운로드 + 종료 버튼)
10. ✅ 다크/라이트 모드 자동 대응 (prefers-color-scheme)
11. ✅ 한글 NanumGothic 폰트 번들 (Linux 호환)
12. ✅ **수강생 본인 이메일로 진단 결과 PDF 자동 첨부 발송** (2026-05-17 추가)

## 4. 미해결 백로그 (다음 세션 후보)

우선순위·소요시간 정리. 대표님이 다음 세션에 어느 것 할지 선택하시면 됩니다.

| 우선순위 | 기능 | 난이도 | 소요 | 비용 | 비고 |
|:---:|------|:---:|:---:|:---:|------|
| ~~1순위~~ | ~~수강생에게 PDF 자동 첨부 메일 발송~~ | — | — | — | ✅ **2026-05-17 완료** |
| **1순위** | 디자인 보강 — 좀 더 세련된 UI/모션 | 중간 | 반나절 | 무료 | 대표님이 1차 출시 후 아쉬워하신 부분 |
| **2순위** | 시트 응답을 숙련도/매물별 자동 분류 (강의반 배정용) | 중간 | 1~2시간 | 무료 | Apps Script 또는 Sheets 수식 |
| **3순위** | 재진단 비교 리포트 — 한 달 후 진행도 비교 | 중간 | 반나절 | 무료 | 이메일 기준 lookup |
| **4순위** | 결과에 추천 유튜브·블로그 콘텐츠 큐레이션 | 중간 | 1일 | 무료 | 매핑 테이블 + 수동 큐레이션 |
| **5순위** | LLM API로 custom_goals 자유입력 자동 분석·맞춤 코멘트 | 어려움 | 1일 | 유료 (소량) | Claude/GPT API |
| **6순위** | 베타 테스터 피드백 반영 (수강생 응답 후) | 가변 | 가변 | 무료 | 베타 결과에 따라 |

## 5. 베타 테스트 진행 상황

- 우수 수강생에게 카톡 안내 메시지 발송 예정 (또는 발송됨)
- 피드백 수집 항목: ① 진단 정확도(10점) ② 추가 항목 ③ 어색했던 부분
- 베타 결과는 응답 시트 + 강사 메일함에서 확인 가능

## 6. 보안 체크리스트 (절대 잊지 말 것)

- ❌ `.streamlit/secrets.toml` GitHub 푸시 금지 — `.gitignore` 처리됨
- ❌ 서비스 계정 JSON 키(`shinhwa-ai-realestate-*.json`) 푸시 금지 — `.gitignore` 처리됨
- ❌ Gmail 앱 비밀번호를 대화창에 노출 금지 — 모든 시크릿은 `secrets.toml` 또는 Streamlit Cloud Secrets에만
- ✅ 대표님이 직접 비밀번호·키를 회전(rotation) 하시려면:
  - Gmail 앱 비밀번호: https://myaccount.google.com/apppasswords
  - 서비스 계정 키: GCP Console → IAM → 서비스 계정 → 키 탭
  - 관리자 비밀번호: Streamlit Cloud Secrets에서 직접 편집

## 7. 다음 세션 재개 방법

대표님이 새 Claude Code 세션에서 다음과 같이 입력하시면 됩니다:

```
신화AI부동산 작업 이어서 하자. HANDOFF.md 읽고 현재 상태 확인한 뒤,
[하고 싶은 작업] 진행해줘.
```

예시:
- "수강생에게 PDF 자동 첨부 메일 발송 기능 추가하자" (1순위)
- "디자인을 좀 더 모던하게 보강하자" (2순위)
- "수강생 베타 피드백이 N건 들어왔어, 같이 검토해보자"

## 8. 파일 구조 (참고)

```
ai-roadmap-generator-for-agents/
├── app.py              # Streamlit 메인 (면책·설문·관리자·관리자 종료)
├── roadmap_logic.py    # 설문 → Markdown 로드맵 (매핑·5단계 트랙)
├── pdf_export.py       # Markdown → 한글 PDF (NanumGothic 번들)
├── storage.py          # Google Sheets 우선, SQLite 폴백 추상화
├── db.py               # SQLite 폴백 구현
├── notify.py           # Gmail SMTP 강사 알림
├── fonts/              # NanumGothic.ttf + Bold + LICENSE
├── requirements.txt    # Streamlit Cloud 의존성
├── .streamlit/
│   ├── secrets.toml    # (gitignore) 시크릿 일체
│   └── .gitignore      # secrets.toml 보호
├── README.md           # 공개 저장소용 설명
├── HANDOFF.md          # ← 이 파일
└── devlog.md           # 학습 실습 기록 (rona.so에 제출 완료)
```

## 9. 작업 일자

- 초기 구축 완료 + 배포: **2026-05-17**
- 다음 세션 예정: 미정
