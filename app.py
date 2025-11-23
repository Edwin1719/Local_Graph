from dotenv import load_dotenv
load_dotenv()

import os
import streamlit as st
import googlemaps
from typing import TypedDict, Annotated, List, Dict, Any
import operator
from st_social_media_links import SocialMediaIcons

from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_community.tools import TavilySearchResults

from langgraph.graph import StateGraph, END

import requests
import psutil

def get_ollama_stats():
    try:
        resp = requests.get("http://localhost:11434/api/ps", timeout=1).json()
        if "models" in resp and len(resp["models"]) > 0:
            m = resp["models"][0]
            return {
                "model": m.get("name", "N/A"),
                "size": round(m.get("size", 0) / 1e9, 2),
                "ram": round(m.get("mem", 0) / 1e9, 2)
            }
    except:
        pass
    return None

def check_service(url):
    try:
        requests.get(url, timeout=1)
        return "🟢 OK"
    except:
        return "🔴 Falló"

def get_conversation_summary(n=3):
    if "messages" not in st.session_state:
        return []
    return st.session_state["messages"][-n:]


# Importar herramientas
tavily_api_key = os.getenv("TAVILY_API_KEY")

# Inicializar cliente de Google Maps
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
if not GOOGLE_MAPS_API_KEY:
    st.error("⚠️ GOOGLE_MAPS_API_KEY no encontrada en el archivo .env. Las herramientas de Google Maps no funcionarán.")
    gmaps = None
else:
    gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)

# Definir herramientas
@tool
def web_search(query: str) -> str:
    """Busca información general, noticias, eventos actuales o datos no estructurados en la web."""
    if tavily_api_key:
        tavily_search = TavilySearchResults(api_key=tavily_api_key, max_results=5)
        results = tavily_search.invoke({"query": query})
        return str(results)
    else:
        return "Por favor, agrega tu TAVILY_API_KEY al archivo .env para habilitar la búsqueda web."

@tool
def google_maps_directions(origin: str, destination: str, mode: str = "driving") -> str:
    """Calcula la distancia, el tiempo y las indicaciones de ruta entre dos ubicaciones."""
    if not gmaps:
        return "Error: Cliente de Google Maps no inicializado. Falta GOOGLE_MAPS_API_KEY."
    try:
        directions_result = gmaps.directions(origin, destination, mode=mode)
        if directions_result:
            route = directions_result[0]
            legs = route['legs'][0]
            distance = legs['distance']['text']
            duration = legs['duration']['text']
            summary = route['summary']
            return f"Ruta: {summary}. Distancia: {distance}. Duración: {duration}."
        else:
            return "No se encontraron indicaciones para la ruta."
    except Exception as e:
        return f"Error al obtener indicaciones de Google Maps: {e}"

@tool
def google_maps_place_search(query: str, location: str = None, radius: int = 5000) -> str:
    """Busca información detallada sobre un lugar específico."""
    if not gmaps:
        return "Error: Cliente de Google Maps no inicializado. Falta GOOGLE_MAPS_API_KEY."
    try:
        places_result = gmaps.places(query=query, location=location, radius=radius)
        if places_result['results']:
            results = []
            for place in places_result['results'][:3]:
                name = place.get('name', 'N/A')
                address = place.get('formatted_address', 'N/A')
                rating = place.get('rating', 'N/A')
                opening_status = place.get('opening_hours', {}).get('open_now', 'Desconocido')
                result = (
                    f"Nombre: {name}\n"
                    f"Dirección: {address}\n"
                    f"Calificación: {rating}/5\n"
                    f"Estado de apertura: {opening_status}\n---"
                )
                results.append(result)
            return "Resultados de la búsqueda:\n" + "\n".join(results)
        else:
            return "No se encontraron lugares para la búsqueda."
    except Exception as e:
        return f"Error al buscar lugares en Google Maps: {e}"

# Definir el estado del grafo
class State(TypedDict):
    messages: Annotated[List[dict], operator.add]
    next_tool: str
    tool_result: str

