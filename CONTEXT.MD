# CrossRecord — contexto para frontend

Contrato de integración entre la aplicación móvil y el backend. No contiene secretos, URI de MongoDB ni claves de terceros.

## API y convenciones

- Base URL de producción: `https://cross-record.vercel.app/api/v1`
- JSON UTF-8. IDs = strings MongoDB ObjectId. Fechas = ISO 8601 UTC, por ejemplo `2026-10-23T17:40:10Z`.
- En rutas protegidas: `Authorization: Bearer <access_token>`.
- Errores: `{ "error": "..." }`; errores nativos JWT pueden usar `{ "msg": "..." }`.
- Paginación: `?limit=20&offset=0`; `limit` entre 1 y 50; `next_offset: null` significa final.

## Sesión y usuario

### Registro y login

`POST /auth/register`

```json
{
  "email": "robert@example.com",
  "password": "minimo-8-caracteres",
  "username": "robert",
  "name": "Robert",
  "last_name": "Tovar",
  "weight": 72.5,
  "profile_private": false
}
```

`weight` y `profile_private` son opcionales. `POST /auth/login` recibe `{ "email", "password" }`. Ambas rutas responden con:

```ts
type AuthResponse = {
  user: CurrentUser;
  access_token: string;
};

type PublicUser = {
  id: string;
  username: string;
  name: string;
  profile_picture: string | null;
  profile_private: boolean;
};

type CurrentUser = PublicUser & {
  email: string;
  email_verified: boolean;
  last_name: string;
  weight: number | null; // kg
  premium: boolean;
  show_ads: boolean; // !premium
  is_admin: boolean;
};
```

Guardar el token de forma segura. El login reactiva una cuenta desactivada. Desactivar una cuenta o restablecer contraseña invalida sesiones anteriores.

### Verificación y recuperación

| Uso | Ruta | Body | Respuesta |
| --- | --- | --- | --- |
| Reenviar correo | `POST /auth/verify-email/request` | Ninguno, autenticado | `202 { "sent": true }` |
| Confirmar correo | `POST /auth/verify-email/confirm` | `{ "token" }` | `{ "verified": true }` |
| Solicitar contraseña | `POST /auth/password-reset/request` | `{ "email" }` | Siempre `202 { "sent": true }` |
| Nueva contraseña | `POST /auth/password-reset/confirm` | `{ "token", "password" }` | `{ "reset": true }` |

Los enlaces de correo son `/verify-email?token=...` y `/reset-password?token=...`; duran una hora y se usan una vez. Un usuario no verificado puede login y `GET /me`, pero el resto de la app devuelve `403 Email verification required`: mostrar pantalla/banner de verificación.

### Perfil y cuenta

| Ruta | Uso |
| --- | --- |
| `GET /me` | Usuario de la sesión, incluso sin email verificado. |
| `PATCH /me` | Editar `name`, `last_name`, `username`, `weight`, `profile_picture`, `profile_private`. |
| `DELETE /me` | Desactivar temporalmente: `{ "deactivated": true }`. |
| `GET /users?q=rob` | Buscar por prefijo de username. |
| `GET /users/{userId}` | Perfil y mejores marcas actuales visibles. |

Los perfiles nunca exponen email ajeno, hashes, contraseñas ni estado interno. Una cuenta desactivada se oculta de perfiles, búsqueda y feed.

## Relaciones y privacidad

| Ruta | Uso |
| --- | --- |
| `POST /users/{userId}/follow` | Seguir; devuelve `{ "following": true, "are_friends": boolean }`. |
| `DELETE /users/{userId}/follow` | Dejar de seguir; devuelve `{ "following": false }`. |
| `GET /me/following` | Personas a las que sigo. |
| `GET /me/followers` | Personas que me siguen. |
| `GET /me/friends` | Seguimiento mutuo. |

Amistad = ambos usuarios se siguen. Dejar de seguir no cancela retos ya existentes.

Reglas de visibilidad:

1. El propietario siempre puede ver sus récords.
2. `is_private: true` solo lo puede ver el propietario.
3. Récord compartido en perfil público: cualquier usuario autenticado.
4. Récord compartido en perfil privado: solo amigos.
5. Perfil: `GET /users/{id}` devuelve `{ user, records, are_friends }`; `records` son las mejores marcas actuales visibles.

## Catálogo

