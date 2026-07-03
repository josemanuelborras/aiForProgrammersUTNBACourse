# Actividad Practica Final - IA para Programadores (Claude)

Implementacion independiente del modulo funcional de autenticacion para la
actividad final, disenada y probada con asistencia de Claude (Claude Code).
Esta version comparte el dominio (registro, login, validacion de token) con
las carpetas hermanas `copilot/` y `antiogravity/` del mismo repositorio,
pero con decisiones de diseno propias, pensadas para agregar escenarios de
prueba mas ricos:

- Hash de contrasena con PBKDF2-HMAC-SHA256 (en vez de SHA256 simple).
- Validacion de fortaleza de contrasena (longitud minima, letra + digito).
- Tokens firmados con HMAC (`payload.signature`), no solo Base64 plano:
  detectan manipulacion (tampering), no solo expiracion.
- Bloqueo de cuenta tras 3 intentos de login fallidos consecutivos.
- Normalizacion de username (trim + lowercase) para evitar duplicados
  como `"Alice"` vs `" alice "`.

## 1. Estructura del proyecto

```text
src/auth_module/
  security.py   # hashing PBKDF2 y validacion de fortaleza de password
  tokens.py     # tokens firmados con HMAC, deteccion de manipulacion
  service.py    # AuthService: registro, login con bloqueo, validate_token
  api.py        # capa HTTP (Flask): /health, /register, /login, /validate
tests/
  unit/
    test_security.py
    test_tokens.py
    test_auth_service.py
    test_service_baseline.py   # suite minima usada para medir el "antes"
  functional/
    test_auth_api.py           # pruebas end-to-end via Flask test client
.github/workflows/ci.yml
```

## 2. Escenarios funcionales mapeados

1. Registro exitoso de usuario.
2. Registro rechazado: username o password vacios.
3. Registro rechazado: password debil (corta / sin letra / sin digito).
4. Registro rechazado: usuario duplicado (incluye normalizacion de mayusculas
   y espacios).
5. Login exitoso, emite token firmado.
6. Login rechazado: usuario inexistente.
7. Login rechazado: password incorrecta (incrementa contador de fallos).
8. Cuenta bloqueada tras 3 fallos consecutivos, incluso con password correcta.
9. El contador de fallos se resetea tras un login exitoso.
10. Validacion de token valido y no expirado.
11. Validacion rechazada: token vacio, token con formato invalido, token con
    firma adulterada, token con payload incompleto, token expirado.
12. Recorrido end-to-end de los mismos escenarios a traves de la API HTTP
    (`/register`, `/login`, `/validate`, incluyendo el 423 por bloqueo).

## 3. Ejecutar localmente

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pytest
```

## 4. Cobertura antes y despues de optimizar

Baseline (solo happy-path, 3 pruebas):

```bash
pytest tests/unit/test_service_baseline.py --cov=src/auth_module --cov-report=term-missing
```

Resultado medido: **67% de cobertura** (51 lineas sin cubrir de 153), dejando
sin probar toda la capa HTTP, los casos de error de seguridad y la deteccion
de manipulacion de tokens.

Suite optimizada (completa):

```bash
pytest --cov=src/auth_module --cov-report=term-missing --cov-report=html --cov-report=xml
```

Resultado medido: **100% de cobertura** (0 lineas sin cubrir de 153).
Estado de los tests: **47 passed**.

La diferencia se explica por agregar deliberadamente los casos borde de
seguridad (password debil, bloqueo de cuenta, token adulterado, payload
incompleto, token expirado) que el baseline, al probar solo el camino feliz,
no ejercita.

## 5. Uso de IA

Todo el diseno del modulo, la suite de pruebas y el pipeline de CI de esta
carpeta fueron generados con asistencia de **Claude Code**, usado para:

1. Proponer el diseno del modulo (separacion security/tokens/service/api) y
   decidir que casos borde de seguridad valia la pena cubrir.
2. Generar los casos de prueba unitarios y funcionales, incluyendo los que
   requieren construir tokens manualmente (firma valida + payload invalido)
   para forzar ramas de error dificiles de alcanzar.
3. Iterar sobre el reporte de cobertura (`--cov-report=term-missing`) para
   identificar lineas sin cubrir y escribir la prueba especifica que las
   ejercita, hasta llegar a 100%.

## 6. CI/CD

El pipeline en [`.github/workflows/ci.yml`](.github/workflows/ci.yml) ejecuta:

1. Instalacion de dependencias.
2. Suite de pruebas con cobertura.
3. Publicacion de `coverage.xml` y `htmlcov/` como artefactos.
