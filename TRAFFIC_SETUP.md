# GitHub Traffic — activación

El panel está en [traffic.html](traffic.html). **No publiques el token, ni el archivo traffic.json**. El dashboard solo lee el historial del repositorio privado usando un token introducido manualmente (en memoria).

## Configuración inicial (una sola vez)

1. Creá un repositorio **privado** vacío llamado `repo-traffic-data` en la cuenta `mateofoulkes-lab`. Inicializalo con README si preferís. Verificá que siga siendo privado.
2. Creá un **Personal Access Token (classic)** desde GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic). Elegí vencimiento y alcance `repo` para permitir la lectura de las estadísticas de tráfico de repositorios propios y escribir en el repositorio privado. Este token tiene permisos amplios: guardalo como secreto, no lo pegues en archivos ni en el chat. Si preferís un fine-grained token, comprobá por separado que los endpoints Traffic y Contents tengan los permisos requeridos para todos tus repositorios.
3. Entrá al repositorio `tools` → Settings → Secrets and variables → Actions → New repository secret. Nombre exacto: `TRAFFIC_TOKEN`. Valor: el token.
4. Abrí [Actions → Archive GitHub traffic](https://github.com/mateofoulkes-lab/tools/actions/workflows/archive-traffic.yml) → **Run workflow**. Confirmá que el job terminó bien. Si hay errores, revisá sus logs, especialmente los permisos sobre repositorios privados.
5. Abrí [traffic.html](traffic.html) desde GitHub Pages (o el sitio donde publiques tools). Escribí tu cuenta, `repo-traffic-data` y un token con **solo lectura de Contents** del repositorio privado de datos, preferentemente otro fine-grained PAT diferente del usado para recolectar. No queda almacenado en localStorage ni cookies por el código del panel.

## Qué se archiva

Cada día a las 07:23 UTC, el workflow enumera los repositorios de la cuenta, consulta las ventanas disponibles de vistas y clonaciones e incorpora los datos al historial privado. La primera ejecución intenta recuperar el intervalo de aproximadamente 14 días que aún conserva GitHub. Los registros se combinan por fecha para evitar duplicación. El archivo `traffic.json` contiene métricas diarias por repositorio, incluyendo repositorios privados. No es información nominativa sobre visitantes.

- La API no identifica visitantes, ni permite separar visitas propias de las ajenas.
- La columna «únicos» suma los valores diarios, **no** es una cantidad deduplicada de personas a lo largo del período.
- Un repositorio sin datos accesibles no debe interpretarse automáticamente como cero visitantes.
- El dashboard no expone públicamente datos privados, pero cualquier persona que tenga acceso al token de lectura puede leerlos.
- Si la ejecución falla por permisos en algunos repositorios, el job se marca fallido pero conserva los datos recuperados de otros. Revisá los logs para corregirlo.
- Si quitás el permiso del token o el token expira, dejará de recoger datos. Se recomienda revisar los Actions periódicamente.

## Seguridad

Usá **dos tokens distintos**, si es posible: uno para la automatización (lectura Traffic de todos los repos y escritura Contents del repo privado) y otro limitado a **Contents: read** del repo privado para consultar el panel. Ambos deben mantenerse fuera de la web pública y rotarse si se exponen.

El repositorio de datos debe permanecer privado. Nunca copies `traffic.json` al repositorio público `tools`.
