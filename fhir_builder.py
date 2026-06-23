from datetime import datetime
import uuid

def construir_receta_fhir_minsal(folio_interno, paciente_rut, paciente_nombre, medico_rut, medico_nombre, medico_rnpi, codigo_deis, codigo_snomed, desc_diagnostico, codigo_tfc, desc_medicamento, indicaciones, cantidad_dispensar, dias_validez):
    """
    Construye el Payload JSON exacto exigido por MINSAL para RecetaPrescripcionCl v0.9.6
    """
    
    fecha_actual_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # 1. Empaquetado del recurso MedicationRequest
    payload_fhir = {
        "resourceType": "MedicationRequest",
        "meta": {
            "profile": [
                "https://interoperabilidad.minsal.cl/fhir/ig/snre/StructureDefinition/RecetaPrescripcionCl"
            ]
        },
        "identifier": [
            {
                "system": "http://medicinadeportivaosorno.cl/folios",
                "value": folio_interno
            }
        ],
        "status": "active",
        "intent": "order",
        
        # Medicamento referenciado por TFC (Terminología Farmacéutica Chilena)
        "medicationCodeableConcept": {
            "coding": [
                {
                    "system": "http://minsal.cl/term/tfc",
                    "code": codigo_tfc,
                    "display": desc_medicamento
                }
            ],
            "text": desc_medicamento
        },
        
        # Identificación del Paciente
        "subject": {
            "identifier": {
                "system": "http://regcivil.cl/Validacion/RUT",
                "value": paciente_rut
            },
            "display": paciente_nombre
        },
        
        "authoredOn": fecha_actual_iso,
        
        # Identificación del Médico Prescriptor (Practitioner)
        "requester": {
            "identifier": {
                "system": "http://minsal.cl/rnpi",
                "value": medico_rnpi
            },
            "display": medico_nombre
        },
        
        # Identificación de la Clínica MDO (Organization)
        "performer": {
            "identifier": {
                "system": "http://minsal.cl/deis",
                "value": codigo_deis
            },
            "display": "Medicina Deportiva Osorno"
        },
        
        # Diagnóstico referenciado por SNOMED-CT
        "reasonCode": [
            {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": codigo_snomed,
                        "display": desc_diagnostico
                    }
                ]
            }
        ],
        
        # Instrucciones de uso para el paciente
        "dosageInstruction": [
            {
                "text": indicaciones
            }
        ],
        
        # Instrucciones de dispensación para la Farmacia
        "dispenseRequest": {
            "validityPeriod": {
                "start": fecha_actual_iso.split("T")[0] # Solo la fecha YYYY-MM-DD
            },
            "quantity": {
                "value": float(cantidad_dispensar),
                "unit": "unidades"
            },
            "expectedSupplyDuration": {
                "value": float(dias_validez),
                "unit": "días",
                "system": "http://unitsofmeasure.org",
                "code": "d"
            }
        }
    }
    
    return payload_fhir