# Inicializar LLM
llm = ChatOllama(
    model="gpt-oss:20b-cloud",
    base_url="http://localhost:11434",
    temperature=0
)

# Nodo para determinar qué herramienta usar
def route_tools(state: State) -> Dict[str, Any]:
    messages = state["messages"]
    last_message = messages[-1]["content"] if messages else ""

    if any(keyword in last_message.lower() for keyword in
           ['noticia', 'news', 'buscar', 'información', 'info', 'reciente', 'actualidad']):
        return {"next_tool": "web_search"}

    elif any(keyword in last_message.lower() for keyword in
             ['restaurante', 'hotel', 'lugar', 'punto de interés', 'ubicación', 'mapa', 'cerca de', 'alrededor']):
        return {"next_tool": "google_maps_place_search"}

    elif any(keyword in last_message.lower() for keyword in
             ['ruta', 'distancia', 'dirección', 'como llegar', 'ir de', 'de [a-z]+ a [a-z]+']):
        return {"next_tool": "google_maps_directions"}

    else:
        return {"next_tool": "none"}

def use_web_search(state: State) -> Dict[str, Any]:
    messages = state["messages"]
    last_message = messages[-1]["content"]
    result = web_search.invoke({"query": last_message})
    return {"tool_result": result, "messages": [{"role": "tool", "name": "web_search", "content": result}]}

def use_google_maps_place_search(state: State) -> Dict[str, Any]:
    messages = state["messages"]
    last_message = messages[-1]["content"]
    import re
    location_match = re.search(r'cerca de ([^\.]+)|en ([^\.]+)|alrededor de ([^\.]+)', last_message, re.IGNORECASE)

    if location_match:
        location = location_match.group(1) or location_match.group(2) or location_match.group(3)
        query = (
            f"{last_message.split('cerca')[0] if 'cerca' in last_message.lower() else 'restaurantes o lugares'} "
            f"en {location.strip()}"
        )
    else:
        query = last_message

    result = google_maps_place_search.invoke({"query": query.strip()})
    return {"tool_result": result, "messages": [{"role": "tool", "name": "google_maps_place_search", "content": result}]}

def use_google_maps_directions(state: State) -> Dict[str, Any]:
    messages = state["messages"]
    last_message = messages[-1]["content"]
    import re

    pattern = r'de ([^a-hk-su-z]+?) (a|hasta) ([^.]+)'
    match = re.search(pattern, last_message.lower())

    if match:
        origin = match.group(1).strip()
        destination = match.group(3).strip()
        result = google_maps_directions.invoke({"origin": origin, "destination": destination})
    else:
        result = (
            "No pude identificar claramente el origen y destino. "
            "Por favor, formula tu pregunta como '¿Cómo llegar de [origen] a [destino]?'"
        )

    return {"tool_result": result, "messages": [{"role": "tool", "name": "google_maps_directions", "content": result}]}

def generate_response(state: State) -> Dict[str, Any]:
    messages = state["messages"]
    tool_result = state.get("tool_result", "")

    if tool_result:
        input_text = messages[-1]["content"]
        prompt = f"Usa la siguiente información para responder la pregunta '{input_text}': {tool_result}"
        response = llm.invoke([("human", prompt)])
        response_content = response.content
    else:
        input_text = messages[-1]["content"]
        response = llm.invoke([("human", input_text)])
        response_content = response.content

    return {"messages": [{"role": "assistant", "content": response_content}]}

def create_graph():
    workflow = StateGraph(State)

    workflow.add_node("route", route_tools)
    workflow.add_node("web_search", use_web_search)
    workflow.add_node("google_maps_place_search", use_google_maps_place_search)
    workflow.add_node("google_maps_directions", use_google_maps_directions)
    workflow.add_node("generate_response", generate_response)

    def choose_tool(state: State):
        next_tool = state.get("next_tool", "none")
        if next_tool == "web_search":
            return "web_search"
        elif next_tool == "google_maps_place_search":
            return "google_maps_place_search"
        elif next_tool == "google_maps_directions":
            return "google_maps_directions"
        else:
            return "generate_response"

    workflow.add_conditional_edges("route", choose_tool)
    workflow.add_edge("web_search", "generate_response")
    workflow.add_edge("google_maps_place_search", "generate_response")
    workflow.add_edge("google_maps_directions", "generate_response")
    workflow.set_entry_point("route")
    workflow.add_edge("generate_response", END)

    return workflow.compile()

