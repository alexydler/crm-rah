"""Datos FICTICIOS compartidos por las pruebas."""
import uuid

ISSUER = 'http://localhost:8080/realms/rah-vzla-test'
AUDIENCE = 'rah-vzla-api'
APP_ROLE = 'rah_app_test'

ORG_A = uuid.UUID('11111111-1111-4111-8111-111111111111')  # DEMO Caracas
ORG_B = uuid.UUID('22222222-2222-4222-8222-222222222222')  # DEMO Valencia
ORG_SUSP = uuid.UUID('33333333-3333-4333-8333-333333333333')
ORG_V1_DEMO = uuid.UUID('44444444-4444-4444-8444-444444444444')

SUB_A = 'sub-demo-a'          # propietario de A
SUB_B = 'sub-demo-b'          # propietario de B
SUB_AB = 'sub-demo-ab'        # gerente en A y en B
SUB_MKT = 'sub-demo-mkt'      # marketing en A
SUB_CONS = 'sub-demo-consulta'  # consulta en A
SUB_SUSP = 'sub-demo-susp'    # propietario de org suspendida
SUB_NADIE = 'sub-demo-sin-membresia'

MEMBRESIAS = [
    (ORG_A, SUB_A, 'propietario'), (ORG_B, SUB_B, 'propietario'),
    (ORG_A, SUB_AB, 'gerente'), (ORG_B, SUB_AB, 'gerente'),
    (ORG_A, SUB_MKT, 'marketing'), (ORG_A, SUB_CONS, 'consulta'),
    (ORG_SUSP, SUB_SUSP, 'propietario'),
]
