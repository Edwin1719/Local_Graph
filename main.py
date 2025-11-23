import os
from dotenv import load_dotenv
from ollama import chat, web_fetch, web_search

# === Cargar variables de entorno desde .env ===
load_dotenv()

print("API KEY detectada en Python:", os.getenv("OLLAMA_API_KEY"))

api_key = os.getenv("OLLAMA_API_KEY")
if not api_key:
    raise ValueError("No se encontró OLLAMA_API_KEY en el archivo .env")

# Exportar al entorno para que ollama lo reconozca
os.environ["OLLAMA_API_KEY"] = api_key

# === Configuración de herramientas disponibles ===
available_tools = {
    'web_search': web_search,
    'web_fetch': web_fetch
}

# Mensaje inicial
messages = [{'role': 'user', 'content': "ultimas noticias de estados Unidos para Septiembre de 2025"}]

# === Bucle principal ===
while True:
    response = chat(
        model='gpt-oss:20b-cloud',
        messages=messages,
        tools=[web_search, web_fetch],
        think=True
    )

    # Mostrar pensamientos (si existen)
    if response.message.thinking:
        print('Thinking: ', response.message.thinking)

    # Mostrar contenido de la respuesta
    if response.message.content:
        print('Content: ', response.message.content)

    # Guardar mensaje en historial
    messages.append(response.message)

    # Manejo de llamadas a herramientas
    if response.message.tool_calls:
        print('Tool calls: ', response.message.tool_calls)

        for tool_call in response.message.tool_calls:
            function_to_call = available_tools.get(tool_call.function.name)

            if function_to_call:
                args = tool_call.function.arguments

                try:
                    result = function_to_call(**args)
                    print('Result: ', str(result)[:200] + '...')  # Truncar para no saturar salida

                    messages.append({
                        'role': 'tool',
                        'content': str(result)[:2000 * 4],
                        'tool_name': tool_call.function.name
                    })

                except Exception as e:
                    print(f"Error ejecutando {tool_call.function.name}: {e}")
                    messages.append({
                        'role': 'tool',
                        'content': f"Error ejecutando {tool_call.function.name}: {e}",
                        'tool_name': tool_call.function.name
                    })

            else:
                messages.append({
                    'role': 'tool',
                    'content': f'Tool {tool_call.function.name} not found',
                    'tool_name': tool_call.function.name
                })
    else:
        break