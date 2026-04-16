import streamlit as st
from openai import OpenAI
import os

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="TDD AI Agent (Strict Mode)",
    page_icon="🛡️",
    layout="wide"
)

# --- FUNGSI PEMBACA ATURAN (MD) ---
def load_rules():
    """Membaca aturan dari file markdown untuk dijadikan System Prompt."""
    rules_content = ""
    files_to_load = ["SKILL.md", "testing-anti-patterns.md"]
    
    for file_name in files_to_load:
        if os.path.exists(file_name):
            with open(file_name, "r", encoding="utf-8") as f:
                rules_content += f"\n\n=== REFERENCE FROM {file_name} ===\n"
                rules_content += f.read()
        else:
            # Fallback jika file tidak ditemukan secara lokal
            rules_content += f"\n\n[Warning: {file_name} not found locally.]"
            
    return rules_content

# --- KONFIGURASI API ---
with st.sidebar:
    st.title("⚙️ Konfigurasi Agent")
    api_key = st.text_input("DeepSeek API Key", type="password", value=os.environ.get('DEEPSEEK_API_KEY', ''))
    
    st.divider()
    st.subheader("📜 Aturan Terdeteksi")
    if os.path.exists("SKILL.md"):
        st.success("✅ SKILL.md terintegrasi")
    else:
        st.error("❌ SKILL.md tidak ditemukan")
        
    if os.path.exists("testing-anti-patterns.md"):
        st.success("✅ Anti-Patterns terintegrasi")
    else:
        st.error("❌ Anti-Patterns tidak ditemukan")

    if st.button("Hapus Riwayat Chat"):
        st.session_state.messages = []
        st.rerun()

# --- INITIALIZE CLIENT ---
client = None
if api_key:
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

# --- CONSTRUCT SYSTEM PROMPT ---
# Kita menggabungkan instruksi utama dengan isi dari file MD
rules_text = load_rules()
TDD_SYSTEM_PROMPT = f"""
You are a Senior Software Engineer AI Agent. Your core identity is defined by the following documents:

{rules_text}

STRICT OPERATIONAL DIRECTIVE:
1. You MUST follow the Red-Green-Refactor cycle for EVERY request.
2. Your FIRST response to any feature request MUST be the test code that fails.
3. You must EXPLICITLY reference rules from SKILL.md or testing-anti-patterns.md if the user's request risks violating them.
4. If you realize you've written production code without a failing test, you must apologize, delete that logic, and restart from the test.

Human Partner: Fabian
"""

# --- UI CHAT ---
st.title("🛡️ TDD AI Agent: Strict Mode")
st.caption("Agent ini membaca aturan langsung dari SKILL.md dan testing-anti-patterns.md")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": TDD_SYSTEM_PROMPT}
    ]

# Tampilkan history
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# --- CHAT LOGIC ---
if prompt := st.chat_input("Berikan instruksi fitur atau perbaikan bug..."):
    if not api_key:
        st.error("Silakan masukkan API Key di sidebar.")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            full_response = ""
            
            try:
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages
                    ],
                    stream=True
                )
                
                for chunk in response:
                    content = chunk.choices[0].delta.content
                    if content:
                        full_response += content
                        response_placeholder.markdown(full_response + "▌")
                
                response_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                
            except Exception as e:
                st.error(f"Gagal memanggil API: {str(e)}")