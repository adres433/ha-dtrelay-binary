# Dingtian DT-Relay (Binary)

Integracja Home Assistant dla płytek przekaźnikowych **Dingtian DT-Rxxx** wykorzystujących **Dingtian Binary Protocol**.  
Komunikuje się **bezpośrednio przez TCP lub UDP**, bez konieczności użycia MQTT lub brokera Mosquitto.

## 🔌 Brak MQTT = Maksymalna Wydajność

Integracja działa w trybie **peer-to-device**, eliminując potrzebę dodatkowych usług pośredniczących.  
Zapewnia to:
- Niższe opóźnienia i szybszą reakcję przekaźników  
- Mniejsze zużycie zasobów CPU/RAM w systemie Home Assistant  
- Prostszą konfigurację i mniejszą liczbę potencjalnych błędów  
- Stabilność i natychmiastową komunikację binarną z urządzeniem

## 🚀 Funkcje

- Pełna obsługa Dingtian Binary Protocol (UDP/TCP)
- Automatyczne wykrywanie płytek w sieci (UDP multicast)
- Obsługa wielu urządzeń jednocześnie
- Dynamiczne wykrywanie kanałów (2–32)
- Konfiguracja przez GUI (Config Flow)
- Opcje Lockout i Pulse
