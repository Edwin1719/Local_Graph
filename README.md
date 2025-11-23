# 🤖 Asistente de IA con LangGraph y Herramientas Locales

Este proyecto presenta un asistente de IA conversacional avanzado construido con Python, que utiliza un modelo de lenguaje ejecutado localmente a través de Ollama. La aplicación cuenta con una interfaz web interactiva creada con Streamlit y un potente agente backend orquestado por LangGraph, capaz de utilizar herramientas externas como Google Maps y búsqueda web para proporcionar respuestas enriquecidas y contextuales.

## 🏛️ Arquitectura

La arquitectura de esta aplicación está diseñada para ser modular y extensible. A continuación se muestra un diagrama del flujo de datos y componentes principales:

```mermaid
graph TD
    A[👨‍💻 Usuario] --> B[🌐 Interfaz Web Streamlit];
    B --> C{🤖 Agente LangGraph};

    subgraph "Flujo del Agente"
        C --> D{1. Router (Decide la ruta)};
        D --> |Necesita datos externos| E[2. Nodo de Herramienta];
        D --> |No necesita datos| G[3. Nodo de Generación];
        E --> F1[🛠️ Tavily Search];
        E --> F2[📍 Google Maps];
        F1 --> G;
        F2 --> G;
    end

    subgraph "Servicios Externos y Locales"
        G --> H((🧠 Ollama LLM));
        H --> G;
        F1 --> I([API Tavily]);
        F2 --> J([API Google Maps]);
    end

    G --> B;

    style A fill:#D6EAF8
    style B fill:#E8DAEF
    style H fill:#D5F5E3
```

A continuación, se detallan los componentes:


1.  **Frontend (Streamlit):** La interfaz de usuario es una aplicación web de chat creada con Streamlit. Es responsable de capturar la entrada del usuario, mostrar el historial de la conversación y renderizar las respuestas del asistente en tiempo real.

2.  **Backend - Agente de LangGraph:** El cerebro de la aplicación es un agente construido con `langgraph`. Este agente gestiona el flujo de la conversación como un grafo de estados:
    *   **Estado (`State`):** Un diccionario que mantiene la información a lo largo del flujo, incluyendo el historial de mensajes y los resultados de las herramientas.
    *   **Nodos:**
        *   `route_tools`: El nodo de entrada que analiza la consulta del usuario para decidir si se necesita una herramienta o si el LLM puede responder directamente.
        *   `use_web_search`: Un nodo que se activa para realizar búsquedas en la web utilizando **Tavily Search**.
        *   `use_google_maps_...`: Nodos que interactúan con la API de Google Maps para buscar lugares u obtener direcciones.
        *   `generate_response`: El nodo final que sintetiza una respuesta para el usuario, utilizando el contexto de la conversación y los resultados de las herramientas si se usaron.
    *   **Bordes Condicionales (`Conditional Edges`):** La lógica de enrutamiento que conecta el nodo `route` con la herramienta apropiada basándose en la intención del usuario.

3.  **Modelo de Lenguaje (Ollama):** El proyecto se conecta a un modelo de lenguaje grande (LLM) que se ejecuta localmente a través del servidor de Ollama. Esto garantiza la privacidad de los datos y reduce la dependencia de servicios de terceros. El modelo `gpt-oss:20b-cloud` es el utilizado, pero puede ser sustituido por cualquier otro modelo compatible con Ollama.

4.  **Herramientas (Tools):**
    *   **Tavily Web Search:** Permite al asistente acceder a información actualizada de internet para responder preguntas sobre eventos actuales, noticias, etc.
    *   **Google Maps Platform:** Otorga capacidades geoespaciales al asistente, permitiéndole:
        *   Buscar información sobre lugares, negocios y puntos de interés (`google_maps_place_search`).
        *   Calcular rutas, distancias y tiempos de viaje entre dos puntos (`google_maps_directions`).

## 💻 Pila Tecnológica

*   **Lenguaje:** Python 3.9+
*   **Framework Web:** Streamlit
*   **Orquestación de Agentes y LLM:** LangChain (específicamente `langgraph` y `langchain-community`)
*   **Servidor de LLM Local:** Ollama
*   **Herramientas Externas:**
    *   Tavily Search API
    *   Google Maps Platform API

## 🚀 Instalación e Implementación

Sigue estos pasos para configurar y ejecutar el proyecto en tu entorno local.

### 1. Prerrequisitos

