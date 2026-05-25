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
| 수강생 PDF 메일 | 동일 Gmail SMTP 인프라 재사용 (HTML 본문 + PDF 첨부) |
| 관리자 모드 | 사이드바 비밀번호 입력 + KPI/차트 대시보드 + CSV 다운로드 |
| 1:1 컨설팅 CTA | Gmail 웹 작성 링크 + 복사 폴백 (mailto 제거됨) |

### 활성 시크릿 (Streamlit Cloud Secrets에만 존재, .gitignore로 보호)
- `[gcp_service_account]` — 서비스 계정 JSON 키
- `[sheets]` — spreadsheet_id, worksheet_name="responses"
- `[admin]` — password (대표님이 설정한 강한 비밀번호)
- `[notify]` — Gmail 앱 비밀번호 + 발신/수신 이메일

## 3. 구현 완료된 기능

### 진단 핵심 흐름
1. ✅ 면책조항 동의 게이트 (체크박스 + 시작 버튼)
2. ✅ 사업자 상호 / 본인 성함 / 이메일(필수, 형식 검증) 입력
3. ✅ 주력 매물 10종 복수 선택 + 기타 자유 입력
4. ✅ AI 활용 목표 12종 복수 선택 + 기타 자유 입력
5. ✅ 5단계 숙련도 (입문 → 전문가 자동화)
6. ✅ 자동 로드맵 생성 (Markdown, 한글 NanumGothic PDF)
7. ✅ Google Sheets 자동 저장 (SQLite 폴백)

### 알림·후속 처리
8. ✅ 강사에게 진단 제출 즉시 이메일 알림 (HTML, 시트 바로가기 버튼)
9. ✅ 수강생 본인 이메일로 진단 결과 PDF 자동 첨부 발송 (재진단 CTA 포함)

### 운영·관리자
10. ✅ 관리자 모드 — 사이드바 비밀번호 진입 / 종료 버튼
11. ✅ 관리자 대시보드 통계 위젯
    - KPI 4타일: 총 응답 / 최근 7일 / 평균 숙련도(1-5) / Top 매물
    - 매물 분포·AI 목표 Top·숙련도 분포·일별 응답 추이 4개 차트
12. ✅ 전체 응답 테이블 + CSV 다운로드
12-1. ✅ **관리자 통계 필터 옵션** (2026-05-25 추가) — TEST 응답·중복 응답·대표님 본인 응답 토글 제외
    - 필터 즉시 KPI·차트·테이블·CSV 모두 반영
    - 베타 데이터 클렌징 (테스트 4~5건 제거) 후 통계 신뢰도 ↑
    - `_filter_rows()` 순수 함수로 분리, `OWNER_EMAILS`·`TEST_KEYWORDS` 상수로 확장 용이

### 디자인·UX
13. ✅ 다크/라이트 모드 자동 대응 (prefers-color-scheme)
14. ✅ Pretendard 폰트 (@import url) + 모던 폼·버튼 폴리시
15. ✅ 히어로 다층 그라데이션 + 부드러운 진입 애니메이션 + 모바일 폭 조정
16. ✅ 진단 결과 시각화 칩(chip) 배지 (선택 매물·목표를 알약 형태로)

### 비즈니스 전환
17. ✅ 결과 페이지 하단 "1:1 컨설팅 신청" CTA — Gmail 웹 작성 링크 (mailto 제거)
18. ✅ Naver/Daum/카톡 사용자용 복사 폴백 expander

## 4. 미해결 백로그 (다음 세션 후보)

| 우선순위 | 기능 | 난이도 | 소요 | 비용 | 비고 |
|:---:|------|:---:|:---:|:---:|------|
| ~~완료~~ | ~~수강생 PDF 자동 첨부 메일~~ | — | — | — | ✅ 2026-05-17 |
| ~~완료~~ | ~~1:1 컨설팅 CTA~~ | — | — | — | ✅ 2026-05-17 |
| ~~완료~~ | ~~디자인 보강 (Pretendard·칩·애니메이션)~~ | — | — | — | ✅ 2026-05-17 |
| ~~완료~~ | ~~관리자 대시보드 통계 위젯~~ | — | — | — | ✅ 2026-05-17 |
| **🟡 진행중(블록)** | 카카오톡 공유 버튼 (결과 페이지 CTA) | — | — | — | 코드 머지됨 / 4019 인증 에러로 운영 노출 차단 — 아래 11번 참고 |
| **2순위** | 시트 응답을 숙련도/매물별 자동 분류 (강의반 배정용) | 중간 | 1~2시간 | 무료 | Apps Script 또는 Sheets 수식 |
| **3순위** | 후속 메일 자동 발송 (1주/1달 뒤) | 중간 | 반나절 | 무료 | GitHub Actions 등 외부 스케줄러 필요 |
| **4순위** | 재진단 비교 리포트 (한 달 후 진행도) | 중간 | 반나절 | 무료 | 이메일 기준 lookup |
| **5순위** | 결과에 추천 유튜브·블로그 콘텐츠 큐레이션 | 중간 | 1일 | 무료 | 매핑 테이블 + 큐레이션 |
| **6순위** | LLM API로 custom_goals 자동 분석·맞춤 코멘트 | 어려움 | 1일 | 유료 (소량) | Claude/GPT API |
| **7순위** | 신화AI부동산 강의 커리큘럼 연동 | 어려움 | 1일+ | 무료 | 강의 메타데이터 정리 선행 |
| **상시** | 베타 테스터 피드백 반영 (수강생 응답 후) | 가변 | 가변 | 무료 | 베타 결과에 따라 |

