# Informe Técnico — Suite de Pruebas Automatizadas (carpeta `claude`)

Este informe cubre el diseño de pruebas, el análisis de cobertura, la
integración de CI/CD y el uso de IA para la implementación del módulo de
autenticación en `claude/`, y la compara contra las otras dos
implementaciones del mismo ejercicio hechas con Copilot y Antigravity
(carpetas `copilot/` y `antiogravity/` del mismo repositorio local), ya que
las tres resuelven el mismo enunciado con asistentes de IA distintos.

## 1. Alcance funcional y escenarios mapeados

El módulo implementa registro, login y validación de token, pero con tres
decisiones de diseño que no están en las otras dos versiones y que existen
específicamente para dar a la suite de pruebas más ramas de riesgo real que
ejercitar:

- **Hashing con PBKDF2-HMAC-SHA256** (100.000 iteraciones) en vez de un
  SHA256 simple con salt.
- **Tokens firmados con HMAC** (`payload.signature`), que permiten distinguir
  "token malformado", "token adulterado" (firma no coincide) y "token
  expirado" como tres fallas distintas, en vez de un único caso de "token
  inválido".
- **Bloqueo de cuenta tras 3 intentos fallidos consecutivos** y reseteo del
  contador tras un login exitoso.

La lista completa de 12 escenarios está en [README.md](README.md#2-escenarios-funcionales-mapeados);
no se repite acá para no duplicar contenido.

## 2. Justificación del diseño de pruebas

Se usó una estrategia por capas, alineada al principio de que las pruebas
unitarias deben aislar reglas de negocio y las funcionales deben validar el
contrato HTTP que consume un cliente real:

- **`test_security.py`**: hashing determinístico dado un salt, salts
  distintos por defecto, y las 5 combinaciones de violación de fortaleza de
  password (corta, sin dígito, sin letra, ambas, válida) vía
  `@pytest.mark.parametrize` para no repetir el mismo assert cinco veces.
- **`test_tokens.py`**: además del roundtrip normal, se construyen tokens
  "a mano" reutilizando las funciones internas `_sign` y `_b64encode` del
  propio módulo para forzar dos ramas que son casi imposibles de alcanzar
  con un token generado normalmente: un payload que falla al decodificar
  como JSON pero tiene firma válida, y un payload válido pero sin los campos
  requeridos. Esta técnica fue una sugerencia directa de Claude al leer el
  reporte `--cov-report=term-missing` y ver esas dos líneas sin cubrir.
- **`test_auth_service.py`**: cubre el flujo de bloqueo completo (3 fallos →
  bloqueo → el bloqueo persiste incluso con password correcta) y el reseteo
  del contador, que es la lógica de negocio con más riesgo real de un bug
  silencioso (ej. resetear mal el contador y dejar cuentas bloqueables para
  siempre, o nunca bloqueables).
- **`test_auth_api.py`** (funcional): repite los mismos escenarios de negocio
  pero a través de `client.post(...)`, verificando los códigos HTTP exactos
  (`201`, `400`, `401`, `423`) — el `423 Locked` para cuenta bloqueada es una
  decisión de diseño de API que no existe en `copilot/` ni `antiogravity/`
  porque ninguna de las dos tiene bloqueo de cuenta.
- Se mantuvo una suite `test_service_baseline.py` separada e intacta (solo
  happy-path) exclusivamente para poder reproducir el número de cobertura
  "antes" en cualquier momento, sin depender de `git log`.

No se agregaron pruebas de carga, concurrencia o UI porque el enunciado pide
un módulo de auth/API básica, no un sistema distribuido: agregar esos casos
sería sobre-ingeniería para el alcance pedido.

**Por qué no se usó Selenium/Playwright para las pruebas funcionales:** el
enunciado los sugiere como herramientas de referencia, pero ambos automatizan
un *navegador* — tienen sentido cuando el módulo expone una UI web. Este
módulo es una API JSON pura (Flask), sin HTML ni JavaScript de por medio;
"lo funcional" acá es el contrato HTTP (rutas, códigos de estado, forma del
JSON de respuesta), no una interacción de usuario en pantalla. El test
client de Flask ejercita ese contrato end-to-end (request HTTP real →
routing → `AuthService` → response HTTP) sin necesidad de levantar un
navegador ni un servidor real, que sería una capa de infraestructura extra
sin valor de prueba adicional para este caso. Si el módulo entregado hubiera
sido una app con UI, Selenium/Playwright habría sido la elección correcta.

## 3. Análisis de cobertura antes y después

| Archivo | Baseline | Final |
|---|---:|---:|
| `__init__.py` | 100% | 100% |
| `api.py` | 12% | 100% |
| `security.py` | 81% | 100% |
| `service.py` | 79% | 100% |
| `tokens.py` | 86% | 100% |
| **TOTAL** | **67%** (51/153 líneas sin cubrir) | **100%** (0/153 sin cubrir) |

Comandos usados (reproducibles, ver [README.md](README.md#4-cobertura-antes-y-despues-de-optimizar)):

```bash
pytest tests/unit/test_service_baseline.py --cov=src/auth_module --cov-report=term-missing
pytest --cov=src/auth_module --cov-report=term-missing --cov-report=html --cov-report=xml
```

Resultado final: **47 passed**, 0 líneas sin cubrir. El salto de 67% a 100%
no vino de "maquillar" cobertura con asserts vacíos, sino de agregar
pruebas para ramas de error de seguridad que el baseline directamente no
ejecutaba: `api.py` pasó de 12% a 100% porque el baseline nunca probaba la
capa HTTP; `service.py` y `tokens.py` subieron por cubrir bloqueo de cuenta,
firma adulterada y payload incompleto.

## 4. Análisis comparativo: Copilot vs Antigravity vs Claude

Las tres carpetas resuelven el mismo módulo (registro/login/validación de
token) pero con decisiones de diseño y de IA distintas:

| | `copilot/` | `antiogravity/` | `claude/` |
|---|---|---|---|
| Hashing | SHA256 + salt | SHA256 + salt | PBKDF2-HMAC-SHA256 |
| Formato de token | JSON en Base64 (sin firma) | JSON en Base64 (sin firma) | `payload.firma` HMAC |
| Bloqueo de cuenta | No | No | Sí (3 intentos) |
| Validación de fortaleza de password | No | No | Sí |
| Líneas de `src/` | ≈105 | 106 | 153 |
| Tests totales | 18 | 24 | 47 |
| Cobertura baseline | 58% | 58% | 67% |
| Cobertura final | 98% (2 líneas sin cubrir) | 100% | 100% |
| Asistente de IA | GitHub Copilot | Antigravity | Claude Code |
| Rol de la IA | Autocompletado/sugerencias dentro del editor, revisadas manualmente | Agente que analiza el código estáticamente y propone casos borde puntuales | Agente que diseñó el módulo completo, escribió todo el código y las pruebas, ejecutó `pytest`/`coverage` él mismo e iteró sobre el resultado hasta 100% |

**Lectura crítica de la tabla:** comparar el "% de cobertura final" entre las
tres columnas de forma directa es engañoso. `claude/` tiene casi 50% más
líneas de código que las otras dos porque el módulo incluye más reglas de
negocio de seguridad (bloqueo, fortaleza de password, firma de tokens); por
eso necesitó más del doble de tests que `copilot/` para llegar a 100%. Un
100% de cobertura sobre un módulo más chico y más simple no es
necesariamente "mejor testing" que un 98% sobre un módulo más grande — la
métrica de cobertura solo tiene sentido interpretada junto con el alcance
funcional que cubre.

También es visible la diferencia en *cómo* participó cada IA: Copilot y
Antigravity actuaron como asistentes dentro de un flujo de trabajo que el
desarrollador seguía manejando paso a paso (aceptar/rechazar sugerencias,
correr los comandos manualmente). Claude Code operó de forma agéntica:
propuso la arquitectura, escribió los archivos, instaló dependencias, corrió
la suite, leyó el reporte de cobertura y volvió a escribir tests hasta
cerrar los huecos, sin que el desarrollador tuviera que ejecutar esos pasos
intermedios a mano.

## 5. Integración en CI/CD

Pipeline en [`.github/workflows/ci.yml`](.github/workflows/ci.yml):
checkout → setup de Python 3.12 → `pip install -r requirements.txt` →
`pytest --cov=src/auth_module --cov-report=term-missing --cov-report=xml
--cov-report=html` → subida de `coverage.xml` y `htmlcov/` como artefacto.

Se hizo push real a `main` en
[josemanuelborras/aiForProgrammersUTNBACourse](https://github.com/josemanuelborras/aiForProgrammersUTNBACourse)
y el workflow corrió exitosamente:

**Run:** https://github.com/josemanuelborras/aiForProgrammersUTNBACourse/actions/runs/28664597653
**Resultado:** `ci` — `completed` / `success`.

Además del artefacto que sube el propio pipeline, se commiteó una copia del
reporte de esa misma corrida (100% de cobertura) directo en el repositorio,
en [`coverage-report/`](coverage-report/htmlcov/index.html) (`index.html` +
`coverage.xml`), para que quede visible sin depender de descargar el
artefacto de Actions.

> Nota para la entrega: la captura de pantalla de esta corrida (pestaña
> *Actions* del repo) debe adjuntarse manualmente al informe final, ya que
> no hay forma de generar esa imagen desde este entorno.

## 6. Uso de IA (Claude Code)

Todo el contenido de `claude/` —diseño del módulo, tests, CI y este
informe— se generó con **Claude Code**. Concretamente se usó para:

1. Proponer la arquitectura (`security.py` / `tokens.py` / `service.py` /
   `api.py`) y decidir qué controles de seguridad agregar por encima del
   enunciado mínimo, para tener escenarios de prueba con valor real.
2. Escribir la suite completa, incluyendo la técnica de construir tokens
   manualmente con `_sign`/`_b64encode` para forzar ramas de error que un
   flujo normal de la app no genera.
3. Ejecutar la suite con cobertura, leer el reporte `term-missing` y cerrar
   iterativamente cada línea sin cubrir hasta 100%, sin intervención manual
   del estudiante en esa iteración.
4. Ejecutar `git init`, el commit y el push al repositorio remoto, y
   verificar el resultado real del pipeline vía la API pública de GitHub.

**Incidente real durante el proceso** (vale la pena documentarlo porque es
justamente el tipo de fricción que la reflexión crítica del enunciado pide
observar): al crear el entorno virtual dentro de `claude/.venv`, la
sincronización de OneDrive bloqueó archivos de `pip` a mitad de una
instalación y corrompió el venv. La solución no fue "ocultar" el error, sino
crear el entorno virtual fuera de la carpeta sincronizada por OneDrive y
volver a instalar ahí. Es un ejemplo concreto de que un agente de IA que
ejecuta comandos reales se topa con problemas de infraestructura que un
asistente de solo-sugerencias de código nunca ve.

## 7. Reflexión crítica

- **La cobertura alta es necesaria pero no suficiente.** Los tres proyectos
  llegan a coberturas altas (98–100%), pero eso no dice nada sobre si el
  *alcance* de lo que prueban es equivalente. `claude/` decidió ampliar el
  alcance funcional (bloqueo de cuenta, tokens firmados) precisamente para
  que un 100% de cobertura representara más garantías reales, no solo un
  número más alto.
- **El tipo de asistencia de IA importa tanto como la herramienta.** Un
  asistente de autocompletado (Copilot) acelera la escritura línea por
  línea, pero el desarrollador sigue orquestando todo el ciclo. Un agente
  (Claude Code, y en menor medida Antigravity) puede ejecutar el ciclo
  completo —código, pruebas, cobertura, CI, incluso el propio informe— lo
  que reduce fricción pero también exige más criterio humano para revisar
  *qué* decidió construir la IA, no solo si el código compila.
- **Usar tokens construidos manualmente en los tests fue una decisión
  deliberada, no un atajo.** Alcanzar ramas de error de seguridad
  (firma adulterada, payload incompleto) sin esa técnica hubiera requerido
  mockear internals o dejar esas líneas sin cubrir, como pasó con las 2
  líneas de `copilot/`. Cubrir código de seguridad con tests reales tiene
  valor especialmente alto porque son las rutas que un atacante ejercitaría
  primero.
- **Aprendizaje principal:** automatizar con IA de forma crítica no es
  "aceptar todo lo que sugiere", sino usarla para acelerar el ciclo
  hipótesis → prueba → medición (correr cobertura, ver qué falta, decidir si
  vale la pena cubrirlo) y quedarse con el criterio humano sobre qué
  escenarios importan para el dominio del problema.