*   **Python 3.9 o superior.**
*   **Ollama instalado y en ejecución.** Puedes descargarlo desde [ollama.com](https://ollama.com/).
*   **Git** para clonar el repositorio.

### 2. Clonar el Repositorio

```bash
git clone https://github.com/Edwin1719/OllamaCloud_Local.git
cd OllamaCloud_Local
```

### 3. Instalar el Modelo de Ollama

Abre tu terminal y ejecuta el siguiente comando para descargar el modelo de lenguaje que utiliza la aplicación:

```bash
ollama pull gpt-oss:20b-cloud
```
*(Puedes configurar otro modelo en `app.py` si lo deseas)*

### 4. Configurar Variables de Entorno

Este proyecto necesita claves API para las herramientas de búsqueda web y Google Maps.

1.  Crea una copia del archivo de ejemplo `.env.example`:
    ```bash
    cp .env.example .env
    ```
2.  Abre el archivo `.env` en un editor de texto y añade tus claves API:
    *   `TAVILY_API_KEY`: Obtén tu clave gratuita en [Tavily AI](https://app.tavily.com/).
    *   `GOOGLE_MAPS_API_KEY`: Obtén tu clave desde [Google Cloud Console](https://console.cloud.google.com/google/maps-apis/). Asegúrate de habilitar las APIs `Geocoding API`, `Directions API`, y `Places API`.

### 5. Instalar Dependencias de Python

Instala todas las librerías necesarias utilizando el archivo `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 6. Ejecutar la Aplicación

Una vez que todos los pasos anteriores estén completados, inicia la aplicación de Streamlit:

```bash
streamlit run app.py
```

Abre tu navegador y ve a la dirección URL local que te indique Streamlit (normalmente `http://localhost:8501`).

## ✨ Usos y Potencial

Un asistente como este, que combina un LLM local con herramientas externas, tiene un enorme potencial tanto para uso personal como empresarial.

### Utilidades y Ejemplos de Uso

A continuación, algunas capturas de pantalla de la aplicación en acción:

![Captura de Pantalla 1 - Ejemplo de Búsqueda Web](https://via.placeholder.com/800x450?text=Captura+de+Pantalla+1:+Busqueda+Web)
*El asistente respondiendo a una pregunta usando la búsqueda web de Tavily.*

![Captura de Pantalla 2 - Ejemplo de Google Maps (Lugares)](https://via.placeholder.com/800x450?text=Captura+de+Pantalla+2:+Google+Maps+Lugares)
*Encontrando lugares de interés con la herramienta de Google Maps.*

![Captura de Pantalla 3 - Ejemplo de Google Maps (Rutas)](https://via.placeholder.com/800x450?text=Captura+de+Pantalla+3:+Google+Maps+Rutas)
*Generando indicaciones y tiempos de viaje con Google Maps.*

*   **Asistente Personal:**
    *   *"¿Cuáles son las últimas noticias sobre inteligencia artificial?"* (Usa `web_search`)
    *   *"Busca restaurantes de comida italiana cerca del centro de Madrid."* (Usa `google_maps_place_search`)
    *   *"¿Cómo llego en coche desde el aeropuerto de Bogotá al Museo del Oro?"* (Usa `google_maps_directions`)

*   **Herramienta de Productividad:**
    *   Planificar viajes obteniendo información de vuelos, hoteles y rutas.
    *   Realizar investigaciones preliminares sobre cualquier tema combinando conocimiento del LLM y datos frescos de la web.

### Potencial en el Sector Empresarial

La capacidad de personalizar y ampliar este asistente lo convierte en un activo valioso para las empresas:

1.  **Privacidad y Seguridad de Datos:** Al usar Ollama, todas las consultas y datos sensibles se procesan localmente, evitando exponer información confidencial a APIs de terceros. Esto es crucial para sectores como el financiero, legal o de salud.

2.  **Customer Support Aumentado:** Se puede integrar con bases de datos internas (documentación, historial de tickets) para crear un agente de soporte que responda preguntas de clientes o de empleados de primer nivel con información precisa y actualizada.

3.  **Análisis de Negocios y Operaciones:** Un agente podría conectarse a APIs internas para consultar el estado de inventario, monitorear envíos (usando la API de mapas), o generar resúmenes de ventas, todo a través de una interfaz conversacional.

4.  **Automatización de Tareas:** Tareas repetitivas como la búsqueda de información sobre clientes potenciales, la programación de rutas de logística o la redacción de informes preliminares pueden ser delegadas al asistente.

## 👨‍💻 Desarrollador

Este proyecto fue desarrollado por **Edwin Quintero**.

¡Conectemos!

*   **GitHub:** [github.com/Edwin1719](https://github.com/Edwin1719)
*   **LinkedIn:** [linkedin.com/in/edwinquintero0329](https://www.linkedin.com/in/edwinquintero0329/)
*   **Email:** [databiq29@gmail.com](mailto:databiq29@gmail.com)