```ts
type Exercise = {
  id: string; slug: string; name: string;
  kind: "calisthenic" | "weighted" | "cardio" | "mixed";
  record_kinds: Array<"calisthenic" | "weighted" | "cardio">;
  domain: "weightlifting" | "gymnastics" | "monostructural" | "plyometric" | "core" | "strongman" | string;
  family: string; equipment: string[]; aliases: string[]; created_at: string;
};
type Variation = {
  id: string; exercise_id: string; slug: string; name: string;
  kind: "calisthenic" | "weighted" | "cardio";
  equipment: string[]; aliases: string[];
  record_protocol: "max_reps" | "max_load" | "fastest_time";
  record_enabled: boolean; created_at: string;
};
```

| Ruta | Uso |
| --- | --- |
| `GET /exercises?kind=calisthenic` | Catálogo; `kind` opcional. |
| `GET /exercises/{exerciseId}/variations` | Variaciones del ejercicio. |
| `POST /exercises` | Solo admin: `{ "name", "kind" }`. |
| `POST /exercises/{exerciseId}/variations` | Solo admin: `{ "name" }`. |

La UI normal consume catálogo remoto: no codificar IDs. `kind: "mixed"` significa que sus variaciones tienen distintos formatos de récord (por ejemplo, Squat incluye Air Squat por repeticiones y Back Squat por kg). Las rutas POST son administrativas.

El seed `CrossFit v1` carga fuerza, levantamientos olímpicos, dumbbells, kettlebells, gimnasia, core, pliometría, strongman y cardio. Si `record_enabled` es `false`, la variación se muestra en el catálogo pero la UI debe deshabilitar el botón de registrar y mostrar “Próximamente”; requiere contexto adicional no soportado aún, como metros de farmer carry o distancia de sled push.

## Registros

```ts
type Record = {
  id: string;
  user_id: string;
  exercise_id: string;
  variation_id: string;
  kind: "calisthenic" | "weighted" | "cardio";
  value: number;
  distance_m: number | null;
  performed_at: string;
  created_at: string;
  is_private: boolean;
  bodyweight: number | null;
  challenge_id: string | null;
};
```

| Tipo | `value` | `distance_m` | Mejor resultado |
| --- | --- | --- | --- |
| `calisthenic` | Repeticiones enteras | `null` | Mayor valor |
| `weighted` | Kg, hasta 2 decimales | `null` | Mayor valor |
| `cardio` | Tiempo entero, segundos | Obligatorio, metros hasta 2 decimales | Menor valor |

`POST /records` crea una marca. Ejemplo:

```json
{ "variation_id": "...", "value": 12, "performed_at": "2026-10-23T18:00:00Z", "is_private": false, "distance_m": 5000 }
```

Para cardio `distance_m` es obligatorio. Los registros nuevos son privados por defecto. El switcher **Publicar récord** debe enviar `is_private: false`.

| Ruta | Uso |
| --- | --- |
| `POST /records/preview` | Preview antes de crear. |
| `POST /records/{recordId}/preview` | Preview antes de editar valor o fecha. |
| `GET /me/records?variation_id=...` | Historial; cardio exige `distance_m`. |
| `PATCH /records/{recordId}/visibility` | Body `{ "is_private": false }`. |
| `PATCH /records/{recordId}` | Editar `value`, `performed_at`, `is_private`. |
| `DELETE /records/{recordId}` | Borrar. |

La fecha puede ser pasada, pero no anterior al último registro de la misma variación (y distancia en cardio). Al editar fecha debe quedar entre sus registros adyacentes. Máximo cinco minutos de fecha futura.

### Límite gratis

Gratis debe pedir `variation_id`; recibe los tres registros más recientes de esa variación (cardio: variación + distancia):

```json
{ "items": ["maximo tres Record"], "has_more_locked": true, "next_offset": null }
```

`has_more_locked: true` debe abrir el paywall. Gratis no puede usar offset ni editar/borrar un registro fuera de esos tres. Premium recibe historial paginado completo y puede omitir `variation_id`. Las mejores marcas del perfil siguen visibles aunque sean antiguas.

## Retos

1. Consultar `GET /challenges/options?user_id={recipientId}&variation_id={variationId}`. Para cardio incluir `distance_m`.
2. La respuesta incluye `baseline`, `limits: { min, max, step }` y `max_percentage`.
3. La UI solo permite valores de esos límites; no los calcula localmente.
4. Crear: `POST /challenges` con `{ user_id, variation_id, target, distance_m?, message? }`.

