import anthropic
import json
import datetime
import re
import sys

client = anthropic.Anthropic()

PROMPT = """Eres un asistente especializado en descuentos de combustible en Argentina.

Tu tarea es buscar en la web los descuentos vigentes para este mes en estaciones de servicio de Argentina (YPF, Shell, Axion Energy, Puma Energy) con todos los bancos y billeteras.

Buscá en sitios como Infobae, Cronista, La Nacion, Ambito, o los sitios oficiales de los bancos.

Devolvé SOLO un JSON válido con esta estructura exacta (sin texto adicional, sin markdown, sin explicaciones):

{
  "ultima_actualizacion": "YYYY-MM-DD",
  "mes": "Mes YYYY",
  "estaciones": [
    {
      "id": "ypf",
      "nombre": "YPF",
      "color": "#009B77",
      "apps": [
        { "nombre": "Nombre del beneficio", "detalle": "descripción corta" }
      ],
      "bancos": [
        {
          "banco": "Nombre del banco",
          "descuento": "XX%",
          "dia": "Día de la semana",
          "detalle": "descripción detallada con tope",
          "nivel": "alto|medio|bajo"
        }
      ]
    }
  ],
  "descuentos_generales": [
    {
      "banco": "Nombre",
      "descuento": "XX%",
      "dia": "Día",
      "detalle": "descripción",
      "nivel": "alto|medio|bajo"
    }
  ]
}

Reglas:
- nivel "alto" = descuento >= 20%
- nivel "medio" = descuento 10-19%
- nivel "bajo" = descuento < 10%
- Incluí SIEMPRE las 4 estaciones: ypf, shell, axion, puma con sus colores (#009B77, #E8282B, #0057A8, #5C2D8A)
- ultima_actualizacion debe ser hoy: """ + datetime.date.today().isoformat() + """
- mes debe ser el mes actual en español: """ + datetime.date.today().strftime("%B %Y").capitalize() + """
- Si no encontrás info de algún banco, omitilo, no inventes datos
- Devolvé ÚNICAMENTE el JSON, nada más"""

def actualizar_data():
    print(f"[{datetime.datetime.now()}] Iniciando actualización de data.json...")

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=4096,
        tools=[{
            "type": "web_search_20250305",
            "name": "web_search"
        }],
        messages=[
            {"role": "user", "content": PROMPT}
        ]
    )

    # Extraer el texto de la respuesta
    texto = ""
    for block in message.content:
        if block.type == "text":
            texto += block.text

    # Limpiar posible markdown
    texto = texto.strip()
    if texto.startswith("```"):
        texto = re.sub(r"^```[a-z]*\n?", "", texto)
        texto = re.sub(r"\n?```$", "", texto)
    texto = texto.strip()

    # Validar que sea JSON válido
    data = json.loads(texto)

    # Verificar estructura mínima
    assert "estaciones" in data, "Falta campo 'estaciones'"
    assert len(data["estaciones"]) >= 1, "No hay estaciones"

    # Guardar
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[{datetime.datetime.now()}] data.json actualizado correctamente.")
    print(f"  Mes: {data.get('mes')}")
    print(f"  Estaciones: {len(data.get('estaciones', []))}")
    total_bancos = sum(len(e.get('bancos', [])) for e in data.get('estaciones', []))
    print(f"  Total descuentos bancarios: {total_bancos}")

if __name__ == "__main__":
    try:
        actualizar_data()
    except json.JSONDecodeError as e:
        print(f"Error: la respuesta no es JSON válido: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error inesperado: {e}")
        sys.exit(1)