### 4-1. 2026-05-25 데이터 기반 우선순위 재조정

베타 35건 응답을 클렌징(TEST 5 + 중복 16 제외) 후 **진짜 unique 사용자 14명** 발견. 평균 **2.1회 재제출 패턴**이 도구의 재방문 가치를 강하게 시사. 이 인사이트 반영하여 다음 우선순위 추천:

| 새 우선 | 작업 | 소요 | 데이터 기반 근거 |
|:---:|---|:---:|---|
| 🥇 | **시트 자동 분류** (기존 2순위) | 1~2h | 14명 unique에게 강의반 배정 즉시 적용 가능 / 곧 100건+ 되면 수동 분류 불가 |
| 🥈 | **재진단 비교 리포트** (기존 4순위 → 격상) | 4h | "같은 사람 평균 2.1회 재진단" 패턴 직접 활용 → 강의 락인·성과 입증 |
| 🥉 | **LLM custom_goals 분석** (기존 6순위 → 격상) | 1d | "부동산 시세 분석" AI 목표 1위 (~25건) — 자유 입력 안 더 구체적 페인 추출 |
| 4 | **후속 메일 자동 발송** (기존 3순위) | 4h | 응답 감소 추세 대응 (5/17 18건 → 5/23 3건) — 재참여 유도 |
| 5 | 추천 콘텐츠 큐레이션 (기존 5순위 유지) | 1d | "시세 분석"·"계약서 작성" 강한 수요 → 매칭 콘텐츠 |
| 6 | 강의 커리큘럼 연동 (기존 7순위 유지) | 1d+ | 메타데이터 정리 선행 필요 |
| 보류 | 카카오 4019 디버깅 (기존 1순위 진행중) | 1~3h | 부가 기능, 영향 적음, 가설 5개 잔존 (§ 11) |

→ 바쁜 주에는 **🥇 시트 자동 분류 (2h) 만 끝내도 큰 진전**. 다음 주에 🥈 재진단 비교 리포트 진행 권장.

## 5. 베타 테스트 진행 상황

- **베타 1차 안내 카톡 발송 완료** — 우수 수강생에게 진단 안내 메시지 발송 (2026-05-17 ~ 5/24)
- **2026-05-25 시점 응답 35건** (원본) / **클렌징 후 14명 unique 사용자**
  - TEST 응답 5건 제외 (TEST/테스트/홍길동 등 가명)
  - 중복 응답 16건 제외 (이메일 기준 최신 1건만 유지) → **평균 2.1회 재제출 패턴 발견**
  - 본인 응답 0건 제외 (체크 OFF 기준)
- **데이터 인사이트**:
  - 🎯 AI 활용 목표 1위: **부동산 시세 분석** (~25건)
  - 🏠 매물 1위: 아파트 (~19건) — 단 다양한 분야 분포 (편중 없음)
  - 📚 숙련도 분포: **입문~기본 88%** (1~3 단계) → 콘텐츠는 기초에 집중해야 ROI 최대
  - 📈 일별: 5/17 피크 18건 → 5/23 3건 (자연스러운 launch 후 안정화)
- 피드백 수집 항목: ① 진단 정확도(10점) ② 추가 항목 ③ 어색했던 부분
- 관리자 대시보드에 **통계 필터 옵션** 추가 완료 (2026-05-25) — TEST/중복/본인 응답 제외 토글로 분석 정확도 ↑
- 베타 응답 후 패턴 분석은 관리자 모드의 "AI 목표 Top" 차트가 가장 유용

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
- "카카오톡 공유 버튼 추가하자" (1순위)
- "시트 응답을 매물·숙련도별 자동 분류하게 하자" (2순위)
- "수강생 베타 피드백이 N건 들어왔어, 같이 검토해보자"

## 8. 파일 구조 (참고)

