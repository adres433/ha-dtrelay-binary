# 🧾 CHANGELOG – Dingtian DT-Relay (Binary)

## [1.0.0] – 2025-11-09

### 🎉 Pierwsze publiczne wydanie

Pierwsze oficjalne wydanie integracji dla płytek **Dingtian DT-Relay**  
(DT-R002 / DT-R004 / DT-R008 / DT-R016 / DT-R032) działających w oparciu o **Dingtian Binary Protocol**.

---

### 🔌 Bez MQTT / Mosquitto

Integracja komunikuje się **bezpośrednio przez TCP/UDP** z urządzeniami, bez użycia protokołu MQTT.  
Dzięki temu oferuje:
- Niższe opóźnienia i szybsze działanie
- Brak konieczności uruchamiania brokera Mosquitto
- Mniejsze zużycie zasobów systemowych
- Prostsze wdrożenie i konfigurację

---

### 🚀 Funkcje

- Pełna obsługa Dingtian Binary Protocol (UDP/TCP)
- Automatyczne wykrywanie płytek w sieci (UDP multicast)
- Obsługa wielu urządzeń jednocześnie
- Dynamiczne wykrywanie kanałów (2–32)
- Konfiguracja przez GUI (Config Flow)
- Opcje Lockout i Pulse

---

### 👥 Współpraca i autorzy

Projekt opracowany wspólnie z asystentem AI (ChatGPT, OpenAI)  
w ramach projektu badawczego konfiguracji Home Assistant.  
Ostateczny kod, struktura i dokumentacja zostały zatwierdzone i rozwinięte przez użytkownika **adres433**.  
Całość objęta licencją **MIT**.
