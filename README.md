# 내 리더

Feeder처럼 **피드 목록 · 기사 목록 · 미리보기** 3단으로 보는 개인 뉴스 리더입니다.
GitHub가 2시간마다 피드를 모아 피드당 최신 10건만 보여줍니다. 무료이고, PC가 꺼져 있어도 폰·회사에서 열 수 있어요.

```
feeds.yaml                    ← 볼 피드 목록 (여기만 고치면 됨)
feeds.opml                    ← (선택) Feeder에서 내보낸 파일을 그대로 올리면 같이 읽음
fetch.py                      ← 피드 수집 스크립트
docs/index.html               ← 3단 화면
docs/data.json                ← 수집 결과 (자동 생성)
.github/workflows/update.yml  ← 2시간마다 자동 실행
```

---

## 처음 설치 (10분)

1. **저장소 만들기** — github.com 로그인 → 오른쪽 위 `+` → **New repository**
   - 이름: 예) `my-reader`
   - **Public** 선택 (무료 계정에서 웹페이지로 공개하려면 Public이어야 합니다. 뉴스 제목만 올라가니 괜찮아요)
   - Create repository

2. **파일 올리기** — 새 저장소 화면의 **uploading an existing file** 클릭 →
   압축을 푼 폴더 안의 내용물 전체(`.github` 폴더 포함)를 끌어다 놓고 **Commit changes**
   > Mac Finder에서 `.github` 폴더가 안 보이면 `Cmd + Shift + .` 를 누르면 보입니다.

3. **웹페이지 켜기** — 저장소의 **Settings → Pages** → Source를 **GitHub Actions** 로 선택

4. **첫 수집 실행** — **Actions** 탭 → (처음이면 녹색 버튼으로 활성화) → 왼쪽 **뉴스 갱신** → **Run workflow**
   1~2분 뒤 초록 체크가 뜨면 완료.

5. **접속** — `https://<내 GitHub 아이디>.github.io/my-reader/`
   폰에서는 Safari 공유 → "홈 화면에 추가" 하면 앱처럼 쓸 수 있어요.

---

## Feeder 피드를 한 번에 옮기기 (추천)

KDI 경제정보센터, 구글 알리미처럼 주소를 따로 찾기 번거로운 피드는 Feeder에서 쓰던 주소를 그대로 가져오는 게 가장 정확합니다.

1. Feeder 설정에서 **OPML 내보내기**(Export)로 피드 목록 파일 받기
2. 받은 파일 이름을 `feeds.opml` 로 바꿔 저장소에 업로드 (Add file → Upload files)
3. 자동으로 다시 수집됩니다

`feeds.yaml` 에 같은 이름의 피드가 있으면 yaml 쪽이 우선이라, AI Matters처럼 고장 난 피드는 yaml에 적어둔 대체 주소로 받아옵니다.

## 피드 추가·삭제

`feeds.yaml` 을 GitHub 화면에서 열고 연필(✏️) 아이콘으로 편집:

```yaml
  - name: 보여줄 이름
    url: https://RSS주소
```

저장하면 자동으로 다시 수집합니다. 피드당 건수는 맨 위 `top_n` 으로 바꿀 수 있어요.

## AI Matters

aimatters.co.kr은 현재 자바스크립트로 쿠키를 확인하는 봇 차단 장치를 쓰고 있어서, RSS 리더나 이런 수집기가 사이트에 직접 접속하면 기사 대신 차단 페이지를 받습니다.
그래서 이 리더는 **구글 뉴스가 수집한 AI Matters 기사**로 대신 받아옵니다(기본값).

더 빠르고 확실하게 받고 싶으면:
- **구글 알리미**에서 `site:aimatters.co.kr` 알림 만들기 → 옵션 표시 → 전송 위치 **RSS 피드** → 알리미 목록의 RSS 아이콘 주소를 `feeds.yaml` 의 AI Matters `url` 에 붙여넣기
- 또는 AI Matters에 "RSS(/feed)가 봇 차단 때문에 리더에서 안 열린다"고 알려주면 사이트에서 RSS 주소만 예외 처리해 줄 수도 있어요.

## 사용법

| 키 | 동작 |
|---|---|
| `j` / `k` (또는 ↓ ↑) | 다음 / 이전 글 |
| `s` | 별표 |
| `m` | 읽음 ↔ 안읽음 |
| `o` 또는 Enter | 원문 새 탭으로 열기 |
| `/` | 검색 |

- 읽음·별표는 **그 브라우저에만** 저장됩니다(회사 PC와 폰은 따로 기록).
- 별표한 글은 최신 10건에서 밀려나도 별표함에 남아요.
- 피드 이름 옆 빨간 점 = 최근 수집 실패 (마우스를 올리면 이유가 보이고, 직전에 받은 기사는 그대로 보여줍니다).

## 참고

- GitHub는 저장소에 60일간 아무 활동이 없으면 자동 실행을 멈출 수 있어요. 그런 메일이 오면 Actions 탭에서 다시 켜면 됩니다.
- 수집 주기를 바꾸려면 `.github/workflows/update.yml` 의 `cron` 줄을 고치세요 (예: 매시간 `"17 * * * *"`).