```
ai-roadmap-generator-for-agents/
├── app.py              # Streamlit 메인 (면책·설문·결과·관리자 대시보드)
├── roadmap_logic.py    # 설문 → Markdown 로드맵 (매핑·5단계 트랙)
├── pdf_export.py       # Markdown → 한글 PDF (NanumGothic 번들)
├── storage.py          # Google Sheets 우선, SQLite 폴백 추상화
├── db.py               # SQLite 폴백 구현
├── notify.py           # Gmail SMTP — 강사 알림 + 수강생 PDF 메일
├── fonts/              # NanumGothic.ttf + Bold + LICENSE
├── requirements.txt    # Streamlit Cloud 의존성
├── .streamlit/
│   ├── secrets.toml    # (gitignore) 시크릿 일체
│   └── .gitignore      # secrets.toml 보호
├── .devcontainer/      # GitHub Codespaces 설정 (자동 추가됨)
├── README.md           # 공개 저장소용 설명
├── HANDOFF.md          # ← 이 파일
└── devlog.md           # 학습 실습 기록 (rona.so에 제출 완료)
```

## 9. 작업 일자

- 초기 구축 완료 + 배포: **2026-05-17**
- 확장 1차 (PDF메일·CTA·디자인·관리자 대시보드): **2026-05-17 동일일**
- 카카오 공유 버튼 시도 + 4019 차단: **2026-05-18**
- 카카오 4019 추가 진단 (origin 가설 기각 + 비즈앱 스왑 실패) + 결정 보류: **2026-05-24**
- 관리자 통계 필터 옵션 운영 배포 (PR #4, 머지 d199bb7) + 베타 14명 unique 사용자 발견: **2026-05-25**
- 다음 세션 예정: **🥇 시트 자동 분류 (2h, 백로그 2순위) 또는 🥈 재진단 비교 리포트 (4h) — § 4-1 참고**

## 10. 운영 노트 (대표님 직접 확인 가능)

- **응답 시트 즉시 조회**: Google Drive → `신화AI부동산_진단응답` 열기
- **누가 진단받았나?**: 강사 알림 메일이 sachol.cap@gmail.com 받은편지함에 즉시 도착
- **전체 트렌드 보기**: 배포 URL → 사이드바에 관리자 비밀번호 입력 → 대시보드
- **수강생이 PDF 못 받았다고 하면?**: 스팸함 확인 권유 → 안 되면 관리자 대시보드에서 CSV 받아 직접 발송 가능

## 11. 🟡 카카오톡 공유 버튼 — 4019 인증 에러 미해결 (다음 세션 우선 항목)

### 현재 상태 (2026-05-18 마지막 작업)
- ✅ 코드 머지 완료 (PR #1) — `kakao_share_button()` 함수, `secrets.toml [kakao]`, `.gitignore` 캡처 보호
- ✅ 운영 안전 차단 (PR #2) — `app.py`의 `SHOW_KAKAO_SHARE = False` 토글로 렌더링 차단
- ❌ 카카오 4019 인증 에러 — 로컬·운영 둘 다 발생

### 카카오 디벨로퍼스 등록 상태 (확인됨)
- 앱명: 공인중개사를 위한 AI 학습 진단기 (앱 ID: 1460796)
- JavaScript 키: `27618d4c245595165d0bea959cd0bff3` (Streamlit Cloud Secrets·로컬 secrets.toml 동일)
- **제품 링크 관리 → 웹 도메인**: `https://shinhwa-...streamlit.app` + `http://localhost:8501` ✅
- **플랫폼 키 → JavaScript SDK 도메인**: `https://shinhwa-...streamlit.app` + `http://localhost:8501` ✅

### 의심 원인 (아직 미확정)
1. **Streamlit components iframe origin이 `null` 또는 srcdoc** → 카카오 SDK 도메인 검증 실패
2. 카카오 디벨로퍼스 도메인 등록 후 **최대 24h 캐시 반영 대기** (카카오 공식 안내)
3. **비즈앱 인증** 필요 가능성 (대표님 보유 비즈앱 키로 분리 테스트 미실시)

### 다음 세션에서 시도할 디버깅 순서
1. F12 콘솔에서 `[...document.querySelectorAll('iframe')].map(f => ({src: f.src, srcdoc: f.hasAttribute('srcdoc'), sandbox: f.sandbox.value}))` 실행 → iframe origin 확정
2. iframe이 `srcdoc`이면 → SDK 우회 방식 변경 (`components.v1.iframe`으로 외부 정적 HTML 임베드 또는 sharer URL 직접 호출)
3. iframe origin이 정상이면 → 비즈앱 키로 임시 교체 테스트 → 비즈앱 인증 필요 여부 확정
4. 24h 후 재시도도 병행 (도메인 캐시 반영 대기 가설 검증)

### 해결되면 부활시키는 법
- `app.py` 의 `SHOW_KAKAO_SHARE = False` → `True` 로 변경 후 PR/푸시
- 추가 secrets·등록 작업 불필요 (이미 모두 세팅됨)

### 만약 영영 안 되면
- 대표님이 "정 안 되면 카카오 버튼은 제외해도 좋다"고 말씀하셨음 (2026-05-18)
- 그 경우 `app.py` 의 `kakao_share_button()` 정의·호출·CSS 일괄 제거 PR 만들기

### 2026-05-24 추가 진단 세션 결과 (3시간) — 가설 ①·③ 모두 기각

**검증한 것 (모두 ✅ 통과, 그러나 4019 지속)**:

1. **iframe origin 가설 (①) 기각 ✅**
   - F12 콘솔 진단으로 확정: Streamlit components iframe 의 `src`·`srcdoc`·`sandbox` 실측치
     ```json
     {
       "src": "https://shinhwa-ai-realestate-roadmap-rsaaiforumfighting.streamlit.app/~/+/",
       "srcdoc": false,
       "sandbox": "allow-forms allow-modals allow-popups allow-popups-to-escape-sandbox allow-same-origin allow-scripts allow-downloads"
     }
     ```
   - 결론: iframe origin = 등록 도메인과 동일. `null` origin 가설 오류였음.

2. **비즈앱 인증 가설 (③) 검증 시도 → 4019 동일**
   - 대표님 보유 비즈앱(키: `589fd23fd9399d999afd314be11a0345`)으로 JS 키 임시 스왑
   - 비즈앱 JavaScript SDK 도메인에 streamlit·localhost 모두 등록 확인
   - 비즈앱 **제품 링크 관리**에 streamlit·localhost 신규 등록 (이전에 누락 발견)
   - 결과: 또 4019. UUID `a191f418-b3bd-4712-9b3e-6bcfe9cce11b`

3. **카카오 SDK 안내문 (재시도 후) 가이드 그대로 따랐는데도 실패**:
   - ① "웹 도메인을 [앱] > [제품 링크 관리]에 등록" ✅ 완료
   - ② "개발 환경 맞는 키 타입" — JS 키 사용 중 ✅
   - ③ "키 해시 Android 등록" — Web 케이스라 N/A

**남은 가능 원인 (다음 세션 우선 탐색)**:

| 우선순위 | 가설 | 확인 방법 |
|:---:|---|---|
| **A** | Streamlit secrets 캐시 미반영 (비즈앱 키 swap이 실제로 적용 안 됐을 수 있음 — 재시작 후에도 옛 키 사용) | F12 → Network 탭 → `sharer.kakao.com` 요청의 `app_key` 파라미터 실측 |
| **B** | 카카오 측 도메인 등록 캐시 (보통 즉시지만 가끔 지연) | 24h 후 동일 조건에서 재시도 |
| **C** | 비즈앱이라도 "카카오톡 공유" 제품 활성화 토글 별도 필요 | 디벨로퍼스 콘솔 → 제품 설정 → 카카오 메시지/공유 활성화 여부 |
| **D** | components.html 의 `Kakao.init()` 타이밍 — iframe load 와 SDK script load 사이 race condition | `Kakao.isInitialized()` 디버깅 로그 추가 |
| **E** | `objectType: 'text'` 의 카카오 측 제약 (비즈앱이라도 메시지 템플릿 검수 필요할 수도) | `objectType: 'feed'` 로 변경하여 동일 에러인지 비교 |

**대표님 결정 (2026-05-24)**:
- 오늘은 여기까지. **두 가지 옵션 보존** — ① 차분히 다시 진행 / ② 카카오 버튼 완전 제거.
- 결정은 다음 세션에서. 그때까지 현재 차단 상태(`SHOW_KAKAO_SHARE = False`) 그대로 유지.

**로컬 환경 백업 상태**:
- `app.py:25` → `SHOW_KAKAO_SHARE = False` 로 롤백 완료 (커밋 안 함, 원래 상태)
- `.streamlit/secrets.toml` → `[kakao] javascript_key` 일반앱 키로 롤백, 비즈앱 키는 주석으로 보존 (다음 세션 즉시 swap 가능)
- 비즈앱의 제품 링크 관리·SDK 도메인 등록은 **유지** (롤백 X, 다음 시도 시 유용)

## 12. 작업 일자 (업데이트)

- 카카오 공유 버튼 시도 + 4019 차단 운영 안전 처리: **2026-05-18**
- 추가 진단 (origin 가설 기각 + 비즈앱 스왑 시도 + 4019 지속): **2026-05-24**
- 관리자 통계 필터 옵션 추가 (베타 데이터 클렌징 기능): **2026-05-25**
- 베타 데이터 인사이트 발견 (14명 unique + 평균 2.1회 재제출) + 백로그 우선순위 재조정: **2026-05-25**
- 다음 세션 예정: **카카오는 보류 / § 4-1 우선순위에 따라 🥇 시트 자동 분류 (2h) → 🥈 재진단 비교 리포트 (4h)**
