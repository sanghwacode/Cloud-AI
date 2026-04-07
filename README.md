# 🤖 Gemini AI Agent v2.2

이 프로젝트는 Google의 **Gemini 1.5 Flash** 모델을 기반으로 한 지능형 로컬 파일 관리 및 웹 검색 에이전트입니다. 사용자의 복잡한 자연어 명령을 분석하여 필요한 도구를 연속적으로 호출하고 작업을 완수합니다.

## ✨ 주요 기능

- **연속 도구 호출(Tool Calling Loop)**: 모델이 스스로 판단하여 `read_file`, `write_file`, `search_namuwiki` 등 여러 도구를 단계별로 실행합니다.
- **로컬 파일 관리**: 파일 읽기, 쓰기, 수정, 내용 추가 기능을 완벽하게 지원합니다.
- **나무위키 실시간 검색**: 궁금한 키워드를 나무위키에서 검색하여 핵심 내용을 요약해줍니다.
- **지능형 의도 분석**: '읽기'와 '쓰기' 요청을 엄격하게 구분하여 불필요한 파일 생성을 방지합니다.

## 📂 파일 구조

- `agent.py`: 에이전트의 핵심 로직과 도구 정의가 담긴 메인 실행 파일입니다.
- `.env`: Gemini API Key 및 환경 변수를 설정합니다 (보안을 위해 로컬에서만 관리).
- `requirements.txt`: 필요한 라이브러리 목록입니다.

## 🚀 시작하기

1. **의존성 설치**:
   ```bash
   pip install -r requirements.txt
   ```
2. **API 키 설정**:
   `.env` 파일을 생성하고 `GEMINI_API_KEY=YOUR_KEY_HERE`를 입력합니다.
3. **에이전트 실행**:
   ```bash
   python agent.py
   ```

---
*개발: Antigravity AI*