graph = create_graph()

with st.sidebar:
    st.title("⚙️ Panel de Control")

    # --- PILA TECNOLÓGICA ---
    st.subheader("🧩 Pila Tecnológica")
    st.markdown("""
    **Frontend:** Streamlit  
    **IA Local:** Ollama  
    **IA Nube:** Groq / OpenAI  
    **Mapas:** Google Maps API  
    **Búsqueda Web:** Tavily  
    **Base de Datos:** ChromaDB  
    """)

    # --- CARACTERÍSTICAS DEL MODELO ---
    st.subheader("🧠 Características del Modelo")
    st.markdown("""
    - Modelo base: **LLaMA / Qwen / Mistral** (según el que cargues)  
    - Modo: **RAG + LLM Híbrido**  
    - Funciones: Razonamiento, búsqueda, geolocalización, memoria corta  
    - Optimizado para: análisis, generación de respuestas y operaciones locales  
    """)

    # --- USO DEL MODELO LOCAL ---
    st.subheader("🖥️ Uso del Modelo Local")

    ollama_stats = get_ollama_stats()
    if ollama_stats:
        st.markdown(f"""
        **Modelo activo:** `{ollama_stats['model']}`  
        **Tamaño:** {ollama_stats['size']} GB  
        **RAM consumida:** {ollama_stats['ram']} GB  
        """)
    else:
        st.markdown("🔴 Ollama no responde o no está ejecutando un modelo.")

    # --- DIAGNÓSTICO DE SERVICIOS ---
    st.subheader("📡 Diagnóstico de Servicios")
    st.write(f"Ollama: {check_service('http://localhost:11434')}")
    st.write(f"Google Maps: {'🟢 OK' if GOOGLE_MAPS_API_KEY else '🔴 Sin clave'}")
    st.write(f"Tavily: {'🟢 OK' if tavily_api_key else '🔴 Sin clave'}")

    # --- HISTORIAL DE CONVERSACIÓN ---
    st.subheader("🗂️ Historial de Conversación")
    hist = get_conversation_summary(3)
    if hist:
        for msg in hist:
            role = "🧑‍💻 Usuario" if msg['role'] == "user" else "🤖 Agente"
            st.markdown(f"**{role}:** {msg['content']}")
    else:
        st.write("No hay mensajes aún.")

st.title("🤖 Asistente con Ollama + LangGraph + Herramientas")
st.write("Haz preguntas al modelo y, si es necesario, usará herramientas para complementar la respuesta.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input = st.chat_input("Escribe tu consulta:")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            try:
                initial_state = {
                    "messages": [{"role": "user", "content": user_input}],
                    "next_tool": "",
                    "tool_result": ""
                }
                result = graph.invoke(initial_state)
                response_content = ""

                if result and "messages" in result:
                    for msg in result["messages"]:
                        if msg.get("role") == "assistant":
                            response_content = msg["content"]
                            break

                if not response_content and result:
                    if "tool_result" in result and result["tool_result"]:
                        response_content = result["tool_result"]
                    else:
                        response = llm.invoke([("human", user_input)])
                        response_content = response.content

                st.markdown(response_content)
                st.session_state.messages.append({"role": "assistant", "content": response_content})

            except Exception as e:
                st.error(f"Error: {e}")

st.markdown("""---
<div style="text-align: center;">
<strong>Desarrollador:</strong> Edwin Quintero Alzate<br>
<strong>Email:</strong> egqa1975@gmail.com
</div>""", unsafe_allow_html=True)

SocialMediaIcons(["https://www.facebook.com/edwin.quinteroalzate", "https://www.linkedin.com/in/edwinquintero0329/", "https://github.com/Edwin1719"]).render()