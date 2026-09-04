# DIAZO — Smart Food Scale (ESP32) Integration Guide

This explains how to connect the ESP32 smart scale to the DIAZO backend. The scale measures **food weight** during meal logging — the patient can choose to weigh their food on the scale, or type the amount in manually. Both options exist side by side in the app.

---

## 1. What you need to send

Every time the scale has a new, stable weight reading, send an **HTTP POST request**.

**Endpoint:**
```
POST https://<your-backend-url>/api/v1/hardware/meal-weight-readings
```
(For local testing before deployment: `http://<your-computer's-local-IP>:8000/api/v1/hardware/meal-weight-readings` — the ESP32 and your computer need to be on the same Wi-Fi network.)

**Headers:**
```
Content-Type: application/json
X-Device-Key: <shared secret — we'll give you this value separately>
```

The `X-Device-Key` header is required — requests without it (or with the wrong value) will be rejected with a `401` error. This key should be hardcoded into the ESP32 firmware.

**Body (JSON):**
```json
{
  "patient_id": "265f7e92-63fd-49e1-a933-65a2fa479d3e",
  "device_id": "scale-01",
  "weight_g": 184.5
}
```

- `patient_id` — a fixed UUID identifying which patient this scale belongs to. Hardcode this into the firmware — every reading from this specific scale sends the same `patient_id`.
- `device_id` — any short identifier for the physical device itself (e.g. `"scale-01"`). Useful if we ever have multiple scales; can be a fixed string in firmware.
- `weight_g` — the measured weight in **grams** (not kg — food portions are small, grams keeps this precise). This is the canonical field name used by the firmware and backend.

---

## 2. What happens on our side

Once we receive the reading, the backend:
1. Stores it as a `meal_weight_reading` record (with a timestamp)
2. Pushes it live to the patient's dashboard over WebSocket, if they have the app open with the meal-logging form active

If the patient is actively logging a meal, they'll see the live weight appear on screen and can confirm/save it as that meal's portion — or ignore it and type the amount manually instead. Both paths are supported; the scale is optional, not required.

The `201` response contains the stored reading, for example:
```json
{
  "id": "...",
  "patient_id": "265f7e92-63fd-49e1-a933-65a2fa479d3e",
  "device_id": "scale-01",
  "weight_g": 184.5
}
```

After the patient selects food and logs the measured meal, poll the LED endpoint with the same `X-Device-Key`:

```text
GET /api/v1/hardware/scale-status/scale-01
```

It returns `"GREEN"` for `WITHIN_TARGET`, `"RED"` for `ABOVE_TARGET`, or `"PENDING"` while the patient has not yet completed food selection. Keep both LEDs off for `PENDING`.

---

## 3. Getting the values you need

- **`X-Device-Key`** — ask us; this is a shared secret we'll set once and give you directly (not something to guess or generate yourself).
- **`patient_id`** — for testing, ask us for a real patient's UUID, or (if you have API access) log in as that patient and call `GET /api/v1/patients/me` — the `user_id` field is the value to use.

---

## 4. Example ESP32 code (Arduino/C++, using WiFiClient + HTTPClient)

```cpp
#include <WiFi.h>
#include <HTTPClient.h>

const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* endpoint = "http://YOUR_BACKEND_URL/api/v1/hardware/meal-weight-readings";
const char* deviceKey = "PASTE_THE_SHARED_SECRET_HERE";
const char* patientId = "265f7e92-63fd-49e1-a933-65a2fa479d3e";
const char* deviceId = "scale-01";

void sendWeightReading(float weightGrams) {
  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;
  http.begin(endpoint);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-Device-Key", deviceKey);

  String payload = String("{\"patient_id\":\"") + patientId +
                    "\",\"device_id\":\"" + deviceId +
                    "\",\"weight_g\":" + String(weightGrams, 1) + "}";

  int responseCode = http.POST(payload);
  // responseCode should be 201 on success, 401 if the device key is wrong
  http.end();
}
```

Call `sendWeightReading(currentWeight)` only once the load cell reading has settled/stabilized — no need to send continuously while the weight is still changing.

---

## 5. Testing without the physical device yet

You can test this endpoint right now with Postman, curl, or our Swagger docs (`/docs`, under the "hardware" section) by sending the same headers/body manually — confirms the backend side works before your firmware is ready.

Example curl:
```bash
curl -X POST https://<backend-url>/api/v1/hardware/meal-weight-readings \
  -H "Content-Type: application/json" \
  -H "X-Device-Key: <the shared secret>" \
  -d '{"patient_id":"265f7e92-63fd-49e1-a933-65a2fa479d3e","device_id":"scale-01","weight_g":184.5}'
```

---

## 6. Known limitations (by design)

- **One shared device key**, not per-device unique tokens — simple, appropriate for this project's scope, not meant for a large fleet of devices.
- **`patient_id` is fixed per device** — no dynamic device-pairing flow exists yet. If a scale needs to work for multiple patients later, that would need a future pairing mechanism.

---

Questions or anything here doesn't match what you're building — let us know and we'll adjust the endpoint or this doc.
