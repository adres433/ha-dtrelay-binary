# 🧠 Home Assistant – Dingtian DT-Relay Binary Integration

Integracja dla płytek przekaźnikowych **Dingtian DT-Relay (DT-R002, DT-R004, DT-R008, DT-R016, DT-R032)**  
opartych o **Dingtian Binary Protocol** i komunikujących się bezpośrednio przez **UDP lub TCP** – bez pośredników.

---

## 🚀 Funkcje

✅ Pełna obsługa **Dingtian Binary Protocol**  
✅ Bezpośrednia komunikacja TCP/UDP — **bez MQTT / Mosquitto**  
✅ Automatyczne wykrywanie urządzeń w sieci LAN (UDP multicast)  
✅ Obsługa wielu płytek jednocześnie  
✅ Konfiguracja przez GUI (Config Flow)  
✅ Dynamiczne wykrywanie liczby kanałów (2, 4, 8, 16, 32)  
✅ Opcje bezpieczeństwa:
- **Lockout** – blokada ponownego wyzwolenia (np. 30 s)
- **Pulse** – chwilowe załączenie przekaźnika (np. 200 ms)
✅ Zgodność z Home Assistant OS / HACS

---

## ⚙️ Dlaczego bez MQTT?

Ta integracja nie wymaga pośredników, takich jak **broker MQTT** czy **Mosquitto**.  
Komunikacja odbywa się bezpośrednio między Home Assistant a płytką przekaźnikową przez gniazda UDP/TCP.

**Zalety bezpośredniego połączenia:**
- Brak opóźnień i natychmiastowa reakcja urządzeń  
- Brak konieczności instalacji i konfiguracji dodatkowego brokera MQTT  
- Mniejsze obciążenie systemu i prostsze wdrożenie  
- Stabilniejsze połączenie i mniej punktów awarii  

Integracja stanowi **wydajną alternatywę dla rozwiązań MQTT**, idealną dla użytkowników ceniących prostotę i szybkość działania.

---

## ⚙️ Instalacja przez HACS

1. Skopiuj repozytorium na GitHub: https://github.com/adres433/ha-dtrelay-binary
2. W HACS wybierz:
   - **Integrations → Custom Repositories → Add**
   - Wklej adres repo i wybierz kategorię *Integration*
3. Po zainstalowaniu:
   - Zrestartuj Home Assistant
   - Przejdź do **Ustawienia → Urządzenia i usługi → Dodaj integrację**
   - Wybierz **Dingtian DT-Relay (Binary)**

---

## 🧩 Quick Start

1. Wybierz w kreatorze **Tryb “Discover”**
2. Integracja wyśle multicast probe (`0x05AA`) do `224.0.2.11:60000`
3. Wybierz znalezioną płytkę z listy (SN, IP, model)

---

## 👥 Współpraca i autorzy

Projekt opracowany wspólnie z asystentem AI (ChatGPT, OpenAI) w ramach projektu badawczego konfiguracji Home Assistant.  
Ostateczny kod, struktura i dokumentacja zostały zatwierdzone i rozwinięte przez użytkownika **adres433**.  
Wszystkie prawa autorskie i prawa do publikacji przysługują **adres433**, kod objęty jest licencją MIT.

---

## 🪪 Licencja

MIT License © 2025 – autor: **adres433**
