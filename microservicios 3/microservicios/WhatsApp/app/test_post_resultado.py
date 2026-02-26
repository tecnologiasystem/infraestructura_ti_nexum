"""
Script para probar el POST de resultados y verificar que el worker los procesa.
"""
import requests
import time
import json

API_URL = "http://localhost:8000"  # Ajusta según tu configuración

def test_enviar_resultado():
    """
    Envía un resultado de prueba al API.
    """
    url = f"{API_URL}/automatizacion/resultadoWhatsApp"
    
    payload = {
        "indicativo": "57",
        "numero": "3001234567",
        "tiene_whatsApp": "SI"
    }
    
    print("📤 Enviando resultado de prueba...")
    print(f"   URL: {url}")
    print(f"   Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload)
        print(f"\n✅ Respuesta del servidor:")
        print(f"   Status: {response.status_code}")
        print(f"   Body: {response.json()}")
        
        if response.status_code in [200, 202]:
            print("\n🎉 ¡Resultado encolado exitosamente!")
            print("   Revisa los logs del worker para ver si se procesa.")
            return True
        else:
            print(f"\n❌ Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error al enviar: {e}")
        return False


def test_multiples_resultados():
    """
    Envía múltiples resultados para probar el procesamiento en batch.
    """
    url = f"{API_URL}/automatizacion/resultadoWhatsApp"
    
    numeros_prueba = [
        ("57", "3001111111", "SI"),
        ("57", "3002222222", "NO"),
        ("57", "3003333333", "SI"),
        ("57", "3004444444", "SI"),
        ("57", "3005555555", "NO"),
    ]
    
    print(f"📤 Enviando {len(numeros_prueba)} resultados de prueba...\n")
    
    exitosos = 0
    fallidos = 0
    
    for i, (indicativo, numero, tiene_wa) in enumerate(numeros_prueba, 1):
        payload = {
            "indicativo": indicativo,
            "numero": numero,
            "tiene_whatsApp": tiene_wa
        }
        
        try:
            response = requests.post(url, json=payload)
            if response.status_code in [200, 202]:
                print(f"   ✅ {i}. {numero}: Encolado")
                exitosos += 1
            else:
                print(f"   ❌ {i}. {numero}: Error {response.status_code}")
                fallidos += 1
        except Exception as e:
            print(f"   ❌ {i}. {numero}: {e}")
            fallidos += 1
        
        time.sleep(0.1)  # Pequeña pausa entre requests
    
    print(f"\n📊 Resumen:")
    print(f"   ✅ Exitosos: {exitosos}")
    print(f"   ❌ Fallidos: {fallidos}")
    print(f"\n💡 Revisa los logs del worker para verificar que se procesaron")


if __name__ == "__main__":
    import sys
    
    print("="*60)
    print("🧪 PRUEBA DE POST /automatizacion/resultadoWhatsApp")
    print("="*60)
    print()
    
    if len(sys.argv) > 1 and sys.argv[1] == "multiple":
        test_multiples_resultados()
    else:
        test_enviar_resultado()
        print("\n💡 Para enviar múltiples resultados:")
        print("   python test_post_resultado.py multiple")
