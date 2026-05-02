from Funciones_Slide.Funciones_Variadas import Enviar_mensaje_Whatsapp, llamada_whatsapp, colgar, Auto_Modificacion
from Funciones_Slide.Gestion_datos import guardar_en_json
from Funciones_Slide.Comandos_Asistente import abrir_camara, Reconocimiento_Facial, Abrir_Apps, Abrir_Videos_Youtube, Buscar_en_Google, limpiar_historial, Salir



tools = [
    {
        "type": "function",
        "function": {
            "name": "Enviar_mensaje_Whatsapp",
            "description": "Envía un mensaje de WhatsApp de forma INMEDIATA a un contacto específico.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_contacto": {
                        "type": "string",
                        "description": "El nombre del contacto al que se enviará el mensaje (ej. MAMA, TITO, JOSHUA)."
                    },
                    "mensaje": {
                        "type": "string",
                        "description": "El contenido del mensaje que se va a enviar."
                    }
                },
                "required": ["nombre_contacto", "mensaje"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "llamada_whatsapp",
            "description": "Inicia una llamada de WhatsApp INMEDIATA a un contacto.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_contacto": {
                        "type": "string",
                        "description": "El nombre del contacto a llamar."
                    }
                },
                "required": ["nombre_contacto"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "colgar",
            "description": "Cuelga o finaliza la llamada en curso.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "abrir_camara",
            "description": "Abre la cámara web para tomar una foto o ver el entorno.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "Reconocimiento_Facial",
            "description": "Activa la cámara para realizar reconocimiento facial biométrico del usuario.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "Abrir_Apps",
            "description": "Abre una aplicación instalada en la computadora (ej. Spotify, Word, Excel).",
            "parameters": {
                "type": "object",
                "properties": {
                    "Aplicacion": {
                        "type": "string",
                        "description": "El nombre de la aplicación a abrir."
                    }
                },
                "required": ["Aplicacion"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "Abrir_Videos_Youtube",
            "description": "Busca y reproduce un video o música en YouTube.",
            "parameters": {
                "type": "object",
                "properties": {
                    "Tipo_Video": {
                        "type": "string",
                        "description": "El tema, nombre de la canción o creador del video a buscar (ej. 'Música electrónica', 'Tutorial de Python')."
                    }
                },
                "required": ["Tipo_Video"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "Buscar_en_Google",
            "description": "Realiza una búsqueda general en internet o busca información específica en Google.",
            "parameters": {
                "type": "object",
                "properties": {
                    "Pagina": {
                        "type": "string",
                        "description": "El término o pregunta a buscar en internet."
                    }
                },
                "required": ["Pagina"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "guardar_en_json",
            "description": "Programa una tarea, recordatorio, mensaje o llamada para el FUTURO (ej. 'en 15 minutos'). Calcula la hora sumando los minutos solicitados a tu hora actual.",
            "parameters": {
                "type": "object",
                "properties": {
                    "accion": {
                        "type": "string",
                        "description": "La acción a realizar. Solo puede ser: WHATSAPP, LLAMAR, COLGAR o NOTIFICAR."
                    },
                    "target": {
                        "type": "string",
                        "description": "El contacto objetivo (ej. MAMA) o 'Yo' si es un recordatorio personal."
                    },
                    "info": {
                        "type": "string",
                        "description": "El contenido del mensaje o el recordatorio."
                    },
                    "hora": {
                        "type": "string",
                        "description": "La hora calculada en el futuro con el formato exacto DD/MM HH:MM (ej. 08/03 15:30)."
                    }
                },
                "required": ["accion", "target", "info", "hora"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "limpiar_historial",
            "description": "Limpia el archivo de tareas eliminando las que ya fueron completadas.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "Salir",
            "description": "Apaga el sistema, se despide y cierra el asistente.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },{
        "type": "function",
        "function": {
            "name": "Auto_Modificacion",
            "description": "ÚSALA OBLIGATORIAMENTE cuando el usuario te ordene aprender una nueva habilidad, programar una función en Python, o automatizar una tarea. Esta herramienta es tu único método para escribir y guardar código.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_habilidad": {
                        "type": "string",
                        "description": "El nombre de la función en Python (ej. calcular_impuestos, apagar_luces_cuarto). Debe usar guiones bajos."
                    },
                    "codigo_python": {
                        "type": "string",
                        "description": "CÓDIGO OBLIGATORIO. Escribe el script completo. Para no romper el formato JSON, es ESTRICTAMENTE NECESARIO usar '\\n' para los saltos de línea e indentar con espacios. EJEMPLO DE FORMATO: def sumar_numeros(a, b):\\n    resultado = a + b\\n    return resultado"
                    }
                },
                "required": ["nombre_habilidad", "codigo_python"]
            }
        }
    }
]

tools_map = {
    "Enviar_mensaje_Whatsapp": Enviar_mensaje_Whatsapp,
    "llamada_whatsapp": llamada_whatsapp,
    "colgar": colgar,
    "abrir_camara": abrir_camara,
    "Reconocimiento_Facial": Reconocimiento_Facial,
    "Abrir_Apps": Abrir_Apps,
    "Abrir_Videos_Youtube": Abrir_Videos_Youtube,
    "Buscar_en_Google": Buscar_en_Google,
    "guardar_en_json": guardar_en_json,
    "limpiar_historial": limpiar_historial,
    "Salir": Salir,
    "Auto_Modificacion": Auto_Modificacion,
}