Solo se puede retar a amigos y si la mejor marca del destinatario es visible. Hay un único reto activo por destinatario + variación + distancia. Vence inicialmente en siete días.

| Tipo | Máximo | Regla |
| --- | --- | --- |
| Calistenia | 20% | Enteros; el incremento sube solo si fracción >= 0.65. |
| Peso | 10% | Paso de 0.01 kg. |
| Cardio | 15% | Menos segundos es mejor. |

Estados: `pending`, `accepted`, `rejected`, `cancelled`, `expired`, `completed`.

| Ruta | Quién |
| --- | --- |
| `GET /challenges` | Participantes. |
| `POST /challenges/{id}/accept` | Destinatario. |
| `POST /challenges/{id}/reject` | Destinatario. |
| `POST /challenges/{id}/cancel` | Creador. |
| `POST /challenges/{id}/complete` | Destinatario; crea récord y completa atómicamente. |

Antes de guardar una marca, llamar a `/records/preview`. Si responde un reto, pedir **Completar** o **Cancelar** y enviar al guardar:

```json
{ "challenge_id": "...", "challenge_target": 12, "challenge_decision": "complete" }
```

`challenge_decision` puede ser `complete` o `cancel`. El backend vuelve a validar todo. Un reto pendiente puede aceptarse/completarse al confirmar una marca actual. Un reto aceptado exige `performed_at` posterior a `accepted_at`. Si el resultado es cardio, alcanza objetivo cuando el tiempo es menor o igual al target.

Editar o borrar la marca base recalcula el objetivo usando el porcentaje elegido. Si cambia un reto aceptado, vuelve a pendiente, requiere nueva aceptación y tiene siete días nuevos. Si no hay objetivo válido, se cancela. Corregir o borrar una marca de finalización puede reabrir el reto.

## Feed

| Ruta | Contenido |
| --- | --- |
| `GET /feed/following` | Actividad propia y de usuarios seguidos; privacidad se revalida al leer. |
| `GET /feed/global` | Récords compartidos de perfiles públicos. |

```ts
type FeedItem = { record: Record; user: PublicUser; challenger: PublicUser | null };
```

Solo publica marcas compartidas que eran mejor marca al crearse. El orden usa `created_at` original, no fecha de corrección. Gratis solo ve tres publicaciones propias más recientes de mejor marca por variación/distancia; no limita publicaciones de otras personas ni el feed entero.

## Premium y estadísticas

Usar `me.premium` y `me.show_ads` para UI. Premium activa historial completo y:

`GET /me/statistics?variation_id=...` (cardio requiere `distance_m`).

```ts
type Statistics = {
  variation_id: string;
  distance_m: number | null;
  count: number;
  best: Record | null;
  first: number | null;
  last: number | null;
  change: number | null;
  change_percentage: number | null;
  series: Array<{ date: string; value: number }>;
};
```

En cardio, cambios positivos indican que el tiempo disminuyó. `403 Premium required` debe abrir paywall.

## Notificaciones internas

| Ruta | Uso |
| --- | --- |
| `GET /me/notifications` | Bandeja paginada. |
| `POST /me/notifications/{id}/read` | Marca leída: `{ "read": true }`. |

```ts
type Notification = {
  id: string; user_id: string; challenge_id: string;
  type: "received" | "accepted" | "rejected" | "cancelled" | "completed" | "reopened" | "target_changed" | "acceptance_required";
  created_at: string; read_at: string | null;
};
```

No hay push notifications. Refrescar la bandeja al abrir la app, volver a foreground y tras acciones de retos.

## Reglas de implementación UI

1. Después de mutar récord, invalidar perfil, historial, estadísticas, feed, retos y notificaciones.
2. Después de follow/unfollow, refrescar relaciones, perfil y feed siguiendo.
3. Después de acción de reto, refrescar retos, notificaciones, feed y perfil.
4. Formatear cardio a `mm:ss` solo para mostrar; enviar segundos numéricos.
5. `401`: sesión no válida. `403 Email verification required`: verificación. `403 Premium required`: paywall. `409`: refrescar datos/preview y pedir confirmación otra vez.

## Límites actuales del backend

- `profile_picture` es una URL externa o `null`; no hay subida de imágenes.
- Premium y anuncios se gestionan en servidor; no hay compras integradas.
- No hay endpoint raíz ni `/health`; API bajo `/api/v1`.
- No hay CORS configurado. No afecta a apps iOS/Android nativas; un frontend web necesitará política CORS antes de consumir la API.
