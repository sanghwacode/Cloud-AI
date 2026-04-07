import os
import sys
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from dotenv import load_dotenv
import urllib.parse
import time

# [Version 2.2] 사용자 명령(읽기/쓰기/검색)의 의도를 엄격하게 구분하도록 개선
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8')

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ WARNING: GEMINI_API_KEY가 설정되지 않았습니다.")
else:
    genai.configure(api_key=api_key)

# --- [도구 정의 (Tools)] ---

def read_file(path: str) -> str:
    """로컬 파일 시스템에서 텍스트 파일을 읽습니다. 단순히 내용을 확인하고 싶을 때 사용합니다."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            return content if content else "파일이 비어있습니다."
    except FileNotFoundError:
        return f"오류: '{path}' 파일을 찾을 수 없습니다."
    except Exception as e:
        return f"파일 읽기 오류: {str(e)}"

def write_file(path: str, content: str) -> str:
    """새로운 파일을 생성합니다. 기존에 없던 파일명을 사용할 때만 호출하세요."""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"성공: '{path}' 파일이 생성되었습니다."
    except Exception as e:
        return f"파일 생성 오류: {str(e)}"

def edit_file(path: str, content: str) -> str:
    """기존 파일의 내용을 완전히 새로운 내용으로 덮어씁니다. 수정 요청 시 사용하세요."""
    if not os.path.exists(path):
        return f"오류: '{path}' 파일이 없습니다. 새 파일을 만들려면 write_file을 쓰세요."
    return write_file(path, content)

def append_to_file(path: str, content: str) -> str:
    """기존 파일의 끝에 내용을 추가합니다. '추가'나 '덧붙이기' 요청 시 매우 유용합니다."""
    try:
        if not os.path.exists(path):
             return f"오류: '{path}' 파일이 없습니다."
        with open(path, 'a', encoding='utf-8') as f:
            f.write("\n" + content)
        return f"성공: '{path}' 파일에 내용이 추가되었습니다."
    except Exception as e:
        return f"내용 추가 오류: {str(e)}"

def search_namuwiki(keyword: str) -> str:
    """나무위키 본문을 검색하여 본문 텍스트를 반환합니다."""
    try:
        encoded_keyword = urllib.parse.quote(keyword)
        url = f"https://namu.wiki/w/{encoded_keyword}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"}
        print(f"\n🔍 나무위키 검색 중: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            content_div = None
            for sel in ['div.wiki-content', 'div.w', 'article']:
                found = soup.select(sel)
                if found:
                    candidate = max(found, key=lambda x: len(x.get_text()))
                    if len(candidate.get_text(strip=True)) > 200:
                        content_div = candidate
                        break
            if not content_div:
                divs_with_v = soup.find_all('div', attrs={"data-v-": True})
                if divs_with_v: content_div = max(divs_with_v, key=lambda x: len(x.get_text()))
            if content_div:
                for tag in content_div.find_all(['nav', 'script', 'style']): tag.decompose()
                content = content_div.get_text(separator='\n', strip=True)
                if len(content) > 8000: content = content[:8000] + "\n\n...(중략)..."
                print(f"✅ 본문을 찾았습니다. ({len(content)}자)")
                return content
            return "❌ 본문 추출 실패"
        return f"❌ HTTP {response.status_code}"
    except Exception as e:
        return f"❌ 오류: {str(e)}"

tools = [read_file, write_file, edit_file, append_to_file, search_namuwiki]

# --- [에이전트 제어 루프] ---

def run_agent(user_prompt: str):
    model_name = "models/gemini-flash-lite-latest"
    try:
        # 시스템 지침 강화: 읽기 요청 시 '쓰기(Write)' 작업을 절대로 하지 말 것!
        model = genai.GenerativeModel(
            model_name=model_name, 
            tools=tools,
            system_instruction="당신은 로컬 파일 관리 도우미입니다.\n"
                               "1. **읽기 우선 원칙**: 사용자가 '읽어줘' 또는 '확인해줘'라고 하면 `read_file`로 내용을 읽은 후 그 내용을 말로만 전달하세요. 절대로 새로 파일을 만들지 마세요.\n"
                               "2. **명시적 쓰기**: 사용자가 '저장해줘', '만들어줘', '수정해줘'라고 명시적으로 요청할 때만 `write_file`, `edit_file`, `append_to_file`을 사용하세요.\n"
                               "3. **불필요한 작업 금지**: 한 명의 사용자가 한 번 질문하면 그 의도에 꼭 필요한 도구만 최소한으로 사용하세요."
        )
        chat = model.start_chat(enable_automatic_function_calling=False)
        print(f"--- 🤖 에이전트 실행 중... ---")
        
        response = chat.send_message(user_prompt)
        
        while True:
            if not response.candidates[0].content.parts: break
            tool_calls = [part.function_call for part in response.candidates[0].content.parts if part.function_call]
            if not tool_calls: break
                
            responses = []
            for call in tool_calls:
                fn_name, fn_args = call.name, call.args
                print(f"🛠️ 도구 실행: {fn_name}({fn_args})")
                tool_func = next((t for t in tools if t.__name__ == fn_name), None)
                res = tool_func(**fn_args) if tool_func else "오류"
                responses.append(genai.protos.Part(function_response=genai.protos.FunctionResponse(name=fn_name, response={"result": res})))
            
            response = chat.send_message(responses)
            
        if response.text:
            print(f"\n[Agent]: {response.text}")
            
    except Exception as e:
        print(f"\n❌ 에러: {str(e)}")

if __name__ == "__main__":
    print("🚀 Gemini AI 에이전트 v2.2")
    print("- '읽어줘'라고 하면 화면에 출력만 하고, '저장해줘'라고 할 때만 파일을 만듭니다.")
    print("-" * 30)
    
    while True:
        try:
            line = input("명령 입력: ").strip()
            if not line: continue
            run_agent(line)
            print("-" * 50)
        except KeyboardInterrupt:
            print("\n👋 종료합니다."); break
        except Exception as e:
            print(f"⚠️ 오류: {e}"); time.sleep(1)
