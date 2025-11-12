# Dingtian Relay Binary - Home Assistant Integration

This custom integration provides native UDP/TCP communication with Dingtian Relay boards (DT-R002/004/008/016/032)
using the Dingtian Binary Protocol.

## Quick Start (EN)
1. Install via HACS (add repository).  
2. In Home Assistant go to **Settings → Devices & Services → Add integration** and search for "Dingtian Relay Binary".  
3. Fill connection details (IP, port, protocol). Use the 'Fill' button to auto-read SN or enter SN manually (5 digits).  
4. Use 'Test' to verify connectivity before saving.

## Szybki start (PL)
1. Zainstaluj przez HACS (dodaj repozytorium).  
2. W Home Assistant: **Ustawienia → Urządzenia i usługi → Dodaj integrację** i wyszukaj "Dingtian Relay Binary".  
3. Wypełnij dane połączenia (IP, port, protokół). Użyj przycisku 'Wypełnij' by pobrać SN lub wpisz ręcznie (5 cyfr).  
4. Przycisk 'Testuj' sprawdzi komunikację przed zapisem.

---

## 📋 Quality Assurance (QA)

This integration has been fully validated prior to release v1.0.3.
See detailed report: ./VALIDATION_REPORT_v1.0.3.md

**Status:** ✅ Ready for public release




## Troubleshooting / Rozwiązywanie problemów

**EN:**
- Error 1258 – device did not respond (check IP, port, firewall). Use 'Test connection' to verify.
- Error 1261 – serial number must be exactly 5 digits. Ensure SN is numeric.
- Connection refused / network unreachable – verify IP/port and protocol (UDP/TCP).

**PL:**
- Błąd 1258 – urządzenie nie odpowiedziało (sprawdź IP, port, zaporę sieciową). Użyj 'Testuj połączenie'.
- Błąd 1261 – numer seryjny musi mieć dokładnie 5 cyfr. Upewnij się, że SN jest numeryczny.
- Połączenie odrzucone / sieć nieosiągalna – sprawdź IP/port i protokół (UDP/TCP).
